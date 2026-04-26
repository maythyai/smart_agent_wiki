---
phase: 01-core-data-cycle
plan: 01
subsystem: [storage, cli, config]
tags: [sqlite, fts5, typer, pydantic, write-queue, hexagonal, outbox-pattern, yaml]

# Dependency graph
requires:
  - phase: none
    provides: "Greenfield project - no prior phase"
provides:
  - "Domain layer: protocols, value objects, models, events, exceptions"
  - "Storage adapters: SQLite connection, Claims DB, Vault, Wiki repositories"
  - "Write Queue: SQLite outbox with atomic enqueue and per-sink tracking"
  - "Dispatcher: parallel sink dispatch with retry and crash recovery"
  - "5 sinks: vault, claims, wiki, fts5, graph (all idempotent)"
  - "Configuration: WikiSettings, LLMSettings, detect_tier() three-tier degradation"
  - "CLI: saw init and saw status commands with Rich output"
  - "Agent compatibility: claude-code, cursor, copilot, gemini templates"
affects: [02-core-data-cycle, ingest-engine, query-engine]

# Tech tracking
tech-stack:
  added: [typer, sqlmodel, litellm, networkx, pydantic, pydantic-settings, rich, python-frontmatter, markdown-it-py, trafilatura, beautifulsoup4, rank-bm25, PyYAML, platformdirs, httpx, hatchling]
  patterns: [hexagonal-architecture, write-queue-outbox, idempotent-sinks, three-tier-degradation, yaml-frontmatter]

key-files:
  created:
    - pyproject.toml
    - src/saw/domain/protocols.py
    - src/saw/domain/value_objects.py
    - src/saw/domain/claims.py
    - src/saw/domain/wiki.py
    - src/saw/domain/entities.py
    - src/saw/domain/events.py
    - src/saw/domain/exceptions.py
    - src/saw/adapters/storage/sqlite_connection.py
    - src/saw/adapters/storage/claims_repository.py
    - src/saw/adapters/storage/vault_repository.py
    - src/saw/adapters/storage/wiki_repository.py
    - src/saw/write_queue/queue.py
    - src/saw/write_queue/dispatcher.py
    - src/saw/write_queue/sinks/vault_sink.py
    - src/saw/write_queue/sinks/claims_sink.py
    - src/saw/write_queue/sinks/wiki_sink.py
    - src/saw/write_queue/sinks/fts5_sink.py
    - src/saw/write_queue/sinks/graph_sink.py
    - src/saw/config/settings.py
    - src/saw/config/defaults.py
    - src/saw/config/agent_templates.py
    - src/saw/drivers/cli/main.py
    - src/saw/drivers/cli/commands/init_cmd.py
    - src/saw/drivers/cli/commands/status_cmd.py
    - tests/unit/domain/test_value_objects.py
    - tests/unit/write_queue/test_queue.py
    - tests/unit/write_queue/test_dispatcher.py
    - tests/integration/test_init_flow.py

key-decisions:
  - "Relaxed pydantic version to >=2.12.5 (from ==2.13.3) due to litellm dependency conflict"
  - "Relaxed typer and other dependencies to >= ranges due to litellm click==8.1.8 pin conflicting with typer>=0.24"
  - "Used raw sqlite3 for Claims DB schema init instead of SQLModel engine (FTS5 CREATE VIRTUAL TABLE requires raw SQL)"
  - "Pydantic model_config = ConfigDict() instead of deprecated inner Config class"

patterns-established:
  - "Hexagonal architecture: domain protocols in domain/, implementations in adapters/"
  - "Write Queue Outbox: all storage writes through SQLite outbox with per-sink tracking"
  - "Idempotent sinks: every sink handles duplicate op_id safely"
  - "YAML frontmatter: wiki pages use YAML + Markdown serialization"
  - "Three-tier degradation: detect_tier() returns OFFLINE/LIGHTWEIGHT/FULL"

