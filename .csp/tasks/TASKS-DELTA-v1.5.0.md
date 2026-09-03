# Tasks Delta — v1.5.0（2026-09-03）

> 04 任务拆解 delta。8 Task（1:1 对应 8 Spec），3 Wave（镜像 DECOMPOSITION-DELTA-v1.5.0）。

## WBS delta（追加行）

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-I-1 | SPEC-F-I-1 | workflow CLI(run/validate/resume/status/lint)+resume()续跑 | backend-cli | M | T-F-I-4 | commands/workflow_cmd.py, engines/collaborate/workflow_executor.py, main.py | AC-WF-1, AC-WF-2 | intelligence-adaptation |
| T-F-I-2 | SPEC-F-I-2 | Learn CLI(distill 在线+gaps) | backend-cli | S | — | commands/learn_cmd.py, main.py | AC-LR-1, AC-LR-2 | intelligence-adaptation |
| T-F-I-3 | SPEC-F-I-3 | Token bench CLI(实测节省%) | backend-cli | S | — | commands/token_cmd.py, main.py | AC-TK-1 | intelligence-adaptation |
| T-F-I-4 | SPEC-F-I-4 | agent 角色一致性 lint(saw workflow lint) | backend-cli | S | — | commands/workflow_cmd.py | AC-AG-1 | intelligence-adaptation |
| T-F-Z-6 | SPEC-F-Z-6 | ruff F841 27 死赋值手修+移除 ignore 启用 | tech-debt | M | T-F-I-1,T-F-Z-7 | pyproject.toml, src/saw/** | AC-LINT-2(续) | test-gate |
| T-F-Z-7 | SPEC-F-Z-7 | workspace 全查询路径路由(repo 层注入 scope) | backend | L | — | engines/query/engine.py, engines/ingest/pipeline.py, adapters/storage/*, domain/protocols.py | AC-WS-3 | intelligence-adaptation |
| T-F-Z-8 | SPEC-F-Z-8 | Cedar policy reload CLI(saw policy reload) | backend-cli | S | — | commands/policy_cmd.py, main.py | AC-SEC-5(续) | security-hardening |
| T-F-Z-9 | SPEC-F-Z-9 | query 子模块测试+fail_under 60→65 | test | M | — | tests/unit/engines/query/*, pyproject.toml | AC-COV-1 | test-gate |

## DAG delta
```
T-F-I-4 ──▶ T-F-I-1 ────────────────────────┐
                                            ├──▶ T-F-Z-6 (serial 末位)
T-F-Z-7 ────────────────────────────────────┘
T-F-I-2  T-F-I-3  T-F-Z-8  T-F-Z-9   (独立，Wave1 并行)
```
- I-4 → I-1（lint 是 run 前校验；同文件 bundle 提交）。
- Z-6 串行末位（全 src 改动后），deps I-1 + Z-7。
- Z-7 串行 Wave 2（多 repo 改动）。
- 无新环。

## Wave 重排（v1.5.0）
- **Wave 1（并行，不同文件）**：T-F-I-4 + T-F-I-1（同 workflow_cmd.py，bundle）/ T-F-I-2（learn_cmd.py）/ T-F-I-3（token_cmd.py）/ T-F-Z-8（policy_cmd.py）/ T-F-Z-9（tests/query）
- **Wave 2（串行）**：T-F-Z-7（workspace scope 注入——QueryEngine + repos）
- **Wave 3（串行末位）**：T-F-Z-6（F841 全库修 + 启用）

## 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-cli | T-F-I-1/2/3/4, T-F-Z-8 | 后端 |
| backend | T-F-Z-7 | 后端（核心引擎） |
| tech-debt | T-F-Z-6 | 后端（lint 治理） |
| test | T-F-Z-9 | QA |

## 拆解门控
- [x] Spec 完整性：8 Task == 8 Spec（03 穷尽门控通过）
- [x] 每个 Feature 有 ≥1 Task（8/8）
- [x] Task 粒度 ≤4h（S/M/L，Z-7=L 因多 repo）
- [x] DAG 无环
- [x] Task 依赖与 decomposition Feature 依赖一致（I-4→I-1；Z-6 末位）
- [x] Wave 划分：共享 workflow_executor.py bundle；Z-7/Z-6 串行
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（intelligence-adaptation + test-gate + security-hardening）
