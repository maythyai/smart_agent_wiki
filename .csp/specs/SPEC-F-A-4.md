---
id: SPEC-F-A-4
title: govern+learn 链路冒烟
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-e2e-usability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-A-4
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [SHARED-SCHEMAS.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-A-4-1]
---

# SPEC-F-A-4: govern+learn 冒烟

## 实现 delta（源自 CMS §M03/M13）
- 冒烟节点：govern lint + verify；learn distill 一次。
- 复用 `Governor.lint`（`governor.py:66`）、`verify_claim`（:70）、`engines/learn/distiller.py`。

## 后端逻辑
- lint → 健康报告非空；verify → provenance chain 非空；distill → 结果非空不报错。

## 测试映射
| AC | 用例 |
|---|---|
| govern lint+verify 产报告+provenance | `test_smoke_govern_lint_verify` |
| learn distill 不报错 | `test_smoke_learn_distill` |

## 实现就绪度
- [x] AC 覆盖 2/2
