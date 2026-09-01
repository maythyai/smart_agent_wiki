---
id: SPEC-F-D-2
title: trace_id 贯穿各层
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-observability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-D-2
complexity: M
tdd_ref: .csp/tech-design/KEY-CHALLENGES.md
related_modules: []
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-D-2-1]
---

# SPEC-F-D-2: trace_id 贯穿

## 实现 delta（源自 CMS §M07 + KEY-CHALLENGES §2）
- 复用 `RequestContextMiddleware`（`observability.py:43`）+ `_RequestIdFilter`（:35）。
- trace_id 经 contextvar 从 drivers 贯穿 engines→write_queue→sinks，日志带同一 id。
- MVP 先 HTTP 入口；CLI/MCP 入口 [TBD] 归 V1.1。

## 后端逻辑
- drivers 注 trace_id 到 contextvar → engines/sinks 日志取 contextvar → 同 id。

## 异常处理
| 场景 | 处理 |
|---|---|
| trace_id 丢失 | 记录降级，标注节点 |

## 测试映射
| AC | 用例 |
|---|---|
| AC-OBS-1（一次请求各层同 trace_id） | `test_trace_id_propagated` |
| trace_id 丢失降级 | `test_trace_id_missing_degraded` |

## 实现就绪度
- [x] AC 覆盖 2/2；依赖 F-D-1
