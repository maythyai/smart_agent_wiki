# Phase 1: Core Data Cycle - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-26
**Phase:** 1-Core Data Cycle
**Mode:** Auto (decisions synthesized from design doc + research findings)
**Areas discussed:** Storage Architecture, Ingestion Pipeline, Query Engine, CLI Design, Cross-Cutting

---

## Storage Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Hexagonal (ports/adapters) | 3+ driving adapters (CLI/MCP/Web) and 6+ driven adapters (sinks) | ✓ |
| Layered (traditional) | Simpler but less testable, harder to swap adapters | |
| Microservices | Over-engineered for local-first tool | |

**Decision:** Hexagonal architecture — matches multi-driver, multi-sink constraint perfectly (per research/ARCHITECTURE.md)

---

## Database Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| SQLModel for all | Unified ORM+Pydantic but v0.0.38 is pre-release | |
| SQLModel simple + SQLAlchemy Core complex | Best of both worlds, mitigates pre-release risk | ✓ |
| SQLAlchemy Core only | Mature but verbose, no Pydantic integration | |
| SQLAlchemy ORM only | Mature but no Pydantic integration | |

**Decision:** SQLModel for simple CRUD, SQLAlchemy Core for complex queries. Falls back gracefully if SQLModel API breaks.

---

## FTS5 Tokenizer

| Option | Description | Selected |
|--------|-------------|----------|
| unicode61 (Phase 1) | Built-in, zero deps, good for English, acceptable CJK via character-level | ✓ |
| jieba custom tokenizer | Better CJK but needs FTS5 tokenizer API prototyping, risky for Phase 1 | |
| Porter + unicode61 | English stemming + unicode61, no CJK improvement | |

**Decision:** unicode61 for Phase 1. CJK tokenizer upgrade deferred — FTS5 tokenizer choice is locked at CREATE TABLE time so this needs a migration strategy later.

---

## PDF Parsing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| MinerU → Docling → PyMuPDF | Best quality first, graceful degradation | ✓ |
| Docling only | Good quality but no fallback | |
| PyMuPDF only | Fastest but lowest quality | |

**Decision:** 3-tier fallback as specified in design doc. Quality validation on first 5 pages.

---

## Multi-LLM Extraction

| Option | Description | Selected |
|--------|-------------|----------|
| Single LLM (Phase 1) | Simpler, cross-validation deferred to Phase 2 | ✓ |
| Dual LLM competition | Better quality but needs confidence system to evaluate | |

**Decision:** Single LLM in Phase 1. Multi-LLM competition deferred to Phase 2 when confidence system exists to evaluate cross-validation results.

---

## Claude's Discretion

- Python project structure (src layout vs flat)
- Typer command organization
- Claims DB schema details
- FTS5 index rebuild strategy
- CLI output formatting
- Test strategy
- Configuration file schema

## Deferred Ideas

- Multi-LLM competition extraction — Phase 2
- CJK custom FTS5 tokenizer (jieba) — needs spike
- Vector search / embeddings — Phase 2 (optional)
- Web UI — Phase 3
- MCP Server (23 tools) — Phase 2
- Chrome clipper, RSS, video/audio — Phase 4
