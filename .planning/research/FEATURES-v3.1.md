# Feature Research: Third-Party Integrations (v3.1)

**Domain:** Third-party platform integrations for Smart Agent Wiki
**Researched:** 2026-05-02
**Context:** Subsequent milestone building on v3.0 Ecosystem Integration (Obsidian, Chrome, RSS)
**Confidence:** MEDIUM (based on training knowledge; web searches unavailable)

---

## Overview

This research covers four integration categories for Smart Agent Wiki v3.1:
1. **Notion** — Cloud-based knowledge management with database sync
2. **Logseq** — Local-first knowledge graph with file-based storage
3. **IM Platforms** — Slack, Discord, Feishu (飞书) message ingestion
4. **GitHub** — Issues, Discussions, PR synchronization

Each integration has distinct characteristics:
- **Notion**: Cloud-native, API-first, OAuth authentication
- **Logseq**: Local-first, file-based, no API (direct file manipulation)
- **IM Platforms**: Event-driven, webhook-based, real-time ingestion
- **GitHub**: Hybrid (API + Webhooks), OAuth authentication

---

## Notion Integration

**Context:** Notion is a cloud-based workspace with databases, pages, and rich content. Users want to sync their SAW knowledge base with Notion databases for collaboration and alternative views.

### Table Stakes (Notion)

Features users expect from any Notion integration.

| Feature | Why Expected | Complexity | Dependency on SAW | Notes |
|---------|--------------|------------|-------------------|-------|
| **OAuth Authentication** | Standard Notion integration pattern | Medium | Auth system | Notion requires OAuth flow for external apps |
| **Database Query** | Must be able to read Notion databases | Medium | Query Engine | `POST /v1/databases/{database_id}/query` |
| **Page CRUD** | Create, read, update Notion pages | Medium | Ingest Engine | `POST /v1/pages`, `PATCH /v1/pages/{page_id}` |
| **Property Mapping** | Map Notion properties to SAW fields | High | Claims DB | Notion has 10+ property types |
| **Incremental Sync** | Don't re-sync unchanged content | Medium | Vault (SHA256) | Use `last_edited_time` timestamp |
| **Rate Limit Handling** | Notion has strict rate limits (3 req/s) | Medium | Write Queue | Implement backoff + retry |
| **Pagination** | Notion API paginates all list responses | Low | Query Engine | `start_cursor` / `has_more` / `next_cursor` |

### Differentiators (Notion)

Features unique to SAW's Notion integration.

| Feature | Value Proposition | Complexity | Dependency on SAW | Notes |
|---------|-------------------|------------|-------------------|-------|
| **Confidence Badge as Property** | Visual trust indicator in Notion views | Low | Governance Engine | `select` property with confidence tier |
| **Freshness as Date Property** | Filter/sort by knowledge age in Notion | Low | Governance Engine | `date` property from freshness timestamp |
| **Source Link Backlink** | Click-through from Notion to SAW Vault | Medium | Vault Layer | URL property pointing to local SAW instance |
| **Bidirectional Property Sync** | Changes in either direction propagate | High | Claims DB + Notion | Conflict resolution required |
| **Database Templates** | Pre-configured Notion databases for SAW types | Medium | None | Templates for concepts, entities, debates |
| **Relation Property Sync** | Sync wikilinks as Notion relations | High | Graph Index | Map `[[wikilinks]]` to `relation` properties |
| **Rollup Aggregation** | Notion rollups for derived metrics | Medium | Claims DB | Count of claims, avg confidence per page |

### Anti-Features (Notion)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time sync** | Notion has no real-time webhooks for page changes; polling required | Poll every 5-15 minutes with incremental sync |
| **Block-level sync** | Notion block API is complex; full-page sync simpler | Sync at page level; treat blocks as opaque content |
| **Custom Notion workspace** | Users have existing Notion setups | Connect to user's existing databases/pages |
| **Formula/Rollup recreation** | Notion formulas are Notion-side; recreating in SAW is duplication | Import formula results as static values; note dependency |

### Property Type Mapping (Notion <-> SAW)

