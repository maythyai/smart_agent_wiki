# Architecture Research

**Domain:** Intelligent multi-agent knowledge management platform (LLM Wiki)
**Researched:** 2026-04-26
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
+=====================================================================+
|                        Driving Adapters                              |
|  CLI (Typer)  |  MCP Server  |  Web API  |  16+ Agent Compat Layer  |
+=======+============+==============+===========+======================+
        |            |              |           |
+=======v============v==============v===========v======================+
|                        API Gateway Layer                              |
|    Auth | Rate Limit | Route | Context Compile | Crypto Audit         |
+====+=======+============+==========+=========+=======================+
     |       |            |          |         |
+----v--+ +--v------+ +---v-----+ +--v------+ +v---------------------+
|Ingest | |Query    | |Govern   | |Learn    | |Collaborate           |
|Engine | |Engine   | |Engine   | |Engine   | |Engine                |
|       | |         | |+Cedar   | |+FSRS    | |+A2A/YAML/6 Agents    |
+----+--+ +--+------+ +--+------+------+ +--+--+----------+----------+
     |       |            |             |        |             |
+====v=======v============v=============v========v=============v========+
|                    Event Bus (asyncio.Queue + SQLite)                  |
+====+=======+============+=============+========+======================+
     |       |            |             |        |
+====v=======v============v=============v========v======================+
|                    Write Queue (Outbox Pattern)                        |
|         Durable SQLite outbox -> parallel dispatch to sinks            |
+====+=======+============+=============+========+=============+========+
     |       |            |             |        |             |
