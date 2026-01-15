"""Pydantic schemas for API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PendingMovieSchema(BaseModel):
    """Schema for pending movie."""

    id: int
    original_path: str
    original_filename: str
    file_size: int
    detected_at: Optional[datetime]
    status: str
    error_message: Optional[str] = None
    metadata: Optional[str] = None

    class Config:
        from_attributes = True


class ProcessedMovieSchema(BaseModel):
    """Schema for processed movie."""

    id: int
    original_path: str
    original_filename: str
    final_path: Optional[str]
    final_filename: Optional[str]
    file_size: int
    detected_at: Optional[datetime]
    processed_at: Optional[datetime]
    action: str
    version_number: int
    mnamer_output: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    """Schema for movie approval request."""

    delete_source: bool = False


class RejectRequest(BaseModel):
    """Schema for movie rejection request."""

    delete_source: bool = True


class StatsSchema(BaseModel):
    """Schema for statistics."""

    pending: int
    approved: int
    rejected: int
    total_processed: int


class ActionResponse(BaseModel):
    """Schema for action response."""

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None