| Notion Property Type | SAW Field | Sync Direction | Notes |
|---------------------|-----------|----------------|-------|
| `title` | Wiki page title | Bidirectional | Primary identifier |
| `rich_text` | Markdown content | Bidirectional | Convert to/from Notion blocks |
| `select` | Type/Category | Bidirectional | Map to SAW page type |
| `multi_select` | Tags | Bidirectional | Map to SAW tags array |
| `date` | Created/Updated/Freshness | Bidirectional | ISO 8601 format |
| `relation` | Wikilinks | Bidirectional | Complex; requires both pages in Notion |
| `url` | Source URL | SAW -> Notion | Link to original source |
| `number` | Confidence score | SAW -> Notion | 1-4 scale |
| `checkbox` | Human verified | Bidirectional | Boolean flag |
| `files` | Attachments | Notion -> SAW | Download and store in Vault |

### Conflict Resolution (Notion)

| Conflict Type | Detection | Resolution Strategy |
|---------------|-----------|---------------------|
| **Concurrent Edit** | `last_edited_time` comparison | Last-write-wins; log conflict for review |
| **Property Type Mismatch** | Schema comparison | Preserve both as separate fields; flag for review |
| **Deleted in Notion** | Page not found on query | Soft delete (archive) in SAW; preserve Vault |
| **Deleted in SAW** | Notion page has no SAW match | Prompt user: keep in Notion or delete? |
| **Relation Dangling** | Relation points to non-existent page | Create placeholder; flag for completion |

### Rate Limits (Notion)

| Limit | Value | Strategy |
|-------|-------|----------|
| Request rate | 3 requests/second | Token bucket in Write Queue |
| Burst | ~10 requests | Batch operations where possible |
| Pagination | 100 pages max per query | Use `start_cursor` for large databases |

### Sync Architecture (Notion)

```
Notion Sync Architecture:

[Notion API] <--> [Sync Engine] <--> [Claims DB]
      |                  |                |
      +-- OAuth          +-- Conflict     +-- Property Map
      +-- Rate Limit     +-- Incremental  +-- Confidence
      +-- Pagination     +-- Queue        +-- Freshness
```

**Sync Flow:**
1. User authorizes via OAuth
2. Select Notion database(s) to sync
3. Initial full sync (paginated query)
4. Incremental sync every N minutes (query `last_edited_time > last_sync`)
5. Outbound: Watch SAW changes, push to Notion
6. Conflict detection + resolution

---

## Logseq Integration

**Context:** Logseq is a local-first, privacy-focused knowledge management tool. It stores data as Markdown or Org-mode files with a specific structure. No API exists—integration is file-based.

### Table Stakes (Logseq)

Features users expect from any Logseq integration.

| Feature | Why Expected | Complexity | Dependency on SAW | Notes |
|---------|--------------|------------|-------------------|-------|
| **File Read/Write** | Logseq stores as files; integration must work with files | Medium | Vault Layer | Markdown files with specific format |
| **Block-level Parsing** | Logseq's fundamental unit is the "block" (bullet point) | High | Ingest Engine | Each bullet = potential claim |
| **Property Drawer Parsing** | Logseq uses `::` syntax for properties | Medium | Metadata | `property:: value` format |
| **Wikilink Support** | Logseq uses `[[wikilinks]]` natively | Low | Existing support | Already supported in SAW |
| **Graph Awareness** | Logseq has built-in graph view | Low | Graph Index | Sync wikilink relationships |
| **Namespace Support** | Logseq uses `namespace/page` organization | Medium | Wiki structure | Map to SAW categories |

### Differentiators (Logseq)

Features unique to SAW's Logseq integration.

