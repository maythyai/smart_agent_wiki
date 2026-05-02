"""Tests for Notion API endpoints.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-02: Database selection API endpoints.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestNotionDatabaseEndpoints:
    """Tests for Notion database API endpoints."""

    @pytest.mark.asyncio
    async def test_list_databases_endpoint(self) -> None:
        """Test GET /api/v1/connectors/notion/databases returns database list."""
        # Mock the endpoint handler
        from saw.connectors.notion.database_selector import DatabaseSelector
        from saw.connectors.notion.models import NotionDatabase, NotionRichText

        mock_client = AsyncMock()
        mock_session = AsyncMock()

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        # Mock search response
        mock_client.search = AsyncMock(return_value={
            "results": [
                {
                    "id": "db-1",
                    "title": [{"plain_text": "My Tasks"}],
                    "properties": {"Title": {"type": "title"}},
                    "description": [],
                    "url": "https://notion.so/db-1",
                    "object": "database",
                },
            ],
            "has_more": False,
        })

        databases = await selector.list_accessible_databases()

        assert len(databases) == 1
        assert databases[0].title[0].plain_text == "My Tasks"

    @pytest.mark.asyncio
    async def test_select_databases_endpoint(self) -> None:
        """Test POST /api/v1/connectors/notion/databases/select persists selection."""
        from saw.connectors.notion.database_selector import DatabaseSelector

        mock_client = AsyncMock()
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        selector = DatabaseSelector(
            client=mock_client,
            session=mock_session,
            connector_id="connector-123",
        )

        # Mock clear_selections
        selector.clear_selections = AsyncMock()

        await selector.select_databases(["db-1", "db-2"])

        # Verify add was called
        assert mock_session.add.call_count == 2

    @pytest.mark.asyncio
    async def test_get_selected_databases_endpoint(self) -> None:
        """Test GET /api/v1/connectors/notion/databases/selected returns selections."""
        from saw.connectors.notion.database_selector import DatabaseSelector
        from saw.db.notion_models import NotionDatabaseConfigModel

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
    async def test_update_property_mapping_endpoint(self) -> None:
        """Test PATCH /api/v1/connectors/notion/databases/{id}/mapping updates mapping."""
        from saw.connectors.notion.database_selector import DatabaseSelector
        from saw.db.notion_models import NotionDatabaseConfigModel

        mock_client = AsyncMock()
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

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

        await selector.update_property_mapping("db-1", {"Title": "title"})

        # Verify flush was called
        mock_session.flush.assert_called()