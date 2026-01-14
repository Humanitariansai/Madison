"""
Database initialization script for PostgreSQL
Run this once to create the database and tables
"""
from src.database import engine, Base
from src.models import User, FileHistory, ReportHistory
from src.config import load_env

def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()

