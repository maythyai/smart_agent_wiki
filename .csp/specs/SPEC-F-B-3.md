---
id: SPEC-F-B-3
title: 过时文档修正 + unverified 标注
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-claim-alignment.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-B-3
complexity: S
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: []
ac_coverage: 2/2
---

# SPEC-F-B-3: 过时文档修正

## 实现 delta
- 按 F-B-1 diff 报告修正 README/docs 宣称；`docs/smart_agent_wiki_deep_audit.md` 加"历史快照 2026-06-23，不作依据"标注（不删）；README_CN badge 已对齐（00 阶段）。
- 每条改动记入 `.csp/artifacts/reconcile-log.md`。

## 测试映射
| AC | 用例 |
|---|---|
| 宣称一致或加历史快照标注 | `test_doc_aligned_or_marked` |
| deep_audit 加历史标注不删 | `test_deep_audit_historical_marker` |

## 实现就绪度
- [x] AC 覆盖 2/2；依赖 F-B-1；修正范围人工确认
