---
phase: 8
milestone: v3.0
name: Chrome Extension
goal: 用户可一键剪藏网页内容到 SAW Vault
status: planning
created: 2026-05-01
---

# Phase 8: Chrome Extension — CONTEXT

## Phase Goal

用户可一键剪藏网页内容到 SAW Vault，自动提取正文（去除导航/广告），支持选择剪藏范围和添加标签备注。

## Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| CHRE-01 | 一键剪藏当前页面到 SAW Vault | Table Stakes |
| CHRE-02 | 自动提取正文（去除导航/广告） | Table Stakes |
| CHRE-03 | 支持选择剪藏范围（全文/选中） | Table Stakes |
| CHRE-04 | 添加标签和备注 | Table Stakes |
| CHRE-05 | Manifest V3 合规 | Table Stakes |
| CHRE-06 | 智能分类建议（基于内容分析） | Differentiator |
| CHRE-07 | 批量剪藏多个标签页 | Differentiator |
| CHRE-08 | 与 Obsidian 插件协同（剪藏后自动同步） | Differentiator |

## Success Criteria

1. 用户点击扩展图标可剪藏当前页面到 SAW Vault
2. 自动提取正文内容（去除导航、广告）
3. 用户可选择剪藏范围（全文/选中内容）
4. 用户可添加标签和备注
5. Manifest V3 合规，可发布到 Chrome Web Store
6. 智能分类建议基于内容分析

## Dependencies

### External Dependencies
- **Chrome Extensions API (Manifest V3)** — Service workers, storage, tabs, offscreen
- **TypeScript 6.0.3** — Extension language
- **@mozilla/readability 0.6.0** — Article extraction
- **@webext-core/messaging** — Type-safe message passing
- **jsdom 29.1.1** — DOM parsing for Readability

### Internal Dependencies
- **v2.0 API Platform** — REST API endpoints for ingestion
- **Ingest Engine** — Content processing pipeline
- **Vault Layer** — Metadata storage

## Technical Architecture

### Extension Structure

```
saw-chrome-extension/
├── manifest.json           # Manifest V3 configuration
├── background.js           # Service worker (bundled)
├── content.js              # Content script (bundled)
├── popup/
│   ├── popup.html          # Popup UI
│   └── popup.js            # Popup logic (bundled)
├── offscreen/
│   ├── offscreen.html      # Offscreen document for DOM ops
│   └── offscreen.js        # Offscreen logic
├── src/
│   ├── background/
│   │   ├── index.ts        # Service worker entry
│   │   ├── clipper.ts      # Clipping logic
│   │   ├── storage.ts      # Chrome storage wrapper
│   │   └── messaging.ts    # Message handlers
│   ├── content/
│   │   ├── index.ts        # Content script entry
│   │   ├── extractor.ts    # Page content extraction
│   │   └── selection.ts    # Selection handling
│   ├── popup/
│   │   ├── index.ts        # Popup entry
│   │   ├── preview.ts      # Content preview
│   │   └── tags.ts         # Tag input handling
│   ├── offscreen/
│   │   └── readability.ts  # Readability.js wrapper
│   ├── api/
│   │   └── client.ts       # SAW REST API client
│   └── types.ts            # Shared types
├── styles/
│   └── popup.css           # Popup styles
├── icons/
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── package.json
├── tsconfig.json
└── esbuild.config.mjs
```

### Data Flow: Web Clipping

```
User clicks extension icon
    │
    ▼
Popup opens, content script extracts page HTML
    │
    ▼
Background service worker receives message
    │
    ├─ If full page:
    │      Readability.parse(html) via offscreen document
    │      │
    │      ▼
    │      Extract: title, content, textContent, excerpt
    │
    ├─ If selection:
    │      Extract selected text/range from content script
    │      │
    │      ▼
    │      Minimal Readability for context
    │
    ▼
User reviews in popup, adds tags/notes
    │
    ▼
POST /api/v1/ingest/web
{
  "url": "https://...",
  "title": "Article Title",
  "content": "<cleaned HTML>",
  "textContent": "plain text",
  "tags": ["tag1", "tag2"],
  "notes": "User notes",
  "source": "chrome-extension"
}
    │
    ▼
SAW Ingest Engine processes content
    │
    ▼
Success notification to user
```

### Manifest V3 Structure

```json
{
  "manifest_version": 3,
  "name": "Smart Agent Wiki Clipper",
  "version": "1.0.0",
  "description": "Clip web pages to Smart Agent Wiki knowledge base",
  "permissions": [
    "storage",
    "activeTab",
    "offscreen",
    "tabs"
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
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "run_at": "document_idle"
  }],
  "commands": {
    "clip-page": {
      "suggested_key": {
        "default": "Alt+S"
      },
      "description": "Clip current page to SAW"
    }
  }
}
```

