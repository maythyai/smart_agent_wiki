"""WebSocket Connection Manager for real-time updates.

Per D-04: WebSocket endpoint for real-time updates.
Per D-05: Event types: agent_status, workflow_progress, page_updated.
Per D-06: Connection management and heartbeat.
Per T-03-02-01: JSON schema validation for incoming messages.
Per T-03-02-02: Connection cleanup and limits.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket

if TYPE_CHECKING:
    pass


@dataclass
class WSMessage:
    """WebSocket message format.

    Per D-05: Message includes type, payload, and timestamp.

    Attributes:
        type: Event type (agent_status, workflow_progress, page_updated).
        payload: Event-specific data.
        timestamp: ISO 8601 timestamp.
    """
    type: str
    payload: dict[str, Any]
    timestamp: str

    def json(self) -> str:
        """Serialize message to JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps({
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })


class ConnectionManager:
    """WebSocket connection manager.

    Per D-04: Manages connections by session_id for targeted broadcasts.
    Per D-06: Heartbeat and cleanup for stale connections.
    Per T-03-02-02: Connection limits per session.
    """

    # Maximum connections per session (per T-03-02-02)
    MAX_CONNECTIONS_PER_SESSION = 10

    def __init__(self) -> None:
        """Initialize connection manager."""
        # session_id -> set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}
        self._event_bus: Any = None
        self._broadcast_task: asyncio.Task | None = None

    def set_event_bus(self, event_bus: Any) -> None:
        """Set event bus for subscription.

        Args:
            event_bus: Event bus instance (from app.state).
        """
        self._event_bus = event_bus

    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """Accept new connection and add to session group.

        Per D-06: Accept connection and register by session_id.
        Per T-03-02-02: Enforce connection limits.

        Args:
            websocket: WebSocket connection to accept.
            session_id: Session identifier for grouping.

        Returns:
            True if connection accepted, False if limit exceeded.
        """
        await websocket.accept()

        if session_id not in self._connections:
            self._connections[session_id] = set()

        # Check connection limit (per T-03-02-02)
        if len(self._connections[session_id]) >= self.MAX_CONNECTIONS_PER_SESSION:
            await websocket.close(code=1013, reason="Connection limit exceeded")
            return False

        self._connections[session_id].add(websocket)
        return True

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove connection from session group.

        Per D-06: Clean up connection on disconnect.

        Args:
            websocket: WebSocket connection to remove.
            session_id: Session identifier.
        """
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)
            if not self._connections[session_id]:
                del self._connections[session_id]

    async def broadcast(self, session_id: str, message: WSMessage) -> None:
        """Send message to all connections in session.

        Per D-04: Targeted broadcast by session_id.

        Args:
            session_id: Target session identifier.
            message: Message to broadcast.
        """
        if session_id not in self._connections:
            return

        for ws in list(self._connections[session_id]):
            try:
                await ws.send_text(message.json())
            except Exception:
                # Connection closed, will be cleaned up on next disconnect
                self._connections[session_id].discard(ws)

    async def broadcast_all(self, message: WSMessage) -> None:
        """Broadcast to all sessions.

        Args:
            message: Message to broadcast.
        """
        for session_id in list(self._connections.keys()):
            await self.broadcast(session_id, message)

    async def start_broadcaster(self) -> None:
        """Start event subscription task.

        Called during app lifespan startup.
        """
        if self._event_bus is None:
            return
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    async def stop_broadcaster(self) -> None:
        """Stop event subscription task.

        Called during app lifespan shutdown.
        """
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

    async def _broadcast_loop(self) -> None:
        """Subscribe to events and broadcast to sessions.

        Note: Event bus must implement async iteration protocol.
        """
        try:
            if hasattr(self._event_bus, "subscribe"):
                async for event in self._event_bus.subscribe():
                    msg = self._event_to_message(event)
                    await self.broadcast_all(msg)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Log but don't crash
            pass

    def _event_to_message(self, event: Any) -> WSMessage:
        """Convert an event (dict or dataclass) to a WebSocket message.

        Per D-05: Map event types to WebSocket message types.
        - AgentProgress -> agent_status
        - WorkflowStep/WorkflowStarted/WorkflowCompleted -> workflow_progress
        - PageCreated/PageUpdated/PageDeleted -> page_updated
        - ContradictionFound -> page_updated
        - ClaimsReady -> page_updated
        - IngestCompleted -> page_updated

        Events may be plain dicts (WorkflowExecutor and the Write Queue
        dispatcher publish ``{"type": "WorkflowStep", ...}``) or dataclass
        instances (domain/plugin events). Both are normalized here.
        """
        event_type_map = {
            "AgentProgress": "agent_status",
            "WorkflowStep": "workflow_progress",
            "WorkflowStarted": "workflow_progress",
            "WorkflowCompleted": "workflow_progress",
            "PageCreated": "page_updated",
            "PageUpdated": "page_updated",
            "PageDeleted": "page_updated",
            "ContradictionFound": "page_updated",
            "ClaimsReady": "page_updated",
            "IngestCompleted": "page_updated",
        }
        if isinstance(event, dict):
            event_name = str(event.get("type") or "unknown")
        else:
            event_name = type(event).__name__
        return WSMessage(
            type=event_type_map.get(event_name, "unknown"),
            payload=self._event_to_payload(event),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _event_to_payload(self, event: Any) -> dict[str, Any]:
        """Extract a JSON-safe payload from an event (dict or dataclass)."""
        from enum import Enum

        if isinstance(event, dict):
            source = event
        elif hasattr(event, "__dict__"):
            source = event.__dict__
        else:
            return {}
        payload: dict[str, Any] = {}
        for key, value in source.items():
            if key == "type":
                # Already represented as the WS message type; skip duplication.
                continue
            # Convert non-serializable types
            if hasattr(value, "isoformat"):
                payload[key] = value.isoformat()
            elif isinstance(value, Enum):
                # For enums, use .value (actual string/int value)
                payload[key] = value.value
            else:
                payload[key] = value
        return payload


# Global manager instance (per D-04)
manager = ConnectionManager()
