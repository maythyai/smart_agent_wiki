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
from saw.connectors.token_encryption import (
    TokenEncryption,
    EncryptionError,
)
from saw.connectors.oauth_handler import (
    OAuthHandler,
    OAuthConfig,
    OAuthState,
    OAuthError,
)
from saw.connectors.token_refresh import (
    TokenRefreshManager,
    RefreshMutex,
    TokenRefreshError,
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
    # OAuth & Encryption (Phase 10-02)
    "TokenEncryption",
    "EncryptionError",
    "OAuthHandler",
    "OAuthConfig",
    "OAuthState",
    "OAuthError",
    "TokenRefreshManager",
    "RefreshMutex",
    "TokenRefreshError",
]