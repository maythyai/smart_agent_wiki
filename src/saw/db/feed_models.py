"""SQLAlchemy models for RSS feed subscriptions and entries.

Phase 9: RSS Subscription — Database models.
Per RSSS-01~07: Feed and FeedEntry models.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from saw.db.models import Base, generate_uuid, utcnow


class Feed(Base):
    """RSS/Atom feed subscription model.

    Per RSSS-01: Subscribe to RSS/Atom Feed.
    Per RSSS-04: Configure sync frequency.
    Per RSSS-06: Feed classification management.
    Per RSSS-07: Filter by keywords.
    """
    __tablename__ = "feeds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of filter keywords
    poll_interval: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    last_poll_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_etag: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_modified: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    entries: Mapped[List["FeedEntry"]] = relationship(
        "FeedEntry", back_populates="feed", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Feed {self.title or self.url}>"


class FeedEntry(Base):
    """Feed entry model with deduplication support.

    Per RSSS-02: Auto ingest new articles to Vault.
    Per RSSS-03: Incremental sync (only process new entries).
    Per RSSS-05: Content change detection triggers re-ingestion.

    Per Pitfall 25: Multi-key deduplication via id field.
    """
    __tablename__ = "feed_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # DeduplicationKey.compute_id()
    feed_id: Mapped[str] = mapped_column(String, ForeignKey("feeds.id"), nullable=False)
    guid: Mapped[str] = mapped_column(String(2048), nullable=False)  # Original GUID from feed
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)  # Entry link
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Full content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Entry summary
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)  # EntryStatus enum
    vault_uuid: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Reference to Vault document

    # Relationships
    feed: Mapped["Feed"] = relationship("Feed", back_populates="entries")

    # Indexes for deduplication
    __table_args__ = (
        Index("ix_feed_entries_feed_guid", "feed_id", "guid"),
        Index("ix_feed_entries_content_hash", "content_hash"),
        Index("ix_feed_entries_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<FeedEntry {self.title[:50]}>"


# Re-export EntryStatus for convenience
from saw.domain.feed import EntryStatus
