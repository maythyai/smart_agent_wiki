# TMS: e2e-usability — 测试说明书

> 继承 PMS-e2e-usability 边界与验收形态。Feature：F-A-1..6。每条 PRD AC ≥1 用例。

## 需求→方法追溯矩阵
| AC | Feature | 用例 | 类型 | 断言 |
|---|---|---|---|---|
| AC-E2E-1 | F-A-1/F-A-6 | test_smoke_skeleton_pass / test_ci_smoke_gate | 集成 | fresh 库全 PASS 退出 0 |
| AC-E2E-2 | F-A-5 | test_smoke_offline_fallback / test_smoke_offline_nl_degraded | 集成 | LLM 不可达→fallback PASS |
| AC-TEST-2（部分） | F-A-6 | test_ci_smoke_gate | CI | CI 冒烟全过否则红 |
| (链路) | F-A-2 | test_smoke_ingest_provenance / test_smoke_compile_incremental | 集成 | claim 可溯源 + wiki 增量 |
| (链路) | F-A-3 | test_smoke_query_keyword_citation / test_smoke_query_nl_citation | 集成 | query 带 citation |
| (链路) | F-A-4 | test_smoke_govern_lint_verify / test_smoke_learn_distill | 集成 | govern/learn 不报错 |

## 入口×状态增量矩阵
| 入口 | fresh | 成功 | 失败 | 离线降级 |
|---|---|---|---|---|
| saw smoke（CLI [TBD]） | ✓ | ✓ PASS | ✓ FAIL 退出1 | ✓ fallback |
| CI smoke job | ✓ | ✓ | ✓ 红 | ✓ |

## 存量用例清单
- F-A-1: 2 / F-A-2: 2 / F-A-3: 2 / F-A-4: 2 / F-A-5: 2 / F-A-6: 1 = 11 用例

## 缺口
- 无（AC 全映射）。[TBD] 命令名定后补 fixture。
