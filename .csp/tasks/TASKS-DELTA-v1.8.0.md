# Tasks Delta — v1.8.0（2026-09-04）

> 04 任务拆解 delta。3 Task（1:1 对应 3 Spec），1 Wave（镜像 DECOMPOSITION-DELTA-v1.8.0）。

## WBS delta（追加行）

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-L-1 | SPEC-F-L-1 | 智能链接建议（saw links suggest）+ 链接审计（saw links audit）bundle | backend-cli | M | — | commands/links_cmd.py, main.py | AC-LINK-1, AC-LINK-2 | smart-linking |
| T-F-L-2 | SPEC-F-L-2 | （并入 T-F-L-1 同 links_cmd.py） | — | — | — | — | — | — |
| T-F-L-3 | SPEC-F-L-3 | AI 摘要（saw summarize） | backend-cli | S | — | commands/summarize_cmd.py, main.py | AC-SUM-1 | smart-linking |

> 注：F-L-1/F-L-2 共享 links_cmd.py（suggest+audit 同文件）→ bundle 为单 Task T-F-L-1（覆盖两 AC）。F-L-3 独立 T-F-L-3。故实际 2 Task（T-F-L-1 bundle + T-F-L-3），覆盖 3 Feature/3 AC。

## DAG delta
- T-F-L-1 与 T-F-L-3 独立（不同文件：links_cmd vs summarize_cmd）。
- 无新环；无依赖。

## Wave 重排（v1.8.0）
- **Wave 1（并行）**：T-F-L-1（links_cmd: suggest+audit）/ T-F-L-3（summarize_cmd）

## 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-cli | T-F-L-1, T-F-L-3 | 后端 |

## 拆解门控
- [x] Spec 完整性：Task 覆盖 3 Spec（T-F-L-1 覆盖 L-1/L-2 bundle + T-F-L-3 = 3 Spec）（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（3/3）
- [x] Task 粒度 ≤4h（S/M）
- [x] DAG 无环
- [x] Task 依赖与 decomposition 一致（独立）
- [x] Wave 划分：1 Wave 全并行
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（smart-linking）
