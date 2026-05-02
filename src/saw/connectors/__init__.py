"""Connectors package for third-party platform integrations.

Phase 10: Connector Framework Foundation.
"""
from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
    SyncDirection,
    AuthenticationError,
    SyncError,
)
from saw.connectors.models import (
    ConnectorConfig,
    ConnectorStatus,
    SyncResult,
    TokenMasker,
)
from saw.connectors.registry import ConnectorRegistry
from saw.connectors.base_connector import BaseConnector
from saw.connectors.rate_limiter import (
    RateLimitManager,
    PlatformRateLimit,
)

__all__ = [
    # Protocol
    "UnifiedConnectorInterface",
    "AuthResult",
    "ConnectorItem",
    "SyncDirection",
    "AuthenticationError",
    "SyncError",
    # Models
    "ConnectorConfig",
    "ConnectorStatus",
    "SyncResult",
    "TokenMasker",
    # Registry
    "ConnectorRegistry",
    # Base
    "BaseConnector",
    # Rate limiting
    "RateLimitManager",
    "PlatformRateLimit",
]