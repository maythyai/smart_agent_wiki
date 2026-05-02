"""Database package for Smart Agent Wiki.

Phase 5: Team Deployment — Database layer.
Phase 9: RSS Subscription — Feed models.
Phase 10: Connector Framework — Connector models.
Phase 11: Sync Engine — Sync state and log models.
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
from saw.db.connector_models import ConnectorConfigModel, ConnectorSyncLog
from saw.db.sync_models import SyncStateModel, SyncLogModel, ConflictRecordModel
from saw.db.notion_models import NotionSyncCursorModel, NotionDatabaseConfigModel, SyncDirection
from saw.db.logseq_models import LogseqFileHashModel, LogseqSyncStateModel

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
    # Phase 10: Connector Framework
    "ConnectorConfigModel",
    "ConnectorSyncLog",
    # Phase 11: Sync Engine
    "SyncStateModel",
    "SyncLogModel",
    "ConflictRecordModel",
    # Phase 12: Notion Connector
    "NotionSyncCursorModel",
    "NotionDatabaseConfigModel",
    "SyncDirection",
    # Phase 13: Logseq Connector
    "LogseqFileHashModel",
    "LogseqSyncStateModel",
]