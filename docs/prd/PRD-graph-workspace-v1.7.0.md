---
id: PRD-graph-workspace-v1.7.0
title: graph workspace 隔离 + scope 清理 + coverage 收口
version: 1.0
status: Released
author: lifecycle-orchestrator
date: "2026-09-04"
product_type: platform
feature_count: 3
mvp_scope: [graph-workspace-isolation, scope-propagation-cleanup, coverage-65]
thin_sections: [3]
upstream_source: "docs/strategy/ROADMAP.md#v1.7.0 + .csp/artifacts/retrospective-v1.6.0.md (findings J1-J3)"
target_version: v1.7.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-debt-closure.md
  - .csp/product-spec/PMS-test-gate.md
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.6.0.md
---

# PRD-graph-workspace-v1.7.0：graph 隔离 + 清理 + 覆盖

> v1.6.0 闭环后的新一轮 01。**债务收口 III**：收 graph workspace 隔离（J2，最后一块——读完写+graph 全闭环）+ scope 传播清理（J3）+ coverage 推向 65（J1）。

## 1. 背景与动机（roadmap v1.7.0 + 复盘 J1-J3）

v1.6.0 把 workspace 读写双闭环（claim 读全路径 + insert/ingest 写）。但 **graph 路径未隔离**（retrospective-v1.6.0.md J2）：`entity`/`entity_relation` 表无 workspace_id 列，`graph_traverse._load_graph` 全量加载，跨 ws 可互查。复盘回流：
- **J2**：graph_traverse 隔离需 entity 表加 workspace_id（migration v9）+ graph 路由注入 → 本轮做。
- **J3**：QueryEngine 用 setattr 同步子服务 _workspace_id，耦合私有属性 → 本轮清理为显式参数。
- **J1**：coverage 63.7%，gap 在 compile/compiler 17% / synthesize/scheduler 32% → 本轮补 synthesize 测试推 ratchet。

## 2. 范围（3 Feature 组）

### F-K-1：graph workspace 隔离（读+写）
migration v9：`entity` 表加 `workspace_id`（default 'default'）+ index。Entity domain 加 workspace_id 字段；IngestPipeline stamp entities（同 F-J-2 claims 模式）；GraphSink INSERT 带 workspace_id 列；graph_traverse 加 workspace_id 过滤 `_load_graph`（只载该 ws entity + 其间 relation）。QueryEngine 透传 workspace_id 给 graph（GraphTraverse）。
- **AC-WS-6**：graph_traverse 跨 ws 隔离（A ws entity 不在 B ws 图遍历结果）。

### F-K-2：scope 传播清理（J3）
QueryEngine.__init__ 的 `setattr(_sub, "_workspace_id", ws)` → 改为 tree_mode.search / compiler.compile 接受显式 workspace_id 参数；QueryEngine 调用时透传。去私有属性耦合。
- **AC-ARCH-1**：QueryEngine 不再 setattr 子服务私有属性（lint/结构守）。

### F-K-3：coverage 推向 65（J1）
补 `synthesize/scheduler.py`（32%）+ `synthesize/engine.py`（37%）测试；coverage ratchet 63→64（实测达 64 设；65 仍 thin 若不达）。
- **AC-COV-3**：synthesize 子模块覆盖提升，全量 ratchet 63→64（≥64 实测后）。

## 3. 非目标
- compile/compiler.py 深覆盖（17%，复杂编译器，留 v1.8.0）。
- 65% 硬目标（north-star 80% 不变；本轮 ratchet 到实测值，硬约定 #10）。
- 新能力（本轮仍债务收口）。

## 4. 风险
- **F-K-1 migration v9**：entity 表 ALTER ADD workspace_id，须保 backward compat（default 'default'，既有 entity 落 default）。
- **F-K-1 GraphSink 写**：entity WriteOp payload 须带 workspace_id（pipeline stamp）；既有 op 无则 default。
- **F-K-2 接口改**：tree_mode.search/compiler.compile 加参数，默认 'default' backward compat；既有调用（engine._tree_query/_nl_query）透传。
- **F-K-3**：synthesize 测试须 mock LLM/scheduler（确定性）。

## 5. 下游衔接
- → 02 拆解：F-K-1..3 各拆 Feature + DAG；F-K-1 读+写共享 entity 域。
- → 03：F-K-1 需 ADR-009（entity workspace 隔离策略）。
- → 04：~5-6 Task；F-K-1 migration 串行；F-K-3 测试独立 Wave。
