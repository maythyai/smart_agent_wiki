# Project Research Summary

**Project:** Smart Agent Wiki (智能多代理知识平台)
**Domain:** Intelligent multi-agent knowledge management platform
**Researched:** 2026-04-26
**Confidence:** HIGH

## Executive Summary

Smart Agent Wiki is a local-first, multi-agent knowledge platform that builds on Karpathy's LLM Wiki concept but extends it far beyond any of the 181 existing derivative projects. Research across the full ecosystem -- 181 projects analyzed, 666 user comments mined, 25+ deep code audits -- shows a clear gap: no existing project combines structured knowledge storage, confidence-based trust, contradiction resolution, learning adaptation, and multi-agent collaboration into a single system. The recommended approach is a Python-based hexagonal architecture with five specialized engines (Ingest, Query, Govern, Learn, Collaborate), a four-layer storage model (Vault/Claims/Wiki/Index), and a Write Queue that guarantees data integrity across all sinks. This architecture enables three driving adapters (CLI, MCP Server, Web API) to share the same engine logic without duplication.

The core technical risk is that this system has many moving parts -- six storage sinks, five engines, three user interfaces, and 23 MCP tools. The critical mitigation is the build order: Ingest + Claims DB + Write Queue + CLI first (Phase 1), Governance + MCP second (Phase 2), Multi-agent + Web UI third (Phase 3). Each phase delivers standalone value and validates the foundation before the next layer is added. The second major risk cluster is around FTS5: segment b-tree proliferation, external content inconsistency, and CJK tokenizer selection all bite at scale and must be configured correctly from day one. The third risk is LLM cost management: the design is deliberately "zero-LLM by default" for structured data, with LiteLLM model routing to keep daily costs under $0.50 for personal use.

## Key Findings

### Recommended Stack

The stack is Python-first, local-first, and deliberately avoids heavy framework dependencies (no LangChain, no LlamaIndex, no ChromaDB default). All 28 packages were verified against PyPI with current versions. The two areas of concern are SQLModel (still 0.0.x beta) and cedar-python (v0.1.4, very early); both have documented fallback paths.

**Core technologies:**
- Python 3.11+: AI ecosystem's first-class language; all LLM/embedding/MCP libraries are Python-native
- FastAPI + Typer: consistent type-annotation-driven development for both Web API and CLI; shared author (tiangolo)
- SQLite FTS5: zero-install full-text search, BM25 ranking, built into standard library; perfect match for local-first architecture
- LiteLLM: 100+ LLM provider unification with built-in retry, fallback, rate limiting, and cost tracking
- FastMCP 3.x: standard MCP server framework wrapping official SDK; 23 tool definitions via decorators
- NetworkX: pure Python graph engine for knowledge graph traversal; sufficient for <100K entities
- LanceDB (optional): embedded vector database with zero server dependency; complements FTS5 for hybrid search

**Critical version notes:**
- SQLModel 0.0.38 is pre-release; complex query paths should use SQLAlchemy Core directly as fallback
- cedar-python 0.1.4 is experimental; Guardian agent must abstract behind PolicyEngine protocol with CLI subprocess fallback
- FastMCP 3.x is RC; pin to stable version for production, test RC in development only

### Expected Features

**Must have (table stakes -- 13 features):**
- Multi-format ingestion (PDF/Markdown/URL) -- core value proposition
- FTS5 full-text search with BM25 ranking -- unusable without search beyond ~50 pages
- Wiki page creation and cross-reference system -- the core Karpathy pattern
- CLI interface (init/ingest/query/lint) -- developer audience, 5-minute onboarding
- Immutable Vault storage -- provenance foundation
- Source provenance tracing -- addresses #1 user pain point (hallucination/accuracy)
- Multi-LLM support via LiteLLM -- users refuse vendor lock-in
- Local-first / offline capable -- privacy is a top-3 pain point
- Git version control -- audit trail expected by power users
- Health check / Lint -- Karpathy's original "lint" operation
- MCP Server -- 20+ competing projects expose MCP; becoming standard protocol
- Incremental knowledge building -- knowledge compounds, never re-derived
- Write Queue (Outbox) -- architectural foundation; impossible to retrofit later

