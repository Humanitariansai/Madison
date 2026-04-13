"""
History management for files and reports
"""
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from src.models import FileHistory, ReportHistory

def save_file_history(
    user_id: int,
    original_filename: str,
    file_hash: str,
    file_path: str,
    rows_count: int,
    db: Session = None
) -> int:
    """Save file upload to history"""
    if db is None:
        from src.database import SessionLocal
        db = SessionLocal()
    file_history = FileHistory(
        user_id=user_id,
        original_filename=original_filename,
        file_hash=file_hash,
        file_path=file_path,
        rows_count=rows_count
    )
    db.add(file_history)
    db.commit()
    db.refresh(file_history)
    return file_history.id

def save_report_history(
    user_id: int,
    file_history_id: Optional[int],
    report_type: str,
    report_path: str,
    report_name: str,
    db: Session = None,
    date_range_start: Optional[datetime] = None,
    date_range_end: Optional[datetime] = None
) -> int:
    """Save report to history"""
    if db is None:
        from src.database import SessionLocal
        db = SessionLocal()
    report_path_obj = Path(report_path)
    file_size = report_path_obj.stat().st_size if report_path_obj.exists() else 0
    
    report_history = ReportHistory(
        user_id=user_id,
        file_history_id=file_history_id,
        report_type=report_type,
        report_path=report_path,
        report_name=report_name,
        file_size=file_size,
        date_range_start=date_range_start,
        date_range_end=date_range_end
    )
    db.add(report_history)
    db.commit()
    db.refresh(report_history)
    return report_history.id

def get_user_file_history(user_id: int, limit: int = 100, db: Session = None) -> List[FileHistory]:
    """Get user's file history"""
    if db is None:
        from src.database import SessionLocal
        db = SessionLocal()
    return db.query(FileHistory).filter(
        FileHistory.user_id == user_id
    ).order_by(FileHistory.uploaded_at.desc()).limit(limit).all()

def get_user_report_history(user_id: int, limit: int = 100, db: Session = None) -> List[ReportHistory]:
    """Get user's report history"""
    if db is None:
        from src.database import SessionLocal
        db = SessionLocal()
    return db.query(ReportHistory).filter(
        ReportHistory.user_id == user_id
    ).order_by(ReportHistory.generated_at.desc()).limit(limit).all()

def get_file_reports(file_history_id: int, db: Session = None) -> List[ReportHistory]:
    """Get all reports for a file"""
    if db is None:
        from src.database import SessionLocal
        db = SessionLocal()
    return db.query(ReportHistory).filter(
        ReportHistory.file_history_id == file_history_id
    ).order_by(ReportHistory.generated_at.desc()).all()

def delete_report_history(report_id: int, db: Session) -> bool:
    """Delete a report from history"""
    report = db.query(ReportHistory).filter(ReportHistory.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
        return True
    return False

