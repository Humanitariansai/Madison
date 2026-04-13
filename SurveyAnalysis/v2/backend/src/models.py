"""
SQLAlchemy database models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    file_history = relationship("FileHistory", back_populates="user")
    report_history = relationship("ReportHistory", back_populates="user")

class FileHistory(Base):
    __tablename__ = "file_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    rows_count = Column(Integer)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="file_history")
    reports = relationship("ReportHistory", back_populates="file_history")

class ReportHistory(Base):
    __tablename__ = "report_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_history_id = Column(Integer, ForeignKey("file_history.id"), nullable=True)
    report_type = Column(String, nullable=False)  # 'pdf', 'csv', 'json'
    report_path = Column(String, nullable=False)
    report_name = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="report_history")
    file_history = relationship("FileHistory", back_populates="reports")

