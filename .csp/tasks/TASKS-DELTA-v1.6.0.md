# Tasks Delta — v1.6.0（2026-09-03）

> 04 任务拆解 delta。4 Task（1:1 对应 4 Spec），2 Wave（镜像 DECOMPOSITION-DELTA-v1.6.0）。

## WBS delta（追加行）

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-J-1 | SPEC-F-J-1 | tree_mode+compiler 注入 workspace scope（QueryEngine 透传） | backend | M | — | engines/query/tree_mode.py, engines/query/compiler.py, engines/query/engine.py, drivers/web/app.py, drivers/cli/commands/query_cmd.py | AC-WS-4 | debt-closure |
| T-F-J-2 | SPEC-F-J-2 | insert 持久化 workspace_id + ingest 透传 | backend | M | — | adapters/storage/claims_repository.py, engines/ingest/pipeline.py | AC-WS-5 | debt-closure |
| T-F-J-3 | SPEC-F-J-3 | query 深覆盖（engine/compare/tree_mode）+ fail_under 63→65 | test | M | T-F-J-1 | tests/unit/engines/query/*, pyproject.toml | AC-COV-2 | test-gate |
| T-F-J-4 | SPEC-F-J-4 | policy reload Web admin 端点（admin-only） | backend | S | — | drivers/web/routes/ 或 api/routes/, drivers/web/app.py | AC-SEC-6 | security-hardening |

## DAG delta
```
T-F-J-1 ──▶ T-F-J-3   (J-3 tree_mode 测试覆盖 J-1 新代码)
T-F-J-2              (独立：claims_repo.insert + pipeline；与 J-1 文件不重叠)
T-F-J-4              (独立：web route)
```
- J-1 → J-3（J-3 在 J-1 代码落定后写 tree_mode 测试）。
- J-1/J-2 文件不冲突（J-1: tree_mode/compiler/engine/app/query_cmd；J-2: claims_repository/pipeline）。
- 无新环。

## Wave 重排（v1.6.0）
- **Wave 1（并行，不同文件）**：T-F-J-1（query 子系统）/ T-F-J-2（claims_repo+ingest）/ T-F-J-4（web route）
- **Wave 2**：T-F-J-3（query 深覆盖测试 + fail_under 上调）

## 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend | T-F-J-1, T-F-J-2, T-F-J-4 | 后端 |
| test | T-F-J-3 | QA |

## 拆解门控
- [x] Spec 完整性：4 Task == 4 Spec（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（4/4）
- [x] Task 粒度 ≤4h（S/M）
- [x] DAG 无环（J-1→J-3）
- [x] Task 依赖与 decomposition 一致
- [x] Wave 划分：J-3 串行 Wave 2
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（debt-closure + test-gate + security-hardening）
