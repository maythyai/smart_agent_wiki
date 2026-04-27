---
phase: 02-intelligence-governance
plan: 03
subsystem: [mcp, query, learn]
tags: [fastmcp, mcp-tools, progressive-memory, adaptive-index, research-on-miss, token-efficiency]

# Dependency graph
requires: [02-01, 02-02]
provides:
  - "MCP Server: FastMCP with 23 tools for agent integration"
  - "Progressive Memory: L0/L1/L2 depth for token efficiency"
  - "Adaptive Index: Automatic upgrade at 50/200 page thresholds"
  - "Research-on-Miss: Automatic knowledge gap filling"
  - "CLI Command: saw mcp"
affects: []

# Tech tracking
tech-stack:
  added: [fastmcp]
  patterns: [mcp-server, progressive-memory, adaptive-index, research-on-miss, rate-limiting]

key-files:
  created:
    - src/saw/drivers/mcp/__init__.py
    - src/saw/drivers/mcp/config.py
    - src/saw/drivers/mcp/server.py
    - src/saw/drivers/mcp/tools/__init__.py
    - src/saw/drivers/mcp/tools/ingest.py
    - src/saw/drivers/mcp/tools/query.py
    - src/saw/drivers/mcp/tools/govern.py
    - src/saw/drivers/mcp/tools/learn.py
    - src/saw/drivers/mcp/tools/collaborate.py
    - src/saw/drivers/mcp/research_on_miss.py
    - src/saw/engines/query/memory.py
    - src/saw/engines/learn/adaptive_index.py
    - src/saw/drivers/cli/commands/mcp_cmd.py
    - tests/unit/drivers/test_mcp_server.py
    - tests/unit/drivers/test_mcp_tools.py
    - tests/unit/engines/query/test_memory.py
    - tests/unit/engines/learn/test_adaptive_index.py
    - tests/unit/drivers/test_research_on_miss.py
  modified:
    - src/saw/drivers/cli/main.py

key-decisions:
  - "MCPConfig defaults to 127.0.0.1 (localhost only) per PITFALLS.md security"
  - "All 23 tools include version field for schema drift detection per PITFALLS.md"
  - "L0 index capped at 100 lines per unified-memory-ai-agents pattern"
  - "Index thresholds at 50 and 200 pages per XCUT-06"
  - "Research-on-Miss threshold defaults to 0.5 coverage per XCUT-08"
  - "Rate limiter allows 10 calls per minute for external APIs"

patterns-established:
  - "MCP tools: async handlers calling engine methods with version field in output"
  - "Progressive memory: L0 (always-loaded), L1 (summaries), L2 (full content)"
  - "Adaptive index: FLAT -> HIERARCHICAL -> INDEXED based on page count"
  - "Research-on-Miss: should_trigger() -> trigger_research() -> auto-ingest"

requirements-completed: [MCP-01, MCP-02, XCUT-05, XCUT-06, XCUT-08]

# Metrics
duration: 25min
completed: 2026-04-27
---
# Phase 02 Plan 03: MCP Server + Progressive Memory Summary

**FastMCP server with 23 tools, progressive memory depth (L0/L1/L2), adaptive index evolution, and Research-on-Miss for automatic knowledge gap filling**

## Performance

- **Duration:** 25 min
- **Started:** 2026-04-27T00:25:49Z
- **Completed:** 2026-04-27T00:51:44Z
- **Tasks:** 5
- **Files modified:** 17

## Accomplishments

- **MCP Server Foundation:**
  - FastMCP server with name 'smart-agent-wiki' and version '1.0.0'
  - MCPConfig with localhost binding (per PITFALLS.md)
  - `saw mcp` CLI command with --port, --host, --transport options
  - Support for stdio (default) and SSE transports
  - 10 tests for server creation, configuration, and CLI

- **23 MCP Tools:**
  - Ingest tools (2): saw_ingest, saw_reparse
  - Query tools (7): saw_query, saw_search, saw_tree_search, saw_graph, saw_compare, saw_compile, saw_coverage
  - Govern tools (7): saw_lint, saw_conflicts, saw_verify, saw_freshness, saw_review, saw_audit, saw_blast_radius
  - Learn tools (5): saw_status, saw_learn, saw_distill, saw_suggest, saw_wip
  - Collaborate tools (2): saw_workflow, saw_feedback
  - All tools include version field for schema drift detection
  - 30 tests for tool registration and handler calls

