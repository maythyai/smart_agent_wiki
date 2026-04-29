"""WebSocket message schemas for validation.

Per T-03-02-01: JSON schema validation for incoming messages.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WSMessageModel(BaseModel):
    """WebSocket message schema for outgoing messages.

    Per D-05: Message includes type, payload, and timestamp.
    """
    type: str
    payload: dict[str, Any]
    timestamp: str


class WSPing(BaseModel):
    """Ping message from client.

    Per D-06: Heartbeat message type.
    """
    type: str = "ping"


class WSPong(BaseModel):
    """Pong response from server.

    Per D-06: Heartbeat response.
    """
    type: str = "pong"
    timestamp: str