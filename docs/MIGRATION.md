# Migration Guide

This guide helps you upgrade between versions of Smart Agent Wiki.

## Table of Contents

1. [v3.4 → v3.5](#v34--v35)
2. [v3.3 → v3.4](#v33--v34)
3. [v3.2 → v3.3](#v32--v33)
4. [General Upgrade Process](#general-upgrade-process)

---

## v3.4 → v3.5

### Summary

v3.5 focuses on Developer Experience with installation improvements, interactive tutorials, and CLI usability enhancements.

### Breaking Changes

**None** — v3.5 is fully backward compatible with v3.4.

### New Features

| Feature | Description |
|---------|-------------|
| `saw tutorial` | Interactive 5-step guided tutorial |
| `saw config` | TUI configuration wizard |
| Short aliases | `saw i`, `saw q`, `saw s`, `saw w` |
| Shell completion | bash/zsh/fish auto-completion |
| Friendly errors | Suggestions instead of stack traces |
| curl install | One-line installation script |

### Recommended Actions

```bash
# 1. Update installation
pipx upgrade smart-agent-wiki

# Or with Homebrew
brew upgrade saw

# Or with curl
curl -fsSL https://get.saw.wiki | bash

# 2. Run interactive tutorial
saw tutorial

# 3. Configure settings (optional)
saw config

# 4. Enable shell completion
saw completion bash --install  # or zsh/fish

# 5. Try short aliases
saw i document.pdf  # same as saw ingest
saw q "topic"       # same as saw query
```

---

## v3.3 → v3.4

### Summary

v3.4 introduces Code Intelligence features including DAG pipeline validation, impact analysis, and process detection.

### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| DAG pipeline API | Internal API only | No CLI impact |
| `pipeline.py` moved | Module rename | Update imports if using SDK |

### New Features

| Feature | Description |
|---------|-------------|
| DAG pipeline | Type-safe ingestion with dependency validation |
| Impact analysis | `saw impact <symbol>` — trace dependencies |
| Process detection | `saw process <entry>` — trace execution flow |
| Agent Skills | `.claude/skills/saw/` — Claude Code integration |
| Staleness detection | Auto-detect outdated wiki content |

### Recommended Actions

```bash
# 1. Update installation
pipx upgrade smart-agent-wiki

# 2. Test new features
saw impact main.main
saw process api.routes.health

# 3. Check staleness
saw freshness --check

# 4. Install Claude Code skills (if using Claude)
cp -r .claude/skills/saw/ ~/.claude/skills/
```

---

## v3.2 → v3.3

### Summary

v3.3 introduces the Tauri desktop application with native file system integration.

### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| Web UI URL | `localhost:3000` → `localhost:8000` | Update bookmarks |
| Config format | YAML → JSON | Run `saw config` to convert |

### New Features

| Feature | Description |
|---------|-------------|
| Desktop app | Native Tauri application |
| Drag-drop | Drag files into app window |
| File watching | Auto-sync when files change |
| URL protocol | `saw://` links open app |

### Recommended Actions

```bash
# 1. Update installation
pipx upgrade smart-agent-wiki

# 2. Install desktop app (optional)
# Download from: https://github.com/chensaics/smart_agent_wiki/releases

# 3. Migrate config
saw config --migrate

# 4. Update bookmarks
# Change http://localhost:3000 → http://localhost:8000
```

---

## General Upgrade Process

### Step 1: Backup

```bash
# Backup wiki data
tar -czf saw-backup-$(date +%Y%m%d).tar.gz vault/ wiki/ claims/

# Backup database
cp wiki.db wiki.db.backup
```

### Step 2: Update

```bash
# pipx
pipx upgrade smart-agent-wiki

# Homebrew
brew upgrade saw

# Docker
docker pull chensaics/saw:latest

# Manual
curl -fsSL https://get.saw.wiki | bash
```

### Step 3: Verify

```bash
# Check version
saw --version

# Verify installation
saw status

# Test basic functionality
saw query "test" --mode direct
```

### Step 4: Cleanup (Optional)

```bash
# Remove old version caches
rm -rf ~/.cache/saw/old/

# Optimize database
saw lint --fix --optimize
```

---

## Rollback Procedure

If you need to revert to a previous version:

```bash
# pipx rollback
pipx install smart-agent-wiki==3.4.0

# Homebrew rollback
brew install saw@3.4

# Docker rollback
docker pull chensaics/saw:v3.4.0

# Restore backup
tar -xzf saw-backup-YYYYMMDD.tar.gz
```

---

## Version History

| Version | Release Date | Major Features |
|---------|-------------|----------------|
| v3.5 | 2026-05-05 | Developer Experience |
| v3.4 | 2026-05-04 | Code Intelligence |
| v3.3 | 2026-05-04 | Desktop App |
| v3.2 | 2026-05-03 | Platform Enhancements |
| v3.1 | 2026-05-02 | Third-Party Integrations |
| v3.0 | 2026-05-01 | Ecosystem Integration |
| v2.0 | 2026-04-30 | Extended Ingestion |
| v1.1 | 2026-04-29 | Collaboration |

---

*Last updated: 2026-05-05*