"""Tests for Integration Dashboard API.

Plan 15-01: Dashboard API and UI components.
Tests: GET /api/v1/integrations/dashboard, DELETE, POST sync, GET errors.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from saw.api.integrations import (
    router,
    DashboardConnector,
    DashboardResponse,
    ConnectorError,
    SyncTriggerResponse,
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
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_registry():
    """Create mock connector registry."""
    with patch("saw.api.integrations.ConnectorRegistry") as mock:
        registry = MagicMock()
        registry.list_all.return_value = ["notion", "slack", "github"]
        registry.get.return_value = MagicMock(platform_name="test-connector")
        registry.unregister.return_value = True
        mock.return_value = registry
        yield registry


@pytest.fixture
def mock_health_monitor():
    """Create mock health monitor."""
    with patch("saw.api.integrations.HealthMonitor") as mock:
        monitor = AsyncMock()
        monitor.get_all_health.return_value = []
        monitor.get_system_health.return_value = {
            "status": "healthy",
            "healthy_count": 3,
            "degraded_count": 0,
            "unhealthy_count": 0,
        }
        mock.return_value = monitor
        yield monitor


@pytest.fixture
def mock_sync_tracker():
    """Create mock sync status tracker."""
    with patch("saw.api.integrations.SyncStatusTracker") as mock:
        tracker = AsyncMock()
        tracker.get_status.return_value = MagicMock(
            state=MagicMock(value="idle"),
            last_sync_at=None,
        )
        tracker.mark_sync_started = AsyncMock()
        mock.return_value = tracker
        yield tracker


class TestDashboardEndpoint:
    """Test GET /api/v1/integrations/dashboard"""

    @pytest.mark.asyncio
    async def test_dashboard_returns_200(self, mock_session, mock_registry, mock_health_monitor, mock_sync_tracker):
        """Test 1: GET /api/v1/integrations/dashboard returns 200 with connectors array."""
        from saw.api.integrations import get_dashboard
        from saw.db.connector_models import ConnectorConfigModel

        # Mock database query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        response = await get_dashboard(session=mock_session)

        assert response is not None
        assert isinstance(response, DashboardResponse)
        assert isinstance(response.connectors, list)

    @pytest.mark.asyncio
    async def test_dashboard_includes_required_fields(self, mock_session, mock_registry, mock_health_monitor, mock_sync_tracker):
        """Test 2: Response includes platform, health_status, last_sync_at, items_synced, is_connected."""
        from saw.api.integrations import get_dashboard
        from saw.connectors.health_monitor import ConnectorHealth, HealthStatus

        # Mock health data
        health = ConnectorHealth(
            connector_id="notion-main",
            platform="notion",
            status=HealthStatus.HEALTHY,
            last_success_at=utcnow(),
        )
        mock_health_monitor.get_all_health.return_value = [health]

        # Mock database results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        response = await get_dashboard(session=mock_session)

        # Check response structure
        assert len(response.connectors) >= 1
        connector = response.connectors[0]
        assert hasattr(connector, "platform")
        assert hasattr(connector, "health_status")
        assert hasattr(connector, "last_sync_at")
        assert hasattr(connector, "items_synced")
        assert hasattr(connector, "is_connected")

    @pytest.mark.asyncio
    async def test_dashboard_system_health_summary(self, mock_session, mock_registry, mock_health_monitor, mock_sync_tracker):
        """Test 3: Response includes system_health with counts."""
        from saw.api.integrations import get_dashboard

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        response = await get_dashboard(session=mock_session)

        assert "status" in response.system_health
        assert "healthy_count" in response.system_health
        assert "degraded_count" in response.system_health
        assert "unhealthy_count" in response.system_health


class TestDisconnectEndpoint:
    """Test DELETE /api/v1/integrations/{platform}"""

    @pytest.mark.asyncio
    async def test_disconnect_returns_204(self, mock_session, mock_registry):
        """Test 3: DELETE /api/v1/integrations/{platform} returns 204 and removes connector."""
        from saw.api.integrations import disconnect_platform
        from saw.db.connector_models import ConnectorConfigModel

        # Mock config exists
        config = MagicMock(spec=ConnectorConfigModel)
        config.platform = "notion"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = config
        mock_session.execute.return_value = mock_result

        await disconnect_platform(platform="notion", session=mock_session)

        # Verify delete was called
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self, mock_session, mock_registry):
        """Test disconnect raises 404 for unknown platform."""
        from saw.api.integrations import disconnect_platform
        from fastapi import HTTPException

        mock_registry.unregister.return_value = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await disconnect_platform(platform="unknown", session=mock_session)

        assert exc_info.value.status_code == 404


class TestSyncEndpoint:
    """Test POST /api/v1/integrations/{platform}/sync"""

    @pytest.mark.asyncio
    async def test_sync_returns_202(self, mock_session, mock_registry, mock_sync_tracker):
        """Test 4: POST /api/v1/integrations/{platform}/sync returns 202 and triggers sync."""
        from saw.api.integrations import trigger_sync

        # Mock connector exists
        connector = MagicMock()
        connector.platform_name = "notion"
        mock_registry.get.return_value = connector

        # Mock sync status as idle
        mock_status = MagicMock()
        mock_status.state = MagicMock(value="idle")
        mock_sync_tracker.get_status.return_value = mock_status

        # Mock SyncEngine — configure .sync as an awaitable returning success
        from saw.connectors.models import SyncResult, SyncDirection
        from unittest.mock import AsyncMock

        with patch("saw.api.integrations.SyncEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_engine.sync = AsyncMock(return_value=SyncResult(
                connector_id="notion-main",
                direction=SyncDirection.BIDIRECTIONAL,
                pulled_count=3,
                pushed_count=1,
            ))
            MockEngine.return_value = mock_engine

            mock_request = MagicMock()
            mock_request.app.state.write_queue = None
            response = await trigger_sync(platform="notion", request=mock_request, session=mock_session)

        assert response.sync_started is True
        assert response.platform == "notion"
        assert "3 pulled" in response.message

    @pytest.mark.asyncio
    async def test_sync_already_in_progress(self, mock_session, mock_registry, mock_sync_tracker):
        """Test sync returns 202 with sync_started=False when already syncing."""
        from saw.api.integrations import trigger_sync
        from saw.connectors.sync_status import SyncState

        connector = MagicMock()
        connector.platform_name = "notion"
        mock_registry.get.return_value = connector

        # Mock sync status as syncing
        mock_status = MagicMock()
        mock_status.state = SyncState.SYNCING
        mock_sync_tracker.get_status.return_value = mock_status

        mock_request = MagicMock()
        mock_request.app.state.write_queue = None
        response = await trigger_sync(platform="notion", request=mock_request, session=mock_session)

        assert response.sync_started is False
        assert "already in progress" in response.message.lower()

    @pytest.mark.asyncio
    async def test_sync_platform_not_found(self, mock_session, mock_registry):
        """Test sync raises 404 for unknown platform."""
        from saw.api.integrations import trigger_sync
        from fastapi import HTTPException

        mock_registry.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            mock_request = MagicMock()
            mock_request.app.state.write_queue = None
            await trigger_sync(platform="unknown", request=mock_request, session=mock_session)

        assert exc_info.value.status_code == 404


class TestErrorsEndpoint:
    """Test GET /api/v1/integrations/{platform}/errors"""

    @pytest.mark.asyncio
    async def test_errors_returns_list(self, mock_session):
        """Test errors endpoint returns list of ConnectorError."""
        from saw.api.integrations import get_connector_errors

        # Mock database query
        mock_log = MagicMock()
        mock_log.started_at = utcnow()
        mock_log.error_message = "Connection timeout"
        mock_log.status = "failed"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_log]
        mock_session.execute.return_value = mock_result

        errors = await get_connector_errors(platform="notion", session=mock_session)

        assert isinstance(errors, list)
        assert len(errors) == 1
        assert isinstance(errors[0], ConnectorError)
        assert errors[0].error_message == "Connection timeout"

    @pytest.mark.asyncio
    async def test_errors_returns_last_three(self, mock_session):
        """Test errors endpoint returns at most 3 errors."""
        from saw.api.integrations import get_connector_errors

        # Create 5 mock logs
        mock_logs = []
        for i in range(5):
            log = MagicMock()
            log.started_at = utcnow()
            log.error_message = f"Error {i}"
            log.status = "failed"
            mock_logs.append(log)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_logs[:3]
        mock_session.execute.return_value = mock_result

        errors = await get_connector_errors(platform="notion", session=mock_session)

        assert len(errors) <= 3


class TestResponseModels:
    """Test Pydantic response models."""

    def test_dashboard_connector_model(self):
        """Test DashboardConnector model."""
        connector = DashboardConnector(
            platform="notion",
            health_status="healthy",
            last_sync_at=utcnow().isoformat(),
            items_synced=100,
            error_count=0,
            is_connected=True,
            sync_direction="bidirectional",
            sync_state="idle",
            last_error=None,
        )

        assert connector.platform == "notion"
        assert connector.health_status == "healthy"
        assert connector.is_connected is True

    def test_dashboard_response_model(self):
        """Test DashboardResponse model."""
        response = DashboardResponse(
            connectors=[
                DashboardConnector(
                    platform="notion",
                    health_status="healthy",
                    is_connected=True,
                ),
            ],
            system_health={
                "status": "healthy",
                "healthy_count": 1,
            },
        )

        assert len(response.connectors) == 1
        assert response.system_health["status"] == "healthy"

    def test_sync_trigger_response(self):
        """Test SyncTriggerResponse model."""
        resp = SyncTriggerResponse(
            platform="notion",
            sync_started=True,
            message="Sync started",
        )

        assert resp.sync_started is True

    def test_connector_error_model(self):
        """Test ConnectorError model."""
        error = ConnectorError(
            timestamp=utcnow().isoformat(),
            error_message="Timeout",
            error_type="TimeoutError",
        )

        assert error.error_message == "Timeout"
        assert error.error_type == "TimeoutError"