requirements-completed: [STOR-01, STOR-02, STOR-03, STOR-04, STOR-05, STOR-06, STOR-07, CLI-01, CLI-07, XCUT-03, XCUT-04, XCUT-07]

# Metrics
duration: 24min
completed: 2026-04-26
---

# Phase 1 Plan 01: Foundation Summary

**Complete four-layer storage (Vault/Claims/Wiki/FTS5), Write Queue with 5 idempotent sinks, CLI init/status commands, and agent compatibility layer**

## Performance

- **Duration:** 24 min
- **Started:** 2026-04-26T03:15:07Z
- **Completed:** 2026-04-26T03:39:06Z
- **Tasks:** 4
- **Files modified:** 29

## Accomplishments
- `saw init` creates all four storage layers, SQLite DB with FTS5, Git repo, config, WIP file
- `saw status` reports page count, claim count, entity count, storage size, WIP state, capability tier
- Write Queue with atomic enqueue, per-sink tracking, crash recovery, and 5 idempotent sinks
- Agent compatibility: `saw init --agent claude-code` generates CLAUDE.md with core instructions
- 42 tests passing (15 domain unit + 14 write queue unit + 13 integration)

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold + Domain layer** - `da6317c` (feat)
2. **Task 2: Storage adapters + SQLite connection + Claims DB + Repositories + Config** - `f534c1e` (feat)
3. **Task 3: Write Queue + Sinks + Dispatcher + Crash Recovery** - `3de3eca` (feat)
4. **Task 4: CLI init/status + Agent Compat + WIP + Integration Tests** - `a245d59` (feat)

## Files Created/Modified
- `pyproject.toml` - Build config with hatchling, all Phase 1 dependencies (relaxed version ranges)
- `src/saw/domain/protocols.py` - All engine interface protocols (ClaimsRepository, VaultRepository, WikiRepository, WriteQueue, Sink)
- `src/saw/domain/value_objects.py` - ConfidenceLevel, SourceMark, FreshnessLevel, PageType, CapabilityTier, WriteOpStatus, ClaimRef, WikiPageRef
- `src/saw/domain/claims.py` - Claim dataclass with SHA-256 content hash
- `src/saw/domain/wiki.py` - WikiPage dataclass + WikiFrontmatter Pydantic model
- `src/saw/domain/entities.py` - Entity and EntityRelation dataclasses
- `src/saw/domain/events.py` - ClaimsReady, WriteFailed, IngestCompleted events
- `src/saw/domain/exceptions.py` - SAWError hierarchy (Storage, WriteQueue, Vault, ClaimsDB, FTS5, Config)
- `src/saw/adapters/storage/sqlite_connection.py` - SQLite connection factory with WAL mode and all PRAGMAs
- `src/saw/adapters/storage/claims_repository.py` - SQLiteClaimsRepository with FTS5 search, INSERT OR IGNORE
- `src/saw/adapters/storage/vault_repository.py` - VaultRepository with immutable UUID directories
- `src/saw/adapters/storage/wiki_repository.py` - WikiRepository with YAML frontmatter + Markdown
- `src/saw/write_queue/queue.py` - SQLiteWriteQueue with atomic enqueue and per-sink tracking
- `src/saw/write_queue/dispatcher.py` - Dispatcher with retry, dead letter, and crash recovery
- `src/saw/write_queue/sinks/vault_sink.py` - Idempotent vault storage sink
- `src/saw/write_queue/sinks/claims_sink.py` - Idempotent claims DB sink
- `src/saw/write_queue/sinks/wiki_sink.py` - Idempotent wiki page sink
- `src/saw/write_queue/sinks/fts5_sink.py` - FTS5 index update sink (DELETE+INSERT pattern)
- `src/saw/write_queue/sinks/graph_sink.py` - Entity/relation graph sink
- `src/saw/config/settings.py` - WikiSettings, LLMSettings, detect_tier(), load_config()
- `src/saw/config/defaults.py` - DEFAULT_CONFIG and WIP_TEMPLATE constants
- `src/saw/config/agent_templates.py` - Agent compatibility templates for 4 agents
- `src/saw/drivers/cli/main.py` - Typer CLI entry point
- `src/saw/drivers/cli/commands/init_cmd.py` - `saw init` command
- `src/saw/drivers/cli/commands/status_cmd.py` - `saw status` command

