"""Main entry point for MovieCP daemon."""
import argparse
import signal
import sys

from loguru import logger

from moviecp.config import load_config
from moviecp.database import close_database, init_database
from moviecp.utils.logger import setup_logging


def run_watcher(config_path=None):
    """Run the file watcher service."""
    from moviecp.watcher.file_watcher import FileWatcher

    try:
        # Load configuration
        config = load_config(config_path)

        # Setup logging
        setup_logging(config.logging)

        # Initialize database
        init_database(config.database.path)

        # Create and start file watcher
        watcher = FileWatcher(config.watcher)

        # Handle signals for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            watcher.stop()
            close_database()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run watcher
        logger.info("Starting MovieCP file watcher...")
        watcher.run()

    except Exception as e:
        logger.error(f"Error running watcher: {e}")
        sys.exit(1)


def run_web(config_path=None):
    """Run the web dashboard service."""
    import uvicorn

    try:
        # Load configuration
        config = load_config(config_path)

        # Setup logging
        setup_logging(config.logging)

        # Initialize database
        init_database(config.database.path)

        logger.info("Starting MovieCP web dashboard...")

        # Run uvicorn server
        uvicorn.run(
            "moviecp.web.app:app",
            host=config.web.host,
            port=config.web.port,
            log_level=config.logging.level.lower(),
        )

    except Exception as e:
        logger.error(f"Error running web server: {e}")
        sys.exit(1)


def init_db(config_path=None):
    """Initialize database."""
    try:
        config = load_config(config_path)
        setup_logging(config.logging)

        logger.info(f"Initializing database at: {config.database.path}")
        init_database(config.database.path)
        logger.success("Database initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MovieCP - Movie Copy Daemon")
    parser.add_argument(
        "command",
        choices=["watcher", "web", "init-db"],
        help="Command to run: watcher (file monitoring), web (dashboard), init-db (initialize database)",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to configuration file",
        default=None,
    )

    args = parser.parse_args()

    if args.command == "watcher":
        run_watcher(args.config)
    elif args.command == "web":
        run_web(args.config)
    elif args.command == "init-db":
        init_db(args.config)


if __name__ == "__main__":
    main()
