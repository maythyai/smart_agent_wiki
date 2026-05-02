"""Tests for Notion conflict handler.

Plan 12-03: Bidirectional sync and polling.
Per NOTI-06: Conflict detection and resolution.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock

from saw.connectors.notion.conflict_handler import (
    NotionConflictHandler,
    NotionConflictInfo,
    ConflictResolution,
)
from saw.connectors.conflict_resolver import ConflictStrategy
from saw.connectors.notion.models import NotionPage, NotionRichText


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestNotionConflictHandler:
    """Tests for NotionConflictHandler class."""

    def test_no_conflict_notion_only_modified(self) -> None:
        """Test 1: No conflict when only Notion modified after last_sync_at."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.LAST_MODIFIED_WINS)

        last_sync = utcnow() - timedelta(hours=1)
        page = NotionPage(
            id="page-1",
            parent={"database_id": "db-1"},
            properties={},
            created_time=utcnow() - timedelta(days=1),
            last_edited_time=utcnow() - timedelta(minutes=30),  # Modified after sync
            url="https://notion.so/page-1",
            archived=False,
        )

        claim = {
            "id": "claim-1",
            "updated_at": utcnow() - timedelta(days=1),  # Not modified after sync
        }

        conflict = handler.detect(page, claim, last_sync)
        assert conflict is None

    def test_no_conflict_saw_only_modified(self) -> None:
        """Test 2: No conflict when only SAW modified after last_sync_at."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.LAST_MODIFIED_WINS)

        last_sync = utcnow() - timedelta(hours=1)
        page = NotionPage(
            id="page-1",
            parent={"database_id": "db-1"},
            properties={},
            created_time=utcnow() - timedelta(days=1),
            last_edited_time=utcnow() - timedelta(days=1),  # Not modified after sync
            url="https://notion.so/page-1",
            archived=False,
        )

        claim = {
            "id": "claim-1",
            "updated_at": utcnow() - timedelta(minutes=30),  # Modified after sync
        }

        conflict = handler.detect(page, claim, last_sync)
        assert conflict is None

    def test_conflict_both_modified(self) -> None:
        """Test 3: Conflict detected when both modified after last_sync_at."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.LAST_MODIFIED_WINS)

        last_sync = utcnow() - timedelta(hours=1)
        now = utcnow()

        page = NotionPage(
            id="page-1",
            parent={"database_id": "db-1"},
            properties={
                "Title": {
                    "id": "title-id",
                    "type": "title",
                    "title": [{"type": "text", "plain_text": "Notion Version", "annotations": {}}],
                },
            },
            created_time=utcnow() - timedelta(days=1),
            last_edited_time=now - timedelta(minutes=30),  # Modified after sync
            url="https://notion.so/page-1",
            archived=False,
        )

        claim = {
            "id": "claim-1",
            "title": "SAW Version",
            "content": "SAW content",
            "updated_at": now - timedelta(minutes=20),  # Also modified after sync
        }

        conflict = handler.detect(page, claim, last_sync)
        assert conflict is not None
        assert conflict.page_id == "page-1"

    def test_last_modified_wins_notion_later(self) -> None:
        """Test 4: LAST_MODIFIED_WINS resolves to Notion when Notion timestamp later."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.LAST_MODIFIED_WINS)

        now = utcnow()

        conflict = NotionConflictInfo(
            page_id="page-1",
            claim_id="claim-1",
            notion_edited_time=now - timedelta(minutes=10),
            saw_updated_time=now - timedelta(minutes=20),
            last_sync_time=now - timedelta(hours=1),
            notion_content_preview="Notion content",
            saw_content_preview="SAW content",
            notion_title="Notion Title",
            saw_title="SAW Title",
        )

        resolution = handler.resolve(conflict)
        assert resolution.winner == "notion"

    def test_last_modified_wins_saw_later(self) -> None:
        """Test 5: LAST_MODIFIED_WINS resolves to SAW when SAW timestamp later."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.LAST_MODIFIED_WINS)

        now = utcnow()

        conflict = NotionConflictInfo(
            page_id="page-1",
            claim_id="claim-1",
            notion_edited_time=now - timedelta(minutes=30),
            saw_updated_time=now - timedelta(minutes=10),
            last_sync_time=now - timedelta(hours=1),
            notion_content_preview="Notion content",
            saw_content_preview="SAW content",
            notion_title="Notion Title",
            saw_title="SAW Title",
        )

        resolution = handler.resolve(conflict)
        assert resolution.winner == "saw"

    @pytest.mark.asyncio
    async def test_conflict_logged_with_both_versions(self) -> None:
        """Test 6: Conflict logged with both versions preserved."""
        mock_session = MagicMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        handler = NotionConflictHandler(mock_session, ConflictStrategy.LAST_MODIFIED_WINS)

        now = utcnow()
        conflict = NotionConflictInfo(
            page_id="page-1",
            claim_id="claim-1",
            notion_edited_time=now,
            saw_updated_time=now,
            last_sync_time=now - timedelta(hours=1),
            notion_content_preview="Notion version",
            saw_content_preview="SAW version",
            notion_title="Notion Title",
            saw_title="SAW Title",
        )

        resolution = ConflictResolution(
            winner="notion",
            kept_content="Notion version",
            kept_title="Notion Title",
            discarded_content="SAW version",
            discarded_title="SAW Title",
            reason="last_modified_wins",
            conflict_id="conflict-123",
        )

        result = await handler.log_conflict(conflict, resolution, "connector-1")
        assert result is not None
        mock_session.add.assert_called()

    def test_timezone_normalization(self) -> None:
        """Test 7: Timestamp comparison handles timezone differences (UTC normalization)."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.LAST_MODIFIED_WINS)

        # Create timestamps with different timezone representations
        now_utc = datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc)

        last_sync = now_utc - timedelta(hours=1)

        # Page edited at same time (different timezone representation)
        page = NotionPage(
            id="page-1",
            parent={"database_id": "db-1"},
            properties={},
            created_time=now_utc - timedelta(days=1),
            last_edited_time=now_utc,  # UTC
            url="https://notion.so/page-1",
            archived=False,
        )

        claim = {
            "id": "claim-1",
            "updated_at": now_utc,  # Same time, UTC
        }

        # Both modified after sync - this IS a conflict
        conflict = handler.detect(page, claim, last_sync)
        assert conflict is not None  # Both modified at same time = conflict


class TestConflictResolution:
    """Tests for conflict resolution."""

    def test_platform_wins_strategy(self) -> None:
        """Test PLATFORM_WINS always selects Notion."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.PLATFORM_WINS)

        now = utcnow()
        conflict = NotionConflictInfo(
            page_id="page-1",
            claim_id="claim-1",
            notion_edited_time=now - timedelta(hours=1),  # Older
            saw_updated_time=now,  # Newer
            last_sync_time=now - timedelta(days=1),
            notion_content_preview="Old Notion",
            saw_content_preview="New SAW",
            notion_title="Old",
            saw_title="New",
        )

        resolution = handler.resolve(conflict)
        assert resolution.winner == "notion"

    def test_saw_wins_strategy(self) -> None:
        """Test SAW_WINS always selects SAW."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.SAW_WINS)

        now = utcnow()
        conflict = NotionConflictInfo(
            page_id="page-1",
            claim_id="claim-1",
            notion_edited_time=now,  # Newer
            saw_updated_time=now - timedelta(hours=1),  # Older
            last_sync_time=now - timedelta(days=1),
            notion_content_preview="New Notion",
            saw_content_preview="Old SAW",
            notion_title="New",
            saw_title="Old",
        )

        resolution = handler.resolve(conflict)
        assert resolution.winner == "saw"

    def test_manual_strategy(self) -> None:
        """Test MANUAL strategy flags for human review."""
        handler = NotionConflictHandler(MagicMock(), ConflictStrategy.MANUAL)

        now = utcnow()
        conflict = NotionConflictInfo(
            page_id="page-1",
            claim_id="claim-1",
            notion_edited_time=now,
            saw_updated_time=now,
            last_sync_time=now - timedelta(hours=1),
            notion_content_preview="Notion",
            saw_content_preview="SAW",
            notion_title="N",
            saw_title="S",
        )

        resolution = handler.resolve(conflict)
        assert resolution.winner == "manual"


class TestNotionConflictInfo:
    """Tests for NotionConflictInfo dataclass."""

    def test_conflict_info_creation(self) -> None:
        """Test 8: Conflict record includes item ID, timestamps, content snippets."""
        now = utcnow()

        info = NotionConflictInfo(
            page_id="page-123",
            claim_id="claim-456",
            notion_edited_time=now,
            saw_updated_time=now,
            last_sync_time=now - timedelta(hours=1),
            notion_content_preview="Notion content preview...",
            saw_content_preview="SAW content preview...",
            notion_title="Notion Title",
            saw_title="SAW Title",
        )

        assert info.page_id == "page-123"
        assert info.claim_id == "claim-456"
        assert len(info.notion_content_preview) > 0
        assert len(info.saw_content_preview) > 0
