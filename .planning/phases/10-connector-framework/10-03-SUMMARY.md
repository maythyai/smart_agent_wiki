---
phase: 10-connector-framework
plan: 03
subsystem: connectors
tags: [webhooks, rate-limiting, signature-verification, audit]
dependency:
  requires: [10-01]
  provides: [WebhookVerifier, WebhookRateLimiter, WebhookLogger]
  affects: []
tech-stack:
  added: []
  patterns: [HMAC-SHA256, Token Bucket, Audit Trail]
key-files:
  created:
    - src/saw/connectors/webhook_verifier.py
    - src/saw/connectors/webhook_log.py
    - src/saw/api/webhook_inbound.py
  modified:
    - src/saw/connectors/rate_limiter.py
    - src/saw/connectors/__init__.py
    - src/saw/api/__init__.py
decisions:
  - HMAC-SHA256 for webhook signature verification
  - Platform-specific signature formats (Slack v0, GitHub sha256=)
  - 5-minute timestamp validation window for replay protection
  - Per-platform webhook rate limits
metrics:
  duration-min: 15
  completed: 2026-05-02
  tests-passed: 24
---

# Phase 10 Plan 03: Webhook Endpoints and Rate Limiting Summary

Unified webhook endpoint with HMAC-SHA256 signature verification and per-platform rate limiting.

## Key Deliverables

- **WebhookVerifier**: HMAC-SHA256 signature verification
  - Platform-specific formats: Slack (v0 prefix with timestamp), GitHub (sha256= prefix), Feishu (timestamp-based)
  - Timestamp validation with 5-minute window for replay attack prevention
  - `verify()`: Validate signature against body and optional timestamp
  - `compute_signature()`: Static method for testing/sending webhooks

- **WebhookRateLimit**: Platform-specific inbound rate limits
  - Slack: 100 req/min, burst 50
  - GitHub: 60 req/min, burst 30
  - Discord: 100 req/min, burst 50
  - Feishu: 60 req/min, burst 30

- **WebhookRateLimiter**: Per-connector rate limiting
  - `acquire()`: Returns (allowed, headers_dict)
  - Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
  - Per-connector isolation for independent limiting

- **WebhookLogger**: Audit trail with token masking
  - `log_received()`: Record webhook event with masked payload
  - `mark_processed()`: Mark as successfully processed
  - `mark_failed()`: Mark as failed with error
  - `get_failed_webhooks()`: Retrieve failed events for retry
  - Automatic masking of sensitive fields (access_token, refresh_token, api_key, secret)

- **FastAPI Endpoints**: Unified webhook handling
  - `GET /api/v1/webhooks/platforms`: List supported platforms
  - `POST /api/v1/webhooks/{platform}`: Receive webhook
  - Signature verification before processing
  - Rate limiting with 429 response on limit exceeded

## Requirements Addressed

- IM-01: Unified webhook endpoint `/api/v1/webhooks/{platform}`
- IM-02: HMAC-SHA256 webhook signature verification
- IM-06: Per-platform rate limits
- AUTH-04: Tokens masked in logs (last 4 chars only)

## Deviations from Plan

None - plan executed exactly as written.

## Test Results

```
24 passed in 2.59s
```

All tests pass covering signature verification, rate limiting, logging, and endpoint definitions.
