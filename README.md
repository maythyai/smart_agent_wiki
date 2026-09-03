# Smart Agent Wiki

**Next-Generation Intelligent Multi-Agent Knowledge Platform** — Knowledge that is Trustworthy, Traceable, and Evolvable

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v1.3.0-blue.svg)](https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.3.0)
[![Tests](https://img.shields.io/badge/tests-1874+%20passing-brightgreen.svg)](tests/)
[![MCP](https://img.shields.io/badge/MCP-64+%20tools-purple.svg)](src/saw/drivers/mcp/)
[![GitHub Stars](https://img.shields.io/github/stars/chensaics/smart_agent_wiki?style=social)](https://github.com/chensaics/smart_agent_wiki)
[![GitHub Issues](https://img.shields.io/github/issues/chensaics/smart_agent_wiki)](https://github.com/chensaics/smart_agent_wiki/issues)

[中文文档](README_CN.md) | [Documentation](docs/COMMANDS.md) | [Troubleshooting](docs/TROUBLESHOOTING.md) | [Migration Guide](docs/MIGRATION.md)

> **Note:** `saw` is the CLI command abbreviation for **Smart Agent Wiki**. Think of it as a "saw" that cuts through knowledge chaos to build structured wisdom.

## Introduction

Smart Agent Wiki is a local-first knowledge management platform that treats knowledge as the result of "compilation" rather than the object of retrieval. Through a four-layer storage architecture (Vault → Claims → Wiki → Index) and five engines (Ingest, Query, Govern, Learn, Collaborate), it manages the full lifecycle of knowledge from ingestion to expiration pruning.

**Highlights:**

- 🔍 **Four-Layer Storage** — Every claim traces back to the exact location in the original document
- 🤖 **6 Agent Roles** — Librarian / Writer / Critic / Linker / Scholar / Guardian (DTOs defined, agent implementations dispatched via workflows)
- 🛡️ **Governance Engine** — 4-tier confidence, 9-level freshness, contradiction detection, Ed25519 audit receipts
- 🧠 **Code Intelligence** — Full code graph lifecycle: AST parsing, impact analysis, execution flow tracing, community detection, doc↔code anchoring
- 🔐 **Security** — JWT auth, RBAC, rate limiting, input sanitization, audit logging
- 🧩 **Plugin System** — Extensible SDK with event-driven hooks (sandbox isolation planned)
- 💰 **Token Optimizer** — Tracking infrastructure for LLM token consumption (theoretical savings benchmark: ~65% in ideal conditions)
- 🌐 **Web UI** — React + Cytoscape.js knowledge graph + Milkdown editor
- 🔌 **MCP Server** — 56+ tools, compatible with Claude Code / Cursor / Copilot

## Quick Start

### 1. Installation

```bash
# Linux/macOS
curl -fsSL https://get.saw.sh | bash

# Windows (PowerShell)
iwr -useb https://get.saw.sh | iex
```

Other options: `pipx install smart-agent-wiki`, `brew install chensaics/tap/saw`, or Docker.

<details>
<summary>Manual Installation (Development)</summary>

```bash
git clone https://github.com/chensaics/smart_agent_wiki.git
cd smart_agent_wiki
python -m venv .venv && source .venv/bin/activate
pip install -e .            # core
pip install -e ".[pdf]"     # + PDF parsing
pip install -e ".[graph]"   # + Leiden community detection (igraph)
pip install -e ".[dev]"     # + dev tools
```
</details>

### 2. Initialize & Ingest

```bash
saw init                          # Create Wiki in current directory
saw init --agent claude-code      # Also generate CLAUDE.md

saw ingest document.pdf           # Single file
saw ingest ./documents/           # Entire directory
saw ingest https://example.com    # URL
saw ingest doc.pdf --no-llm       # Offline mode (structure only)
```

Supported formats: **Markdown**, **PDF** (Docling/PyMuPDF), **URL** (trafilatura), **Code** (AST parsing, zero LLM calls).

### 3. Query & Search

```bash
saw query "What are the main design decisions?"   # Natural language
saw search "entity resolution"                     # BM25 keyword search
saw status                                         # Knowledge base overview
```

### 4. Web UI & MCP

```bash
saw web    # → http://localhost:8000  (API docs: /docs)
saw mcp    # Start MCP Server
```

Claude Desktop MCP config:
```json
{ "mcpServers": { "smart-agent-wiki": { "command": "saw", "args": ["mcp"] } } }
```

## Features

### Knowledge Governance

- **4-Tier Confidence** — Unverified → Single Source → Cross-Validated → Human Verified
- **9-Level Freshness** — 🟢 Fresh → 🟡 Fairly fresh → 🟠 Somewhat stale → 🔴 Stale
- **Contradiction Detection** — Automatic detection of conflicting claims across sources
- **Ed25519 Audit Receipts** — Cryptographic proof of data provenance
- **Write Queue** — SQLite outbox pattern as the single mutation gateway

### Code Intelligence

Analyze codebases through the knowledge graph:

```bash
saw impact UserService                  # Modification impact analysis (BFS risk grading)
saw impact handleLogin --direction downstream
saw process handleRequest               # Execution flow detection (DFS call tree)
saw staleness --threshold-days 7        # Knowledge base freshness check
```

Risk levels: **WILL_BREAK** (direct dependency) → **LIKELY_AFFECTED** (secondary) → **MAY_NEED_TESTING** (tertiary).

The ingestion pipeline uses Kahn's topological sort for DAG validation with cycle detection across 6 phases: Classify → Parse → Extract → Merge → Validate → Store.

### Security

Production-ready security built in:

- **JWT Authentication** — Access/refresh token pairs with configurable expiry
- **RBAC** — Role-based access control (admin / editor / viewer)
- **Rate Limiting** — Per-user, per-endpoint request throttling
- **Input Sanitization** — SQL injection and XSS pattern detection
- **Security Headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Audit Logging** — All write operations logged with timestamps and user context

### Plugin System

Extend SAW with custom plugins:

```bash
saw plugin list                  # List installed plugins
saw plugin install my-plugin     # Install from registry
saw plugin enable my-plugin      # Enable/disable
```

- **Plugin SDK** — `PluginBase`, `PluginContext`, event hooks
- **Event System** — `PageCreated`, `PageUpdated`, `PageDeleted`, `ClaimCreated`, `IngestCompleted`, `QueryExecuted`
- **Sandbox Isolation** — Each plugin gets its own `data_dir`

See [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) for building custom plugins.

### Token Optimizer

Reduce LLM token consumption by up to 65%:

| Module | Purpose |
|--------|---------|
| **Anatomy Index** | Project structure index with file descriptions and token estimates |
| **Cerebrum** | Cross-session learning memory — accumulates preferences, prevents repeated mistakes |
| **Bug Log** | Fix memory — prevents re-discovery of known solutions |
| **Session Tracker** | Detects repeated file reads and provides warnings |
| **Token Ledger** | Tracks token consumption across sessions and estimates savings |

```python
from saw.token_optimizer import AnatomyIndex, TokenLedger

index = AnatomyIndex(project_root="./my_project")
index.scan_directory()
entry = index.get_entry("src/main.py")
print(f"{entry.description} (~{entry.estimated_tokens} tokens)")
```

### Developer Experience

- **One-Line Installation** — `curl -fsSL https://get.saw.sh | bash`
- **Interactive Tutorial** — `saw tutorial` (5-step guided tour with demo content)
- **Short Aliases** — `saw i` (ingest), `saw q` (query), `saw s` (status), `saw w` (web)
- **Friendly Errors** — Actionable suggestions instead of raw tracebacks
- **Shell Completion** — `saw completion bash|zsh|fish --install`
- **Offline Docs** — `saw docs --output ./docs-offline/`
- **Query Cache** — LRU with TTL (300s default, 1000 entries max)
- **Dashboard Stats** — Real-time metrics: total pages, recent edits, active agents, uptime

## CLI Commands Reference

| Command | Alias | Description |
|---------|-------|-------------|
| `saw init` | — | Initialize new Wiki |
| `saw status` | `saw s` | Display knowledge base status |
| `saw ingest <source>` | `saw i` | Ingest document/URL/directory |
| `saw query <question>` | `saw q` | Natural language query |
| `saw search <keywords>` | — | BM25 keyword search |
| `saw impact <symbol>` | — | Code modification impact analysis |
| `saw process <entry>` | — | Execution flow detection |
| `saw staleness` | — | Knowledge base staleness detection |
| `saw lint` | `saw l` | Health check |
| `saw conflicts` | — | List contradictions |
| `saw freshness` | — | Freshness report |
| `saw plugin <action>` | — | Plugin management (list/install/enable/disable) |
| `saw mcp` | — | Start MCP Server |
| `saw web` | `saw w` | Start Web UI |
| `saw tutorial` | — | Interactive tutorial |
| `saw config` | — | TUI configuration |
| `saw completion` | — | Shell completion |
| `saw docs` | — | Offline documentation |

## MCP Tools (56+)

**Ingestion (2):** `saw_ingest`, `saw_reparse`

**Query (7):** `saw_query`, `saw_search`, `saw_tree_search`, `saw_graph`, `saw_compare`, `saw_compile`, `saw_coverage`

**Governance (7):** `saw_lint`, `saw_conflicts`, `saw_verify`, `saw_freshness`, `saw_review`, `saw_audit`, `saw_blast_radius`

**Code Intelligence (6):** `saw_impact`, `saw_process`, `saw_staleness`, `saw_code_query`, `saw_code_search`, `saw_architecture`

**Learning (5):** `saw_status`, `saw_learn`, `saw_distill`, `saw_suggest`, `saw_wip`

**Collaborate (2):** `saw_workflow`, `saw_feedback`

**Pages & Links (9):** `saw_page_create`, `saw_page_update`, `saw_page_delete`, `saw_page_read`, `saw_page_list`, `saw_wiki_link`, `saw_wiki_unlink`, `saw_backlinks`, `saw_outlinks`

**Compile & Archive (18):** `saw_wiki_compile`, `saw_wiki_index`, `saw_wiki_page`, `saw_wiki_log`, `saw_archive`, `saw_archive_suggest`, `saw_wiki_lint`, `saw_concept_list`, `saw_concept_view`, `saw_concept_relate`, `saw_graph_overview`, `saw_graph_navigate`, `saw_issue_create`, `saw_issue_list`, `saw_cr_create`, `saw_cr_review`, `saw_code_wiki_generate`, `saw_code_wiki_status`

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface Layer                    │
├─────────────────┬─────────────────┬─────────────────────────┤
│   CLI (Typer)   │  Web UI (React) │  MCP Server (FastMCP)   │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         │                 │                      │
         └─────────────────┼──────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                        Engine Layer                          │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ IngestEngine│ QueryEngine │GovernEngine │ CollaborateEngine │
│ (DAG pipe)  │ (+ Cache)   │ (+ RBAC)    │                   │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       ▼             ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                       Storage Layer                          │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Vault    │ Claims (DB) │ Wiki Pages  │ FTS5 + Graph      │
│  (Immutable)│  (SQLite)   │ (Markdown)  │ (Index Layer)     │
└─────────────┴─────────────┴─────────────┴───────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│   Code Intelligence  │  │    Token Optimizer    │
├──────────────────────┤  ├──────────────────────┤
│ Impact · Process     │  │ Anatomy · Cerebrum   │
│ Staleness · DAG      │  │ BugLog · Tracker     │
└──────────────────────┘  └──────────────────────┘
```

Hexagonal architecture: `domain/` (pure Python) → `engines/` (business logic) → `adapters/` (infrastructure) → `drivers/` (CLI/Web/MCP). Six specialized agents — Librarian, Writer, Critic, Linker, Scholar, Guardian — handle collaborative knowledge processing.

## Roadmap

| Feature | Status |
|---------|--------|
| REST API (govern / query / ingest / learn / collaborate) | ✅ Shipped (v1.1.0) |
| JWT auth + RBAC + DB-backed users | ✅ Shipped |
| Write Queue outbox + migration framework | ✅ Shipped |
| Web UI Impact visualization (D3.js graph) | 🔜 Planned |
| Tree-sitter AST zero LLM parsing | 🔜 Planned |
| LadybugDB / KuzuDB graph database | 🔜 Planned |
| Agent Skills Layer (Claude Code Skills) | 🔜 Planned |
| Plugin sandbox isolation | 🔜 Planned |

## Development

```bash
pytest tests/ -v              # Run all tests
pytest --cov=src/saw          # With coverage
cd web && npm run dev         # Frontend dev server
```

## License

[MIT License](LICENSE)

## Acknowledgments

This project was inspired by Karpathy's LLM Wiki concept. Special thanks to:

- GitNexus — DAG Pipeline, Impact Analysis architecture reference
- Knowledge Pipeline — Compilation paradigm, contradiction detection
- Multi-Agent Wiki — Multi-agent governance
- codesight — AST zero LLM extraction
- llm-wiki1 — FSRS spaced repetition
- unified-memory-ai-agents — Three-layer cognition, WIP momentum
