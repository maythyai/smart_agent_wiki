---
phase: 09-rss-subscription
plan: 03
subsystem: api
tags: [rest-api, crud, opml, endpoints]
requires: [09-02]
provides: [feeds_router]
affects: []
---

# Phase 09 Plan 03: API Endpoints Summary

## One-liner
REST API endpoints for feed management with CRUD operations, entry listing, manual poll trigger, and OPML import/export.

## Key Decisions

1. **Soft delete for feeds** - Sets `active=False` to preserve entry history rather than hard delete

2. **Pydantic model validation** - URL format and poll_interval bounds validated at request parsing stage

3. **OPML grouping by category** - Export groups feeds by category for better organization

4. **Pagination for entries** - Default limit of 20 entries with offset support

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `src/saw/api/feeds.py` | REST API endpoints | ~450 |
| `tests/unit/test_api_feeds.py` | Unit tests (22 tests) | ~270 |

## Test Results

```
22 passed in 3.49s
```

### Coverage

- **Pydantic models (6 tests)**: URL validation, poll_interval bounds, response serialization
- **Router configuration (11 tests)**: Prefix, tags, all endpoint paths
- **OPML parsing (3 tests)**: Simple, multiple feeds, categories
- **OPML export (2 tests)**: Structure generation, category grouping

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/v1/feeds | List all subscriptions |
| POST | /api/v1/feeds | Create subscription |
| GET | /api/v1/feeds/{id} | Get feed details |
| PUT | /api/v1/feeds/{id} | Update settings |
| DELETE | /api/v1/feeds/{id} | Soft delete |
| GET | /api/v1/feeds/{id}/entries | List entries |
| POST | /api/v1/feeds/{id}/poll | Trigger poll |
| POST | /api/v1/feeds/import | Import OPML |
| GET | /api/v1/feeds/export | Export OPML |

## Threat Model Coverage

| Threat | Mitigation | Status |
|--------|------------|--------|
| T-09-08: Spoofing (POST /feeds) | API key auth (via DI) | Implemented |
| T-09-09: Tampering (PUT /feeds) | Pydantic validation | Implemented |
| T-09-10: DoS (GET /feeds) | Pagination limits | Implemented |
| T-09-11: Info Disclosure | User-scoped queries | Implemented |

## Commits

1. `4a78e88`: feat(09-03): add REST API endpoints for feed management

## Next Steps

Plan 09-04 will implement:
- CLI commands for feed management (Typer)
- APScheduler integration for automatic polling
- Staggered polling to avoid burst requests

---
*Completed: 2026-05-01*
