---
id: PRD-provenance-activity-v1.31.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
roadmap_ref: ROADMAP
target_version: v1.31.0
type: feature
see_also: .csp/audit/AUDIT-FINDINGS-v1.30.0.json (AUDIT-F-05) | docs/analysis/AUDIT-TO-ROADMAP.md
---

# PRD — v1.31.0 Provenance Verification API + Activity 持久化

> feat MINOR（additive，无 breaking）。闭合 AUDIT-F-05 deferred-gate（activity 持久化）+ 暴露 provenance chain 为 REST。

## 背景
- AUDIT-F-05（v1.19.0 deferred-gate）：`AgentActivityTracker` 仅内存态（`activity_tracker.py:10` 注释 "not persisted PRD §3.3 rule 6"），进程重启 agent 活动计数全丢。多 agent 可观测性（v1.16 仪表盘）依赖此数据，重启后归零。
- 既有 `saw_verify` MCP 已返回 provenance chain（`governor.verify_claim`），但**无 REST 暴露**——外部应用/agent 须走 MCP，不能经 HTTP 验证 claim 溯源。

## 范围（3 项 feat）
1. **Activity 持久化**（AUDIT-F-05 闭合）：v12 migration `agent_activity` 表 + `AgentActivityTracker` write-through + 启动 load。重启不丢计数。
2. **`GET /api/v1/provenance/{claim_id}` REST**：trace claim → source chain（follow `source_uuid` 上溯至根）→ 返回链数组（uuid/content/source_uuid/page:line/confidence）+ receipt_id。外部应用可经 HTTP 验证溯源。
3. **`saw_verify` MCP 增强**：output 增 `receipt_id`（从 receipts 表查 claim_uuid）+ `source_claim_uuid`。

## 非目标（拆 v1.31.1，deferred 附解除条件）
- **contamination scan**（检测衍生自过期/被取代源的 claim）：需 freshness + supersede 状态逻辑，是独立能力 → v1.31.1 MINOR。解除条件：v1.31.0 释放后开 v1.31.1 01。

## 成功指标
- Activity 跨重启不丢：写计数 → 重启 → load → 计数一致（单测）。
- `/api/v1/provenance/{id}` 返回链（含根源 page:line + receipt_id）。
- saw_verify output 含 receipt_id + source_claim_uuid。
- pytest 0 fail / ruff 0 / coverage 不回归 / tsc clean。

## 留尾
- contamination scan → deferred v1.31.1（附解除条件，计入 v1.31.1 01 入口清单 + 本版 Release notes）。
