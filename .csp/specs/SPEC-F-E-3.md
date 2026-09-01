---
id: SPEC-F-E-3
title: CI 集成（冒烟+coverage+报告趋势）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-test-gate.md
cms_ref: "[无]"
feature_id: F-E-3
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-E-3-1]
---

# SPEC-F-E-3: CI 集成

## 实现 delta
- `.github/workflows/ci.yml` 集成：单测 + 冒烟（F-A-6）+ coverage（F-E-2）+ 报告产物/趋势。
- 覆盖率报告入 artifact，趋势可查。

## 接口契约
- CI job：`test`（单测+coverage）+ `smoke`（F-A-6）；产物 coverage report。

## 测试映射
| AC | 用例 |
|---|---|
| AC-TEST-2（CI 单测+冒烟+coverage 全跑） | `test_ci_integrated_runs` |
| coverage 报告趋势可查 | `test_coverage_report_trend` |

## 实现就绪度
- [x] AC 覆盖 2/2；依赖 F-A-6 + F-E-2
