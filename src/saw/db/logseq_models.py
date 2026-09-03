"""SQLAlchemy models for Logseq sync state.

Plan 13-01 Task 1: Database models for Logseq connector.
Per LOGS-06: System detects concurrent edits (file hash comparison).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

# Use the same Base as other models
from saw.db.models import Base
from saw.domain.utils import utcnow  # noqa: F401


class LogseqFileHashModel(Base):
    """File hash tracking for change detection.

    Per LOGS-06: System detects concurrent edits via file hash comparison.
    Per T-13-01: Track file paths to detect modifications.

    Attributes:
        id: Unique identifier.
        file_path: Relative path within graph (indexed).
        content_hash: SHA-256 hash of file content.
        updated_at: Last hash update timestamp.
    """

    __tablename__ = "logseq_file_hashes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_logseq_file_hashes_path_hash", "file_path", "content_hash"),
    )


class LogseqSyncStateModel(Base):
    """Sync state tracking per graph.

    Per LOGS-01: Track sync state per configured graph.

    Attributes:
        id: Unique identifier.
        graph_path: Path to the Logseq graph (indexed).
        last_sync_at: Timestamp of last successful sync.
        sync_cursor: Cursor for incremental sync (file path or timestamp).
        files_synced: Count of files synced.
        blocks_synced: Count of blocks synced.
    """

    __tablename__ = "logseq_sync_states"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    graph_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True, unique=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_cursor: Mapped[str | None] = mapped_column(String(512), nullable=True)
    files_synced: Mapped[int] = mapped_column(Integer, default=0)
    blocks_synced: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_logseq_sync_states_graph", "graph_path"),
    )
