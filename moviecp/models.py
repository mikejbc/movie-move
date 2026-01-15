"""Database models for MovieCP."""
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class PendingMovie(Base):
    """Model for movies pending approval."""

    __tablename__ = "pending_movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_path = Column(String, nullable=False, unique=True)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    status = Column(
        String,
        default="pending",
        nullable=False,
    )
    error_message = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string

    __table_args__ = (
        CheckConstraint(
            status.in_(["pending", "approved", "rejected", "processing", "completed", "failed"]),
            name="pending_movies_status_check",
        ),
    )

    def __repr__(self) -> str:
        return f"<PendingMovie(id={self.id}, filename='{self.original_filename}', status='{self.status}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "original_path": self.original_path,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "status": self.status,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class ProcessedMovie(Base):
    """Model for processed movies history."""

    __tablename__ = "processed_movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    final_path = Column(String, nullable=True)
    final_filename = Column(String, nullable=True)
    file_size = Column(Integer, nullable=False)
    detected_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    action = Column(String, nullable=False)  # approved or rejected
    version_number = Column(Integer, default=1)
    mnamer_output = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            action.in_(["approved", "rejected"]),
            name="processed_movies_action_check",
        ),
    )

    def __repr__(self) -> str:
        return f"<ProcessedMovie(id={self.id}, filename='{self.final_filename}', action='{self.action}')>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "original_path": self.original_path,
            "original_filename": self.original_filename,
            "final_path": self.final_path,
            "final_filename": self.final_filename,
            "file_size": self.file_size,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "action": self.action,
            "version_number": self.version_number,
            "mnamer_output": self.mnamer_output,
            "notes": self.notes,
        }
