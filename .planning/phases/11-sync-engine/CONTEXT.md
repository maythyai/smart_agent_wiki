# Context: Phase 11 - Sync Engine + Write Queue Integration

**Phase:** 11
**Goal:** System can perform bidirectional sync between SAW and connected platforms with conflict detection
**Milestone:** v3.1 Third-Party Integrations

---

## Requirements

| ID | Description | Priority |
|----|-------------|----------|
| SYNC-01 | System provides unified sync status dashboard | HIGH |
| SYNC-02 | System prevents sync loops (source metadata tracking) | HIGH |
| SYNC-03 | System logs all sync operations for audit | HIGH |
| SYNC-04 | System provides manual sync trigger per connector | MEDIUM |
| SYNC-05 | System handles backpressure via Write Queue | HIGH |
| ERRO-01 | System retries transient failures with exponential backoff | HIGH |
| ERRO-02 | System alerts on persistent failures | HIGH |
| ERRO-03 | System provides per-connector health status | HIGH |
| ERRO-04 | System preserves data integrity on partial failures | HIGH |
| IM-03 | System extracts message content, author, timestamp, channel | HIGH |
| IM-04 | System captures thread context for threaded messages | MEDIUM |
| IM-05 | System handles message reactions as confidence signals | MEDIUM |
| IM-07 | System provides graceful degradation when platforms unavailable | HIGH |

## Success Criteria

1. User can view sync status dashboard showing all connected platforms
2. System detects sync loops via source metadata tracking
3. All sync operations are logged with timestamp, direction, and item count
4. User can trigger manual sync for any connector from CLI or Web UI
5. System handles backpressure by queuing writes to Write Queue
6. Transient API failures retry with exponential backoff (max 5 retries)
7. Persistent failures trigger alerts and mark connector as unhealthy
8. Per-connector health status is visible in dashboard

## Technical Context

### Existing Architecture (Phase 10)

- **UnifiedConnectorInterface:** Protocol for all platform connectors
- **ConnectorRegistry:** Singleton registry for available connectors
- **RateLimitManager:** Per-platform rate limiting
- **OAuthHandler:** Unified OAuth flow management
- **TokenEncryption:** Fernet-based token encryption
- **WebhookVerifier:** HMAC signature verification

### Phase 10 Components to Extend

```python
# From Phase 10
from saw.connectors.protocol import UnifiedConnectorInterface
from saw.connectors.models import ConnectorConfig, ConnectorItem
from saw.connectors.registry import ConnectorRegistry
from saw.connectors.rate_limiter import RateLimitManager
from saw.connectors.oauth_handler import OAuthHandler
from saw.connectors.webhook_verifier import WebhookVerifier
```

### New Components Required

```
src/saw/connectors/
├── sync_engine.py        # Bidirectional sync orchestration
├── conflict_resolver.py  # Conflict detection and resolution
├── sync_status.py        # Sync status tracking
├── sync_logger.py        # Audit logging for sync operations
└── backpressure.py       # Write Queue backpressure handling

src/saw/write_queue/sinks/
└── connector_sink.py      # Updated to integrate with sync engine

src/saw/api/
├── sync.py               # Sync status and trigger endpoints
└── health.py             # Connector health status endpoints
```

### Write Queue Integration

From ARCHITECTURE.md Phase 11:

```
Write Queue Outbox (v1.1)
      │
      ├─▶ ConnectorSink (new)
      │     └─ Handles sync_push operations
      │     └─ Integrates with SyncEngine
      │
      └─▶ Backpressure Manager (new)
            └─ Monitors queue depth
            └─ Triggers throttling when threshold exceeded
```

## Design Decisions (Auto-Decided)

Based on Phase 10 implementation and requirements:

1. **Sync Loop Detection:** Track `source_platform` and `source_id` in Claim metadata. If a Claim originated from platform X, don't push it back to platform X.

2. **Conflict Resolution Strategy:** Default to `last_modified_wins`. Store `last_sync_at` timestamp per connector. Detect conflicts when both sides modified after last sync.

3. **Backpressure Handling:** When Write Queue depth > 1000 items, pause sync_pull operations. Resume when depth < 500.

4. **Retry Strategy:** Exponential backoff: 1s → 2s → 4s → 8s → 16s (max 5 retries). Use `tenacity` library (already in stack).

5. **Health Status:** Three states: `healthy`, `degraded` (some failures but operational), `unhealthy` (persistent failures, sync paused).

6. **Alerting:** Log persistent failures to sync_log with ERROR level. Emit `connector_unhealthy` event for external alerting systems.

7. **Thread Context (IM-04):** Store parent message ID in Claim metadata as `thread_parent_id`. When ingesting thread replies, link to parent Claim.

8. **Message Reactions (IM-05):** Map reactions to Claim metadata: `reactions: {"👍": 5, "❤️": 3}`. Use reactions as confidence signal multiplier.

## Dependencies

- **Phase 10:** Connector framework foundation (Complete)
- **Write Queue:** v1.1 implementation (existing)

## Out of Scope

- Actual connector implementations (Phase 12-14)
- Dashboard UI (Phase 15)
- Real-time WebSocket sync status (deferred)

---

*Context generated: 2026-05-02*
*Auto-decisions based on user instruction to make reasonable choices*
