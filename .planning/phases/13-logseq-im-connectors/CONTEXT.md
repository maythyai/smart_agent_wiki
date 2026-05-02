# Context: Phase 13 - Logseq + IM Connectors

**Phase:** 13
**Goal:** Users can sync local Logseq graphs and ingest messages from IM platforms
**Milestone:** v3.1 Third-Party Integrations

---

## Requirements

### Logseq Integration (LOGS)

| ID | Description | Priority |
|----|-------------|----------|
| LOGS-01 | User can configure Logseq graph path (local directory) | HIGH |
| LOGS-02 | System parses Markdown files and extracts blocks as Claims | HIGH |
| LOGS-03 | System handles property drawers as Claim metadata | HIGH |
| LOGS-04 | System watches Logseq directory for file changes | HIGH |
| LOGS-05 | User can edit in SAW and sync changes back to Logseq files | MEDIUM |
| LOGS-06 | System detects concurrent edits (file hash comparison) | MEDIUM |
| LOGS-07 | System creates conflict copies when edits collide | MEDIUM |
| LOGS-08 | System handles EDN format for Logseq configuration | LOW |
| LOGS-09 | System maps Logseq namespaces to SAW Wiki page hierarchy | MEDIUM |
| LOGS-10 | System preserves Logseq wikilink syntax during sync | HIGH |

### Slack Integration (SLAK)

| ID | Description | Priority |
|----|-------------|----------|
| SLAK-01 | User can install Slack app via OAuth 2.0 | HIGH |
| SLAK-02 | System receives events via Slack Events API | HIGH |
| SLAK-03 | System handles message events (message.channels, message.groups) | HIGH |
| SLAK-04 | System captures thread replies with parent message context | MEDIUM |
| SLAK-05 | System handles Slack's URL unfurling and attachments | MEDIUM |
| SLAK-06 | System respects Slack's tier-based rate limits | HIGH |

### Discord Integration (DISC)

| ID | Description | Priority |
|----|-------------|----------|
| DISC-01 | User can add Discord bot to server | HIGH |
| DISC-02 | System receives messages via Discord Gateway (WebSocket) | HIGH |
| DISC-03 | System handles reconnection with resume sequence | HIGH |
| DISC-04 | System captures embeds and attachments | MEDIUM |
| DISC-05 | System respects Discord's 50 req/sec global rate limit | HIGH |

### Feishu Integration (FEIS)

| ID | Description | Priority |
|----|-------------|----------|
| FEIS-01 | User can install Feishu app via OAuth 2.0 | HIGH |
| FEIS-02 | System receives messages via Feishu webhook events | HIGH |
| FEIS-03 | System handles multi-tenant token (app_token + tenant_token) | HIGH |
| FEIS-04 | System captures Feishu Wiki docs as content source | MEDIUM |
| FEIS-05 | System handles Chinese content encoding correctly | HIGH |

### WeCom Integration (WECO)

| ID | Description | Priority |
|----|-------------|----------|
| WECO-01 | User can configure WeCom bot webhook URL | HIGH |
| WECO-02 | System receives messages via WeCom webhook | HIGH |
| WECO-03 | System handles WeCom's message encryption (AES-256-CBC) | HIGH |
| WECO-04 | System respects WeCom's API rate limits | MEDIUM |

## Success Criteria

### Logseq:
1. User can configure local Logseq graph directory path
2. System parses Markdown files and extracts blocks as Claims
3. Property drawers map to Claim metadata correctly
4. System watches directory for file changes in real-time
5. User can edit in SAW and sync changes back to Logseq files
6. System detects concurrent edits and creates conflict copies
7. System preserves Logseq wikilink syntax during sync
8. Logseq namespaces map to SAW Wiki page hierarchy

### IM Platforms:
9. User can install Slack app and receive message events in real-time
10. User can add Discord bot to server and receive messages via Gateway
11. User can install Feishu app and sync Wiki docs
12. User can configure WeCom bot webhook for message ingestion
13. System captures thread context for threaded messages
14. System handles message reactions as confidence signals
15. System gracefully degrades when platforms are unavailable

## Technical Context

### Existing Architecture (Phase 10-12)

- **UnifiedConnectorInterface:** Protocol for all connectors
- **SyncEngine:** Bidirectional sync orchestration
- **MessageHandler:** IM message extraction (from Phase 11)
- **ReactionProcessor:** Reaction to confidence signals (from Phase 11)
- **ConnectorSink:** Write Queue integration

### SDKs (from STACK.md v3.1)

- **Logseq:** `edn-format 0.7.5`, `watchdog 6.0.0` (already in stack)
- **Slack:** `slack-sdk 3.41.0`, `slack-bolt 1.28.0`
- **Discord:** `discord.py 2.7.1`
- **Feishu:** `lark-oapi 1.5.5`
- **WeCom:** No official Python SDK, use `httpx` with webhook

### Logseq File Format

```markdown
---
title: Page Title
id:: 648a1b2c-uuid
created_at:: 2026-05-01T10:00:00
tags:: [[tag1]] [[tag2]]
confidence:: Layer 2
---

- First block
  - Nested block
    - Deep nested block
- Second block with [[wikilink]]
```

### IM Message Patterns

All IM platforms share common patterns via `MessageHandler`:
- Extract: content, author, timestamp, channel
- Thread context: parent_message_id
- Reactions: emoji → count mapping

## Design Decisions (Auto-Decided)

### Logseq:
1. **Block Parsing:** Each bullet point = one Claim. Nesting preserved via `parent_block_id`.
2. **File Watching:** Use `watchdog` with debouncing (500ms) to batch rapid changes.
3. **Conflict Detection:** SHA-256 hash of file content. Store hash in metadata. If hash changed on disk but not in SAW = concurrent edit.
4. **Conflict Resolution:** Create `.conflict` file with timestamp, keep both versions.
5. **Wikilink Preservation:** Regex pattern `\[\[([^\]]+)\]\]` preserved in Claim text.

### Slack:
1. **Events API:** Use `slack-bolt` for event handling. Verify signatures with signing secret.
2. **Rate Limits:** Tier-based: `tier_1` (1/min) to `tier_4` (100/min). Use `RateLimitManager`.
3. **Thread Context:** Store `thread_ts` as `thread_parent_id` in Claim metadata.

### Discord:
1. **Gateway:** Use `discord.py` with `Intents.messages` and `Intents.message_content`.
2. **Reconnection:** Implement `on_resumed` event handler. Store `session_id` for resume.
3. **Rate Limit:** 50 req/sec global, use built-in rate limiter in `discord.py`.

### Feishu:
1. **Multi-tenant Token:** Store `app_token` and `tenant_token` separately. Refresh both on expiry.
2. **Chinese Content:** Ensure UTF-8 encoding for all API calls. Handle GBK fallback.

### WeCom:
1. **Message Encryption:** AES-256-CBC with PKCS7 padding. Use `cryptography` library.
2. **Webhook:** Simple POST endpoint, no OAuth needed.

## Dependencies

- **Phase 10:** Connector framework (Complete)
- **Phase 11:** Sync engine, message handling (Complete)
- **Phase 12:** Notion patterns (Complete - reference)

## Out of Scope

- Logseq plugin development (outbound sync only)
- IM message sending (read-only ingestion)
- Real-time collaborative editing

---

*Context generated: 2026-05-02*
*Auto-decisions based on user instruction to make reasonable choices*
