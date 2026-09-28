# 复盘 — v1.31.1 contamination scan（2026-09-18）

> 07 闭环校验。feat MINOR（v1.31.0 deferred 项，解除条件已满足）。前置：06-ship done（v1.31.1 tagged @064764c, pushed, Release 含 wheel+sdist）。

## 闭环校验：✅ 通过
| 链路 | 状态 | 证据 |
|---|---|---|
| PRD→Spec | ✅ | PRD-contamination-scan-v1.31.1 Approved；SPEC-F-CONTAMINATION-SCAN 1 feat 1:1 |
| Spec→Task | ✅ | claims_repo.scan_contamination() + saw_contamination_scan MCP + GET /api/v1/contamination REST |
| AC→测试 | ✅ | TestContaminationRoute(3: empty/superseded-source/ignores-unresolved) + test_mcp_tools expected 36 |
| commit→tag | ✅ | v1.31.1 @064764c |
| 测试/lint | ✅ | pytest 2409/0 fail；ruff 0；cov 68.42%；tsc clean |
| 构建+Release | ✅ | wheel+sdist；https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.31.1 |

## 度量
- 1 feat done（contamination scan）
- pytest 2409 passed（+3）
- MCP 工具 35→36
- feat MINOR（additive）

## Findings（回流）
- stale-freshness contamination → deferred v1.34（附解除条件：freshness threshold 可配，已并入 v1.34 入口）。
- 续留：AUDIT-F-01/04/06/08 + CRITIC-F-01 + E2E-BLOCKED-01。

## 教训
- contamination scan 设计选择保守策略：SUPERSEDED 矛盾双方都视为"潜在污染源"（contradictions 表不记 winning claim），衍生 claim 命中即标 review。比"猜哪方赢"更安全——污染检测宁可过标不可漏。
- 共用 impl 放 claims_repo.scan_contamination()，MCP+REST 双暴露——避免逻辑重复（v1.31.0 provenance REST 同模式）。

## 下游衔接 → v1.32.0
- v1.32.0 (feat MINOR)：Compliance & Audit Tier（Ed25519 receipt 导出 bundle + 数据驻留 + 删除传播 + 合规 profile）。入口清单：audit-to-roadmap AUDIT-F-05/06 折入 v1.33（注意：v1.32 是 Compliance，saw-web-SPA 在 v1.33）。
