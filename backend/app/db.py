"""Database engine, session factory and FastAPI dependency."""

from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_SQLITE_PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA foreign_keys=ON",
    "PRAGMA busy_timeout=5000",
    "PRAGMA synchronous=NORMAL",
)


def _set_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        for pragma in _SQLITE_PRAGMAS:
            cursor.execute(pragma)
    finally:
        cursor.close()


def make_engine(url: str) -> Engine:
    """Create an engine; SQLite engines get the required pragmas on every connection."""
    if url.startswith("sqlite"):
        eng = create_engine(url, connect_args={"check_same_thread": False})
        event.listen(eng, "connect", _set_sqlite_pragmas)
        return eng
    return create_engine(url)


engine = make_engine(get_settings().database_url)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db(session: Session) -> bool:
    """Return True if the database answers SELECT 1."""
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
