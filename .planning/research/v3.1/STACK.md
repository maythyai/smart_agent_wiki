# Technology Stack — v3.1 Third-Party Integrations

**Project:** Smart Agent Wiki
**Milestone:** v3.1 Third-Party Integrations
**Researched:** 2026-05-01
**Confidence:** HIGH (versions verified via pip)

---

## Executive Summary

This document specifies the technology stack additions required for the v3.1 Third-Party Integrations milestone, which adds Notion, Logseq, IM (Slack/Discord/飞书), and GitHub integrations. These features extend the existing v2.0 API Platform with new bidirectional sync capabilities and real-time messaging intake channels.

**Key principle:** Leverage existing OAuth framework (v2.0) and Write Queue Outbox pattern (v1.1). Each integration is implemented as an independent "Sink" in the Write Queue architecture, enabling parallel, reliable sync operations.

**Existing capabilities NOT repeated here:**
- FastAPI REST API + GraphQL (v2.0)
- SQLite + PostgreSQL database (v2.0)
- JWT authentication + OAuth framework (v2.0)
- Write Queue Outbox pattern (v1.1)
- MCP Server 23 tools (v1.1)
- Plugin architecture (v3.0)

---

## Recommended Stack

### 1. Notion Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| notion-client | 3.0.0 | Official Notion SDK | Official Python client; full API coverage for databases, pages, blocks; async support |
| httpx | 0.28.1 | HTTP client | Already in stack; used by notion-client internally for async operations |

**Authentication Pattern:**
- Notion uses **OAuth 2.0** for workspace access
- Existing v2.0 OAuth framework handles token exchange
- Store `access_token` and `workspace_id` in existing `oauth_connections` table
- Token refresh handled by existing OAuth middleware

**Integration Points:**
```
Notion Workspace
      │
      ▼ (OAuth 2.0)
v2.0 OAuth Framework
      │
      ▼ (access_token)
NotionSyncEngine (new component)
      │
      ├─▶ GET /api/v1/wiki/{page} → Notion database row
      ├─▶ POST /api/v1/wiki/{page} ← Notion database update
      └─▶ Write Queue Outbox → Notion Sink (new)
```

**Key API Operations:**
- `databases.query` — Read Notion database as wiki pages
- `pages.create` / `pages.update` — Write wiki content to Notion
- `blocks.children.append` — Add content blocks
- `pages.properties.update` — Sync metadata/frontmatter

**Property Mapping (Notion ↔ SAW):**
| Notion Property | SAW Field | Type |
|-----------------|-----------|------|
| Title | wiki.title | string |
| Confidence | page.confidence | select (4-tier) |
| Freshness | page.freshness | select (9-level) |
| Last Sync | sync.last_modified | datetime |
| Source URL | claim.source_url | url |
| Tags | page.tags | multi-select |

---

### 2. Logseq Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| edn-format | 0.7.5 | EDN parser | Logseq uses EDN format; only mature Python EDN library |
| watchdog | 6.0.0 | File watching | Already in stack; monitor Logseq graph directory for changes |
| aiofiles | 25.1.0 | Async file I/O | Already in stack; read/write `.md` files in Logseq format |
| pyyaml | 6.0.2 | YAML frontmatter | Already in stack; parse Logseq page properties |

**Authentication Pattern:**
- Logseq is **local-first** — no OAuth required
- Access via local file system path (user configures graph location)
- File-based authentication: user grants read/write permission to graph directory

**Logseq File Format:**
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

**Integration Points:**
```
Logseq Graph Directory (local)
      │
      ▼ (file watch events)
watchdog observer (new component)
      │
      ▼ (parse .md files)
LogseqParser (new, uses edn-format for .edn, pyyaml for frontmatter)
      │
      ├─▶ Block-level extraction → Claims
      ├─▶ Page-level metadata → Wiki page properties
      └─▶ Write Queue Outbox → Logseq Sink (new)
```

**Block-to-Claim Mapping:**
| Logseq Block | SAW Claim |
|--------------|-----------|
| Block content | claim.text |
| Block UUID | claim.block_id |
| Page reference | claim.page_id |
| Indentation level | claim.nesting_level |
- `[[wikilinks]]` | claim.related_entities

