"""Database connection and session management."""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from moviecp.models import Base

# Global engine and session factory
_engine = None
_session_factory = None


def init_database(db_path: str, echo: bool = False) -> None:
    """
    Initialize database connection and create tables.

    Args:
        db_path: Path to SQLite database file.
        echo: Whether to echo SQL statements (for debugging).
    """
    global _engine, _session_factory

    # Create directory if it doesn't exist
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # Create engine with WAL mode for better concurrent access
    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=echo,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable WAL mode for better concurrency
    with _engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.commit()

    # Create all tables
    Base.metadata.create_all(_engine)

    # Create session factory
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)


def get_engine():
    """Get the global database engine."""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session_factory():
    """Get the global session factory."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        SQLAlchemy session.

    Example:
        with get_db_session() as session:
            movie = session.query(PendingMovie).first()
            print(movie)
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_session() -> Session:
    """
    Create a new database session.

    Returns:
        SQLAlchemy session.

    Note:
        Caller is responsible for closing the session.
        Prefer using get_db_session() context manager instead.
    """
    session_factory = get_session_factory()
    return session_factory()


def close_database() -> None:
    """Close database connection and cleanup resources."""
    global _engine, _session_factory

    if _engine is not None:
        _engine.dispose()
        _engine = None

    _session_factory = None