+----v---+ +-v--------+ +-v----------+ +-v------+v--+ +-------v------+
|Vault   | |Claims DB | |Wiki Pages | |FTS5    | |Vector| |WIP File |
|(Git)   | |(SQLite)  | |(Markdown) | |Index   | |(opt) | |(.yaml)  |
+--------+ +----------+ +-----------+ +--------+ +------+ +---------+
```

The system follows a **Hexagonal (Ports and Adapters) architecture**. Driving adapters (CLI, MCP, Web) call inward through domain protocols into the five engines. Engines write outward through a single Write Queue to multiple storage sinks. This separation means the same engine logic serves all user interfaces without duplication, and storage backends can be swapped without touching business logic.

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| **CLI (Typer)** | Primary developer interface. `init/ingest/query/lint/verify/status/prune` commands. 5-minute onboarding target. | Typer app with Rich output formatting. Calls engine layer directly. |
| **MCP Server (FastMCP)** | Agent integration protocol. 23 tools mapping 1:1 to engine operations. Enables Claude Code, Cursor, Copilot, Gemini CLI etc. | FastMCP 3.x `@mcp.tool` decorators wrapping engine protocols. Shares logic with CLI. |
| **Web API (FastAPI)** | HTTP + WebSocket interface for Web UI and programmatic access. 27 REST endpoints, cursor pagination, RFC 7807 errors. | FastAPI with Pydantic v2 models, uvicorn ASGI server. Shares engine layer with CLI/MCP. |
| **Ingest Engine** | Document intake pipeline: classify format, extract claims, fuse with existing knowledge, validate confidence, enqueue writes. | 5-stage pipeline. Structured data (code/JSON) uses zero-LLM AST parse. Unstructured data uses LiteLLM with multi-model competition. |
| **Query Engine** | Answer questions from the knowledge base with source provenance. 5 modes: direct search, graph traversal, reasoning chain, comparison, synthesis. | LiteLLM for answer generation. FTS5 + optional vector for retrieval. NetworkX for graph traversal. Context compilation with token budget. |
| **Govern Engine** | Trust and integrity. 4-layer confidence assessment, contradiction detection with 3 resolution strategies, 9-level freshness tracking, Cedar policy checks. | Contradiction detection via claim-to-claim comparison (temporal/factual/opinion classification). Confidence aggregation from per-claim source marks. |
| **Learn Engine** | Self-improvement. Training-period adaptation (30 days), FSRS spaced repetition, cognitive distillation to SOPs, knowledge expiry pruning, trend sensing. | FSRS library for spaced repetition. Feedback files (approved/rejected) injected into agent prompts. Pattern mining for SOP extraction. |
| **Collaborate Engine** | Multi-agent orchestration. 6 role-based agents (Librarian/Writer/Critic/Linker/Scholar/Guardian), A2A protocol, YAML workflow parser, gate evaluator. | YAML-defined workflows with step-by-step agent dispatch. Guardian is zero-LLM rules engine. Other agents use LiteLLM with model routing by task complexity. |
| **Write Queue** | Single write entry point for all mutations. Durable SQLite outbox with parallel dispatch to sinks. Guarantees at-least-once delivery via op_id dedup. | Outbox pattern: engine enqueues -> outbox persists in SQLite -> dispatcher fans out to Vault/Claims/Wiki/FTS5/Graph/Vector sinks. Failed writes retry with exponential backoff. |
| **Event Bus** | Async inter-engine communication. Decouples engines for eventual consistency. | asyncio.Queue for in-process, SQLite table for crash recovery. Events: ClaimsReady, ContradictionFound, FreshnessExpired, QueryCompleted, CoverageMiss, SOPDistilled, WriteFailed. |
| **Vault (L0)** | Immutable original document storage. Git version controlled. Never modified after ingest. | File system: `vault/{uuid}/original.ext`, `transcript.md`, `meta.yaml`. Auto git commit on ingest. |
| **Claims DB (L1)** | Structured knowledge assertions. 8 core tables + FTS5 virtual table. Confidence, source mark, freshness, temperature orthogonal axes. | SQLite with WAL mode, partial indexes, trigger-enforced soft delete. UUID primary keys. |
| **Wiki Pages (L2)** | Mutable markdown synthesis. Agent-edited pages with inline claim references. Entity/concept/summary page types. | Markdown files with YAML frontmatter in `wiki/` directory. `[^claim:uuid]` inline references to L1. |
| **Index (L3)** | Full-text and vector search indices. FTS5 default, LanceDB optional. Adaptive evolution (flat -> hierarchical -> indexed). | SQLite FTS5 with Porter stemmer + Unicode61 tokenizer for BM25. LanceDB + all-MiniLM-L6-v2 for vector. |

## Recommended Project Structure

```
smart_agent_wiki/
+-- src/saw/
|   +-- domain/                        # Core domain models + Protocol definitions
|   |   +-- protocols.py               # Engine interface protocols (IngestPipeline, QueryEngine, Governor, etc.)
|   |   +-- value_objects.py            # ClaimRef, WikiPageRef, Confidence, Freshness, SourceMark, etc.
|   |   +-- events.py                  # Domain events (ClaimsReady, ContradictionFound, etc.)
|   |   +-- exceptions.py              # Domain-specific exceptions
|   |   +-- claims.py                  # Claim, ClaimRelation, ClaimSource entity models
|   |   +-- wiki.py                    # WikiPage, PageType, WikiLink models
|   |   +-- entities.py                # Entity, EntityRelation models (knowledge graph nodes)
|   +-- engines/                       # Five engines (pure business logic, no I/O dependencies)
|   |   +-- ingest/
|   |   |   +-- pipeline.py            # Main IngestPipeline orchestrator
|   |   |   +-- classifier.py          # Format detection (AST/schema/text/PDF/audio/video)
|   |   |   +-- extractors/            # Format-specific extractors
|   |   |   |   +-- code_ast.py        # Zero-LLM AST extraction for code
|   |   |   |   +-- schema.py          # Zero-LLM schema extraction for JSON/tables
|   |   |   |   +-- llm_extract.py     # LLM-based extraction for unstructured text
|   |   |   |   +-- pdf.py             # PDF parsing with 3-tier fallback (Docling -> PyMuPDF)
|   |   |   |   +-- audio.py           # Whisper-based audio transcription
|   |   |   |   +-- url.py             # Web content extraction (trafilatura)
|   |   |   +-- fuser.py               # New-vs-existing claim comparison and fusion
|   |   |   +-- validator.py           # Post-extraction validation (dedup, completeness)
|   |   +-- query/
|   |   |   +-- engine.py              # Main QueryEngine with 5 query modes
|   |   |   +-- search.py              # BM25 + vector hybrid search
|   |   |   +-- graph_traverse.py      # NetworkX BFS/DFS traversal with 4-signal relevance
|   |   |   +-- compiler.py            # Context compilation with token budget
|   |   |   +-- compare.py             # Multi-page comparison logic
|   |   |   +-- synthesizer.py         # Multi-source synthesis generation
|   |   +-- govern/
|   |   |   +-- governor.py            # Main Governor orchestrator
|   |   |   +-- confidence.py          # 4-layer confidence assessment + aggregation
|   |   |   +-- contradiction.py       # Contradiction detection + 3-strategy resolution
|   |   |   +-- freshness.py           # 9-level freshness tracking + scoring
|   |   |   +-- blast_radius.py        # Impact analysis for proposed changes
|   |   |   +-- linter.py              # KB health checks (orphans, stale, broken links)
|   |   +-- learn/
|   |   |   +-- engine.py              # Main LearnEngine orchestrator
|   |   |   +-- adaptive.py            # 30-day training period preference learning
|   |   |   +-- fsrs_scheduler.py      # FSRS spaced repetition scheduling
|   |   |   +-- distiller.py           # Cognitive distillation -> SOP extraction
|   |   |   +-- expiry.py              # Knowledge expiry + pruning (tactical/strategic)
|   |   |   +-- trends.py              # Growth pattern monitoring, gap detection
|   |   |   +-- hot_cache.py           # High-frequency page pre-compilation
|   |   +-- collaborate/
|   |       +-- orchestrator.py        # Main CollaborateEngine orchestrator
|   |       +-- agents/                # 6 agent role implementations
|   |       |   +-- librarian.py       # Index + classification (Haiku)
|   |       |   +-- writer.py          # Page creation + editing (Sonnet)
|   |       |   +-- critic.py          # Quality review + contradiction (Sonnet)
|   |       |   +-- linker.py          # Cross-reference discovery (Haiku)
|   |       |   +-- scholar.py         # Deep reasoning + synthesis (Opus)
|   |       |   +-- guardian.py        # Policy + security (zero-LLM rules)
|   |       +-- workflow_parser.py     # YAML workflow definition parser
|   |       +-- scheduler.py           # Step-by-step agent dispatch with gates
|   +-- write_queue/
|   |   +-- queue.py                   # WriteQueue protocol + SQLite outbox implementation
|   |   +-- dispatcher.py              # Parallel sink dispatch with retry + dead letter
|   |   +-- sinks/                     # Sink implementations (Driven Adapters)
|   |       +-- vault_sink.py          # File system + git commit
|   |       +-- claims_sink.py         # SQLite Claims DB writes
|   |       +-- wiki_sink.py           # Markdown file writes
|   |       +-- fts5_sink.py           # FTS5 index updates
|   |       +-- graph_sink.py          # NetworkX graph persistence
|   |       +-- vector_sink.py         # LanceDB vector indexing (optional)
|   +-- event_bus/
|   |   +-- bus.py                     # EventBus: asyncio.Queue + SQLite persistence
|   |   +-- handlers.py               # Event handler registration and dispatch
|   +-- adapters/                      # Driven Adapters (infrastructure)
|   |   +-- storage/
|   |   |   +-- sqlite_connection.py   # SQLite connection pool with WAL + PRAGMA
|   |   |   +-- claims_repository.py   # Claims DB CRUD + complex queries
|   |   |   +-- vault_repository.py    # Vault file operations
|   |   |   +-- wiki_repository.py     # Wiki page read/write
|   |   +-- llm/
|   |   |   +-- router.py              # LiteLLM model routing (Haiku/Sonnet/Opus by task)
|   |   |   +-- prompts/               # YAML prompt templates with versioning
|   |   |   +-- cache.py               # 3-tier LLM response cache (exact/semantic/hot)
|   |   |   +-- embeddings.py          # sentence-transformers embedding generation
|   |   +-- parsers/
|   |   |   +-- pdf_parser.py          # 3-tier: Docling -> PyMuPDF fallback
|   |   |   +-- markdown_parser.py     # python-frontmatter + markdown-it-py
|   |   |   +-- html_parser.py         # BeautifulSoup4 + trafilatura
|   |   |   +-- code_parser.py         # AST parsing for Python/JS/TS/Rust
|   |   +-- crypto/
|   |       +-- ed25519.py             # PyNaCl signing and verification
|   |       +-- cedar_policy.py        # Cedar policy evaluation (via cedar-python or CLI fallback)
|   +-- drivers/                       # Driving Adapters (user-facing entry points)
|   |   +-- cli/
|   |   |   +-- main.py                # Typer app entry point
|   |   |   +-- commands/              # init, ingest, query, search, lint, verify, status, prune
|   |   +-- web/
|   |   |   +-- app.py                 # FastAPI application factory
|   |   |   +-- routes/                # API route handlers by engine
|   |   |   +-- middleware/            # Auth, CORS, error handling
|   |   |   +-- websocket.py           # WebSocket handler for real-time events
|   |   +-- mcp/
|   |       +-- server.py              # FastMCP server with 23 @mcp.tool definitions
|   +-- plugins/
|   |   +-- hooks.py                   # HookPoints enum for plugin extension
|   |   +-- loader.py                  # entry_points-based plugin discovery
|   +-- config/
|       +-- settings.py                # Pydantic Settings (saw.yaml + env vars)
|       +-- defaults.py                # Default configuration values
+-- web/                               # React 19 frontend (Phase 3)
|   +-- src/
|   |   +-- components/                # ui/, graph/, editor/, wiki/, search/, dashboard/
|   |   +-- stores/                    # Zustand: auth, graph, search, editor
|   |   +-- hooks/                     # Custom React hooks
|   |   +-- lib/                       # mcp-client.ts, api.ts
|   |   +-- pages/                     # Route pages
|   +-- src-tauri/                     # Tauri v2 desktop shell (Phase 4)
+-- tests/
|   +-- unit/                          # Engine unit tests (mocked adapters)
|   +-- integration/                   # Multi-engine integration tests
|   +-- e2e/                           # CLI and MCP end-to-end tests
|   +-- fixtures/                      # Sample documents, expected claims
+-- pyproject.toml                     # Build config, dependencies, entry points
+-- saw.yaml                           # User configuration (generated by `saw init`)
```

### Structure Rationale

- **domain/:** Contains pure Python Protocols and value objects with zero external dependencies. Engines depend on these protocols, not on each other's implementations. This is the innermost hexagon.
- **engines/:** Pure business logic organized by the five engine domains. Each engine folder is internally cohesive but communicates with other engines only through the event bus or direct protocol calls. No I/O code here -- engines receive dependencies via constructor injection.
- **write_queue/:** Isolated write path following the Outbox pattern. This is the single mutation entry point for all storage, ensuring no engine directly writes to databases or files. This boundary prevents partial writes and enables crash recovery.
- **adapters/:** All infrastructure code lives here. Storage, LLM, parsers, and crypto are behind adapter interfaces. Swapping SQLite for PostgreSQL means writing a new claims_repository adapter, not touching engine code.
- **drivers/:** Three driving adapters (CLI, Web, MCP) share the same engine layer. Adding a new interface (e.g., Obsidian plugin) means adding a new driver, not modifying engines.
- **plugins/:** Entry-points-based extension system. External packages can register hooks at defined extension points (e.g., custom parsers, custom agent behaviors) without modifying core code.

## Architectural Patterns

### Pattern 1: Hexagonal Architecture (Ports and Adapters)

**What:** The core domain (engines + protocols) has no knowledge of external systems. All I/O flows through adapter interfaces (ports). Driving adapters (CLI/MCP/Web) call inward. Driven adapters (storage/LLM/parsers) are called outward.

**When to use:** This pattern is the right choice for Smart Agent Wiki because the system has multiple user-facing entry points (3 confirmed, 16+ agent compat layer) and multiple storage backends (SQLite, optional PostgreSQL, optional vector DB). Without this pattern, swapping one storage backend or adding one new interface would require changes across the codebase.

**Trade-offs:**
- Pro: Each engine can be tested in complete isolation with mocked adapters.
- Pro: New entry points (Obsidian plugin, team API) are just new drivers.
- Pro: Storage migration (SQLite to PostgreSQL) is a new adapter, zero engine changes.
- Con: More indirection layers than a simple script. Overkill for Phase 1A but pays off starting Phase 1B when MCP joins CLI.
- Con: Requires discipline to keep engines pure (no `import sqlite3` in engine code).

**Example:**
```python
# domain/protocols.py -- Port definition
from typing import Protocol

