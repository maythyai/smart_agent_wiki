"""Database package for Smart Agent Wiki.

Phase 5: Team Deployment — Database layer.
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
]