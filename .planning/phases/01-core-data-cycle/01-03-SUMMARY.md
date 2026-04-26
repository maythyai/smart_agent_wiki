---
phase: 01-core-data-cycle
plan: 03
subsystem: [query, search, graph, compare, cli]
tags: [fts5, bm25, networkx, typer, rich, layered-answer, inline-citations]

# Dependency graph
requires:
  - phase: 01-core-data-cycle
    plan: 01
    provides: "Foundation layer - Write Queue, Claims DB, FTS5, CLI scaffold"
  - phase: 01-core-data-cycle
    plan: 02
    provides: "Ingestion Engine - LLM Router, parsers, claims extraction"
provides:
  - "Search: FTS5 with bm25() ranking, snippet highlighting"
  - "Tree Mode: Anchor retrieval + tree walk for hierarchical documents"
  - "Graph Traversal: BFS/DFS via NetworkX, shortest path finding"
  - "Comparison: Similarity scoring, shared/unique claim detection"
  - "Context Compiler: L0/L1/L2 levels, token budget enforcement"
  - "Query Engine: NL query with layered answer (L1-L4), inline [^claim:uuid] citations"
  - "CLI: saw query and saw search commands with Rich output"
  - "Offline mode: Graceful fallback to keyword search when no LLM"
affects: []

# Tech tracking
tech-stack:
  added: [networkx]
  patterns: [fts5-bm25, graph-traversal, layerd-answer, token-budget, offline-fallback]

key-files:
  created:
    - src/saw/engines/query/__init__.py
    - src/saw/engines/query/search.py
    - src/saw/engines/query/tree_mode.py
    - src/saw/engines/query/graph_traverse.py
    - src/saw/engines/query/compare.py
    - src/saw/engines/query/compiler.py
    - src/saw/engines/query/engine.py
    - src/saw/drivers/cli/commands/query_cmd.py
    - src/saw/drivers/cli/commands/search_cmd.py
    - tests/unit/engines/query/__init__.py
    - tests/unit/engines/query/test_search.py
    - tests/unit/engines/query/test_graph_traverse.py
    - tests/unit/engines/query/test_compiler.py
    - tests/integration/test_query_flow.py
  modified:
    - src/saw/drivers/cli/main.py
    - src/saw/adapters/llm/prompts/query_default.yaml

key-decisions:
  - "FTS5 search uses direct table (not external content) for simpler testing"
  - "Citations use flexible regex [a-zA-Z0-9_-]+ to support various ID formats"
  - "Layered answer parsed from LLM response: first line=L1, first paragraph=L2, bullets=L3"
  - "Offline mode detected via detect_tier() and forces keyword search fallback"
  - "Graph loaded into NetworkX DiGraph on initialization with lazy reload on staleness"

patterns-established:
  - "Four query modes: search (FTS5), graph (BFS/DFS), compare (similarity), tree (structure)"
  - "Token budget enforced in ContextCompiler with coverage metric"
  - "Sources resolved from citations using claims_repo.get_by_id()"
  - "Rich-formatted CLI output with tables, panels, and progress spinners"

requirements-completed: [QUER-01, QUER-02, QUER-03, QUER-04, QUER-05, QUER-06, QUER-07, CLI-03, CLI-04]

# Metrics
duration: 20min
completed: 2026-04-26
---

# Phase 1 Plan 03: Query Engine Summary

**FTS5 search, NetworkX graph traversal, context compilation, and CLI query/search commands**

## Performance

- **Duration:** 20 min
- **Started:** 2026-04-26T08:44:35Z
- **Completed:** 2026-04-26T09:04:52Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- FTS5Search with bm25() ranking and snippet/highlight functions
- TreeModeSearch for hierarchical documents (anchor retrieval + tree walk + path aggregation)
- GraphTraverse with NetworkX BFS/DFS traversal and shortest path finding
- CompareEngine with Jaccard-like similarity scoring
- ContextCompiler with L0/L1/L2 levels and token budget enforcement
- QueryEngine orchestrating all query modes with NL query via LLM
- `saw query` CLI command with layered answer output and offline mode fallback
- `saw search` CLI command with Rich tables
- 30 tests passing (18 unit + 4 compiler + 8 integration)

## Task Commits

Each task was committed atomically:

