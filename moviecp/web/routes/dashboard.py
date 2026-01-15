"""Dashboard page routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from moviecp.web.routes.api import get_movie_manager

router = APIRouter(tags=["dashboard"])

# Templates will be set by the app
templates: Jinja2Templates = None


def set_templates(tmpl: Jinja2Templates):
    """Set the templates instance."""
    global templates
    templates = tmpl


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    try:
        manager = get_movie_manager()
        stats = manager.get_stats()

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "stats": stats,
            },
        )
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return templates.TemplateResponse(
            "error.html" if templates else "dashboard.html",
            {
                "request": request,
                "error": str(e),
            },
        )
