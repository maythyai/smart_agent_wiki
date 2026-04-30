# Technology Stack — v3.0 Ecosystem Integration

**Project:** Smart Agent Wiki
**Milestone:** v3.0 Ecosystem Integration
**Researched:** 2026-04-30
**Confidence:** HIGH

---

## Executive Summary

This document specifies the technology stack additions required for the v3.0 Ecosystem Integration milestone, which adds Obsidian Plugin, Chrome Extension, and RSS Subscription capabilities. These features extend the existing v2.0 API Platform (REST + GraphQL + Webhooks) with new intake channels and user interfaces.

**Key principle:** Minimize new backend dependencies by leveraging existing v2.0 API Platform. New frontend components (Obsidian Plugin, Chrome Extension) use TypeScript with their respective platform APIs.

---

## Recommended Stack

### 1. Obsidian Plugin

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| TypeScript | 6.0.3 | Plugin language | Obsidian API is TypeScript-first; full type safety with `obsidian` package types |
| obsidian | 1.12.3 | Obsidian API | Official type definitions; provides Vault, Workspace, TFile, TFolder APIs |
| esbuild | 0.28.0 | Build tool | Obsidian plugin standard; fast bundling; supports Svelte preprocessing if needed |
| @mozilla/readability | 0.6.0 | Content extraction | Extract clean article content from HTML for web clipping feature |
| jsdom | 29.1.1 | DOM parsing | Required for Readability to parse HTML in plugin context |

**Manifest V3 Requirements (Obsidian Plugin):**
```json
{
  "id": "smart-agent-wiki",
  "name": "Smart Agent Wiki Sync",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "Bidirectional sync with Smart Agent Wiki knowledge base",
  "author": "Smart Agent Wiki Team",
  "isDesktopOnly": false
}
```

**Integration Points with Existing System:**
- Connects to v2.0 REST API (`/api/v1/*`) for sync operations
- Uses existing authentication (JWT tokens from v2.0 Team Deployment)
- Leverages existing `/api/v1/ingest` endpoint for new content
- Calls `/api/v1/query` for search within Obsidian
- Uses `/api/v1/sync` for bidirectional sync (new endpoint needed)

### 2. Chrome Extension

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| TypeScript | 6.0.3 | Extension language | Type safety across content scripts, service worker, popup |
| @webext-core/messaging | (latest) | Message passing | Type-safe wrapper over chrome.runtime.sendMessage; eliminates serialization bugs |
| @mozilla/readability | 0.6.0 | Article extraction | Firefox Reader View engine; best-in-class content extraction |
| jsdom | 29.1.1 | DOM parsing | Parse HTML for Readability in extension context |
| Chrome Storage API | (native) | Persist state | Service workers are ephemeral; chrome.storage.local persists data |
| Chrome Offscreen API | (native) | DOM access | Manifest V3 requires offscreen documents for clipboard/DOM operations |

**Manifest V3 Structure:**
```json
{
  "manifest_version": 3,
  "name": "Smart Agent Wiki Clipper",
  "version": "1.0.0",
  "permissions": [
    "storage",
    "activeTab",
    "offscreen"
  ],
  "host_permissions": [
    "http://localhost:8000/*",
    "https://your-saw-instance.com/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "action": {
    "default_popup": "popup.html"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }]
}
```

**Integration Points with Existing System:**
- Authenticates via v2.0 JWT tokens (stored in chrome.storage.local)
- Posts to `/api/v1/ingest/web` for clipping (new endpoint)
- Uses `/api/v1/tags` for auto-tagging suggestions
- Calls `/api/v1/collections` to organize clipped content

### 3. RSS Subscription

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| fastfeedparser | 0.6.0 | RSS/Atom parsing | 25x faster than feedparser; supports RSS 2.0, Atom, RDF, JSON feeds; same API as feedparser |
| APScheduler | 3.11.2 | Feed scheduling | Already in stack; interval/cron triggers for periodic feed checks |
| httpx | 0.28.1 | HTTP client | Already in stack; async HTTP for fetching feeds |
| trafilatura | 2.0.0 | Content extraction | Already in stack; extract full article content from feed entry links |

