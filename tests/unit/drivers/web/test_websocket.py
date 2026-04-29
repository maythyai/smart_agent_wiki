"""Tests for WebSocket ConnectionManager and endpoint.

Tests:
- ConnectionManager.connect() adds connection to session
- ConnectionManager.disconnect() removes connection
- ConnectionManager.broadcast() sends message to all connections
- WebSocket message format includes type, payload, timestamp
- Event type mapping: AgentProgress -> agent_status, etc.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from saw.drivers.web.websocket import ConnectionManager, WSMessage


class TestWSMessage:
    """Tests for WSMessage dataclass."""

    def test_ws_message_json(self):
        """WSMessage.json() should serialize to valid JSON."""
        msg = WSMessage(
            type="agent_status",
            payload={"agent": "Librarian"},
            timestamp="2024-01-01T00:00:00Z",
        )
        expected = '{"type": "agent_status", "payload": {"agent": "Librarian"}, "timestamp": "2024-01-01T00:00:00Z"}'
        assert msg.json() == expected

    def test_ws_message_with_complex_payload(self):
        """WSMessage should handle complex payloads."""
        msg = WSMessage(
            type="workflow_progress",
            payload={
                "workflow": "ingest",
                "step": 1,
                "total": 5,
                "status": "running",
            },
            timestamp="2024-01-01T00:00:00Z",
        )
        json_str = msg.json()
        assert '"workflow": "ingest"' in json_str
        assert '"step": 1' in json_str


class TestConnectionManagerConnect:
    """Tests for ConnectionManager.connect()."""

    @pytest.mark.asyncio
    async def test_connect_adds_to_session(self):
        """connect() should add connection to session group."""
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.accept = AsyncMock()

        accepted = await manager.connect(ws, "session-1")

        assert accepted is True
        assert "session-1" in manager._connections
        assert ws in manager._connections["session-1"]

    @pytest.mark.asyncio
    async def test_connect_multiple_connections_same_session(self):
        """Multiple connections should be allowed for same session."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "session-1")
        accepted2 = await manager.connect(ws2, "session-1")

        assert accepted2 is True
        assert len(manager._connections["session-1"]) == 2

    @pytest.mark.asyncio
    async def test_connect_enforces_limit(self):
        """connect() should enforce connection limit per session."""
        manager = ConnectionManager()
        manager.MAX_CONNECTIONS_PER_SESSION = 2

        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.close = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.close = AsyncMock()
        ws3 = AsyncMock()
        ws3.accept = AsyncMock()
        ws3.close = AsyncMock()

        await manager.connect(ws1, "session-1")
        await manager.connect(ws2, "session-1")
        accepted3 = await manager.connect(ws3, "session-1")

        assert accepted3 is False
        ws3.close.assert_called_once()


class TestConnectionManagerDisconnect:
    """Tests for ConnectionManager.disconnect()."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        """disconnect() should remove connection from session."""
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.accept = AsyncMock()

        await manager.connect(ws, "session-1")
        manager.disconnect(ws, "session-1")

        assert "session-1" not in manager._connections

    @pytest.mark.asyncio
    async def test_disconnect_leaves_other_connections(self):
        """disconnect() should only remove the specified connection."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, "session-1")
        await manager.connect(ws2, "session-1")
        manager.disconnect(ws1, "session-1")

        assert "session-1" in manager._connections
        assert ws2 in manager._connections["session-1"]
        assert ws1 not in manager._connections["session-1"]


