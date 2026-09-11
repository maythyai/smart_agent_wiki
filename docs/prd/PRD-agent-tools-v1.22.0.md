---
id: PRD-agent-tools-v1.22.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: Approved
roadmap_ref: ROADMAP
target_version: v1.22.0
see_also: docs/analysis/COMPETITIVE-REFERENCE.md (C1/C2) | .csp/product-spec/PMS-agent-tools.md
---

# PRD: agent-native tools — saw_resolve + saw_record (v1.22.0, C1/C2)

> 竞品借鉴 Phase 0.5 C1/C2（Potpie `resolve`/`record`）。强化 agent-native 定位。

## 1. 背景与价值
SAW 是 agent-native MCP 后端，但缺"改前任务级上下文召回"与"持久学习"两个原语。C1 `saw_resolve(task)` 聚合 claims+code+freshness 给 agent 改前读；C2 `saw_record(summary)` 把决策/约定持久化为 claim（经 Write Queue→receipt）。差异化：经 Write Queue 落库 = 可溯源 claim（非游离 note），与 Ed25519 receipt 闭环。

## 2. 需求（AC）
- **AC-C1-1**：`saw_resolve(task, limit)` 聚合 FTS5 claims（带 confidence+score）+ code graph symbols（best-effort）+ freshness 警告（level≥6 的 claim）。query_engine 未初始化→明确 error。
- **AC-C2-1**：`saw_record(summary, kind, confidence)` 经 Write Queue enqueue 一个 sink=claims 的 WriteOp（content=summary, source_uuid=agent:saw_record, tags=[kind]）；返回 recorded+op_id+claim_uuid。空 summary→error；无 write_queue→error。
- **AC-C1/C2-2**：工具经 `init_agent_tools` 注入（query_engine/code_graph_engine/write_queue），注册于 `tools/__init__.py`。
- **AC-C1/C2-3**：幂等（claim_uuid=op_id，ClaimsSink INSERT OR IGNORE）。

## 3. 非目标
- receipt 签名 wiring（经 dispatcher 自动 receipt，本周期不直签）。
- saw_resolve 的语义检索（本期用 FTS5；语义留后续）。

## 4. 验收
- 6 单测 pass（resolve 聚合/stale flag/no-engine；record enqueue/no-wq/empty）。
- 全量 gate 绿，零回归。
