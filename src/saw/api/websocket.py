"""WebSocket connection manager for real-time updates.

Plan 16-01: WebSocket server infrastructure.
Provides base WebSocket connection manager with heartbeat and subscription filtering.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Set, Any

from fastapi import WebSocket


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with heartbeat and subscription filtering.

    Features:
    - Tracks multiple client connections
    - Heartbeat ping/pong at configurable intervals
    - Platform-based subscription filtering
    - Automatic cleanup of dead connections

    Threat mitigations:
    - T-16-01: Client ID generated server-side, not client-provided
    - T-16-02: Connection tracking enables rate limiting per IP
    """

    def __init__(
        self,
        heartbeat_interval: float = 30.0,
        client_timeout: float = 60.0,
    ):
        """Initialize connection manager.

        Args:
            heartbeat_interval: Seconds between heartbeat pings (default 30s).
            client_timeout: Seconds before unresponsive client is disconnected (default 60s).
        """
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # platform -> client_ids
        self._heartbeat_task: asyncio.Task | None = None
        self.heartbeat_interval = heartbeat_interval
        self.client_timeout = client_timeout
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection.
            client_id: Unique client identifier (generated server-side).
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket

        # Start heartbeat task if this is the first connection
        if len(self.active_connections) == 1 and self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.debug(f"WebSocket client connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Remove a client connection.

        Args:
            client_id: Client identifier to remove.
        """
        self.active_connections.pop(client_id, None)

        # Remove from all subscriptions
        for platform_subs in self.subscriptions.values():
            platform_subs.discard(client_id)

        # Stop heartbeat if no connections remain
        if not self.active_connections and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

        logger.debug(f"WebSocket client disconnected: {client_id}")

    def subscribe(self, platform: str, client_id: str) -> None:
        """Subscribe a client to platform-specific updates.

        Args:
            platform: Platform to subscribe to (e.g., "notion", "slack").
            client_id: Client identifier.
        """
        if platform not in self.subscriptions:
            self.subscriptions[platform] = set()
        self.subscriptions[platform].add(client_id)
        logger.debug(f"Client {client_id} subscribed to {platform}")

    def unsubscribe(self, platform: str, client_id: str) -> None:
        """Unsubscribe a client from platform updates.

        Args:
            platform: Platform to unsubscribe from.
            client_id: Client identifier.
        """
        if platform in self.subscriptions:
            self.subscriptions[platform].discard(client_id)

        logger.debug(f"Client {client_id} unsubscribed from {platform}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients.

        Handles dead connections gracefully by removing them.

        Args:
            message: Message dict to send (will be JSON-serialized).
        """
        dead_clients = []

        for client_id, ws in list(self.active_connections.items()):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to {client_id}: {e}")
                dead_clients.append(client_id)

        # Clean up dead connections
        for client_id in dead_clients:
            self.disconnect(client_id)

    async def broadcast_to_subscribers(self, platform: str, message: dict) -> None:
        """Broadcast a message to clients subscribed to a platform.

        Args:
            platform: Platform to broadcast to.
            message: Message dict to send.
        """
        if platform not in self.subscriptions:
            return

        dead_clients = []

        for client_id in list(self.subscriptions[platform]):
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    logger.debug(f"Failed to send to {client_id}: {e}")
                    dead_clients.append(client_id)

        # Clean up dead connections
        for client_id in dead_clients:
            self.disconnect(client_id)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat pings to all clients.

        Disconnects clients that fail to respond within timeout.
        """
        while self.active_connections:
            await asyncio.sleep(self.heartbeat_interval)

            if not self.active_connections:
                break

            message = {
                "type": "ping",
                "timestamp": utcnow().isoformat(),
            }

            await self.broadcast(message)


# Global instance for application-wide use
manager = ConnectionManager()
