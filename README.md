# Smart Agent Wiki

**Next-Generation Intelligent Multi-Agent Knowledge Platform** — Knowledge that is Trustworthy, Traceable, and Evolvable

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v3.4.0-blue.svg)](https://github.com/chensaics/smart_agent_wiki/releases/tag/v3.4.0)
[![Tests](https://img.shields.io/badge/tests-24%20passing-brightgreen.svg)](tests/)
[![MCP](https://img.shields.io/badge/MCP-24+%20tools-purple.svg)](src/saw/mcp/)
[![Code Intelligence](https://img.shields.io/badge/code%20intelligence-v3.4-orange.svg)](src/saw/analysis/)
[![GitHub Stars](https://img.shields.io/github/stars/chensaics/smart_agent_wiki?style=social)](https://github.com/chensaics/smart_agent_wiki)
[![GitHub Issues](https://img.shields.io/github/issues/chensaics/smart_agent_wiki)](https://github.com/chensaics/smart_agent_wiki/issues)

[中文文档](README_CN.md)

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

## v3.4 New Feature: Code Intelligence

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
# Output: saw 3.4.0
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

| Command | Description |
|---------|-------------|
| `saw init` | Initialize new Wiki |
| `saw status` | Display knowledge base status overview |
| `saw ingest <source>` | Ingest document/URL/directory |
| `saw query <question>` | Natural language query |
| `saw search <keywords>` | BM25 keyword search |
| `saw impact <symbol>` | Code modification impact analysis ⭐ |
| `saw process <entry>` | Execution flow detection ⭐ |
| `saw staleness` | Knowledge base staleness detection ⭐ |
| `saw lint` | Health check |
| `saw conflicts` | List contradictions |
| `saw freshness` | Freshness report |
| `saw mcp` | Start MCP Server |
| `saw web` | Start Web UI |

⭐ New in v3.4

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

**Current Version: v3.4.0**

**Completed:**
- ✅ Four-layer storage architecture
- ✅ DAG Pipeline Validation (Kahn's topological sort)
- ✅ Impact Analysis Engine (BFS risk grading)
- ✅ Process Detection (DFS call tree)
- ✅ Staleness Detection (Git commit comparison)
- ✅ MCP Server 24+ tools
- ✅ CLI 16 commands
- ✅ Web UI (Search/Graph/Editor/Dashboard)
- ✅ 24 unit tests passing

**Roadmap (v3.5):**
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