class ClaimsRepository(Protocol):
    def get_by_id(self, uuid: str) -> Claim | None: ...
    def search(self, query: str, limit: int) -> list[Claim]: ...
    def insert(self, claim: Claim) -> str: ...

class IngestPipeline(Protocol):
    def ingest(self, source: Source, options: IngestOptions) -> IngestResult: ...

# adapters/storage/claims_repository.py -- Adapter implementation
import sqlite3
class SQLiteClaimsRepository:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path))
    def get_by_id(self, uuid: str) -> Claim | None:
        row = self._conn.execute("SELECT * FROM claim WHERE uuid=?", (uuid,)).fetchone()
        return Claim.from_row(row) if row else None

# engines/ingest/pipeline.py -- Engine uses port, not adapter
class IngestPipelineImpl:
    def __init__(self, claims: ClaimsRepository, write_queue: WriteQueue):
        self._claims = claims
        self._write_queue = write_queue
```

### Pattern 2: Write Queue / Outbox Pattern

**What:** All mutations to storage go through a single Write Queue. The engine enqueues a write operation to a durable SQLite outbox table. A dispatcher picks up pending operations and fans them out to multiple sinks (Vault, Claims, Wiki, FTS5, Graph, Vector) in parallel. Each sink is independently retried on failure.

**When to use:** Any time the system writes to more than one storage location and those writes must not be lost. In Smart Agent Wiki, every ingest creates writes to at least 3 sinks (Vault + Claims + FTS5). Without the outbox, a crash between Claims write and FTS5 update would leave the system in an inconsistent state.

**Trade-offs:**
- Pro: Crash-safe. The outbox is written to SQLite before any storage operation. If the process dies, the dispatcher resumes from the outbox on restart.
- Pro: Sink failures are isolated. If LanceDB is down, Vault and Claims still get written. The failed operation retries independently.
- Pro: Natural fit for the event-driven architecture -- outbox entries can also be published as domain events.
- Con: Eventual consistency between sinks. The Claims DB might be updated before the FTS5 index. For a personal knowledge tool, this delay (typically < 1 second) is acceptable.
- Con: Requires op_id deduplication in sinks to handle retry-at-least-once semantics.

**Example:**
```python
# write_queue/queue.py
@dataclass
class WriteOp:
    op_id: str           # UUID, used for dedup
    session_id: str      # Groups related writes
    sink_name: str       # "vault" | "claims" | "fts5" | ...
    payload: dict        # Sink-specific data
    status: str          # "pending" | "dispatched" | "done" | "failed"
    retry_count: int
    created_at: datetime

