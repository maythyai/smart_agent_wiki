---
gsd_state_version: 1.0
milestone: v3.1
milestone_name: Third-Party Integrations
status: roadmap_created
last_updated: "2026-05-01T00:00:00.000Z"
last_activity: 2026-05-01
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 17
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-02)

**Core value:** 知识可信、可溯源、可进化 — 每一条回答都可以追溯到原始文档的具体位置
**Current focus:** v3.1 Third-Party Integrations — Phase 10 planning

## Current Position

Phase: 10 — Connector Framework Foundation
Plan: —
Status: Roadmap created, ready for planning
Last activity: 2026-05-01 — Roadmap created for v3.1

Progress: [░░░░░░░░░░] 0%

## v3.1 Roadmap Summary

| Phase | Goal | Requirements | Status |
|-------|------|--------------|--------|
| 10 | Connector Framework | AUTH-01~04, IM-01,02,06 (7) | Not started |
| 11 | Sync Engine | SYNC-01~05, ERRO-01~04, IM-03~05,07 (13) | Not started |
| 12 | Notion Connector | NOTI-01~10 (10) | Not started |
| 13 | Logseq + IM | LOGS-01~10, SLAK-01~06, DISC-01~05, FEIS-01~05, WECO-01~04 (30) | Not started |
| 14 | GitHub Connector | GITH-01~11 (11) | Not started |
| 15 | Dashboard + Polish | Cross-cutting (4) | Not started |

**Coverage:** 65/65 requirements mapped (100%)

## Previous Milestone Context (v3.0)

**Completed:** 2026-05-01
**Phases:** 3 (07, 08, 09)
**Key deliverables:**
- Obsidian Plugin — 双向同步、图谱可视化
- Chrome Extension — Manifest V3、一键剪藏
- RSS Subscription — fastfeedparser、多键去重

## Accumulated Context

### Decisions (v3.1)

1. **Milestone scope:** 4 platforms (Notion, Logseq, IM, GitHub) all in v3.1
2. **Authentication:** OAuth for Notion/Slack/GitHub, API Token for Logseq
3. **Sync strategy:** SAW as knowledge hub, platforms as sources/consumers
4. **Conflict handling:** Timestamp priority + configurable strategy
5. **Phase numbering:** Continue from Phase 10 (v3.0 ended at Phase 9)
6. **Granularity:** Coarse — 6 phases, aggressive grouping

### Architecture Patterns (from research)

- UnifiedConnectorInterface (Protocol)
- ConnectorSink (Write Queue integration)
- SyncEngine (bidirectional orchestration)
- RateLimitManager (per-platform limiting)
- OAuthHandler (unified flow management)

### Tech Stack Additions (v3.1)

- notion-client 3.0.0
- slack-sdk 3.41.0 + slack-bolt 1.28.0
- discord.py 2.7.1
- lark-oapi 1.5.5
- PyGithub 2.9.1
- edn-format 0.7.5
- svix 1.92.2

### Tech Debt (from previous milestones)

1. Integration tests needed for Docker Compose deployment (v2.0)
2. OpenAPI documentation can be auto-generated (v2.0)
3. Performance benchmarks for rate limiter (v2.0)
4. Phase VERIFICATION.md files missing for some phases (v1.1)
5. React frontend tests deferred (v1.1)

### Blockers/Concerns

None — Roadmap created, ready for Phase 10 planning.

## Session Continuity

Last session: 2026-05-01T00:00:00.000Z
Next action: `/gsd-plan-phase 10` to begin Phase 10 planning

---
*Last updated: 2026-05-01 — Roadmap created*