# Phase 19: Performance Benchmarks - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Mode:** Infrastructure phase (auto-generated context)

<domain>
## Phase Boundary

执行性能基准测试，验证 RateLimiter 和 SyncEngine 在负载下正确工作。生成基准测试报告，记录延迟分布和吞吐量。

此阶段不修改用户可见功能，只验证现有实现的性能特性。

**In scope:**
- Rate limiter 基准测试（token bucket 行为、throttling 正确性）
- Sync engine 基准测试（大规模同步、内存稳定性）
- Backpressure manager 基准测试（队列阈值处理）
- 基准测试报告（p50/p90/p99 延迟、吞吐量）

**Out of scope:**
- 新功能实现
- UI 变更
- API 变更

</domain>

<decisions>
## Implementation Decisions

### Benchmark Framework
- **D-01:** 使用 pytest-benchmark 作为基准测试框架
- **D-02:** 基准测试结果输出到 `.planning/benchmarks/` 目录
- **D-03:** 使用 matplotlib 生成延迟分布图

### Rate Limiter Benchmarks
- **D-04:** 测试 10x 负载下的 throttling 正确性
- **D-05:** 验证 token bucket refill 时间精确度
- **D-06:** 测试并发请求下的公平性

### Sync Engine Benchmarks
- **D-07:** 测试 1000+ items 同步的内存使用
- **D-08:** 测试批量处理吞吐量（items/second）
- **D-09:** 测试长时间运行的内存稳定性

### Backpressure Benchmarks
- **D-10:** 测试队列满时的 throttling 行为
- **D-11:** 验证 resume 恢复逻辑

### Claude's Discretion
- 基准测试具体参数（并发数、持续时间）
- 报告格式细节
- 是否添加内存分析工具（memory_profiler）

</decisions>

<code_context>
## Existing Code Insights

### Target Components (from Phase 11)
- **src/saw/connectors/rate_limiter.py** — TokenBucketRateLimiter
- **src/saw/connectors/sync_engine.py** — SyncEngine, SyncOrchestrator
- **src/saw/connectors/backpressure.py** — BackpressureManager
- **src/saw/connectors/sync_status.py** — SyncStatusTracker

### Test Infrastructure
- **tests/** — pytest 配置已存在
- **tests/conftest.py** — 共享 fixtures

</code_context>

<specifics>
## Specific Ideas

### Benchmark Directory Structure

```
.planning/benchmarks/
├── rate_limiter/
│   ├── throughput.json
│   ├── latency_distribution.json
│   └── latency_distribution.png
├── sync_engine/
│   ├── memory_profile.json
│   ├── throughput.json
│   └── throughput.png
└── backpressure/
    ├── queue_throttling.json
    └── resume_logic.json
```

### Benchmark Report Format

```json
{
  "benchmark": "rate_limiter_throughput",
  "date": "2026-05-03",
  "config": {"rate": 10, "burst": 20},
  "results": {
    "requests_total": 1000,
    "requests_allowed": 500,
    "requests_throttled": 500,
    "p50_latency_ms": 0.5,
    "p90_latency_ms": 1.2,
    "p99_latency_ms": 5.0
  }
}
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 19 requirements are in scope.

</deferred>

---

*Phase: 19-performance-benchmarks*
*Context gathered: 2026-05-03 via auto-generation (infrastructure phase)*