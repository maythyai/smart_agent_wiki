---
id: PRD-v1.34.1-core-trust-hardening
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: Draft
prd_depth: planning
upstream_source: docs/strategy/ROADMAP.md#v1.34.1
roadmap_ref: ROADMAP
target_version: v1.34.1
type: feature
tracks: [core-trust]
---

# PRD — v1.34.1 core-trust 硬化 + coverage 70%（规划级）

## §1 背景与目标
v1.34.0 shipped wiki 根性能 + coverage 推进（parse 13→77%, validate 15→87%, total 68.74%），但 70% target 未达。AUDIT-F-01 (god-files) + AUDIT-F-04 (coverage) + stale-freshness contamination (v1.31.1 deferred) 仍 open。CRITIC-F-01 (Dashboard 按钮→nav 重复) 折入本版。

**目标**：coverage ≥70%（fail_under 68→70）；god-files 拆分起步（compiler.py/engine.py）；stale-freshness contamination 实现；Dashboard 按钮去重。

## §3 功能设计

### F1: coverage → 70%（AUDIT-F-04）
- **用户故事**：开发者跑 CI 时 coverage gate 不再踩线。
- **优先级**：P0
- **关键规则要点**：① 补 extract.py 测试（async mock LLM）；② 补 feed_cmd.py 测试（CliRunner + mock DB）；③ 补 learn.py 测试。
- **主流程**：补 thin 模块 unit tests → coverage ≥70% → fail_under=70。

### F2: god-files 拆分起步（AUDIT-F-01）
- **用户故事**：维护者审查代码时 god-file 不超过 600 行。
- **优先级**：P1
- **关键规则要点**：① compiler.py (663L) → 提取 synthesize 子模块；② engine.py (631L) → 已 v1.19 拆过, 评估再拆 ANN helpers。
- **主流程**：提取子模块 → 原文件 <600L → 测试不回归。

### F3: stale-freshness contamination（v1.31.1 deferred）
- **用户故事**：Guardian 巡检时标出"衍生自过期源"的 claim。
- **优先级**：P1
- **关键规则要点**：① 复用 FreshnessTracker（9 级 freshness）；② source claim freshness ≤ LEVEL_2 → 标 contaminated；③ 合并入既有 `scan_contamination()`（加 reason="stale_source"）。
- **主流程**：FreshnessTracker.get_freshness(source_claim) ≤ threshold → flag。

### F4: Dashboard 按钮去重（CRITIC-F-01）
- **用户故事**：Dashboard 聚焦状态卡，不当 nav 替代。
- **优先级**：P2
- **关键规则要点**：① 移除 "View Graph"/"Search Pages"/"Manage Integrations" 按钮（nav 已覆盖）；② 改为状态卡（队列深度/最近 ingest/矛盾数/freshness）。
- **主流程**：Dashboard → 状态卡（接 /api/dashboard/stats + /api/v1/workflows + /api/v1/contradictions）。

## §6 验收标准
- **AC-F1**：pytest --cov-fail-under=70 → exit 0。
- **AC-F2**：compiler.py < 600 行（wc -l 验证）。
- **AC-F3**：scan_contamination() 返回 stale_source 命中（claim source freshness ≤ LEVEL_2）。
- **AC-F4**：Dashboard 无 "View Graph"/"Search Pages" 按钮；有状态卡。

## §8 风险与依赖
- 前置：v1.34.0 ✓。
- R1: extract.py async+LLM 测试需 mock——可能 coverage 增量不够到 70%。缓解：尽力推 + 诚实标残余 gap。
- thin_sections: extract.py mock 策略、feed_cmd.py DB mock 策略 → 01 升级补全。
