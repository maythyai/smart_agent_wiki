---
id: ARCHIVE-MANIFEST-v1.31.1
milestone: v1.31.1
release_type: MINOR (feat)
tag: v1.31.1
commit: 064764c
released: 2026-09-18
canonical_version: 1.31.1
---

# Archive Manifest — v1.31.1 (contamination scan)

## Release
- tag: `v1.31.1` (annotated, pushed origin)
- commit: `064764c release: v1.31.1 — contamination scan (feat MINOR)`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.31.1
- assets: wheel + sdist (1.31.1)

## Added (1)
- `saw_contamination_scan` MCP + `GET /api/v1/contamination` REST: scan claims derived from resolved SUPERSEDED contradiction sources. `claims_repo.scan_contamination()` shared impl.
- MCP 工具 35→36（expected_tools synced）.

## Gate
- pytest 2409 pass / 7 skip / 0 fail (+3 TestContaminationRoute: empty / superseded-source / ignores-unresolved)
- coverage 68.42% (gate 67 ✓); ruff 0; tsc clean
- bump: 1.31.0 → 1.31.1 (MINOR, additive)

## Deferred → v1.34（附解除条件）
- stale-freshness contamination（源 freshness 过期）: 需 FreshnessTracker 集成 + threshold 配置 → v1.34 perf 硬化。解除条件: v1.34 freshness threshold 可配。

## 续留（折入后续版本）
- AUDIT-F-01/04 (god-files + coverage 70) + stale-freshness contamination → v1.34.0
- AUDIT-F-05/06 (saw web SPA + proxy) + AUDIT-F-08 (404→200) → v1.33.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- E2E-BLOCKED-01 → v1.33 saw web 挂 SPA 解除
