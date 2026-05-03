"""Tests for Integration WebSocket endpoint.

Plan 16-01: WebSocket server infrastructure.
Tests: WebSocket endpoint at /ws/integrations, subscribe/unsubscribe, health broadcasts.
"""
from __future__ import annotations

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from fastapi import FastAPI


def utcnow():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket for testing."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock()
    return ws


class TestIntegrationsWebSocketEndpoint:
    """Test WebSocket endpoint at /ws/integrations."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with WebSocket router."""
        from saw.api.integrations_ws import router as integrations_ws_router

        app = FastAPI()
        app.include_router(integrations_ws_router, prefix="/ws")
        return app

    @pytest.mark.asyncio
    async def test_websocket_upgrades_at_integrations_endpoint(self, app, mock_websocket):
        """Test 1: GET /ws/integrations upgrades to WebSocket."""
        from saw.api.integrations_ws import integrations_websocket
        from saw.api.websocket import manager

        # Clear any existing connections
        manager.active_connections.clear()

        # Mock the receive_text to simulate disconnect
        mock_websocket.receive_text.side_effect = Exception("Disconnected")

        try:
            await integrations_websocket(mock_websocket)
        except Exception:
            pass  # Expected due to disconnect

        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_receives_connection_status_on_connect(self, mock_websocket):
        """Test 2: Client receives connection_status message on connect."""
        from saw.api.integrations_ws import integrations_websocket
        from saw.api.websocket import manager

        # Clear any existing connections
        manager.active_connections.clear()

        # Mock receive to return disconnect after first call
        mock_websocket.receive_text.side_effect = Exception("Disconnected")

        try:
            await integrations_websocket(mock_websocket)
        except Exception:
            pass

        # Verify connection_status was sent
        assert mock_websocket.send_json.call_count >= 1

        # Check the first call contains connection_status
        first_call = mock_websocket.send_json.call_args_list[0]
        message = first_call[0][0]
        assert message["type"] == "connection_status"
        assert message["data"]["connected"] is True
        assert "client_id" in message["data"]

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe_messages(self, mock_websocket):
        """Test 3: Client can send subscribe/unsubscribe messages for platforms."""
        from saw.api.integrations_ws import integrations_websocket
        from saw.api.websocket import manager

        # Clear any existing connections
        manager.active_connections.clear()

        # Simulate subscribe, then unsubscribe, then disconnect
        messages = [
            json.dumps({"action": "subscribe", "platform": "notion"}),
            json.dumps({"action": "unsubscribe", "platform": "notion"}),
        ]
        mock_websocket.receive_text.side_effect = messages + [Exception("Disconnected")]

        try:
            await integrations_websocket(mock_websocket)
        except Exception:
            pass

        # Should have: connection_status, subscribed, unsubscribed
        assert mock_websocket.send_json.call_count >= 2

        # Check for subscribed confirmation
        calls = [c[0][0] for c in mock_websocket.send_json.call_args_list]
        subscribed_msg = next((m for m in calls if m.get("type") == "subscribed"), None)
        assert subscribed_msg is not None
        assert subscribed_msg["platform"] == "notion"

    @pytest.mark.asyncio
    async def test_health_status_change_triggers_broadcast(self):
        """Test 4: HealthMonitor status changes trigger broadcasts to subscribers."""
        from saw.api.integrations_ws import broadcast_health_change
        from saw.api.websocket import ConnectionManager
        from saw.connectors.health_monitor import ConnectorHealth, HealthStatus

        # Create a test manager with a mock client
        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, "test-client")
        manager.subscribe("notion", "test-client")

        # Create mock health
        health = ConnectorHealth(
            connector_id="notion-main",
            platform="notion",
            status=HealthStatus.DEGRADED,
            last_success_at=utcnow(),
            consecutive_failures=2,
            last_error="Connection timeout",
        )

        # Broadcast health change
        await broadcast_health_change("notion", health, manager)

        # Verify broadcast was sent
        ws.send_json.assert_called_once()

        message = ws.send_json.call_args[0][0]
        assert message["type"] == "connector_health"
        assert message["platform"] == "notion"
        assert message["data"]["status"] == "degraded"