**Should have (differentiators -- 21 features):**
- 4-layer confidence system -- zero competing implementations; headline differentiator
- Contradiction detection with 3-strategy resolution -- only 3 projects attempt any form
- Learning engine (training period + FSRS + cognitive distillation) -- zero competitors
- Structured zero-LLM extraction (AST for code, schema for JSON) -- 60-131x token savings
- Multi-agent role-based collaboration (6 specialized agents) -- only 1 project has multi-agent governance
- Cryptographic audit layer (Ed25519 + Cedar) -- novel for knowledge governance
- 4-layer storage architecture -- no project combines all four layers
- Research-on-Miss auto-research loop -- positive feedback flywheel
- 16+ agent compatibility layer -- most portable design in ecosystem

**Defer to v2+:**
- General-purpose chatbot UI, real-time collaboration, mobile app, plugin marketplace, custom embedding training

### Architecture Approach

The system follows a Hexagonal (Ports and Adapters) architecture with five domain engines, a single Write Queue for all mutations, and a hybrid communication model (60% synchronous protocol calls, 40% async event bus). The Write Queue (Outbox pattern) is the architectural linchpin: every storage mutation flows through it, enabling crash recovery, idempotent sinks, and audit logging. The event bus decouples engines for eventual-consistency side effects (ClaimsReady triggers governance, CoverageMiss triggers auto-research).

**Major components:**
1. **Domain layer** (domain/) -- pure Python Protocols, value objects, events; zero external dependencies; innermost hexagon
2. **Five engines** (engines/) -- Ingest, Query, Govern, Learn, Collaborate; pure business logic with constructor-injected dependencies
3. **Write Queue** (write_queue/) -- SQLite-backed Outbox with parallel sink dispatch; single mutation entry point for all storage
4. **Adapters** (adapters/) -- storage, LLM, parsers, crypto; swappable implementations behind Protocol interfaces
5. **Three drivers** (drivers/) -- CLI (Typer), MCP Server (FastMCP), Web API (FastAPI); share engine layer via dependency injection

### Critical Pitfalls

1. **FTS5 external content table inconsistency** -- FTS5 silently diverges from source tables when writes are partial. Prevent with Write Queue per-sink tracking, periodic rebuild checks in `saw lint`, and consistency count verification.

2. **LiteLLM cooldown cascading failure** -- Default `allowed_fails=0` puts a deployment in cooldown after ONE failure, which cascades across tiers. Set `allowed_fails=3`, use separate API keys per model tier, implement three-layer degradation fallback.

3. **Confidence score inflation through circular validation** -- Two LLMs "cross-validating" from shared training data is not real validation. Enforce different model families for cross-validation, strict context isolation, weighted aggregation instead of strict-minimum scoring.

4. **Knowledge graph entity resolution explosion** -- Over-merging creates hairball graphs; under-merging creates fragmented graphs. Build canonical entity registry in Phase 1, use Scholar (Opus) for ambiguous resolution, add resolution confidence weight to 4-signal model.

5. **Write Queue orphan messages** -- 6 sinks means 64 possible partial-completion states after crash. Implement per-sink completion tracking, idempotent sinks (content-addressable Vault, UUID-primary-key Claims), and `saw lint --queue` recovery command.

## Implications for Roadmap

### Phase 1A: Core Data Cycle (Weeks 1-4)
**Rationale:** Everything depends on the ability to ingest documents, produce structured claims, and query them. This phase establishes the data foundation -- domain models, storage, write queue, and the first engine (Ingest). No other feature works without this.
**Delivers:** Working `saw init && saw ingest doc.md && saw query "..."` cycle with Markdown/URL ingestion, FTS5 search, and CLI interface.
**Addresses:** Multi-format ingestion (Markdown/URL), FTS5 full-text search, CLI interface, Vault + Claims storage, source provenance, Write Queue, Git version control, WIP momentum.
**Avoids:** FTS5 inconsistency (Write Queue per-sink tracking from day one), FTS5 segment proliferation (automerge/crisismerge config set at table creation), Write Queue orphans (idempotent sinks with UUID dedup).
**Research needed:** No -- this phase uses well-documented patterns (SQLite FTS5, Typer CLI, Outbox pattern).

### Phase 1B: PDF Ingestion + MCP Foundation (Weeks 5-7)
**Rationale:** PDF support is the most-requested format. MCP Server is the second driving adapter and validates that the hexagonal architecture works (CLI and MCP sharing the same engines). This phase proves the architecture.
**Delivers:** PDF ingestion with 3-tier fallback (Docling/PyMuPDF), initial MCP Server with 5 tools, Ed25519 basic signing, hardened Write Queue with retry/dead-letter.
**Addresses:** PDF ingestion, MCP Server (initial 5 tools), cryptographic audit (basic).
**Avoids:** PDF silent failures (quality metrics: word count vs. expected, parser tier recorded in Vault metadata), MCP schema drift (Pydantic models for tool schemas from the start).
**Research needed:** Low -- Docling API patterns may need a quick spike during planning.

