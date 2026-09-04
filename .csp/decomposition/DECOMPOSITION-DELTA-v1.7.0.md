# Decomposition Delta — v1.7.0（2026-09-04）

> 新一轮 02 拆解 delta。源自 PRD-graph-workspace-v1.7.0 + retrospective-v1.6.0.md findings J1/J2/J3。
> debt-closure III track：3 Feature（F-K-1..3），graph 隔离（最后一块）+ scope 清理 + 覆盖。

## 新增 Feature

| id | name | domain | priority | complexity | depends_on | wave | blocked_by | source | AC |
|---|---|---|---|---|---|---|---|---|---|
| F-K-1 | graph workspace 隔离（migration v9 + graph_traverse 过滤 + Entity/GraphSink 写） | graph-workspace | P0 | M | — | 1 | — | retro J2 | AC-WS-6 |
| F-K-2 | scope 传播清理（QueryEngine 显式 workspace_id 参数，去 setattr） | graph-workspace | P1 | S | F-K-1 | 2 | — | retro J3 | AC-ARCH-1 |
| F-K-3 | coverage→65（synthesize/scheduler+engine 测试，ratchet 63→64） | graph-workspace | P1 | M | F-K-1 | 2 | — | retro J1 | AC-COV-3 |

## 原子 Feature → Spec 映射（03 1:1）
- F-K-1 → SPEC-F-K-1（graph workspace 隔离：migration v9 + 读写）
- F-K-2 → SPEC-F-K-2（scope 显式参数化）
- F-K-3 → SPEC-F-K-3（synthesize 覆盖 + 棘轮）
> 3 原子 Feature = 3 Spec。

## DAG delta
```
F-K-1 ──▶ F-K-2   (K-2 改 QueryEngine scope 传播，在 K-1 QueryEngine 改后)
F-K-1 ──▶ F-K-3   (K-3 graph 覆盖测试在 K-1 后)
```
- K-1 → K-2/K-3（K-2/K-3 在 K-1 代码落定后）。
- K-1 读+写共享 entity 域（migration + GraphSink + graph_traverse + Entity domain + pipeline stamp）。
- 无新环。

## Wave 重排（v1.7.0）
- **Wave 1**：F-K-1（graph 隔离——migration v9 串行 + graph_traverse + GraphSink + Entity domain + pipeline stamp）
- **Wave 2（并行）**：F-K-2（scope 清理，engine.py）/ F-K-3（synthesize 测试，独立文件）

## 共享资源串行
- migration v9（F-K-1）：串行 Wave 1。
- engine.py：F-K-1 加 graph workspace 透传；F-K-2 改 scope 传播 → 同 Wave 2 串行？不，K-1 在 Wave1 改 engine（graph 透传），K-2 在 Wave2 改 engine（scope）。串行不同 Wave，不冲突。
- GraphSink + Entity domain + pipeline（F-K-1 write）+ graph_traverse（F-K-1 read）同 Wave 1 bundle（共享 entity 域）。

## NFR delta
- **兼容**：migration v9 entity.workspace_id default 'default'（既有 entity 落 default，backward compat）。
- **可测**：F-K-3 synthesize 测试 mock LLM/scheduler（确定性）。
- **架构**：F-K-2 去 setattr 私有属性耦合（显式参数更干净）。

## 下游消费
- → 03：F-K-1 需 ADR-009（entity workspace 隔离策略）；3 Spec 1:1。
- → 04：~5-6 Task；F-K-1 migration 串行 Wave 1；F-K-2/K-3 Wave 2。
