# Architecture Research: Third-Party Integrations

**Domain:** Third-Party Platform Integration Architecture
**Researched:** 2026-05-01
**Confidence:** HIGH (based on comprehensive existing codebase analysis)

## Integration with Existing SAW Architecture

### System Overview

```
                              EXISTING ARCHITECTURE
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interaction Layer                      │
│   CLI (Typer)  │  MCP Server  │  Web UI  │  Obsidian Plugin        │
└───────┬────────┴──────┬───────┴────┬─────┴──────┬──────────────────┘
        │               │            │            │
┌───────▼───────────────▼────────────▼────────────▼───────────────────┐
│                          API Gateway Layer                           │
│       Auth (JWT/API Key) │ Rate Limit │ Routing │ Webhook Handler    │
└───────┬──────────────────┬────────────────────┬─────────────────────┘
        │                  │                    │
        │         ┌────────▼────────┐           │
        │         │  Ingest Engine   │           │
        │         │  (Pipeline)      │           │
        │         └────────┬────────┘           │
        │                  │                     │
┌───────▼──────────────────▼────────────────────▼─────────────────────┐
│                    Write Queue (Outbox)                              │
│             Single Entry Point → Multi-Sink Dispatch                  │
└───────┬──────────┬──────────┬──────────┬──────────┬──────────────────┘
        │          │          │          │          │
┌───────▼──────┐┌──▼──────┐┌──▼──────┐┌──▼──────┐┌──▼──────┐
│    Vault     ││  Claims ││  Wiki   ││  FTS5   ││  Graph  │
│    Sink      ││  Sink   ││  Sink   ││  Sink   ││  Sink   │
└──────────────┘└─────────┘└─────────┘└─────────┘└─────────┘


                              NEW INTEGRATION LAYER
┌─────────────────────────────────────────────────────────────────────┐
│                    Connector Abstraction Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   Notion    │ │   Logseq    │ │     IM      │ │   GitHub    │   │
│  │  Connector  │ │  Connector  │ │ Connectors  │ │  Connector  │   │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘   │
│         │               │               │               │           │
│  ┌──────▼───────────────▼───────────────▼───────────────▼──────┐   │
│  │              Unified Connector Interface                     │   │
│  │   - authenticate()  - sync_pull()  - sync_push()           │   │
│  │   - get_items()     - put_item()   - delete_item()         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │         Sync Engine             │
                    │  - Conflict Detection            │
                    │  - Timestamp Resolution          │
                    │  - Batch Operations               │
                    │  - Retry/Recovery                 │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │    Write Queue Integration      │
                    │  - Connector as Sink            │
                    │  - Connector as Source           │
                    └─────────────────────────────────┘
```

### Integration Points with Existing Engines

| Engine | Integration Point | New Components Needed |
|--------|-------------------|----------------------|
| **Ingest Engine** | `IngestPipeline.ingest()` | `ConnectorSource` adapter for pull-based ingestion |
| **Query Engine** | None (reads from existing stores) | None - connectors write to existing stores |
| **Govern Engine** | Conflict detection, confidence | `ConnectorClaim` with `source_platform` field |
| **Learn Engine** | None (operates on claims) | None - existing FSRS works on connector-sourced claims |
| **Collaborate Engine** | None (agent coordination) | None - agents operate on unified data model |

### New Component Responsibilities

| Component | Responsibility | Implementation Location |
|-----------|----------------|------------------------|
| `UnifiedConnectorInterface` | Protocol for all platform connectors | `src/saw/connectors/protocol.py` |
| `ConnectorRegistry` | Registry for available connectors | `src/saw/connectors/registry.py` |
| `SyncEngine` | Bidirectional sync orchestration | `src/saw/connectors/sync_engine.py` |
| `OAuthHandler` | OAuth flow management | `src/saw/connectors/oauth_handler.py` |
| `WebhookReceiver` | Incoming webhook endpoint | `src/saw/api/connectors.py` |
| `ConnectorSink` | Write Queue sink for push | `src/saw/write_queue/sinks/connector_sink.py` |
| `RateLimitManager` | Per-platform rate limiting | `src/saw/connectors/rate_limiter.py` |

## Recommended Project Structure

