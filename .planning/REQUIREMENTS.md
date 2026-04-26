# Requirements: Smart Agent Wiki

**Defined:** 2026-04-26
**Core Value:** 知识可信、可溯源、可进化 — 每一条回答都可以追溯到原始文档的具体位置

## v1 Requirements

### Storage

- [ ] **STOR-01**: User can initialize a wiki with `saw init` creating Vault, Claims DB, Wiki, and Index layers
- [ ] **STOR-02**: Raw documents are stored immutably in Vault with UUID directories (original file + transcript + metadata)
- [ ] **STOR-03**: Structured knowledge claims are extracted and stored in Claims SQLite DB with source provenance (UUID + page location)
- [ ] **STOR-04**: Wiki pages are generated as Markdown with YAML frontmatter (type, tags, confidence, freshness)
- [ ] **STOR-05**: Full-text index (FTS5) is automatically built and maintained for all Wiki pages
- [ ] **STOR-06**: Every claim traces back to Vault source via `source_uuid` (document → page number / timestamp / line number)
- [ ] **STOR-07**: Write Queue (Outbox) ensures all mutations flow through a single durable entry point with per-sink tracking

### Ingestion

- [ ] **INGE-01**: User can ingest Markdown files with LLM-based entity, concept, and claim extraction
- [ ] **INGE-02**: User can ingest PDF documents via 3-tier fallback parser (MinerU → Docling → PyMuPDF)
- [ ] **INGE-03**: User can ingest web pages via URL with content extraction
- [ ] **INGE-04**: Structured data (code/JSON/tables) is extracted using AST/schema parsing with zero LLM calls
- [ ] **INGE-05**: Unstructured data is extracted by 2 independent LLMs for cross-validation to reduce hallucination
- [ ] **INGE-06**: Ingestion produces structured claims written to Claims DB, entity pages as Wiki drafts, and Graph updates
- [ ] **INGE-07**: Each ingestion creates a session branch for git blame dual provenance chain

### Query

- [ ] **QUER-01**: User can search the knowledge base via BM25 + FTS5 full-text search
- [ ] **QUER-02**: User can perform structure-aware Tree Mode search for hierarchical documents (academic papers, technical docs)
- [ ] **QUER-03**: User can query the knowledge base in natural language and receive layered answers (L1 title, L2 summary, L3 conclusions, L4 full text)
- [ ] **QUER-04**: Context compilation assembles relevant Wiki pages within token budget, prioritizing high-confidence and high-relevance content
- [ ] **QUER-05**: Query results include inline citations linking to specific claims and Vault sources
- [ ] **QUER-06**: Graph traversal (BFS/DFS) enables exploratory research across entity relationships
- [ ] **QUER-07**: Comparison analysis identifies similarities and differences between two or more Wiki pages

### Governance

- [ ] **GOVE-01**: Each Wiki page has a 4-tier confidence level (Unverified → Single Source → Cross-Validated → Human Verified)
- [ ] **GOVE-02**: Each claim has a 3-level source marking (extracted / inferred / ambiguous) orthogonal to page confidence
- [ ] **GOVE-03**: Contradiction detection identifies temporal, opinion, and factual conflicts between claims
- [ ] **GOVE-04**: Conflicts are resolved via 3 strategies: Superseded (temporal), Disputed (opinion), Historical (factual + human review)
- [ ] **GOVE-05**: 9-level freshness system tracks knowledge staleness with color-coded indicators (green/yellow/orange/red)
- [ ] **GOVE-06**: Health check (`saw lint`) detects contradictions, orphan pages, broken links, missing metadata, and stale claims
- [ ] **GOVE-07**: Blast radius analysis shows downstream impact before modifying a Wiki page
- [ ] **GOVE-08**: Cryptographic audit generates Ed25519 signed receipts for all agent operations (offline-verifiable)

### Learning

- [ ] **LEARN-01**: Training period (first 30 days) learns user's knowledge organization preferences automatically
- [ ] **LEARN-02**: FSRS-based spaced repetition schedules review for high-freshness (level 7-8) pages
- [ ] **LEARN-03**: Cognitive distillation (Echo) extracts SOPs from user feedback patterns across sessions
- [ ] **LEARN-04**: Knowledge expiry classifies and prunes tactical knowledge (30-day auto-expiry) while preserving strategic knowledge
- [ ] **LEARN-05**: Trend sensing monitors growth patterns and suggests synthesis pages for knowledge gaps
- [ ] **LEARN-06**: Dual feedback files (approved.yaml + rejected.yaml) provide positive/negative behavioral reinforcement to agents

### Collaboration

