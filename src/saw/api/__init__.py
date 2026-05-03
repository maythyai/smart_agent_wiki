"""API package for Smart Agent Wiki.

Phase 6: API Platform — RESTful API and integrations.
Phase 9: RSS Subscription — Feed management endpoints.
Phase 10: OAuth Callback & Webhooks.
Phase 11: Health status endpoints.
Phase 16: Real-time WebSocket updates.
"""

from saw.api.keys import (
    APIKey,
    APIKeyData,
    APIKeyService,
    CreatedAPIKey,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)
from saw.api.rate_limit import (
    RateLimitConfig,
    RateLimitStatus,
    RateLimitMiddleware,
    RedisRateLimiter,
)
from saw.api.webhooks import (
    Webhook,
    WebhookEvent,
    WebhookService,
    WebhookSigner,
)
from saw.api.bulk import (
    ImportFormat,
    ExportFormat,
    BulkImportService,
    BulkExportService,
)
from saw.api.feeds import router as feeds_router
from saw.api.oauth_callback import router as oauth_router
from saw.api.webhook_inbound import router as webhook_inbound_router
from saw.api.health import router as health_router
from saw.api.sync import router as sync_router
from saw.api.integrations import router as integrations_router
from saw.api.websocket import ConnectionManager, manager as ws_manager
from saw.api.integrations_ws import router as integrations_ws_router

__all__ = [
    # API Keys
    "APIKey",
    "APIKeyData",
    "APIKeyService",
    "CreatedAPIKey",
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    # Rate Limiting
    "RateLimitConfig",
    "RateLimitStatus",
    "RateLimitMiddleware",
    "RedisRateLimiter",
    # Webhooks
    "Webhook",
    "WebhookEvent",
    "WebhookService",
    "WebhookSigner",
    # Bulk Operations
    "ImportFormat",
    "ExportFormat",
    "BulkImportService",
    "BulkExportService",
    # Phase 9: RSS Feeds
    "feeds_router",
    # Phase 10: OAuth Callback & Webhooks
    "oauth_router",
    "webhook_inbound_router",
    # Phase 11: Health Status & Sync
    "health_router",
    "sync_router",
    # Phase 15: Integration Dashboard
    "integrations_router",
    # Phase 16: Real-time WebSocket
    "ConnectionManager",
    "ws_manager",
    "integrations_ws_router",
]