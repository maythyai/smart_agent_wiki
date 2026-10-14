---
id: PRD-compliance-audit-v1.32.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-14
status: approved
roadmap_ref: ROADMAP
target_version: v1.32.0
type: feature
see_also: docs/analysis/AUDIT-TO-ROADMAP.md
---

# PRD — v1.32.0 Compliance & Audit Tier (feat MINOR)

> feat MINOR（additive）。对齐 2026.05《智能体规范》可信底线 + GDPR/PIPL 被遗忘权。

## 背景
企业（医疗/金融/政务）合规准入需：① 可导出 claim 的审计链给监管（Ed25519 receipt bundle）；② 被遗忘权——删除用户数据须级联清除 claims/relations/receipts/索引。既有 `soft_delete_claim` 仅置 `deleted_at`（逻辑删），无 hard purge 级联；`saw_audit` 可验链但无 per-claim bundle 导出。

## 范围（2 feat）
1. **Audit receipt bundle 导出**: `saw_export_receipt_bundle(claim_uuid)` MCP + `GET /api/v1/claims/{claim_id}/receipt-bundle` REST——导出该 claim 的全部 receipts（含 prev 链）+ claim 元数据为 JSON bundle，bundle 本身由 ReceiptSigner 签名（监管可离线验）。
2. **删除传播（GDPR/PIPL purge）**: `saw_purge_claim(claim_uuid)` MCP + `DELETE /api/v1/claims/{claim_id}` REST——hard-delete claim + 级联 `claim_relation`（两端）+ `receipts`（claim_uuid）+ `fts_index`（doc_id=slug）。不可逆，须 confirm。

## 非目标（deferred → v1.32.1）
- **数据驻留控制**（workspace→存储后端绑定 + on-prem 断言）+ **合规配置 profile**（YAML profile per 行业）: config-heavy，拆 v1.32.1 MINOR。解除条件: v1.32.0 released。

## 成功指标
- `saw_export_receipt_bundle(uuid)` 返回 `{claim, receipts:[...], bundle_signature}`，bundle 签名可验。
- `saw_purge_claim(uuid)` 后：claim 不存在；claim_relation 无该 uuid（两端）；receipts 无该 claim_uuid；fts_index 无该 doc。
- 既有 soft_delete 不变（purge 是新能力，不替代）。

## 留尾
- 数据驻留 + compliance profile → deferred v1.32.1（附解除条件，计入入口 + Release notes）。