- **Progressive Memory Depth (L0/L1/L2):**
  - MemoryLevel enum (L0=always-loaded, L1=summary, L2=full)
  - ProgressiveMemory class with get_l0(), get_l1(), get_l2()
  - L0 capped at 100 lines (per unified-memory-ai-agents)
  - L1 summaries for ~15 recent topics with budget
  - L2 full content with budget truncation
  - auto_select_level() for automatic selection
  - 10 tests for all memory levels

- **Adaptive Index Evolution:**
  - IndexMode enum (FLAT, HIERARCHICAL, INDEXED)
  - AdaptiveIndexManager with mode detection and upgrade
  - Thresholds at 50 and 200 pages
  - build_category_tree() for hierarchical mode
  - build_concept_clusters() for indexed mode
  - 10 tests for mode detection and upgrade

- **Research-on-Miss:**
  - ResearchResult dataclass for research results
  - RateLimiter for external API rate limiting
  - ResearchOnMissHandler with trigger detection
  - Parallel web/academic/code searches
  - Auto-ingest with rate limiting
  - 7 tests for trigger and execution

- 67 tests passing (10 + 30 + 10 + 10 + 7)

## Task Commits

Each task was committed atomically:

1. **Task 1: MCP Server Foundation with FastMCP** - `53fd7fb` (feat)
2. **Task 2: Implement All 23 MCP Tools** - `c04f0f3` (feat)
3. **Task 3: Progressive Memory Depth (L0/L1/L2)** - `d92d4ab` (feat)
4. **Task 4: Adaptive Index Evolution** - `8015e0f` (feat)
5. **Task 5: Research-on-Miss Handler** - `c822f90` (feat)

## Files Created/Modified

### MCP Driver
- `src/saw/drivers/mcp/__init__.py` - Module exports
- `src/saw/drivers/mcp/config.py` - MCPConfig settings
- `src/saw/drivers/mcp/server.py` - FastMCP server
- `src/saw/drivers/mcp/tools/__init__.py` - Tool registration
- `src/saw/drivers/mcp/tools/ingest.py` - saw_ingest, saw_reparse
- `src/saw/drivers/mcp/tools/query.py` - 7 query tools
- `src/saw/drivers/mcp/tools/govern.py` - 7 govern tools
- `src/saw/drivers/mcp/tools/learn.py` - 5 learn tools
- `src/saw/drivers/mcp/tools/collaborate.py` - 2 collaborate tools
- `src/saw/drivers/mcp/research_on_miss.py` - Research-on-Miss handler

### Query Engine Extension
- `src/saw/engines/query/memory.py` - Progressive memory depth

### Learn Engine Extension
- `src/saw/engines/learn/adaptive_index.py` - Adaptive index evolution

### CLI
- `src/saw/drivers/cli/commands/mcp_cmd.py` - `saw mcp` command
- `src/saw/drivers/cli/main.py` - Registered mcp command

### Tests
- `tests/unit/drivers/test_mcp_server.py` - 10 server tests
- `tests/unit/drivers/test_mcp_tools.py` - 30 tools tests
- `tests/unit/engines/query/test_memory.py` - 10 memory tests
- `tests/unit/engines/learn/test_adaptive_index.py` - 10 index tests
- `tests/unit/drivers/test_research_on_miss.py` - 7 research tests

## Decisions Made

- MCPConfig defaults to 127.0.0.1 (localhost only) per PITFALLS.md security requirement
- All 23 tools include version field for schema drift detection per PITFALLS.md
- L0 index capped at 100 lines per unified-memory-ai-agents pattern (XCUT-05)
- Index mode thresholds at 50 and 200 pages per XCUT-06
- Research-on-Miss coverage threshold defaults to 0.5 per XCUT-08
- Rate limiter allows 10 calls per minute for external APIs
- Backward-compatible tool parameters (new params have defaults)

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

- MCP server ready for integration with Claude Code, Cursor, and other MCP-compatible agents
- Progressive memory ready for boot sequence optimization
- Adaptive index ready for scalability testing
- Research-on-Miss ready for knowledge gap filling
- `saw mcp` CLI command functional with all options
- Phase 02 complete - all 3 plans finished

## Self-Check: PASSED

- All 17 files verified present on disk
- All 5 task commits verified in git log (53fd7fb, c04f0f3, d92d4ab, 8015e0f, c822f90)
- All 67 tests passing
- CLI `saw mcp --help` functional
- Zero warnings in pytest output

---

*Phase: 02-intelligence-governance*
*Completed: 2026-04-27*