- [ ] **COLL-01**: 6 specialized agents with distinct roles: Librarian(Haiku), Writer(Sonnet), Critic(Sonnet), Linker(Haiku), Scholar(Opus), Guardian(rules)
- [ ] **COLL-02**: Agents are dispatched per-task with model routing (Haiku for high-frequency/low-cost, Sonnet for quality, Opus for deep reasoning)
- [ ] **COLL-03**: YAML workflow orchestration allows users to define multi-step agent workflows with gate conditions
- [ ] **COLL-04**: Cedar-based policy engine defines permit/forbid rules per agent per tool
- [ ] **COLL-05**: A2A protocol enables inter-agent communication and task handoff

### CLI

- [ ] **CLI-01**: User can run `saw init` to create an empty wiki with all storage layers
- [ ] **CLI-02**: User can run `saw ingest <source>` to ingest documents, URLs, or directories
- [ ] **CLI-03**: User can run `saw query <question>` to query the knowledge base in natural language
- [ ] **CLI-04**: User can run `saw search <keywords>` for BM25/FTS5 keyword search
- [ ] **CLI-05**: User can run `saw lint` to perform health check on the knowledge base
- [ ] **CLI-06**: User can run `saw verify <claim>` to verify a specific claim's provenance
- [ ] **CLI-07**: User can run `saw status` to see knowledge base overview (pages, claims, freshness, confidence distribution)
- [ ] **CLI-08**: User can run `saw conflicts` to list detected contradictions
- [ ] **CLI-09**: User can run `saw freshness` to get freshness report
- [ ] **CLI-10**: User can run `saw review` to trigger human review workflow
- [ ] **CLI-11**: User can run `saw audit` to verify Ed25519 receipt chain integrity

### MCP Server

- [ ] **MCP-01**: MCP server exposes 23 tools covering ingest, query, govern, learn, and collaborate operations
- [ ] **MCP-02**: MCP server works with Claude Code, Cursor, Copilot, and other MCP-compatible agents
- [ ] **MCP-03**: 16+ agent compatibility layer generates agent-specific config files via `saw init --agent <name>`

### Web UI

- [ ] **WEB-01**: Web UI provides search interface for querying the knowledge base
- [ ] **WEB-02**: Knowledge graph visualization via Cytoscape.js enables visual exploration of entity relationships
- [ ] **WEB-03**: Wiki page editor (Milkdown) allows review, approve, reject, and edit of LLM-generated pages

### Cross-Cutting

- [ ] **XCUT-01**: Git integration auto-commits on ingestion and edits with session branch tracking
- [ ] **XCUT-02**: Multi-LLM support via LiteLLM provides unified interface to 100+ providers with fallback/retry
- [ ] **XCUT-03**: Three-tier degradation ensures system remains usable: full (LLM+embeddings) → lightweight (LLM only) → offline (BM25+TF-IDF)
- [ ] **XCUT-04**: WIP file (.saw/wip.yaml) captures cross-session work momentum (active tasks, next steps, pending questions)
- [ ] **XCUT-05**: Progressive memory depth reduces boot tokens from ~20K to ~8-10K (L0 always-loaded, L1 summaries, L2 full content)
- [ ] **XCUT-06**: Adaptive index evolves automatically: flat (≤50 pages) → hierarchical (≤200) → indexed (>200)
- [ ] **XCUT-07**: Local-first with zero external dependencies by default; cloud LLM and vector search are opt-in enhancements
- [ ] **XCUT-08**: Research-on-Miss triggers parallel web/academic/code search when query coverage falls below threshold

## v2 Requirements

### Extended Ingestion

- **INGE-08**: Video ingestion with audio extraction via Whisper transcription
- **INGE-09**: Audio ingestion (podcasts, lectures) with Whisper transcription
- **INGE-10**: Chrome clipper extension for one-click web page capture
- **INGE-11**: RSS feed subscription for automated periodic ingestion
- **INGE-12**: Real-time meeting transcription (Soniox/Whisper)

### Extended Collaboration

- **COLL-06**: Obsidian plugin for bidirectional sync with Obsidian vaults
- **COLL-07**: Tauri desktop application for cross-platform native experience
- **COLL-08**: P2P knowledge sharing between Smart Agent Wiki instances
- **COLL-09**: Team deployment mode (Docker Compose + PostgreSQL + Redis)

### Extended Platform

- **PLAT-01**: API开放平台 for third-party integrations
- **PLAT-02**: Multi-language support (English / 中文 / 日本語)
- **PLAT-03**: OWL-RL ontology reasoning for advanced knowledge inference

## Out of Scope

