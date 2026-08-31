# F-INGEST-09 — Ingest 流水线统一规划

> 状态：规划已定，部分安全动作已执行（见 §6）
> 日期：2026-08-31
> 关联审计：`docs/audit/09-db-storage-writequeue.md` 之外的全局 §4-3（两套并行实现）；`99-summary.md` Batch 34 推迟项

---

## 1. 现状（两套实现）

| | Pipeline A（生产） | Pipeline B（DAG 框架） |
|---|---|---|
| 位置 | `src/saw/engines/ingest/pipeline.py` | `src/saw/ingest/pipeline/`（runner/validator/types/phases）+ `src/saw/ingest/pipeline_v2.py` |
| 类 | `IngestPipeline`（同步） | `PipelineRunner` + `PipelinePhase` + `validate_dag`（Kahn 拓扑排序 + 循环检测） |
| 阶段 | classify→extract→fuse→validate→enqueue（经 WriteQueue sinks） | classify→parse→extract→merge→validate→store（phases，部分 placeholder） |
| 完整度 | 完整、可用 | 框架完整（runner/validator 经测试）；**ingest 专用 phases 不完整**（`store.py` 标注 "Store to claims DB (placeholder)" / "Create wiki pages (placeholder)"） |
| 生产接线 | web/MCP/CLI 全部使用 | **未接入生产摄入**；`pipeline_v2.py` 为死代码（无任何 import） |
| 测试 | `test_pipeline_existing_claims` / `test_ingest_flow` 等（真实摄入） | `test_pipeline_dag.py`（仅隔离测 DAG 框架） |

**结论**：生产摄入实际只有一套（A）。B 是一个**未完成的 DAG 框架实验** + 一个**死代码入口**（pipeline_v2.py）。审计的"两套并行实现"在用户层面不成立（B 不接生产），但在代码层面是真实的重复/混淆来源。

## 2. 项目目标

- 单一、连贯、可维护的摄入管线，避免"两套实现"的混淆与维护负担。
- 保留已经过测试、全链路接线的生产能力（A），不引入回归。
- 让 B 中真正有独立价值的部分（通用 DAG runner：拓扑排序、循环检测、类型安全的阶段结果）有明确归属，而非作为"半成品摄入管线"闲置。

## 3. 风险评估（为何不直接重构合并）

- **A 是关键路径**：web/MCP/CLI 三处调用，覆盖 FTS5/claims/vault/wiki/graph 多 sink，测试完备。把 A 迁到 B 的 phase 模型需：补全 B 的 store/extract placeholder、用 phase 风格重写 fuser/validator/extractor 集成、改写三处调用方、重写 WriteQueue 接线。**高风险、大工作量、零用户面收益**（A 已工作）。
- **B 的 phases 是半成品**：store.py 等为 placeholder，直接切换会丢失写入能力。
- **B 框架的独立价值**：`PipelineRunner`/`validate_dag` 是与"摄入"无关的通用 DAG 执行器，有隔离测试，可作为可复用工具保留。

因此：**不进行 A→B 的重写合并**。改用"定角色 + 去死代码 + 文档化"的方式消除混淆。

## 4. 推荐方案（实用优先）

1. **A 仍为唯一摄入管线**（`engines/ingest/pipeline.py` = `IngestPipeline`）。生产摄入、测试、接线不变。
2. **B 的 DAG 框架重新定位为"通用 pipeline runner 工具"**（`saw.ingest.pipeline` 包），而非"第二套摄入管线"。其 `PipelineRunner`/`validate_dag`/`PipelinePhase` 作为可复用 DAG 执行器保留，供未来需要拓扑编排的特性（如多阶段编译、批量治理流）使用。
3. **B 的 ingest 专用 phases**（`phases/store.py` 等 placeholder）明确标注为"框架示例/未接生产摄入"，不作为摄入路径。
4. **删除死代码 `pipeline_v2.py`**（无任何 import），消除误导性的"v2 入口"。
5. **文档化决策**（本文件 + 模块 docstring），使重复成为**有意的设计**而非遗留气味。

## 5. 分阶段计划

| 阶段 | 动作 | 风险 | 验收 |
|------|------|------|------|
| P0（本次） | 删 `pipeline_v2.py`；`ingest/pipeline/__init__.py` 加定位 docstring；落地本文档 | 极低 | 全测试 0 回归；无 import 指向 v2 |
| P1（后续，可选） | 给 `phases/store.py` 等 placeholder 加 `# NOT WIRED — framework example` 标注，或移至 `examples/` | 低 | 隔离测试仍过；无生产路径引用 |
| P2（后续，可选） | 若未来确需 DAG 编排某特性，基于 B 框架实现，与 A 并存但职责清晰（A=摄入，B=通用编排） | 中 | 新特性测试；A 不受影响 |
| 不做 | 把生产摄入迁到 B 的 phase 模型 | 高 | — |

## 6. 已执行（P0）

- 删除 `src/saw/ingest/pipeline_v2.py`（死代码，无 import）。
- `src/saw/ingest/pipeline/__init__.py` 增加定位说明：本包是**通用 DAG pipeline runner 工具**，不是生产摄入管线；生产摄入见 `saw.engines.ingest.pipeline.IngestPipeline`。
- 本文档落地。

## 7. 决策记录

- **保留** `engines/ingest/pipeline.IngestPipeline` 为唯一生产摄入管线。
- **保留** `ingest/pipeline/` 作为通用 DAG runner 工具（有独立测试价值）。
- **删除** `pipeline_v2.py`（死代码）。
- **不**进行高风险重写合并。重复通过"明确职责 + 去死代码 + 文档"消除，而非"合并成一套"。
