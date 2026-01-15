"""Helper utility functions."""
import os
from pathlib import Path
from typing import Optional


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted string (e.g., "1.5 GB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def is_video_file(file_path: str, supported_extensions: list) -> bool:
    """
    Check if file is a supported video file.

    Args:
        file_path: Path to file.
        supported_extensions: List of supported extensions (e.g., ['.mkv', '.mp4']).

    Returns:
        True if file has supported extension.
    """
    ext = Path(file_path).suffix.lower()
    return ext in [e.lower() for e in supported_extensions]


def ensure_directory(path: str) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def is_mount_accessible(mount_path: str) -> bool:
    """
    Check if mount path is accessible.

    Args:
        mount_path: Path to check.

    Returns:
        True if path exists and is accessible.
    """
    if not os.path.exists(mount_path):
        return False

    # Try to list directory to verify access
    try:
        os.listdir(mount_path)
        return True
    except (PermissionError, OSError):
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.
    Prevents path traversal attacks by removing path separators.

    Args:
        filename: Original filename.

    Returns:
        Sanitized filename.
    """
    # Remove any path components to prevent directory traversal
    filename = os.path.basename(filename)
    
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing spaces and dots
    filename = filename.strip().strip(".")
    
    # Prevent empty filename or dangerous names
    if not filename or filename in (".", "..", ""):
        filename = "sanitized_file"

    return filename