```
src/saw/
├── connectors/                      # NEW: Third-party connector framework
│   ├── __init__.py
│   ├── protocol.py                  # UnifiedConnectorInterface (Protocol)
│   ├── registry.py                  # ConnectorRegistry singleton
│   ├── base_connector.py            # Abstract base implementation
│   ├── sync_engine.py               # Bidirectional sync orchestration
│   ├── oauth_handler.py             # OAuth 2.0 flow management
│   ├── rate_limiter.py              # Per-platform rate limiting
│   ├── conflict_resolver.py         # Platform-specific conflict handling
│   ├── models.py                    # ConnectorConfig, SyncStatus, etc.
│   │
│   ├── notion/                      # Notion connector implementation
│   │   ├── __init__.py
│   │   ├── connector.py             # NotionConnector class
│   │   ├── models.py                # Notion-specific models
│   │   ├── transformer.py           # Notion ↔ SAW transformation
│   │   └── oauth.py                 # Notion OAuth specifics
│   │
│   ├── logseq/                      # Logseq connector implementation
│   │   ├── __init__.py
│   │   ├── connector.py             # LogseqConnector class
│   │   ├── models.py                # Logseq block/page models
│   │   └── transformer.py           # Logseq ↔ SAW transformation
│   │
│   ├── im/                          # IM connectors (shared patterns)
│   │   ├── __init__.py
│   │   ├── base_im_connector.py     # Shared IM connector base
│   │   ├── slack/
│   │   │   ├── connector.py
│   │   │   └── models.py
│   │   ├── discord/
│   │   │   ├── connector.py
│   │   │   └── models.py
│   │   └── feishu/
│   │       ├── connector.py
│   │       └── models.py
│   │
│   └── github/                      # GitHub connector implementation
│       ├── __init__.py
│       ├── connector.py             # GitHubConnector class
│       ├── models.py                # Issue/PR/Discussion models
│       └── transformer.py           # GitHub ↔ SAW transformation
│
├── api/
│   ├── connectors.py                # NEW: Connector API endpoints
│   └── oauth_callback.py            # NEW: OAuth callback handler
│
├── write_queue/
│   └── sinks/
│       └── connector_sink.py        # NEW: Push sync via Write Queue
│
└── db/
    └── connector_models.py          # NEW: Connector config persistence
```

### Structure Rationale

- **`connectors/` as top-level:** Mirrors existing `engines/` structure; connectors are peers to engines, not subordinate
- **Per-platform subdirectories:** Each connector has its own namespace for models, transformers, and OAuth specifics
- **`im/` shared base:** Slack/Discord/Feishu share message ingestion patterns; reduce code duplication
- **`api/connectors.py`:** Single file for all connector REST endpoints, matching existing `api/feeds.py` pattern
- **`connector_sink.py` in write_queue:** Follows existing Sink protocol; enables push-based sync via Write Queue

## Architectural Patterns

### Pattern 1: Unified Connector Interface

**What:** A Protocol defining common operations all connectors must implement. Enables polymorphic sync engine.

**When to use:** Always - this is the core abstraction.

**Trade-offs:**
- Pros: Swappable connectors, testable sync engine, consistent error handling
- Cons: Lowest-common-denominator API; platform-specific features need extensions

**Example:**

```python
# src/saw/connectors/protocol.py
from typing import Protocol
from datetime import datetime
from saw.domain.claims import Claim

class UnifiedConnectorInterface(Protocol):
    """Protocol for all third-party platform connectors."""

    @property
    def platform_name(self) -> str:
        """Platform identifier (e.g., 'notion', 'logseq')."""
        ...

    @property
    def supports_push(self) -> bool:
        """Whether platform supports webhooks/push notifications."""
        ...

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete authentication flow, return auth tokens."""
        ...

    async def get_items(
        self,
        since: datetime | None = None,
        filters: dict | None = None,
    ) -> list[ConnectorItem]:
        """Pull items from platform (incremental if since provided)."""
        ...

    async def put_item(self, item: ConnectorItem) -> str:
        """Push item to platform. Return platform item ID."""
        ...

    async def delete_item(self, item_id: str) -> bool:
        """Delete item from platform. Return success."""
        ...

    def transform_to_claim(self, item: ConnectorItem) -> Claim:
        """Convert platform item to SAW Claim."""
        ...

    def transform_from_claim(self, claim: Claim) -> ConnectorItem:
        """Convert SAW Claim to platform item format."""
        ...
```

