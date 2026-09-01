# Coverage Report — AC 覆盖与缺口

> 每条 PRD §6 AC 映射 ≥1 用例。未映射 AC 显式标缺口，不掩盖。

## AC 覆盖
| AC | 描述 | 映射 Feature | 用例 | 状态 |
|---|---|---|---|---|
| AC-E2E-1 | 端到端冒烟 fresh 全 PASS 退出 0 | F-A-1, F-A-6 | test_smoke_skeleton_pass, test_ci_smoke_gate | covered |
| AC-E2E-2 | 离线降级 fallback PASS | F-A-5 | test_smoke_offline_fallback, test_smoke_offline_nl_degraded | covered |
| AC-ALIGN-1 | 宣称与代码 0 diff | F-B-1 | test_claim_diff_mcp, test_claim_diff_clean | covered |
| AC-ALIGN-2 | 未验证项标 [unverified] | F-B-2, F-B-3 | test_capabilities_unverified_marked, test_doc_aligned_or_marked | covered |
| AC-SEC-1 | 0 裸 write 路由 | F-C-1 | test_no_unprotected_write_routes | covered |
| AC-SEC-2 | receipt 链不断裂 | F-C-2 | test_receipt_chain_intact, test_receipt_coverage | covered |
| AC-SEC-3 | 超 100/h→429+Retry-After | F-C-3 | test_rate_limit_429 | covered |
| AC-OBS-1 | trace_id 贯穿 | F-D-1, F-D-2 | test_trace_id_propagated, test_logger_via_init | covered |
| AC-OBS-2 | /health/ready engine 异常非200 | F-D-3 | test_health_ready_reflects_engine | covered |
| AC-TEST-1 | 核心 ≥80% 否则红 | F-E-2 | test_coverage_gate_core | covered |
| AC-TEST-2 | CI 冒烟全过 | F-A-6, F-E-3 | test_ci_smoke_gate, test_ci_integrated_runs | covered |

## 汇总
- PRD AC 总数：11
- 已覆盖：11（100%）
- 缺口：0

## [TBD] 留尾（非 AC 缺口，实现期待验）
- F-C-2 receipt 覆盖率（核验后补用例）
- F-C-5 前端 token 互通（实机核验后补）
- F-E-1 覆盖率基线数值（实测后定）
- F-A-1 冒烟命令名
