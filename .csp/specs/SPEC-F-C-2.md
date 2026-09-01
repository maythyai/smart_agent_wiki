---
id: SPEC-F-C-2
title: Ed25519 receipt 全链路闭环
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-security-hardening.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-C-2
complexity: M
tdd_ref: .csp/tech-design/SECURITY-ARCHITECTURE.md
related_modules: [SHARED-SCHEMAS.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-C-2-1]
---

# SPEC-F-C-2: Ed25519 receipt 闭环

## 实现 delta（源自 CMS §M08/M09）
- agent 操作 + write_queue 变更挂 Ed25519 receipt：复用 `ReceiptSigner`（`adapters/crypto/ed25519.py:63`）。
- 链式 `prev_receipt_id` 校验器：遍历 receipt 链，断点 = FAIL。
- 覆盖率统计：哪些路径已挂 receipt [TBD]。

## 接口契约
- receipt 数据结构见 `SHARED-SCHEMAS.md`（op_id/prev_receipt_id/signature）。
- 校验命令：`saw security-check receipts` [TBD]。

## 后端逻辑
- agent execute → 产 receipt；Dispatcher.dispatch_pending → sinks 变更产 receipt；链式链接 prev_id。

## 测试映射
| AC | 用例 |
|---|---|
| AC-SEC-2（receipt 链不断裂） | `test_receipt_chain_intact` |
| 高危操作 100% 产 receipt | `test_receipt_coverage` |

## 实现就绪度
- [x] AC 覆盖 2/2
- [TBD] 既有 receipt 覆盖率须核验