| Feature | Value Proposition | Complexity | Dependency on SAW | Notes |
|---------|-------------------|------------|-------------------|-------|
| **Block <-> Claim Mapping** | Map Logseq blocks to SAW claims with granular provenance | High | Claims DB | Preserve block hierarchy |
| **Daily Notes Sync** | Logseq's journal feature syncs with SAW's temporal knowledge | Medium | Wiki | Map `yyyy-mm-dd.md` to date pages |
| **Query Block Interpretation** | Logseq queries become SAW query templates | High | Query Engine | `{{query ...}}` syntax |
| **TODO State Sync** | Logseq TODOs become SAW tasks with freshness | Medium | Learn Engine | DONE/FDOING/TODO states |
| **Confidence as Property** | Add `confidence::` property to blocks | Low | Governance Engine | Custom property per block |
| **Source Attribution** | Add `source::` property pointing to Vault | Medium | Vault | `source:: [[vault:uuid]]` format |
| **Template Sync** | Logseq templates map to SAW page templates | Medium | Wiki | `/template` namespace |

### Anti-Features (Logseq)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time sync** | File watching is fragile; conflicts likely | Periodic sync with user trigger |
| **Block ID injection** | Logseq has block IDs but they're internal | Use content hash for identification |
| **Custom renderer** | Logseq renders its own way; custom rendering breaks | Export standard Markdown; let Logseq render |
| **PDF annotation sync** | Logseq PDF annotations are complex; scope creep | Sync text notes only; PDFs stay separate |

### File Format Mapping (Logseq <-> SAW)

| Logseq Concept | SAW Concept | Mapping |
|----------------|-------------|---------|
| Page (`page.md`) | Wiki page | 1:1 mapping |
| Block (bullet) | Claim | Extract as claim with hierarchy |
| Property (`key:: value`) | Frontmatter / Claim metadata | Parse and map |
| Wikilink (`[[page]]`) | Wikilink | Direct mapping |
| Tag (`#tag`) | Tag | Direct mapping |
| Namespace (`parent/child`) | Category hierarchy | Map to SAW categories |
| Daily note (`2024-01-01.md`) | Dated page | Map to SAW temporal pages |
| Query (`{{query}}`) | Saved query | Convert to SAW query template |
| Embed (`{{embed}}`) | Transclusion | Resolve to content |

### Conflict Resolution (Logseq)

| Conflict Type | Detection | Resolution Strategy |
|---------------|-----------|---------------------|
| **File modified in both** | SHA256 hash comparison | Last-write-wins based on mtime |
| **Block deleted in Logseq** | Block not found in file | Archive claim; preserve in Vault |
| **Block deleted in SAW** | Claim not found | Remove from Logseq file |
| **Property mismatch** | Different `key:: value` | Merge or prompt user |
| **Wikilink broken** | Target page not found | Flag for review in both systems |

### Sync Architecture (Logseq)

```
Logseq Sync Architecture:

[Logseq Files] <--> [File Watcher] <--> [Sync Engine] <--> [Claims DB]
      |                   |                   |                 |
      +-- .md/.org        +-- inotify/FSEvents +-- Block Parser  +-- Claim mapping
      +-- pages/          +-- Coalesce         +-- Property Map  +-- Wikilinks
      +-- journals/       +-- Debounce         +-- Conflict      +-- Confidence
```

**Sync Flow:**
1. User specifies Logseq graph directory
2. Initial scan: parse all `.md` files in `pages/` and `journals/`
3. Extract blocks as claims with hierarchy
4. Create bidirectional wikilink map
5. Watch for file changes (inotify/FSEvents)
6. On change: parse modified files, detect conflicts
7. Apply sync with conflict resolution

### Block Parsing Strategy

```markdown
- Main block content
  - Nested block 1
    - Deeply nested
  - Nested block 2
  property:: value
  another:: data
```

**Parsed as:**
```yaml
- id: block-hash-1
  content: "Main block content"
  level: 0
  children:
    - id: block-hash-2
      content: "Nested block 1"
      level: 1
      children:
        - id: block-hash-3
          content: "Deeply nested"
          level: 2
    - id: block-hash-4
      content: "Nested block 2"
      level: 1
      properties:
        property: value
        another: data
```

---

## IM Platform Integration

**Context:** Instant messaging platforms contain valuable knowledge in conversations. Users want to ingest messages from Slack, Discord, and Feishu (飞书) into their knowledge base.

### Common Patterns Across IM Platforms

