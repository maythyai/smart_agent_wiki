---
phase: 09-rss-subscription
plan: 01
subsystem: domain, db
tags: [data-models, deduplication, sqlalchemy]
requires: []
provides: [Feed, FeedEntry, DeduplicationService, EntryStatus]
affects: []
---

# Phase 09 Plan 01: Data Models and Database Schema Summary

## One-liner
SQLAlchemy models for RSS feed subscriptions and entries with multi-key deduplication support (GUID + title hash + content hash).

## Key Decisions

1. **Multi-key deduplication** - Use composite key (GUID:title_hash:content_hash) to prevent duplicates when feed publishers change GUID formats (Pitfall 25)

2. **URL normalization** - Strip tracking parameters (utm_*, ref, fbclid, etc.) before comparison to improve duplicate detection

3. **Fuzzy title matching** - Use Levenshtein distance via SequenceMatcher with 0.9 threshold for detecting similar articles

4. **Poll interval bounds** - Enforce 900s (15 min) to 86400s (24 hours) to prevent aggressive polling (Pitfall 27)

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `src/saw/domain/feed.py` | Domain entities: EntryHash, DeduplicationKey, FeedConfig, DeduplicationService | ~266 |
| `src/saw/db/feed_models.py` | SQLAlchemy models: Feed, FeedEntry | ~90 |
| `tests/unit/test_feed_models.py` | Unit tests (36 tests) | ~430 |

## Test Results

```
36 passed in 0.44s
```

### Coverage

- EntryHash: SHA256 computation with HTML stripping, whitespace normalization
- DeduplicationKey: Composite key generation from GUID + title + content
- FeedConfig: URL validation, poll_interval bounds checking
- EntryStatus: Enum values (new, updated, historical)
- URL normalization: Tracking parameter removal
- Title similarity: Levenshtein distance calculation
- DeduplicationService: GUID, content hash, and fuzzy title matching
- Feed model: Field definitions, relationships
- FeedEntry model: Status defaults, indexes, vault reference

## Pitfalls Addressed

| Pitfall | Prevention | Status |
|---------|------------|--------|
| 25: RSS GUID changes | Multi-key deduplication (GUID + title + content) | Verified |
| 27: Aggressive polling | Poll interval bounds (900-86400) | Verified |

## Threat Model Coverage

| Threat | Mitigation | Status |
|--------|------------|--------|
| T-09-01: Tampering (FeedEntry.content) | Content validation, HTML sanitization in EntryHash | Implemented |
| T-09-02: Information Disclosure (Feed.url) | Accepted - URLs stored in plaintext | Documented |
| T-09-03: DoS (poll_interval) | Enforce minimum 900s interval | Implemented |

## Commits

1. `d718d61`: feat(09-01): add domain entities for feed configuration and deduplication
2. `946765e`: feat(09-01): add SQLAlchemy models for Feed and FeedEntry

## Next Steps

Plan 09-02 will implement FeedManager that uses these models to:
- Parse RSS/Atom feeds with fastfeedparser
- Implement conditional GET (ETag/Last-Modified)
- Process entries with deduplication
- Ingest content to Vault

---
*Completed: 2026-05-01*
