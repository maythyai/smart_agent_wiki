"""WebSocket endpoint for real-time updates.

Per D-04: WebSocket endpoint at /ws/{session_id}.
Per D-06: Connection management with heartbeat.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


def _verify_ws_token(token: str) -> bool:
    """Verify a WebSocket ``?token=`` credential.

    Accepts a JWT access token (the same credential the REST API uses via
    ``Authorization: Bearer``). API-key support can be added here later.
    Returns True iff the token is a valid, unexpired access token.
    """
    try:
        from saw.auth.jwt_auth import AuthConfig, JWTHandler

        JWTHandler(AuthConfig.from_env()).verify_access_token(token)
        return True
    except Exception:
        return False


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates.

    Per D-04: Accept connections and register with ConnectionManager.
    Per D-06: Handle disconnect and cleanup.

    In ``team`` auth mode the stream is gated behind a ``?token=<jwt access
    token>`` query parameter (contract §6.1), mirroring the JWT requirement
    on protected REST routes. In ``local`` mode the loopback connection is
    trusted, so no token is required — the frontend may still send one.

    Args:
        websocket: WebSocket connection.
        session_id: Session identifier for grouping.
    """
    from saw.drivers.web.websocket import manager

    auth_mode = getattr(websocket.app.state, "auth_mode", "local")
    if auth_mode == "team":
        token = websocket.query_params.get("token")
        if not token or not _verify_ws_token(token):
            # Reject the handshake before accepting (Starlette supports
            # closing an un-accepted WebSocket to deny the upgrade).
            await websocket.close(code=4401, reason="unauthorized")
            return

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