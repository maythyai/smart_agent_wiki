---
phase: 11-sync-engine
plan: 02
subsystem: sync
tags: [backpressure, retry, health-monitoring, alerting]
dependency:
  requires: [11-01]
  provides: [BackpressureManager, RetryHandler, HealthMonitor]
  affects: []
tech-stack:
  added: []
  patterns: [Hysteresis, Exponential Backoff, Three-tier Health]
key-files:
  created:
    - src/saw/connectors/backpressure.py
    - src/saw/connectors/retry_handler.py
    - src/saw/connectors/health_monitor.py
    - src/saw/api/health.py
    - tests/unit/test_backpressure.py
    - tests/unit/test_retry_handler.py
    - tests/unit/test_health_monitor.py
  modified:
    - src/saw/api/__init__.py
decisions:
  - Hysteresis-based backpressure (pause at 1000, resume at 500)
  - Exponential backoff 1s→2s→4s→8s→16s (max 5 retries)
  - Three-tier health: HEALTHY, DEGRADED, UNHEALTHY
  - Degraded after 2 failures, unhealthy after 5, recover after 3 successes
  - connector_unhealthy event for external alerting
metrics:
  duration-min: 15
  completed: 2026-05-02
  tests-passed: 45
---

# Phase 11 Plan 02: Backpressure, Retry, and Health Status Summary

Implemented backpressure management, retry handling with exponential backoff, and three-tier health monitoring with alerting.

## Key Deliverables

- **BackpressureManager**: Hysteresis-based throttling for Write Queue (SYNC-05)
- **BackpressureConfig**: Configurable thresholds (pause at 1000, resume at 500)
- **BackpressureState**: ACTIVE, PAUSED, THROTTLED states
- **RetryHandler**: Exponential backoff for transient failures (ERRO-01)
- **TransientError/PermanentError**: Exception types for retry categorization
- **HealthMonitor**: Per-connector health status tracking (ERRO-02, ERRO-03)
- **HealthStatus**: Three-tier (HEALTHY, DEGRADED, UNHEALTHY)
- **Health API**: REST endpoints for health status visibility

## Requirements Addressed

- **SYNC-01**: Foundation for unified sync status dashboard
- **SYNC-05**: Backpressure handling via Write Queue
- **ERRO-01**: Exponential backoff (1s→2s→4s→8s→16s, max 5 retries)
- **ERRO-02**: Persistent failures trigger alerts
- **ERRO-03**: Per-connector health status visible
- **IM-07**: Graceful degradation when platforms unavailable

## Deviations from Plan

None - plan executed exactly as written.

## Architecture Notes

### Backpressure Hysteresis
Prevents oscillation between pause/resume states:
- Pause triggered when depth >= 1000
- Resume only when depth < 500
- Admin override via force_resume()

### Retry Backoff
Delay sequence: 1s, 2s, 4s, 8s, 16s (capped at max)
- Jitter added (±25%) to prevent thundering herd
- Retry-After header honored when provided
- Transient errors: 429, 500, 502, 503, 504, timeouts
- Permanent errors: 401, 403, 404, 400

### Health Thresholds
Default configuration:
- Degraded after 2 consecutive failures
- Unhealthy after 5 consecutive failures
- Healthy after 3 consecutive successes

## Test Results

```
45 passed in 13.35s
```

All tests pass covering backpressure, retry handler, and health monitor.

## Self-Check: PASSED

- [x] All 6 test files exist and pass
- [x] Health API router registered in api/__init__.py
- [x] RetryHandler integrates with SyncEngine pattern
- [x] 3 commits created (Task 1, Task 2, Task 3)