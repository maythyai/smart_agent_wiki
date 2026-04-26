# Phase 1: Core Data Cycle - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning
**Mode:** Auto (decisions from design doc + research)

<domain>
## Phase Boundary

Build the foundational data cycle: users can `saw init` a wiki, `saw ingest` documents (Markdown/PDF/URL), and `saw query` / `saw search` their knowledge base via CLI. Every claim traces back to its Vault source. Write Queue (Outbox) ensures no data loss. Multi-LLM support via LiteLLM. Git integration with session branches. Agent compatibility layer. Three-tier degradation. WIP cross-session momentum.

</domain>

<decisions>
## Implementation Decisions

### Storage Architecture
- **D-01:** Four-layer storage: Vault (immutable originals) → Claims (SQLite) → Wiki (Markdown+YAML) → Index (FTS5). Hexagonal architecture with ports/adapters.
- **D-02:** SQLite as default database with WAL mode for concurrent read/write. SQLModel for simple CRUD, SQLAlchemy Core for complex queries (per stack research — SQLModel 0.0.38 is pre-release).
- **D-03:** FTS5 with `content=''` (external content mode) for full-text search. Use `unicode61` tokenizer for Phase 1 (CJK via jieba custom tokenizer deferred — requires FTS5 tokenizer API prototyping).
- **D-04:** Write Queue (Outbox) in SQLite: single durable entry point → parallel distribution to Vault/Claims/Wiki/Index sinks. Per-sink tracking with `op_id` deduplication.
- **D-05:** Vault storage: UUID directories under `vault/`, each containing `original.*`, `transcript.md`, `meta.yaml`. Git-tracked, never modified after ingest.
- **D-06:** Wiki pages: Markdown with YAML frontmatter (type, tags, related, confidence, freshness, record_type). 5 record types: SUMMARY/META/SOURCE/ALIAS/COLLECTION.
- **D-07:** Namespace organization: `wiki/concepts/`, `wiki/entities/`, `wiki/sources/`, `wiki/collections/`.

### Ingestion Pipeline
- **D-08:** Format detection → structured path (AST/schema parse, zero LLM) vs unstructured path (LLM extraction). Structured extraction for code, JSON, tables.
- **D-09:** PDF parsing: 3-tier fallback — MinerU → Docling → PyMuPDF. Quality validation on first 5 pages before committing to a parser.
- **D-10:** Unstructured extraction: single LLM in Phase 1 (multi-LLM competition deferred to Phase 2 when confidence system exists to evaluate cross-validation). Use LiteLLM with configurable model.
- **D-11:** Ingestion creates session branch `session/{timestamp}-{source_name}` for git blame dual provenance. Merge to main after successful ingest.
- **D-12:** Ingestion output: structured claims → Claims DB, entity pages → Wiki drafts, relationships → Graph (SQLite JSONL), index auto-update.

### Query Engine
- **D-13:** BM25 + FTS5 as primary search. Tree Mode (structure-aware) for hierarchical documents using anchor retrieval → tree walk → path aggregation.
- **D-14:** Context compilation: assemble relevant Wiki pages within token budget. L0 always-loaded index (~85 lines), L1 summary (~15 topics), L2 full content on demand.
- **D-15:** Natural language query via LLM: compile context → LLM generates layered answer (L1-L4) with inline citations `[^claim:uuid]`.
- **D-16:** Graph traversal: BFS/DFS on SQLite-stored entity relationships via NetworkX. Lightweight graph storage as JSONL edges.

### CLI Design
- **D-17:** CLI built with Typer. Commands: `init`, `ingest`, `query`, `search`, `status`. Rich-formatted output with tables and colors.
- **D-18:** `saw init` creates `.saw/` config directory, SQLite DB, `vault/`, `wiki/`, initializes Git repo. `--agent <name>` flag generates agent-specific config.
- **D-19:** `saw status` shows: page count, claim count, storage size, recent ingestions, WIP active tasks.

