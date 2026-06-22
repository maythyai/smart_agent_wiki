# CLAUDE.md

## Project Overview
Smart Agent Wiki (SAW) is a local-first multi-agent knowledge platform.
CLI: `saw` | Python 3.11+ | React 19 + TypeScript + Vite frontend | Tauri 2 desktop app.

## Key Commands

### Python Backend
- Install: `pip install -e ".[dev]"`
- Run CLI: `saw`
- Run tests: `pytest tests/`
- Lint: `ruff check src/`
- Start web server: `saw web`

### Web Frontend (web/)
- Install: `cd web && npm install`
- Dev: `cd web && npm run dev`
- Build: `cd web && npm run build`
- Test: `cd web && npm run test`
- Type check: `cd web && npx tsc --noEmit`

### Desktop (desktop/)
- Dev: `cd desktop && npm run tauri:dev`
- Build: `cd desktop && npm run tauri:build`

## Architecture
- Hexagonal architecture: domain/ (pure Python) → engines/ (business logic) → adapters/ (infrastructure) → drivers/ (CLI/Web/MCP)
- Five engines: Ingest, Query, Govern, Learn, Collaborate
- Write Queue (SQLite outbox) is the single mutation gateway
- Connectors framework: Notion, GitHub, Slack, Discord, Feishu, WeCom, Logseq
- 6 specialized agents: Librarian, Writer, Critic, Linker, Scholar, Guardian

## Code Style
- Python: Ruff for linting, type hints required on public APIs
- TypeScript: strict mode, no unused locals/params
- Follow existing patterns in each module