**Key Design Decisions:**
- **Block-level granularity**: Each Logseq block becomes a Claim, preserving outline structure
- **Property sync**: Logseq page properties ↔ SAW wiki page metadata
- **Bi-directional sync**: Changes in SAW write back to Logseq as new/updated blocks
- **Conflict resolution**: Use `created_at` timestamps; last-modified wins

---

### 3. IM Integrations (Slack/Discord/飞书)

#### 3.1 Slack Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| slack-sdk | 3.41.0 | Slack Web API | Official Python SDK; comprehensive API coverage |
| slack-bolt | 1.28.0 | App framework | Handles events, commands, interactivity; async support |
| svix | 1.92.2 | Webhook verification | Industry-standard webhook signature verification |

**Authentication Pattern:**
- Slack uses **OAuth 2.0** (Bot User + Workspace access)
- v2.0 OAuth framework handles Slack OAuth flow
- Store `bot_token`, `user_token`, and `team_id` in `oauth_connections`
- Slack Bolt handles event subscription verification

**Integration Points:**
```
Slack Workspace Events
      │
      ▼ (Events API → Webhook)
FastAPI endpoint: POST /webhooks/slack
      │
      ▼ (signature verification via svix)
SlackEventHandler (new component)
      │
      ├─▶ message events → Ingest as conversation
      ├─▶ file_shared events → Ingest attachment
      └─▶ Write Queue Outbox → Slack Sink (for replies)
```

**Supported Events:**
| Event Type | SAW Action |
|------------|------------|
| `message.channels` | Ingest as conversational claim |
| `message.groups` | Ingest private channel message |
| `file_shared` | Download and ingest attachment |
| `reaction_added` | Update claim confidence (if configured) |
| `app_mention` | Trigger query and reply |

---

#### 3.2 Discord Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| discord.py | 2.7.1 | Discord Bot API | Official Python library; full bot + webhook support |
| httpx | 0.28.1 | Webhook client | Already in stack; Discord webhook execution |

**Authentication Pattern:**
- Discord uses **OAuth 2.0** for bot installation
- Bot token stored in `oauth_connections` (encrypted)
- Discord.py handles gateway connection and event dispatch

**Integration Points:**
```
Discord Gateway (WebSocket)
      │
      ▼ (events)
discord.py Client (new component)
      │
      ├─▶ on_message → Ingest message
      ├─▶ on_message_edit → Update existing claim
      └─▶ Write Queue Outbox → Discord Sink (for replies via webhook)
```

**Supported Events:**
| Event Type | SAW Action |
|------------|------------|
| `on_message` | Ingest as conversational claim |
| `on_message_edit` | Update claim with edit history |
| `on_reaction_add` | Update claim metadata |
| `on_thread_create` | Create new topic context |

---

#### 3.3 飞书 Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| lark-oapi | 1.5.5 | Feishu Open API | Official ByteDance SDK; comprehensive API coverage |

**Authentication Pattern:**
- Feishu uses **OAuth 2.0** (App ID + App Secret)
- Tenant access token for bot operations
- User access token for user-specific operations

**Integration Points:**
```
Feishu Events (Webhook)
      │
      ▼ (Event subscription)
FastAPI endpoint: POST /webhooks/feishu
      │
      ▼ (signature verification via lark-oapi)
FeishuEventHandler (new component)
      │
      ├─▶ message events → Ingest as conversation
      ├─▶ doc events → Sync wiki pages
      └─▶ Write Queue Outbox → Feishu Sink
```

**Supported Features:**
| Feature | SAW Action |
|---------|------------|
| Chat messages | Ingest as conversational claims |
| Wiki documents | Bidirectional sync with SAW wiki |
| Bitable (database) | Sync as structured claims |
| Calendar events | Ingest as temporal claims |

---

### 4. GitHub Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PyGithub | 2.9.1 | GitHub REST API | Comprehensive API coverage; Issues, PRs, Discussions, Releases |
| authlib | 1.7.0 | OAuth 2.0 flows | Already in stack; GitHub App OAuth flow |
| PyJWT | 2.10.1 | JWT for App auth | Generate JWT for GitHub App authentication |

**Authentication Pattern:**
- GitHub uses **OAuth 2.0** for user authorization
- GitHub Apps use JWT + App Private Key for server-to-server
- v2.0 OAuth framework handles user OAuth flow
- Store `access_token` (user) or `app_id` + `private_key` (App) in `oauth_connections`

