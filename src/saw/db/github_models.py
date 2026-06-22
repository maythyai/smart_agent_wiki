"""SQLAlchemy models for GitHub connector sync state.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-02: Repository selection persistence.
Per GITH-09: Rate limit state tracking.
Per GITH-10: Sync cursor persistence for resume capability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import enum

from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, Index, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saw.db.models import Base, generate_uuid
from saw.domain.utils import utcnow  # noqa: F401


class GitHubSyncType(enum.Enum):
    """Sync type for GitHub items."""
    ISSUES = "issues"
    DISCUSSIONS = "discussions"
    COMMENTS = "comments"


class GitHubSyncCursorModel(Base):
    """Per-repository sync cursor for incremental sync.

    Per GITH-10: Sync cursor persists after each fetch for resume capability.
    Per GITH-11: ETag stored for conditional requests.

    Attributes:
        id: Unique cursor identifier.
        connector_id: FK to connector_configs.id.
        repository_id: Repository full name (owner/repo).
        sync_type: Type of items synced (issues/discussions/comments).
        last_issue_number: Last issue number synced.
        last_discussion_number: Last discussion number synced.
        last_comment_id: Last comment ID synced.
        last_sync_at: Last successful sync timestamp.
        last_item_edited_at: Max edited time in last batch.
        etag: ETag for conditional requests.
        graphql_cursor: GraphQL pagination cursor for discussions.
        items_synced: Running count of synced items.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "github_sync_cursor"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False, index=True
    )
    repository_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sync_type: Mapped[GitHubSyncType] = mapped_column(
        SQLEnum(GitHubSyncType), default=GitHubSyncType.ISSUES
    )
    last_issue_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_discussion_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_comment_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_item_edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    etag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    graphql_cursor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    items_synced: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_github_cursor_connector_repo", "connector_id", "repository_id", "sync_type", unique=True),
    )


class GitHubRepositoryConfigModel(Base):
    """Selected GitHub repositories for sync.

    Per GITH-02: Persist repository selection with sync preferences.

    Attributes:
        id: Unique config identifier.
        connector_id: FK to connector_configs.id.
        repository_id: Repository full name (owner/repo).
        repository_name: Cached repository display name.
        is_selected: Whether repository is selected for sync.
        sync_issues: Whether to sync issues.
        sync_discussions: Whether to sync discussions.
        sync_comments: Whether to sync comments.
        label_tag_mapping: Custom label to SAW tag mappings.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "github_repository_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False, index=True
    )
    repository_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    repository_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_issues: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_discussions: Mapped[bool] = mapped_column(Boolean, default=False)
    sync_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    label_tag_mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    __table_args__ = (
        Index("ix_github_repo_config_connector_repo", "connector_id", "repository_id", unique=True),
    )


class GitHubRateLimitStateModel(Base):
    """GitHub rate limit state tracking.

    Per GITH-09: Track rate limit for conditional requests.

    Attributes:
        id: Unique state identifier.
        connector_id: FK to connector_configs.id.
        remaining_requests: Remaining API requests.
        reset_at: Rate limit reset timestamp.
        last_checked_at: Last check timestamp.
        created_at: Record creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "github_rate_limit_state"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    connector_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("connector_configs.id"), nullable=False, index=True
    )
    remaining_requests: Mapped[int] = mapped_column(Integer, default=5000)
    reset_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class GitHubWebhookDeliveryModel(Base):
    """GitHub webhook delivery log for deduplication.

    Per T-14-16: Check for duplicate delivery_id within 24-hour window.

    Attributes:
        id: Unique delivery record identifier.
        delivery_id: GitHub delivery UUID (X-GitHub-Delivery).
        event_type: Event type (issues, issue_comment, etc.).
        repository: Repository full name.
        action: Event action (opened, closed, etc.).
        processed_at: Processing timestamp.
        items_created: Number of items created from this event.
        created_at: Record creation timestamp.
    """

    __tablename__ = "github_webhook_delivery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    delivery_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    repository: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    items_created: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)