### Phase 2A: Governance Engine (Weeks 8-11)
**Rationale:** The 4-layer confidence system is the headline differentiator. It requires a mature Claims DB (built in Phase 1) to compare claims and detect contradictions. Building governance before learning means the learning engine has quality signals to learn from.
**Delivers:** Full confidence assessment, contradiction detection with 3 resolution strategies, 9-level freshness tracking, blast radius analysis, lint/verify CLI commands.
**Addresses:** Confidence system, contradiction detection, freshness tracking, blast radius.
**Avoids:** Confidence inflation (strict cross-validation independence rules, weighted aggregation), Guardian complexity spiral (200-rule cap, 30-day TTL on auto-generated rules).
**Research needed:** Moderate -- Cedar policy engine integration is under-documented; the cedar-python 0.1.4 binding may need CLI subprocess fallback prototyping.

### Phase 2B: Learning Engine + Full MCP (Weeks 12-15)
**Rationale:** Learning requires user behavior data that only exists after Phase 1+2 runtime. The training period adaptation, FSRS spaced repetition, and cognitive distillation all need real usage patterns. Full MCP (23 tools) enables agent ecosystem integration.
**Delivers:** 30-day training period, FSRS scheduling, cognitive distillation to SOPs, knowledge expiry/pruning, full 23-tool MCP Server, multi-LLM competition extraction.
**Addresses:** Learning engine, FSRS spaced repetition, cognitive distillation, knowledge lifecycle, full MCP tools.
**Avoids:** Entity resolution explosion (canonical entity registry built in Phase 1 now gets Scholar-level disambiguation), LiteLLM cooldown cascading (multi-LLM routing with per-tier API keys and degradation fallbacks).
**Research needed:** Moderate -- FSRS library integration and A2A protocol details need spikes.

### Phase 3: Collaboration + Visualization (Weeks 16-21)
**Rationale:** Multi-agent orchestration depends on all five engines being functional. Web UI depends on all engines and the API layer. This is the integration phase that connects everything.
**Delivers:** 6 role-based agents, YAML workflow orchestration, React Web UI with Cytoscape.js graph visualization and Milkdown editor, Research-on-Miss auto-research loop, Chrome clipper extension.
**Addresses:** Multi-agent collaboration, YAML workflows, Web UI, graph visualization, Research-on-Miss, agent compatibility layer.
**Avoids:** Multi-agent deadlock (workflow timeouts, lock ordering, max_retries with fallback actions on every YAML gate), graph hairball (adaptive visualization: full graph under 50 nodes, community view 50-200, topic clusters over 200).
**Research needed:** Yes -- React 19 + Cytoscape.js integration patterns, Milkdown configuration, A2A protocol spec details, and Chrome extension manifest v3 patterns all need research spikes.

### Phase Ordering Rationale

- **Data before intelligence:** Ingest + Claims DB + Write Queue must be solid before any LLM-dependent feature (confidence assessment, contradiction detection, multi-agent orchestration). Bad data foundation corrupts everything above it.
- **Trust before learning:** The governance engine must produce reliable confidence signals before the learning engine tries to learn from them. Learning from inflated confidence data teaches the system wrong preferences.
- **Engines before agents:** All five engines must be functional before the collaborate engine orchestrates them. Multi-agent workflows call into Ingest, Query, Govern, and Learn; if any are missing or unreliable, workflows break unpredictably.
- **Write Queue as first architectural commitment:** The Outbox pattern is impossible to retrofit. It must be the first infrastructure built and must be correct from day one. Every other feature depends on writes being reliable.
- **FTS5 config at creation time:** Tokenizer choice, detail level, automerge/crisismerge settings are locked at `CREATE VIRTUAL TABLE` time. Wrong choices require full index rebuilds. Phase 1 must get this right.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2A:** Cedar policy engine integration -- cedar-python is v0.1.4, minimal documentation; may need custom policy engine design
- **Phase 2B:** FSRS library integration patterns -- how to map FSRS card scheduling to wiki page freshness review scheduling
- **Phase 3:** React 19 + Cytoscape.js + Milkdown frontend stack -- integration patterns, state management with Zustand, WebSocket real-time updates
- **Phase 3:** A2A protocol specification -- JSON-RPC message format, agent capability negotiation, async message queue implementation