**Note on feedparser vs fastfeedparser:**
The existing stack uses `feedparser 6.0.12`. For RSS-intensive workloads, `fastfeedparser 0.6.0` provides 25x speedup with identical API. Use fastfeedparser for v3.0 RSS engine.

**Integration Points with Existing System:**
- New `FeedManager` component in Ingest Engine
- Uses existing `/api/v1/ingest` pipeline for content processing
- Stores feed subscriptions in SQLite (new `feeds` table)
- Integrates with existing scheduler (APScheduler) for periodic polling

---

## Supporting Libraries

### Python Backend (RSS Engine)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| fastfeedparser | 0.6.0 | Parse RSS/Atom feeds | Primary feed parser for RSS subscription feature |
| APScheduler | 3.11.2 | Schedule feed checks | Already in stack; use `IntervalTrigger` for hourly feed polling |
| httpx | 0.28.1 | Fetch feed URLs | Already in stack; async client for parallel feed fetching |
| trafilatura | 2.0.0 | Extract full content | Already in stack; fetch full article when feed only has summary |
| feedparser | 6.0.12 | Fallback parser | Keep as fallback for malformed feeds that fastfeedparser can't handle |

### TypeScript Frontend (Obsidian Plugin + Chrome Extension)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @mozilla/readability | 0.6.0 | Article extraction | Both Obsidian Plugin and Chrome Extension for clipping |
| jsdom | 29.1.1 | DOM parsing | Required for Readability; parse HTML into DOM |
| @webext-core/messaging | (latest) | Chrome messaging | Chrome Extension only; type-safe message passing |
| obsidian | 1.12.3 | Obsidian API | Obsidian Plugin only; Vault, Workspace, Settings APIs |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| RSS Parser | fastfeedparser | feedparser | feedparser 6.0.12 is 25x slower; fastfeedparser has identical API |
| RSS Parser | fastfeedparser | newspaper3k | newspaper3k is unmaintained; trafilatura (already in stack) is better for content extraction |
| Content Extraction | @mozilla/readability | trafilatura (JS) | trafilatura is Python-only; Readability is the JS standard |
| Content Extraction | @mozilla/readability | Postlight Parser | Postlight is deprecated; Readability is actively maintained by Mozilla |
| Chrome Messaging | @webext-core/messaging | raw chrome.runtime | Raw API is error-prone; webext-core provides type safety |
| Chrome Messaging | @webext-core/messaging | webext-bridge | webext-bridge has less active maintenance; webext-core is more comprehensive |
| Obsidian Build | esbuild | webpack | esbuild is Obsidian plugin standard; faster builds |
| Obsidian UI | Vanilla TypeScript | Svelte | Svelte adds complexity; vanilla TS is sufficient for sync plugin |

---

## Installation

### Python Backend (RSS Engine)

```bash
# RSS feed parsing (add to existing requirements)
pip install fastfeedparser==0.6.0

# APScheduler, httpx, trafilatura already in stack
# No additional installation needed
```

### Obsidian Plugin

```bash
# Create plugin project
mkdir smart-agent-wiki-plugin && cd smart-agent-wiki-plugin

# Initialize npm project
npm init -y

# Install dependencies
npm install obsidian@1.12.3
npm install @mozilla/readability@0.6.0 jsdom@29.1.1

# Install dev dependencies
npm install -D typescript@6.0.3 esbuild@0.28.0
npm install -D @types/node

# Build script (add to package.json)
# "build": "esbuild main.ts --bundle --external:obsidian --outfile=main.js --format=cjs --platform=node"
```

### Chrome Extension

```bash
# Create extension project
mkdir saw-chrome-extension && cd saw-chrome-extension

# Initialize npm project
npm init -y

# Install dependencies
npm install @mozilla/readability@0.6.0 jsdom@29.1.1
npm install @anthropic-ai/sdk@0.91.1  # Optional: for AI-powered tagging

# Install dev dependencies
npm install -D typescript@6.0.3 @types/chrome

# Build script (add to package.json)
# "build": "tsc && esbuild src/background.ts --bundle --outfile=background.js --format=iife"
```