## Critical Pitfalls to Prevent

### Pitfall 21: Manifest V3 Remote Code Prohibition

**Problem:** Extension rejected by Chrome Web Store if it loads external JavaScript.

**Prevention:**
- Bundle ALL JavaScript with the extension package
- No CDN scripts, no dynamically fetched code execution
- Use web APIs directly instead of loading libraries from CDN
- Use `declarativeNetRequest` instead of dynamic `webRequest` blocking

### Pitfall 22: Service Worker Lifecycle Breaks State

**Problem:** Background state (variables, connections, timers) disappears when service worker terminates after ~30 seconds of inactivity.

**Prevention:**
- Persist ALL state to `chrome.storage.local` or `chrome.storage.session`
- Use IndexedDB for complex data structures
- Re-establish connections on service worker wake (`chrome.runtime.onStartup`)
- Use `chrome.alarms` for scheduled tasks instead of `setInterval`

### Pitfall 23: Content Script Isolation Blocking

**Problem:** Content script cannot access page JavaScript variables or functions directly.

**Prevention:**
- Use `window.postMessage` for page-to-content-script communication
- Inject script tags into page DOM for direct page access (but loses extension APIs)
- Use custom events with `CustomEvent` for structured data

### Pitfall 24: Chrome Storage Sync Quota Exceeded

**Problem:** `chrome.storage.sync.set()` silently fails or throws quota exceeded errors.

**Limits:**
- 100KB total (QUOTA_BYTES)
- 8KB per item (QUOTA_BYTES_PER_ITEM)
- 120 writes per hour

**Prevention:**
- Use `storage.local` for large data (10MB default, unlimited with permission)
- Only use `storage.sync` for settings that need cross-device sync
- Check `chrome.runtime.lastError` after storage operations

### Pitfall 29: CORS Blocking to Local Server

**Problem:** Chrome extension cannot communicate with local SAW API server due to CORS policy.

**Prevention:**
- Add extension ID to CORS allowed origins in FastAPI server
- Use `chrome.runtime.sendMessage` to background script for API calls (bypasses CORS from content script)
- Configure FastAPI CORS middleware:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://YOUR_EXTENSION_ID",
        "http://localhost:*",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Key Design Decisions

### 1. Offscreen Document for Readability

**Decision:** Use Chrome's Offscreen API to run Readability.js in a proper DOM environment.

**Rationale:** Manifest V3 service workers don't have DOM access. Readability requires a DOM to parse HTML. Offscreen documents provide a sanctioned way to access DOM APIs.

**Implementation:**
- Create `offscreen/offscreen.html` and `offscreen.js`
- Background sends HTML to offscreen document
- Offscreen document runs Readability, returns parsed content
- Use `chrome.offscreen.createDocument()` API

### 2. Message Passing Architecture

**Decision:** Use `@webext-core/messaging` for type-safe communication between content script, background, and popup.

**Rationale:** Raw `chrome.runtime.sendMessage` is error-prone. `@webext-core/messaging` provides TypeScript type safety and automatic serialization.

**Implementation:**
- Define typed message contracts
- Background registers handlers
- Content script and popup send typed messages

### 3. Smart Tagging via SAW API

**Decision:** Tag suggestions generated by calling `/api/v1/tags/suggest` endpoint (new endpoint needed).

**Rationale:** SAW already has embedding model and classification capability. Leverage existing backend intelligence rather than implementing in extension.

**Implementation:**
- Send extracted content to SAW API for tag suggestion
- Display top 5 suggested tags in popup
- User can accept/reject/add custom tags

### 4. Batch Clipping via Tabs API

**Decision:** "Clip all tabs" feature uses `chrome.tabs.query()` to iterate all open tabs.

**Rationale:** Common use case for research sessions. Chrome Tab Groups API for organizing clipped tabs.

**Implementation:**
- Context menu item "Clip all tabs"
- Show progress indicator
- Collect all results, batch POST to API

## Implementation Patterns

### Service Worker Entry Point

