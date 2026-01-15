"""Logging configuration for MovieCP."""
import sys
from pathlib import Path

from loguru import logger

from moviecp.config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """
    Configure logging for the application.

    Args:
        config: Logging configuration.
    """
    # Remove default handler
    logger.remove()

    # Create log directory if it doesn't exist
    log_file = Path(config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Add console handler
    logger.add(
        sys.stderr,
        format=config.format,
        level=config.level,
        colorize=True,
    )

    # Add file handler with rotation
    logger.add(
        config.file,
        format=config.format,
        level=config.level,
        rotation=f"{config.max_size_mb} MB",
        retention=config.backup_count,
        compression="zip",
    )

    logger.info("Logging initialized")


def get_logger(name: str = None):
    """Get a logger instance."""
    if name:
        return logger.bind(name=name)
    return logger
