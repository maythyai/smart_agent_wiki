"""Abstract base implementation of UnifiedConnectorInterface.

Plan 10-01: Base connector with common functionality.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    ConnectorItem,
)
from saw.connectors.rate_limiter import RateLimitManager


class BaseConnector(UnifiedConnectorInterface, ABC):
    """Abstract base implementation of UnifiedConnectorInterface.

    Provides common functionality like rate limiting.
    Subclasses must implement abstract methods.
    """

    def __init__(self) -> None:
        """Initialize base connector with rate limiter."""
        self._rate_limiter = RateLimitManager(self.platform_name)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier."""
        ...

    @property
    def supports_push(self) -> bool:
        """Default: supports push (webhooks)."""
        return True

    async def get_items(
        self,
        since: datetime | None = None,
        filters: dict | None = None,
    ) -> list[ConnectorItem]:
        """Pull items with rate limiting.

        Args:
            since: Only return items updated after this timestamp.
            filters: Platform-specific filters.

        Returns:
            List of items from the platform.
        """
        await self._rate_limiter.acquire()
        return await self._do_get_items(since, filters)

    @abstractmethod
    async def _do_get_items(
        self,
        since: datetime | None,
        filters: dict | None,
    ) -> list[ConnectorItem]:
        """Actual implementation of get_items (override in subclass).

        Args:
            since: Only return items updated after this timestamp.
            filters: Platform-specific filters.

        Returns:
            List of items from the platform.
        """
        ...

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert platform item to SAW Claim dict.

        Default implementation. Override for platform-specific format.

        Args:
            item: Item from the platform.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "url": item.url,
            "author": item.author,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "metadata": item.metadata,
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert SAW Claim dict to platform item format.

        Default implementation. Override for platform-specific format.

        Args:
            claim: SAW Claim dict.

        Returns:
            Item ready for platform push.
        """
        return ConnectorItem(
            id=claim.get("id", ""),
            title=claim.get("title", ""),
            content=claim.get("content", ""),
            url=claim.get("url"),
            author=claim.get("author"),
            created_at=claim.get("created_at"),
            updated_at=claim.get("updated_at"),
            metadata=claim.get("metadata", {}),
        )
