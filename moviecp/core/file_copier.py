"""File copying with streaming and verification."""
import os
import shutil
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from moviecp.config import NetworkShareConfig
from moviecp.utils.exceptions import FileCopyError, NetworkShareError
from moviecp.utils.helpers import ensure_directory, format_file_size, is_mount_accessible


class FileCopier:
    """Handles file copying to network share with verification."""

    def __init__(self, config: NetworkShareConfig):
        """
        Initialize file copier.

        Args:
            config: Network share configuration.
        """
        self.config = config
        self.chunk_size = 1024 * 1024  # 1 MB chunks

    def copy_file(self, source_path: str, filename: str) -> str:
        """
        Copy file to network share with verification.

        Args:
            source_path: Source file path.
            filename: Destination filename.

        Returns:
            Final destination path.

        Raises:
            FileCopyError: If copy fails.
            NetworkShareError: If network share is not accessible.
        """
        try:
            # Verify network share is accessible
            if self.config.verify_mount:
                if not is_mount_accessible(self.config.mount_path):
                    raise NetworkShareError(
                        f"Network share not accessible: {self.config.mount_path}"
                    )

            # Construct destination path
            dest_dir = os.path.join(self.config.mount_path, self.config.target_folder)
            ensure_directory(dest_dir)

            dest_path = os.path.join(dest_dir, filename)
            temp_path = dest_path + ".tmp"

            # Check if file already exists
            if os.path.exists(dest_path):
                logger.warning(f"Destination file already exists: {dest_path}")
                # Could optionally raise error or return existing path

            # Get source file size
            source_size = os.path.getsize(source_path)
            logger.info(
                f"Copying file: {os.path.basename(source_path)} "
                f"({format_file_size(source_size)}) -> {dest_path}"
            )

            # Copy with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Copy to temp file
                    self._stream_copy(source_path, temp_path)

                    # Verify copy
                    if not self._verify_copy(source_path, temp_path):
                        raise FileCopyError("File verification failed")

                    # Rename temp to final
                    os.rename(temp_path, dest_path)

                    logger.success(f"File copied successfully: {dest_path}")
                    return dest_path

                except Exception as e:
                    logger.warning(f"Copy attempt {attempt + 1} failed: {e}")

                    # Clean up temp file
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass

                    if attempt == max_retries - 1:
                        raise

                    # Wait before retry
                    time.sleep(2 ** attempt)  # Exponential backoff

            raise FileCopyError("All copy attempts failed")

        except NetworkShareError:
            raise

        except Exception as e:
            error_msg = f"Error copying file {source_path}: {e}"
            logger.error(error_msg)
            raise FileCopyError(error_msg)

    def _stream_copy(self, source_path: str, dest_path: str) -> None:
        """
        Stream copy file in chunks.

        Args:
            source_path: Source file path.
            dest_path: Destination file path.

        Raises:
            FileCopyError: If copy fails.
        """
        try:
            source_size = os.path.getsize(source_path)
            bytes_copied = 0

            with open(source_path, "rb") as source_file:
                with open(dest_path, "wb") as dest_file:
                    while True:
                        chunk = source_file.read(self.chunk_size)
                        if not chunk:
                            break

                        dest_file.write(chunk)
                        bytes_copied += len(chunk)

                        # Log progress
                        progress = (bytes_copied / source_size) * 100
                        if bytes_copied % (self.chunk_size * 100) == 0:  # Every 100 MB
                            logger.debug(
                                f"Copy progress: {progress:.1f}% "
                                f"({format_file_size(bytes_copied)} / "
                                f"{format_file_size(source_size)})"
                            )

            logger.debug(f"Stream copy completed: {format_file_size(bytes_copied)}")

        except Exception as e:
            raise FileCopyError(f"Stream copy failed: {e}")

    def _verify_copy(self, source_path: str, dest_path: str) -> bool:
        """
        Verify copied file matches source.

        Args:
            source_path: Source file path.
            dest_path: Destination file path.

        Returns:
            True if verification passes.
        """
        try:
            # Compare file sizes
            source_size = os.path.getsize(source_path)
            dest_size = os.path.getsize(dest_path)

            if source_size != dest_size:
                logger.error(
                    f"Size mismatch: source={source_size}, dest={dest_size}"
                )
                return False

            logger.debug("File verification passed (size match)")
            return True

        except Exception as e:
            logger.error(f"Error verifying file: {e}")
            return False

    def delete_source(self, source_path: str) -> bool:
        """
        Delete source file after successful copy.

        Args:
            source_path: Source file path to delete.

        Returns:
            True if deleted successfully.
        """
        try:
            if os.path.exists(source_path):
                os.remove(source_path)
                logger.info(f"Deleted source file: {source_path}")
                return True
            else:
                logger.warning(f"Source file not found: {source_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting source file {source_path}: {e}")
            return False