class TestBroadcastFunctions:
    """Test broadcast helper functions."""

    @pytest.mark.asyncio
    async def test_broadcast_health_change_format(self):
        """Test health change broadcast message format."""
        from saw.api.integrations_ws import broadcast_health_change
        from saw.api.websocket import ConnectionManager
        from saw.connectors.health_monitor import ConnectorHealth, HealthStatus

        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, "test-client")
        manager.subscribe("slack", "test-client")

        health = ConnectorHealth(
            connector_id="slack-main",
            platform="slack",
            status=HealthStatus.HEALTHY,
            last_success_at=utcnow(),
        )

        await broadcast_health_change("slack", health, manager)

        message = ws.send_json.call_args[0][0]
        assert message["type"] == "connector_health"
        assert "last_success_at" in message["data"]
        assert "last_failure_at" in message["data"]
        assert "consecutive_failures" in message["data"]

    @pytest.mark.asyncio
    async def test_broadcast_sync_progress_format(self):
        """Test sync progress broadcast message format."""
        from saw.api.integrations_ws import broadcast_sync_progress
        from saw.api.websocket import ConnectionManager
        from saw.connectors.sync_status import SyncStatus, SyncState

        manager = ConnectionManager()
        ws = AsyncMock()
        await manager.connect(ws, "test-client")
        manager.subscribe("github", "test-client")

        # SyncStatus uses items_pending (not items_synced)
        status = SyncStatus(
            connector_id="github-main",
            platform="github",
            state=SyncState.SYNCING,
            items_pending=50,
        )

        await broadcast_sync_progress("github", status, manager)

        message = ws.send_json.call_args[0][0]
        assert message["type"] == "sync_progress"
        assert message["platform"] == "github"
        assert message["data"]["state"] == "syncing"

    @pytest.mark.asyncio
    async def test_broadcast_only_to_subscribers(self):
        """Test broadcast only goes to subscribers of that platform."""
        from saw.api.integrations_ws import broadcast_health_change
        from saw.api.websocket import ConnectionManager
        from saw.connectors.health_monitor import ConnectorHealth, HealthStatus

        manager = ConnectionManager()

        # Two clients, only one subscribed to notion
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")
        manager.subscribe("notion", "client-1")  # Only client-1 subscribed

        health = ConnectorHealth(
            connector_id="notion-main",
            platform="notion",
            status=HealthStatus.HEALTHY,
        )

        await broadcast_health_change("notion", health, manager)

        # client-1 should receive
        ws1.send_json.assert_called_once()

        # client-2 should NOT receive
        ws2.send_json.assert_not_called()


class TestInvalidMessages:
    """Test handling of invalid messages."""

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(self, mock_websocket):
        """Test invalid JSON returns error message."""
        from saw.api.integrations_ws import integrations_websocket
        from saw.api.websocket import manager

        manager.active_connections.clear()

        # Send invalid JSON, then disconnect
        mock_websocket.receive_text.side_effect = [
            "not valid json",
            Exception("Disconnected"),
        ]

        try:
            await integrations_websocket(mock_websocket)
        except Exception:
            pass

        # Find error message in calls
        calls = [c[0][0] for c in mock_websocket.send_json.call_args_list]
        error_msg = next((m for m in calls if m.get("type") == "error"), None)

        assert error_msg is not None
        assert "Invalid JSON" in error_msg.get("message", "")

    @pytest.mark.asyncio
    async def test_unknown_action_ignored(self, mock_websocket):
        """Test unknown action is ignored gracefully."""
        from saw.api.integrations_ws import integrations_websocket
        from saw.api.websocket import manager

        manager.active_connections.clear()

        # Send unknown action, then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps({"action": "unknown_action"}),
            Exception("Disconnected"),
        ]

        try:
            await integrations_websocket(mock_websocket)
        except Exception:
            pass

        # Should have connection_status, no error
        calls = [c[0][0] for c in mock_websocket.send_json.call_args_list]
        error_msg = next((m for m in calls if m.get("type") == "error"), None)

        # Unknown action should NOT produce an error
        assert error_msg is None