class WriteQueueImpl:
    def enqueue(self, ops: list[WriteOp]) -> None:
        """Atomically insert all ops for a session. All-or-nothing."""
        with self._conn:
            for op in ops:
                self._conn.execute(
                    "INSERT INTO write_outbox (op_id, session_id, sink_name, payload, status) "
                    "VALUES (?, ?, ?, ?, 'pending')",
                    (op.op_id, op.session_id, op.sink_name, json.dumps(op.payload))
                )

    def enqueue_atomic(self, ops: list[WriteOp]) -> None:
        """Same as enqueue, but also dispatches atomically."""
        self.enqueue(ops)
        self.dispatcher.dispatch_pending()
```

### Pattern 3: Hybrid Communication (60% Direct + 40% Event-Driven)

**What:** Engines communicate via two modes. Synchronous operations that need return values use direct Python function calls through protocol interfaces. Fire-and-forget operations that trigger downstream processing use the event bus.

**When to use:** Direct calls for orchestration (Collaborate -> Agent execution), validation (Ingest -> Govern confidence check), and query compilation (Query -> Learn hot cache). Events for side effects (ClaimsReady -> trigger governance evaluation, CoverageMiss -> trigger Research-on-Miss auto-ingest).

**Trade-offs:**
- Pro: Simpler than full event-driven for the 60% of calls that need synchronous responses.
- Pro: Event bus enables loose coupling for the 40% of operations where eventual consistency is fine.
- Pro: Engines remain independently testable. Tests use direct calls for assertions and mock the event bus for side effects.
- Con: Two communication patterns means developers must decide which to use for each new interaction. The rule of thumb: if the caller needs the result, use direct call; if the callee just needs to eventually react, use event.

**Direct call map:**
```
Collaborate -> Ingest/Query/Govern   (orchestration needs results)
Query       -> Learn                 (compilation needs hot cache data)
Ingest      -> Govern                (validation needs confidence assessment)
Agent       -> Guardian              (policy check is synchronous gate)
Agent       -> WriteQueue            (enqueue is synchronous write to outbox)
```

**Event flow map:**
```
Ingest   --[ClaimsReady]---------> Govern      (trigger confidence evaluation)
Govern   --[ContradictionFound]--> Learn        (trigger FSRS/reinforcement update)
Govern   --[FreshnessExpired]----> Learn        (add to review queue)
Query    --[QueryCompleted]------> Learn        (update hot cache + query patterns)
Query    --[CoverageMiss]--------> Ingest       (trigger Research-on-Miss)
Learn    --[SOPDistilled]--------> Collaborate  (inject SOP into agent context)
WriteQueue --[WriteFailed]-------> Govern       (audit log entry)
```

### Pattern 4: Local-First Progressive Degradation

**What:** The system operates at three capability tiers based on available resources. Full-featured mode (LLM + embeddings + vector search). Lightweight mode (LLM only, BM25 search). Offline mode (BM25 + TF-IDF only, no LLM). The wiki never becomes a "read-only ruin" -- even fully offline, users can search, browse, and add Markdown content.

**When to use:** This pattern is critical for a personal knowledge tool because users may be on airplanes, in areas with poor connectivity, or running on resource-constrained machines. The system must degrade gracefully rather than fail.

**Trade-offs:**
- Pro: User trust. Knowledge is always accessible regardless of network state.
- Pro: Cost control. Offline mode costs $0/day. Lightweight mode can use cheaper models.
- Pro: Natural testing strategy. Each tier can be tested independently.
- Con: Feature parity testing. Every feature must be validated at each tier. Does search work without vector? Does ingest work without LLM? This triples the test matrix for cross-cutting features.
- Con: Some features degrade to no-ops. Contradiction detection requires LLM, so it is skipped in offline mode. Confidence assessment degrades to automatic (no cross-validation possible).

## Data Flow

### Ingest Flow

```
User: saw ingest paper.pdf
       |
       v
