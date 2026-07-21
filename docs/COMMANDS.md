# Command Reference

Complete reference for all Smart Agent Wiki CLI commands.

## Overview

```
saw <command> [arguments] [options]
```

**Short aliases available:**
- `saw i` = `saw ingest`
- `saw q` = `saw query`
- `saw s` = `saw status`
- `saw w` = `saw web`
- `saw v` = `saw verify`
- `saw l` = `saw lint`

---

## Commands

### init

Initialize a new wiki in the current directory.

```bash
saw init [OPTIONS]
```

**Options:**
- `--name TEXT` — Wiki name (default: "My Wiki")
- `--description TEXT` — Wiki description
- `--path PATH` — Custom directory path

**Examples:**
```bash
saw init
saw init --name "Project Knowledge" --description "Development notes"
saw init --path ./my-wiki
```

---

### ingest (alias: i)

Ingest documents into the wiki knowledge base.

```bash
saw ingest PATH [OPTIONS]
```

**Arguments:**
- `PATH` — File, directory, or URL to ingest

**Options:**
- `--format TEXT` — Override format detection (md, pdf, py, js, ts, html)
- `--recursive, -r` — Process directories recursively
- `--dry-run` — Show what would be ingested without changes
- `--validate` — Validate extracted claims immediately
- `--confidence FLOAT` — Minimum confidence threshold (0.0-1.0)

**Examples:**
```bash
saw ingest document.pdf
saw ingest ./documents/ --recursive
saw ingest https://example.com/article
saw ingest code.py --format py
saw i ./notes/ --dry-run
```

---

### query (alias: q)

Search the knowledge base with intelligent reasoning.

```bash
saw query QUERY [OPTIONS]
```

**Arguments:**
- `QUERY` — Search query text

**Options:**
- `--mode TEXT` — Query mode: direct, graph, reasoning, contrast, synthesis (default: direct)
- `--max-results N` — Maximum results (default: 20)
- `--confidence FLOAT` — Minimum confidence filter
- `--freshness TEXT` — Filter by freshness level (fresh, recent, dated, stale)
- `--output TEXT` — Output format: text, json, markdown

**Examples:**
```bash
saw query "API design patterns"
saw query "authentication" --mode graph
saw q "database optimization" --max-results 10
saw query "security" --confidence 0.8 --freshness fresh
```

---

### search

Full-text search across all content.

```bash
saw search QUERY [OPTIONS]
```

**Options:**
- `--max-results N` — Maximum results (default: 50)
- `--case-sensitive` — Enable case-sensitive search
- `--regex` — Treat query as regex pattern

**Examples:**
```bash
saw search "OAuth"
saw search "function.*auth" --regex
saw search "TODO" --case-sensitive
```

---

### status (alias: s)

Show wiki status and statistics.

```bash
saw status [OPTIONS]
```

**Options:**
- `--verbose, -v` — Show detailed statistics
- `--json` — Output as JSON

**Examples:**
```bash
saw status
saw status --verbose
saw s --json
```

---

### web (alias: w)

Launch the web UI.

```bash
saw web [OPTIONS]
```

**Options:**
- `--port N` — Server port (default: 8000)
- `--host TEXT` — Server host (default: localhost)
- `--open` — Open browser automatically
- `--no-browser` — Don't open browser

**Examples:**
```bash
saw web
saw web --port 8080 --open
saw w --no-browser
```

---

### verify (alias: v)

Verify claims against source documents.

```bash
saw verify [OPTIONS]
```

**Options:**
- `--claim-id TEXT` — Verify specific claim
- `--all` — Verify all unverified claims
- `--auto` — Auto-verify where possible
- `--threshold FLOAT` — Confidence threshold for auto-verify

**Examples:**
```bash
saw verify --claim-id claim_123
saw verify --all
saw v --auto --threshold 0.8
```

---

### lint (alias: l)

Lint wiki pages for quality issues.

```bash
saw lint [OPTIONS]
```

**Options:**
- `--fix` — Automatically fix issues where possible
- `--page TEXT` — Lint specific page
- `--all` — Lint all pages
- `--severity TEXT` — Minimum severity: info, warning, error

**Examples:**
```bash
saw lint --all
saw lint --page architecture.md
saw l --fix
```

---

### review

Review claims for accuracy.

```bash
saw review [OPTIONS]
```

**Options:**
- `--claim-id TEXT` — Review specific claim
- `--pending` — Review all pending claims
- `--approve` — Approve reviewed claims
- `--reject` — Reject reviewed claims

**Examples:**
```bash
saw review --pending
saw review --claim-id claim_123 --approve
```

---

### audit

Show audit trail and history.

```bash
saw audit [OPTIONS]
```

**Options:**
- `--claim-id TEXT` — Audit specific claim
- `--tail N` — Show last N entries
- `--since DATE` — Show entries since date
- `--format TEXT` — Output format: text, json

**Examples:**
```bash
saw audit --tail 50
saw audit --claim-id claim_123
saw audit --since "2026-01-01"
```

