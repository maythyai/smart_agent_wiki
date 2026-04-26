# Roadmap: Smart Agent Wiki

## Overview

Build a local-first intelligent multi-agent knowledge platform in 3 phases. Phase 1 establishes the core data cycle: users can initialize a wiki, ingest documents (Markdown/PDF/URL), query them with natural language and keyword search, and trust that every answer traces back to its source. Phase 2 adds intelligence on top of that foundation: confidence scoring, contradiction detection, freshness tracking, learning from user behavior, and full MCP server integration with 23 tools. Phase 3 connects multiple specialized agents into collaborative workflows and provides a visual Web UI for graph exploration and page editing. Each phase delivers standalone, verifiable value.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Core Data Cycle** - Ingest documents, extract claims, query with search and natural language, all via CLI (completed 2026-04-26)
- [ ] **Phase 2: Intelligence & Governance** - Confidence scoring, contradiction detection, learning, MCP server, audit trail
- [ ] **Phase 3: Collaboration & Visualization** - Multi-agent workflows, Web UI, knowledge graph, page editing

## Phase Details

### Phase 1: Core Data Cycle
**Goal**: Users can create a wiki, ingest documents into a trusted four-layer storage system, and query their knowledge base via CLI with full source provenance
**Depends on**: Nothing (first phase)
**Requirements**: STOR-01, STOR-02, STOR-03, STOR-04, STOR-05, STOR-06, STOR-07, INGE-01, INGE-02, INGE-03, INGE-04, INGE-05, INGE-06, INGE-07, QUER-01, QUER-02, QUER-03, QUER-04, QUER-05, QUER-06, QUER-07, CLI-01, CLI-02, CLI-03, CLI-04, CLI-07, MCP-03, XCUT-01, XCUT-02, XCUT-03, XCUT-04, XCUT-07
**Success Criteria** (what must be TRUE):
  1. User can run `saw init`, then `saw ingest paper.pdf`, then `saw query "what are the key findings"` and receive a sourced answer with inline citations linking to the original document
  2. User can run `saw search "entity resolution"` and get BM25-ranked results with snippet context from FTS5
  3. Every claim in the knowledge base traces back to the exact Vault source (document UUID + page/line number), verifiable by inspection
  4. User can ingest Markdown, PDF (3-tier fallback), and URL sources, and each produces structured claims, entity Wiki drafts, and graph updates
  5. User can run `saw status` and see knowledge base overview (pages, claims, storage health) and `saw init --agent claude-code` generates agent-specific config
**Plans**: 3

Plans:
- [x] 01-01: Foundation: Domain + Write Queue + Storage + CLI Init
- [x] 01-02: Ingestion Engine: Document Parsing + LLM Extraction + Git Provenance
- [x] 01-03: Query Engine: Search + Context Compilation + NL Query + Graph

### Phase 2: Intelligence & Governance
**Goal**: Users can trust the quality of their knowledge base through confidence scoring, contradiction detection, freshness tracking, and learning from their own usage patterns, all accessible via CLI and MCP server
**Depends on**: Phase 1
**Requirements**: GOVE-01, GOVE-02, GOVE-03, GOVE-04, GOVE-05, GOVE-06, GOVE-07, GOVE-08, LEARN-01, LEARN-02, LEARN-03, LEARN-04, LEARN-05, LEARN-06, CLI-05, CLI-06, CLI-08, CLI-09, CLI-10, CLI-11, MCP-01, MCP-02, XCUT-05, XCUT-06, XCUT-08
**Success Criteria** (what must be TRUE):
  1. User can run `saw lint` and see a health report identifying contradictions, orphan pages, broken links, missing metadata, and stale claims
  2. User can run `saw conflicts` and see detected contradictions with resolution strategy (Superseded/Disputed/Historical) and blast radius analysis
  3. Each Wiki page displays a 4-tier confidence level and 9-level freshness indicator, and user can run `saw freshness` to see a freshness report
  4. User can run `saw audit` and verify Ed25519 receipt chain integrity for all agent operations
  5. MCP server exposes 23 tools and works with Claude Code, Cursor, and other MCP-compatible agents; knowledge base learns from user behavior over time (training period, spaced repetition, cognitive distillation)
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD

### Phase 3: Collaboration & Visualization
**Goal**: Users can orchestrate multiple specialized agents to collaboratively manage knowledge and explore their knowledge base visually through a Web UI with graph visualization and page editing
**Depends on**: Phase 2
**Requirements**: COLL-01, COLL-02, COLL-03, COLL-04, COLL-05, WEB-01, WEB-02, WEB-03
**Success Criteria** (what must be TRUE):
  1. User can define a YAML workflow that dispatches tasks to 6 specialized agents (Librarian, Writer, Critic, Linker, Scholar, Guardian) with model routing and Cedar policy enforcement
  2. User can open Web UI, search the knowledge base, and explore entity relationships visually via Cytoscape.js knowledge graph
  3. User can review, approve, reject, and edit LLM-generated Wiki pages in the Milkdown editor within the Web UI
  4. Agents can communicate and hand off tasks via A2A protocol within orchestrated workflows
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Data Cycle | 3/3 | Complete | 2026-04-26 |
| 2. Intelligence & Governance | 0/3 | Not started | - |
| 3. Collaboration & Visualization | 0/2 | Not started | - |
