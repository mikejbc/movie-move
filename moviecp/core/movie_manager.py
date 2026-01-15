"""Movie manager - orchestrates approval/rejection workflow."""
import os
from datetime import datetime
from typing import Optional

from loguru import logger

from moviecp.config import Config
from moviecp.core.file_copier import FileCopier
from moviecp.core.renamer import MovieRenamer
from moviecp.core.version_detector import VersionDetector
from moviecp.database import get_db_session
from moviecp.models import PendingMovie, ProcessedMovie
from moviecp.utils.exceptions import FileCopyError, MnamerError, NetworkShareError


class MovieManager:
    """Manages movie approval and rejection workflow."""

    def __init__(self, config: Config):
        """
        Initialize movie manager.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.renamer = MovieRenamer(config.mnamer)
        self.version_detector = VersionDetector(config.version_detection)
        self.file_copier = FileCopier(config.network_share)

    def approve_movie(self, movie_id: int, delete_source: bool = False) -> dict:
        """
        Approve and process a movie.

        Args:
            movie_id: ID of the pending movie.
            delete_source: Whether to delete source file after copy.

        Returns:
            Dictionary with result information.

        Raises:
            Various exceptions if processing fails.
        """
        logger.info(f"Starting approval process for movie ID: {movie_id}")

        with get_db_session() as session:
            # Get pending movie
            movie = session.query(PendingMovie).filter_by(id=movie_id).first()

            if not movie:
                error_msg = f"Movie with ID {movie_id} not found"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            if movie.status != "pending":
                error_msg = f"Movie is not pending (status: {movie.status})"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            # Update status to processing
            movie.status = "processing"
            session.commit()

        try:
            # Step 1: Run mnamer to get new filename
            logger.info("Step 1: Running mnamer...")
            new_filename, mnamer_output = self.renamer.rename_movie(movie.original_path)

            if not new_filename:
                raise MnamerError("mnamer failed to generate new filename")

            # Step 2: Check for existing versions
            logger.info("Step 2: Checking for existing versions...")
            target_dir = os.path.join(
                self.config.network_share.mount_path,
                self.config.network_share.target_folder,
            )
            versioned_filename, version_number = self.version_detector.detect_version(
                new_filename, target_dir
            )

            # Step 3: Copy file to network share
            logger.info("Step 3: Copying file to network share...")
            final_path = self.file_copier.copy_file(
                movie.original_path, versioned_filename
            )

            # Step 4: Update database
            logger.info("Step 4: Updating database...")
            with get_db_session() as session:
                # Remove from pending
                pending_movie = session.query(PendingMovie).filter_by(id=movie_id).first()

                if pending_movie:
                    # Create processed record
                    processed = ProcessedMovie(
                        original_path=pending_movie.original_path,
                        original_filename=pending_movie.original_filename,
                        final_path=final_path,
                        final_filename=versioned_filename,
                        file_size=pending_movie.file_size,
                        detected_at=pending_movie.detected_at,
                        processed_at=datetime.utcnow(),
                        action="approved",
                        version_number=version_number,
                        mnamer_output=mnamer_output,
                    )

                    session.add(processed)
                    session.delete(pending_movie)
                    session.commit()

            # Step 5: Optionally delete source
            if delete_source:
                logger.info("Step 5: Deleting source file...")
                self.file_copier.delete_source(movie.original_path)

            result = {
                "success": True,
                "original_filename": movie.original_filename,
                "final_filename": versioned_filename,
                "final_path": final_path,
                "version_number": version_number,
            }

            logger.success(f"Movie approved successfully: {versioned_filename}")
            return result

        except (MnamerError, FileCopyError, NetworkShareError) as e:
            # Update status to failed
            logger.error(f"Error processing movie {movie_id}: {e}")

            with get_db_session() as session:
                failed_movie = session.query(PendingMovie).filter_by(id=movie_id).first()
                if failed_movie:
                    failed_movie.status = "failed"
                    failed_movie.error_message = str(e)
                    session.commit()

            return {"success": False, "error": str(e)}

        except Exception as e:
            logger.error(f"Unexpected error processing movie {movie_id}: {e}")

            with get_db_session() as session:
                failed_movie = session.query(PendingMovie).filter_by(id=movie_id).first()
                if failed_movie:
                    failed_movie.status = "failed"
                    failed_movie.error_message = str(e)
                    session.commit()

            return {"success": False, "error": f"Unexpected error: {e}"}

    def reject_movie(self, movie_id: int, delete_source: bool = True) -> dict:
        """
        Reject a movie.

        Args:
            movie_id: ID of the pending movie.
            delete_source: Whether to delete source file.

        Returns:
            Dictionary with result information.
        """
        logger.info(f"Rejecting movie ID: {movie_id}")

        try:
            with get_db_session() as session:
                # Get pending movie
                movie = session.query(PendingMovie).filter_by(id=movie_id).first()

                if not movie:
                    error_msg = f"Movie with ID {movie_id} not found"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}

                # Create processed record
                processed = ProcessedMovie(
                    original_path=movie.original_path,
                    original_filename=movie.original_filename,
                    file_size=movie.file_size,
                    detected_at=movie.detected_at,
                    processed_at=datetime.utcnow(),
                    action="rejected",
                    notes="Rejected by user",
                )

                session.add(processed)
                session.delete(movie)
                session.commit()

            # Optionally delete source
            if delete_source:
                self.file_copier.delete_source(movie.original_path)

            logger.success(f"Movie rejected: {movie.original_filename}")

            return {
                "success": True,
                "original_filename": movie.original_filename,
            }

        except Exception as e:
            logger.error(f"Error rejecting movie {movie_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_pending_movies(self) -> list:
        """
        Get all pending movies.

        Returns:
            List of pending movie dictionaries.
        """
        try:
            with get_db_session() as session:
                movies = (
                    session.query(PendingMovie)
                    .filter_by(status="pending")
                    .order_by(PendingMovie.detected_at.desc())
                    .all()
                )

                return [movie.to_dict() for movie in movies]

        except Exception as e:
            logger.error(f"Error retrieving pending movies: {e}")
            return []

    def get_processed_movies(self, limit: int = 50) -> list:
        """
        Get processed movies history.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of processed movie dictionaries.
        """
        try:
            with get_db_session() as session:
                movies = (
                    session.query(ProcessedMovie)
                    .order_by(ProcessedMovie.processed_at.desc())
                    .limit(limit)
                    .all()
                )

                return [movie.to_dict() for movie in movies]

        except Exception as e:
            logger.error(f"Error retrieving processed movies: {e}")
            return []

    def get_stats(self) -> dict:
        """
        Get statistics.

        Returns:
            Dictionary with statistics.
        """
        try:
            with get_db_session() as session:
                pending_count = session.query(PendingMovie).filter_by(status="pending").count()
                approved_count = session.query(ProcessedMovie).filter_by(action="approved").count()
                rejected_count = session.query(ProcessedMovie).filter_by(action="rejected").count()

                return {
                    "pending": pending_count,
                    "approved": approved_count,
                    "rejected": rejected_count,
                    "total_processed": approved_count + rejected_count,
                }

        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "total_processed": 0,
            }