CLI Driver --> IngestPipeline.ingest(source=file, path=paper.pdf)
       |
       v
Classifier: PDF detected --> choose PDF parser path
       |
       v
Extractor: Docling/PyMuPDF --> raw text + structure
       |
       v
LLM Extract: Sonnet extracts claims + entities + relations
       |  (or: AST parse for code, schema parse for JSON -- zero LLM)
       v
Fuser: compare new claims vs existing Claims DB
       |  -> no conflict: mark for direct insert
       |  -> conflict found: emit ContradictionFound event
       v
Validator: dedup (content_hash), completeness check
       |
       v
Govern.confidence: assign initial confidence (Layer 1: Unverified)
       |
       v
WriteQueue.enqueue_atomic([
   op("vault", store_original_pdf),
   op("claims", insert_claims),
   op("fts5", update_search_index),
   op("graph", update_entities_and_relations),
])
       |
       v
Dispatcher -> parallel write to all sinks
       |
       v
EventBus.publish(ClaimsReady, claim_ids=[...])
       |
       v
[Async] Govern assesses confidence, Learns updates hot cache
```

### Query Flow

```
User: saw query "Why did Transformer replace RNN?"
       |
       v
CLI Driver --> QueryEngine.query(question, mode=auto, depth=L3)
       |
       v
Intent Recognition (Haiku): classify query type
       |  -> "comparative reasoning" --> choose reasoning mode
       v
Context Compilation:
  1. FTS5 search for "Transformer", "RNN" --> candidate claims
  2. Graph traverse from Transformer entity --> related entities
  3. Learn.hot_cache --> pre-compiled high-frequency pages
  4. Token budget filter: prioritize high-confidence, high-relevance claims
       |
       v
LLM Generate (Opus): synthesize answer from compiled context
       |
       v
Response: {
    answer: "...",
    sources: [{claim_uuid, content, confidence, vault_uuid, page: 5, paragraph: 2}],
    related_pages: ["transformer", "rnn", "attention-mechanism"],
    meta: {model: "opus", tokens: 1850, cost: $0.012, coverage: 0.82}
}
       |
       v
EventBus.publish(QueryCompleted) --> Learn updates hot cache
       |
       v
If coverage < 0.5: EventBus.publish(CoverageMiss) --> Ingest triggers Research-on-Miss
```

### Governance Flow (Contradiction Resolution)

```
Ingest detects new claim contradicts existing claim
       |
       v
EventBus.publish(ClaimsReady) --> Govern.contradiction_detected()
       |
       v
Contradiction Classifier (Sonnet): classify as temporal | factual | opinion
       |
       v
Strategy Selection:
  temporal --> Superseded (new data wins, old marked historical)
  factual  --> Historical (both preserved, flagged for human review)
  opinion  --> Disputed (both preserved, readers see both perspectives)
       |
       v
WriteQueue.enqueue_atomic([
    op("claims", update_claim(old, status=superseded)),
    op("claims", update_claim(new, confidence=3)),
    op("claims", insert_contradiction_record),
])
       |
       v