## Decisions Made
- Relaxed dependency version pins to ranges (>=) because litellm 1.83.13 pins click==8.1.8 which conflicts with typer>=0.24 requiring click>=8.2.1. Using typer>=0.23.1 resolves this.
- Used raw sqlite3 for Claims DB schema initialization instead of SQLModel engine, because FTS5 CREATE VIRTUAL TABLE requires raw SQL execution that SQLModel's create_engine doesn't handle for virtual tables.
- Migrated WikiSettings from deprecated Pydantic inner Config class to model_config = ConfigDict().

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Relaxed dependency versions for litellm compatibility**
- **Found during:** Task 1 (pip install)
- **Issue:** litellm 1.83.13 pins click==8.1.8 and pydantic==2.12.5, conflicting with pinned typer==0.24.2 and pydantic==2.13.3
- **Fix:** Changed pyproject.toml to use >= ranges for typer, pydantic, pydantic-settings, and other conflicting dependencies
- **Files modified:** pyproject.toml
- **Verification:** `pip install -e ".[dev]"` succeeds without conflicts
- **Committed in:** da6317c (Task 1 commit)

**2. [Rule 1 - Bug] Fixed missing datetime parameter in Dispatcher.recover()**
- **Found during:** Task 3 (test run)
- **Issue:** recover() had `updated_at = ?` placeholder but supplied no parameter value
- **Fix:** Added `now = datetime.now(timezone.utc).isoformat()` and passed it as parameter
- **Files modified:** src/saw/write_queue/dispatcher.py
- **Verification:** test_recover_resets_processing_to_pending passes
- **Committed in:** 3de3eca (Task 3 commit)

**3. [Rule 1 - Bug] Fixed f-string syntax error in init_cmd.py**
- **Found during:** Task 4 (integration test collection)
- **Issue:** `wiki_path / 'vault'/` has trailing slash inside f-string expression causing SyntaxError
- **Fix:** Moved trailing slash outside the expression: `{wiki_path / 'vault'}/`
- **Files modified:** src/saw/drivers/cli/commands/init_cmd.py
- **Verification:** All 13 integration tests pass
- **Committed in:** a245d59 (Task 4 commit)

**4. [Rule 1 - Bug] Fixed Pydantic V2 deprecated Config class**
- **Found during:** Task 4 (pytest warning)
- **Issue:** WikiSettings used deprecated inner `class Config` pattern, triggering PydanticDeprecatedSince20 warning
- **Fix:** Replaced with `model_config = ConfigDict(arbitrary_types_allowed=True)` and imported ConfigDict
- **Files modified:** src/saw/config/settings.py
- **Verification:** All 42 tests pass with zero warnings
- **Committed in:** a245d59 (Task 4 commit)

---

**Total deviations:** 4 auto-fixed (2 blocking, 2 bugs)
**Impact on plan:** All auto-fixes necessary for build/test correctness. No scope creep.

## Issues Encountered
- pygit2 excluded from dependencies due to system dependency (libgit2) availability uncertainty; git operations use subprocess fallback in init_cmd.py

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full four-layer storage foundation ready for Plan 02 (Ingest Engine) to write through Write Queue
- Domain protocols ready for engine implementations to depend on
- Claims DB schema supports all fields needed for Phase 2 confidence system
- FTS5 index ready for search operations in Plan 03 (Query Engine)
- CLI scaffold ready for additional commands (ingest, query, search)
- pygit2 needs to be added back or git operations need to be finalized for session branch support (Plan 02)

---
*Phase: 01-core-data-cycle*
*Completed: 2026-04-26*

## Self-Check: PASSED

- All 30 files verified present on disk
- All 4 task commits verified in git log (da6317c, f534c1e, 3de3eca, a245d59)
- All 42 tests passing with zero warnings
