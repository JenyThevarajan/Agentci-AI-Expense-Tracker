"""Runtime configuration. Database location comes from the environment, not a committed file."""

import os
from pathlib import Path

DEFAULT_DATABASE_PATH = "data/expenses.sqlite"


def database_path() -> Path:
    """Return the SQLite file path, creating its parent directory when needed."""
    configured = os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)
    path = Path(configured)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def sqlite_url(path: Path) -> str:
    """Build a SQLite URL from an absolute path so Windows separators stay valid."""
    return "sqlite:///" + path.resolve().as_posix()
