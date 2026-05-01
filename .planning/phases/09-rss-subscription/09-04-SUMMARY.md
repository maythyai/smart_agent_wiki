---
phase: 09-rss-subscription
plan: 04
subsystem: cli, scheduler
tags: [typer, cli, apscheduler, polling]
requires: [09-02, 09-03]
provides: [FeedScheduler, feed CLI commands]
affects: []
---

# Phase 09 Plan 04: CLI Commands and Scheduler Integration Summary

## One-liner
Typer CLI commands for feed management and APScheduler integration for automatic polling with staggered scheduling and exponential backoff.

## Key Decisions

1. **Typer CLI with Rich formatting** - Consistent with existing SAW CLI, uses Rich tables for list output

2. **Global scheduler instance** - Singleton pattern for web app integration, managed via `start_scheduler()` and `stop_scheduler()`

3. **Staggered polling** - Distribute feeds with same interval across time window + jitter to avoid burst requests

4. **Exponential backoff** - Failed polls double interval (max 24h), reset on success

5. **Async database integration** - CLI commands use asyncio.run() for async operations

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `src/saw/drivers/cli/commands/feed_cmd.py` | CLI commands (9 commands) | ~340 |
| `src/saw/engines/ingest/scheduler.py` | APScheduler integration | ~300 |
| `tests/unit/test_feed_cli.py` | CLI tests (17 tests) | ~150 |
| `tests/unit/test_feed_scheduler.py` | Scheduler tests (12 tests) | ~260 |

## Test Results

```
29 passed in 5.18s
```

### Coverage

- **CLI commands (17 tests)**: Command existence, flags, help text, app structure
- **Scheduler (12 tests)**: Initialization, start/stop, job management, adaptive intervals, backoff

## CLI Commands

| Command | Purpose |
|---------|---------|
| `saw feed add <url>` | Subscribe to feed |
| `saw feed list` | List all subscriptions |
| `saw feed poll <id>` | Manual poll |
| `saw feed remove <id>` | Soft delete |
| `saw feed update <id>` | Update settings |
| `saw feed entries <id>` | List entries |
| `saw feed info <id>` | Show details |
| `saw feed import <file>` | Import OPML |
| `saw feed export` | Export OPML |

## Pitfalls Addressed

| Pitfall | Prevention | Status |
|---------|------------|--------|
| 27: Aggressive polling | Staggered scheduling, adaptive intervals, backoff | Verified |

## Threat Model Coverage

| Threat | Mitigation | Status |
|--------|------------|--------|
| T-09-12: DoS (FeedScheduler) | max_instances=1, graceful shutdown | Implemented |
| T-09-13: Info Disclosure (CLI) | No secrets in output | Documented |
| T-09-14: Privilege Escalation | CLI requires shell access | Documented |

## Commits

1. `07f09e8`: feat(09-04): add CLI commands and scheduler for RSS polling

## Integration Points

- CLI registered in `src/saw/drivers/cli/main.py` as `app.add_typer(feed_app, name="feed")`
- Scheduler available via `saw.engines.ingest.scheduler.start_scheduler()`

---
*Completed: 2026-05-01*