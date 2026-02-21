"""Database session management for the MVM backend."""
from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.orm_models import Base

# Reads DATABASE_URL from environment. Falls back to an in-process SQLite
# database so the application can still start during development/testing
# without a running PostgreSQL instance.
_DATABASE_URL: str = os.environ.get(
    "DATABASE_URL", "sqlite:///./mvm_dev.db"
)

# For SQLite we must pass check_same_thread=False; the argument is ignored
# for other dialects.
_connect_args: dict = (
    {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(_DATABASE_URL, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
