"""File watcher using Watchdog library."""
import time
from pathlib import Path

from loguru import logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from moviecp.config import WatcherConfig
from moviecp.watcher.processor import FileProcessor
from moviecp.watcher.validator import FileValidator


class MovieFileHandler(FileSystemEventHandler):
    """Handles file system events for movie files."""

    def __init__(self, config: WatcherConfig):
        """
        Initialize file handler.

        Args:
            config: Watcher configuration.
        """
        super().__init__()
        self.config = config
        self.validator = FileValidator(config)
        self.processor = FileProcessor()

    def on_created(self, event):
        """Handle file creation event."""
        if event.is_directory:
            return

        file_path = event.src_path
        logger.debug(f"File created: {file_path}")

        self._process_file(file_path)

    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return

        file_path = event.src_path
        logger.debug(f"File modified: {file_path}")

        # Only process if it's a new file (not already in database)
        self._process_file(file_path)

    def _process_file(self, file_path: str):
        """
        Process a detected file.

        Args:
            file_path: Path to the file.
        """
        try:
            # Validate file
            if not self.validator.validate_file(file_path):
                logger.debug(f"File validation failed: {file_path}")
                return

            # Get file info
            file_info = self.validator.get_file_info(file_path)
            if not file_info:
                logger.warning(f"Could not get file info: {file_path}")
                return

            # Process file (add to database)
            result = self.processor.process_file(file_info)

            if result:
                logger.success(
                    f"Successfully processed new movie: {file_info['filename']} "
                    f"(ID: {result.id})"
                )
            else:
                logger.debug(f"File already processed or exists: {file_path}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")


class FileWatcher:
    """Watches directory for new movie files."""

    def __init__(self, config: WatcherConfig):
        """
        Initialize file watcher.

        Args:
            config: Watcher configuration.
        """
        self.config = config
        self.observer = Observer()
        self.event_handler = MovieFileHandler(config)

    def start(self):
        """Start watching the download folder."""
        watch_path = self.config.download_folder

        if not Path(watch_path).exists():
            raise FileNotFoundError(f"Download folder does not exist: {watch_path}")

        logger.info(f"Starting file watcher on: {watch_path}")
        logger.info(f"Recursive: {self.config.watch_recursive}")
        logger.info(f"Min file size: {self.config.min_file_size_mb} MB")
        logger.info(f"Supported extensions: {', '.join(self.config.supported_extensions)}")

        self.observer.schedule(
            self.event_handler,
            watch_path,
            recursive=self.config.watch_recursive,
        )

        self.observer.start()
        logger.success("File watcher started successfully")

    def stop(self):
        """Stop watching."""
        logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped")

    def run(self):
        """Run the watcher (blocking)."""
        self.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
