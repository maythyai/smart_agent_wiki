---
phase: 9
milestone: v3.0
name: RSS Subscription
goal: 用户可订阅 RSS/Atom Feed 并自动摄入新内容
status: planning
created: 2026-05-01
---

# Phase 9: RSS Subscription — CONTEXT

## Phase Goal

用户可订阅 RSS/Atom Feed 并自动摄入新内容到 Vault 层，实现增量同步和内容变更检测。

## Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| RSSS-01 | 订阅 RSS/Atom Feed | Table Stakes |
| RSSS-02 | 自动摄入新文章到 Vault | Table Stakes |
| RSSS-03 | 增量同步（只处理新条目） | Table Stakes |
| RSSS-04 | 配置同步频率 | Table Stakes |
| RSSS-05 | 内容变更检测（文章更新时触发重新摄入） | Differentiator |
| RSSS-06 | Feed 分类管理 | Differentiator |
| RSSS-07 | 按关键词过滤订阅 | Differentiator |

## Success Criteria

1. 用户可添加 RSS/Atom Feed 订阅
2. 新文章自动摄入到 Vault 层
3. 增量同步只处理新条目，不重复摄入
4. 用户可配置同步频率
5. 内容变更检测触发重新摄入
6. Feed 支持分类管理

## Dependencies

### External Dependencies
- **fastfeedparser 0.6.0** — RSS/Atom parsing (25x faster than feedparser)
- **APScheduler 3.11.2** — Already in stack for scheduling
- **httpx 0.28.1** — Already in stack for async HTTP
- **trafilatura 2.0.0** — Already in stack for full content extraction

### Internal Dependencies
- **v2.0 API Platform** — REST API for feed management
- **Ingest Engine** — Content processing pipeline
- **Vault Layer** — Source storage
- **Claims DB** — Feed subscription storage

## Technical Architecture

### Backend Structure

```
src/saw/
├── engines/
│   └── ingest/
│       └── feed_manager.py      # New: RSS subscription manager
├── models/
│   └── feed.py                  # New: Feed, FeedEntry models
├── api/
│   └── v1/
│       └── feeds.py             # New: Feed CRUD endpoints
└── cli/
    └── feed_commands.py         # New: feed CLI commands
```

### Database Schema

```sql
-- Feed subscriptions
CREATE TABLE feeds (
    id TEXT PRIMARY KEY,           -- UUID
    url TEXT NOT NULL UNIQUE,      -- Feed URL
    title TEXT,                    -- Feed title
    description TEXT,              -- Feed description
    category TEXT,                 -- User-defined category
    tags TEXT,                     -- JSON array of filter keywords
    poll_interval INTEGER DEFAULT 3600,  -- Seconds between polls
    last_poll_at TEXT,             -- ISO timestamp
    last_etag TEXT,                -- ETag for conditional GET
    last_modified TEXT,            -- Last-Modified for conditional GET
    active INTEGER DEFAULT 1,      -- Active subscription
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Feed entries (deduplication)
CREATE TABLE feed_entries (
    id TEXT PRIMARY KEY,           -- Content hash (GUID + title + content)
    feed_id TEXT NOT NULL,         -- Foreign key to feeds
    guid TEXT NOT NULL,            -- Entry GUID from feed
    title TEXT NOT NULL,
    url TEXT,                      -- Entry link
    content_hash TEXT,             -- SHA256 of content
    content TEXT,                  -- Full content (extracted or from feed)
    summary TEXT,                  -- Entry summary
    published_at TEXT,             -- Publication date
    updated_at TEXT,               -- Entry update date
    first_seen_at TEXT NOT NULL,   -- When we first ingested
    last_seen_at TEXT NOT NULL,    -- Last time we saw this entry
    status TEXT DEFAULT 'new',     -- new, updated, historical
    vault_uuid TEXT,               -- Reference to Vault document
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);

-- Entry deduplication index
CREATE INDEX idx_feed_entries_guid ON feed_entries(feed_id, guid);
CREATE INDEX idx_feed_entries_hash ON feed_entries(content_hash);
```

