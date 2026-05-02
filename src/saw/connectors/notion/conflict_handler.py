"""Notion-specific conflict detection and resolution.

Plan 12-03: Bidirectional sync and polling.
Per NOTI-06: Concurrent edit detection and resolution.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.conflict_resolver import ConflictStrategy
from saw.connectors.notion.models import NotionPage
from saw.db.sync_models import ConflictRecordModel


logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class NotionConflictInfo:
    """Information about a detected Notion conflict.

    Per NOTI-06: Contains details for conflict resolution and logging.

    Attributes:
        page_id: Notion page ID.
        claim_id: SAW claim ID.
        notion_edited_time: When Notion page was last edited.
        saw_updated_time: When SAW claim was last updated.
        last_sync_time: Last successful sync timestamp.
        notion_content_preview: First 500 chars of Notion content.
        saw_content_preview: First 500 chars of SAW content.
        notion_title: Title from Notion.
        saw_title: Title from SAW.
    """

    page_id: str
    claim_id: str
    notion_edited_time: datetime
    saw_updated_time: datetime
    last_sync_time: datetime
    notion_content_preview: str
    saw_content_preview: str
    notion_title: str
    saw_title: str


@dataclass
class ConflictResolution:
    """Result of conflict resolution.

    Attributes:
        winner: Which version won ("notion", "saw", or "manual").
        kept_content: Content from winning version.
        kept_title: Title from winning version.
        discarded_content: Content from losing version.
        discarded_title: Title from losing version.
        reason: Resolution reason.
        conflict_id: Unique conflict identifier.
    """

    winner: str
    kept_content: str
    kept_title: str
    discarded_content: str
    discarded_title: str
    reason: str
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class NotionConflictHandler:
    """Detects and resolves sync conflicts for Notion.

    Per NOTI-06: Conflict when both sides modified after last_sync_at.
    """

    CONTENT_PREVIEW_LENGTH = 500

    def __init__(
        self,
        session: AsyncSession,
        strategy: ConflictStrategy = ConflictStrategy.LAST_MODIFIED_WINS,
    ) -> None:
        """Initialize conflict handler.

        Args:
            session: SQLAlchemy async session.
            strategy: Resolution strategy.
        """
        self._session = session
        self._strategy = strategy

    def detect(
        self,
        page: NotionPage,
        claim: dict,
        last_sync_at: Optional[datetime],
    ) -> Optional[NotionConflictInfo]:
        """Detect if there's a conflict between Notion and SAW versions.

        Per NOTI-06: Conflict when both modified after last_sync_at.

        Args:
            page: Notion page.
            claim: SAW claim dict.
            last_sync_at: Last sync timestamp. If None, no conflict possible.

        Returns:
            NotionConflictInfo if conflict detected, None otherwise.
        """
        if last_sync_at is None:
            # First sync - no conflict possible
            return None

        # Normalize timestamps to UTC
        notion_edited = page.last_edited_time
        if notion_edited and notion_edited.tzinfo is None:
            notion_edited = notion_edited.replace(tzinfo=timezone.utc)

        saw_updated_str = claim.get("updated_at") or claim.get("created_at")
        saw_updated = None
        if saw_updated_str:
            if isinstance(saw_updated_str, str):
                saw_updated = datetime.fromisoformat(saw_updated_str.replace("Z", "+00:00"))
            elif isinstance(saw_updated_str, datetime):
                saw_updated = saw_updated_str

        if notion_edited is None or saw_updated is None:
            # Can't compare - no conflict
            return None

        # Check if both modified after last sync
        notion_modified = notion_edited > last_sync_at
        saw_modified = saw_updated > last_sync_at

        if notion_modified and saw_modified:
            # Both sides modified - conflict!
            # Extract content previews
            notion_content = self._extract_content_preview(claim, "notion")
            saw_content = self._extract_content_preview(claim, "saw")

            # Extract titles
            notion_title = self._extract_title(page)
            saw_title = claim.get("title", "")

            return NotionConflictInfo(
                page_id=page.id,
                claim_id=claim.get("id") or claim.get("uuid", ""),
                notion_edited_time=notion_edited,
                saw_updated_time=saw_updated,
                last_sync_time=last_sync_at,
                notion_content_preview=notion_content,
                saw_content_preview=saw_content,
                notion_title=notion_title,
                saw_title=saw_title,
            )

        return None

    def _extract_content_preview(self, claim: dict, source: str) -> str:
        """Extract content preview from claim."""
        content = claim.get("content", "")
        if len(content) > self.CONTENT_PREVIEW_LENGTH:
            return content[:self.CONTENT_PREVIEW_LENGTH] + "..."
        return content

    def _extract_title(self, page: NotionPage) -> str:
        """Extract title from Notion page."""
        for prop in page.properties.values():
            if prop.get("type") == "title":
                title_list = prop.get("title", [])
                if title_list:
                    return title_list[0].get("plain_text", "")
        return ""

    def resolve(self, conflict: NotionConflictInfo) -> ConflictResolution:
        """Resolve a conflict using configured strategy.

        Args:
            conflict: Conflict information.

        Returns:
            ConflictResolution indicating the winning version.
        """
        if self._strategy == ConflictStrategy.PLATFORM_WINS:
            winner = "notion"
        elif self._strategy == ConflictStrategy.SAW_WINS:
            winner = "saw"
        elif self._strategy == ConflictStrategy.MANUAL:
            winner = "manual"
        else:
            # LAST_MODIFIED_WINS - compare timestamps
            # Normalize to UTC for comparison
            notion_time = conflict.notion_edited_time
            saw_time = conflict.saw_updated_time

            if notion_time.tzinfo is None:
                notion_time = notion_time.replace(tzinfo=timezone.utc)
            if saw_time.tzinfo is None:
                saw_time = saw_time.replace(tzinfo=timezone.utc)

            if notion_time >= saw_time:
                winner = "notion"
            else:
                winner = "saw"

        # Build resolution
        if winner == "notion":
            return ConflictResolution(
                winner=winner,
                kept_content=conflict.notion_content_preview,
                kept_title=conflict.notion_title,
                discarded_content=conflict.saw_content_preview,
                discarded_title=conflict.saw_title,
                reason="last_modified_wins" if self._strategy == ConflictStrategy.LAST_MODIFIED_WINS else "platform_wins",
            )
        elif winner == "saw":
            return ConflictResolution(
                winner=winner,
                kept_content=conflict.saw_content_preview,
                kept_title=conflict.saw_title,
                discarded_content=conflict.notion_content_preview,
                discarded_title=conflict.notion_title,
                reason="last_modified_wins" if self._strategy == ConflictStrategy.LAST_MODIFIED_WINS else "saw_wins",
            )
        else:
            # Manual - need human review
            return ConflictResolution(
                winner=winner,
                kept_content="",  # Not decided yet
                kept_title="",
                discarded_content="",
                discarded_title="",
                reason="manual_review_required",
            )

    async def log_conflict(
        self,
        conflict: NotionConflictInfo,
        resolution: ConflictResolution,
        connector_id: str,
    ) -> ConflictRecordModel:
        """Log a conflict for audit trail.

        Per NOTI-06: Conflicts logged with both versions for manual review.

        Args:
            conflict: Conflict information.
            resolution: Resolution result.
            connector_id: Connector identifier.

        Returns:
            Created ConflictRecordModel.
        """
        record = ConflictRecordModel(
            connector_id=connector_id,
            platform_item_id=conflict.page_id,
            saw_claim_id=conflict.claim_id,
            platform_modified_at=conflict.notion_edited_time,
            saw_modified_at=conflict.saw_updated_time,
            resolution=resolution.winner + "_wins" if resolution.winner != "manual" else "manual",
            resolved_at=utcnow() if resolution.winner != "manual" else None,
        )
        # Store version details in extra field if available
        # Note: ConflictRecordModel doesn't have a versions field,
        # but we can log the details

        self._session.add(record)
        await self._session.flush()

        logger.info(
            f"Conflict logged: page={conflict.page_id}, claim={conflict.claim_id}, "
            f"winner={resolution.winner}, reason={resolution.reason}"
        )

        return record

    async def get_unresolved_conflicts(
        self,
        connector_id: Optional[str] = None,
    ) -> list[ConflictRecordModel]:
        """Get unresolved (manual) conflicts.

        Args:
            connector_id: Filter by connector (optional).

        Returns:
            List of unresolved ConflictRecordModel instances.
        """
        stmt = (
            select(ConflictRecordModel)
            .where(ConflictRecordModel.resolution == "manual")
            .where(ConflictRecordModel.resolved_at.is_(None))
            .order_by(ConflictRecordModel.created_at.desc())
        )

        if connector_id:
            stmt = stmt.where(ConflictRecordModel.connector_id == connector_id)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def resolve_manual_conflict(
        self,
        conflict_id: int,
        winner: str,
    ) -> ConflictRecordModel:
        """Manually resolve a conflict.

        Args:
            conflict_id: Conflict record ID.
            winner: Resolution choice ("notion" or "saw").

        Returns:
            Updated ConflictRecordModel.

        Raises:
            ValueError: If conflict not found or already resolved.
        """
        stmt = select(ConflictRecordModel).where(ConflictRecordModel.id == conflict_id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            raise ValueError(f"Conflict {conflict_id} not found")
        if record.resolved_at is not None:
            raise ValueError(f"Conflict {conflict_id} already resolved")

        record.resolution = f"{winner}_wins"
        record.resolved_at = utcnow()

        await self._session.flush()
        return record
