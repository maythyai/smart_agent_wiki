# Release v1.15.0 — agent/link 能力

**Date**: 2026-09-06
**Tag**: v1.15.0
**Type**: additive MINOR (no breaking API changes)
**Commits**: 53cd582 (F-T-1) / 8f6ad2b (F-T-2) / 59f9552 (F-T-3)

## Summary

补齐 agent 自定义 + 链接自动化 + 活动可观测，让多代理协作与知识链接更完整。

## What's New

### F-T-1: Custom Agent Role Registry (ADR-015)

Users can now register custom agent roles via YAML configuration (`agents.yaml`), merged with `build_default_agents` at runtime. This enables domain-specific agent roles beyond the 6 built-in roles (architect, researcher, coder, reviewer, summarizer, linker).

- **CLI**: `saw agents --custom` lists custom + built-in roles
- **REST**: `GET /api/v1/agents` returns merged roster
- **Config**: `agents.yaml` with `name`, `model_tier`, `tools` fields
- **Design**: YAML config + runtime merge (candidate ① over ② DB table) — no persistence layer, no migration needed

### F-T-2: Links Auto-Apply

`saw links apply <page> --suggestion` automatically inserts `[[link]]` into page content from `saw links suggest` output. Closes the L2 finding (links suggest only printed, didn't modify files).

- **`--dry-run`**: preview changes without writing
- **`--confirm`**: interactive confirmation (default on, destructive operation)
- **Safety**: never applies without user confirmation unless `--no-confirm` explicitly passed

### F-T-3: Agent Activity Aggregation

`InMemoryEventBus` subscriber now tracks `WorkflowStep` events per agent, providing activity visibility. Closes the M2 finding (agent roster was static, no recent activity).

- **REST**: `GET /api/v1/agents/{name}/activity` returns recent steps + call counts
- **CLI**: `saw agents <name> --activity` shows activity summary
- **Design**: event_bus subscriber + in-memory counter (candidate ① over ② DB aggregation) — not persisted, resets on restart

## Verification

| Gate | Result |
|---|---|
| pytest | 2220 passed, 3 skipped, 1 deselected (0 failed) |
| ruff | 0 errors |
| coverage | 67.42% (≥67 fail_under) |
| smoke | 6/6 passed |
| wheel | smart_agent_wiki-1.15.0-py3-none-any.whl (832KB) |
| sdist | smart_agent_wiki-1.15.0.tar.gz (3.1MB) |
| pyproject | version = "1.15.0" |

## Dependencies

No new dependencies. Reuses existing `yaml`, `typer`, `fastapi` packages.

## Backward Compatibility

- Fully backward compatible — built-in agent roles always available
- `links apply` is a new command (no existing behavior changed)
- Agent activity counters are additive (new endpoints, no existing endpoints modified)

## Roadmap

v1.15.0 closes deferred findings M2 (agent activity aggregation) and L2 (links auto-apply) from retrospective-v1.14.0, plus adds custom agent role registration (v1.5.0 留 v2.0 候选).