---

### conflicts

Show conflicting claims.

```bash
saw conflicts [OPTIONS]
```

**Options:**
- `--resolve` — Attempt automatic resolution
- `--page TEXT` — Show conflicts for specific page

**Examples:**
```bash
saw conflicts
saw conflicts --page architecture.md
saw conflicts --resolve
```

---

### freshness

Check content freshness status.

```bash
saw freshness [OPTIONS]
```

**Options:**
- `--check` — Check for staleness
- `--page TEXT` — Check specific page
- `--threshold DAYS` — Days threshold for stale

**Examples:**
```bash
saw freshness
saw freshness --check --threshold 90
```

---

### mcp

Manage MCP server for Claude Code integration.

```bash
saw mcp [OPTIONS]
```

**Options:**
- `--start` — Start MCP server
- `--stop` — Stop MCP server
- `--status` — Show server status
- `--tools` — List available MCP tools
- `--logs` — Show server logs

**Examples:**
```bash
saw mcp --start
saw mcp --status
saw mcp --tools
```

---

### tutorial

Start interactive tutorial.

```bash
saw tutorial [OPTIONS]
```

**Options:**
- `--step N` — Start from specific step (1-5)
- `--skip-demo` — Skip demo content creation
- `--reset` — Reset tutorial progress

**Examples:**
```bash
saw tutorial
saw tutorial --step 3
saw tutorial --reset
```

---

### config

Configure wiki settings (TUI interface).

```bash
saw config [OPTIONS]
```

**Options:**
- `--path PATH` — Config file path
- `--show` — Show current config without editing

**Examples:**
```bash
saw config
saw config --show
saw config --path ./my-wiki/saw.json
```

---

### completion

Generate shell completion scripts.

```bash
saw completion SHELL [OPTIONS]
```

**Arguments:**
- `SHELL` — Shell type: bash, zsh, fish

**Options:**
- `--install, -i` — Install completion script

**Examples:**
```bash
saw completion bash
saw completion zsh --install
saw completion fish --install
```

---

### feed

Manage RSS subscriptions.

```bash
saw feed [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**
- `add` — Add RSS feed subscription
- `list` — List subscribed feeds
- `sync` — Sync all feeds
- `remove` — Remove feed subscription

**Examples:**
```bash
saw feed add https://blog.example.com/rss
saw feed list
saw feed sync
```

---

### code-graph

Code graph lifecycle management — build, query, and maintain the code structure graph.

```bash
saw code-graph [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

#### build

Build the code graph from source files.

```bash
saw code-graph build [OPTIONS]
```

**Options:**
- `--full, -f` — Full rebuild (ignore cache)
- `--lang, -l TEXT` — Comma-separated languages (e.g., "python,typescript")
- `--no-postprocess` — Skip postprocess pipeline
- `--root, -r PATH` — Project root path (default: ".")

**Examples:**
```bash
saw code-graph build
saw code-graph build --full --lang python
saw code-graph build -r /path/to/project
```

#### update

Incremental update — only re-parse changed files (< 2s typical).

```bash
saw code-graph update [--root PATH]
```

#### health

Check code graph health (5 checks: empty graph, orphan edges, staleness, error rate, FTS).

```bash
saw code-graph health [--json] [--root PATH]
```

#### verify

Verify graph integrity (orphan edges, FTS consistency, file tracking).

```bash
saw code-graph verify [--root PATH]
```

#### stats

Show code graph statistics (nodes, edges, files, DB path).

```bash
saw code-graph stats [--root PATH]
```

#### search

Search code symbols by name or signature.

```bash
saw code-graph search QUERY [--kind TEXT] [--limit N] [--root PATH]
```

**Options:**
- `--kind, -k TEXT` — Filter by kind (function, class, method, type, test, endpoint)
- `--limit, -n N` — Max results (default: 10)

**Examples:**
```bash
saw code-graph search "authenticate"
saw code-graph search "User" --kind class
```

#### impact

Analyze impact of modifying a symbol (blast radius).

```bash
saw code-graph impact TARGET [--direction TEXT] [--depth N] [--root PATH]
```

**Options:**
- `--direction, -d TEXT` — "upstream" (dependents) or "downstream" (dependencies)
- `--depth N` — Max traversal depth (default: 3, max: 5)

**Examples:**
```bash
saw code-graph impact "AuthService"
saw code-graph impact "handleLogin" --direction downstream --depth 2
```

---

## Global Options

These options apply to all commands:

- `--help` — Show help message
- `--version` — Show version
- `--debug` — Enable debug mode
- `--quiet` — Suppress non-error output
- `--config PATH` — Use custom config file

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SAW_CONFIG` | Custom config file path |
| `SAW_DEBUG` | Enable debug mode |
| `SAW_DATA_DIR` | Custom data directory |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |

---

## Help System

```bash
# General help
saw --help

# Command help
saw <command> --help
saw help <command>

# Examples: Get detailed command help
saw ingest --help
saw help query
```

---

*Last updated: 2026-05-05*