| Feature | Slack | Discord | Feishu |
|---------|-------|---------|--------|
| **Authentication** | OAuth 2.0 | Bot Token | App ID + Secret |
| **Message Access** | Web API | Gateway + REST | REST API |
| **Real-time Events** | Events API | Gateway | Webhook |
| **Rate Limits** | Tier-based (1-100+ req/min) | Global (50 req/sec) | Tenant-based |
| **Message Format** | Blocks (JSON) | Embeds (JSON) | Card (JSON) |
| **Threading** | Thread replies | Thread channels | Reply chain |
| **Files/Attachments** | Files API | CDN URLs | Drive API |

### Table Stakes (IM Platforms)

Features users expect from any IM integration.

| Feature | Why Expected | Complexity | Dependency on SAW | Notes |
|---------|--------------|------------|-------------------|-------|
| **Message Ingestion** | Core function: capture messages | Medium | Ingest Engine | Parse message content |
| **Channel/Server Selection** | Users want to choose what to ingest | Low | Config | Filter by channel/server |
| **User Attribution** | Know who said what | Low | Claims DB | Map user ID to name |
| **Timestamp Preservation** | When was message sent | Low | Claims DB | ISO 8601 timestamp |
| **Thread Context** | Messages in context of conversation | Medium | Claims DB | Parent message reference |
| **Attachment Handling** | Files/images in messages | High | Vault | Download and store |
| **Incremental Sync** | Don't re-ingest old messages | Medium | Vault | Track last message timestamp |

### Slack Integration

#### Table Stakes (Slack)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **OAuth Installation** | Slack apps require OAuth flow | Medium | `chat:read`, `files:read` scopes |
| **Channel List** | Select channels to ingest | Low | `conversations.list` API |
| **Message History** | `conversations.history` API | Medium | Pagination with `cursor` |
| **Thread Replies** | `conversations.replies` API | Medium | Ingest as child claims |
| **User Info** | `users.info` for attribution | Low | Cache user mapping |
| **File Download** | `files.info` + URL | Medium | Store in Vault |
| **Rate Limits** | Tier-based rate limits | Medium | `Retry-After` header handling |

#### Differentiators (Slack)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Reaction as Signal** | :+1: reactions indicate valuable content | Low | Use reactions for confidence weighting |
| **Pin as High-Value** | Pinned messages are knowledge-worthy | Low | Auto-elevate confidence for pins |
| **Starred Messages** | User's starred messages are personal knowledge | Medium | Sync user's stars |
| **Link Unfurling** | Extract content from links in messages | High | Already have URL ingestion |
| **Bot Message Detection** | Filter out bot messages or attribute correctly | Medium | Check `bot_id` field |
| **Slack Connect** | Ingest from external org channels | High | Verify permissions |

#### Rate Limits (Slack)

| Tier | Rate Limit | Methods |
|------|------------|---------|
| Tier 1 | 1 req/min | `conversations.history` |
| Tier 2 | 20 req/min | `conversations.list`, `users.info` |
| Tier 3 | 100 req/min | `chat.post` |
| Tier 4 | 100+ req/min | `files.*` |

### Discord Integration

#### Table Stakes (Discord)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Bot Setup** | Discord requires bot application | Low | Developer portal setup |
| **Guild/Channel Access** | Read messages in servers | Medium | `MESSAGE_CONTENT` intent |
| **Message Gateway** | Real-time via WebSocket | High | Event-driven ingestion |
| **Message History** | REST API for backfill | Medium | `GET /channels/{id}/messages` |
| **User Avatar** | User identification | Low | Store avatar URL |
| **Attachment URLs** | Files are CDN URLs | Low | Download and store |
| **Embed Parsing** | Rich content in embeds | Medium | Extract structured data |

#### Differentiators (Discord)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Forum Channels** | Structured discussions with threads | Medium | Map to discussion pages |
| **Thread as Page** | Each thread becomes a wiki page | Low | Coherent conversation unit |
| **Reaction Aggregation** | Aggregate reactions across messages | Medium | Measure community agreement |
| **Voice Transcription** | Transcribe voice channel audio | Very High | Requires separate service |
| **Server Archive** | Full server knowledge extraction | High | Multiple channels, threads |

