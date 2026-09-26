---
id: PRD-wiki-index-resilience-v1.30.2
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
roadmap_ref: ROADMAP
target_version: v1.30.2
type: fix
see_also: .csp/audit/AUDIT-FINDINGS-v1.30.0.json (AUDIT-F-03)
---

# PRD — v1.30.2 wiki 索引 YAML 韧性 (PATCH fix)

## 背景
v1.30.0 审计 AUDIT-F-03 [P1 resilience]：`saw web` 启动时 `WikiIndexer.index_all()` 读到坏 YAML front-matter 的 wiki 页（如 `.claude/skills/csp-workflow/commands/csp-test-spec.md`，"mapping values are not allowed"）→ `wiki_repo.read()` raise `StorageError` → 整库索引失败（all-or-nothing）。一个坏页阻断全部 wiki 搜索索引。

## 范围（1 fix）
- **AUDIT-F-03**: `WikiIndexer.index_all()` per-page 容错——坏页 skip + warn + 继续，整库索引不被单页阻断。

## 非目标
- 不改 `wiki_repo.read()` 行为（仍 raise StorageError，调用方决定容错策略）。
- 不修坏页本身（`.claude/skills/...` 是外部内容）。

## 成功指标
- 含 1 坏页 + N 好页的 wiki：`index_all()` 返回 N（好页数），不 raise，坏页 warn。
- 现有 wiki_indexer 测试不回归。