Phases with standard patterns (skip research-phase):
- **Phase 1A:** SQLite FTS5, Typer CLI, Outbox pattern, Pydantic models -- all well-documented, extensive examples
- **Phase 1B:** Docling/PyMuPDF PDF parsing, FastMCP basic tools -- good documentation available
- **Phase 2B:** LiteLLM routing, sentence-transformers embeddings -- mature libraries with clear docs

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All 28 packages verified against PyPI with current versions. Fallback paths documented for SQLModel and cedar-python risks. |
| Features | HIGH | Based on comprehensive analysis of 181 existing projects, 666 user comments, and 25 deep code audits. Feature categorization grounded in primary research. |
| Architecture | HIGH | Hexagonal + Outbox + Event Bus pattern is well-proven. Design doc includes detailed component responsibilities, data flows, and dependency maps. |
| Pitfalls | HIGH | 12 pitfalls sourced from official documentation (SQLite FTS5, LiteLLM Router, FastMCP) and ecosystem audit. Each includes specific warning signs and recovery strategies. |

**Overall confidence:** HIGH

### Gaps to Address

- **Cedar policy engine viability:** cedar-python 0.1.4 is very early. During Phase 2A planning, spike the binding to determine if it is production-ready or if a custom policy engine / Cedar CLI subprocess approach is needed. The PolicyEngine protocol abstraction must be in place before Guardian implementation.

- **CJK FTS5 tokenizer strategy:** The design doc targets Chinese-speaking users but defaults to `unicode61` tokenizer. During Phase 1 planning, decide whether to (a) build a jieba custom FTS5 tokenizer from the start, (b) use separate FTS5 tables per language, or (c) defer CJK support to Phase 4 with a documented migration path. Changing tokenizer requires full index rebuild.

- **SQLModel production readiness:** SQLModel 0.0.38 is pre-release. During Phase 1 implementation, validate that it handles the Claims DB query patterns correctly. If not, the fallback to SQLAlchemy Core for complex queries and Pydantic models for API schemas must be designed from the start.

- **Embedding model for technical content:** all-MiniLM-L6-v2 is the default for offline mode but performs poorly on code and technical jargon. During Phase 2B, benchmark hybrid search (BM25 + vector) on a representative technical document set to determine alpha weighting and whether a larger model is needed.

- **FSRS-to-wiki mapping:** FSRS is designed for flashcard review scheduling. Mapping it to wiki page freshness review requires design decisions (what constitutes a "review", how to handle multi-claim pages, how review results update confidence). This needs a design spike in Phase 2B.

## Sources

### Primary (HIGH confidence)
- PyPI API (pypi.org) -- all 28 package versions verified, 2026-04-26
- SQLite FTS5 Official Documentation (sqlite.org/fts5.html) -- external content tables, segment b-trees, automerge/crisismerge, tokenizer options
- LiteLLM Router Documentation (docs.litellm.ai) -- cooldowns, allowed_fails, routing strategies, exception mapping
- FastMCP Documentation (gofastmcp.com) -- v3 architecture, schema generation, tool registration
- Project design document (docs/smart_agent_wiki_design.md) -- full architecture, 5 engines, 4-layer storage, 23 appendix design decisions

### Secondary (MEDIUM confidence)
- Ecosystem analysis (docs/llm_wiki_ecosystem_analysis.md) -- 181-project categorization, feature coverage matrix, quality tiers
- Remote audit findings (docs/remote_project_audit_findings.md) -- 27 Tier 1 project deep audits with unique feature extraction
- User pain points (docs/karpathy_llm_wiki_comments.md) -- 666 comments with frequency analysis
- Karpathy's original concept (docs/llm-wiki.md) -- foundational pattern and user expectations
- Project list (docs/karpathy_llm_wiki_projects.md) -- 181 derivative project enumeration

### Tertiary (LOW confidence)
- cedar-python 0.1.4 binding -- very early stage, limited documentation, may need fallback
- SQLModel 0.0.x beta API stability -- pre-release, potential breaking changes
- A2A protocol specification -- referenced in design doc but implementation details sparse
- FSRS-to-wiki page mapping -- novel application of flashcard algorithm to knowledge management

---
*Research completed: 2026-04-26*
*Ready for roadmap: yes*
