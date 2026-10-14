---
id: SPEC-F-COMPLIANCE-AUDIT
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-14
status: approved
prd_ref: PRD-compliance-audit-v1.32.0
target_version: v1.32.0
---

# SPEC — v1.32.0 Compliance & Audit Tier（详细）

## F-CA-1: Audit receipt bundle 导出

### 共用 impl: `claims_repository.export_receipt_bundle(claim_uuid) -> dict | None`
- 查 claim（get_by_id，含元数据 uuid/content/source_uuid/confidence/created_at）。
- 查 receipts: `SELECT * FROM receipts WHERE claim_uuid=? ORDER BY timestamp`。
- 跟 prev_receipt_id 链（从最新回溯，cap 50）。
- bundle = `{claim: {...metadata}, receipts: [{receipt_id, operation_id, operation_type, agent, timestamp, signature, prev_receipt_id, public_key}, ...], receipt_count, exported_at}`。
- bundle 签名: 用 ReceiptSigner 对 `json.dumps(bundle, sort_keys=True)` 的 sha256 签名 → `bundle_signature` + `bundle_public_key`。若 ReceiptSigner 不可用（无 key），bundle 仍导出但 `bundle_signature=None`（best-effort）。
- 返回 bundle dict；claim 不存在 → None。

### MCP: `saw_export_receipt_bundle(claim_uuid)` (govern.py)
- 调 `claims_repo.export_receipt_bundle(claim_uuid)`。
- 返回 bundle 或 `{error: claim_not_found}`。

### REST: `GET /api/v1/claims/{claim_id}/receipt-bundle` (govern.py)
- 调同 impl。404 if claim 不存在。

## F-CA-2: 删除传播（purge）

### 共用 impl: `claims_repository.purge_claim(claim_uuid) -> dict`
- 验证 claim 存在（get_by_id）。
- 级联 hard-delete（顺序）：
  1. `DELETE FROM claim_relation WHERE source_claim_uuid=? OR target_claim_uuid=?`
  2. `DELETE FROM receipts WHERE claim_uuid=?`
  3. `DELETE FROM fts_index WHERE title=?`（doc_id=claim_uuid，FTS5 title 列存 slug/uuid）
  4. `DELETE FROM claim WHERE uuid=?`
- 返回 `{purged: True, claim_uuid, cascade: {relations, receipts, fts, claim}}` 各删除计数。
- 单事务（with conn:）。

### MCP: `saw_purge_claim(claim_uuid)` (govern.py)
- 调 `claims_repo.purge_claim(claim_uuid)`。不可逆，docstring 标注。

### REST: `DELETE /api/v1/claims/{claim_id}` (govern.py)
- 调同 impl。404 if 不存在。

## AC
- bundle: claim 有 receipts → bundle.receipts 非空 + bundle_signature 可验；无 receipts → bundle.receipts=[] + signature 仍签 bundle。
- purge: 插 claim + relation + receipt + fts entry → purge → 各表无该 uuid/claim_uuid；count 正确。
- 404: bundle/purge on 不存在 → 404。

## 测试
- `tests/unit/engines/govern/test_compliance.py` 或扩 test_h1_routes：bundle + purge + 404。
- 全量回归 + ruff 0 + coverage 不回归。
