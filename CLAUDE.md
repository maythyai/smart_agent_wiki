# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

This is a **design documentation repository** for Smart Agent Wiki — a next-generation intelligent multi-agent knowledge platform. It contains no runnable code. The repo holds research, analysis, and design documents that will inform a future Python implementation.

## Document Map

| File | Purpose |
|------|---------|
| `docs/llm-wiki.md` | Karpathy's original LLM Wiki concept — the foundational pattern this project builds on |
| `docs/karpathy_llm_wiki_comments.md` | Raw comments (666 entries) from Karpathy's gist — primary research source |
| `docs/karpathy_llm_wiki_projects.md` | Enumerated list of 181 open-source projects spawned by the concept |
| `docs/llm_wiki_ecosystem_analysis.md` | Ecosystem analysis — categorization of all 181 projects by type, architecture, and quality tier |
| `docs/remote_project_audit_findings.md` | Deep audit of 156 remote projects — unique features extracted per project |
| `docs/smart_agent_wiki_design.md` | **The main design document** — complete architecture, five engines, storage layers, tech stack, roadmap |

## Key Design Decisions (from smart_agent_wiki_design.md)

- **Four-layer storage**: Vault (immutable originals) → Claims (structured assertions) → Wiki (mutable synthesis) → Index (search)
- **Five engines**: Ingest, Query, Govern, Learn, Collaborate
- **Four-tier confidence**: Unverified → Single Source → Cross-Validated → Human Verified
- **Local-first with progressive enhancement**: BM25+FTS5 by default, optional vector search
- **Planned tech stack**: Python 3.11+, Typer (CLI), FastAPI (Web), SQLite (default DB), FastMCP (MCP server)
- **Three deployment modes**: pure local, local+cloud LLM, team (Docker Compose+PostgreSQL)

## Working With These Docs

- All documents are in Chinese. Maintain Chinese for new content.
- The design doc uses extensive ASCII diagrams — preserve formatting when editing.
- Appendixes A.1–A.23 in the design doc capture design decisions inspired by specific audited projects; each includes source attribution.
- When updating the design, ensure cross-references between sections stay consistent (many features reference each other, e.g., confidence tiers ↔ freshness system ↔ governance engine).

## No Build/Test/Lint Commands

This repo has no code, no package.json, no Makefile, no CI pipeline. Editing markdown files is the primary activity.
