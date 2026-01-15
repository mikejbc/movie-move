"""Custom exceptions for MovieCP."""


class MovieCPException(Exception):
    """Base exception for MovieCP."""

    pass


class ConfigurationError(MovieCPException):
    """Raised when configuration is invalid."""

    pass


class DatabaseError(MovieCPException):
    """Raised when database operation fails."""

    pass


class FileValidationError(MovieCPException):
    """Raised when file validation fails."""

    pass


class NetworkShareError(MovieCPException):
    """Raised when network share operations fail."""

    pass


class MnamerError(MovieCPException):
    """Raised when mnamer operation fails."""

    pass


class FileCopyError(MovieCPException):
    """Raised when file copy operation fails."""

    pass


class VersionDetectionError(MovieCPException):
    """Raised when version detection fails."""

    pass
