---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-product-hardening-v1.md]]"
  - "[[.csp/code-spec/saw/CODE-MODULE-SPEC.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M09/M07"
created: "2026-09-01"
updated: "2026-09-01"
---

# PMS: observability（可观测性与日志一致性）

## 模块边界
- **做什么**：统一跨模块 logger 规约；trace_id（request_id）从 drivers 贯穿 engines→write_queue→sinks；结构化 JSON 日志为生产默认；健康端点反映 engines 真实状态。
- **不做什么**：不引入新可观测后端选型（HOW）；不覆盖非 HTTP 入口的日志（CLI/MCP 的 trace 贯穿 [TBD] 归 V1.1）。
- **PMS 边界=PRD §3.4**。

## 验收形态
- 一次请求各层日志同 trace_id。
- 模块经 `init_observability` 取 logger，lint 检出散落 `logging.basicConfig` 即 FAIL。
- `/health/ready` 在 engine 异常时非 200。
- 生产 JSON 日志默认，本地可读模式可切。

## 接口契约摘要
- 初始化：`middleware/observability.py:init_observability`（`:75`）。
- trace：`RequestContextMiddleware`（`:43`）+ `_RequestIdFilter`（`:35`）。
- 健康：`drivers/web/health.py` `/health`/`/health/live`/`/health/ready`/`/metrics`。

## 关联
- PRD: `docs/prd/PRD-product-hardening-v1.md` §3.4
- CMS: `CODE-MODULE-SPEC.md` drift D7（observability 已在，跨模块一致性 [TBD]）
- 下游 Spec: [待 03 回填]
