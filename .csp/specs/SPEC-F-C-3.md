---
id: SPEC-F-C-3
title: 限流双轨生效（429+Retry-After）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-security-hardening.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-C-3
complexity: S
tdd_ref: .csp/tech-design/SECURITY-ARCHITECTURE.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-C-3-1]
---

# SPEC-F-C-3: 限流双轨

## 实现 delta（源自 CMS §M08）
- 复用 `RateLimitConfig`（`api/rate_limit.py:24`，100/h、1000/d，env 覆盖）。
- 验证双轨：API key + 匿名；超限 → 429 + `Retry-After` header。

## 接口契约
- 超限响应：`429 Too Many Requests` + `Retry-After: <seconds>`。

## 测试映射
| AC | 用例 |
|---|---|
| AC-SEC-3（超 100/h→429+Retry-After） | `test_rate_limit_429` |
| env 覆盖阈值生效 | `test_rate_limit_env_override` |

## 实现就绪度
- [x] AC 覆盖 2/2
