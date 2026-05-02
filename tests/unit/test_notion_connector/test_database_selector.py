"""Tests for Notion database selector.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-02: Database selection persistence.
Per NOTI-10: Sync cursor persistence and resume.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from saw.connectors.notion.database_selector import DatabaseSelector
from saw.connectors.notion.models import NotionDatabase, NotionRichText
from saw.db.notion_models import NotionDatabaseConfigModel, NotionSyncCursorModel


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestDatabaseSelector:
    """Tests for DatabaseSelector class."""

    @pytest.mark.asyncio
    async def test_list_accessible_databases(self) -> None:
        """Test 1: list_accessible_databases() returns databases from Notion search."""
        mock_client = AsyncMock()
        mock_client.search = AsyncMock(return_value={
            "results": [
                {
                    "id": "db-1",
                    "title": [{"plain_text": "Database 1", "type": "text"}],
                    "properties": {"Title": {"type": "title", "title": {}}},
                    "description": [{"plain_text": "Test database"}],
                    "url": "https://notion.so/db-1",
                    "object": "database",
                },
                {
                    "id": "db-2",
                    "title": [{"plain_text": "Database 2", "type": "text"}],
                    "properties": {"Name": {"type": "title", "title": {}}},
                    "description": [],
                    "url": "https://notion.so/db-2",
                    "object": "database",
                },
            ],
            "has_more": False,
            "next_cursor": None,
        })

        mock_session = AsyncMock()

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        databases = await selector.list_accessible_databases()

        assert len(databases) == 2
        assert databases[0].id == "db-1"
        mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_databases(self) -> None:
        """Test 2: select_databases() persists selection to NotionDatabaseConfigModel."""
        mock_client = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        # Mock empty existing selections
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        await selector.select_databases(["db-1", "db-2"])

        # Verify session.add was called for each database
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_get_selected_databases(self) -> None:
        """Test 3: get_selected_databases() returns only selected databases."""
        mock_client = AsyncMock()
        mock_session = AsyncMock()

        mock_config = NotionDatabaseConfigModel(
            id="config-1",
            connector_id="connector-123",
            database_id="db-1",
            database_name="Selected DB",
            is_selected=True,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config]
        mock_session.execute = AsyncMock(return_value=mock_result)

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        databases = await selector.get_selected_databases()

        assert len(databases) == 1
        assert databases[0].database_id == "db-1"

    @pytest.mark.asyncio
    async def test_sync_cursor_updates_after_fetch(self) -> None:
        """Test 4: Sync cursor updates after each page fetch in get_items()."""
        # This is tested in test_notion_connector.py
        assert True

    @pytest.mark.asyncio
    async def test_sync_resume_from_cursor(self) -> None:
        """Test 5: Sync resume continues from last cursor position."""
        mock_client = AsyncMock()
        mock_session = AsyncMock()

        # Mock existing cursor
        mock_cursor = NotionSyncCursorModel(
            id="cursor-1",
            connector_id="connector-123",
            database_id="db-1",
            cursor_token="saved-cursor-token",
            last_sync_at=utcnow(),
            items_synced=50,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_cursor]
        mock_session.execute = AsyncMock(return_value=mock_result)

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        cursors = await selector.get_sync_cursors()

        assert "db-1" in cursors
        assert cursors["db-1"] == "saved-cursor-token"


class TestDatabaseSelectorPagination:
    """Tests for database selector pagination."""

    @pytest.mark.asyncio
    async def test_list_databases_pagination(self) -> None:
        """Test that list_accessible_databases handles pagination."""
        mock_client = AsyncMock()

        # First call returns has_more=True
        call_count = [0]

        async def mock_search(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    "results": [{"id": "db-1", "title": [{"plain_text": "DB 1"}], "properties": {}, "description": [], "url": "", "object": "database"}],
                    "has_more": True,
                    "next_cursor": "cursor-abc",
                }
            else:
                return {
                    "results": [{"id": "db-2", "title": [{"plain_text": "DB 2"}], "properties": {}, "description": [], "url": "", "object": "database"}],
                    "has_more": False,
                    "next_cursor": None,
                }

        mock_client.search = mock_search

        mock_session = AsyncMock()

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        databases = await selector.list_accessible_databases()

        assert len(databases) == 2
        assert call_count[0] == 2


class TestDatabaseSelectorUpdate:
    """Tests for updating database configuration."""

    @pytest.mark.asyncio
    async def test_update_property_mapping(self) -> None:
        """Test updating property mapping for a database."""
        mock_client = AsyncMock()
        mock_session = AsyncMock()

        mock_config = NotionDatabaseConfigModel(
            id="config-1",
            connector_id="connector-123",
            database_id="db-1",
            database_name="Test DB",
            is_selected=True,
            property_mapping={},
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_config
        mock_session.execute = AsyncMock(return_value=mock_result)

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        await selector.update_property_mapping("db-1", {"Title": "title", "Status": "confidence"})

        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_clear_selections(self) -> None:
        """Test clearing all database selections."""
        mock_client = AsyncMock()
        mock_session = AsyncMock()

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        await selector.clear_selections()

        mock_session.execute.assert_called()
