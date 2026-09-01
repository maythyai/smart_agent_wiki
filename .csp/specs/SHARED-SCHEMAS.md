# Shared Schemas — 共享数据结构（棕地，reference CMS）

> 棕地既有 schema 不重定义。本文件只列共享实体锚点，详细 DDL 见 `adapters/storage/*_repository.py` 与 CMS §M09。

## 共享实体（源自 CMS）
| 实体 | 表/位置 | 关键字段 | 来源 |
|---|---|---|---|
| VaultDocument | vault_repository | doc_uuid, content_hash, source_path | CMS §M09 |
| Claim | claims_repository | uuid, doc_uuid, anchor, confidence, freshness, deleted_at | CMS §M09 |
| WikiPage | wiki_repository | slug, content, links | CMS §M09 |
| Receipt | adapters/crypto/ed25519.py | op_id, prev_receipt_id, signature | CMS §M08 |
| WriteOp | write_queue/queue | op_id, sink, payload, status | CMS §M09 |
| HealthReport | engines/govern | findings, score | CMS §M03 |
| AgentResult | engines/collaborate/agents/base | success, payload, confidence, metadata | CMS §M04 |

## 约定
- 软删 `deleted_at`；部分索引 `WHERE deleted_at IS NULL`（既有）。
- FTS5 全文索引（既有 `fts5_utils.py`）。
- 所有 mutation 经 Write Queue（outbox + sinks），不经 repos 直写。
- trace_id 透传（contextvar，F-D-2）。

## 共享错误格式
`{error:{code, message, details:[{field, message}]}}`（`middleware/errors.py:90`）。
