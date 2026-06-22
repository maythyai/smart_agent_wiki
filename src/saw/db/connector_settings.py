"""SQLAlchemy model for connector settings persistence.

Plan 18-01: Per-connector configuration storage.
Per D-01: Dedicated settings table with platform as primary key.
Per D-02: Schema with sync_interval, sync_directions, property_mappings, rate_limit_override.
Per CONF-05: Rate limit override with safety bounds (1-100).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from saw.db.models import Base
from saw.domain.utils import utcnow  # noqa: F401


# Default values per D-07, D-11
DEFAULT_SYNC_INTERVAL = "15min"
DEFAULT_SYNC_DIRECTIONS = "bidirectional"


class ConnectorSettingsModel(Base):
    """SQLAlchemy model for connector settings.

    Per D-01: One settings row per platform (platform is primary key).

    Attributes:
        platform: Platform identifier (notion, slack, github, etc.) - primary key.
        sync_interval: Named interval mode - "5min", "15min", "1hr", "6hr", "manual".
        sync_directions: Sync direction mode - "inbound_only", "outbound_only", "bidirectional".
        rate_limit_override: Optional override for rate limit (1-100).
        property_mappings: JSON object mapping SAW fields to platform properties.
        updated_at: Last update timestamp.
    """

    __tablename__ = "connector_settings"

    platform: Mapped[str] = mapped_column(String(50), primary_key=True)
    sync_interval: Mapped[str] = mapped_column(
        String(20),
        default=DEFAULT_SYNC_INTERVAL,
        nullable=False,
    )
    sync_directions: Mapped[str] = mapped_column(
        String(20),
        default=DEFAULT_SYNC_DIRECTIONS,
        nullable=False,
    )
    rate_limit_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    property_mappings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_connector_settings_platform", "platform"),
    )