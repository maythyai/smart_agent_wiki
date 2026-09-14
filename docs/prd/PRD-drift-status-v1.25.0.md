---
id: PRD-drift-status-v1.25.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: Approved
roadmap_ref: ROADMAP
target_version: v1.25.0
see_also: docs/analysis/COMPETITIVE-REFERENCE.md (A3/B3)
---

# PRD: DRIFT 混合检索 + claim 状态轴 (v1.25.0)

> 竞品借鉴 A3（GraphRAG DRIFT 检索）/ B3（GraphRAG claim TRUE/FALSE/SUSPECTED 状态轴）。

## 1. 背景
- **A3 saw_drift_search(query, depth)**：GraphRAG DRIFT = global（社区）+ local（实体邻域）混合，按置信门控扩展深度。SAW 落地：primer（semantic 找 top claims→community_of 广角）+ follow-up（traverse 局部邻域细化）。建在 A2 communities + semantic 之上。差异化：扩展用 SAW 4 级置信门控（低置信不扩展）。
- **B3 ClaimStatus**：GraphRAG claim 带 TRUE/FALSE/SUSPECTED 状态+时间界。SAW 落地：`ClaimStatus` 枚举 + `derive_claim_status(confidence, contradicted, resolution)`——复用 4 级置信 + B1 contradicts 边的 resolution 派生，不另造维度。差异化：与 Ed25519 receipt + contradicts 边闭环。

## 2. AC
- **AC-A3-1**：`saw_drift_search(query, depth, limit)` 返回 `{broad: community, follow_ups: [{entity, neighbors}], claims: [{uuid, content, confidence, status, score}]}`；无 query_engine→error。
- **AC-B3-1**：`ClaimStatus`（TRUE/FALSE/SUSPECTED）+ `derive_claim_status(confidence, contradicted, resolution)`：高置信无矛盾→TRUE；低置信→SUSPECTED；矛盾+SUPERSEDED→FALSE；矛盾+DISPUTED/HISTORICAL→SUSPECTED。
- **AC-B3-2**：`Claim.status` 属性（confidence-based）；saw_search + saw_drift_search 输出带 `status` 字段。

## 3. 非目标
- DRIFT 社区报告 LLM 摘要（仅结构社区，报告留后续）。
- claim 时间界（B3 仅 status，不加时间区间列）。

## 4. 验收
- B3: 5 测试（TRUE/SUSPECTED/FALSE/disputed-historical/Claim.status 属性）✓
- A3: 3 测试（claims 带 status / broad community / no-engine）✓
- 全量 gate 绿，零回归。