```typescript
// src/background/index.ts
import { setupMessaging } from './messaging';
import { Clipper } from './clipper';
import { StorageManager } from './storage';

export default class BackgroundWorker {
  private clipper: Clipper;
  private storage: StorageManager;

  constructor() {
    this.storage = new StorageManager();
    this.clipper = new Clipper(this.storage);
    this.init();
  }

  async init() {
    // Restore state from storage on wake
    await this.storage.restoreState();

    // Setup message handlers
    setupMessaging({
      'clip-page': (data) => this.clipper.clipPage(data),
      'clip-selection': (data) => this.clipper.clipSelection(data),
      'get-history': () => this.storage.getClipHistory(),
    });

    // Listen for alarm wake-ups
    chrome.alarms.onAlarm.addListener((alarm) => {
      if (alarm.name === 'sync-check') {
        this.checkPendingSync();
      }
    });
  }
}

// Initialize on load
new BackgroundWorker();
```

### Content Script Pattern

```typescript
// src/content/index.ts
import { extractPageContent, extractSelection } from './extractor';

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'extract-page') {
    const content = extractPageContent();
    sendResponse(content);
  } else if (message.type === 'extract-selection') {
    const selection = extractSelection();
    sendResponse(selection);
  }
  return true; // Keep channel open for async response
});

// Notify background that content script is ready
chrome.runtime.sendMessage({ type: 'content-ready' });
```

### Offscreen Document Pattern

```typescript
// background sends HTML to offscreen
async function parseWithReadability(html: string): Promise<ParsedContent> {
  // Check if offscreen document exists
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
  });

  if (existingContexts.length === 0) {
    await chrome.offscreen.createDocument({
      url: 'offscreen/offscreen.html',
      reasons: [chrome.offscreen.Reason.DOM_PARSER],
      justification: 'Parse HTML with Readability.js',
    });
  }

  // Send message to offscreen document
  const response = await chrome.runtime.sendMessage({
    type: 'parse-readability',
    html,
  });

  return response;
}

// offscreen/offscreen.js
import Readability from '@mozilla/readability';

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'parse-readability') {
    const doc = new JSDOM(message.html, { url: message.url });
    const reader = new Readability(doc.window.document);
    const article = reader.parse();
    sendResponse(article);
  }
});
```

## UI Components

### 1. Popup Interface
- Page title (editable)
- URL display
- Content preview (truncated)
- Selection indicator (if selection clipped)
- Tag input with suggestions
- Notes textarea
- Clip/Cancel buttons
- Connection status indicator

### 2. Context Menu
- "Clip to SAW" (page)
- "Clip selection to SAW" (selected text)
- "Clip all tabs" (browser action context)

### 3. Notifications
- Success notification after clip
- Error notification on failure
- Progress indicator for batch clips

## Test Strategy

### Unit Tests
- Content extraction logic
- Readability wrapper
- Message passing contracts
- Storage wrapper operations

### Integration Tests
- Full clip flow: popup -> content script -> background -> API
- Selection extraction
- Batch clipping
- Offline queue and retry

### Manual Verification
- Install extension in Chrome
- Connect to local SAW instance
- Clip various page types (articles, blogs, PDFs, videos)
- Verify content extraction quality
- Verify tags and notes saved correctly

## API Endpoints Needed

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/ingest/web` | POST | Clip web page content |
| `/api/v1/tags/suggest` | POST | Suggest tags for content |
| `/api/v1/auth/verify` | GET | Verify API key validity |

## File Deliverables

| File | Purpose |
|------|---------|
| `.planning/phases/08-chrome-extension/PLAN-01.md` | Extension core (manifest, service worker) |
| `.planning/phases/08-chrome-extension/PLAN-02.md` | Content extraction and offscreen |
| `.planning/phases/08-chrome-extension/PLAN-03.md` | Popup UI and tagging |
| `.planning/phases/08-chrome-extension/PLAN-04.md` | API client and commands |
| `.planning/phases/08-chrome-extension/VERIFICATION.md` | Test checklist |
| `.planning/phases/08-chrome-extension/SUMMARY.md` | Phase summary |

## Timeline Estimate

| Plan | Estimated Duration |
|------|-------------------|
| PLAN-01: Extension Core | 1 day |
| PLAN-02: Content Extraction | 1 day |
| PLAN-03: Popup UI | 0.5 day |
| PLAN-04: API & Commands | 0.5 day |
| Integration & Testing | 0.5 day |
| **Total** | **3.5 days** |

## Notes

- **Phase 8 is marked with UI hint** — requires popup UI design
- Chrome Extension development is TypeScript-only — no Python backend changes needed except new API endpoints
- Manifest V3 compliance is mandatory for Chrome Web Store publication
- Extension ID will be generated on first load; must be added to SAW CORS settings

---
*Context created: 2026-05-01*
*Phase: 8 — Chrome Extension*
*Milestone: v3.0 Ecosystem Integration*