#### Rate Limits (Discord)

| Type | Rate Limit | Strategy |
|------|------------|----------|
| Global | 50 req/sec | Global bucket |
| Route-specific | Varies by route | Check `X-RateLimit-*` headers |
| Bucket reset | `X-RateLimit-Reset-After` | Wait before retry |

### Feishu (飞书) Integration

#### Table Stakes (Feishu)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **App Authentication** | App ID + App Secret | Medium | `auth/v3/app_access_token/internal` |
| **Tenant Access Token** | Multi-tenant support | Medium | `auth/v3/tenant_access_token/internal` |
| **Message List** | `im/v1/messages` API | Medium | `receive_time` pagination |
| **Chat List** | `im/v1/chats` API | Low | Select chats to ingest |
| **User Info** | `contact/v3/users/{user_id}` | Low | User attribution |
| **File Download** | `drive/v1/files/{file_token}` | High | Lark Drive API |
| **Rich Text Parsing** | Card/Post message parsing | High | JSON structure to Markdown |

#### Differentiators (Feishu)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Doc Integration** | Feishu Doc -> Wiki page | High | Separate from chat messages |
| **Wiki Space** | Feishu Wiki sync | Very High | Full wiki sync |
| **Multi-language** | Chinese/English content | Low | Already multi-language aware |
| **Approval Flow** | Knowledge requiring approval | High | Governance integration |
| **Organization Chart** | User context from org structure | Medium | Enhanced attribution |

#### Rate Limits (Feishu)

| Type | Rate Limit | Strategy |
|------|------------|----------|
| App-level | Varies by API | Check response headers |
| Tenant-level | Per-tenant limits | Multi-tenant aware |

### Anti-Features (IM Platforms)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time ingestion only** | Missing historical context; user may want backfill | Support both real-time (webhook) and historical (API) |
| **Full server sync** | Overwhelming; users want selective ingestion | Channel/chat selection with filters |
| **Edit/Delete tracking** | Complex; often not needed for knowledge | Ingest at point-in-time; optional re-sync |
| **Private message ingestion** | Privacy concerns; scope creep | Public channels only (with clear documentation) |
| **Message sending** | Not a knowledge management function | Read-only integration |

### Message to Claim Mapping

```
IM Message -> SAW Claim Mapping:

Message:
  - id: msg_12345
  - user: @alice
  - channel: #general
  - timestamp: 2024-01-15T10:30:00Z
  - content: "The new API rate limit is 100 req/sec"
  - thread_ts: null (top-level)
  - reactions: [{"name": "thumbsup", "count": 3}]

Claim:
  - id: claim-hash
  - content: "The new API rate limit is 100 req/sec"
  - source_uuid: vault-im-slack-general
  - source_location: msg_12345
  - confidence: 2 (Single Source)
  - confidence_modifier: +0.5 (3 reactions indicate community validation)
  - metadata:
      author: alice
      channel: general
      platform: slack
      thread_position: top-level
```

### Sync Architecture (IM Platforms)

```
IM Integration Architecture:

[Slack/Discord/Feishu] --> [Webhook/Gateway] --> [Message Queue] --> [Ingest Engine]
        |                        |                     |                   |
        +-- OAuth/Token          +-- Event Filter      +-- Dedupe         +-- Claim extraction
        +-- API Client           +-- Rate Limit        +-- Buffer         +-- Confidence calc
                                 +-- Parse             +-- Batch          +-- Vault storage
```

**Ingestion Modes:**

| Mode | Description | Use Case |
|------|-------------|----------|
| **Real-time** | Webhook/Gateway events | Live conversation capture |
| **Scheduled** | Periodic API poll | Backfill, offline catch-up |
| **Manual** | User-triggered import | Specific channel/message selection |
| **Selective** | Keyword/regex filter | Targeted knowledge extraction |

---

## GitHub Integration

**Context:** GitHub contains valuable knowledge in Issues, Discussions, and Pull Requests. Users want to sync this structured content with their knowledge base.

