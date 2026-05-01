"""Database package for Smart Agent Wiki.

Phase 5: Team Deployment — Database layer.
Phase 9: RSS Subscription — Feed models.
"""

from saw.db.config import DatabaseConfig, get_engine, get_async_engine, get_session_factory
from saw.db.models import (
    Base,
    User,
    Vault,
    Claim,
    VaultPermission,
    AuditLog,
    RefreshToken,
    SystemConfig,
    init_db,
    drop_db,
)
from saw.db.feed_models import Feed, FeedEntry

__all__ = [
    "DatabaseConfig",
    "get_engine",
    "get_async_engine",
    "get_session_factory",
    "Base",
    "User",
    "Vault",
    "Claim",
    "VaultPermission",
    "AuditLog",
    "RefreshToken",
    "SystemConfig",
    "init_db",
    "drop_db",
    # Phase 9: RSS Subscription
    "Feed",
    "FeedEntry",
]