**Integration Points:**
```
GitHub Events (Webhooks)
      │
      ▼ (Webhook delivery)
FastAPI endpoint: POST /webhooks/github
      │
      ▼ (signature verification via HMAC-SHA256)
GitHubEventHandler (new component)
      │
      ├─▶ issues events → Ingest issue as claim
      ├─▶ discussion events → Ingest discussion thread
      ├─▶ pull_request events → Ingest PR context
      └─▶ Write Queue Outbox → GitHub Sink (for comments)
```

**Supported Events:**
| Event Type | SAW Action |
|------------|------------|
| `issues.opened` | Ingest new issue as claim |
| `issues.edited` | Update claim content |
| `issue_comment.created` | Ingest comment as sub-claim |
| `discussion.created` | Ingest discussion thread |
| `pull_request.opened` | Ingest PR metadata |
| `push` | Trigger code ingestion (if configured) |

**API Operations:**
- `repo.get_issues()` — Query issues for ingestion
- `issue.create_comment()` — Post SAW responses as comments
- `discussion.get_comments()` — Read discussion threads
- `repo.get_contents()` — Ingest repository files

---

## Supporting Libraries

### OAuth & Authentication

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| authlib | 1.7.0 | OAuth 2.0 flows | Already in stack; handles Notion/Slack/GitHub/Feishu OAuth |
| PyJWT | 2.10.1 | JWT generation | Already in stack; GitHub App authentication |

### Webhook Handling

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| svix | 1.92.2 | Webhook verification | Slack webhook signature verification |
| httpx | 0.28.1 | HTTP client | Already in stack; Discord webhooks, API calls |

### File Processing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| edn-format | 0.7.5 | EDN parsing | Logseq graph format |
| watchdog | 6.0.0 | File watching | Already in stack; Logseq directory monitoring |
| aiofiles | 25.1.0 | Async file I/O | Already in stack; Logseq file operations |

### Retry & Reliability

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | 9.1.4 | Retry logic | Already in stack; API rate limit handling |

---

## Installation

```bash
# Notion Integration
pip install notion-client==3.0.0

# Slack Integration
pip install slack-sdk==3.41.0 slack-bolt==1.28.0 svix==1.92.2

# Discord Integration
pip install discord.py==2.7.1

# Feishu Integration
pip install lark-oapi==1.5.5

# GitHub Integration
pip install PyGithub==2.9.1

# Logseq Integration
pip install edn-format==0.7.5

# Note: authlib, httpx, watchdog, aiofiles, tenacity, PyJWT already in stack
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Notion SDK | notion-client | notion-py | notion-py is unmaintained; notion-client is official |
| Slack SDK | slack-sdk + slack-bolt | python-slackclient (old name) | Same package, renamed; use new name |
| Discord | discord.py | disnake | disnake is fork; discord.py is official and actively maintained |
| Feishu SDK | lark-oapi | feishu (unofficial) | lark-oapi is official ByteDance SDK |
| GitHub SDK | PyGithub | PyGitHub (capital G) | Same package; PyGithub is correct name |
| GitHub SDK | PyGithub | github3.py | PyGithub has larger community, more active maintenance |
| EDN Parsing | edn-format | pyclj | pyclj is unmaintained; edn-format is actively maintained |
| Webhook Verification | svix | Manual HMAC | svix provides replay protection, timing-safe comparison |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| requests | Synchronous; httpx already in stack for async | httpx 0.28.1 |
| websockets library | discord.py includes its own gateway | discord.py built-in |
| feedparser for GitHub | GitHub API is REST; no RSS needed | PyGithub |
| custom OAuth implementations | authlib already handles all flows | authlib 1.7.0 |
| asyncio-retry | tenacity already in stack for async retry | tenacity 9.1.4 |
| apscheduler for webhook retry | Write Queue Outbox handles reliability | Existing Outbox pattern |

---

## Architecture Integration

### Write Queue Sink Pattern

All four integrations follow the same Sink pattern:

```
Write Queue Outbox (v1.1)
      │
      ├─▶ NotionSink (new)
      │     └─ notion-client: pages.update()
      │
      ├─▶ LogseqSink (new)
      │     └─ aiofiles: write .md files
      │
      ├─▶ SlackSink (new)
      │     └─ slack-sdk: chat.postMessage()
      │
      ├─▶ DiscordSink (new)
      │     └─ httpx: Webhook URL POST
      │
      ├─▶ FeishuSink (new)
      │     └─ lark-oapi: message.send()
      │
      └─▶ GitHubSink (new)
            └─ PyGithub: issue.create_comment()