class TestConnectionManagerBroadcast:
    """Tests for ConnectionManager.broadcast()."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self):
        """broadcast() should send message to all connections in session."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()

        await manager.connect(ws1, "session-1")
        await manager.connect(ws2, "session-1")

        msg = WSMessage(type="test", payload={"key": "value"}, timestamp="2024-01-01T00:00:00Z")
        await manager.broadcast("session-1", msg)

        ws1.send_text.assert_called_once_with(msg.json())
        ws2.send_text.assert_called_once_with(msg.json())

    @pytest.mark.asyncio
    async def test_broadcast_ignores_closed_connections(self):
        """broadcast() should handle closed connections gracefully."""
        manager = ConnectionManager()
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock(side_effect=Exception("Connection closed"))

        await manager.connect(ws, "session-1")

        msg = WSMessage(type="test", payload={}, timestamp="2024-01-01T00:00:00Z")
        # Should not raise
        await manager.broadcast("session-1", msg)

        # Connection should be removed after error
        assert ws not in manager._connections["session-1"]

    @pytest.mark.asyncio
    async def test_broadcast_all_sends_to_all_sessions(self):
        """broadcast_all() should send to all sessions."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()

        await manager.connect(ws1, "session-1")
        await manager.connect(ws2, "session-2")

        msg = WSMessage(type="test", payload={}, timestamp="2024-01-01T00:00:00Z")
        await manager.broadcast_all(msg)

        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()


class TestEventToMessage:
    """Tests for event to WebSocket message conversion."""

    def test_event_to_message_agent_progress(self):
        """AgentProgress event should map to agent_status."""
        manager = ConnectionManager()

        # Create a mock event with instance attributes
        class AgentProgress:
            def __init__(self):
                self.agent = "Librarian"
                self.status = "running"
                self.task = "indexing"

        event = AgentProgress()
        msg = manager._event_to_message(event)

        assert msg.type == "agent_status"
        assert msg.payload["agent"] == "Librarian"

    def test_event_to_message_workflow_step(self):
        """WorkflowStep event should map to workflow_progress."""
        manager = ConnectionManager()

        class WorkflowStep:
            def __init__(self):
                self.workflow = "ingest"
                self.step = 1

        event = WorkflowStep()
        msg = manager._event_to_message(event)

        assert msg.type == "workflow_progress"
        assert msg.payload["workflow"] == "ingest"

    def test_event_to_message_page_updated(self):
        """PageUpdated event should map to page_updated."""
        manager = ConnectionManager()

        class PageUpdated:
            def __init__(self):
                self.slug = "test-page"
                self.change = "modified"

        event = PageUpdated()
        msg = manager._event_to_message(event)

        assert msg.type == "page_updated"

    def test_event_to_message_contradiction_found(self):
        """ContradictionFound event should map to page_updated."""
        manager = ConnectionManager()

        class ContradictionFound:
            def __init__(self):
                self.claim_a_uuid = "uuid-a"
                self.claim_b_uuid = "uuid-b"

        event = ContradictionFound()
        msg = manager._event_to_message(event)

        assert msg.type == "page_updated"

    def test_event_to_message_unknown_type(self):
        """Unknown event types should map to 'unknown'."""
        manager = ConnectionManager()

        class UnknownEvent:
            def __init__(self):
                self.data = "something"

        event = UnknownEvent()
        msg = manager._event_to_message(event)

        assert msg.type == "unknown"

    def test_event_to_message_handles_datetime(self):
        """Event with datetime should be converted to ISO format."""
        manager = ConnectionManager()

        class EventWithDateTime:
            def __init__(self):
                self.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        event = EventWithDateTime()
        payload = manager._event_to_payload(event)

        assert payload["timestamp"] == "2024-01-01T12:00:00+00:00"

    def test_event_to_message_handles_enum(self):
        """Event with enum should be converted to its name."""
        manager = ConnectionManager()

        from enum import Enum

        class Status(str, Enum):
            RUNNING = "running"
            DONE = "done"

        class EventWithEnum:
            def __init__(self):
                self.status = Status.RUNNING

        event = EventWithEnum()
        payload = manager._event_to_payload(event)

        assert payload["status"] == "running"


class TestBroadcasterLifecycle:
    """Tests for broadcaster start/stop."""

    @pytest.mark.asyncio
    async def test_start_broadcaster_without_event_bus(self):
        """start_broadcaster() should do nothing without event_bus."""
        manager = ConnectionManager()

        await manager.start_broadcaster()

        assert manager._broadcast_task is None

    @pytest.mark.asyncio
    async def test_stop_broadcaster_without_task(self):
        """stop_broadcaster() should handle no task gracefully."""
        manager = ConnectionManager()

        # Should not raise
        await manager.stop_broadcaster()

    @pytest.mark.asyncio
    async def test_stop_broadcaster_cancels_task(self):
        """stop_broadcaster() should cancel running task."""
        manager = ConnectionManager()

        # Create a mock event bus that never yields
        mock_event_bus = MagicMock()
        mock_event_bus.subscribe = AsyncMock(side_effect=asyncio.CancelledError)

        manager.set_event_bus(mock_event_bus)
        await manager.start_broadcaster()

        # Should not raise
        await manager.stop_broadcaster()
        assert manager._broadcast_task is not None


import asyncio
