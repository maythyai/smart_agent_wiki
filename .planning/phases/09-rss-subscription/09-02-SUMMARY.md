---
phase: 09-rss-subscription
plan: 02
subsystem: engines, ingest
tags: [feed-manager, polling, deduplication, ingestion]
requires: [09-01]
provides: [FeedManager, PollResult, FeedManagerError]
affects: []
---

# Phase 09 Plan 02: FeedManager Implementation Summary

## One-liner
RSS/Atom feed manager with conditional GET, multi-key deduplication, content extraction, and ingestion integration.

## Key Decisions

1. **fastfeedparser over feedparser** - 25x faster parsing with same API, critical for polling hundreds of feeds efficiently

2. **Conditional GET** - Use ETag and Last-Modified headers to skip unchanged feeds (304 response), reducing bandwidth and server load

3. **Content extraction strategy** - If feed only has summary (<500 chars), fetch full article URL and extract with trafilatura

4. **Adaptive polling** - Calculate poll interval from median update frequency * 0.75, bounded to 900-86400 seconds

5. **Keyword filtering before ingestion** - Filter entries by tags early in the pipeline to avoid unnecessary processing

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `src/saw/engines/ingest/feed_manager.py` | FeedManager implementation | ~520 |
| `tests/unit/test_feed_manager.py` | Unit tests (19 tests) | ~380 |
| `pyproject.toml` | Added dependencies | +2 |

## Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| fastfeedparser | 0.6.0 | RSS/Atom parsing (25x faster than feedparser) |
| apscheduler | 3.11.2 | Background job scheduling |

## Test Results

```
19 passed in 3.61s
```

### Coverage

- **Core functionality (4 tests)**: add_feed, parse_feed, URL validation, bozo handling
- **Conditional GET (5 tests)**: If-Modified-Since, If-None-Match, 304 handling, ETag storage
- **Entry processing (5 tests)**: New entry ingest, duplicate skip, update detect, content extract
- **Adaptive polling (5 tests)**: Interval calculation, bounds, keyword filter

## Pitfalls Addressed

| Pitfall | Prevention | Status |
|---------|------------|--------|
| 26: Encoding issues | fastfeedparser handles detection | Verified |
| 27: Aggressive polling | Conditional GET, adaptive intervals | Verified |

## Integration Points

- `FeedManager._ingest_entry()` → `IngestPipeline.ingest()`
- `FeedManager.db_session` → SQLAlchemy Session
- `FeedManager.http_client` → httpx.AsyncClient

## Threat Model Coverage

| Threat | Mitigation | Status |
|--------|------------|--------|
| T-09-04: Tampering (_extract_content) | HTML sanitization in trafilatura | Implemented |
| T-09-05: DoS (poll_feed) | 30s timeout on HTTP | Implemented |
| T-09-07: Spoofing (Feed.url) | URL scheme validation (http/https only) | Implemented |

## Commits

1. `dccc98f`: feat(09-02): implement FeedManager for RSS polling and ingestion

## Next Steps

Plan 09-03 will create REST API endpoints for feed management:
- CRUD operations (list, create, update, delete)
- Entry listing with pagination
- Manual poll trigger
- OPML import/export

---
*Completed: 2026-05-01*
