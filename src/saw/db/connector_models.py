"""SQLAlchemy models for connector persistence.

Plan 10-01: Connector database models.
Per AUTH-02: OAuth tokens encrypted at rest.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from saw.db.models import Base, generate_uuid


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class ConnectorConfigModel(Base):
    """SQLAlchemy model for connector configuration.

    Per AUTH-02: OAuth tokens encrypted at rest using Fernet.

    Attributes:
        id: Unique configuration identifier.
        user_id: Owner user ID (FK to users).
        platform: Platform identifier (notion, slack, github, etc.).
        name: User-defined name for this connection.
        credentials_encrypted: Encrypted OAuth tokens (Fernet).
        sync_direction: Direction of synchronization.
        last_sync_at: Timestamp of last successful sync.
        sync_interval: Seconds between syncs.
        is_active: Whether sync is enabled.
        config: Platform-specific configuration JSON.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "connector_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sync_direction: Mapped[str] = mapped_column(String(20), default="bidirectional")
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_interval: Mapped[int] = mapped_column(Integer, default=3600)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_connector_configs_user_platform", "user_id", "platform"),
    )


class ConnectorSyncLog(Base):
    """SQLAlchemy model for sync operation logging.

    Attributes:
        id: Unique log identifier.
        config_id: Connector config ID (FK to connector_configs).
        direction: Direction of sync (pull, push, bidirectional, webhook).
        items_pulled: Number of items pulled.
        items_pushed: Number of items pushed.
        conflicts_detected: Number of conflicts.
        errors: JSON array of error messages.
        started_at: When sync started.
        completed_at: When sync completed.
        duration_ms: Duration in milliseconds.
    """

    __tablename__ = "connector_sync_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    config_id: Mapped[str] = mapped_column(String(36), ForeignKey("connector_configs.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    items_pulled: Mapped[int] = mapped_column(Integer, default=0)
    items_pushed: Mapped[int] = mapped_column(Integer, default=0)
    conflicts_detected: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_connector_sync_log_config_started", "config_id", "started_at"),
    )