---

## Architecture Integration

### Data Flow: Chrome Extension

```
User clicks "Clip" button
    │
    ▼
content.js extracts page HTML
    │
    ▼
background.js runs Readability on HTML
    │
    ▼
Offscreen document handles DOM parsing (if needed)
    │
    ▼
POST /api/v1/ingest/web
{
  "url": "https://...",
  "title": "Article Title",
  "content": "<cleaned HTML>",
  "textContent": "plain text",
  "source": "chrome-extension"
}
    │
    ▼
Existing Ingest Engine processes content
```

### Data Flow: RSS Subscription

```
APScheduler triggers feed check (hourly)
    │
    ▼
FeedManager.fetch_feed(url)
    │
    ▼
fastfeedparser.parse(url)
    │
    ▼
For each new entry:
    ├─ If full content in feed → Direct to Ingest Engine
    └─ If summary only → Fetch URL, trafilatura extract → Ingest Engine
    │
    ▼
POST /api/v1/ingest/rss
{
  "feed_url": "https://...",
  "entries": [...],
  "source": "rss-subscription"
}
    │
    ▼
Existing Ingest Engine processes content
```

### Data Flow: Obsidian Plugin

```
User creates/edits note in Obsidian
    │
    ▼
Plugin's onChange handler (debounced)
    │
    ▼
GET /api/v1/sync/status?path=note.md
    │
    ▼
If local newer:
    PUT /api/v1/wiki/{path}
    {
      "content": "...",
      "frontmatter": {...},
      "modified_at": "2026-04-30T..."
    }
    │
    ▼
If remote newer:
    Vault.modify(file, remote_content)
    │
    ▼
Both sides sync'd
```

---

## API Endpoints Required

### New v2.0 API Endpoints for v3.0

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/api/v1/ingest/web` | POST | Clip web page content | Chrome Extension |
| `/api/v1/ingest/rss` | POST | Batch ingest RSS entries | RSS Engine |
| `/api/v1/sync/status` | GET | Check sync status for path | Obsidian Plugin |
| `/api/v1/sync/batch` | POST | Batch sync multiple files | Obsidian Plugin |
| `/api/v1/feeds` | CRUD | Manage RSS subscriptions | CLI, Web UI |
| `/api/v1/feeds/{id}/entries` | GET | List entries for feed | Web UI |

---

## Sources

- Obsidian Developer Docs: https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin (Context7: /obsidianmd/obsidian-developer-docs)
- Chrome Extensions Manifest V3: https://developer.chrome.com/docs/extensions/develop/mv3-intro (Context7: /websites/developer_chrome_extensions)
- FastFeedParser: https://github.com/kagisearch/fastfeedparser (Context7: /kagisearch/fastfeedparser)
- Feedparser: https://github.com/kurtmckee/feedparser (Context7: /kurtmckee/feedparser)
- Mozilla Readability: https://github.com/mozilla/readability (Context7: /mozilla/readability)
- Trafilatura: https://github.com/adbar/trafilatura (Context7: /adbar/trafilatura)
- WebExt Core: https://github.com/aklinker1/webext-core (Context7: /aklinker1/webext-core)
- APScheduler: https://github.com/agronholm/apscheduler (Context7: /agronholm/apscheduler)

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Obsidian Plugin Stack | HIGH | Obsidian API is stable; TypeScript/esbuild are standard; Readability is battle-tested |
| Chrome Extension Stack | HIGH | Manifest V3 is mature; Offscreen API patterns documented; @webext-core provides type safety |
| RSS Processing Stack | HIGH | fastfeedparser is proven (Kagi search uses it); APScheduler already in stack |
| API Integration | HIGH | v2.0 API Platform already provides REST + GraphQL foundation; only minor additions needed |

---

*This document extends the existing STACK.md. The core backend stack (FastAPI, SQLite, LiteLLM, etc.) is already established in v1.1-v2.0 and not repeated here.*
