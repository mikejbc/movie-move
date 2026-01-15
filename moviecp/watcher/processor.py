"""File processing logic - adds validated files to database."""
import json
from typing import Optional

from loguru import logger
from sqlalchemy.exc import IntegrityError

from moviecp.database import get_db_session
from moviecp.models import PendingMovie
from moviecp.utils.exceptions import DatabaseError


class FileProcessor:
    """Processes validated files and adds them to the database."""

    def process_file(self, file_info: dict) -> Optional[PendingMovie]:
        """
        Process a validated file and add it to the pending movies table.

        Args:
            file_info: Dictionary with file information from validator.

        Returns:
            PendingMovie object if successful, None if file already exists.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            with get_db_session() as session:
                # Check if file already exists in pending movies
                existing = (
                    session.query(PendingMovie)
                    .filter_by(original_path=file_info["path"])
                    .first()
                )

                if existing:
                    logger.info(
                        f"File already in database: {file_info['filename']} "
                        f"(status: {existing.status})"
                    )
                    return None

                # Create metadata JSON
                metadata = {
                    "extension": file_info.get("extension", ""),
                    "modified_time": file_info.get("modified_time", 0),
                }

                # Create new pending movie record
                pending_movie = PendingMovie(
                    original_path=file_info["path"],
                    original_filename=file_info["filename"],
                    file_size=file_info["size"],
                    status="pending",
                    file_metadata=json.dumps(metadata),
                )

                session.add(pending_movie)
                session.commit()
                session.refresh(pending_movie)

                logger.info(
                    f"Added new movie to database: {file_info['filename']} "
                    f"(ID: {pending_movie.id}, Size: {file_info['size']} bytes)"
                )

                return pending_movie

        except IntegrityError as e:
            logger.warning(f"File already exists in database: {file_info['path']}")
            return None

        except Exception as e:
            logger.error(f"Error processing file {file_info['path']}: {e}")
            raise DatabaseError(f"Failed to add file to database: {e}")

    def update_status(
        self, movie_id: int, status: str, error_message: Optional[str] = None
    ) -> bool:
        """
        Update status of a pending movie.

        Args:
            movie_id: ID of the movie to update.
            status: New status value.
            error_message: Optional error message if status is 'failed'.

        Returns:
            True if updated successfully, False otherwise.

        Raises:
            DatabaseError: If database operation fails.
        """
        try:
            with get_db_session() as session:
                movie = session.query(PendingMovie).filter_by(id=movie_id).first()

                if not movie:
                    logger.warning(f"Movie with ID {movie_id} not found")
                    return False

                movie.status = status
                if error_message:
                    movie.error_message = error_message

                session.commit()

                logger.info(f"Updated movie {movie_id} status to: {status}")
                return True

        except Exception as e:
            logger.error(f"Error updating movie {movie_id} status: {e}")
            raise DatabaseError(f"Failed to update movie status: {e}")

    def get_pending_movies(self) -> list:
        """
        Get all pending movies from the database.

        Returns:
            List of PendingMovie objects with status 'pending'.
        """
        try:
            with get_db_session() as session:
                movies = (
                    session.query(PendingMovie)
                    .filter_by(status="pending")
                    .order_by(PendingMovie.detected_at.desc())
                    .all()
                )

                # Detach from session to avoid issues
                return [
                    session.merge(movie, load=False) for movie in movies
                ]

        except Exception as e:
            logger.error(f"Error retrieving pending movies: {e}")
            return []
