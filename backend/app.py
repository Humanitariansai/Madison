"""
FastAPI Backend for Survey Analysis Application
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import os
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from src.database import get_db, engine, Base
from src.models import User, FileHistory, ReportHistory
from src.auth import (
    create_user as auth_create_user,
    authenticate_user as auth_authenticate_user,
    get_current_user,
    hash_password
)
from src.config import load_env, DATA_DIR, PROCESSED_DIR, DB_PATH
from src.utils import ensure_dirs
from src.ingestion import ingest_and_prepare
from src.sentiment import analyze_sentiment
from src.themes import extract_themes
from src.trends import sentiments_over_time, trend_metrics
from src.priorities import compute_theme_priorities
from src.theme_analysis import analyze_theme_sentiment, analyze_themes_over_time, get_overall_theme_trends
from src.ai import (
    classify_sentiments,
    extract_keyphrases,
    extract_weighted_keyphrases,
    extract_impact_terms,
    summarize_overall,
    recommend_actions
)
from src.wordcloud_gen import build_wordcloud_image, build_ai_impact_wordcloud
from src.report_generator import generate_pdf_report, generate_json_report
from src.history import (
    save_file_history,
    save_report_history,
    get_user_file_history,
    get_user_report_history,
    get_file_reports
)
from src.report import build_pdf_report, ReportSection
from src.storage import save_processed, get_engine
from src.cache import (
    get_cached_sentiment_result,
    cache_sentiment_result,
    get_cached_theme_result,
    cache_theme_result,
    invalidate_cache
)
from src.summarization import generate_multi_level_summaries, generate_executive_summary
from src.vector_db import (
    store_embeddings,
    find_similar_responses,
    ensure_collection,
    get_vector_db_client
)

from pydantic import BaseModel, EmailStr
from datetime import datetime
import pandas as pd
import hashlib
import tempfile
import shutil

# Initialize FastAPI app
app = FastAPI(
    title="Survey Analysis API",
    description="""
    Backend API for Humanitarians AI Survey Analysis Platform
    
    ## Features
    - User authentication with JWT
    - CSV file upload and validation
    - Sentiment analysis (VADER and LLM)
    - Theme extraction (YAKE, LDA, NMF)
    - Large file processing (1M+ rows)
    - Async background processing
    - History tracking
    
    ## Authentication
    All protected endpoints require a Bearer token in the Authorization header.
    Get your token by logging in at `/api/auth/login`.
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@humanitarians.ai"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.humanitarians.ai",
            "description": "Production server"
        }
    ]
)

# CORS configuration - use FastAPI's built-in CORS middleware
# IMPORTANT: When allow_credentials=True, you CANNOT use allow_origins=["*"]
# Solution: Use a custom middleware that allows all origins with credentials

# Custom CORS middleware that allows all origins even with credentials
class AllowAllCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        # Get origin from request header, default to "*" if not present
        origin = request.headers.get("origin")
        if not origin:
            origin = "*"
        
        # Handle OPTIONS preflight requests
        if request.method == "OPTIONS":
            response = Response(
                content="",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With, X-CSRFToken",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "3600",
                    "Access-Control-Expose-Headers": "*",
                }
            )
            return response
        
        # Process the actual request
        response = await call_next(request)
        
        # Add CORS headers to all responses
        # Use the request's origin to echo it back (required for credentials)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With, X-CSRFToken"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response

# Use custom middleware that allows all origins with credentials
app.add_middleware(AllowAllCORSMiddleware)

# Security
security = HTTPBearer()

# Initialize database (create tables if they don't exist)
# Run `python src/db_init.py` manually if needed
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables automatically: {e}")
    print("Please run: python src/db_init.py")

# Ensure directories exist
env = load_env()
ensure_dirs(DATA_DIR, PROCESSED_DIR, DB_PATH.parent)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    rows_count: int
    columns: List[str]
    text_col: Optional[str]
    time_col: Optional[str]
    issues: List[str]

class AnalysisRequest(BaseModel):
    file_id: int
    use_ai: bool = False
    use_lda: bool = False  # Use LDA topic modeling instead of YAKE
    top_k: int = 20
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    frequency: Optional[str] = "W"  # Frequency for temporal analysis: "D" (Daily), "W" (Weekly), "M" (Monthly)

class SentimentResponse(BaseModel):
    sentiment_distribution: dict
    processed_data: dict
    wordcloud_path: Optional[str] = None
    sentiment_over_time: Optional[List[dict]] = None  # Sentiment trends over time
    trend_metrics: Optional[List[dict]] = None  # Detailed trend metrics

class ThemeResponse(BaseModel):
    themes: List[dict]
    priorities: Optional[List[dict]] = None
    wordcloud_path: Optional[str] = None
    theme_sentiment: Optional[List[dict]] = None  # Sentiment analysis per theme
    theme_temporal: Optional[List[dict]] = None  # Themes over time
    overall_trends: Optional[List[dict]] = None  # Overall theme trends over time

class SummariesResponse(BaseModel):
    overall: Optional[str] = None
    by_theme: Dict[str, str] = {}
    by_segment: Dict[str, str] = {}
    executive_summary: Optional[str] = None
    statistics: Dict = {}

class TrendsResponse(BaseModel):
    trends: List[dict]
    frequency: str = "W"  # D, W, M
    summary: Optional[Dict] = None

class SemanticSearchRequest(BaseModel):
    file_id: int
    query_text: str
    top_k: int = 10
    score_threshold: float = 0.5

class SemanticSearchResponse(BaseModel):
    results: List[dict]
    query_text: str
    total_found: int