### Pattern 2: Connector as Source + Sink

**What:** Connectors implement both pull (source) and push (sink) patterns, integrated with Write Queue.

**When to use:** For bidirectional sync platforms (Notion, Logseq, GitHub).

**Trade-offs:**
- Pros: Unified sync engine; Write Queue guarantees; automatic retry
- Cons: More complex than simple polling; requires careful ordering

**Example:**

```python
# src/saw/write_queue/sinks/connector_sink.py
class ConnectorSink:
    """Write Queue sink for pushing to external platforms."""

    def __init__(self, connector: UnifiedConnectorInterface):
        self._connector = connector

    @property
    def name(self) -> str:
        return f"connector_{self._connector.platform_name}"

    def write(self, op: WriteOp) -> None:
        """Push operation to external platform.

        Idempotent: uses op.op_id as external ID for deduplication.
        """
        if op.payload.get("action") == "push":
            item = self._connector.transform_from_claim(
                Claim.from_dict(op.payload["claim"])
            )
            self._connector.put_item(item)
```

### Pattern 3: Sync Engine with Conflict Detection

**What:** Centralized sync engine coordinates bidirectional sync, detects conflicts, applies resolution strategies.

**When to use:** For all bidirectional sync scenarios.

**Trade-offs:**
- Pros: Consistent conflict handling; batch operations for efficiency; audit trail
- Cons: Single point of failure; requires careful locking

**Example:**

```python
# src/saw/connectors/sync_engine.py
class SyncEngine:
    """Orchestrates bidirectional sync between SAW and platforms."""

    def __init__(self, connector: UnifiedConnectorInterface, write_queue: WriteQueue):
        self._connector = connector
        self._write_queue = write_queue

    async def sync(self, direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> SyncResult:
        """Perform sync in specified direction.

        Conflict resolution: timestamp priority by default.
        """
        # Pull phase
        if direction in (SyncDirection.PULL, SyncDirection.BIDIRECTIONAL):
            remote_items = await self._connector.get_items(since=self._last_sync)
            for item in remote_items:
                claim = self._connector.transform_to_claim(item)
                self._detect_conflict(claim)
                self._enqueue_claim(claim)

        # Push phase
        if direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
            pending_claims = self._get_pending_push_claims()
            for claim in pending_claims:
                item = self._connector.transform_from_claim(claim)
                await self._connector.put_item(item)

        return SyncResult(pulled=len(remote_items), pushed=len(pending_claims))
```

### Pattern 4: OAuth Callback Handler

**What:** FastAPI endpoint receives OAuth callbacks, exchanges code for tokens, stores credentials.

**When to use:** For OAuth-based platforms (Notion, Slack, GitHub).

**Trade-offs:**
- Pros: Standard OAuth 2.0 flow; secure token storage; user-friendly
- Cons: Requires HTTPS in production; state management for CSRF protection

**Example:**

```python
# src/saw/api/oauth_callback.py
from fastapi import APIRouter, Request, HTTPException
from saw.connectors.oauth_handler import OAuthHandler

router = APIRouter(prefix="/api/v1/oauth", tags=["oauth"])

@router.get("/{platform}/callback")
async def oauth_callback(
    platform: str,
    code: str,
    state: str,
    request: Request,
):
    """Handle OAuth callback from platform."""
    handler = OAuthHandler(platform)

    # Verify state for CSRF protection
    if not handler.verify_state(state):
        raise HTTPException(400, "Invalid state")

    # Exchange code for tokens
    tokens = await handler.exchange_code(code)

    # Store tokens securely
    user_id = request.state.user.id
    await handler.store_tokens(user_id, platform, tokens)

    return {"status": "connected", "platform": platform}
```

### Pattern 5: Rate Limit Manager

**What:** Per-platform rate limit tracking with exponential backoff.

**When to use:** For all external API calls.

**Trade-offs:**
- Pros: Prevents API bans; respects platform limits; automatic backoff
- Cons: Adds latency; requires careful configuration per platform

**Example:**