1. **Task 1: Search + Tree Mode + Graph Traversal + Comparison** - `6087c85` (feat)
2. **Task 2: Context Compiler + Query Engine + CLI commands + Integration tests** - `7f483fa` (feat)

## Files Created/Modified

- `src/saw/engines/query/search.py` - FTS5Search with bm25() ranking and SEARCH_WITH_SNIPPETS
- `src/saw/engines/query/tree_mode.py` - TreeModeSearch with heading hierarchy support
- `src/saw/engines/query/graph_traverse.py` - GraphTraverse using NetworkX for entity relationships
- `src/saw/engines/query/compare.py` - CompareEngine with similarity scoring
- `src/saw/engines/query/compiler.py` - ContextCompiler with token budget
- `src/saw/engines/query/engine.py` - QueryEngine orchestrator with NL/query/search/graph/compare/tree modes
- `src/saw/drivers/cli/commands/query_cmd.py` - `saw query` command
- `src/saw/drivers/cli/commands/search_cmd.py` - `saw search` command
- `src/saw/drivers/cli/main.py` - Registered query and search commands
- `src/saw/adapters/llm/prompts/query_default.yaml` - Query prompt template with citation rules

## Decisions Made

- FTS5 queries use direct table access (not external content mode) for simpler test fixtures
- Citation regex uses flexible pattern `[a-zA-Z0-9_-]+` to support various claim ID formats
- Layered answer parsing: first non-empty line = L1, first paragraph = L2, bullet points = L3
- Offline mode: when `detect_tier() < LIGHTWEIGHT`, auto-switch to keyword search
- Graph staleness checked by comparing entity_relation count

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed FTS5 query syntax**
- **Found during:** Task 1 test run
- **Issue:** FTS5 MATCH queries were failing because test fixture used external content mode incorrectly
- **Fix:** Simplified to direct FTS5 table queries without external content, fixed JOIN logic
- **Files modified:** src/saw/engines/query/search.py, tests/unit/engines/query/test_search.py
- **Committed in:** 6087c85 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed citation regex pattern**
- **Found during:** Task 2 test run
- **Issue:** Original regex `r'\[\^claim:([a-f0-9-]+)\]'` only matched UUID format, not test IDs like "claim-1"
- **Fix:** Changed to flexible pattern `r'\[\^claim:([a-zA-Z0-9_-]+)\]'`
- **Files modified:** src/saw/engines/query/engine.py
- **Committed in:** 7f483fa (Task 2 commit)

**3. [Rule 3 - Blocking] Fixed import paths for detect_tier**
- **Found during:** Task 2 import verification
- **Issue:** `detect_tier` was imported from wrong module (`domain.value_objects` instead of `config.settings`)
- **Fix:** Corrected imports in query_cmd.py and search_cmd.py
- **Files modified:** src/saw/drivers/cli/commands/query_cmd.py, src/saw/drivers/cli/commands/search_cmd.py
- **Committed in:** 7f483fa (Task 2 commit)

**4. [Rule 3 - Blocking] Fixed test fixture schema alignment**
- **Found during:** Task 2 integration test run
- **Issue:** Test fixture claim table columns in different order than ClaimsRepository expected
- **Fix:** Aligned test fixture schema with ClaimsRepository.CLAIMS_DB_SCHEMA
- **Files modified:** tests/integration/test_query_flow.py
- **Committed in:** 7f483fa (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (2 bugs, 2 blocking)
**Impact on plan:** All auto-fixes necessary for test correctness. No scope creep.

## User Setup Required

- LLM API key (optional): Set OPENAI_API_KEY or ANTHROPIC_API_KEY for NL query mode
- Without LLM: System operates in offline mode with keyword search only

## Next Phase Readiness

- Query engine ready for end-to-end: `saw init -> saw ingest -> saw query`
- All query modes functional: search, graph, compare, tree
- Layered answer format standardized for UI consumption
- Offline mode tested and working

## Self-Check: PASSED

- All 14 files verified present on disk
- All 2 task commits verified in git log (6087c85, 7f483fa)
- All 105 tests passing (105 total: 86 unit + 21 integration)
- Zero warnings in pytest output

---

*Phase: 01-core-data-cycle*
*Completed: 2026-04-26*
