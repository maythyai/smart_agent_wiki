---
id: PRD-v1.35-structured-context-api
project: smart-agent-wiki
version: 1.1
last_updated: 2026-11-06
status: Approved
prd_depth: engineering
upstream_source: docs/strategy/ROADMAP.md#v1.35.0
roadmap_ref: ROADMAP
target_version: v1.35.0
type: feature
tracks: [intelligence-adaptation]
see_also: .csp/convergence/CONVERGED-FEATURE-PLAN.md
---

# PRD — v1.35.0 Structured Context API v1（工程级, ★品类定位）

## §1 背景与目标
2026.09 行业论点 "Structured Context Infrastructure"（vector+graph+ontology+state+permission+action）。SAW 架构覆盖六要素但未统一暴露。本版**品类定位**：`saw_context` 统一 API 抢占"agent 可信编译知识层"。

**目标**：统一检索路由 + state 层过滤（freshness/confidence）+ 基础 permission（workspace）。v1.34.1 deferred coverage/god-files 顺带推进。

## §3 功能设计

### F1: `saw_context` 统一 MCP+REST 接口（P0）
- **用户故事**：agent 经单一 `saw_context(query, mode, filters)` 获取结构化 context bundle。
- **业务规则**：
  1. mode = `semantic` | `graph` | `drift` | `hybrid`（hybrid=semantic+graph 合并）。
  2. filters: `freshness_min`（int 0-8，默认 0=不过滤）、`confidence_min`（str unverified/single_source/cross_validated/human_verified，默认不过滤）、`workspace_id`（默认 contextvar）。
  3. 返回 unified bundle: `{mode, query, claims: [...], graph: {nodes, edges}, metadata: {total_claims, filtered_out, elapsed_ms}, receipts_included}`。
  4. claims 经 post-filter（freshness/confidence）后返回；filtered_out 计数诚实。
  5. 既有 saw_query/saw_search/saw_drift_search 保留（saw_context 为上层封装，不替代）。
- **AC**：
  1. `saw_context(query="test", mode="semantic")` → 返回 claims+metadata bundle。
  2. `mode="hybrid"` → claims+graph 均非空（有数据时）。
  3. `confidence_min="cross_validated"` → 仅返回 ≥cross_validated 的 claim；filtered_out>0 诚实。

### F3: state 层过滤（P1，并入 F1 实现）
- **业务规则**：freshness_min/confidence_min 作 query filter；低置信 claim 默认不排除（除非 filter 显式设定）。

### F5: permission 维度（P2 部分）
- **业务规则**：workspace_id filter 走既有 contextvar（per-request ws）。

### F2/F4: deferred → v1.35.1
- F2 ontology 层（concept type/relations 抽取设计较大）。
- F4 自适应路由（confidence 门控扩展）。

## §6 验收标准（GWT）
- **GWT-1**: Given semantic mode; When saw_context(query); Then bundle.claims 非空 + metadata.elapsed_ms > 0。
- **GWT-2**: Given confidence_min="cross_validated" + 库中有 unverified+cross_validated claims; When saw_context; Then 仅返回 cross_validated + filtered_out ≥ 1。
- **GWT-3**: Given mode="graph"; When saw_context; Then bundle.graph 含 nodes/edges（或空数组+note）。
- **GWT-4**: REST `POST /api/v1/context` 返回同 MCP bundle。
- **回归**: pytest 0 fail / ruff 0 / tsc clean / MCP 工具 39→40（expected+README 同步）。

## §8 风险与依赖
- 前置 v1.34.1 ✓。
- R1: QueryEngine 方法签名差异（semantic/graph/drift 参数不同）→ 统一 wrapper 适配。
- R2: freshness 数据不总是存在（last_accessed NULL）→ filter 对 NULL 视为 0（最不新鲜）。
- thin_sections: ontology schema → v1.35.1。