If factual: escalate to human review queue
If temporal/opinion: auto-resolve + EventBus.publish(ContradictionFound) --> Learn
```

### Key Data Flows

1. **Ingest -> Write -> Index:** The critical write path. Document enters through any driver, flows through Ingest engine's 5-stage pipeline, enqueues atomic writes to Vault+Claims+FTS5, and fires ClaimsReady event for downstream processing. Total latency target: < 30 seconds for a 10-page PDF.

2. **Query -> Compile -> LLM -> Answer:** The critical read path. Query enters through any driver, triggers context compilation (FTS5 search + graph traversal + hot cache), feeds compiled context to LLM, returns answer with source provenance chain (answer -> claim -> vault document -> page number). Total latency target: < 10 seconds for a standard query.

3. **Contradiction -> Classify -> Resolve -> Notify:** The governance loop. New claims are compared against existing claims during ingest. Contradictions are classified (temporal/factual/opinion) and resolved with appropriate strategy. Factual contradictions escalate to human review; others auto-resolve. The Learn engine receives the outcome for spaced repetition reinforcement.

4. **Feedback -> Learn -> Adapt:** The self-improvement loop. User approves/rejects agent outputs. The Learn engine records feedback patterns, extracts SOPs via cognitive distillation, and injects learned preferences back into agent system prompts. Over 30 days, the system transitions from "asking questions" to "quietly executing."

## Build Order (Dependency-Based)

The build order follows the 21-week roadmap, with each phase building on capabilities from the previous phase. Components are listed in dependency order within each phase.

```
Phase 1A: Core Cycle (Weeks 1-4)
=================================
1. domain/ (protocols, value_objects, events, exceptions)
   -- Everything depends on this. Pure Python, no I/O.
2. adapters/storage/ (sqlite_connection, claims_repository)
   -- Engines need storage to work.
3. write_queue/ (queue, dispatcher, sinks: vault, claims, fts5)
   -- Engines need write path to persist results.
4. engines/ingest/ (classifier, extractors/markdown+url, fuser, validator)
   -- First engine. Can test end-to-end with domain + storage + write_queue.
5. engines/query/ (search, compiler)
   -- Depends on Claims DB being populated by Ingest.
6. engines/govern/ (confidence baseline only)
   -- Confidence is assessed during ingest.
7. drivers/cli/ (init, ingest, query, search, lint)
   -- First driving adapter. Enables `saw init && saw ingest doc.md && saw query "..."`.
   -- VERIFICATION: init -> ingest -> query < 5 minutes.

Phase 1B: Infrastructure (Weeks 5-7)
=====================================
8. engines/ingest/extractors/pdf (Docling + PyMuPDF fallback)
   -- Extends Ingest with PDF support.
9. adapters/parsers/ (pdf_parser, html_parser)
   -- Parser adapters for new formats.
10. adapters/crypto/ (ed25519 basic)
    -- Signing for audit trail.
11. write_queue/ improvements (retry, dead letter queue)
    -- Production hardening of write path.
12. drivers/mcp/ (5 tools: ingest/query/search/lint/status)
    -- Second driving adapter. Shares engine layer with CLI.
    -- VERIFICATION: MCP tools work via Claude Code / Cursor.

Phase 2A: Governance (Weeks 8-11)
==================================
13. engines/govern/ (full: confidence, contradiction, freshness, blast_radius)
    -- Full governance engine. Depends on mature Claims DB.
14. adapters/crypto/ (cedar_policy)
    -- Policy engine for agent authorization.
    -- WARNING: cedar-python binding is early-stage. May need CLI fallback.
15. drivers/cli/ (verify, conflicts commands)
    -- New CLI commands for governance operations.
    -- VERIFICATION: Contradiction detection rate > 80%.

Phase 2B: Learning + Full MCP (Weeks 12-15)
============================================
16. engines/learn/ (adaptive, fsrs_scheduler, distiller, expiry, trends)
    -- Learning engine. Depends on having user behavior data (requires Phase 1+2 runtime).
17. engines/ingest/extractors/llm_extract (multi-LLM competition)
    -- Dual-LLM extraction for cross-validation.
18. drivers/mcp/ (full 23 tools)
    -- Complete MCP tool set.
    -- VERIFICATION: 3 external users, 7-day retention > 40%.

Phase 3: Collaboration + Visualization (Weeks 16-21)
=====================================================
19. engines/collaborate/ (agents/, workflow_parser, scheduler)
    -- Multi-agent engine. Depends on all other engines being functional.
20. adapters/llm/ (full model routing with Haiku/Sonnet/Opus)
    -- Multi-model routing for agent roles.
21. adapters/storage/ (vector_sink with LanceDB)
    -- Optional vector search.
22. web/ (React frontend)
    -- Third driving adapter. Depends on all engines and Web API.
23. drivers/web/ (full 27 endpoints + WebSocket)
    -- Full Web API with real-time updates.
    -- VERIFICATION: Multi-agent workflow runs end-to-end.