| Feature | Reason |
|---------|--------|
| General-purpose chatbot UI | Users already have ChatGPT/Claude/Gemini; building another dilutes focus |
| Real-time collaboration (Google Docs style) | Massive engineering complexity; file-lock + Git-based async is sufficient |
| Built-in LLM hosting | Ollama/LM Studio already do this well; support via API endpoint |
| Custom embedding model training | Niche requirement, massive ML effort; pre-trained models sufficient |
| Social features (comments, likes, feeds) | Personal/small-team platform; P2P sharing in Phase 4 is opt-in |
| Mobile app | Responsive Web UI covers mobile; Chrome clipper for mobile capture |
| Plugin/extension marketplace | Premature; YAML workflows and SOPs provide extensibility |
| Multi-tenant SaaS | Contradicts local-first philosophy; self-hosted deployment modes only |
| SPARQL/Cypher graph query language | Over-engineered; BFS/DFS APIs + Cytoscape.js visualization sufficient |
| Custom authentication system | Leverage API keys, Git credentials, Cedar policies; no custom auth needed |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STOR-01 | Phase 1 | Pending |
| STOR-02 | Phase 1 | Pending |
| STOR-03 | Phase 1 | Pending |
| STOR-04 | Phase 1 | Pending |
| STOR-05 | Phase 1 | Pending |
| STOR-06 | Phase 1 | Pending |
| STOR-07 | Phase 1 | Pending |
| INGE-01 | Phase 1 | Pending |
| INGE-02 | Phase 1 | Pending |
| INGE-03 | Phase 1 | Pending |
| INGE-04 | Phase 1 | Pending |
| INGE-05 | Phase 1 | Pending |
| INGE-06 | Phase 1 | Pending |
| INGE-07 | Phase 1 | Pending |
| QUER-01 | Phase 1 | Pending |
| QUER-02 | Phase 1 | Pending |
| QUER-03 | Phase 1 | Pending |
| QUER-04 | Phase 1 | Pending |
| QUER-05 | Phase 1 | Pending |
| QUER-06 | Phase 1 | Pending |
| QUER-07 | Phase 1 | Pending |
| GOVE-01 | Phase 2 | Pending |
| GOVE-02 | Phase 2 | Pending |
| GOVE-03 | Phase 2 | Pending |
| GOVE-04 | Phase 2 | Pending |
| GOVE-05 | Phase 2 | Pending |
| GOVE-06 | Phase 2 | Pending |
| GOVE-07 | Phase 2 | Pending |
| GOVE-08 | Phase 2 | Pending |
| LEARN-01 | Phase 2 | Pending |
| LEARN-02 | Phase 2 | Pending |
| LEARN-03 | Phase 2 | Pending |
| LEARN-04 | Phase 2 | Pending |
| LEARN-05 | Phase 2 | Pending |
| LEARN-06 | Phase 2 | Pending |
| COLL-01 | Phase 3 | Pending |
| COLL-02 | Phase 3 | Pending |
| COLL-03 | Phase 3 | Pending |
| COLL-04 | Phase 3 | Pending |
| COLL-05 | Phase 3 | Pending |
| CLI-01 | Phase 1 | Pending |
| CLI-02 | Phase 1 | Pending |
| CLI-03 | Phase 1 | Pending |
| CLI-04 | Phase 1 | Pending |
| CLI-05 | Phase 2 | Pending |
| CLI-06 | Phase 2 | Pending |
| CLI-07 | Phase 1 | Pending |
| CLI-08 | Phase 2 | Pending |
| CLI-09 | Phase 2 | Pending |
| CLI-10 | Phase 2 | Pending |
| CLI-11 | Phase 2 | Pending |
| MCP-01 | Phase 2 | Pending |
| MCP-02 | Phase 2 | Pending |
| MCP-03 | Phase 1 | Pending |
| WEB-01 | Phase 3 | Pending |
| WEB-02 | Phase 3 | Pending |
| WEB-03 | Phase 3 | Pending |
| XCUT-01 | Phase 1 | Pending |
| XCUT-02 | Phase 1 | Pending |
| XCUT-03 | Phase 1 | Pending |
| XCUT-04 | Phase 1 | Pending |
| XCUT-05 | Phase 2 | Pending |
| XCUT-06 | Phase 2 | Pending |
| XCUT-07 | Phase 1 | Pending |
| XCUT-08 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 65 total
- Phase 1 (Core Data Cycle): 32 requirements
- Phase 2 (Intelligence & Governance): 25 requirements
- Phase 3 (Collaboration & Visualization): 8 requirements
- Mapped to phases: 65
- Unmapped: 0

---
*Requirements defined: 2026-04-26*
*Last updated: 2026-04-26 after roadmap creation*
