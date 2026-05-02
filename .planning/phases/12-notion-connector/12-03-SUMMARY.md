---
phase: 12-notion-connector
plan: 03
subsystem: connector
tags: [notion, sync, polling, conflict-resolution, bidirectional]
dependencies:
  requires: [12-01, 12-02]
  provides: [notion-sync-manager, notion-conflict-handler, sync-api, sync-cli]
tech_stack:
  added: []
  patterns: [bidirectional-sync, conflict-resolution, scheduled-polling]
key_files:
  created:
    - src/saw/connectors/notion/conflict_handler.py
    - src/saw/connectors/notion/sync_manager.py
    - src/saw/api/notion_sync.py
    - src/saw/cli/notion.py
    - tests/unit/test_notion_sync/test_notion_conflict.py
    - tests/unit/test_notion_sync/test_notion_sync.py
    - tests/unit/test_notion_sync/test_notion_sync_api.py
  modified: []
metrics:
  duration: "15 minutes"
  completed: "2026-05-02"
  test_coverage: "32 tests passing"
---

# Phase 12 Plan 03: Bidirectional Sync and Polling Summary

## One-liner

Bidirectional sync between SAW and Notion with conflict detection, configurable polling, and API/CLI control.

## Completed Tasks

### Task 1: Implement NotionConflictHandler

**Commit:** `6a345f0`

- Added NotionConflictHandler for concurrent edit detection (NOTI-06)
- Implemented LAST_MODIFIED_WINS, PLATFORM_WINS, SAW_WINS strategies
- Added manual resolution for human review
- Conflict logging with both versions preserved
- UTC timezone normalization for timestamp comparison

**Files:** 2 files created, 647 lines added

### Task 2: Implement NotionSyncManager

**Commit:** `400e4a7`

- Added NotionSyncManager for orchestration (NOTI-05)
- Added NotionSyncConfig with configurable polling (NOTI-08)
- Implemented sync_pull, sync_push, bidirectional sync
- Start/stop polling via APScheduler
- Conflict detection integration
- Backpressure handling

**Files:** 2 files created, 568 lines added

### Task 3: Implement sync API endpoints and CLI commands

**Commit:** `386ab02`

- Added FastAPI endpoints for sync control (NOTI-05)
- Added Typer CLI commands for sync operations
- Implemented poll start/stop/status commands
- Added conflict listing and resolution endpoints
- Support manual sync triggering via API/CLI

**Files:** 3 files created, 717 lines added

## Key Decisions

1. **Conflict resolution**: LAST_MODIFIED_WINS as default strategy
2. **Polling interval**: Default 1 hour (3600 seconds), minimum 60 seconds
3. **Sync manager**: Delegates to SyncEngine for actual sync operations
4. **Backpressure**: Handled by sync_engine, sync manager respects pause state

## Deviations from Plan

None - plan executed exactly as written.

## Test Results

```
32 tests passed in 1.40s
```

All unit tests pass including:
- Conflict handler tests (11 tests)
- Sync manager tests (11 tests)
- API/CLI tests (10 tests)

## Requirements Coverage

| Requirement | Status | Notes |
|-------------|--------|-------|
| NOTI-05 | Complete | User can edit wiki page and sync back to Notion |
| NOTI-06 | Complete | Concurrent edits detected and resolved by timestamp |
| NOTI-08 | Complete | System polls Notion at configurable intervals |

## Phase 12 Complete

All three plans for Phase 12 (Notion Connector) are now complete:
- Plan 12-01: Core connector and OAuth
- Plan 12-02: Property mapping and block transformation
- Plan 12-03: Bidirectional sync and polling
