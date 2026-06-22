# Smart Agent Wiki

**Next-Generation Intelligent Multi-Agent Knowledge Platform** — Knowledge that is Trustworthy, Traceable, and Evolvable

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v3.7.0-blue.svg)](https://github.com/chensaics/smart_agent_wiki/releases/tag/v3.7.0)
[![Tests](https://img.shields.io/badge/tests-106+%20passing-brightgreen.svg)](tests/)
[![MCP](https://img.shields.io/badge/MCP-24+%20tools-purple.svg)](src/saw/mcp/)
[![Code Intelligence](https://img.shields.io/badge/code%20intelligence-v3.4-orange.svg)](src/saw/analysis/)
[![GitHub Stars](https://img.shields.io/github/stars/chensaics/smart_agent_wiki?style=social)](https://github.com/chensaics/smart_agent_wiki)
[![GitHub Issues](https://img.shields.io/github/issues/chensaics/smart_agent_wiki)](https://github.com/chensaics/smart_agent_wiki/issues)

[中文文档](README_CN.md) | [Documentation](docs/COMMANDS.md) | [Troubleshooting](docs/TROUBLESHOOTING.md) | [Migration Guide](docs/MIGRATION.md)

> **Note:** `saw` is the CLI command abbreviation for **Smart Agent Wiki**. Think of it as a "saw" that cuts through knowledge chaos to build structured wisdom.

## Introduction

Smart Agent Wiki is a local-first knowledge management platform that treats knowledge as the result of "compilation" rather than the object of retrieval. Through a four-layer storage architecture (Vault → Claims → Wiki → Index) and five engines (Ingest, Query, Govern, Learn, Collaborate), it manages the full lifecycle of knowledge from ingestion to expiration pruning.

**Core Features:**
- 🔍 **Four-Layer Storage Architecture** — Every claim can be traced back to the exact location in the original document
- 🤖 **6 Specialized Agents** — Librarian/Writer/Critic/Linker/Scholar/Guardian collaborative orchestration
- 🛡️ **Governance Engine** — 4-tier confidence, 9-level freshness, contradiction detection, Ed25519 audit receipts
- 🌐 **Web UI** — React + Cytoscape.js knowledge graph visualization + Milkdown editor
- 🔌 **MCP Server** — 24+ tools, compatible with Claude Code/Cursor/Copilot
- 🧠 **Code Intelligence** — Code knowledge graph analysis (new in v3.4)
- 💰 **Token Optimizer** — Reduce LLM token consumption by 65%+ (new in v3.6)
- 🔐 **Security Hardening** — JWT auth, RBAC, rate limiting, audit logs (new in v3.7)
- 🧩 **Plugin System** — Extensible SDK with event-driven architecture (new in v3.6)

## v3.5 New Feature: Developer Experience

v3.5 focuses on lowering the barrier to entry with improved installation, onboarding, and CLI usability.

### One-Line Installation
```bash
# Linux/macOS
curl -fsSL https://get.saw.wiki | bash

# Windows (PowerShell)
iwr -useb https://get.saw.wiki | iex
```

### Interactive Tutorial
```bash
saw tutorial
# 5-step guided tour with demo content
```

### Short Command Aliases
```bash
saw i document.pdf  # same as saw ingest
saw q "topic"       # same as saw query
saw s               # same as saw status
saw w               # same as saw web
```

### Friendly Error Messages
```bash
# Before
Traceback (most recent call last):
  ...
Error: FileNotFoundError

# After
❌ Error: File 'document.pdf' not found

💡 Suggestions:
  • Check if the file exists: ls document.pdf
  • Use absolute path: saw ingest /path/to/document.pdf
  • Ingest entire directory: saw ingest ./documents/
```

### Shell Completion
```bash
saw completion bash --install   # Bash
saw completion zsh --install    # Zsh
saw completion fish --install   # Fish
```

### Offline Documentation
```bash
saw docs --output ./docs-offline/
```

## v3.7 Feature: Security & Quality

v3.7 focuses on production-readiness with comprehensive security hardening, expanded test coverage, and documentation.

### Security Hardening
- **JWT Authentication** — Access/refresh token pairs with configurable expiry
- **RBAC Permissions** — Role-based access control (admin/editor/viewer)
- **Rate Limiting** — Per-user, per-endpoint request throttling
- **Input Sanitization** — SQL injection and XSS pattern detection
- **Security Headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Audit Logging** — All write operations logged with timestamps and user context

### Test Coverage Expansion
- **82 new test cases** across 4 test files
- JWT auth: 28 tests (token creation, verification, expiry, refresh flow)
- Permissions: 24 tests (RBAC enforcement, role hierarchy, middleware)
- Security middleware: 16 tests (rate limiting, input sanitization, headers)
- Plugin system: 14 tests (lifecycle, events, sandbox isolation)

### Documentation & Developer Experience
- Plugin development guide (`docs/PLUGIN_DEVELOPMENT.md`)
- Architecture documentation (`docs/ARCHITECTURE.md`)
- Mobile-responsive Graph page with touch gestures

## v3.6 Feature: Plugin System & Performance

v3.6 introduces an extensible plugin system and performance optimizations.

### Plugin System
- **Plugin SDK** — `PluginBase`, `PluginContext`, event hooks
- **CLI Management** — `saw plugin list/install/enable/disable/uninstall`
- **Event System** — `PageCreated`, `PageUpdated`, `PageDeleted`, `ClaimCreated`, `IngestCompleted`, `QueryExecuted`
- **Example Plugins** — markdown-formatter (admonitions, anchors), word-counter (statistics)
- **Sandbox Isolation** — Each plugin gets isolated `data_dir`

### Query Cache
- **LRU with TTL** — 300s default, 1000 entries max
- **Dashboard Stats API** — `/api/dashboard/stats` endpoint
- **Real-time Metrics** — Total pages, recent edits, active agents, uptime

### Token Optimizer

Inspired by OpenWolf's token optimization techniques, Smart Agent Wiki now includes a Token Optimizer module to reduce LLM token consumption by up to 65%:

### Anatomy Index (File Map)
Project structure index with file descriptions and token estimates - know what a file contains before reading it:
```python
from saw.token_optimizer import AnatomyIndex

index = AnatomyIndex(project_root="./my_project")
index.scan_directory()

# Get file info without reading
entry = index.get_entry("src/main.py")
print(f"{entry.description} (~{entry.estimated_tokens} tokens)")
```

### Cerebrum (Learning Memory)
Cross-session learning memory that accumulates preferences and prevents repeated mistakes:
```python
from saw.token_optimizer import Cerebrum

cerebrum = Cerebrum()
cerebrum.add_do_not_repeat(
    mistake="Used mutable default argument",
    correction="Use None default and check inside function"
)

# Check before making same mistake
if cerebrum.check_do_not_repeat("mutable default"):
    # Apply learned correction
```

### Bug Log (Fix Memory)
Bug fix memory that prevents re-discovery of known solutions:
```python
from saw.token_optimizer import BugLog

buglog = BugLog()
buglog.add_bug(
    error_message="TypeError: 'NoneType' object is not subscriptable",
    file="src/api.py",
    fix="Added null check before dict access"
)

# Search for known fix
fix = buglog.get_fix_for_error("TypeError: 'NoneType'")
if fix:
    print(f"Known fix: {fix.fix}")
```

### Session Tracker (Read Tracking)
Detects repeated file reads and provides warnings:
```python
from saw.token_optimizer import SessionTracker

tracker = SessionTracker()
tracker.track_read("src/main.py", 150)

# Second read triggers warning
result = tracker.track_read("src/main.py", 150)
if "warning" in result:
    print(result["warning"])  # "File read 2 times..."
```

### Token Ledger
Track token consumption across sessions and estimate savings:
```python
from saw.token_optimizer import TokenLedger

ledger = TokenLedger()
ledger.start_session()
ledger.record_read(100, was_anatomy_hit=True)  # Saved ~800 tokens

report = ledger.get_savings_report()
print(f"Saved {report['savings_percentage']}% tokens")
```

## v3.4 Feature: Code Intelligence

Inspired by GitNexus (35K+ stars), Smart Agent Wiki now has code knowledge graph analysis capabilities:

### DAG Pipeline Validation
Type-safe ingestion pipeline architecture ensuring correct phase dependencies:
- Kahn's topological sort algorithm
- Cycle detection with precise error reporting
- 6-phase ingestion flow: Classify → Parse → Extract → Merge → Validate → Store

### Impact Analysis Engine
Code modification impact analysis - understand breaking scope before changes:
```bash
saw impact UserService
# Output:
# Summary:
#   Total affected: 5
#   Depth 1 (will break): 2
#   Depth 2 (likely affected): 3
# ⚠ HIGH RISK: 2 direct dependents will break!
```

Risk levels:
- **WILL_BREAK** — Direct dependency, modification will break
- **LIKELY_AFFECTED** — Secondary dependency, possibly affected
- **MAY_NEED_TESTING** — Tertiary dependency, testing recommended

### Process Detection
Trace execution flow from entry points:
```bash
saw process handleRequest
# Output:
# Execution flow:
#   handleRequest
#     → validateInput
#       → parseJSON
#     → processData
#       → saveToDatabase
```

### Staleness Detection
Knowledge base staleness detection to judge data trustworthiness:
```bash
saw staleness
# Output:
# Stale nodes: 3
# - UserService (10 days old, 12 commits behind)
# - OldService (8 days old, 5 commits behind)
# Recommendation: Run ingest to update 3 stale nodes
```

## Quick Start

### 1. Installation

**Quick Install (Recommended):**

```bash
# Linux/macOS
curl -fsSL https://get.saw.sh | bash

# Windows (PowerShell)
iwr -useb https://get.saw.sh | iex
```

**Package Managers:**

```bash
# pipx (isolated environment)
pipx install smart-agent-wiki

# Homebrew (macOS)
brew install chensaics/tap/saw

# Docker
docker run -it chensaics/saw:latest saw init
```

**Verify Installation:**

```bash
saw --version
# Output: saw 3.5.0
```

<details>
<summary>Manual Installation (Development)</summary>

```bash
# Clone repository
git clone https://github.com/chensaics/smart_agent_wiki.git
cd smart-agent-wiki

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install core dependencies
pip install -e .

# Install PDF parsing support (optional)
pip install -e ".[pdf]"

# Install development dependencies (optional)
pip install -e ".[dev]"
```
</details>

### 2. Initialize Wiki

```bash
# Create new Wiki in current directory
saw init

# Generate Agent config files
saw init --agent claude-code  # Generate CLAUDE.md
saw init --agent cursor       # Generate .cursorrules
```

### 3. Ingest Documents

```bash
# Ingest single file
saw ingest document.pdf
saw ingest notes.md
saw ingest https://example.com/article

# Ingest entire directory
saw ingest ./documents/

# Offline mode (structure extraction only)
saw ingest document.pdf --no-llm
```

Supported formats:
- **Markdown** (`.md`) — LLM extracts entities, concepts, claims
- **PDF** (`.pdf`) — Docling → PyMuPDF parsing
- **URL** — trafilatura content extraction
- **Code** (`.py`, `.js`, `.ts`, etc.) — AST parsing, zero LLM calls

### 4. Code Intelligence Usage

```bash
# Analyze code modification impact (upstream: dependents)
saw impact UserService

# Analyze downstream dependencies
saw impact handleLogin --direction downstream

# Depth limit
saw impact AuthModule --max-depth 5

# Confidence filtering
saw impact UserService --min-confidence 0.9

# JSON output
saw impact UserService --json

# Detect execution flow
saw process handleRequest --max-depth 5

# Detect stale nodes
saw staleness --threshold-days 7
```

### 5. Query Knowledge Base

```bash
# Natural language query
saw query "What are the main design decisions of this project?"

# Keyword search (BM25 + FTS5)
saw search "entity resolution"

# View knowledge base status
saw status
```

### 6. Start Web UI

```bash
saw web
# Access: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 7. Start MCP Server

```bash
saw mcp
```

Configure in Claude Desktop:
```json
{
  "mcpServers": {
    "smart-agent-wiki": {
      "command": "saw",
      "args": ["mcp"]
    }
  }
}
```

## CLI Commands Reference

| Command | Alias | Description |
|---------|-------|-------------|
| `saw init` | — | Initialize new Wiki |
| `saw status` | `saw s` | Display knowledge base status |
| `saw ingest <source>` | `saw i` | Ingest document/URL/directory |
| `saw query <question>` | `saw q` | Natural language query |
| `saw search <keywords>` | — | BM25 keyword search |
| `saw impact <symbol>` | — | Code modification impact analysis ⭐ |
| `saw process <entry>` | — | Execution flow detection ⭐ |
| `saw staleness` | — | Knowledge base staleness detection ⭐ |
| `saw lint` | `saw l` | Health check |
| `saw conflicts` | — | List contradictions |
| `saw freshness` | — | Freshness report |
| `saw mcp` | — | Start MCP Server |
| `saw web` | `saw w` | Start Web UI |
| `saw tutorial` | — | Interactive tutorial 🆕 |
| `saw config` | — | TUI configuration 🆕 |
| `saw completion` | — | Shell completion 🆕 |
| `saw docs` | — | Offline documentation 🆕 |

⭐ v3.4 | 🆕 v3.5

## MCP Tools List

**Ingestion Tools (2)**
- `saw_ingest` — Ingest document
- `saw_reparse` — Re-parse

**Query Tools (7)**
- `saw_query` — Natural language query
- `saw_search` — BM25 search
- `saw_tree_search` — Structure-aware search
- `saw_graph` — Knowledge graph traversal
- `saw_compare` — Page comparison
- `saw_compile` — Context compilation
- `saw_coverage` — Coverage analysis

**Governance Tools (7)**
- `saw_lint` — Health check
- `saw_conflicts` — Contradiction list
- `saw_verify` — Verify traceability
- `saw_freshness` — Freshness report
- `saw_review` — Manual review
- `saw_audit` — Audit chain verification
- `saw_blast_radius` — Impact scope

**Code Intelligence Tools (3) ⭐**
- `saw_impact` — Code modification impact analysis
- `saw_process` — Execution flow detection
- `saw_staleness` — Knowledge base staleness detection

**Learning Tools (5)**
- `saw_status` — Knowledge base status
- `saw_learn` — Trigger learning cycle
- `saw_distill` — Cognitive distillation
- `saw_suggest` — Knowledge gap suggestions
- `saw_wip` — Work in progress

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
│ (DAG v3.4)  │             │             │                   │
└──────┬──────┴──────┬──────┴──────┬──────┴─────────┬─────────┘
       │             │             │                │
       ▼             ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                       Storage Layer                          │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    Vault    │ Claims (DB) │ Wiki Pages  │ FTS5 + Graph      │
│  (Immutable)│  (SQLite)   │ (Markdown)  │ (Index Layer)     │
└─────────────┴─────────────┴─────────────┴───────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Code Intelligence (v3.4)                    │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ DAG Pipeline│ Impact Eng. │Process Det. │ Staleness Det.    │
│ Validation  │ (BFS trav.) │ (DFS tree)  │ (Git compare)     │
└─────────────┴─────────────┴─────────────┴───────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Token Optimizer (v3.6)                      │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ Anatomy Index│ Cerebrum    │ Bug Log     │ Session Tracker   │
│ (File Map)  │ (Learn Mem) │ (Fix Hist)  │ (Read Track)      │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

## Confidence & Freshness

### 4-Tier Confidence System

| Level | Name | Description |
|-------|------|-------------|
| 1 | Unverified | Single source, unverified |
| 2 | Single Source | Single source, verified |
| 3 | Cross-Validated | Multi-source cross-validation |
| 4 | Human Verified | Human confirmed |

### 9-Level Freshness System

| Level | Color | Description |
|-------|-------|-------------|
| 0-2 | 🟢 Green | Fresh |
| 3-5 | 🟡 Yellow | Fairly fresh |
| 6-7 | 🟠 Orange | Somewhat stale |
| 8 | 🔴 Red | Stale |

## Project Status

**Current Version: v3.7.0**

**Completed:**
- ✅ Four-layer storage architecture
- ✅ DAG Pipeline Validation (Kahn's topological sort)
- ✅ Impact Analysis Engine (BFS risk grading)
- ✅ Process Detection (DFS call tree)
- ✅ Staleness Detection (Git commit comparison)
- ✅ MCP Server 24+ tools
- ✅ CLI 20 commands
- ✅ Web UI (Search/Graph/Editor/Dashboard)
- ✅ 106+ unit tests passing
- ✅ One-line installation (curl/pipx/homebrew/docker)
- ✅ Interactive tutorial with demo content
- ✅ Short command aliases
- ✅ Friendly error messages
- ✅ Shell completion (bash/zsh/fish)
- ✅ Offline documentation
- ✅ Plugin system with SDK and CLI management (v3.6)
- ✅ Query cache and dashboard stats API (v3.6)
- ✅ Token Optimizer — 65%+ token savings (v3.6)
- ✅ Security hardening — JWT, RBAC, rate limiting, audit logs (v3.7)
- ✅ 82 new test cases for auth/permissions/plugins (v3.7)
- ✅ Plugin development and architecture docs (v3.7)
- ✅ Mobile-responsive Graph page (v3.7)

**Roadmap (v3.8):**
- Web UI Impact visualization (D3.js graph)
- Tree-sitter AST zero LLM parsing
- LadybugDB/KuzuDB graph database
- Agent Skills Layer (Claude Code Skills)

## Development

```bash
# Run tests
pytest tests/unit/ingest/ tests/unit/analysis/ -v

# Run coverage tests
pytest --cov=src/saw

# Frontend development
cd web && npm run dev
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
