"""Singleton registry for available connectors.

Plan 10-01: Connector registry for platform management.
"""
from __future__ import annotations

from typing import Optional

from saw.connectors.protocol import UnifiedConnectorInterface


class ConnectorRegistry:
    """Singleton registry for available connectors.

    Per AUTH-01: Unified OAuth flow for all OAuth platforms.

    This registry maintains a single instance per process that tracks
    all available platform connectors.
    """

    _instance: Optional["ConnectorRegistry"] = None
    _connectors: dict[str, UnifiedConnectorInterface]

    def __new__(cls) -> "ConnectorRegistry":
        """Create or return singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connectors = {}
        return cls._instance

    def register(self, connector: UnifiedConnectorInterface) -> None:
        """Register a connector instance.

        Args:
            connector: Connector implementing UnifiedConnectorInterface.
        """
        self._connectors[connector.platform_name] = connector

    def get(self, platform: str) -> Optional[UnifiedConnectorInterface]:
        """Get connector by platform name.

        Args:
            platform: Platform identifier (notion, slack, github, etc.).

        Returns:
            Connector instance or None if not registered.
        """
        return self._connectors.get(platform)

    def list_all(self) -> list[str]:
        """List all registered platform names.

        Returns:
            List of platform identifiers.
        """
        return list(self._connectors.keys())

    def unregister(self, platform: str) -> bool:
        """Remove connector from registry.

        Args:
            platform: Platform identifier to remove.

        Returns:
            True if connector existed and was removed, False otherwise.
        """
        if platform in self._connectors:
            del self._connectors[platform]
            return True
        return False

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None