```

**Key dependency insight:** The Ingest engine is the foundation. Everything flows from the ability to take in documents and produce structured claims. Query depends on claims. Governance depends on claims. Learning depends on user interactions with claims and query results. Collaboration depends on all engines. This is why Ingest + Claims DB + Write Queue must be solid before anything else.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **Personal (< 1K pages, < 50K claims)** | Current architecture as designed. SQLite handles this trivially. Single-process, asyncio concurrency. FTS5 flat index mode. Total memory footprint < 200MB. |
| **Power user (1K-10K pages, 50K-500K claims)** | Enable hierarchical index mode (auto-detected). Add LanceDB for vector search. Hot cache becomes important. Consider WAL checkpoint tuning. NetworkX graph still fine in-memory. |
| **Small team (10K-100K pages, 500K-5M claims)** | Migrate to PostgreSQL + pgvector. SQLite -> PostgreSQL adapter swap. Add connection pooling. Consider graph partitioning for NetworkX (or evaluate iGraph). Docker Compose deployment. |
| **Large org (> 100K pages)** | Out of scope for current design. Would need microservice decomposition, separate graph database, distributed search. This is firmly Phase 4+ territory. |

### Scaling Priorities

1. **First bottleneck: FTS5 search quality at > 200 pages.** Flat FTS5 index returns too many results. Mitigation: adaptive index evolution (flat -> hierarchical -> indexed with concept clustering). Auto-detected by the Learn engine's trend sensing.

2. **Second bottleneck: LLM token cost at scale.** Each ingest uses LLM tokens; each query uses LLM tokens. Mitigation: zero-LLM structured extraction saves ~60% of ingest tokens. Hot cache eliminates re-compilation of frequent queries. Three-tier caching (exact match -> semantic -> session) reduces redundant LLM calls.

3. **Third bottleneck: Write Queue throughput under batch ingest.** Ingesting 100 documents simultaneously creates write pressure. Mitigation: batch write_queue.enqueue_atomic() groups operations by session. SQLite WAL mode handles concurrent readers. Dispatcher parallelizes sink writes.

4. **Fourth bottleneck: NetworkX graph traversal at > 100K entities.** Pure Python graph library has limits. Mitigation: Phase 4 evaluation of iGraph (C core) or dedicated graph database. For Phase 1-3, NetworkX with lazy loading of subgraphs is sufficient.

## Anti-Patterns

### Anti-Pattern 1: Engine-to-Engine Direct Import

**What people do:** `from saw.engines.ingest import IngestEngine` inside QueryEngine code. Engine A directly imports and instantiates Engine B.

**Why it is wrong:** Engines become tightly coupled. Testing Engine A requires Engine B to be real (or manually mocked). Changing Engine B's interface breaks Engine A. The hexagonal boundary is violated.

**Do this instead:** Engines communicate through domain Protocols (for synchronous calls) or through the Event Bus (for async side effects). The application composition root (in drivers/) wires engines together via dependency injection.

```python
# WRONG: direct import between engines
# query/engine.py
from saw.engines.learn import LearnEngine  # tight coupling

# CORRECT: protocol-based dependency injection
# domain/protocols.py
class LearnProvider(Protocol):
    def get_hot_cache(self, topic: str) -> list[CompiledPage]: ...

# query/engine.py
class QueryEngineImpl:
    def __init__(self, learn: LearnProvider):  # depends on protocol, not implementation
        self._learn = learn
