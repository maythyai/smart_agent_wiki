# TMS: security-hardening — 测试说明书

> 继承 PMS-security-hardening。Feature：F-C-1..5。

## 需求→方法追溯矩阵
| AC | Feature | 用例 | 类型 | 断言 |
|---|---|---|---|---|
| AC-SEC-1 | F-C-1 | test_no_unprotected_write_routes / test_auth_dep_attached | 集成 | 0 裸 write 路由 |
| AC-SEC-2 | F-C-2 | test_receipt_chain_intact / test_receipt_coverage | 集成 | receipt 链不断裂 |
| AC-SEC-3 | F-C-3 | test_rate_limit_429 / test_rate_limit_env_override | 集成 | 超 100/h→429+Retry-After |
| (守卫) | F-C-4 | test_url_guard_coverage / test_url_guard_block_internal | 单元 | URL 入口全覆盖+阻断内网 |
| (token) | F-C-5 | test_frontend_token_interop / test_backend_auth_unified | 集成 | 前后端 token 同源 |

## 入口×状态增量矩阵
| 入口 | 正常 | 超限 | 越权 | 裸路由 | receipt 断 |
|---|---|---|---|---|---|
| REST（/api/v1/*） | ✓ | ✓429 | ✓拒 | ✓检出 | — |
| security-check cmd | — | — | — | ✓ FAIL | ✓ FAIL |

## 存量用例
- F-C-1: 2 / F-C-2: 2 / F-C-3: 2 / F-C-4: 2 / F-C-5: 2 = 10 用例

## 缺口
- [TBD] receipt 覆盖率须核验后补用例；前端 token 互通实机核验后补。

## 05 增量用例（2026-09-01，feat/hardening-wave1-slice）
| Task | 用例 | commit |
|---|---|---|
| T-F-C-4-1 | test_internal_and_metadata_blocked / test_non_http_scheme_blocked / test_empty_and_hostless_blocked / test_public_ip_literal_passes / test_guard_referenced_at_all_external_url_entry_points (15) | fece73d |
| T-F-C-3-1 | test_env_override / test_defaults / test_limiter_allows_under_limit / test_limiter_blocks_over_limit / test_middleware_returns_429_with_retry_after / test_middleware_skips_health_paths (6) | cf5b86b |
