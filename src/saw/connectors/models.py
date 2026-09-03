"""Data models for connector configuration and status.

Plan 10-01: Core Connector Models.
Per AUTH-04: Token masking in logs/API responses (last 4 chars only).
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime

from saw.connectors.protocol import SyncDirection
from saw.domain.utils import utcnow  # noqa: F401


class ConnectorStatus(enum.Enum):
    """Status of a connector connection."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"


class TokenMasker:
    """Masks sensitive tokens in logs and API responses.

    Per AUTH-04: Tokens masked in logs/API responses (last 4 chars only).
    """

    @staticmethod
    def mask_token(token: str | None) -> str:
        """Return masked token showing only last 4 characters.

        Per AUTH-04: Tokens masked in logs/API responses (last 4 chars only).

        Args:
            token: The token string to mask.

        Returns:
            Masked token with only last 4 characters visible.
            Returns "****" for None, empty, or short tokens.
        """
        if not token:
            return "****"
        if len(token) <= 4:
            return "****"
        return f"****{token[-4:]}"

    @staticmethod
    def mask_dict(d: dict, keys: list[str]) -> dict:
        """Return copy of dict with specified keys masked.

        Args:
            d: Dictionary to mask.
            keys: Keys whose values should be masked.

        Returns:
            Copy of dict with sensitive keys masked.
        """
        result = d.copy()
        for key in keys:
            if key in result:
                result[key] = TokenMasker.mask_token(result[key])
        return result


@dataclass
class ConnectorConfig:
    """Configuration for a third-party platform connector.

    Attributes:
        id: Unique configuration identifier.
        user_id: Owner user ID.
        platform: Platform identifier (notion, slack, github, etc.).
        name: User-defined name for this connection.
        credentials_encrypted: Encrypted OAuth tokens (Fernet).
        sync_direction: Direction of synchronization.
        last_sync_at: Timestamp of last successful sync.
        sync_interval: Seconds between syncs.
        is_active: Whether sync is enabled.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        config: Platform-specific configuration JSON.
    """
    id: str
    user_id: str
    platform: str
    name: str
    credentials_encrypted: str | None = None
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    last_sync_at: datetime | None = None
    sync_interval: int = 3600  # seconds
    is_active: bool = True
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime | None = None
    config: dict = field(default_factory=dict)


@dataclass
class SyncResult:
    """Result of a synchronization operation.

    Attributes:
        connector_id: ID of the connector that performed the sync.
        direction: Direction of the sync.
        pulled_count: Number of items pulled from platform.
        pushed_count: Number of items pushed to platform.
        conflicts_count: Number of conflicts detected.
        errors: List of error messages.
        started_at: When sync started.
        completed_at: When sync completed.
        duration_ms: Duration in milliseconds.
        success: Whether sync completed without errors.
    """
    connector_id: str
    direction: SyncDirection
    pulled_count: int = 0
    pushed_count: int = 0
    conflicts_count: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None
    duration_ms: int | None = None

    @property
    def success(self) -> bool:
        """Return True if sync completed without errors."""
        return len(self.errors) == 0