### Data Flow: RSS Ingestion

```
APScheduler triggers feed check (interval per feed)
    │
    ▼
FeedManager.poll_feed(feed_id)
    │
    ▼
HTTP GET with conditional headers (If-Modified-Since, If-None-Match)
    │
    ├─ 304 Not Modified:
    │      Skip this feed, update last_poll_at
    │
    └─ 200 OK:
        Parse with fastfeedparser
        │
        ▼
        For each entry:
            ├─ Compute entry hash (GUID + title + content_hash)
            ├─ Check if exists in feed_entries
            │
            ├─ New entry:
            │      ├─ If full content in feed: Use directly
            │      ├─ If summary only: Fetch URL, trafilatura extract
            │      └─ Ingest to Vault via existing pipeline
            │
            └─ Existing entry:
                   ├─ Compare content_hash
                   └─ If changed: Update content, mark 'updated'
        │
        ▼
        Store new ETag/Last-Modified for next request
        Update last_poll_at
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/feeds` | GET | List all feed subscriptions |
| `/api/v1/feeds` | POST | Add new feed subscription |
| `/api/v1/feeds/{id}` | GET | Get feed details |
| `/api/v1/feeds/{id}` | PUT | Update feed settings |
| `/api/v1/feeds/{id}` | DELETE | Unsubscribe from feed |
| `/api/v1/feeds/{id}/entries` | GET | List entries for feed |
| `/api/v1/feeds/{id}/poll` | POST | Trigger immediate poll |
| `/api/v1/feeds/import` | POST | Import OPML file |
| `/api/v1/feeds/export` | GET | Export as OPML |

## Critical Pitfalls to Prevent

### Pitfall 25: RSS Feed GUID Changes Breaking Deduplication

**Problem:** RSS items appear as duplicates because feed publisher changed the GUID format or domain.

**Prevention:**
- Use multiple deduplication keys: GUID + title hash + content hash
- Implement fuzzy matching for similar titles (edit distance)
- Store historical GUIDs for each source and match against all
- Normalize URLs before comparison (remove tracking parameters)

```python
def get_entry_id(entry: FeedEntry) -> str:
    """Generate stable ID from multiple signals."""
    title_hash = hashlib.md5(entry.title.encode()).hexdigest()[:8]
    content_clean = re.sub(r'\s+', ' ', strip_html(entry.description or ''))
    content_hash = hashlib.md5(content_clean.encode()).hexdigest()[:8]
    return f"{entry.guid}:{title_hash}:{content_hash}"
```

### Pitfall 26: RSS Feed Parsing Encoding Issues

**Problem:** Text appears garbled (Mojibake) - accented characters broken, quotes replaced with question marks.

**Prevention:**
- Use robust parsing library (fastfeedparser handles encoding detection)
- Normalize all content to UTF-8 after parsing
- Log encoding warnings for manual review
- Fallback to HTTP Content-Type header encoding if XML parsing fails

```python
import fastfeedparser

feed = fastfeedparser.parse(url, request_headers={'Accept': 'application/xml'})

if feed.bozo:  # bozo bit indicates parsing issue
    logger.warning(f"Feed {url} has encoding issues: {feed.bozo_exception}")
```

### Pitfall 27: RSS Aggressive Polling Leading to IP Blocks

**Problem:** Feed sources block your IP or return 429 errors; feeds stop updating.

**Prevention:**
- Implement adaptive polling intervals based on feed update frequency
- Use conditional GET with `If-Modified-Since` and `If-None-Match` headers
- Respect `ttl` and `sy:updatePeriod` elements in feeds
- Exponential backoff for failing feeds
- Stagger polling across time windows, not all at once

```python
headers = {}
if last_modified:
    headers['If-Modified-Since'] = last_modified
if etag:
    headers['If-None-Match'] = etag

response = httpx.get(url, headers=headers)
if response.status_code == 304:
    # Not modified, skip parsing
    return None
```

## Key Design Decisions

### 1. fastfeedparser over feedparser

**Decision:** Use `fastfeedparser 0.6.0` instead of `feedparser 6.0.12`.

