---
id: SPEC-F-D-3
title: 健康端点真实化 + 生产 JSON 日志默认
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-observability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-D-3
complexity: S
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-D-3-1]
---

# SPEC-F-D-3: 健康真实 + JSON 日志

## 实现 delta（源自 CMS §M07）
- `/health/ready`（`drivers/web/health.py:100`）反映 engines 真实状态（非恒 200）。
- `JsonFormatter`（`observability.py:59`）生产默认；本地可切可读模式。

## 接口契约
- `GET /health/ready`：engine 异常 → 非 200 + 状态体。
- `GET /metrics`（:188）：指标。

## 测试映射
| AC | 用例 |
|---|---|
| AC-OBS-2（engine 异常→/health/ready 非200） | `test_health_ready_reflects_engine` |
| 生产 JSON 日志默认 | `test_json_log_default` |

## 实现就绪度
- [x] AC 覆盖 2/2
