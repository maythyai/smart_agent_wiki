---
phase: 12-notion-connector
plan: 01
subsystem: connector
tags: [notion, oauth, sync, database-selection]
dependencies:
  requires: [10-connector-framework, 11-sync-engine]
  provides: [notion-connector-core, notion-oauth, notion-database-selection]
tech_stack:
  added: ["notion-client>=2.0.0"]
  patterns: [connector-protocol, oauth-flow, cursor-pagination]
key_files:
  created:
    - src/saw/connectors/notion/__init__.py
    - src/saw/connectors/notion/models.py
    - src/saw/connectors/notion/connector.py
    - src/saw/connectors/notion/oauth.py
    - src/saw/connectors/notion/database_selector.py
    - src/saw/db/notion_models.py
    - src/saw/api/notion.py
    - tests/unit/test_notion_connector/test_notion_models.py
    - tests/unit/test_notion_connector/test_notion_db_models.py
    - tests/unit/test_notion_connector/test_notion_connector.py
    - tests/unit/test_notion_connector/test_database_selector.py
    - tests/unit/test_notion_connector/test_notion_api.py
  modified:
    - src/saw/db/__init__.py
    - pyproject.toml
metrics:
  duration: "15 minutes"
  completed: "2026-05-02"
  test_coverage: "57 tests passing"
---

# Phase 12 Plan 01: Notion Connector Core and OAuth Summary

## One-liner

Notion connector implementing UnifiedConnectorInterface with OAuth flow, database selection, and sync cursor persistence.

## Completed Tasks

### Task 1: Create Notion models and database schema

**Commit:** `8095134`

- Added Pydantic models for Notion API (NotionPage, NotionDatabase, NotionProperty)
- Implemented discriminated union for 17 Notion property types
- Added SQLAlchemy models for sync state (NotionSyncCursorModel, NotionDatabaseConfigModel)
- Registered models in database package

**Files:** 7 files created, 1028 lines added

### Task 2: Implement NotionConnector core

**Commit:** `9494fc9`

- Implemented NotionConnector class with UnifiedConnectorInterface
- Added NotionOAuthHandler for workspace connection
- Implemented get_items() with database querying and pagination
- Implemented put_item() for creating/updating pages
- Added sync cursor persistence for resume capability
- Rate limiting via notion-client SDK (3 req/s)

**Files:** 3 files created, 982 lines added

### Task 3: Implement database selection and sync cursor persistence

**Commit:** `ab2140f`

- Added DatabaseSelector for database selection management
- Implemented sync cursor persistence and resume logic
- Added FastAPI endpoints for database selection API
- Implemented property mapping configuration

**Files:** 4 files created, 826 lines added

## Key Decisions

1. **notion-client SDK**: Used official Notion SDK which handles rate limiting (3 req/s) automatically
2. **Discriminated union**: Used Pydantic's discriminated union for type-safe property handling
3. **Cursor persistence**: Sync cursors stored in database for incremental sync resume
4. **Database selection**: User can select specific databases for sync with per-database settings

## Deviations from Plan

None - plan executed exactly as written.

## Test Results

```
57 tests passed in 1.57s
```

All unit tests pass including:
- Notion API model tests (28 tests)
- Database model tests (7 tests)
- Connector implementation tests (10 tests)
- Database selector tests (8 tests)
- API endpoint tests (4 tests)

## Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| NOTI-01 | Complete | OAuth workspace connection with workspace_id capture |
| NOTI-02 | Complete | Database selection persistence |
| NOTI-09 | Complete | Rate limiting via notion-client SDK |
| NOTI-10 | Complete | Sync cursor persistence for resume |

## Next Steps

Continue to Plan 12-02: Property mapping and block transformation.
