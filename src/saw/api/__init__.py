"""API package for Smart Agent Wiki.

Phase 6: API Platform — RESTful API and integrations.
Phase 9: RSS Subscription — Feed management endpoints.
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
]