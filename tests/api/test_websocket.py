"""Tests for WebSocket connection manager.

Plan 16-01: WebSocket server infrastructure.
Tests: ConnectionManager, broadcast, subscribe/unsubscribe, heartbeat.
"""
from __future__ import annotations

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


class TestConnectionManager:
    """Test WebSocket ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connection_manager_tracks_multiple_clients(self):
        """Test 1: ConnectionManager tracks multiple client connections."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()

        # Create mock websockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        # Connect two clients
        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        assert "client-1" in manager.active_connections
        assert "client-2" in manager.active_connections
        assert len(manager.active_connections) == 2

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self):
        """Test 2: broadcast() sends message to all connected clients."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()

        # Create mock websockets
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        # Broadcast message
        message = {"type": "test", "data": "hello"}
        await manager.broadcast(message)

        # Verify both clients received the message
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_disconnect_removes_client(self):
        """Test 3: disconnect() removes client from active list."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        # Disconnect client-1
        manager.disconnect("client-1")

        assert "client-1" not in manager.active_connections
        assert "client-2" in manager.active_connections
        assert len(manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_heartbeat_sends_ping_every_30_seconds(self):
        """Test 4: Heartbeat task sends ping every 30 seconds."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()
        manager.heartbeat_interval = 0.1  # Speed up for testing

        ws = AsyncMock()
        await manager.connect(ws, "client-1")

        # Wait for at least one heartbeat
        await asyncio.sleep(0.15)

        # Verify ping was sent
        assert ws.send_json.call_count >= 1

        # Check ping message format
        call_args = ws.send_json.call_args
        if call_args:
            message = call_args[0][0]
            assert message["type"] == "ping"
            assert "timestamp" in message

        # Cleanup
        manager.disconnect("client-1")

    @pytest.mark.asyncio
    async def test_unresponsive_clients_disconnected_after_timeout(self):
        """Test 5: Clients that don't respond to ping within 60s are disconnected."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()
        manager.heartbeat_interval = 0.05
        manager.client_timeout = 0.15  # 3x heartbeat for testing

        # Create a client that will fail to receive
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("Connection lost")

        await manager.connect(ws, "client-1")

        # Wait for heartbeat to detect and disconnect
        await asyncio.sleep(0.2)

        # Client should be disconnected
        assert "client-1" not in manager.active_connections


class TestSubscriptionFiltering:
    """Test platform subscription filtering."""

    @pytest.mark.asyncio
    async def test_subscribe_to_platform(self):
        """Test subscribing to a platform."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()

        ws = AsyncMock()
        await manager.connect(ws, "client-1")

        manager.subscribe("notion", "client-1")

        assert "notion" in manager.subscriptions
        assert "client-1" in manager.subscriptions["notion"]

    @pytest.mark.asyncio
    async def test_unsubscribe_from_platform(self):
        """Test unsubscribing from a platform."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()

        ws = AsyncMock()
        await manager.connect(ws, "client-1")

        manager.subscribe("notion", "client-1")
        manager.unsubscribe("notion", "client-1")

        assert "client-1" not in manager.subscriptions.get("notion", set())

    @pytest.mark.asyncio
    async def test_broadcast_to_subscribers_only(self):
        """Test broadcast_to_subscribers sends only to subscribed clients."""
        from saw.api.websocket import ConnectionManager

        manager = ConnectionManager()

        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "client-1")
        await manager.connect(ws2, "client-2")

        # Only client-1 subscribes to notion
        manager.subscribe("notion", "client-1")

        message = {"type": "connector_health", "platform": "notion"}
        await manager.broadcast_to_subscribers("notion", message)

        # client-1 should receive
        ws1.send_json.assert_called_once_with(message)

        # client-2 should NOT receive
        ws2.send_json.assert_not_called()
