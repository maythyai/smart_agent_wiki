---
id: PRD-debt-closure-v1.6.0
title: workspace 全路径 II + 深覆盖 + policy web 端点
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-03"
product_type: platform
feature_count: 4
mvp_scope: [workspace-routing-ii, ingest-workspace-write, query-deep-coverage, policy-web-endpoint]
thin_sections: [4]
upstream_source: "docs/strategy/ROADMAP.md#v1.6.0 + .csp/artifacts/retrospective-v1.5.0.md (findings I1-I4)"
target_version: v1.6.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-intelligence-adaptation.md
  - .csp/product-spec/PMS-security-hardening.md
  - .csp/product-spec/PMS-test-gate.md
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.5.0.md
---

# PRD-debt-closure-v1.6.0：workspace 全路径 II + 深覆盖

> v1.5.0 闭环后的新一轮 01。**债务收口周期**：延续 v1.5.0 未竟的 workspace 全路径路由（I1）+ coverage 65（I2）+ policy web 端点（I4）。不开新能力——先把 v1.5.0 标 thin 的债清干净。

## 1. 背景与动机（roadmap v1.6.0 + 复盘 I1-I4）

v1.5.0 把 workspace scope 注入到 claims search/get_by_id + QueryEngine 搜索路径，并修了 query-cache 跨 ws 泄漏。但**全路径未做**（retrospective-v1.5.0.md I1）。复盘回流：
- **I1**：workspace 路由仅搜索路径；tree_mode / compiler / ingest 写入未注入 → 本轮补。
- **I2**：coverage 棘轮仅 63（未达 65）；query engine.py 14% / compare 23% / tree_mode 21% 是杠杆点 → 本轮补深覆盖。
- **I4**：policy reload 仅 CLI，Web admin 端点 defer → 本轮补 `POST /api/admin/policy/reload`。
（I3 resume 全量快照标 v2.0；I5 脏工作区治理性，本轮不触。）

## 2. 范围（4 Feature 组）

### F-J-1：workspace 读取路径全路由（tree_mode + compiler）
v1.5.0 做了 search 路径；本轮把 workspace scope 注入 tree_mode（`engines/query/tree_mode.py`）+ ContextCompiler（`engines/query/compiler.py`）——两者调 `claims_repo.get_by_id/get_by_source` 但未传 workspace_id。QueryEngine 持 workspace_id 透传。
- **AC-WS-4**：tree_mode + compiler 路径跨 workspace 隔离（A ws claim 不在 B ws tree/compile 结果）。

### F-J-2：workspace 写入路径（insert 持久化 + ingest 透传）
v1.5.0 发现 `Claim.workspace_id` 字段存在但 `SQLiteClaimsRepository.insert` 的 SQL **丢弃 workspace_id**（只写列默认 'default'）→ 写入永远落 default。本轮：insert SQL 补 workspace_id 列；IngestPipeline 持 workspace_id 透传到 Claim 构建。
- **AC-WS-5**：ingest 到 workspace "alpha" 的 claim 落 alpha（非 default），且 B ws 不可见。

### F-J-3：query 深覆盖（engine/compare/tree_mode → 65%）
补 `engines/query/engine.py`（14%）/ `compare.py`（23%）/ `tree_mode.py`（21%）测试；coverage fail_under 63→65。
- **AC-COV-2**：query 子模块覆盖提升，全量 coverage ≥ 65%（棘轮上调）。

### F-J-4：policy reload Web admin 端点
v1.5.0 CLI 已落；本轮补 `POST /api/admin/policy/reload`（admin-only，复用 RBAC）。
- **AC-SEC-6**：admin 触发 Cedar 热加载（Web 端点，403 非 admin）。

### F-debt-carried（源自 I1/I2/I4）
- I1 → F-J-1/F-J-2；I2 → F-J-3；I4 → F-J-4。

## 3. 非目标
- graph_traverse 的 workspace 隔离（entity 表无 workspace_id，需 migration → 标 finding，defer v1.7.0）。
- resume 全量 context 快照（I3，v2.0）。
- 脏工作区治理（I5，非功能性）。
- coverage 80%（north-star 不变，本轮只到 65）。

## 4. 风险
- **F-J-2 insert SQL 改**：补 workspace_id 列到既有 INSERT，须保 backward compat（既有调用 Claim.workspace_id 默认 'default' → 行为不变）。
- **F-J-3 coverage 65**：须实测达 65 再设 fail_under（硬约定 #10）；若 engine.py 深覆盖成本高，65 不达则 ratchet 到实测值。
- **F-J-4 Web 端点**：须 admin RBAC 守（复用 require_role("admin")），勿裸暴露。

## 5. 下游衔接
- → 02 拆解：F-J-1..4 各拆 Feature + DAG；F-J-1/J-2 共享 workspace 域。
- → 03：F-J-2 insert 列变更需 ADR-008（workspace 写入策略）；F-J-4 RBAC 守卫。
- → 04：~6-7 Task；F-J-3 测试独立 Wave；F-J-1/J-2 触 query/ingest 核心串行。
