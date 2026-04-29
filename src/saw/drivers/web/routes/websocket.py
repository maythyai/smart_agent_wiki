"""WebSocket endpoint for real-time updates.

Per D-04: WebSocket endpoint at /ws/{session_id}.
Per D-06: Connection management with heartbeat.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates.

    Per D-04: Accept connections and register with ConnectionManager.
    Per D-06: Handle disconnect and cleanup.

    Args:
        websocket: WebSocket connection.
        session_id: Session identifier for grouping.
    """
    from saw.drivers.web.websocket import manager

    # Attempt to connect (may be rejected due to limit)
    accepted = await manager.connect(websocket, session_id)
    if not accepted:
        return

    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_json()

            # Handle client messages (ping/pong heartbeat)
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    except Exception:
        # Unexpected error - connection will be cleaned up
        pass
    finally:
        # Always cleanup connection
        manager.disconnect(websocket, session_id)