### Cross-Cutting
- **D-20:** Git integration: auto-commit on ingest and edit. Session branch per ingestion with merge to main.
- **D-21:** LiteLLM for multi-LLM support. Default model configurable via `.saw/config.yaml`. Model routing by task complexity (not per-phase).
- **D-22:** Three-tier degradation: full (LLM+embeddings) → lightweight (LLM only, BM25 search) → offline (BM25+TF-IDF, zero LLM). Auto-detect available capabilities on startup.
- **D-23:** WIP file `.saw/wip.yaml`: active tasks, next steps, pending questions. Auto-updated on each session.
- **D-24:** Agent compatibility: `saw init --agent <name>` generates CLAUDE.md/.cursorrules/AGENTS.md/GEMINI.md from shared template. All reference same core instructions.
- **D-25:** Local-first by default. No external API required for core functionality. LLM API calls are opt-in.

### Claude's Discretion
- Exact Python project structure (src layout vs flat)
- Typer command grouping and subcommand organization
- Claims DB schema details (beyond core fields)
- FTS5 index rebuild strategy
- Error message wording and CLI output formatting
- Test strategy and coverage targets
- Configuration file format details (.saw/config.yaml schema)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Document
- `docs/smart_agent_wiki_design.md` — Full architecture, 5 engines, 4-layer storage, 23 appendix design decisions (A.1-A.23)

### Research
- `.planning/research/STACK.md` — Technology stack recommendations with versions and rationale
- `.planning/research/FEATURES.md` — Feature landscape, table stakes, differentiators, dependency chains, MVP recommendation
- `.planning/research/ARCHITECTURE.md` — Hexagonal architecture, Write Queue design, engine decomposition, build order
- `.planning/research/PITFALLS.md` — 12 domain-specific pitfalls with warning signs, prevention, phase mapping
- `.planning/research/SUMMARY.md` — Synthesized research findings and roadmap implications

### Project Context
- `.planning/PROJECT.md` — Vision, core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — 65 v1 requirements with traceability
- `.planning/ROADMAP.md` — Phase 1 definition, requirements mapping, success criteria
- `.planning/STATE.md` — Current state, blockers/concerns

### Ecosystem Analysis
- `docs/llm_wiki_ecosystem_analysis.md` — 181-project categorization
- `docs/karpathy_llm_wiki_comments.md` — 666 user comments with pain points

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None (greenfield project). Design docs serve as specification.

### Established Patterns
- This is a design-only repository. No runnable code exists yet.
- All documentation is in Chinese. Maintain Chinese for user-facing content.
- ASCII diagrams in design doc must be preserved.

### Integration Points
- First code will be created in this phase. Python project structure to be established.
- Must follow hexagonal architecture pattern from research/ARCHITECTURE.md.

</code_context>

<specifics>
## Specific Ideas

- 5-minute onboarding promise: `pip install smart-agent-wiki && saw init && saw ingest paper.pdf && saw query "核心观点"` must work in under 5 minutes
- Write Queue (Outbox) is the single most critical architectural decision — must be built from day 1, cannot be retrofitted
- FTS5 tokenizer choice is locked at CREATE TABLE time — CJK strategy must be decided in this phase
- Claims DB is the foundation for Phase 2 confidence system — schema must support future confidence fields
- Git blame dual provenance (Claims→Vault + git blame→session branch) is more reliable than anchor cites

</specifics>

<deferred>
## Deferred Ideas

- Multi-LLM competition extraction (2 LLMs cross-validating) — deferred to Phase 2 when confidence system exists
- CJK custom FTS5 tokenizer (jieba) — needs prototyping; start with unicode61, upgrade later
- Vector search / embedding support — deferred to Phase 2 (optional enhancement)
- Web UI — Phase 3
- MCP Server (23 tools) — Phase 2 (agent compatibility layer MCP-03 only in Phase 1)
- Chrome clipper, RSS, video/audio ingestion — Phase 4

</deferred>

---

*Phase: 01-core-data-cycle*
*Context gathered: 2026-04-26*
