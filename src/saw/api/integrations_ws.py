"""Integration WebSocket endpoint for real-time dashboard updates.

Plan 16-01: WebSocket server infrastructure.
Provides WebSocket endpoint at /ws/integrations for real-time connector health
and sync progress updates.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from saw.api.websocket import ConnectionManager
from saw.drivers.web.routes.websocket import _verify_ws_token


if TYPE_CHECKING:
    from saw.connectors.health_monitor import ConnectorHealth
    from saw.connectors.sync_status import SyncStatus


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


logger = logging.getLogger(__name__)


router = APIRouter(tags=["websocket"])


@router.websocket("/integrations")
async def integrations_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for integration dashboard updates.

    Clients can:
    1. Receive connection_status on connect
    2. Subscribe/unsubscribe to platform-specific updates
    3. Receive connector_health and sync_progress broadcasts

    Message format (server -> client):
    - {"type": "connection_status", "data": {...}}
    - {"type": "subscribed", "platform": "notion"}
    - {"type": "connector_health", "platform": "...", "data": {...}}
    - {"type": "sync_progress", "platform": "...", "data": {...}}

    Message format (client -> server):
    - {"action": "subscribe", "platform": "notion"}
    - {"action": "unsubscribe", "platform": "notion"}

    Threat mitigations:
    - T-16-01: Client ID generated server-side (UUID)
    - T-16-03: Message handling is stateless, no amplification
    """
    from saw.api.websocket import manager

    # SEC: in team mode the integrations WS is gated behind ?token=<jwt
    # access token>, matching the main /ws/{session_id} endpoint and the
    # protected REST routes. Local mode trusts the loopback connection.
    auth_mode = getattr(websocket.app.state, "auth_mode", "local")
    if auth_mode == "team":
        token = websocket.query_params.get("token")
        if not token or not _verify_ws_token(token):
            await websocket.close(code=4401, reason="unauthorized")
            return

    # Generate client ID server-side (T-16-01)
    client_id = str(uuid.uuid4())[:8]
    await manager.connect(websocket, client_id)

    try:
        # Send initial connection status
        await websocket.send_json({
            "type": "connection_status",
            "data": {
                "connected": True,
                "client_id": client_id,
                "server_time": utcnow().isoformat(),
            },
        })

        # Message loop
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })
                continue

            action = msg.get("action")
            platform = msg.get("platform")

            if action == "subscribe" and platform:
                manager.subscribe(platform, client_id)
                await websocket.send_json({
                    "type": "subscribed",
                    "platform": platform,
                })
            elif action == "unsubscribe" and platform:
                manager.unsubscribe(platform, client_id)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "platform": platform,
                })
            # Unknown actions are ignored gracefully

    except WebSocketDisconnect:
        logger.debug(f"WebSocket client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        manager.disconnect(client_id)


async def broadcast_health_change(
    platform: str,
    health: "ConnectorHealth",
    manager: ConnectionManager | None = None,
) -> None:
    """Broadcast health status change to platform subscribers.

    Called by HealthMonitor when connector status changes.

    Args:
        platform: Platform identifier (e.g., "notion", "slack").
        health: ConnectorHealth dataclass with current status.
        manager: ConnectionManager instance (uses global if None).
    """
    if manager is None:
        from saw.api.websocket import manager as global_manager
        manager = global_manager

    await manager.broadcast_to_subscribers(platform, {
        "type": "connector_health",
        "platform": platform,
        "data": {
            "status": health.status.value,
            "last_success_at": health.last_success_at.isoformat() if health.last_success_at else None,
            "last_failure_at": health.last_failure_at.isoformat() if health.last_failure_at else None,
            "consecutive_failures": health.consecutive_failures,
            "last_error": health.last_error,
        },
    })


async def broadcast_sync_progress(
    platform: str,
    status: "SyncStatus",
    manager: ConnectionManager | None = None,
) -> None:
    """Broadcast sync progress update to platform subscribers.

    Called by SyncEngine during sync operations.

    Args:
        platform: Platform identifier.
        status: SyncStatus dataclass with current progress.
        manager: ConnectionManager instance (uses global if None).
    """
    if manager is None:
        from saw.api.websocket import manager as global_manager
        manager = global_manager

    await manager.broadcast_to_subscribers(platform, {
        "type": "sync_progress",
        "platform": platform,
        "data": {
            "state": status.state.value,
            "items_synced": status.items_synced,
            "items_total": status.items_total,
            "completion_percent": status.completion_percent,
            "items_pending": status.items_pending,
            "last_error": status.last_error,
            "last_sync_at": status.last_sync_at.isoformat() if status.last_sync_at else None,
        },
    })
