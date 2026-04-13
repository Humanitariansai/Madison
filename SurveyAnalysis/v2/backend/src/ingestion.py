"""
CSV file ingestion and validation
Supports both small and large files
"""
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, List, Optional
import os

# Threshold for large file handling (rows)
LARGE_FILE_THRESHOLD = 100000  # 100k rows

def ingest_and_prepare(file_path: str, max_rows: Optional[int] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Ingest CSV file and prepare for analysis
    For large files, only loads sample for column detection
    
    Args:
        file_path: Path to CSV file
        max_rows: Maximum rows to load (None = load all, use for large files)
    
    Returns:
        tuple: (dataframe, report_dict)
    """
    # Check file size first
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    # For very large files, only read sample
    if max_rows:
        df = pd.read_csv(
            file_path,
            nrows=max_rows,
            encoding='utf-8-sig',
            on_bad_lines='skip'
        )
    elif file_size_mb > 100:  # Files > 100MB
        # Read sample for column detection
        df = pd.read_csv(
            file_path,
            nrows=1000,
            encoding='utf-8-sig',
            on_bad_lines='skip'
        )
    else:
        # Small file, load all
        df = pd.read_csv(file_path, encoding='utf-8-sig', on_bad_lines='skip')
    
    # Detect text column
    text_col = None
    text_keywords = ['comment', 'feedback', 'response', 'text', 'answer', 'review']
    for col in df.columns:
        if any(kw in col.lower() for kw in text_keywords):
            text_col = col
            break
    
    # If not found, try to find column with most text
    if not text_col:
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains mostly text
                sample = df[col].dropna().head(10).astype(str)
                avg_length = sample.str.len().mean()
                if avg_length > 20:  # Average length > 20 chars
                    text_col = col
                    break
    
    # Detect time column
    time_col = None
    time_keywords = ['time', 'date', 'timestamp', 'created', 'submitted']
    for col in df.columns:
        if any(kw in col.lower() for kw in time_keywords):
            time_col = col
            break
    
    # Estimate total rows for large files
    estimated_rows = None
    if file_size_mb > 100 or max_rows:
        # Count rows efficiently
        try:
            with open(file_path, 'rb') as f:
                estimated_rows = sum(1 for _ in f) - 1  # Subtract header
        except:
            pass
    
    # Validation report
    issues = []
    if not text_col:
        issues.append("No text column detected - please specify manually")
    
    if estimated_rows and estimated_rows > LARGE_FILE_THRESHOLD:
        issues.append(f"Large file detected ({estimated_rows:,} rows). Will use chunked processing.")
    
    report = {
        "ok": len(issues) == 0,
        "columns": list(df.columns),
        "text_col": text_col,
        "time_col": time_col,
        "issues": issues,
        "estimated_rows": estimated_rows,
        "file_size_mb": round(file_size_mb, 2),
        "is_large_file": estimated_rows is not None and estimated_rows > LARGE_FILE_THRESHOLD
    }
    
    return df, report

