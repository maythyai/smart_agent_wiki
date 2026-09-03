"""SQLAlchemy models for Notion connector sync state.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-10: Sync cursor persistence for resume capability.
Per NOTI-02: Database selection persistence.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, Index, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from saw.db.models import Base, generate_uuid
from saw.domain.utils import utcnow  # noqa: F401


class SyncDirection(enum.Enum):
    """Sync direction for Notion database."""
    PULL = "pull"
    PUSH = "push"
    BIDIRECTIONAL = "bidirectional"


class NotionSyncCursorModel(Base):
    """Per-database sync cursor for incremental sync.

    Per NOTI-10: Cursor persists after each sync for resume capability.

    Attributes:
        id: Unique cursor identifier.
        connector_id: FK to connector_configs.id.
        database_id: Notion database ID.
        cursor_token: Pagination cursor (nullable).
        last_sync_at: Last successful sync timestamp.
        last_page_edited_at: Max edited time in last batch.
        items_synced: Running count of synced items.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "notion_sync_cursor"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False, index=True
    )
    database_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cursor_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_page_edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    items_synced: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_notion_cursor_connector_db", "connector_id", "database_id", unique=True),
    )


class NotionDatabaseConfigModel(Base):
    """Selected Notion databases for sync.

    Per NOTI-02: Persist database selection with sync preferences.

    Attributes:
        id: Unique config identifier.
        connector_id: FK to connector_configs.id.
        database_id: Notion database ID.
        database_name: Cached database title.
        is_selected: Whether database is selected for sync.
        sync_direction: Sync direction (pull/push/bidirectional).
        property_mapping: Custom property to field mappings.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "notion_database_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False, index=True
    )
    database_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    database_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_direction: Mapped[SyncDirection] = mapped_column(
        SQLEnum(SyncDirection), default=SyncDirection.BIDIRECTIONAL
    )
    property_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_notion_db_config_connector_db", "connector_id", "database_id", unique=True),
    )
