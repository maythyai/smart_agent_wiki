# Context: Phase 10 - Connector Framework Foundation

**Phase:** 10
**Goal:** Users can securely connect third-party platforms via OAuth with encrypted credential storage
**Milestone:** v3.1 Third-Party Integrations

---

## Requirements

| ID | Description | Priority |
|----|-------------|----------|
| AUTH-01 | System provides unified OAuth flow for all OAuth platforms | HIGH |
| AUTH-02 | System stores OAuth tokens encrypted at rest | HIGH |
| AUTH-03 | System handles token refresh with mutex | HIGH |
| AUTH-04 | System masks tokens in logs and API responses | HIGH |
| IM-01 | System provides unified webhook endpoint `/api/v1/webhooks/{platform}` | HIGH |
| IM-02 | System verifies webhook signatures (HMAC-SHA256) | HIGH |
| IM-06 | System respects per-platform rate limits | MEDIUM |

## Success Criteria

1. User can initiate OAuth flow for Notion/Slack/GitHub/Feishu from Web UI
2. System stores OAuth tokens encrypted at rest using Fernet encryption
3. System automatically refreshes expired tokens with mutex lock
4. Tokens are masked in logs and API responses (showing only last 4 characters)
5. Unified webhook endpoint `/api/v1/webhooks/{platform}` receives and verifies HMAC signatures

## Technical Context

### Existing Architecture (v2.0)

- **OAuth Framework:** `authlib 1.7.0` already in stack for v2.0 JWT auth
- **Database:** SQLite (local) / PostgreSQL (team mode)
- **API:** FastAPI with rate limiting (Redis-based)
- **Encryption:** No existing token encryption - needs new implementation

### New Components Required

From ARCHITECTURE.md research:

```
src/saw/connectors/
├── protocol.py          # UnifiedConnectorInterface (Protocol)
├── registry.py          # ConnectorRegistry singleton
├── base_connector.py    # Abstract base implementation
├── models.py            # ConnectorConfig, SyncStatus, etc.
├── oauth_handler.py     # OAuth 2.0 flow management
└── rate_limiter.py      # Per-platform rate limiting
```

### Stack Additions (from STACK.md v3.1)

- `cryptography 44.0.0` — Fernet encryption for token storage
- `svix 1.92.2` — Webhook signature verification (already in STACK.md)
- Existing: `authlib 1.7.0` — OAuth flows

## Design Decisions (Auto-Decided)

Based on current tech architecture and feature requirements:

1. **Token Encryption:** Use Fernet (symmetric encryption) with key from environment variable `SAW_ENCRYPTION_KEY`. Generate on first run if not set.

2. **OAuth State Management:** Use session-based state with CSRF protection. Store state in Redis with 10-minute TTL.

3. **Rate Limiting Strategy:** Token bucket algorithm per platform. Platform limits:
   - Notion: 3 req/s
   - GitHub: 5000 req/hr
   - Slack: 60 req/min
   - Discord: 50 req/s global

4. **Webhook Verification:** HMAC-SHA256 signature verification using Svix library for Slack, platform-specific for others.

5. **Token Refresh Mutex:** Use Redis distributed lock for team mode, asyncio.Lock for single-user mode.

## Dependencies

- Phase 10 is the foundation - no dependencies on other v3.1 phases
- Depends on v3.0 (shipped) for API patterns, database models

## Out of Scope

- Actual connector implementations (Phase 12-14)
- Sync engine and conflict resolution (Phase 11)
- Web UI for OAuth flow initiation (deferred to Phase 15)

---

*Context generated: 2026-05-02*
*Auto-decisions based on user instruction to make reasonable choices*
