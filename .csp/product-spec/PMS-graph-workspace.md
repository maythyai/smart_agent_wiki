---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-graph-workspace-v1.7.0.md]]"
  - "[[.csp/artifacts/retrospective-v1.6.0.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M09(query)/§M08(ingest+write_queue)"
created: "2026-09-04"
updated: "2026-09-04"
---

# PMS: graph-workspace（graph 隔离 + scope 清理 + 覆盖）

> v1.7.0 债务收口 III。收 graph workspace 隔离（最后一块，读完写+graph 全闭环）+ scope 传播清理 + coverage 推向 65。

## 模块边界
- **做什么**：
  - graph workspace 隔离（entity 表 workspace_id + graph_traverse 过滤 + Entity/GraphSink 写入透传）；
  - scope 传播清理（QueryEngine 显式 workspace_id 参数，去 setattr 私有属性）；
  - coverage 推向 65（synthesize/scheduler + engine 测试，ratchet 63→64）。
- **不做什么**：compile/compiler.py 深覆盖（留 v1.8.0）；新能力；65% 硬指标（ratchet 到实测）。
- **PMS 边界=PRD §2 F-K-1..3**。复用 v1.6.0 既有 workspace_id 原语 + claim 写模式（F-J-2）镜像到 entity。

## 验收形态
- graph_traverse 跨 ws 隔离（AC-WS-6）。
- QueryEngine 不再 setattr 子服务私有属性（AC-ARCH-1）。
- synthesize 覆盖提升，全量 ratchet ≥64（AC-COV-3）。

## 接口契约摘要（ground 自源码）
- entity 表：`adapters/storage/claims_repository.py:73` `_CLAIMS_CORE_SCHEMA`（entity 无 workspace_id）。
- graph_traverse：`engines/query/graph_traverse.py:GraphTraverse._load_graph`（全量 SELECT entity + entity_relation）+ `traverse`。
- Entity 写入：`write_queue/sinks/graph_sink.py:write`（INSERT entity，无 workspace_id 列，line 47）。
- Entity domain：`domain/`（无 workspace_id 字段，须加）。
- QueryEngine setattr：`engines/query/engine.py:__init__`（T-F-J-1 的 setattr 同步）。
- migration v9 槽：`db/migrations.py`（_register(9, ...) 待加）。

## 关联
- PRD: `docs/prd/PRD-graph-workspace-v1.7.0.md`
- 上游复盘: `.csp/artifacts/retrospective-v1.6.0.md`（J1/J2/J3）
- 复用 PMS: `PMS-debt-closure.md`（workspace 续）、`PMS-test-gate.md`（coverage）
- 下游 Spec: [待 03 回填] —— F-K-1..3 各 1 Spec
