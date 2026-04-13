"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import load_env

env = load_env()

# Build PostgreSQL connection URL
# Support both DATABASE_URL and individual components
if env.get("DATABASE_URL") and not env["DATABASE_URL"].startswith("sqlite"):
    DATABASE_URL = env["DATABASE_URL"]
else:
    # Build from components
    db_user = env.get("DB_USER", "postgres")
    db_password = env.get("DB_PASSWORD", "postgres")
    db_host = env.get("DB_HOST", "localhost")
    db_port = env.get("DB_PORT", "5432")
    db_name = env.get("DB_NAME", "survey_analysis")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