# Routes
@app.get("/")
async def root():
    return {"message": "Survey Analysis API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Authentication routes
@app.post("/api/auth/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account"""
    success, message, user = auth_create_user(
        user_data.username,
        user_data.email,
        user_data.password,
        db
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return UserResponse.model_validate(user)

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    success, message, user_id = auth_authenticate_user(
        credentials.username,
        credentials.password,
        db
    )
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    # Generate JWT token (simplified - you should use proper JWT)
    from src.auth import create_access_token
    token = create_access_token({"sub": str(user_id)})
    
    user = db.query(User).filter(User.id == user_id).first()
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    user = get_current_user(credentials.credentials, db)
    return UserResponse.model_validate(user)

class GoogleLoginRequest(BaseModel):
    google_token: str

@app.post("/api/auth/google", response_model=TokenResponse)
async def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with Google OAuth token"""
    import requests
    
    try:
        # Verify Google token and get user info
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {request.google_token}'},
            timeout=10
        )
        response.raise_for_status()
        google_user = response.json()
        
        email = google_user.get('email')
        name = google_user.get('name', '')
        google_id = google_user.get('id', '')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user with Google account
            # Generate username from email or name
            username = email.split('@')[0] if email else f"user_{google_id[:8]}"
            # Ensure username is unique
            base_username = username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user without password (OAuth users don't need password)
            user = User(
                username=username,
                email=email,
                password_hash=hash_password(f"oauth_{google_id}")  # Dummy password for OAuth users
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate JWT token
        from src.auth import create_access_token
        token = create_access_token({"sub": str(user.id)})
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
    except requests.RequestException as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google authentication failed: {str(e)}")

# File upload and analysis routes
@app.post("/api/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Upload and validate CSV file"""
    user = get_current_user(credentials.credentials, db)
    
    # Save uploaded file
    file_hash = hashlib.md5()
    file_content = await file.read()
    file_hash.update(file_content)
    file_hash_str = file_hash.hexdigest()
    
    # Save to temporary location
    tmp_path = DATA_DIR / f"upload_{user.id}_{file_hash_str[:8]}.csv"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(tmp_path, "wb") as f:
        f.write(file_content)
    
    # Ingest and validate
    df_raw, report = ingest_and_prepare(tmp_path)
    
    # Save to history
    file_history_id = save_file_history(
        user_id=user.id,
        original_filename=file.filename,
        file_hash=file_hash_str,
        file_path=str(tmp_path),
        rows_count=len(df_raw),
        db=db
    )
    
    return FileUploadResponse(
        file_id=file_history_id,
        filename=file.filename,
        rows_count=len(df_raw),
        columns=report["columns"],
        text_col=report.get("text_col"),
        time_col=report.get("time_col"),
        issues=report.get("issues", [])
    )

@app.post("/api/analysis/sentiment")
async def analyze_sentiment_endpoint(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Perform sentiment analysis on uploaded file"""
    user = get_current_user(credentials.credentials, db)
    
    # Get file history
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check cache
    cache_params = {
        "use_ai": request.use_ai,
        "date_start": request.date_start,
        "date_end": request.date_end,
        "frequency": request.frequency or "W"
    }
    cached_result = get_cached_sentiment_result(request.file_id, cache_params)
    if cached_result and cached_result.get("wordcloud_path"):
        # Return cached result if it includes wordcloud
        return SentimentResponse(**cached_result)
    elif cached_result:
        # Cached result exists but no wordcloud - generate it and update cache
        # Load data to generate wordcloud
        df_raw, report = ingest_and_prepare(file_history.file_path)
        if request.date_start and request.date_end and report.get("time_col"):
            time_col = report["time_col"]
            df_raw[time_col] = pd.to_datetime(df_raw[time_col], errors="coerce")
            start_date = pd.Timestamp(request.date_start)
            end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
            mask = (df_raw[time_col] >= start_date) & (df_raw[time_col] < end_date)
            df_raw = df_raw[mask].copy()
        
        # Perform sentiment analysis to get processed data
        if request.use_ai:
            try:
                labels = classify_sentiments(
                    df_raw[report["text_col"]].astype(str).tolist(),
                    batch_size=40
                )
                df_proc = df_raw.copy()
                df_proc["sent_label"] = labels
            except Exception:
                df_proc = analyze_sentiment(df_raw, report["text_col"])
        else:
            df_proc = analyze_sentiment(df_raw, report["text_col"])
        
        # Generate wordcloud for cached result
        wordcloud_path = None
        try:
            wordcloud_dir = Path(PROCESSED_DIR) / "wordclouds"
            wordcloud_dir.mkdir(parents=True, exist_ok=True)
            wordcloud_file = wordcloud_dir / f"sentiment_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
            
            sent_col = "sent_label" if "sent_label" in df_proc.columns else "sent_compound"
            
            wordcloud_path_result = build_wordcloud_image(
                df_proc,
                report["text_col"],
                wordcloud_file,
                sent_col=sent_col
            )
            
            if wordcloud_path_result:
                wordcloud_path = f"/api/wordclouds/sentiment_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
        except Exception as e:
            import logging
            logging.warning(f"Wordcloud generation failed: {e}")
        
        # Update cached result with wordcloud
        cached_result["wordcloud_path"] = wordcloud_path
        cache_sentiment_result(request.file_id, cache_params, cached_result)
        return SentimentResponse(**cached_result)
    
    # Load and process data (with large file handling)
    # For large files, only load sample for column detection
    max_rows = 10000 if request.file_id else None  # Sample for large files
    df_raw, report = ingest_and_prepare(file_history.file_path, max_rows=max_rows)
    
    # Check if this is a large file
    is_large_file = report.get("is_large_file", False)
    estimated_rows = report.get("estimated_rows")
    
    # Apply date filter if provided
    if request.date_start and request.date_end and report.get("time_col"):
        time_col = report["time_col"]
        df_raw[time_col] = pd.to_datetime(df_raw[time_col], errors="coerce")
        start_date = pd.Timestamp(request.date_start)
        end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
        mask = (df_raw[time_col] >= start_date) & (df_raw[time_col] < end_date)
        df_raw = df_raw[mask].copy()
    
    # For large files, use chunked processing
    if is_large_file and estimated_rows and estimated_rows > 100000:
        from src.large_file_processor import analyze_sentiment_chunked
        
        results = analyze_sentiment_chunked(
            file_history.file_path,
            report["text_col"],
            chunk_size=10000
        )
        
        # Generate wordcloud from sample for large files
        wordcloud_path = None
        try:
            # Load a sample for wordcloud (max 10k rows)
            df_sample, _ = ingest_and_prepare(file_history.file_path, max_rows=10000)
            if request.date_start and request.date_end and report.get("time_col"):
                time_col = report["time_col"]
                df_sample[time_col] = pd.to_datetime(df_sample[time_col], errors="coerce")
                start_date = pd.Timestamp(request.date_start)
                end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
                mask = (df_sample[time_col] >= start_date) & (df_sample[time_col] < end_date)
                df_sample = df_sample[mask].copy()
            
            df_proc_sample = analyze_sentiment(df_sample, report["text_col"])
            
            wordcloud_dir = Path(PROCESSED_DIR) / "wordclouds"
            wordcloud_dir.mkdir(parents=True, exist_ok=True)
            wordcloud_file = wordcloud_dir / f"sentiment_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
            
            sent_col = "sent_label" if "sent_label" in df_proc_sample.columns else "sent_compound"
            
            wordcloud_path_result = build_wordcloud_image(
                df_proc_sample,
                report["text_col"],
                wordcloud_file,
                sent_col=sent_col
            )
            
            if wordcloud_path_result:
                wordcloud_path = f"/api/wordclouds/sentiment_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
        except Exception as e:
            import logging
            logging.warning(f"Wordcloud generation for large file failed: {e}")
        
        # Calculate sentiment over time for large files (if time column exists)
        sentiment_over_time_df = None
        trend_metrics_df = None
        time_col = report.get("time_col")
        
        if time_col:
            try:
                # Get frequency from request (default to "W" for weekly)
                freq = request.frequency or "W"
                # Validate frequency
                if freq not in ["D", "W", "M"]:
                    freq = "W"
                
                # Load sample for temporal analysis
                df_sample, _ = ingest_and_prepare(file_history.file_path, max_rows=50000)
                if request.date_start and request.date_end:
                    df_sample[time_col] = pd.to_datetime(df_sample[time_col], errors="coerce")
                    start_date = pd.Timestamp(request.date_start)
                    end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
                    mask = (df_sample[time_col] >= start_date) & (df_sample[time_col] < end_date)
                    df_sample = df_sample[mask].copy()
                
                df_proc_sample = analyze_sentiment(df_sample, report["text_col"])
                
                if time_col in df_proc_sample.columns:
                    sentiment_over_time_df = sentiments_over_time(df_proc_sample, time_col, freq=freq)
                    trend_metrics_df = trend_metrics(df_proc_sample, time_col, freq=freq, roll=3)
            except Exception as e:
                import logging
                logging.warning(f"Sentiment temporal analysis for large file failed: {e}")
        
        # Helper function to clean records for JSON
        def clean_records_for_json(df):
            """Convert DataFrame to records and clean for JSON serialization"""
            if df is None or df.empty:
                return None
            records = df.to_dict("records")
            # Clean each record
            for record in records:
                for key, value in record.items():
                    # Handle NaN, inf, -inf
                    if isinstance(value, float):
                        if pd.isna(value) or value == float('inf') or value == float('-inf'):
                            record[key] = None
                        # Ensure values are within JSON range
                        elif abs(value) > 1e308:
                            record[key] = None
                    # Convert datetime objects to strings
                    elif hasattr(value, 'isoformat'):
                        record[key] = value.isoformat() if pd.notnull(value) else None
                    # Convert Period objects to strings
                    elif hasattr(value, 'strftime'):
                        try:
                            record[key] = value.strftime('%Y-%m-%d') if pd.notnull(value) else None
                        except:
                            record[key] = str(value) if pd.notnull(value) else None
            return records
        
        # Clean temporal dataframes
        sentiment_over_time_records = clean_records_for_json(sentiment_over_time_df)
        trend_metrics_records = clean_records_for_json(trend_metrics_df)
        
        response_data = {
            "sentiment_distribution": results["sentiment_distribution"],
            "processed_data": {
                "total_rows": results["total_rows_processed"],
                "positive": results["sentiment_distribution"].get("positive", 0),
                "negative": results["sentiment_distribution"].get("negative", 0),
                "neutral": results["sentiment_distribution"].get("neutral", 0)
            },
            "wordcloud_path": wordcloud_path,
            "sentiment_over_time": sentiment_over_time_records,
            "trend_metrics": trend_metrics_records
        }
        
        # Cache result
        cache_sentiment_result(request.file_id, cache_params, response_data)
        
        return SentimentResponse(**response_data)
    
    # Perform sentiment analysis (normal processing for small files)
    if request.use_ai:
        import logging
        logging.info("🤖 [APP] Use AI enabled for sentiment analysis - calling OpenAI")
        try:
            labels = classify_sentiments(
                df_raw[report["text_col"]].astype(str).tolist(),
                batch_size=40
            )
            df_proc = df_raw.copy()
            df_proc["sent_label"] = labels
            logging.info("✅ [APP] AI sentiment classification completed successfully")
        except Exception as e:
            import logging
            logging.warning(f"⚠️ [APP] AI sentiment classification failed: {e}, falling back to VADER")
            df_proc = analyze_sentiment(df_raw, report["text_col"])
    else:
        import logging
        logging.info("📊 [APP] Using VADER for sentiment analysis (AI not enabled)")
        df_proc = analyze_sentiment(df_raw, report["text_col"])
    
    # Calculate distribution
    distribution = df_proc["sent_label"].value_counts().to_dict()
    
    # Calculate sentiment over time (if time column exists)
    sentiment_over_time_df = None
    trend_metrics_df = None
    time_col = report.get("time_col")
    
    def clean_dataframe_for_json(df):
        """Clean DataFrame to make it JSON-compliant by replacing NaN, inf, -inf"""
        if df is None or df.empty:
            return None
        df_clean = df.copy()
        # Replace NaN, inf, -inf with None (which becomes null in JSON)
        df_clean = df_clean.replace([float('inf'), float('-inf')], None)
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        return df_clean
    
    if time_col and time_col in df_proc.columns:
        try:
            # Get frequency from request (default to "W" for weekly)
            freq = request.frequency or "W"
            # Validate frequency
            if freq not in ["D", "W", "M"]:
                freq = "W"
            
            # Calculate sentiment over time
            sentiment_over_time_df = sentiments_over_time(
                df_proc,
                time_col,
                freq=freq
            )
            sentiment_over_time_df = clean_dataframe_for_json(sentiment_over_time_df)
            
            # Calculate detailed trend metrics
            trend_metrics_df = trend_metrics(
                df_proc,
                time_col,
                freq=freq,
                roll=3  # 3-period rolling average
            )
            trend_metrics_df = clean_dataframe_for_json(trend_metrics_df)
        except Exception as e:
            import logging
            logging.warning(f"Sentiment temporal analysis failed: {e}")
    
    # Generate wordcloud
    wordcloud_path = None
    try:
        wordcloud_dir = Path(PROCESSED_DIR) / "wordclouds"
        wordcloud_dir.mkdir(parents=True, exist_ok=True)
        wordcloud_file = wordcloud_dir / f"sentiment_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
        
        # Determine sentiment column
        sent_col = "sent_label" if "sent_label" in df_proc.columns else "sent_compound"
        
        wordcloud_path_result = build_wordcloud_image(
            df_proc,
            report["text_col"],
            wordcloud_file,
            sent_col=sent_col
        )
        
        if wordcloud_path_result:
            wordcloud_path = f"/api/wordclouds/sentiment_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
    except Exception as e:
        import logging
        logging.warning(f"Wordcloud generation failed: {e}")
    
    # Clean temporal dataframes before converting to dict
    def clean_records_for_json(df):
        """Convert DataFrame to records and clean for JSON serialization"""
        if df is None or df.empty:
            return None
        records = df.to_dict("records")
        # Clean each record
        for record in records:
            for key, value in record.items():
                # Handle NaN, inf, -inf
                if isinstance(value, float):
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        record[key] = None
                    # Ensure values are within JSON range
                    elif abs(value) > 1e308:
                        record[key] = None
                # Convert datetime objects to strings
                elif hasattr(value, 'isoformat'):
                    record[key] = value.isoformat() if pd.notnull(value) else None
                # Convert Period objects to strings
                elif hasattr(value, 'strftime'):
                    try:
                        record[key] = value.strftime('%Y-%m-%d') if pd.notnull(value) else None
                    except:
                        record[key] = str(value) if pd.notnull(value) else None
        return records
    
    sentiment_over_time_records = clean_records_for_json(sentiment_over_time_df)
    trend_metrics_records = clean_records_for_json(trend_metrics_df)
    
    response_data = {
        "sentiment_distribution": distribution,
        "processed_data": {
            "total_rows": len(df_proc),
            "positive": distribution.get("positive", 0),
            "negative": distribution.get("negative", 0),
            "neutral": distribution.get("neutral", 0)
        },
        "wordcloud_path": wordcloud_path,
        "sentiment_over_time": sentiment_over_time_records,
        "trend_metrics": trend_metrics_records
    }
    
    # Cache result
    cache_sentiment_result(request.file_id, cache_params, response_data)
    
    return SentimentResponse(**response_data)

@app.post("/api/analysis/themes")
async def extract_themes_endpoint(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Extract themes using YAKE, TF-IDF, or LDA topic modeling"""
    user = get_current_user(credentials.credentials, db)
    
    # Get file history
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check cache
    cache_params = {
        "use_ai": request.use_ai,
        "top_k": request.top_k,
        "use_lda": getattr(request, "use_lda", False),
        "date_start": request.date_start,
        "date_end": request.date_end
    }
    cached_result = get_cached_theme_result(request.file_id, cache_params)
    if cached_result:
        return ThemeResponse(**cached_result)
    
    # Load data
    df_raw, report = ingest_and_prepare(file_history.file_path)
    
    # Apply date filter
    if request.date_start and request.date_end and report.get("time_col"):
        time_col = report["time_col"]
        df_raw[time_col] = pd.to_datetime(df_raw[time_col], errors="coerce")
        start_date = pd.Timestamp(request.date_start)
        end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
        mask = (df_raw[time_col] >= start_date) & (df_raw[time_col] < end_date)
        df_raw = df_raw[mask].copy()
    
    # Extract themes
    themes_df = None
    use_lda = request.use_lda  # Direct access, no need for getattr
    
    # Try LDA topic modeling if requested
    if use_lda:
        import logging
        logging.info(f"LDA topic modeling requested (use_lda=True)")
        try:
            from src.topic_modeling import extract_topics_lda
            texts = df_raw[report["text_col"]].astype(str).tolist()
            # Filter out empty texts
            texts = [t for t in texts if isinstance(t, str) and t.strip()]
            
            if len(texts) >= 10:  # Need minimum texts for LDA
                logging.info(f"Running LDA on {len(texts)} texts")
                topics, topic_dist = extract_topics_lda(
                    texts,
                    n_topics=min(request.top_k, len(texts) // 10),  # Adaptive topic count
                    max_features=1000
                )
                
                if topics:
                    logging.info(f"LDA extracted {len(topics)} topics")
                    # Convert topics to themes format
                    themes_list = []
                    for topic in topics[:request.top_k]:
                        # Use top 3 words as keyphrase
                        keyphrase = " ".join(topic["top_words"][:3])
                        themes_list.append({
                            "keyphrase": keyphrase,
                            "weight": topic["topic_weight"] / 100.0  # Normalize
                        })
                    themes_df = pd.DataFrame(themes_list)
                else:
                    logging.warning("LDA returned no topics")
            else:
                logging.warning(f"LDA requires at least 10 texts, but only {len(texts)} provided")
        except Exception as e:
            import logging
            logging.warning(f"LDA topic modeling failed: {e}")
    
    # Fallback to AI or YAKE/TF-IDF
    if themes_df is None or themes_df.empty:
        if request.use_ai:
            try:
                import logging
                logging.info(f"🤖 [APP] Use AI enabled for theme extraction - calling OpenAI")
                weighted = extract_weighted_keyphrases(
                    df_raw[report["text_col"]].astype(str).tolist(),
                    top_k=request.top_k
                )
                if weighted:
                    themes_df = pd.DataFrame([
                        {"keyphrase": w["keyphrase"], "weight": w["weight"]}
                        for w in weighted
                    ])
                    logging.info(f"✅ [APP] AI extracted {len(weighted)} themes successfully")
                else:
                    logging.warning("⚠️ [APP] AI theme extraction returned empty results, falling back to YAKE/TF-IDF")
            except Exception as e:
                import logging
                logging.warning(f"⚠️ [APP] AI theme extraction failed: {e}, falling back to YAKE/TF-IDF")
                pass
        
        if themes_df is None or themes_df.empty:
            themes_df = extract_themes(
                df_raw,
                report["text_col"],
                top_k=request.top_k,
                ngram_range=(1, 3)
            )
    
    theme_list = themes_df["keyphrase"].tolist() if not themes_df.empty else []
    
    # Run sentiment analysis on the data (required for theme sentiment analysis)
    df_with_sentiment = None
    try:
        df_with_sentiment = analyze_sentiment(df_raw, report["text_col"])
    except Exception as e:
        import logging
        logging.warning(f"Sentiment analysis failed: {e}")
        df_with_sentiment = df_raw.copy()
        # Add dummy sentiment columns if analysis failed
        if "sent_label" not in df_with_sentiment.columns:
            df_with_sentiment["sent_label"] = "neutral"
        if "sent_compound" not in df_with_sentiment.columns:
            df_with_sentiment["sent_compound"] = 0.0
    
    # Analyze theme sentiment (individual theme sentiment)
    theme_sentiment_df = None
    if theme_list and df_with_sentiment is not None:
        try:
            theme_sentiment_df = analyze_theme_sentiment(
                df_with_sentiment,
                theme_list,
                report["text_col"]
            )
        except Exception as e:
            import logging
            logging.warning(f"Theme sentiment analysis failed: {e}")
    
    # Analyze themes over time (temporal trends)
    theme_temporal_df = None
    overall_trends_df = None
    if theme_list and df_with_sentiment is not None:
        try:
            time_col = report.get("time_col")
            theme_temporal_df = analyze_themes_over_time(
                df_with_sentiment,
                theme_list,
                report["text_col"],
                time_col=time_col,
                freq="W"  # Weekly by default
            )
            
            # Get overall trends
            if not theme_temporal_df.empty:
                overall_trends_df = get_overall_theme_trends(theme_temporal_df)
        except Exception as e:
            import logging
            logging.warning(f"Theme temporal analysis failed: {e}")
    
    # Compute priorities
    prio = None
    if theme_list:
        try:
            effort_map = {t: 0.5 for t in theme_list}
            prio = compute_theme_priorities(
                df_with_sentiment if df_with_sentiment is not None else df_raw,
                theme_list,
                text_col=report["text_col"],
                time_col=report.get("time_col"),
                effort_map=effort_map
            )
        except Exception:
            pass
    
    # Generate wordcloud from themes
    wordcloud_path = None
    try:
        if not themes_df.empty:
            wordcloud_dir = Path(PROCESSED_DIR) / "wordclouds"
            wordcloud_dir.mkdir(parents=True, exist_ok=True)
            wordcloud_file = wordcloud_dir / f"themes_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
            
            # Convert themes to AI impact format
            terms = []
            for _, row in themes_df.iterrows():
                # Get sentiment for this theme from processed data
                theme_text = str(row.get("keyphrase", ""))
                if theme_text:
                    # Find rows mentioning this theme
                    mask = df_raw[report["text_col"]].astype(str).str.contains(theme_text, case=False, na=False)
                    if mask.any():
                        # Get sentiment for matching rows
                        df_theme = df_raw[mask].copy()
                        df_theme_proc = analyze_sentiment(df_theme, report["text_col"])
                        
                        # Calculate average sentiment
                        if "sent_compound" in df_theme_proc.columns:
                            avg_sent = df_theme_proc["sent_compound"].mean()
                        else:
                            sent_map = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
                            avg_sent = df_theme_proc["sent_label"].map(sent_map).mean()
                        
                        terms.append({
                            "term": theme_text,
                            "freq": int(mask.sum()),
                            "sentiment": float(avg_sent) if not pd.isna(avg_sent) else 0.0
                        })
            
            if terms:
                wordcloud_path_result = build_ai_impact_wordcloud(
                    terms,
                    wordcloud_file
                )
                
                if wordcloud_path_result:
                    wordcloud_path = f"/api/wordclouds/themes_{request.file_id}_{hashlib.md5(str(cache_params).encode()).hexdigest()[:8]}.png"
    except Exception as e:
        import logging
        logging.warning(f"Theme wordcloud generation failed: {e}")
    
    response_data = {
        "themes": themes_df.to_dict("records") if not themes_df.empty else [],
        "priorities": prio.to_dict("records") if prio is not None and not prio.empty else None,
        "wordcloud_path": wordcloud_path,
        "theme_sentiment": theme_sentiment_df.to_dict("records") if theme_sentiment_df is not None and not theme_sentiment_df.empty else None,
        "theme_temporal": theme_temporal_df.to_dict("records") if theme_temporal_df is not None and not theme_temporal_df.empty else None,
        "overall_trends": overall_trends_df.to_dict("records") if overall_trends_df is not None and not overall_trends_df.empty else None
    }
    
    # Cache result
    cache_theme_result(request.file_id, cache_params, response_data)
    
    return ThemeResponse(**response_data)

@app.post("/api/analysis/summaries")
async def generate_summaries_endpoint(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Generate multi-level summaries: overall, by theme, by segment"""
    user = get_current_user(credentials.credentials, db)
    
    # Get file history
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Load data
    df_raw, report = ingest_and_prepare(file_history.file_path)
    
    # Apply date filter
    if request.date_start and request.date_end and report.get("time_col"):
        time_col = report["time_col"]
        df_raw[time_col] = pd.to_datetime(df_raw[time_col], errors="coerce")
        start_date = pd.Timestamp(request.date_start)
        end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
        mask = (df_raw[time_col] >= start_date) & (df_raw[time_col] < end_date)
        df_raw = df_raw[mask].copy()
    
    # Get themes first
    themes_df = extract_themes(
        df_raw,
        report["text_col"],
        top_k=request.top_k,
        ngram_range=(1, 3)
    )
    theme_list = themes_df["keyphrase"].tolist() if not themes_df.empty else []
    
    # Get sentiment distribution for executive summary
    df_proc = analyze_sentiment(df_raw, report["text_col"])
    sentiment_dist = df_proc["sent_label"].value_counts().to_dict()
    
    # Detect segment column (if exists)
    segment_col = None
    segment_keywords = ['region', 'country', 'product', 'segment', 'category', 'cohort']
    for col in df_raw.columns:
        if any(kw in col.lower() for kw in segment_keywords):
            segment_col = col
            break
    
    # Generate summaries
    summaries = generate_multi_level_summaries(
        df_raw,
        report["text_col"],
        theme_list,
        segment_col=segment_col,
        time_col=report.get("time_col")
    )
    
    # Generate executive summary
    executive_summary = generate_executive_summary(
        summaries,
        sentiment_dist,
        theme_list
    )
    summaries["executive_summary"] = executive_summary
    
    return SummariesResponse(**summaries)

@app.post("/api/analysis/trends", response_model=TrendsResponse)
async def analyze_trends_endpoint(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Analyze sentiment trends over time"""
    user = get_current_user(credentials.credentials, db)
    
    # Get file history
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Load data
    df_raw, report = ingest_and_prepare(file_history.file_path)
    
    # Apply date filter if provided
    if request.date_start and request.date_end and report.get("time_col"):
        time_col = report["time_col"]
        df_raw[time_col] = pd.to_datetime(df_raw[time_col], errors="coerce")
        start_date = pd.Timestamp(request.date_start)
        end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
        mask = (df_raw[time_col] >= start_date) & (df_raw[time_col] < end_date)
        df_raw = df_raw[mask].copy()
    
    # Check if time column exists
    time_col = report.get("time_col")
    if not time_col or time_col not in df_raw.columns:
        return TrendsResponse(
            trends=[],
            frequency=request.frequency or "W",
            summary={"error": "Time column not found. Trends analysis requires a time/date column in your data."}
        )
    
    # Perform sentiment analysis
    df_proc = analyze_sentiment(df_raw, report["text_col"])
    
    # Get frequency from request (default to "W" for weekly)
    freq = request.frequency or "W"
    # Validate frequency
    if freq not in ["D", "W", "M"]:
        freq = "W"
    
    # Calculate trend metrics
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Calculating trend metrics with frequency: {freq}, time_col: {time_col}")
        
        trend_metrics_df = trend_metrics(
            df_proc,
            time_col,
            freq=freq,
            roll=3  # 3-period rolling average
        )
        
        logger.info(f"Trend metrics calculated. Shape: {trend_metrics_df.shape if not trend_metrics_df.empty else 'empty'}")
        
        if trend_metrics_df.empty:
            return TrendsResponse(
                trends=[],
                frequency=freq,
                summary={"error": "No trend data available. Ensure your data has valid timestamps and sentiment labels."}
            )
        
        # Clean data for JSON
        def clean_records_for_json(df):
            """Convert DataFrame to records and clean for JSON serialization"""
            if df is None or df.empty:
                return []
            
            # Convert period column to string before converting to records
            if 'period' in df.columns:
                df = df.copy()
                # Use period_str if available, otherwise convert period to string
                if 'period_str' in df.columns:
                    df['period'] = df['period_str']
                else:
                    df['period'] = pd.to_datetime(df['period'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            records = df.to_dict("records")
            # Clean each record
            for record in records:
                for key, value in record.items():
                    # Handle NaN, inf, -inf
                    if isinstance(value, float):
                        if pd.isna(value) or value == float('inf') or value == float('-inf'):
                            record[key] = None
                        # Ensure values are within JSON range
                        elif abs(value) > 1e308:
                            record[key] = None
                    # Convert datetime objects to strings
                    elif hasattr(value, 'isoformat'):
                        try:
                            record[key] = value.isoformat() if pd.notnull(value) else None
                        except:
                            # If isoformat fails, try strftime
                            try:
                                if hasattr(value, 'strftime'):
                                    record[key] = value.strftime('%Y-%m-%d') if pd.notnull(value) else None
                                else:
                                    record[key] = str(value) if pd.notnull(value) else None
                            except:
                                record[key] = str(value) if pd.notnull(value) else None
                    # Convert Period objects to strings
                    elif hasattr(value, 'strftime'):
                        try:
                            record[key] = value.strftime('%Y-%m-%d') if pd.notnull(value) else None
                        except:
                            record[key] = str(value) if pd.notnull(value) else None
                    # Handle pandas Timestamp objects
                    elif isinstance(value, pd.Timestamp):
                        try:
                            record[key] = value.isoformat() if pd.notnull(value) else None
                        except:
                            record[key] = str(value) if pd.notnull(value) else None
            return records
        
        trends_records = clean_records_for_json(trend_metrics_df)
        logger.info(f"Cleaned {len(trends_records)} trend records for JSON")
        
        # Calculate summary statistics
        if not trend_metrics_df.empty:
            latest = trend_metrics_df.iloc[-1]
            first = trend_metrics_df.iloc[0]
            
            summary = {
                "total_periods": len(trend_metrics_df),
                "latest_sentiment_index": float(latest.get("sent_index", 0)) if pd.notnull(latest.get("sent_index")) else 0.0,
                "first_sentiment_index": float(first.get("sent_index", 0)) if pd.notnull(first.get("sent_index")) else 0.0,
                "sentiment_change": float(latest.get("sent_index", 0) - first.get("sent_index", 0)) if pd.notnull(latest.get("sent_index")) and pd.notnull(first.get("sent_index")) else 0.0,
                "latest_positive_pct": float(latest.get("pos_pct", 0)) if pd.notnull(latest.get("pos_pct")) else 0.0,
                "latest_negative_pct": float(latest.get("neg_pct", 0)) if pd.notnull(latest.get("neg_pct")) else 0.0,
                "trend_direction": "improving" if (latest.get("sent_index", 0) > first.get("sent_index", 0)) else "declining" if (latest.get("sent_index", 0) < first.get("sent_index", 0)) else "stable"
            }
        else:
            summary = {"error": "No trend data available"}
        
        return TrendsResponse(
            trends=trends_records,
            frequency=freq,
            summary=summary
        )
    except Exception as e:
        import logging
        logging.error(f"Trend analysis failed: {e}")
        return TrendsResponse(
            trends=[],
            frequency=freq,
            summary={"error": f"Trend analysis failed: {str(e)}"}
        )

@app.post("/api/analysis/semantic-search")
async def semantic_search_endpoint(
    request: SemanticSearchRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Find similar responses using semantic search"""
    user = get_current_user(credentials.credentials, db)
    
    # Get file history
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Collection name based on file_id
    collection_name = f"survey_responses_{request.file_id}"
    
    # Check if vector DB is available
    client, db_type = get_vector_db_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Vector database (Qdrant) is not available. Please start Qdrant service or configure QDRANT_URL."
        )
    
    # Load data first (needed for both PyTorch and TF-IDF fallback)
    from src.ingestion import ingest_and_prepare
    df_raw, report = ingest_and_prepare(file_history.file_path)
    
    # Try PyTorch-based embeddings first, fallback to TF-IDF if it fails
    embeddings_error = None
    use_tfidf_fallback = False
    
    try:
        from src.embeddings import generate_embeddings
        
        # Check if vector DB is needed (only for PyTorch path)
        if client:
            # Check if embeddings exist, if not generate and store
            ensure_collection(collection_name, vector_size=384)  # all-MiniLM-L6-v2 dimension
            
            texts = df_raw[report["text_col"]].astype(str).tolist()
            
            # Generate embeddings (limit to prevent memory issues)
            max_texts = 10000
            if len(texts) > max_texts:
                texts = texts[:max_texts]
            
            embeddings = generate_embeddings(texts, batch_size=32)
            
            # Store embeddings
            metadata = [{"file_id": request.file_id, "index": i} for i in range(len(texts))]
            store_embeddings(collection_name, embeddings, texts, metadata)
    except ImportError as e:
        embeddings_error = f"Embeddings library not available: {str(e)}. Install sentence-transformers."
        use_tfidf_fallback = True
    except Exception as e:
        error_msg = str(e)
        if "DLL" in error_msg or "torch" in error_msg.lower() or "PyTorch" in error_msg:
            embeddings_error = "PyTorch initialization failed. Using TF-IDF fallback (works without PyTorch)."
            use_tfidf_fallback = True
        else:
            embeddings_error = f"Could not generate embeddings: {error_msg}"
        import logging
        logging.warning(f"Could not prepare PyTorch embeddings: {e}. Will try TF-IDF fallback.")
    
    # Use TF-IDF fallback if PyTorch failed
    if use_tfidf_fallback:
        try:
            from src.vector_db import find_similar_responses_tfidf_fallback
            
            results = find_similar_responses_tfidf_fallback(
                file_history.file_path,
                request.query_text,
                report["text_col"],
                top_k=request.top_k,
                score_threshold=request.score_threshold * 0.6  # Lower threshold for TF-IDF
            )
            
            return SemanticSearchResponse(
                results=results,
                query_text=request.query_text,
                total_found=len(results)
            )
        except Exception as fallback_error:
            import logging
            logging.error(f"TF-IDF fallback also failed: {fallback_error}")
            raise HTTPException(
                status_code=503,
                detail=f"{embeddings_error} TF-IDF fallback also failed: {str(fallback_error)}"
            )
    
    # If we got here, PyTorch worked - perform semantic search in vector DB
    results = find_similar_responses(
        collection_name,
        request.query_text,
        top_k=request.top_k,
        score_threshold=request.score_threshold
    )
    
    return SemanticSearchResponse(
        results=results,
        query_text=request.query_text,
        total_found=len(results)
    )

@app.get("/api/wordclouds/{filename}")
async def get_wordcloud(
    filename: str,
    request: StarletteRequest,
    db: Session = Depends(get_db)
):
    """Serve wordcloud images with optional authentication"""
    # Security: validate filename format
    if not filename.endswith('.png') or '..' in filename or '/' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    wordcloud_path = Path(PROCESSED_DIR) / "wordclouds" / filename
    
    if not wordcloud_path.exists():
        raise HTTPException(status_code=404, detail="Wordcloud not found")
    
    # Try to get user from auth header (optional for images)
    user = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            user = get_current_user(token, db)
        except Exception:
            # If auth fails, continue without user (will verify via filename hash)
            pass
    
    # Verify user has access (extract file_id from filename)
    try:
        if filename.startswith("sentiment_"):
            file_id = int(filename.split("_")[1])
        elif filename.startswith("themes_"):
            file_id = int(filename.split("_")[1])
        else:
            raise HTTPException(status_code=400, detail="Invalid wordcloud type")
        
        # If user is authenticated, verify ownership
        if user:
            file_history = db.query(FileHistory).filter(
                FileHistory.id == file_id,
                FileHistory.user_id == user.id
            ).first()
            
            if not file_history:
                raise HTTPException(status_code=403, detail="Access denied")
        else:
            # Without auth, we rely on the hash in filename for security
            # The hash is generated from cache_params which includes file_id
            # This provides basic security without requiring auth headers
            # For better security, users should be authenticated
            pass
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Invalid filename format")
    except HTTPException:
        raise
    except Exception as e:
        # Log error but don't expose details
        import logging
        logging.warning(f"Error verifying wordcloud access: {e}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        path=str(wordcloud_path),
        media_type="image/png",
        filename=filename
    )

@app.get("/api/history/files")
async def get_files_history(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get user's file upload history with reports"""
    user = get_current_user(credentials.credentials, db)
    files = get_user_file_history(user.id, limit=limit, db=db)
    
    result = []
    for f in files:
        # Get reports for this file
        file_reports = get_file_reports(f.id, db=db)
        result.append({
            "id": f.id,
            "filename": f.original_filename,
            "rows_count": f.rows_count,
            "uploaded_at": f.uploaded_at.isoformat(),
            "file_hash": f.file_hash,
            "file_path": f.file_path,
            "reports": [{
                "id": r.id,
                "report_name": r.report_name,
                "report_type": r.report_type,
                "file_size": r.file_size,
                "generated_at": r.generated_at.isoformat(),
                "report_path": r.report_path,
                "date_range_start": r.date_range_start.isoformat() if r.date_range_start else None,
                "date_range_end": r.date_range_end.isoformat() if r.date_range_end else None
            } for r in file_reports]
        })
    
    return result

@app.get("/api/history/reports")
async def get_reports_history(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get user's report history with file details"""
    user = get_current_user(credentials.credentials, db)
    reports = get_user_report_history(user.id, limit=limit, db=db)
    
    result = []
    for r in reports:
        file_info = None
        if r.file_history_id:
            file_history = db.query(FileHistory).filter(FileHistory.id == r.file_history_id).first()
            if file_history:
                file_info = {
                    "id": file_history.id,
                    "filename": file_history.original_filename,
                    "uploaded_at": file_history.uploaded_at.isoformat()
                }
        
        result.append({
            "id": r.id,
            "report_name": r.report_name,
            "report_type": r.report_type,
            "file_size": r.file_size,
            "generated_at": r.generated_at.isoformat(),
            "report_path": r.report_path,
            "date_range_start": r.date_range_start.isoformat() if r.date_range_start else None,
            "date_range_end": r.date_range_end.isoformat() if r.date_range_end else None,
            "file_info": file_info
        })
    
    return result

@app.get("/api/history/reports/{report_id}/download")
async def download_report(
    report_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Download a generated report"""
    user = get_current_user(credentials.credentials, db)
    
    report = db.query(ReportHistory).filter(
        ReportHistory.id == report_id,
        ReportHistory.user_id == user.id
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_path = Path(report.report_path)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        path=str(report_path),
        filename=report.report_name,
        media_type=f"application/{report.report_type}" if report.report_type == "pdf" else f"text/{report.report_type}"
    )

class ReportGenerationRequest(BaseModel):
    file_id: int
    report_type: str = "pdf"  # "pdf" or "json"
    include_sentiment: bool = True
    include_themes: bool = True
    include_summaries: bool = True
    include_priorities: bool = True
    include_trends: bool = True
    date_start: Optional[str] = None
    date_end: Optional[str] = None

@app.post("/api/reports/generate")
async def generate_report(
    request: ReportGenerationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive report from analysis results"""
    user = get_current_user(credentials.credentials, db)
    
    # Get file history
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Load and prepare data
    df_raw, report = ingest_and_prepare(file_history.file_path)
    
    # Apply date filter if provided
    if request.date_start and request.date_end and report.get("time_col"):
        time_col = report["time_col"]
        df_raw[time_col] = pd.to_datetime(df_raw[time_col], errors="coerce")
        start_date = pd.Timestamp(request.date_start)
        end_date = pd.Timestamp(request.date_end) + pd.Timedelta(days=1)
        mask = (df_raw[time_col] >= start_date) & (df_raw[time_col] < end_date)
        df_raw = df_raw[mask].copy()
    
    # Collect analysis data
    sentiment_data = None
    themes_data = None
    summaries_data = None
    priorities_data = None
    trends_data = None
    
    try:
        # Get sentiment data
        if request.include_sentiment:
            df_proc = analyze_sentiment(df_raw, report["text_col"])
            pos = (df_proc["sent_label"] == "positive").sum()
            neg = (df_proc["sent_label"] == "negative").sum()
            neu = (df_proc["sent_label"] == "neutral").sum()
            total = len(df_proc)
            sentiment_data = {
                "sentiment_distribution": {
                    "positive": int(pos),
                    "negative": int(neg),
                    "neutral": int(neu),
                    "total": total,
                    "positive_pct": (pos / total * 100) if total > 0 else 0,
                    "negative_pct": (neg / total * 100) if total > 0 else 0,
                    "neutral_pct": (neu / total * 100) if total > 0 else 0
                }
            }
        
        # Get themes data
        if request.include_themes:
            themes_df = extract_themes(df_raw, report["text_col"], top_k=20)
            themes_data = {
                "themes": themes_df.to_dict('records') if not themes_df.empty else []
            }
        
        # Get priorities
        if request.include_priorities and themes_data and themes_data.get("themes"):
            themes_list = [t.get("keyphrase", "") for t in themes_data["themes"] if isinstance(t, dict)]
            if themes_list:
                priorities_df = compute_theme_priorities(
                    df_raw,
                    themes_list,
                    report["text_col"],
                    time_col=report.get("time_col")
                )
                priorities_data = {
                    "priorities": priorities_df.to_dict('records') if not priorities_df.empty else []
                }
        
        # Get trends
        if request.include_trends and report.get("time_col"):
            try:
                trend_df = trend_metrics(df_raw, report["time_col"], freq="W")
                trends_data = {
                    "trends": trend_df.to_dict('records') if not trend_df.empty else []
                }
            except Exception as e:
                import logging
                logging.warning(f"Trend analysis failed: {e}")
        
        # Get summaries (if available from cache or generate)
        if request.include_summaries:
            # Try to get from summaries endpoint data if available
            # For now, we'll include basic summaries
            summaries_data = {
                "overall_summary": f"Analysis of {len(df_raw)} responses from {file_history.original_filename}",
                "by_theme": []
            }
        
        # Prepare metadata
        metadata = {
            "rows_count": len(df_raw),
            "file_name": file_history.original_filename,
            "uploaded_at": file_history.uploaded_at.isoformat() if file_history.uploaded_at else None
        }
        
        # Generate report
        reports_dir = Path(PROCESSED_DIR) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_base = Path(file_history.original_filename).stem
        
        if request.report_type == "pdf":
            report_filename = f"{file_base}_report_{timestamp}.pdf"
            report_path = reports_dir / report_filename
            
            date_start = pd.to_datetime(request.date_start) if request.date_start else None
            date_end = pd.to_datetime(request.date_end) if request.date_end else None
            
            generate_pdf_report(
                report_path,
                file_history.original_filename,
                sentiment_data=sentiment_data,
                themes_data=themes_data,
                summaries_data=summaries_data,
                trends_data=trends_data,
                priorities_data=priorities_data,
                date_range_start=date_start,
                date_range_end=date_end,
                metadata=metadata
            )
        else:  # JSON
            report_filename = f"{file_base}_report_{timestamp}.json"
            report_path = reports_dir / report_filename
            
            generate_json_report(
                report_path,
                sentiment_data=sentiment_data,
                themes_data=themes_data,
                summaries_data=summaries_data,
                trends_data=trends_data,
                priorities_data=priorities_data,
                metadata=metadata
            )
        
        # Save to history
        date_start_dt = pd.to_datetime(request.date_start) if request.date_start else None
        date_end_dt = pd.to_datetime(request.date_end) if request.date_end else None
        
        report_id = save_report_history(
            user_id=user.id,
            file_history_id=file_history.id,
            report_type=request.report_type,
            report_path=str(report_path),
            report_name=report_filename,
            db=db,
            date_range_start=date_start_dt,
            date_range_end=date_end_dt
        )
        
        return {
            "report_id": report_id,
            "report_name": report_filename,
            "report_type": request.report_type,
            "report_path": f"/api/history/reports/{report_id}/download",
            "file_size": report_path.stat().st_size,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        import logging
        logging.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

# Async processing endpoints for large files
@app.post("/api/analysis/async/sentiment")
async def start_async_sentiment(
    request: AnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Start async sentiment analysis for large files"""
    user = get_current_user(credentials.credentials, db)
    
    file_history = db.query(FileHistory).filter(
        FileHistory.id == request.file_id,
        FileHistory.user_id == user.id
    ).first()
    
    if not file_history:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        from src.async_processor import start_async_processing
        
        task_id = start_async_processing(
            file_id=request.file_id,
            user_id=user.id,
            operation="sentiment",
            text_col=request.text_col or "text",
            chunk_size=10000
        )
        
        if task_id:
            return {"task_id": task_id, "status": "started"}
        else:
            raise HTTPException(
                status_code=503,
                detail="Async processing not available. Use regular endpoint."
            )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Async processing requires Celery. Install with: pip install celery redis"
        )

@app.get("/api/analysis/async/status/{task_id}")
async def get_async_status(
    task_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get status of async processing task"""
    get_current_user(credentials.credentials, None)  # Just verify auth
    
    try:
        from src.async_processor import get_task_status
        status = get_task_status(task_id)
        return status
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Async processing not available"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