**Rationale:** 25x faster with identical API. Critical for polling hundreds of feeds efficiently. Same parsing logic, just optimized.

**Implementation:**
- Install fastfeedparser alongside feedparser (fallback for malformed feeds)
- Use fastfeedparser for all normal parsing
- Fall back to feedparser if fastfeedparser fails

### 2. Adaptive Polling Intervals

**Decision:** Adjust poll interval based on observed feed update frequency.

**Rationale:** Different feeds have different update patterns. News sites update hourly, blogs weekly. Adaptive polling respects server resources and avoids IP blocks.

**Implementation:**
- Start with default interval (1 hour)
- Track actual update times for each feed
- Calculate median update interval
- Set poll_interval = median * 0.75 (poll slightly more often)
- Minimum: 15 minutes, Maximum: 24 hours

### 3. Content Extraction Strategy

**Decision:** If feed only has summary, fetch full article URL and extract with trafilatura.

**Rationale:** Many feeds only provide short summaries. Full content extraction provides better knowledge base quality. trafilatura is already in stack.

**Implementation:**
- Check if `entry.content` is present
- If not, fetch `entry.link` with httpx
- Extract full content with trafilatura
- Store both summary and full content

### 4. Change Detection via Content Hash

**Decision:** Track content hash for each entry. If hash changes, mark entry as 'updated' and re-ingest.

**Rationale:** Articles are sometimes updated after publication. Users want to know when content changes.

**Implementation:**
- Compute SHA256 of normalized content
- Compare on each poll
- If different: update content, set status='updated', trigger re-ingestion
- Keep version history in Vault

## Implementation Patterns

### FeedManager Class

```python
from fastfeedparser import parse as parse_feed
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class FeedManager:
    def __init__(self, db_path: str, scheduler: AsyncIOScheduler):
        self.db = sqlite3.connect(db_path)
        self.scheduler = scheduler
        self.http_client = httpx.AsyncClient()

    async def add_feed(self, url: str, category: str = None, poll_interval: int = 3600) -> str:
        """Subscribe to a new feed."""
        # Parse feed to get title
        feed_data = parse_feed(url)
        
        # Insert into database
        feed_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO feeds (id, url, title, description, category, poll_interval) VALUES (?, ?, ?, ?, ?, ?)",
            (feed_id, url, feed_data.feed.title, feed_data.feed.description, category, poll_interval)
        )
        
        # Schedule polling job
        self.scheduler.add_job(
            self.poll_feed,
            'interval',
            seconds=poll_interval,
            id=f"feed_{feed_id}",
            args=[feed_id]
        )
        
        return feed_id

    async def poll_feed(self, feed_id: str) -> List[str]:
        """Poll a feed for new entries."""
        # Get feed info
        feed = self.db.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
        
        # Conditional GET
        headers = {}
        if feed['last_etag']:
            headers['If-None-Match'] = feed['last_etag']
        if feed['last_modified']:
            headers['If-Modified-Since'] = feed['last_modified']
        
        response = await self.http_client.get(feed['url'], headers=headers)
        
        if response.status_code == 304:
            # Not modified
            return []
        
        # Parse feed
        feed_data = parse_feed(response.text)
        
        # Process entries
        new_entry_ids = []
        for entry in feed_data.entries:
            entry_id = await self.process_entry(feed_id, entry)
            if entry_id:
                new_entry_ids.append(entry_id)
        
        # Update feed metadata
        self.db.execute(
            "UPDATE feeds SET last_poll_at = ?, last_etag = ?, last_modified = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), response.headers.get('ETag'), response.headers.get('Last-Modified'), feed_id)
        )
        
        return new_entry_ids

    async def process_entry(self, feed_id: str, entry: FeedEntry) -> Optional[str]:
        """Process a single entry, ingest if new or updated."""
        # Compute entry hash
        entry_hash = self.compute_entry_hash(entry)
        
        # Check if exists
        existing = self.db.execute(
            "SELECT * FROM feed_entries WHERE feed_id = ? AND guid = ?",
            (feed_id, entry.id)
        ).fetchone()
        
        if existing:
            # Check if content changed
            if existing['content_hash'] != self.compute_content_hash(entry):
                # Content updated
                await self.update_entry(existing['id'], entry)
                return existing['id']
            return None
        
        # New entry
        content = await self.extract_content(entry)
        vault_uuid = await self.ingest_to_vault(entry, content)
        
        # Insert entry record
        entry_id = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO feed_entries 
               (id, feed_id, guid, title, url, content, summary, content_hash, vault_uuid, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, feed_id, entry.id, entry.title, entry.link, content, entry.summary, 
             self.compute_content_hash(entry), vault_uuid, entry.published)
        )
        
        return entry_id

    async def extract_content(self, entry: FeedEntry) -> str:
        """Extract full content from entry or fetch from URL."""
        if entry.content:
            return entry.content
        
        # Fetch from URL
        response = await self.http_client.get(entry.link)
        content = trafilatura.extract(response.text)
        return content or entry.summary
```

