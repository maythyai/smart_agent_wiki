# TMS: observability — 测试说明书

> 继承 PMS-observability。Feature：F-D-1..3。

## 需求→方法追溯矩阵
| AC | Feature | 用例 | 类型 | 断言 |
|---|---|---|---|---|
| AC-OBS-1 | F-D-1/F-D-2 | test_logger_via_init / test_no_raw_basicconfig / test_trace_id_propagated / test_trace_id_missing_degraded | 集成 | 统一 logger + trace 贯穿 |
| AC-OBS-2 | F-D-3 | test_health_ready_reflects_engine / test_json_log_default | 集成 | 健康真实 + JSON 日志 |

## 入口×状态增量矩阵
| 入口 | 正常 | engine 异常 | trace 丢失 |
|---|---|---|---|
| HTTP（/health/ready） | ✓200 | ✓非200 | — |
| 各层日志 | ✓ trace | ✓ trace | ✓ 降级标注 |

## 存量用例
- F-D-1: 2 / F-D-2: 2 / F-D-3: 2 = 6 用例

## 缺口
- [TBD] CLI/MCP 入口 trace 贯穿归 V1.1。