### Table Stakes (GitHub)

Features users expect from any GitHub integration.

| Feature | Why Expected | Complexity | Dependency on SAW | Notes |
|---------|--------------|------------|-------------------|-------|
| **OAuth Authentication** | Standard GitHub App pattern | Medium | Auth system | `repo`, `read:org` scopes |
| **Repository Selection** | Choose which repos to sync | Low | Config | User's repos or org repos |
| **Issue Sync** | Issues as knowledge items | Medium | Claims DB | Map issue body to claims |
| **Discussion Sync** | Discussions as knowledge threads | High | Claims DB | Different API endpoint |
| **PR Metadata** | PRs as development context | Medium | Vault | PR description, comments |
| **Comment Ingestion** | Comments contain valuable insights | Medium | Claims DB | Issue/PR/Discussion comments |
| **Label as Tag** | GitHub labels map to SAW tags | Low | Metadata | Direct mapping |
| **Milestone as Category** | Group issues by milestone | Low | Metadata | Optional categorization |
| **User Attribution** | Map GitHub users to knowledge authors | Low | Claims DB | Cache user mapping |

### Differentiators (GitHub)

Features unique to SAW's GitHub integration.

| Feature | Value Proposition | Complexity | Dependency on SAW | Notes |
|---------|-------------------|------------|-------------------|-------|
| **Code Reference Extraction** | Extract code blocks from issues/PRs | Medium | Claims DB | Code claims with syntax highlighting |
| **Cross-reference Resolution** | Resolve `#123` issue references | High | Graph Index | Create wikilinks between related items |
| **Commit-Claim Linking** | Link commits to knowledge claims | High | Vault | `git commit` references claims |
| **Repository Knowledge Graph** | Visualize repo knowledge structure | High | Graph Index | Issues, PRs, Discussions as nodes |
| **Search-Based Ingestion** | GitHub Search API for targeted sync | Medium | Query Engine | Search query -> ingest results |
| **Webhook Real-time** | Real-time sync on new issues/PRs | Medium | Write Queue | GitHub Webhooks |
| **Release Notes Sync** | Releases as version history pages | Low | Wiki | Auto-generate version pages |
| **Action Workflow Knowledge** | Extract CI/CD knowledge | High | Claims DB | Parse workflow YAML |

### Anti-Features (GitHub)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Codebase sync** | GitHub is for code, but SAW is for knowledge | Ingest docs, README, wiki, not source code |
| **PR code review** | Code review is development activity | Ingest PR comments, not the review process |
| **CI/CD state** | Ephemeral, not knowledge | Ignore workflow runs |
| **Fork/Star sync** | Social metrics, not knowledge | Skip fork/star data |
| **Full clone** | SAW has separate ingestion for repos | Use API for metadata, not git clone |

### API Endpoints (GitHub)

| Resource | Endpoint | Pagination | Rate Limit |
|----------|----------|------------|------------|
| Issues | `GET /repos/{owner}/{repo}/issues` | `page` / `per_page` | 5000 req/hr (auth) |
| Issue | `GET /repos/{owner}/{repo}/issues/{issue_number}` | N/A | Same |
| Issue Comments | `GET /repos/{owner}/{repo}/issues/{issue_number}/comments` | `page` / `per_page` | Same |
| Discussions | `GET /repos/{owner}/{repo}/discussions` | `page` / `per_page` | GraphQL API |
| Discussion | `GET /repos/{owner}/{repo}/discussions/{discussion_number}` | N/A | GraphQL API |
| Pull Requests | `GET /repos/{owner}/{repo}/pulls` | `page` / `per_page` | Same |
| PR Review Comments | `GET /repos/{owner}/{repo}/pulls/{pull_number}/comments` | `page` / `per_page` | Same |
| Releases | `GET /repos/{owner}/{repo}/releases` | `page` / `per_page` | Same |
| Search | `GET /search/issues?q={query}` | `page` / `per_page` | 30 req/min |

### Data Model Mapping (GitHub <-> SAW)

