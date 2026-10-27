---
id: PRD-v1.34.1-core-trust-hardening
project: smart-agent-wiki
version: 1.1
last_updated: 2026-10-27
status: Approved
prd_depth: engineering
upstream_source: docs/strategy/ROADMAP.md#v1.34.1
roadmap_ref: ROADMAP
target_version: v1.34.1
type: feature
tracks: [core-trust]
see_also: .csp/convergence/CONVERGED-FEATURE-PLAN.md | .csp/audit/AUDIT-FINDINGS-v1.30.0.json
---

# PRD — v1.34.1 core-trust 硬化 + coverage 70%（工程级）

## §1 背景与目标
v1.34.0 shipped wiki 根性能 + coverage 推进（68.43%→68.74%, gate 68）。收敛闸门通过（CVG-001 纳入）。AUDIT-F-01/04 + CRITIC-F-01 + stale-freshness (v1.31.1 deferred) 闭合或推进。

**目标**：coverage ≥70% + compiler.py 拆分 <600L + stale-freshness contamination + Dashboard 修复。

## §3 功能设计

### F1: coverage → 70%（AUDIT-F-04 partial close）
- **用户故事**：DEV 跑 CI 时 coverage gate 不踩线。
- **优先级**：P0
- **业务规则**：
  1. 补 `extract.py` 测试——`_extract_claims/_extract_entities` 用 async mock LLM；每个 helper 2-3 个 test case。
  2. fail_under bump: 68 → 70（pyproject.toml）。
  3. 若 coverage 增量不足到 70%：诚实标 gap + defer 余量到 v1.34.2（不 fake pass）。
  4. 测试不引入新 fixture 依赖（用 `pytest-asyncio` 已有 + `unittest.mock.AsyncMock`）。
- **AC**：
  1. Given `pytest -q --cov=src/saw --cov-fail-under=70` → exit 0。
  2. Given 新增 extract.py tests，Given 每个 helper 至少 2 个 test case。
  3. Given coverage 报告显示 extract.py ≥ 40%（从 14% 提升）。

### F2: god-files 拆分起步——compiler.py（AUDIT-F-01 partial）
- **用户故事**：维护者审查 compiler.py 时不需翻 600+ 行。
- **优先级**：P1
- **业务规则**：
  1. `src/saw/engines/compile/compiler.py`（663L）→ 提取 `synthesize` 相关逻辑到 `src/saw/engines/compile/synthesizer.py`（≤200L）。
  2. compiler.py 保留 compile 核心 + synthesize 调用（import 替换）。
  3. 公开接口不变（`ContextCompiler` 类 API 不变）。
- **AC**：
  1. Given `wc -l src/saw/engines/compile/compiler.py` < 600。
  2. Given 既有 compile 测试全部 pass（无回归）。
  3. Given `from saw.engines.compile.compiler import ContextCompiler` 仍可用。

### F3: stale-freshness contamination（v1.31.1 deferred）
- **用户故事**：Guardian 巡检时标出"衍生自过期源"的 claim。
- **优先级**：P1
- **业务规则**：
  1. 复用 `scan_contamination()`（v1.31.1）；新增 `reason="stale_source"` 判定。
  2. stale 判定：source claim 的 `last_accessed` 早于 `N days ago`（默认 90d，config 可配 `SAW_STALE_THRESHOLD_DAYS`）。
  3. 与既有 `reason="superseded_source"` 并列（二者独立，一个 claim 可同时命中）。
  4. 若 source claim 不存在或被 purged → 不标记（无法判定 freshness）。
- **AC**：
  1. Given source claim last_accessed >90d ago；Given derived claim exists；When `scan_contamination()` → returns derived claim with reason="stale_source"。
  2. Given `SAW_STALE_THRESHOLD_DAYS=30` → threshold 30d。
  3. Given source claim purged（不存在）→ 不标记。

### F4: Dashboard 按钮去重 + 状态卡（CRITIC-F-01）
- **用户故事**：OPS/Dashboard 用户看到状态概览而非 nav 替代。
- **优先级**：P2
- **业务规则**：
  1. `web/src/pages/Dashboard.tsx`：移除 "View Graph"/"Search Pages"/"Manage Integrations" 按钮（nav 已覆盖）。
  2. 改为状态卡组件 `StatusCards`：队列深度（/api/v1/write-outbox/pending count）、最近 agent 活动（/api/v1/agents 聚合）、矛盾数（/api/v1/contradictions pending count）。
  3. 保留 "Run"（workflow 触发按钮）——非 nav 重复。
- **AC**：
  1. Given Dashboard 加载 → 无 "View Graph"/"Search Pages"/"Manage Integrations" 按钮。
  2. Given Dashboard 加载 → 有 StatusCards 组件显示队列深度/agent 活动/矛盾数。
  3. Given API 返回数据 → StatusCards 显示正确计数。

## §6 验收标准（全版本 GWT）
- **GWT-F1-1**: `pytest --cov-fail-under=70` → exit 0, total ≥70%。
- **GWT-F2-1**: `wc -l compiler.py` < 600 + 既有 test pass。
- **GWT-F3-1**: `scan_contamination()` returns `{reason:"stale_source", source_uuid, claim_uuid}` for claim with stale source。
- **GWT-F4-1**: Dashboard DOM 不含 "View Graph" 按钮；含 StatusCards。
- **回归**: ruff 0 / pytest 0 fail / tsc clean / vitest pass。

## §8 风险与依赖
- 前置：v1.34.0 ✓。
- R1: extract.py async mock 复杂 → 可能 coverage 增量不够 70%。缓解：诚实标 gap + defer 余量 v1.34.2。
- R2: compiler.py synthesize 提取可能 cyclic import → 加 `from __future__ import annotations` + 单文件测试。
- R3: Dashboard StatusCards 接 3 个 API → API 404（数据依赖）可能空态。缓解：空态展示 "--" + retry。