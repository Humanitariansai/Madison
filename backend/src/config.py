"""
Configuration and environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent

# For Cloud Storage, use environment variable or local path
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # "local" or "gcs"

if STORAGE_TYPE == "gcs":
    # Cloud Storage paths (will be handled by GCS client)
    DATA_DIR = Path("/tmp/uploads")  # Temporary for uploads
    PROCESSED_DIR = Path("/tmp/processed")  # Temporary for processing
else:
    # Local file system paths
    DATA_DIR = BASE_DIR / "data" / "uploads"
    PROCESSED_DIR = BASE_DIR / "data" / "processed"

DB_PATH = BASE_DIR / "data" / "survey_analysis.db"

# Environment variables
def load_env():
    """Load and return environment variables as dict"""
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "SECRET_KEY": os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
        "ALGORITHM": os.getenv("ALGORITHM", "HS256"),
        "ACCESS_TOKEN_EXPIRE_MINUTES": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        # PostgreSQL Database Configuration
        "DATABASE_URL": os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/survey_analysis"
        ),
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
        "DB_NAME": os.getenv("DB_NAME", "survey_analysis"),
        "DB_USER": os.getenv("DB_USER", "postgres"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        # Redis Configuration
        "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
        "REDIS_PORT": os.getenv("REDIS_PORT", "6379"),
        "REDIS_DB": os.getenv("REDIS_DB", "0"),
    }