| GitHub Entity | SAW Entity | Mapping |
|---------------|------------|---------|
| Issue | Wiki Page | `issue-{number}.md` |
| Issue Body | Primary Claim | First claim from issue |
| Issue Comment | Claim | Claim with issue context |
| Discussion | Wiki Page | `discussion-{number}.md` |
| Discussion Reply | Claim | Claim with discussion context |
| PR | Wiki Page | `pr-{number}.md` |
| PR Description | Primary Claim | Feature/fix description |
| PR Comment | Claim | Review comments |
| Label | Tag | Direct mapping |
| Milestone | Category | Group by milestone |
| Assignee | Author | Attribution |
| Reactions | Confidence Signal | :+1: adds confidence |
| Cross-references (`#123`) | Wikilink | `[[issue-123]]` |

### Conflict Resolution (GitHub)

| Conflict Type | Detection | Resolution Strategy |
|---------------|-----------|---------------------|
| **Issue updated on GitHub** | `updated_at` timestamp | Re-sync; create new version |
| **Issue closed/reopened** | State change | Update status; preserve history |
| **Issue deleted on GitHub** | 404 response | Archive in SAW; mark as deleted |
| **Label added/removed** | Label list change | Update tags; preserve history |
| **Comment edited** | `edited_at` timestamp | Update claim; track revision |

### Webhook Events (GitHub)

| Event | Trigger | Action |
|-------|---------|--------|
| `issues` | Issue opened/closed/edited/reopened | Sync issue |
| `issue_comment` | Comment created/edited/deleted | Sync comment |
| `discussion` | Discussion created/edited/closed | Sync discussion |
| `discussion_comment` | Discussion comment created | Sync comment |
| `pull_request` | PR opened/closed/merged | Sync PR |
| `pull_request_review_comment` | PR review comment | Sync comment |
| `release` | Release published | Create version page |
| `push` | Push to main (docs only) | Ingest updated docs |

### Sync Architecture (GitHub)

```
GitHub Integration Architecture:

[GitHub API] <--> [Sync Engine] <--> [Claims DB]
      |                  |                |
      +-- OAuth          +-- Rate Limit   +-- Issue -> Claim
      +-- Webhooks       +-- Pagination   +-- PR -> Page
      +-- GraphQL        +-- Incremental  +-- Discussion -> Thread
```

**Sync Flow:**
1. User authorizes GitHub App (OAuth)
2. Select repositories to sync
3. Initial sync: fetch all issues/discussions/PRs (paginated)
4. Store `updated_at` for incremental sync
5. Set up webhooks for real-time updates
6. On webhook event: parse and ingest
7. Periodic full sync for missed events

---

## Feature Dependencies

```
# Cross-Platform Dependencies

Governance Engine (Confidence System)
    └── All Integrations --> Confidence display/inheritance
        
Vault Layer (Immutable Storage)
    └── All Integrations --> Source document storage
        
Claims DB
    └── All Integrations --> Structured claim storage
        
Write Queue (Outbox)
    └── Notion --> Rate limit queue
    └── Slack/Discord/Feishu --> Message buffer
    └── GitHub --> Webhook event queue
        
Graph Index
    └── Notion --> Relation properties
    └── Logseq --> Wikilink sync
    └── GitHub --> Cross-references

# Platform-Specific Dependencies

Notion Integration:
    OAuth System --> Auth system
    Rate Limiter --> Write Queue
    Property Mapper --> Claims DB schema

Logseq Integration:
    File Watcher --> Platform-specific (inotify/FSEvents)
    Block Parser --> Ingest Engine
    Conflict Resolver --> Vault (SHA256)

IM Platforms:
    Webhook Server --> FastAPI
    Message Queue --> Write Queue
    User Cache --> Metadata storage

GitHub Integration:
    OAuth System --> Auth system
    GraphQL Client --> Optional (for Discussions)
    Webhook Handler --> FastAPI
```

---

## MVP Recommendations

### Priority Matrix

