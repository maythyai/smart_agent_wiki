# 复盘 — v1.32.0 Compliance & Audit Tier（2026-10-14）

> 07 闭环校验。feat MINOR。前置：06-ship done（v1.32.0 tagged @29173af, pushed, Release 含 wheel+sdist）。

## 闭环校验：✅ 通过
| 链路 | 状态 | 证据 |
|---|---|---|
| PRD→Spec | ✅ | PRD-compliance-audit-v1.32.0 Approved；SPEC-F-COMPLIANCE-AUDIT 2 feat 1:1 |
| Spec→Task | ✅ | claims_repo.export_receipt_bundle + purge_claim + 2 MCP + 2 REST |
| AC→测试 | ✅ | TestComplianceRoute(5: bundle 404/hash/receipts + purge 404/cascade) + expected_tools 38 |
| commit→tag | ✅ | v1.32.0 @29173af |
| 测试/lint | ✅ | pytest 2414/0 fail；ruff 0；cov 68.39%；tsc clean |
| 构建+Release | ✅ | wheel+sdist；https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.32.0 |

## 度量
- 2 feat done（receipt bundle + GDPR purge）
- pytest 2414 passed（+5）
- MCP 工具 36→38
- feat MINOR（additive）

## Findings（回流）
- 数据驻留 + compliance profile → deferred v1.32.1（附解除条件：v1.32.0 released ✓，已并入 v1.32.1 入口）。
- 续留：AUDIT-F-01/04/06/08 + CRITIC-F-01 + E2E-BLOCKED-01 + stale-freshness contamination。

## 教训
- purge_claim 用单事务（with conn:）+ 顺序级联（relations→receipts→fts→claim）——外键 claim_relation 引用 claim(uuid)，先删 relation 再删 claim 避 FK 违约（SQLite FK 默认开 per PRAGMA foreign_keys=ON）。
- bundle 导出 receipts 时不含 bundle_signature 默认（需 signer），但 bundle_hash 恒算（integrity-only 兜底）——合规场景宁可无 non-repudiation 也要有完整性校验。

## 下游衔接 → v1.32.1
- v1.32.1 (feat MINOR)：数据驻留控制 + 合规配置 profile。入口清单：v1.32.0 deferred 项。
