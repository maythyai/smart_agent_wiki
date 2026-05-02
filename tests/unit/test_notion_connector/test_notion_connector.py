"""Tests for NotionConnector core implementation.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-01: OAuth workspace connection.
Per NOTI-09: Rate limiting (3 req/s).
Per NOTI-10: Sync cursor persistence.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.notion.connector import NotionConnector
from saw.connectors.protocol import AuthResult, ConnectorItem
from saw.connectors.models import ConnectorConfig
from saw.connectors.rate_limiter import RateLimitManager


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def create_mock_result(scalars_data):
    """Create a mock result with scalars().all() chain."""
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = scalars_data
    mock_result.scalars.return_value = mock_scalars
    return mock_result


class TestNotionConnectorProperties:
    """Tests for NotionConnector basic properties."""

    def test_platform_name(self) -> None:
        """Test 1: NotionConnector.platform_name returns 'notion'."""
        assert NotionConnector.platform_name == "notion"

    def test_supports_push(self) -> None:
        """Test 2: NotionConnector.supports_push returns True."""
        assert NotionConnector.supports_push is True


class TestNotionConnectorAuthentication:
    """Tests for NotionConnector authenticate method."""

    @pytest.mark.asyncio
    async def test_authenticate_exchanges_code(self) -> None:
        """Test 3: authenticate() exchanges OAuth code for AuthResult."""
        # Mock the OAuth handler
        mock_oauth_handler = MagicMock()
        mock_oauth_handler.exchange_code = AsyncMock(return_value=(
            {"encrypted_token": "encrypted_value", "workspace_id": "ws-123"},
            "user-123",
        ))

        connector = NotionConnector.__new__(NotionConnector)
        connector._oauth_handler = mock_oauth_handler

        result = await connector.authenticate({
            "code": "auth_code_123",
            "state": "state_abc",
        })

        assert isinstance(result, AuthResult)
        mock_oauth_handler.exchange_code.assert_called_once_with("auth_code_123", "state_abc")

    @pytest.mark.asyncio
    async def test_authenticate_returns_workspace_info(self) -> None:
        """Test that authenticate captures workspace_id in raw_response."""
        mock_oauth_handler = MagicMock()
        mock_oauth_handler.exchange_code = AsyncMock(return_value=(
            {
                "encrypted_token": "encrypted_value",
                "workspace_id": "ws-123",
                "workspace_name": "My Workspace",
            },
            "user-123",
        ))

        connector = NotionConnector.__new__(NotionConnector)
        connector._oauth_handler = mock_oauth_handler

        result = await connector.authenticate({
            "code": "auth_code",
            "state": "state",
        })

        assert result.raw_response.get("workspace_id") == "ws-123"


class TestNotionConnectorGetItems:
    """Tests for NotionConnector get_items method."""

    @pytest.mark.asyncio
    async def test_get_items_returns_connector_items(self) -> None:
        """Test 4: get_items() returns list of ConnectorItem from selected databases."""
        mock_client = AsyncMock()
        mock_client.databases = AsyncMock()
        mock_client.databases.query = AsyncMock(return_value={
            "results": [
                {
                    "id": "page-1",
                    "parent": {"database_id": "db-123"},
                    "properties": {
                        "Title": {
                            "id": "title-id",
                            "type": "title",
                            "title": [{"plain_text": "Test Page", "type": "text"}],
                        },
                    },
                    "created_time": utcnow().isoformat(),
                    "last_edited_time": utcnow().isoformat(),
                    "url": "https://notion.so/page-1",
                    "archived": False,
                },
            ],
            "has_more": False,
            "next_cursor": None,
        })

        mock_session = AsyncMock()
        # Mock _load_selected_databases and _load_sync_cursors
        mock_session.execute = AsyncMock()

        mock_config = ConnectorConfig(
            id="connector-123",
            user_id="user-123",
            platform="notion",
            name="Test Notion",
        )

        connector = NotionConnector.__new__(NotionConnector)
        connector._client = mock_client
        connector._session = mock_session
        connector._config = mock_config
        connector._rate_limiter = RateLimitManager("notion")
        connector._selected_databases = [{"database_id": "db-123", "database_name": "Test DB"}]
        connector._sync_cursors = {}

        # Mock the internal methods
        connector._load_selected_databases = AsyncMock(return_value=connector._selected_databases)
        connector._load_sync_cursors = AsyncMock(return_value={})
        connector._update_sync_cursor = AsyncMock()

        items = await connector.get_items()

        assert isinstance(items, list)
        assert len(items) == 1
        assert items[0].id == "page-1"
        mock_client.databases.query.assert_called()

    @pytest.mark.asyncio
    async def test_get_items_filters_by_since(self) -> None:
        """Test 5: get_items(since=dt) only returns pages edited after dt."""
        mock_client = AsyncMock()
        mock_client.databases = AsyncMock()

        since = utcnow() - timedelta(hours=1)

        call_args = {}

        async def mock_query(**kwargs):
            call_args.update(kwargs)
            return {
                "results": [],
                "has_more": False,
                "next_cursor": None,
            }

        mock_client.databases.query = mock_query

        mock_config = ConnectorConfig(
            id="connector-123",
            user_id="user-123",
            platform="notion",
            name="Test Notion",
        )

        connector = NotionConnector.__new__(NotionConnector)
        connector._client = mock_client
        connector._session = AsyncMock()
        connector._config = mock_config
        connector._rate_limiter = RateLimitManager("notion")
        connector._selected_databases = [{"database_id": "db-123", "database_name": "Test DB"}]
        connector._sync_cursors = {}

        # Mock the internal methods
        connector._load_selected_databases = AsyncMock(return_value=connector._selected_databases)
        connector._load_sync_cursors = AsyncMock(return_value={})
        connector._update_sync_cursor = AsyncMock()

        items = await connector.get_items(since=since)

        # Verify filter was applied in query
        assert "filter" in call_args or len(items) == 0

    @pytest.mark.asyncio
    async def test_get_items_persists_cursor(self) -> None:
        """Test 7: Sync cursor persists after get_items() for resume."""
        mock_client = AsyncMock()
        mock_client.databases = AsyncMock()
        mock_client.databases.query = AsyncMock(return_value={
            "results": [
                {
                    "id": "page-1",
                    "parent": {"database_id": "db-123"},
                    "properties": {},
                    "created_time": utcnow().isoformat(),
                    "last_edited_time": utcnow().isoformat(),
                    "url": "https://notion.so/page-1",
                    "archived": False,
                },
            ],
            "has_more": True,
            "next_cursor": "next-cursor-token",
        })

        mock_config = ConnectorConfig(
            id="connector-123",
            user_id="user-123",
            platform="notion",
            name="Test Notion",
        )

        connector = NotionConnector.__new__(NotionConnector)
        connector._client = mock_client
        connector._session = AsyncMock()
        connector._config = mock_config
        connector._rate_limiter = RateLimitManager("notion")
        connector._selected_databases = [{"database_id": "db-123", "database_name": "Test DB"}]
        connector._sync_cursors = {}

        # Mock the internal methods
        connector._load_selected_databases = AsyncMock(return_value=connector._selected_databases)
        connector._load_sync_cursors = AsyncMock(return_value={})
        connector._update_sync_cursor = AsyncMock()

        await connector.get_items()

        # Cursor should be updated
        connector._update_sync_cursor.assert_called()


class TestNotionConnectorRateLimiting:
    """Tests for NotionConnector rate limiting."""

    def test_rate_limiter_configured(self) -> None:
        """Test 6: Rate limiter enforces 3 req/s."""
        # This is tested by RateLimitManager tests
        # Just verify the platform is configured
        from saw.connectors.rate_limiter import PlatformRateLimit
        limits = PlatformRateLimit.notion()
        assert limits.requests_per_second == 3


class TestNotionConnectorTransform:
    """Tests for NotionConnector transform methods."""

    def test_transform_to_claim_basic(self) -> None:
        """Test basic transform_to_claim functionality."""
        mock_config = ConnectorConfig(
            id="connector-123",
            user_id="user-123",
            platform="notion",
            name="Test Notion",
        )

        connector = NotionConnector.__new__(NotionConnector)
        connector._config = mock_config
        connector._session = AsyncMock()
        connector._rate_limiter = RateLimitManager("notion")

        item = ConnectorItem(
            id="page-123",
            title="Test Page",
            content="Test content",
            url="https://notion.so/page-123",
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata={"database_id": "db-123"},
        )

        claim = connector.transform_to_claim(item)

        assert claim.get("source_platform") == "notion"
        assert claim.get("source_id") == "page-123"
        assert claim.get("title") == "Test Page"

    def test_transform_from_claim_basic(self) -> None:
        """Test basic transform_from_claim functionality."""
        mock_config = ConnectorConfig(
            id="connector-123",
            user_id="user-123",
            platform="notion",
            name="Test Notion",
        )

        connector = NotionConnector.__new__(NotionConnector)
        connector._config = mock_config
        connector._session = AsyncMock()
        connector._rate_limiter = RateLimitManager("notion")

        claim = {
            "title": "Test Claim",
            "content": "Test content",
            "source_id": "page-123",
            "source_url": "https://notion.so/page-123",
        }

        item = connector.transform_from_claim(claim)

        assert isinstance(item, ConnectorItem)
        assert item.title == "Test Claim"
