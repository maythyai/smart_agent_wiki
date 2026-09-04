# Tasks Delta — v1.7.0（2026-09-04）

> 04 任务拆解 delta。3 Task（1:1 对应 3 Spec），2 Wave（镜像 DECOMPOSITION-DELTA-v1.7.0）。

## WBS delta（追加行）

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-K-1 | SPEC-F-K-1 | graph workspace 隔离（migration v9 + entity domain + GraphSink 写 + graph_traverse 读 + QueryEngine 透传） | backend | M | — | db/migrations.py, domain/*.py, write_queue/sinks/graph_sink.py, engines/query/graph_traverse.py, engines/query/engine.py, engines/ingest/pipeline.py, drivers/web/app.py, drivers/cli/commands/query_cmd.py | AC-WS-6 | graph-workspace |
| T-F-K-2 | SPEC-F-K-2 | scope 传播清理（tree_mode.search/compiler.compile 显式 workspace_id，去 setattr） | backend | S | T-F-K-1 | engines/query/tree_mode.py, engines/query/compiler.py, engines/query/engine.py | AC-ARCH-1 | graph-workspace |
| T-F-K-3 | SPEC-F-K-3 | synthesize 覆盖（engine+scheduler）+ fail_under 63→64 | test | M | T-F-K-1 | tests/unit/engines/synthesize/*, pyproject.toml | AC-COV-3 | test-gate |

## DAG delta
```
T-F-K-1 ──▶ T-F-K-2   (K-2 改 QueryEngine scope 传播，在 K-1 后)
T-F-K-1 ──▶ T-F-K-3   (K-3 graph 覆盖在 K-1 后)
```
- K-1 → K-2/K-3。
- K-1 读+写共享 entity 域（migration + GraphSink + graph_traverse + Entity domain + pipeline stamp）bundle。
- 无新环。

## Wave 重排（v1.7.0）
- **Wave 1**：T-F-K-1（graph 隔离——migration v9 串行 + 读写 bundle）
- **Wave 2（并行，不同文件）**：T-F-K-2（engine.py scope）/ T-F-K-3（synthesize 测试）

## 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend | T-F-K-1, T-F-K-2 | 后端 |
| test | T-F-K-3 | QA |

## 拆解门控
- [x] Spec 完整性：3 Task == 3 Spec（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（3/3）
- [x] Task 粒度 ≤4h（S/M）
- [x] DAG 无环（K-1→K-2/K-3）
- [x] Task 依赖与 decomposition 一致
- [x] Wave 划分：K-1 串行 Wave 1；K-2/K-3 Wave 2
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（graph-workspace + test-gate）
