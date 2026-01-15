"""File validation logic."""
import os
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from moviecp.config import WatcherConfig
from moviecp.utils.exceptions import FileValidationError
from moviecp.utils.helpers import is_video_file


class FileValidator:
    """Validates files before processing."""

    def __init__(self, config: WatcherConfig):
        """
        Initialize file validator.

        Args:
            config: Watcher configuration.
        """
        self.config = config
        self.min_file_size_bytes = config.min_file_size_mb * 1024 * 1024
        self.stable_time_seconds = config.stable_time_seconds

    def validate_file(self, file_path: str) -> bool:
        """
        Validate if file meets all criteria for processing.

        Args:
            file_path: Path to file to validate.

        Returns:
            True if file is valid, False otherwise.

        Raises:
            FileValidationError: If validation fails with error.
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.debug(f"File does not exist: {file_path}")
                return False

            # Check if it's a file (not directory)
            if not os.path.isfile(file_path):
                logger.debug(f"Not a file: {file_path}")
                return False

            # Check if file matches exclude patterns
            if self._matches_exclude_pattern(file_path):
                logger.debug(f"File matches exclude pattern: {file_path}")
                return False

            # Check if supported video format
            if not is_video_file(file_path, self.config.supported_extensions):
                logger.debug(f"Unsupported file format: {file_path}")
                return False

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size < self.min_file_size_bytes:
                logger.debug(
                    f"File too small ({file_size} bytes < {self.min_file_size_bytes} bytes): {file_path}"
                )
                return False

            # Check if file is stable (not being written)
            if not self._is_file_stable(file_path):
                logger.debug(f"File is still being written: {file_path}")
                return False

            logger.info(f"File validation passed: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            raise FileValidationError(f"Failed to validate file: {e}")

    def _matches_exclude_pattern(self, file_path: str) -> bool:
        """
        Check if file matches any exclude pattern.

        Args:
            file_path: Path to file.

        Returns:
            True if file matches exclude pattern.
        """
        filename = os.path.basename(file_path)

        for pattern in self.config.exclude_patterns:
            # Simple wildcard matching
            if pattern.startswith("*") and filename.endswith(pattern[1:]):
                return True
            elif pattern.endswith("*") and filename.startswith(pattern[:-1]):
                return True
            elif pattern == filename:
                return True

        return False

    def _is_file_stable(self, file_path: str) -> bool:
        """
        Check if file size is stable (not being written).

        Args:
            file_path: Path to file.

        Returns:
            True if file size hasn't changed for configured duration.
        """
        try:
            # Get initial size
            initial_size = os.path.getsize(file_path)

            # Wait for configured duration
            time.sleep(self.stable_time_seconds)

            # Check size again
            final_size = os.path.getsize(file_path)

            return initial_size == final_size

        except (FileNotFoundError, OSError) as e:
            logger.warning(f"Could not check file stability for {file_path}: {e}")
            return False

    def get_file_info(self, file_path: str) -> dict:
        """
        Extract file information.

        Args:
            file_path: Path to file.

        Returns:
            Dictionary with file information.
        """
        try:
            stat = os.stat(file_path)

            return {
                "path": file_path,
                "filename": os.path.basename(file_path),
                "size": stat.st_size,
                "extension": Path(file_path).suffix,
                "modified_time": stat.st_mtime,
            }

        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