```

### Anti-Pattern 2: Bypassing Write Queue

**What people do:** An engine directly writes to SQLite or the filesystem because "it is faster" or "it is just one write."

**Why it is wrong:** The Write Queue guarantees atomicity, crash recovery, and auditability. A direct write bypasses all of these. If the process crashes between a direct Vault write and the Claims write that should accompany it, the knowledge base is in an inconsistent state. Also, direct writes are invisible to the audit layer.

**Do this instead:** Every mutation goes through `WriteQueue.enqueue()`. The engine produces write operations; the Write Queue executes them. If latency is critical, use `enqueue_atomic()` which dispatches immediately after enqueuing.

### Anti-Pattern 3: Giant God Engine

**What people do:** The Ingest engine grows to include search logic, confidence assessment, and wiki page generation because "they are all related to processing a document."

**Why it is wrong:** The five engines exist for a reason. Ingest takes documents in. Govern assesses trust. Query answers questions. Learn improves the system. Collaborate orchestrates agents. Merging responsibilities creates a monolith that is impossible to test in isolation and impossible for one person to hold in their head.

**Do this instead:** Ingest produces claims and fires ClaimsReady. Govern listens to ClaimsReady and assesses confidence. If Ingest needs a synchronous confidence check (e.g., to decide whether to proceed with ingest), it calls Govern through the protocol interface. But Govern owns the confidence logic, not Ingest.

### Anti-Pattern 4: LLM in Every Code Path

**What people do:** Every operation calls an LLM -- search ranking, deduplication, format detection, link discovery, even counting claims.

**Why it is wrong:** LLM calls cost money, add latency, and introduce non-determinism. The design explicitly identifies 15+ operations that should never touch an LLM (AST parsing, BM25 scoring, freshness calculation, Cedar policy check, Ed25519 signing, content hash dedup, etc.). Over-using LLM also makes the system unusable in offline mode.

**Do this instead:** Follow the "zero-LLM by default" principle. Use LLM only when structural extraction is impossible (unstructured text). Code -> AST. JSON/tables -> schema. Search -> BM25/TF-IDF. Policy -> Cedar rules. Signatures -> Ed25519. Reserve LLM for: claim extraction from prose, query answering, contradiction classification, synthesis generation, and cognitive distillation.

### Anti-Pattern 5: SQLite as Afterthought

**What people do:** Treat SQLite as a "simple file database" and skip proper PRAGMA configuration, index design, and migration strategy.

**Why it is wrong:** SQLite with default settings is 10-100x slower than properly configured SQLite for knowledge management workloads. Without WAL mode, concurrent reads block writes. Without mmap, large result sets are slow. Without proper indexes, FTS5 queries degrade at scale.

**Do this instead:** Apply the PRAGMA configuration from day one (WAL mode, 64MB cache, 64MB mmap, NORMAL sync, 5s lock wait). Design partial indexes for the soft-delete pattern (`WHERE deleted_at IS NULL`). Use the Claims schema DDL as the reference implementation. Test with realistic data volumes from the start.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **LLM APIs (100+ providers)** | LiteLLM unified interface. All engine LLM calls go through adapters/llm/router.py. Model selection by task complexity: Haiku (classify/search), Sonnet (extract/write/review), Opus (reason/synthesize). | LiteLLM handles retry, fallback, rate limiting, cost tracking. Configure in saw.yaml under `llm.models.*`. Three-tier cache prevents redundant calls. |
| **Embedding model** | sentence-transformers local model (all-MiniLM-L6-v2, 80MB). No API required. Optional swap to OpenAI embeddings via LiteLLM. | Default model is privacy-safe (local only). Vector search is optional; system works with BM25 alone. |
| **Git** | pygit2 (libgit2 binding) for blame-based provenance. subprocess git for Vault auto-commit. | Vault auto-commits on every ingest. Git blame links Wiki edits to processing sessions. Requires git installed on system. |
| **Cedar Policy Engine** | cedar-python binding (PyO3 wrapper). Fallback: subprocess call to Cedar CLI if binding fails. | **RISK:** cedar-python is v0.1.4, early stage. Architecture must support graceful fallback to simpler rule engine if Cedar binding proves unreliable. |
| **PDF Parsing** | 3-tier fallback: Docling (best quality) -> PyMuPDF (fast fallback). | Docling is primary; PyMuPDF is always available as zero-dependency fallback. MinerU reserved for Phase 4 (heavy dependency chain). |
| **Audio/Video** | faster-whisper for transcription. Optional: not included in Phase 1-2. | CTranslate2 backend, 4x faster than openai-whisper. Audio files stored in Vault, transcript in Vault alongside original. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Drivers <-> Engines** | Direct call via Protocol interface. Drivers instantiate engines via dependency injection in composition root. | All three drivers (CLI/MCP/Web) share the same engine instances. No per-driver engine duplication. |
| **Engines <-> Write Queue** | Direct call. Engines call `write_queue.enqueue()` synchronously. Queue persists to SQLite outbox, returns immediately. | Engines never touch storage directly. Write Queue is the single mutation path. |
| **Engines <-> Event Bus** | Publish/subscribe. Engines publish events. Other engines subscribe to events they care about. | Fire-and-forget. No return values. Used for eventual consistency side effects. |
| **Write Queue <-> Sinks** | Direct call via Sink protocol. Dispatcher calls each sink's `write()` method in parallel. | Each sink is independent. Failure in one sink does not block others. Retries are per-sink with exponential backoff. |
| **Engines <-> Adapters (LLM/Parsers)** | Direct call via Protocol. Engines receive adapter instances via constructor injection. | Adapters are swappable. Mock adapters for testing. Real adapters for production. |
| **Event Bus <-> Write Queue** | EventBus publishes WriteFailed events when a sink exhausts retries. Govern subscribes to WriteFailed for audit logging. | The event bus and write queue are complementary, not competing. Write Queue handles synchronous writes; Event Bus handles async notifications about write outcomes. |

## Critical Architecture Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **cedar-python binding immaturity (v0.1.4)** | HIGH | Architecture must support Cedar CLI subprocess fallback or a simplified custom policy engine. Do not deeply couple Guardian agent to cedar-python API. Abstract behind PolicyEngine protocol. |
| **SQLite write contention under batch ingest** | MEDIUM | WAL mode + 5s lock wait timeout mitigates most contention. For extreme batch loads, serialize writes through Write Queue (which already does this). |
| **SQLModel 0.0.x beta status** | MEDIUM | Critical data paths (Claims repository) should use SQLAlchemy Core directly as fallback. SQLModel for simple CRUD, Core for complex queries. |
| **LLM API cost escalation** | MEDIUM | Zero-LLM structured extraction for 60% of operations. Three-tier cache. Model routing (Haiku for volume, Opus only when needed). Daily cost tracking in LiteLLM. |
| **Eventual consistency window between sinks** | LOW | For personal use, the window is sub-second. Users will not notice. If it becomes visible, add a polling-based consistency check in `saw lint`. |

## Sources

- Design document: `docs/smart_agent_wiki_design.md` -- Full architecture with 5 engine specifications, 4-layer storage, 23 appendix design decisions
- Optimization document: `docs/smart_agent_wiki_optimization.md` -- Hexagonal Architecture recommendation, engine data flow, directory structure, Protocol definitions, 21-week roadmap
- Claims Schema: `docs/claims_schema.sql` -- SQLite DDL with PRAGMA optimization, 8 core tables, partial indexes, trigger-enforced soft delete
- API Contract: `docs/api_contract.md` -- 27 REST endpoints, WebSocket protocol, MCP tool mapping
- Ecosystem Analysis: `docs/llm_wiki_ecosystem_analysis.md` -- 181-project architecture pattern analysis
- Remote Audit: `docs/remote_project_audit_findings.md` -- Deep audit of 25 reference projects
- Stack Research: `.planning/research/STACK.md` -- Technology recommendations with version compatibility
- Feature Research: `.planning/research/FEATURES.md` -- Feature landscape with dependencies and MVP recommendation

---
*Architecture research for: Smart Agent Wiki (intelligent multi-agent knowledge platform)*
*Researched: 2026-04-26*
