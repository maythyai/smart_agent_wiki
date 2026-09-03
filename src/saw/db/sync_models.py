"""SQLAlchemy models for sync state persistence.

Plan 11-01: Sync engine core with conflict detection.
Per SYNC-03: All sync operations logged with timestamp, direction, item count.
Per ERRO-04: Error details preserved for data integrity tracking.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from saw.db.models import Base, generate_uuid
from saw.domain.utils import utcnow  # noqa: F401


class SyncStateModel(Base):
    """Per-connector sync state tracking.

    Per SYNC-02: Track last_sync_at per connector for conflict detection.

    Attributes:
        id: Unique state identifier.
        connector_id: FK to connector_configs.id.
        platform: Platform name (denormalized for queries).
        last_sync_at: Last successful sync timestamp.
        last_sync_cursor: Pagination cursor for incremental sync.
        last_error: Last error message.
        last_error_at: Last error timestamp.
        items_synced_total: Total items synced (cumulative).
        sync_in_progress: Whether sync is currently running.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "sync_state"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False, unique=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_cursor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    items_synced_total: Mapped[int] = mapped_column(Integer, default=0)
    sync_in_progress: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_sync_state_connector", "connector_id"),
        Index("ix_sync_state_platform", "platform"),
    )


class SyncLogModel(Base):
    """Audit log for all sync operations.

    Per SYNC-03: All sync operations logged with timestamp, direction, item count.

    Attributes:
        id: Auto-increment log identifier.
        connector_id: FK to connector_configs.id.
        platform: Platform name.
        direction: Sync direction (pull, push, bidirectional).
        started_at: When sync started.
        completed_at: When sync completed.
        status: Sync outcome (success, partial, failed).
        items_pulled: Number of items pulled.
        items_pushed: Number of items pushed.
        items_skipped: Number of items skipped (loop detection, etc.).
        error_message: Error details if failed.
        metadata: Additional JSON metadata.
    """

    __tablename__ = "sync_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # pull, push, bidirectional
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, partial, failed
    items_pulled: Mapped[int] = mapped_column(Integer, default=0)
    items_pushed: Mapped[int] = mapped_column(Integer, default=0)
    items_skipped: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("ix_sync_log_connector_started", "connector_id", "started_at"),
        Index("ix_sync_log_platform_status", "platform", "status"),
    )


class ConflictRecordModel(Base):
    """Records of detected conflicts during sync.

    Per ERRO-04: Record conflicts for data integrity tracking.

    Attributes:
        id: Auto-increment conflict identifier.
        connector_id: FK to connector_configs.id.
        platform_item_id: Platform's item ID.
        saw_claim_id: SAW's claim ID.
        platform_modified_at: Platform modification timestamp.
        saw_modified_at: SAW modification timestamp.
        resolution: How conflict was resolved (platform_wins, saw_wins, manual).
        resolved_at: When resolution occurred.
        created_at: When conflict was detected.
    """

    __tablename__ = "conflict_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False
    )
    platform_item_id: Mapped[str] = mapped_column(String(255), nullable=False)
    saw_claim_id: Mapped[str] = mapped_column(String(36), nullable=False)
    platform_modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    saw_modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolution: Mapped[str] = mapped_column(String(50), nullable=False)  # platform_wins, saw_wins, manual
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_conflict_record_connector", "connector_id"),
        Index("ix_conflict_record_platform_item", "platform_item_id"),
    )