| Integration | User Value | Implementation Cost | Priority |
|-------------|------------|---------------------|----------|
| **GitHub Issues/Discussions** | HIGH - Developer knowledge | MEDIUM - Well-documented API | P1 |
| **Notion Database Sync** | HIGH - Popular tool, collaboration | HIGH - Complex property mapping | P1 |
| **Slack Message Ingestion** | MEDIUM - Team knowledge capture | MEDIUM - OAuth + rate limits | P2 |
| **Logseq File Sync** | MEDIUM - Local-first overlap | MEDIUM - File watching complexity | P2 |
| **Discord Message Ingestion** | MEDIUM - Community knowledge | MEDIUM - Gateway complexity | P2 |
| **Feishu Integration** | LOW-MEDIUM - Regional | HIGH - Less familiar API | P3 |

### Phase 10: GitHub + Notion (MVP)

**Rationale:** GitHub and Notion have the clearest use cases for SAW's target audience (knowledge workers and developers).

| Feature | Integration | Complexity |
|---------|-------------|------------|
| OAuth authentication | GitHub, Notion | Medium |
| Issue sync (read) | GitHub | Medium |
| Database sync (read) | Notion | High |
| Property mapping | Notion | High |
| Incremental sync | Both | Medium |
| Webhook events | GitHub | Medium |

### Phase 11: IM Platforms

**Rationale:** IM ingestion adds real-time knowledge capture capability.

| Feature | Platform | Complexity |
|---------|----------|------------|
| Bot setup | Slack, Discord | Low |
| Message ingestion | All | Medium |
| Channel selection | All | Low |
| Thread context | Slack, Discord | Medium |
| Rate limit handling | All | Medium |

### Phase 12: Logseq + Bidirectional

**Rationale:** File-based sync and bidirectional updates require more complex conflict resolution.

| Feature | Integration | Complexity |
|---------|-------------|------------|
| File watching | Logseq | Medium |
| Block parsing | Logseq | High |
| Bidirectional sync | Notion, Logseq | High |
| Conflict resolution | Both | High |

---

## Complexity Summary

| Integration | OAuth/API Auth | Sync Pattern | Conflict Resolution | Overall |
|-------------|----------------|--------------|---------------------|---------|
| **Notion** | OAuth 2.0 | Polling + bidirectional | Property-level | HIGH |
| **Logseq** | None (local) | File watching + bidirectional | Block-level | MEDIUM-HIGH |
| **Slack** | OAuth 2.0 | Webhook + API backfill | N/A (read-only) | MEDIUM |
| **Discord** | Bot Token | Gateway + REST | N/A (read-only) | MEDIUM |
| **Feishu** | App ID + Secret | REST API | N/A (read-only) | MEDIUM-HIGH |
| **GitHub** | OAuth 2.0 | API + Webhooks | Version tracking | MEDIUM |

---

## Confidence Assessment

| Integration | Confidence | Notes |
|-------------|------------|-------|
| GitHub | HIGH | Well-documented API, common integration pattern |
| Notion | HIGH | Good official SDK, clear API documentation |
| Logseq | MEDIUM | File-based, no official API; format may change |
| Slack | HIGH | Mature API, extensive documentation |
| Discord | MEDIUM-HIGH | Gateway complexity, but well-documented |
| Feishu | MEDIUM | Less familiar, language barrier in docs |

---

## Sources

**Research methodology:** Training knowledge of API patterns, integration best practices, and platform-specific documentation. Web searches were unavailable due to network restrictions.

**Recommended verification:**
1. Notion API documentation: https://developers.notion.com/
2. GitHub REST API: https://docs.github.com/en/rest
3. Slack API: https://api.slack.com/
4. Discord Developer Portal: https://discord.com/developers/docs
5. Feishu Open Platform: https://open.feishu.cn/
6. Logseq documentation: https://logseq.github.io/

**Cross-reference with existing SAW documentation:**
- Obsidian Plugin patterns (Phase 7) for file-based sync
- Chrome Extension patterns (Phase 8) for OAuth flow
- RSS patterns (Phase 9) for incremental sync and rate limiting

---

*Feature research for: Third-Party Integrations (v3.1)*
*Researched: 2026-05-02*
*Confidence: MEDIUM (training knowledge; verification recommended)*