```python
# src/saw/connectors/rate_limiter.py
import asyncio
from datetime import datetime

class RateLimitManager:
    """Per-platform rate limit tracking."""

    PLATFORM_LIMITS = {
        "notion": {"requests_per_second": 3, "burst": 10},
        "github": {"requests_per_hour": 5000, "burst": 100},
        "slack": {"requests_per_minute": 60, "burst": 20},
    }

    def __init__(self, platform: str):
        self._limits = self.PLATFORM_LIMITS.get(platform, {})
        self._last_request: datetime | None = None

    async def acquire(self) -> None:
        """Wait until rate limit allows next request."""
        if not self._limits:
            return

        now = datetime.utcnow()
        if self._last_request:
            min_interval = 1.0 / self._limits.get("requests_per_second", 1)
            elapsed = (now - self._last_request).total_seconds()
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

        self._last_request = datetime.utcnow()
```

## Data Flow

### Pull Sync Flow (Platform → SAW)

```
[Connector Poll/Webhook]
         │
         ▼
    [Sync Engine]
         │
         ▼ get_items(since=last_sync)
    [Connector]
         │
         ▼ transform_to_claim()
    [Claim Objects]
         │
         ▼ detect_conflicts()
    [Conflict Resolver]
         │
         ▼
    [Write Queue] ─────► [Claims Sink]
         │                    │
         └────────────────────┼──► [Wiki Sink]
                              ├──► [FTS5 Sink]
                              └──► [Graph Sink]
```

### Push Sync Flow (SAW → Platform)

```
[Claim Update/Creation]
         │
         ▼
    [Write Queue]
         │
         ▼ enqueue with sink_name="connector_{platform}"
    [Connector Sink]
         │
         ▼ transform_from_claim()
    [Connector]
         │
         ▼ put_item()
    [Platform API]
         │
         ▼
    [Remote Platform]
```

### OAuth Flow

```
[User] ──► [SAW Web UI] ──► GET /api/v1/oauth/{platform}/authorize
                                      │
                                      ▼ redirect
                           [Platform OAuth Page]
                                      │
                                      ▼ user approves
                           [Callback URL] ◄── redirect with code
                                      │
                                      ▼ POST /api/v1/oauth/{platform}/callback
                           [OAuth Handler]
                                      │
                                      ├──► exchange_code()
                                      │           │
                                      │           ▼
                                      │    [Platform Token Endpoint]
                                      │           │
                                      │           ▼ access_token, refresh_token
                                      │           │
                                      ◄───────────┘
                                      │
                                      ▼ store_tokens()
                           [Encrypted Credential Store]
```

### Key Data Flows

1. **Pull Ingestion:** Platform item → Connector.transform_to_claim() → Sync Engine → Write Queue → Claims/Wiki/FTS5/Graph Sinks
2. **Push Sync:** Claim creation → Write Queue → ConnectorSink → Connector.put_item() → Platform API
3. **Webhook Ingestion:** Platform webhook → API endpoint → Connector.parse_webhook() → Sync Engine (same as pull)
4. **OAuth:** User click → redirect → platform auth → callback → token exchange → secure storage

## Integration with Existing Components

### Write Queue Integration

| Aspect | Existing | New |
|--------|----------|-----|
| Sink Protocol | `VaultSink`, `ClaimsSink`, etc. | `ConnectorSink` implements same `Sink` protocol |
| Dispatch | `Dispatcher.dispatch_pending()` | No changes - connector sink registered like others |
| Retry | Built into Write Queue | ConnectorSink failures trigger Write Queue retry |
| Idempotency | `op.op_id` dedup | Connector uses `op.op_id` as platform correlation ID |

### Ingest Engine Integration

```python
# Extend IngestPipeline for connector sources
class IngestPipeline:
    # ... existing code ...

    async def ingest_from_connector(
        self,
        connector: UnifiedConnectorInterface,
        since: datetime | None = None,
    ) -> IngestResult:
        """Ingest items pulled from a connector."""
        items = await connector.get_items(since=since)

        session_id = str(uuid.uuid4())
        source_uuid = str(uuid.uuid4())

        ops = []
        for item in items:
            claim = connector.transform_to_claim(item)
            ops.extend(self._build_claim_ops(session_id, source_uuid, claim))

        self._write_queue.enqueue_atomic(ops)

        return IngestResult(
            session_id=session_id,
            claim_count=len(ops),
            entity_count=0,
            relation_count=0,
            parser=connector.platform_name,
        )
```

