# Migration Guide

This guide helps you upgrade between versions of Smart Agent Wiki.

## Table of Contents

1. [v3.4 → v3.5](#v34--v35)
2. [v3.3 → v3.4](#v33--v34)
3. [v3.2 → v3.3](#v32--v33)
4. [v1.2.0 行为变更](#v120-行为变更)
5. [General Upgrade Process](#general-upgrade-process)

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

## v1.2.0 行为变更

v1.2.0 不含 breaking API 变更，但调整了 2 处运行时默认行为。升级前请确认以下内容对部署与日志管道的影响。

### 行为变更一览

| 变更 | 此前行为 | v1.2.0 新行为 | 影响面 |
|------|----------|---------------|--------|
| JSON 日志默认开启 | 需 opt-in（`SAW_JSON_LOGS=1` 或 team 模式） | 生产环境默认 ON；team 模式强制 ON | 升级后日志格式由纯文本变 JSON |
| `/health/ready` engine-aware | DB + Redis 通即返回 200 | 新增 `check_engines`，引擎未就绪返回 503 | K8s readiness 探针变严 |

### 1. JSON 结构化日志默认 ON

**源码位置**：`src/saw/drivers/web/middleware/observability.py` → `init_observability`

v1.2.0 之前，JSON 结构化日志需要显式 opt-in（设置 `SAW_JSON_LOGS=1` 或启用 team 模式）。v1.2.0 起，生产环境默认输出 JSON 结构化日志；team 模式下强制开启，无法关闭。

**升级影响**：升级到 v1.2.0 后，日志输出格式将从纯文本变为 JSON。如果你有日志解析、grep 或基于正则的告警脚本，需适配 JSON 字段提取。

**Opt-out / 切回可读文本**（本地开发场景）：

```bash
# 方式一：切回纯文本可读日志（推荐本地 dev 使用）
export SAW_PRETTY_LOGS=1

# 方式二：显式关闭 JSON 日志
export SAW_JSON_LOGS=0
```

> 注意：team 模式下 JSON 日志强制 ON，上述环境变量不生效。

### 2. `/health/ready` 新增 engine-aware 检查

**源码位置**：`src/saw/drivers/web/health.py` → `readiness_check`

v1.2.0 之前，`/health/ready` 只要 DB + Redis 连通即返回 `200 ready`。v1.2.0 起新增 `check_engines`，会检查 `app.state` 上的 `query` / `collaborate` / `write_queue` 三个引擎是否已初始化；任一缺失即返回 `503 not_ready`。

**升级影响**：

- **K8s readiness 探针行为变严**：引擎未就绪时 Pod 不再接收流量（此前可能在引擎尚未初始化时误判为就绪）。
- 滚动更新期间，新 Pod 需等引擎初始化完成后才接流量，可能短暂延长启动到就绪的时间。
- 排查 `503 not_ready` 时，除 DB/Redis 连通性外，还需确认三个引擎是否完成初始化。

```bash
# 手动检查 readiness
curl -s http://localhost:8000/health/ready | jq .

# 引擎未就绪时返回示例：
# { "status": "not_ready", "reason": "engine not initialized: collaborate" }
```

### 升级检查清单

- [ ] 评估日志解析/grep 脚本是否需适配 JSON 格式
- [ ] 本地开发环境设置 `SAW_PRETTY_LOGS=1`
- [ ] 确认 K8s readiness 探针超时配置是否需放宽（引擎初始化耗时）
- [ ] 验证 team 模式部署的日志输出符合预期

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
pipx install smart-agent-wiki==1.0.1

# Homebrew rollback
brew install saw@1.0.1

# Docker rollback
docker pull chensaics/saw:v1.0.1

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
| v1.2.0 | 2026-04-29 | JSON log default ON, engine-aware readiness |
| v1.1 | 2026-04-29 | Collaboration |

---

*Last updated: 2026-05-05*