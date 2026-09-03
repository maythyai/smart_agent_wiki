"""SQLite connection factory with WAL mode and PRAGMA configuration.

Per D-02: WAL mode for concurrent read/write, optimized PRAGMAs.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import event
from sqlmodel import create_engine


def _set_pragma(dbapi_connection, connection_record) -> None:
    """Set all SQLite PRAGMAs on each new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-64000")       # 64MB
    cursor.execute("PRAGMA mmap_size=67108864")       # 64MB
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")        # 5s lock wait
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_wiki_engine(db_path: Path):
    """Create an optimized SQLite engine with WAL mode and PRAGMAs.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        SQLModel/SQLAlchemy engine instance.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    url = f"sqlite:///{db_path}"

    engine = create_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    event.listens_for(engine, "connect")(_set_pragma)

    return engine
