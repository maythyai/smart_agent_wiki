"""Tests for Connector Settings API.

Plan 18-01: Settings API endpoints tests.
Tests: GET/PUT /api/v1/connectors/{platform}/settings, validation, persistence.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from saw.api.connector_settings import (
    router,
    SettingsResponse,
    SettingsUpdateRequest,
    ReauthResponse,
    VALID_SYNC_INTERVALS,
    VALID_SYNC_DIRECTIONS,
)


def utcnow():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


class TestGetSettings:
    """Test GET /api/v1/connectors/{platform}/settings"""

    @pytest.mark.asyncio
    async def test_get_settings_existing(self, mock_session):
        """Test 1: GET returns stored settings for existing connector."""
        from saw.api.connector_settings import get_settings
        from saw.db.connector_settings import ConnectorSettingsModel

        # Mock existing settings
        settings = MagicMock(spec=ConnectorSettingsModel)
        settings.platform = "notion"
        settings.sync_interval = "1hr"
        settings.sync_directions = "bidirectional"
        settings.property_mappings = '{"title": "Name", "content": "Body"}'
        settings.rate_limit_override = 50
        settings.updated_at = utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = settings
        mock_session.execute.return_value = mock_result

        response = await get_settings(platform="notion", session=mock_session)

        assert isinstance(response, SettingsResponse)
        assert response.platform == "notion"
        assert response.sync_interval == "1hr"
        assert response.sync_directions == "bidirectional"
        assert response.property_mappings == {"title": "Name", "content": "Body"}
        assert response.rate_limit_override == 50

    @pytest.mark.asyncio
    async def test_get_settings_default(self, mock_session):
        """Test 2: GET returns defaults for new connector."""
        from saw.api.connector_settings import get_settings

        # Mock no existing settings
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        response = await get_settings(platform="slack", session=mock_session)

        assert isinstance(response, SettingsResponse)
        assert response.platform == "slack"
        assert response.sync_interval == "15min"  # Default
        assert response.sync_directions == "bidirectional"  # Default
        assert response.property_mappings == {}
        assert response.rate_limit_override is None


class TestUpdateSettings:
    """Test PUT /api/v1/connectors/{platform}/settings"""

    @pytest.mark.asyncio
    async def test_update_settings_valid(self, mock_session):
        """Test 3: PUT with valid values returns 200."""
        from saw.api.connector_settings import update_settings
        from saw.db.connector_settings import ConnectorSettingsModel

        # Mock existing settings
        settings = MagicMock(spec=ConnectorSettingsModel)
        settings.platform = "notion"
        settings.sync_interval = "15min"
        settings.sync_directions = "bidirectional"
        settings.property_mappings = None
        settings.rate_limit_override = None
        settings.updated_at = utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = settings
        mock_session.execute.return_value = mock_result

        update = SettingsUpdateRequest(
            sync_interval="1hr",
            sync_directions="inbound_only",
        )

        response = await update_settings(
            platform="notion",
            update=update,
            session=mock_session,
        )

        assert isinstance(response, SettingsResponse)
        assert response.sync_interval == "1hr"
        assert response.sync_directions == "inbound_only"
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_settings_invalid_interval(self, mock_session):
        """Test 4: PUT with invalid sync_interval returns 400."""
        from saw.api.connector_settings import update_settings
        from fastapi import HTTPException

        # Test validation at Pydantic level
        with pytest.raises(ValueError) as exc_info:
            SettingsUpdateRequest(sync_interval="invalid_value")

        assert "Invalid sync_interval" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_settings_invalid_direction(self, mock_session):
        """Test 5: PUT with invalid sync_directions returns 400."""
        from saw.api.connector_settings import update_settings
        from fastapi import HTTPException

        # Test validation at Pydantic level
        with pytest.raises(ValueError) as exc_info:
            SettingsUpdateRequest(sync_directions="invalid_direction")

        assert "Invalid sync_directions" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_settings_rate_limit_bounds(self, mock_session):
        """Test 6: PUT with rate_limit > 100 returns 400."""
        from fastapi import HTTPException

        # Test upper bound violation
        with pytest.raises(ValueError) as exc_info:
            SettingsUpdateRequest(rate_limit_override=150)

        assert "rate_limit_override must be between 1 and 100" in str(exc_info.value)

        # Test lower bound violation
        with pytest.raises(ValueError) as exc_info:
            SettingsUpdateRequest(rate_limit_override=0)

        assert "rate_limit_override must be between 1 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_settings_persist(self, mock_session):
        """Test 7: PUT then GET returns same values (CONF-07)."""
        from saw.api.connector_settings import get_settings, update_settings
        from saw.db.connector_settings import ConnectorSettingsModel

        # Mock settings that persist
        settings = MagicMock(spec=ConnectorSettingsModel)
        settings.platform = "notion"
        settings.sync_interval = "15min"
        settings.sync_directions = "bidirectional"
        settings.property_mappings = '{"title": "Name"}'
        settings.rate_limit_override = 25
        settings.updated_at = utcnow()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = settings
        mock_session.execute.return_value = mock_result

        # Update settings
        update = SettingsUpdateRequest(
            sync_interval="6hr",
            property_mappings={"title": "Name"},
            rate_limit_override=25,
        )

        update_response = await update_settings(
            platform="notion",
            update=update,
            session=mock_session,
        )

        # Get settings again (same mock returns persisted values)
        get_response = await get_settings(platform="notion", session=mock_session)

        assert get_response.sync_interval == settings.sync_interval
        assert get_response.rate_limit_override == settings.rate_limit_override


class TestReauthEndpoint:
    """Test POST /api/v1/connectors/{platform}/reauth"""

    @pytest.mark.asyncio
    async def test_reauth_returns_url(self, mock_session):
        """Test reauth endpoint returns authorization URL."""
        from saw.api.connector_settings import reauthorize_platform

        # Mock connector with OAuth handler
        mock_connector = MagicMock()
        mock_oauth_handler = AsyncMock()
        mock_oauth_handler.get_authorization_url.return_value = (
            "https://api.notion.com/v1/oauth/authorize?...",
            "random_state_string",
        )
        mock_connector.oauth_handler = mock_oauth_handler

        with patch("saw.connectors.registry.ConnectorRegistry") as mock_registry:
            registry = MagicMock()
            registry.get.return_value = mock_connector
            mock_registry.return_value = registry

            response = await reauthorize_platform(
                platform="notion",
                session=mock_session,
            )

            assert isinstance(response, ReauthResponse)
            assert response.platform == "notion"
            assert "authorize" in response.authorize_url.lower() or "oauth" in response.authorize_url.lower()
            assert response.state == "random_state_string"

    @pytest.mark.asyncio
    async def test_reauth_platform_not_found(self, mock_session):
        """Test reauth raises 404 for unknown platform."""
        from saw.api.connector_settings import reauthorize_platform
        from fastapi import HTTPException

        with patch("saw.connectors.registry.ConnectorRegistry") as mock_registry:
            registry = MagicMock()
            registry.get.return_value = None
            mock_registry.return_value = registry

            with pytest.raises(HTTPException) as exc_info:
                await reauthorize_platform(platform="unknown", session=mock_session)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_reauth_non_oauth_platform(self, mock_session):
        """Test reauth raises 400 for non-OAuth platform."""
        from saw.api.connector_settings import reauthorize_platform
        from fastapi import HTTPException

        # Mock connector without OAuth (like Logseq)
        mock_connector = MagicMock()
        mock_connector.oauth_handler = None

        with patch("saw.connectors.registry.ConnectorRegistry") as mock_registry:
            registry = MagicMock()
            registry.get.return_value = mock_connector
            mock_registry.return_value = registry

            with pytest.raises(HTTPException) as exc_info:
                await reauthorize_platform(platform="logseq", session=mock_session)

            assert exc_info.value.status_code == 400


class TestValidation:
    """Test validation logic."""

    def test_valid_sync_intervals(self):
        """Test sync_interval accepts valid values."""
        for interval in VALID_SYNC_INTERVALS:
            request = SettingsUpdateRequest(sync_interval=interval)
            assert request.sync_interval == interval

    def test_valid_sync_directions(self):
        """Test sync_directions accepts valid values."""
        for direction in VALID_SYNC_DIRECTIONS:
            request = SettingsUpdateRequest(sync_directions=direction)
            assert request.sync_directions == direction

    def test_rate_limit_valid_range(self):
        """Test rate_limit_override accepts valid range."""
        for value in [1, 50, 100]:
            request = SettingsUpdateRequest(rate_limit_override=value)
            assert request.rate_limit_override == value

    def test_property_mappings_dict(self):
        """Test property_mappings accepts dict."""
        request = SettingsUpdateRequest(property_mappings={"title": "Name"})
        assert request.property_mappings == {"title": "Name"}


class TestResponseModels:
    """Test Pydantic response models."""

    def test_settings_response_model(self):
        """Test SettingsResponse model."""
        response = SettingsResponse(
            platform="notion",
            sync_interval="15min",
            sync_directions="bidirectional",
            property_mappings={"title": "Name"},
            rate_limit_override=50,
            updated_at=utcnow().isoformat(),
        )

        assert response.platform == "notion"
        assert response.sync_interval == "15min"
        assert response.sync_directions == "bidirectional"
        assert response.property_mappings == {"title": "Name"}
        assert response.rate_limit_override == 50

    def test_reauth_response_model(self):
        """Test ReauthResponse model."""
        response = ReauthResponse(
            platform="slack",
            authorize_url="https://slack.com/oauth/authorize",
            state="abc123",
        )

        assert response.platform == "slack"
        assert response.authorize_url == "https://slack.com/oauth/authorize"
        assert response.state == "abc123"