### CLI Commands

```python
# saw feed add <url>
@saw_cli.command("feed-add")
def feed_add(url: str, category: str = None, interval: int = 3600):
    """Subscribe to an RSS/Atom feed."""
    feed_manager = FeedManager.get_instance()
    feed_id = await feed_manager.add_feed(url, category, interval)
    click.echo(f"Subscribed to feed: {feed_id}")

# saw feed list
@saw_cli.command("feed-list")
def feed_list():
    """List all feed subscriptions."""
    feeds = db.execute("SELECT id, url, title, category FROM feeds WHERE active = 1").fetchall()
    for feed in feeds:
        click.echo(f"{feed['id'][:8]}  {feed['title'] or feed['url']}  [{feed['category'] or 'default'}]")

# saw feed poll <feed_id>
@saw_cli.command("feed-poll")
def feed_poll(feed_id: str):
    """Manually poll a feed for new entries."""
    feed_manager = FeedManager.get_instance()
    new_entries = await feed_manager.poll_feed(feed_id)
    click.echo(f"Found {len(new_entries)} new entries")
```

## Test Strategy

### Unit Tests
- Feed URL parsing and validation
- Entry hash computation
- Content extraction
- Deduplication logic
- Adaptive interval calculation

### Integration Tests
- Full poll cycle: fetch -> parse -> dedupe -> ingest
- OPML import/export
- Conditional GET handling
- Content update detection

### Manual Verification
- Subscribe to several real RSS feeds
- Verify new entries appear in Vault
- Verify duplicates are not created
- Verify content updates are detected
- Verify polling respects rate limits

## File Deliverables

| File | Purpose |
|------|---------|
| `.planning/phases/09-rss-subscription/PLAN-01.md` | Data models and database schema |
| `.planning/phases/09-rss-subscription/PLAN-02.md` | FeedManager implementation |
| `.planning/phases/09-rss-subscription/PLAN-03.md` | API endpoints |
| `.planning/phases/09-rss-subscription/PLAN-04.md` | CLI commands and scheduler |
| `.planning/phases/09-rss-subscription/VERIFICATION.md` | Test checklist |
| `.planning/phases/09-rss-subscription/SUMMARY.md` | Phase summary |

## Timeline Estimate

| Plan | Estimated Duration |
|------|-------------------|
| PLAN-01: Data Models | 0.5 day |
| PLAN-02: FeedManager | 1 day |
| PLAN-03: API Endpoints | 0.5 day |
| PLAN-04: CLI & Scheduler | 0.5 day |
| Integration & Testing | 0.5 day |
| **Total** | **3 days** |

## Notes

- **Phase 9 is NOT marked with UI hint** — Pure Python backend, no UI design needed
- RSS builds on existing Ingest Engine patterns
- APScheduler is already in stack from v2.0
- fastfeedparser needs to be added to requirements
- All backend changes, no frontend changes needed

---
*Context created: 2026-05-01*
*Phase: 9 — RSS Subscription*
*Milestone: v3.0 Ecosystem Integration*