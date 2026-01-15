"""REST API endpoints."""
from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger

from moviecp.core.movie_manager import MovieManager
from moviecp.schemas import (
    ActionResponse,
    ApproveRequest,
    PendingMovieSchema,
    ProcessedMovieSchema,
    RejectRequest,
    StatsSchema,
)

router = APIRouter(prefix="/api", tags=["api"])

# Global movie manager (will be set by app startup)
_movie_manager: MovieManager = None


def set_movie_manager(manager: MovieManager):
    """Set the global movie manager instance."""
    global _movie_manager
    _movie_manager = manager


def get_movie_manager() -> MovieManager:
    """Get the global movie manager instance."""
    if _movie_manager is None:
        raise RuntimeError("Movie manager not initialized")
    return _movie_manager


@router.get("/movies/pending", response_model=List[PendingMovieSchema])
async def get_pending_movies():
    """Get all pending movies."""
    try:
        manager = get_movie_manager()
        movies = manager.get_pending_movies()
        return movies
    except Exception as e:
        logger.error(f"Error getting pending movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movies/history", response_model=List[ProcessedMovieSchema])
async def get_processed_movies(limit: int = 50):
    """Get processed movies history."""
    try:
        manager = get_movie_manager()
        movies = manager.get_processed_movies(limit=limit)
        return movies
    except Exception as e:
        logger.error(f"Error getting processed movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/movies/{movie_id}/approve", response_model=ActionResponse)
async def approve_movie(movie_id: int, request: ApproveRequest = ApproveRequest()):
    """Approve a pending movie."""
    try:
        # Validate movie_id is positive
        if movie_id <= 0:
            return ActionResponse(success=False, error="Invalid movie ID")
        
        logger.info(f"API: Approving movie {movie_id}")
        manager = get_movie_manager()
        result = manager.approve_movie(movie_id, delete_source=request.delete_source)

        if result["success"]:
            return ActionResponse(
                success=True,
                message=f"Movie approved: {result['final_filename']}",
                data=result,
            )
        else:
            return ActionResponse(success=False, error=result.get("error"))

    except Exception as e:
        logger.error(f"Error approving movie {movie_id}: {e}")
        # Don't expose internal error details to client
        return ActionResponse(success=False, error="Failed to approve movie")


@router.post("/movies/{movie_id}/reject", response_model=ActionResponse)
async def reject_movie(movie_id: int, request: RejectRequest = RejectRequest()):
    """Reject a pending movie."""
    try:
        # Validate movie_id is positive
        if movie_id <= 0:
            return ActionResponse(success=False, error="Invalid movie ID")
        
        logger.info(f"API: Rejecting movie {movie_id}")
        manager = get_movie_manager()
        result = manager.reject_movie(movie_id, delete_source=request.delete_source)

        if result["success"]:
            return ActionResponse(
                success=True,
                message=f"Movie rejected: {result['original_filename']}",
                data=result,
            )
        else:
            return ActionResponse(success=False, error=result.get("error"))

    except Exception as e:
        logger.error(f"Error rejecting movie {movie_id}: {e}")
        # Don't expose internal error details to client
        return ActionResponse(success=False, error="Failed to reject movie")


@router.get("/stats", response_model=StatsSchema)
async def get_stats():
    """Get statistics."""
    try:
        manager = get_movie_manager()
        stats = manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "MovieCP"}
