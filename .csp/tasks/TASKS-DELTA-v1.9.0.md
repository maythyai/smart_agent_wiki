# Tasks Delta — v1.9.0（2026-09-04）

> 04 任务拆解 delta。3 Task（1:1 对应 3 Spec），1 Wave。

## WBS delta（追加行）

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-M-1 | SPEC-F-M-1 | saw workflow list（durable 历史，workflow_executions v4） | backend-cli | S | — | commands/workflow_cmd.py, main.py | AC-WF-3 | agent-viz |
| T-F-M-2 | SPEC-F-M-2 | saw agents（6-role roster CLI） | backend-cli | S | — | commands/agents_cmd.py, main.py | AC-AG-2 | agent-viz |
| T-F-M-3 | SPEC-F-M-3 | GET /api/v1/agents（roster REST） | backend | S | — | api/routes/collaborate.py | AC-API-1 | agent-viz |

## DAG delta
- T-F-M-1 / T-F-M-2 / T-F-M-3 互相独立（不同文件）。
- 无新环；无依赖。

## Wave 重排（v1.9.0）
- **Wave 1（全并行）**：T-F-M-1（workflow_cmd 加 list）/ T-F-M-2（agents_cmd）/ T-F-M-3（collaborate router 加 /agents）

## 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-cli | T-F-M-1, T-F-M-2 | 后端 |
| backend | T-F-M-3 | 后端 |

## 拆解门控
- [x] Spec 完整性：3 Task == 3 Spec（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（3/3）
- [x] Task 粒度 ≤4h（S）
- [x] DAG 无环（独立）
- [x] Task 依赖与 decomposition 一致
- [x] Wave 划分：1 Wave 全并行
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（agent-viz）