### Webhook Integration

Existing `WebhookService` handles outgoing webhooks. New `WebhookReceiver` handles incoming:

```python
# src/saw/api/connectors.py
@router.post("/webhooks/{platform}")
async def receive_webhook(
    platform: str,
    request: Request,
    x_signature: str = Header(...),
):
    """Receive webhook from external platform."""
    connector = ConnectorRegistry.get(platform)
    if not connector:
        raise HTTPException(404, f"Unknown platform: {platform}")

    body = await request.body()

    # Verify signature
    if not connector.verify_webhook_signature(body, x_signature):
        raise HTTPException(401, "Invalid signature")

    # Parse and process
    items = connector.parse_webhook(body)

    # Trigger sync for changed items
    sync_engine = SyncEngine(connector, get_write_queue())
    result = await sync_engine.sync_items(items)

    return {"processed": len(items)}
```

## Database Schema Additions

```sql
-- Connector configuration storage
CREATE TABLE connector_configs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    platform TEXT NOT NULL,
    name TEXT NOT NULL,
    credentials_encrypted TEXT,  -- Encrypted OAuth tokens
    sync_direction TEXT DEFAULT 'bidirectional',
    last_sync_at TEXT,
    sync_interval INTEGER DEFAULT 3600,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    UNIQUE(user_id, platform, name)
);

-- Sync status tracking
CREATE TABLE connector_sync_log (
    id TEXT PRIMARY KEY,
    config_id TEXT NOT NULL REFERENCES connector_configs(id),
    direction TEXT NOT NULL,  -- 'pull', 'push', 'bidirectional'
    items_pulled INTEGER DEFAULT 0,
    items_pushed INTEGER DEFAULT 0,
    conflicts_detected INTEGER DEFAULT 0,
    errors TEXT,  -- JSON array of error messages
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration_ms INTEGER
);

-- Extend claims with source platform
ALTER TABLE claims ADD COLUMN source_platform TEXT;
-- Values: 'local', 'notion', 'logseq', 'slack', 'discord', 'feishu', 'github'
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single user, <10 connectors | Direct sync, no batching needed |
| Single user, 10+ connectors | Batch sync operations, stagger polling |
| Team mode, <50 connectors | Per-connector sync workers in scheduler |
| Team mode, 50+ connectors | Dedicated sync service, Redis queue |

### Scaling Priorities

1. **First bottleneck:** API rate limits - mitigated by `RateLimitManager` per connector
2. **Second bottleneck:** Database write contention - mitigated by Write Queue batching

## Anti-Patterns

### Anti-Pattern 1: Direct API Calls in Write Queue Sinks

**What people do:** Make synchronous API calls in `Sink.write()` without rate limiting

**Why it's wrong:** Blocks Write Queue dispatch; one slow API slows all sinks; no retry isolation

**Do this instead:** Use `ConnectorSink` with `RateLimitManager`; queue API calls to async task queue if platform is slow

### Anti-Pattern 2: Storing OAuth Tokens in Plaintext

**What people do:** Store `access_token` directly in SQLite

**Why it's wrong:** Database access = credential access; violates security best practices

**Do this instead:** Encrypt with `cryptography.fernet` using key from environment; store in `credentials_encrypted` field

### Anti-Pattern 3: Polling Without Conditional GET

**What people do:** Poll platform API every N seconds, always fetch full data

**Why it's wrong:** Wastes API quota; unnecessary bandwidth; slower sync

**Do this instead:** Use `If-Modified-Since` header; respect `ETag` and `Last-Modified`; follow existing RSS FeedManager pattern

### Anti-Pattern 4: Ignoring Platform-Specific Data Models

**What people do:** Map everything to generic `Claim` model, lose platform-specific fields

**Why it's wrong:** Loss of fidelity; can't round-trip; platform features unavailable

**Do this instead:** Keep platform-specific fields in `Claim.metadata` JSON field; use `transformer.py` for bidirectional mapping

## Build Order (Considering Dependencies)

### Phase 10: Connector Framework Foundation

**Dependencies:** None (standalone infrastructure)

**Components:**
1. `connectors/protocol.py` - UnifiedConnectorInterface
2. `connectors/models.py` - ConnectorConfig, ConnectorItem, SyncResult
3. `connectors/base_connector.py` - Abstract base with common implementations
4. `connectors/registry.py` - ConnectorRegistry singleton
5. `connectors/rate_limiter.py` - RateLimitManager
6. `connectors/oauth_handler.py` - OAuthHandler base class
7. `db/connector_models.py` - SQLAlchemy models for config storage
8. `api/oauth_callback.py` - OAuth endpoints

**Tests:**
- `tests/unit/test_connector_protocol.py`
- `tests/unit/test_rate_limiter.py`
- `tests/unit/test_oauth_handler.py`

### Phase 11: Sync Engine + Write Queue Integration

**Dependencies:** Phase 10 (protocol, models)

**Components:**
1. `connectors/sync_engine.py` - SyncEngine with conflict detection
2. `connectors/conflict_resolver.py` - ConflictResolver strategies
3. `write_queue/sinks/connector_sink.py` - ConnectorSink implementation
4. `api/connectors.py` - Connector CRUD and sync endpoints

**Tests:**
- `tests/unit/test_sync_engine.py`
- `tests/unit/test_connector_sink.py`
- `tests/integration/test_connector_sync_flow.py`

### Phase 12: Notion Connector

**Dependencies:** Phase 10, Phase 11

**Components:**
1. `connectors/notion/models.py` - Notion API models
2. `connectors/notion/connector.py` - NotionConnector implementation
3. `connectors/notion/transformer.py` - Notion ↔ SAW transformation
4. `connectors/notion/oauth.py` - Notion OAuth specifics

**Tests:**
- `tests/unit/test_notion_connector.py`
- `tests/integration/test_notion_sync.py`

### Phase 13: Logseq Connector

**Dependencies:** Phase 10, Phase 11

**Components:**
1. `connectors/logseq/models.py` - Logseq block/page models
2. `connectors/logseq/connector.py` - LogseqConnector (local file-based)
3. `connectors/logseq/transformer.py` - Logseq ↔ SAW transformation

**Tests:**
- `tests/unit/test_logseq_connector.py`
- `tests/integration/test_logseq_sync.py`

### Phase 14: IM Connectors (Slack/Discord/Feishu)

**Dependencies:** Phase 10, Phase 11

**Components:**
1. `connectors/im/base_im_connector.py` - Shared IM base class
2. `connectors/im/slack/connector.py` - SlackConnector
3. `connectors/im/slack/models.py` - Slack message models
4. `connectors/im/discord/connector.py` - DiscordConnector
5. `connectors/im/discord/models.py` - Discord message models
6. `connectors/im/feishu/connector.py` - FeishuConnector
7. `connectors/im/feishu/models.py` - Feishu message models

**Tests:**
- `tests/unit/test_slack_connector.py`
- `tests/unit/test_discord_connector.py`
- `tests/unit/test_feishu_connector.py`

### Phase 15: GitHub Connector

**Dependencies:** Phase 10, Phase 11

**Components:**
1. `connectors/github/models.py` - Issue/PR/Discussion models
2. `connectors/github/connector.py` - GitHubConnector
3. `connectors/github/transformer.py` - GitHub ↔ SAW transformation
4. `connectors/github/oauth.py` - GitHub App OAuth

**Tests:**
- `tests/unit/test_github_connector.py`
- `tests/integration/test_github_sync.py`

## Sources

- Existing SAW Architecture: `docs/smart_agent_wiki_design.md`
- Write Queue Implementation: `src/saw/write_queue/queue.py`, `dispatcher.py`
- Sink Protocol: `src/saw/domain/protocols.py`
- RSS Integration Pattern: `src/saw/engines/ingest/feed_manager.py`, `scheduler.py`
- API Patterns: `src/saw/api/feeds.py`, `webhooks.py`
- Auth Implementation: `src/saw/auth/jwt_auth.py`
- Obsidian Plugin Sync: `plugins/obsidian-smart-agent-wiki/src/api/sync.ts`

---
*Architecture research for: Third-Party Integrations (v3.1)*
*Researched: 2026-05-01*
