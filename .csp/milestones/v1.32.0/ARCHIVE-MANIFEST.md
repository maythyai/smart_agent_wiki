---
id: ARCHIVE-MANIFEST-v1.32.0
milestone: v1.32.0
release_type: MINOR (feat)
tag: v1.32.0
commit: 29173af
released: 2026-10-14
canonical_version: 1.32.0
---

# Archive Manifest — v1.32.0 (Compliance & Audit Tier)

## Release
- tag: `v1.32.0` (annotated, pushed origin)
- commit: `29173af release: v1.32.0 — Compliance & Audit Tier (feat MINOR)`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.32.0
- assets: wheel + sdist (1.32.0)

## Added (2)
- `saw_export_receipt_bundle` MCP + `GET /api/v1/claims/{id}/receipt-bundle` REST: claim metadata + Ed25519 receipts + SHA-256 bundle hash. `claims_repo.export_receipt_bundle()`.
- `saw_purge_claim` MCP + `DELETE /api/v1/claims/{id}` REST: GDPR/PIPL hard-delete + cascade (claim_relation/receipts/fts_index/claim). `claims_repo.purge_claim()`.
- MCP 工具 36→38.

## Gate
- pytest 2414 pass / 7 skip / 0 fail (+5 TestComplianceRoute: bundle 404/bundle+hash/bundle+receipts/purge 404/purge-cascade)
- coverage 68.39% (gate 67 ✓); ruff 0; tsc clean
- bump: 1.31.1 → 1.32.0 (MINOR, additive)

## Deferred → v1.32.1（附解除条件，已满足）
- 数据驻留控制（workspace→存储后端绑定 + on-prem 断言）+ 合规配置 profile（YAML per 行业）→ v1.32.1 MINOR。解除条件: v1.32.0 released ✓。

## 续留（折入后续版本）
- AUDIT-F-05/06 (saw web SPA + proxy) + AUDIT-F-08 (404→200) → v1.33.0
- AUDIT-F-01/04 (god-files + coverage 70) + stale-freshness contamination → v1.34.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- E2E-BLOCKED-01 → v1.33 saw web 挂 SPA 解除