```

### Webhook Endpoint Structure

```
/api/v1/webhooks/
    ├── slack       → SlackEventHandler
    ├── discord     → DiscordEventHandler
    ├── feishu      → FeishuEventHandler
    └── github      → GitHubEventHandler
```

### OAuth Connection Storage

Existing `oauth_connections` table (v2.0) extended for v3.1:

```sql
ALTER TABLE oauth_connections ADD COLUMN platform VARCHAR(50);
-- Values: 'notion', 'slack', 'discord', 'feishu', 'github'

ALTER TABLE oauth_connections ADD COLUMN metadata JSON;
-- Platform-specific data:
-- notion: { "workspace_id": "...", "workspace_name": "..." }
-- slack: { "team_id": "...", "team_name": "...", "bot_user_id": "..." }
-- discord: { "guild_id": "...", "guild_name": "..." }
-- feishu: { "tenant_token": "...", "app_id": "..." }
-- github: { "app_id": "...", "installation_id": "..." }
```

---

## API Endpoints Required

### New v3.1 Endpoints

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/api/v1/webhooks/slack` | POST | Slack event delivery | Slack Events API |
| `/api/v1/webhooks/discord` | POST | Discord interaction | Discord Interactions |
| `/api/v1/webhooks/feishu` | POST | Feishu event delivery | Feishu Event Subscription |
| `/api/v1/webhooks/github` | POST | GitHub webhook delivery | GitHub Webhooks |
| `/api/v1/integrations` | GET | List connected integrations | Web UI |
| `/api/v1/integrations/{platform}` | POST | Initiate OAuth flow | Web UI |
| `/api/v1/integrations/{platform}/callback` | GET | OAuth callback | OAuth Providers |
| `/api/v1/integrations/{platform}/sync` | POST | Trigger manual sync | CLI, Web UI |
| `/api/v1/notion/databases` | GET | List Notion databases | Web UI (database selection) |
| `/api/v1/logseq/graph` | GET | Get graph status | Web UI |
| `/api/v1/github/repos` | GET | List accessible repos | Web UI (repo selection) |

---

## Sources

- notion-client PyPI: https://pypi.org/project/notion-client/ (version verified 2026-05-01)
- slack-sdk PyPI: https://pypi.org/project/slack-sdk/ (version verified 2026-05-01)
- slack-bolt PyPI: https://pypi.org/project/slack-bolt/ (version verified 2026-05-01)
- discord.py PyPI: https://pypi.org/project/discord.py/ (version verified 2026-05-01)
- lark-oapi PyPI: https://pypi.org/project/lark-oapi/ (version verified 2026-05-01)
- PyGithub PyPI: https://pypi.org/project/PyGithub/ (version verified 2026-05-01)
- edn-format PyPI: https://pypi.org/project/edn-format/ (version verified 2026-05-01)
- svix PyPI: https://pypi.org/project/svix/ (version verified 2026-05-01)
- authlib PyPI: https://pypi.org/project/authlib/ (version verified 2026-05-01)

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Notion SDK | HIGH | notion-client 3.0.0 is official, stable, async-compatible |
| Slack SDK | HIGH | slack-sdk 3.41.0 + slack-bolt 1.28.0 are official, actively maintained |
| Discord SDK | HIGH | discord.py 2.7.1 is official, comprehensive bot framework |
| Feishu SDK | HIGH | lark-oapi 1.5.5 is official ByteDance SDK |
| GitHub SDK | HIGH | PyGithub 2.9.1 is widely adopted, active maintenance |
| Logseq EDN | MEDIUM | edn-format 0.7.5 is the only option; Logseq format may need reverse-engineering |
| Webhook Handling | HIGH | svix is industry standard; HMAC-SHA256 patterns well-documented |
| OAuth Integration | HIGH | authlib 1.7.0 already in stack; all platforms use standard OAuth 2.0 |

---

*This document extends the existing v3.0 STACK.md. The core backend stack (FastAPI, SQLite, LiteLLM, etc.) is already established in v1.1-v2.0 and not repeated here.*
