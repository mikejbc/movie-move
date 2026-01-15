"""Configuration management for MovieCP daemon."""
import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class WatcherConfig(BaseModel):
    """File watcher configuration."""
    download_folder: str
    watch_recursive: bool = True
    min_file_size_mb: int = 500
    stable_time_seconds: int = 30
    supported_extensions: List[str] = [".mkv", ".mp4", ".avi", ".m4v", ".mov", ".wmv", ".flv"]
    exclude_patterns: List[str] = ["*.part", "*.tmp", "*.downloading"]

    @field_validator("download_folder")
    @classmethod
    def validate_download_folder(cls, v: str) -> str:
        """Validate download folder exists."""
        if not os.path.exists(v):
            raise ValueError(f"Download folder does not exist: {v}")
        if not os.path.isdir(v):
            raise ValueError(f"Download folder is not a directory: {v}")
        return v


class NetworkShareConfig(BaseModel):
    """Network share configuration."""
    mount_path: str
    target_folder: str = "Movies"
    auto_mount: bool = False
    verify_mount: bool = True

    @field_validator("mount_path")
    @classmethod
    def validate_mount_path(cls, v: str) -> str:
        """Validate mount path exists."""
        if not os.path.exists(v):
            raise ValueError(f"Mount path does not exist: {v}")
        return v


class MnamerConfig(BaseModel):
    """mnamer tool configuration."""
    executable_path: str = "mnamer"
    batch_mode: bool = True
    movie_directory: str = ""
    media_type: str = "movie"
    movie_format: str = "{name} ({year})"
    extra_args: List[str] = ["--no-cache"]


class VersionDetectionConfig(BaseModel):
    """Version detection configuration."""
    enabled: bool = True
    format: str = ".v{number}"
    check_similar: bool = True
    similarity_threshold: float = 0.9


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "/var/lib/moviecp/moviecp.db"
    backup_enabled: bool = True
    backup_path: str = "/var/lib/moviecp/backups"
    backup_retention_days: int = 30


class WebConfig(BaseModel):
    """Web dashboard configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    enable_auth: bool = False
    cors_origins: List[str] = ["*"]
    session_secret: str = "CHANGE_ME_IN_PRODUCTION"


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "/var/log/moviecp/moviecp.log"
    max_size_mb: int = 10
    backup_count: int = 5
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


class ApplicationConfig(BaseModel):
    """Main application configuration."""
    name: str = "MovieCP Daemon"
    environment: str = "production"


class Config(BaseModel):
    """Root configuration model."""
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    watcher: WatcherConfig
    network_share: NetworkShareConfig
    mnamer: MnamerConfig = Field(default_factory=MnamerConfig)
    version_detection: VersionDetectionConfig = Field(default_factory=VersionDetectionConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, searches in standard locations.

    Returns:
        Config object with validated settings.

    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If config validation fails.
    """
    if config_path is None:
        # Search for config in standard locations
        search_paths = [
            "config/config.yaml",
            "/etc/moviecp/config.yaml",
            os.path.expanduser("~/.config/moviecp/config.yaml"),
        ]

        for path in search_paths:
            if os.path.exists(path):
                config_path = path
                break

        if config_path is None:
            raise FileNotFoundError(
                f"Config file not found in any of: {', '.join(search_paths)}"
            )

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global config instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: Config) -> None:
    """Set the global config instance."""
    global _config
    _config = config
