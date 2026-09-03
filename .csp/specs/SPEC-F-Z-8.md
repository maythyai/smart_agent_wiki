---
id: SPEC-F-Z-8
title: Cedar policy reload CLI
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-Z-8
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-Z-8]
---

# SPEC-F-Z-8: policy reload CLI

## 实现 delta（ground 自源码）
- `adapters/crypto/cedar_policy.py:CedarPolicyEngine.reload()` 已实现（AC-SEC-5，重建 PolicySet / CLI 后端 inherently hot）。
- gap = 无 CLI 触发端点（operator 须编程调）。
- 新增 `drivers/cli/commands/policy_cmd.py`（`saw policy reload`），`main.py` 注册。
- 装配 CedarPolicyEngine（policy_path 来自 config，复用 `auth/permissions.py` 既有装配路径）。

## 接口契约
- `saw policy reload` → 调 `CedarPolicyEngine.reload()`，打印 backend（python/CLI）+ 结果。退出 0。
- CLI 本地无鉴权（local-first；Web admin 端点 `POST /api/admin/policy/reload` 留 [TBD] 不本轮）。

## UI/DB
- N/A。

## 后端逻辑
- load engine → reload() → 报。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-SEC-5 续（reload CLI 触发） | `tests/unit/test_policy_reload_cmd.py`：mock CedarPolicyEngine.reload → assert CLI 调用 + 退出 0 + backend 报告 |

## 实现就绪度
- [x] reload() 就绪
- [x] AC 覆盖 1/1
- Web admin 端点 defer（标 thin）
