"""Protocol definition for third-party platform connectors.

Plan 10-01: Core Connector Protocol.
Per AUTH-04: Unified interface for all OAuth platforms.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable


class SyncDirection(enum.Enum):
    """Direction of data synchronization."""
    PULL = "pull"
    PUSH = "push"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class AuthResult:
    """Result of successful authentication with a platform.

    Attributes:
        access_token: OAuth access token.
        refresh_token: OAuth refresh token (optional).
        expires_at: Token expiration timestamp (optional).
        scopes: Granted permission scopes.
        raw_response: Original platform response for debugging.
    """
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scopes: list[str] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)


@dataclass
class ConnectorItem:
    """Item from a third-party platform.

    Attributes:
        id: Platform-specific identifier.
        title: Item title/name.
        content: Item body content.
        url: URL to original item (optional).
        author: Author/display name (optional).
        created_at: Creation timestamp (optional).
        updated_at: Last update timestamp (optional).
        metadata: Platform-specific fields.
    """
    id: str
    title: str
    content: str
    url: str | None = None
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class UnifiedConnectorInterface(Protocol):
    """Protocol for all third-party platform connectors.

    Per AUTH-01: Unified OAuth flow for all OAuth platforms.
    Per AUTH-04: Tokens masked in logs/API responses.

    This Protocol defines the contract that all platform connectors
    (Notion, Slack, GitHub, Discord, Feishu, etc.) must implement.
    """

    @property
    def platform_name(self) -> str:
        """Platform identifier (e.g., 'notion', 'slack', 'github')."""
        ...

    @property
    def supports_push(self) -> bool:
        """Whether platform supports webhooks/push notifications."""
        ...

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete authentication flow, return auth tokens.

        Args:
            credentials: Platform-specific credentials (OAuth code, API key, etc.)

        Returns:
            AuthResult with tokens and metadata.

        Raises:
            AuthenticationError: If authentication fails.
        """
        ...

    async def get_items(
        self,
        since: datetime | None = None,
        filters: dict | None = None,
    ) -> list[ConnectorItem]:
        """Pull items from platform (incremental if since provided).

        Args:
            since: Only return items updated after this timestamp.
            filters: Platform-specific filters.

        Returns:
            List of items from the platform.
        """
        ...

    async def put_item(self, item: ConnectorItem) -> str:
        """Push item to platform. Return platform item ID.

        Args:
            item: Item to create/update on the platform.

        Returns:
            Platform-specific item ID.

        Raises:
            SyncError: If push fails.
        """
        ...

    async def delete_item(self, item_id: str) -> bool:
        """Delete item from platform. Return success.

        Args:
            item_id: Platform-specific item ID.

        Returns:
            True if deleted, False if not found.

        Raises:
            SyncError: If deletion fails.
        """
        ...

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert platform item to SAW Claim dict.

        Args:
            item: Item from the platform.

        Returns:
            Dict matching Claim schema for SAW ingestion.
        """
        ...

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert SAW Claim dict to platform item format.

        Args:
            claim: SAW Claim dict.

        Returns:
            Item ready for platform push.
        """
        ...


class AuthenticationError(Exception):
    """Raised when platform authentication fails."""
    pass


class SyncError(Exception):
    """Raised when synchronization operation fails."""
    pass
