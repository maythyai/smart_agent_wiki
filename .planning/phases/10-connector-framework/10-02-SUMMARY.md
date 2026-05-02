---
phase: 10-connector-framework
plan: 02
subsystem: connectors
tags: [oauth, encryption, token-refresh, fastapi]
dependency:
  requires: [10-01]
  provides: [TokenEncryption, OAuthHandler, TokenRefreshManager]
  affects: []
tech-stack:
  added: [cryptography 44.0.0]
  patterns: [Fernet, State Machine, Mutex Lock]
key-files:
  created:
    - src/saw/connectors/token_encryption.py
    - src/saw/connectors/oauth_handler.py
    - src/saw/connectors/token_refresh.py
    - src/saw/api/oauth_callback.py
  modified:
    - src/saw/connectors/__init__.py
    - src/saw/api/__init__.py
decisions:
  - Fernet symmetric encryption for token storage
  - Environment variable SAW_ENCRYPTION_KEY for key management
  - Redis for OAuth state (team mode), local dict (single-user)
  - asyncio.Lock for single-user, Redis distributed lock for team
metrics:
  duration-min: 20
  completed: 2026-05-02
  tests-passed: 25
---

# Phase 10 Plan 02: OAuth Handler and Token Encryption Summary

Secure OAuth 2.0 flow management with Fernet token encryption and automatic token refresh with mutex protection.

## Key Deliverables

- **TokenEncryption**: Fernet symmetric encryption for OAuth tokens
  - `from_env()`: Load key from SAW_ENCRYPTION_KEY environment variable
  - `generate_key()`: Generate new Fernet key
  - `encrypt_token_set()`: Encrypt access_token, refresh_token, expires_at
  - `decrypt_token_set()`: Decrypt and parse token data
  - Raises EncryptionError on decryption failure

- **OAuthConfig**: Platform-specific OAuth configuration factory
  - `notion()`, `slack()`, `github()`, `feishu()` class methods
  - Pre-configured authorize_url, token_url, scopes

- **OAuthHandler**: OAuth 2.0 flow management
  - `get_authorization_url()`: Generate authorization URL with state
  - `verify_state()`: Validate OAuth state for CSRF protection
  - State stored in Redis with 10-minute TTL (team mode) or local dict (single-user)
  - Cryptographically random state using secrets.token_urlsafe(32)

- **TokenRefreshManager**: Automatic token refresh with mutex
  - `refresh_if_needed()`: Check expiry and refresh if needed
  - 5-minute refresh buffer before expiry
  - Double-check after mutex acquisition to prevent redundant refreshes

- **RefreshMutex**: Distributed lock for token refresh
  - asyncio.Lock for single-user mode
  - Redis SET NX EX for distributed locking (team mode)
  - 30-second lock timeout

- **FastAPI Endpoints**: OAuth callback handling
  - `GET /api/v1/oauth/platforms`: List supported platforms
  - `GET /api/v1/oauth/{platform}/authorize`: Start OAuth flow
  - `GET /api/v1/oauth/{platform}/callback`: Handle callback
  - Tokens stored encrypted in database, masked in responses (AUTH-04)

## Requirements Addressed

- AUTH-01: Unified OAuth flow for all OAuth platforms
- AUTH-02: OAuth tokens encrypted at rest using Fernet
- AUTH-03: Token refresh with mutex lock
- AUTH-04: Tokens masked in API responses (last 4 chars only)

## Deviations from Plan

None - plan executed exactly as written.

## Test Results

```
25 passed in 2.70s
```

All tests pass covering encryption, OAuth configuration, state management, token refresh, and endpoint definitions.
