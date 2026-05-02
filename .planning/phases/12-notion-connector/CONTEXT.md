# Context: Phase 12 - Notion Connector

**Phase:** 12
**Goal:** Users can sync SAW wiki content bidirectionally with Notion databases
**Milestone:** v3.1 Third-Party Integrations

---

## Requirements

| ID | Description | Priority |
|----|-------------|----------|
| NOTI-01 | User can connect Notion workspace via OAuth 2.0 | HIGH |
| NOTI-02 | User can select Notion databases to sync with SAW | HIGH |
| NOTI-03 | System automatically ingests new/modified pages from connected databases | HIGH |
| NOTI-04 | System maps Notion properties to SAW Claim fields | HIGH |
| NOTI-05 | User can edit pages in SAW and sync changes back to Notion | HIGH |
| NOTI-06 | System detects conflicts when both sides modified | HIGH |
| NOTI-07 | System handles Notion property type changes gracefully | MEDIUM |
| NOTI-08 | System polls for changes at configurable intervals | MEDIUM |
| NOTI-09 | System respects Notion rate limits (3 req/s) with token bucket limiter | HIGH |
| NOTI-10 | System persists sync cursor for resume after interruption | HIGH |

## Success Criteria

1. User can connect Notion workspace and select databases to sync
2. System ingests new/modified pages from connected databases as Claims
3. Notion properties map correctly to SAW fields (title, content, confidence, freshness)
4. User can edit wiki page in SAW and sync changes back to Notion
5. System detects concurrent edits and resolves by timestamp (last-modified wins)
6. System handles Notion property type changes without crashing
7. System polls for changes at configurable intervals (default: 1 hour)
8. System respects Notion rate limits (3 req/s) with token bucket limiter
9. System resumes sync after interruption using persisted sync cursor

## Technical Context

### Existing Architecture (Phase 10-11)

- **UnifiedConnectorInterface:** Protocol for all platform connectors
- **SyncEngine:** Bidirectional sync orchestration
- **ConflictResolver:** LAST_MODIFIED_WINS conflict resolution
- **ConnectorSink:** Write Queue integration
- **RateLimitManager:** Token bucket rate limiting

### Notion SDK

From STACK.md v3.1:
- `notion-client 3.0.0` — Official Python SDK
- Async support for efficient API calls
- Full API coverage for databases, pages, blocks

### Property Mapping (Notion ↔ SAW)

| Notion Property | SAW Field | Type |
|-----------------|-----------|------|
| Title | wiki.title | string |
| Confidence | page.confidence | select (4-tier) |
| Freshness | page.freshness | select (9-level) |
| Last Sync | sync.last_modified | datetime |
| Source URL | claim.source_url | url |
| Tags | page.tags | multi-select |

### Notion API Operations

Key API operations needed:
- `databases.query` — Read Notion database as wiki pages
- `pages.create` / `pages.update` — Write wiki content to Notion
- `blocks.children.append` — Add content blocks
- `pages.properties.update` — Sync metadata/frontmatter

## Design Decisions (Auto-Decided)

Based on Phase 10-11 implementation and requirements:

1. **OAuth Flow:** Use existing OAuthHandler with Notion-specific OAuth endpoints. Notion OAuth returns `access_token` and `workspace_id`.

2. **Database Selection:** Store selected database IDs in `ConnectorConfig.metadata["database_ids"]`. Provide API endpoint to list available databases.

3. **Polling Strategy:** Use `last_edited_time` filter in `databases.query` for incremental sync. Store cursor in `ConnectorSyncLog.cursor`.

4. **Block Mapping:** Notion blocks → SAW Claim content. Support: paragraph, heading, bulleted_list, numbered_list, to_do, code, quote.

5. **Bidirectional Sync:**
   - Pull: Notion page → SAW Wiki page + Claims
   - Push: SAW Wiki page → Notion page (via ConnectorSink)

6. **Property Type Changes:** Detect type mismatches, log warning, use string fallback. Never crash on unexpected types.

7. **Rate Limiting:** Use existing RateLimitManager with Notion limits: 3 req/s, burst 10.

8. **Sync Cursor:** Store `last_edited_time` of last synced page. Resume by filtering `last_edited_time > cursor`.

## Dependencies

- **Phase 10:** Connector framework (Complete)
- **Phase 11:** Sync engine (Complete)
- **notion-client 3.0.0:** SDK to install

## Out of Scope

- Notion block-level sync (page-level only for v3.1)
- Real-time sync via webhooks (polling only)
- Notion comments ingestion (deferred)

---

*Context generated: 2026-05-02*
*Auto-decisions based on user instruction to make reasonable choices*
