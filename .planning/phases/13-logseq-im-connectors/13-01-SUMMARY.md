---
phase: 13-logseq-im-connectors
plan: 01
subsystem: connectors
tags:
  - logseq
  - local-sync
  - file-watching
  - bidirectional
requires:
  - PHASE-10-connector-framework
  - PHASE-11-sync-engine
provides:
  - LogseqConnector
  - LogseqParser
  - LogseqFileWatcher
  - logseq-sync-capability
key_decisions:
  - Block-level granularity for Claims (each bullet = one Claim)
  - 500ms debounce for file watching
  - SHA-256 hash for change detection
  - Conflict files with timestamp suffix
metrics:
  duration: 15m
  tests: 37
  files_created: 13
  completed_at: "2026-05-02"
---

# Phase 13 Plan 01: Logseq Connector Summary

## One-liner

Logseq local file connector with Markdown parsing, property drawer extraction, real-time file watching, and bidirectional sync capability.

## Implementation

### Files Created

- `src/saw/connectors/logseq/__init__.py` - Package exports
- `src/saw/connectors/logseq/models.py` - LogseqConfig, BlockNode, PropertyDrawer, ParsedPage
- `src/saw/connectors/logseq/parser.py` - LogseqParser for Markdown/EDN parsing
- `src/saw/connectors/logseq/file_watcher.py` - LogseqFileWatcher with debouncing
- `src/saw/connectors/logseq/connector.py` - LogseqConnector implementing UnifiedConnectorInterface
- `src/saw/db/logseq_models.py` - SQLAlchemy models for file hash and sync state
- `src/saw/api/logseq.py` - FastAPI endpoints for connect/sync/watch

### Requirements Covered

| ID | Description | Status |
|----|-------------|--------|
| LOGS-01 | Configure Logseq graph path | Done |
| LOGS-02 | Parse Markdown blocks | Done |
| LOGS-03 | Extract property drawers | Done |
| LOGS-04 | File watching with debouncing | Done |
| LOGS-05 | Bidirectional sync (put_item) | Done |
| LOGS-06 | Change detection via hash | Done |
| LOGS-08 | EDN config parsing | Done |
| LOGS-09 | Namespace hierarchy mapping | Done |
| LOGS-10 | Wikilink preservation | Done |

## Key Decisions

1. **Block Granularity**: Each bullet point becomes a separate Claim, with parent-child relationships preserved via `parent_block_id`.

2. **Debounce Window**: 500ms debounce to batch rapid file changes (e.g., during bulk saves).

3. **Conflict Handling**: When concurrent edits detected (hash mismatch), create `.conflict-{timestamp}.md` file preserving both versions.

4. **Wikilink Preservation**: All `[[page]]` syntax preserved in content; not transformed to SAW internal links.

## Tests

37 unit tests covering:
- Model validation (12 tests)
- Parser functionality (10 tests)
- File watcher (6 tests)
- Connector implementation (9 tests)

## Deviations

None - executed exactly as planned.
