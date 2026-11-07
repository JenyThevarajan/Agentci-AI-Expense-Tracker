"""SQLite engine and session factory."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import database_path, sqlite_url
from app.models import Base

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def init_db() -> None:
    """Open the configured SQLite file and create the expenses table if needed."""
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = create_engine(
        sqlite_url(database_path()),
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(_engine)


def get_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        init_db()
    assert SessionLocal is not None
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
