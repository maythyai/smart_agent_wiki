# ADR-009: Entity Workspace 隔离策略

## 状态：Accepted
## 上下文
v1.6.0 闭环了 claim 的 workspace 读写隔离（ADR-007 读 + ADR-008 写）。但 `entity` / `entity_relation` 表无 `workspace_id` 列（migration v8 只加在 claim）。`graph_traverse._load_graph`（`engines/query/graph_traverse.py`）全量 SELECT entity + entity_relation 载入 NetworkX，跨 ws 可互查（retro J2）。GraphSink 写 entity 也无 workspace_id（`write_queue/sinks/graph_sink.py:47`）。
## 决策
1. **migration v9**：`entity` 表加 `workspace_id TEXT NOT NULL DEFAULT 'default'` + index。entity_relation 不加列（关系通过 source/target entity 的 workspace 间接过滤——graph_traverse 只载该 ws entity，关系两端须都在该 ws）。
2. **Entity domain 加 workspace_id 字段**（default 'default'，镜像 Claim v1.4.0 模式）。
3. **写路径**：IngestPipeline stamp entities（同 F-J-2 claims 模式）；GraphSink INSERT 带 workspace_id 列。
4. **读路径**：graph_traverse 加 `workspace_id` 参数，`_load_graph` SQL 加 `WHERE workspace_id = ?`（entity + relation 须两端都属该 ws——relation 加 `JOIN entity` 过滤两端）。QueryEngine 透传 workspace_id 给 GraphTraverse。
## 备选方案
| 方案 | 优势 | 劣势 | 适用 |
|---|---|---|---|
| entity 加列 + 关系两端过滤（选） | 复用 claim 模式，零语义变化 | relation 过滤须 JOIN | 本轮 ✓ |
| entity_relation 加 workspace_id 冗余列 | 查询简单 | 冗余 + 一致性维护 | 不值得 |
| graph 完全重建 per ws | 强隔离 | 性能（每次重载）| 不适用 |
## 理由
镜像 claim 隔离模式（ADR-007/008）到 entity，架构一致。relation 两端过滤保证图连通性在 ws 内闭合（跨 ws 边不出现）。default 'default' 保单机兼容。
## 后果
- 正：graph 跨 ws 隔离；workspace 读写+graph 三闭环。
- 负：relation 过滤须 JOIN entity 两端（性能可接受，图规模小）。
- 风险：既有 entity 落 default，单机行为不变。
## 关联 Feature
F-K-1（AC-WS-6）。依赖 ADR-005（workspace 原语）+ ADR-007/008（claim 读写）。
