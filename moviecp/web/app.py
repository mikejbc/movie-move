"""FastAPI application."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from moviecp.config import get_config
from moviecp.core.movie_manager import MovieManager
from moviecp.web.routes import api, dashboard

# Create FastAPI app
app = FastAPI(
    title="MovieCP",
    description="Movie Copy Daemon - Web Dashboard",
    version="1.0.0",
)

# Global config and manager
_config = None
_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    global _config, _manager

    try:
        # Load configuration
        _config = get_config()

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_config.web.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Initialize movie manager
        _manager = MovieManager(_config)
        api.set_movie_manager(_manager)

        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        templates = Jinja2Templates(directory=str(template_dir))
        dashboard.set_templates(templates)

        # Mount static files
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        logger.info("FastAPI app initialized successfully")

    except Exception as e:
        logger.error(f"Error during app startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("FastAPI app shutting down")


# Include routers
app.include_router(api.router)
app.include_router(dashboard.router)
