# ADR-003: 可观测性复用（自建 JSON log + trace_id middleware）

## 状态：Accepted
## 上下文
SAW 已有 `middleware/observability.py`：`init_observability`（:75）、`RequestContextMiddleware`（:43）、`_RequestIdFilter`（:35）、`JsonFormatter`（:59）、`/metrics`（health.py:188）。硬化目标是"有模块→全链路闭环"，非重造。
## 决策
复用自建可观测 middleware。不引入 ELK/Prometheus/OTel 重设施。F-D-1 收敛 logger 至 `init_observability` 唯一点；F-D-2 trace_id 贯穿 engines→write_queue→sinks（context 传递）；F-D-3 `/health/ready` 反映 engine 真实状态。
## 备选方案
| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| 自建 middleware（复用） | 零依赖，local-first | 无分布式 trace | 单机/小部署 ✓ |
| OTel + Jaeger | 标准分布式 trace | 重依赖，破 local-first | 微服务 |
| Loki + Grafana | 聚合日志 | 需服务 | 多实例 |
## 理由
需求匹配（local-first + 已有 middleware）40% + 团队 20% + 生态 15% + 运维（零外部服务）15% + 成本 10%。硬化只需收敛 + trace 贯穿 + 健康真实化，无需新设施。
## 后果
- 正：trace_id 贯穿可定位问题；零外部依赖。
- 负：分布式场景需后续加 OTel（[TBD]，非本项目）。
- 风险：CLI/MCP 入口 trace 贯穿 [TBD] 归 V1.1（F-D-2 已标）。
## 关联 Feature
F-D-1（logger 收敛）、F-D-2（trace 贯穿）、F-D-3（健康+JSON 日志）、F-E-3（CI 报告）
