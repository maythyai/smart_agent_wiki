---
id: SPEC-F-A-6
title: 冒烟纳入 CI
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-e2e-usability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-A-6
complexity: S
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
---

# SPEC-F-A-6: 冒烟纳入 CI

## 实现 delta
- `.github/workflows/ci.yml` 增 smoke job：调用 `saw smoke` [TBD]，退出码门禁。
- 失败附节点报告（artifact）。
- 不含 coverage 门禁（F-E-2/E-3）。

## 接口契约
- CI workflow job `smoke`；门禁：退出码非 0 → CI 红。

## 测试映射
| AC | 用例 |
|---|---|
| AC-TEST-2（CI 冒烟全过否则红） | `test_ci_smoke_gate`（workflow 断言） |
| AC-E2E-1（全过退出0） | 同上 job |

## 实现就绪度
- [x] AC 覆盖 2/2；依赖 F-A-5
