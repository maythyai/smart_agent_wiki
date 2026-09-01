---
id: SPEC-F-D-1
title: 统一 logger 收敛
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-observability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-D-1
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: []
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-D-1-1]
---

# SPEC-F-D-1: 统一 logger 收敛

## 实现 delta（源自 CMS §M07）
- `init_observability`（`middleware/observability.py:75`）为唯一 logger 初始化点。
- lint：检出散落 `logging.basicConfig`/直接 `getLogger` 未经 init 的模块 → FAIL。

## 后端逻辑
- 各模块经 `init_observability` 返回的 logger 记录；移除散落 basicConfig。

## 测试映射
| AC | 用例 |
|---|---|
| 模块经 init_observability 取 logger | `test_logger_via_init` |
| 散落 basicConfig lint FAIL（AC-OBS-1 辅） | `test_no_raw_basicconfig` |

## 实现就绪度
- [x] AC 覆盖 2/2
- [TBD] 跨模块 logger 收敛量
