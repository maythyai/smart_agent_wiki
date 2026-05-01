# Roadmap: Smart Agent Wiki

## Milestones

- ✅ **v1.1 Collaboration & Visualization** — Phases 1-3 (shipped 2026-04-29) — [Details](milestones/v1.1-ROADMAP.md)
- ✅ **v2.0 Extended Ingestion & Team Platform** — Phases 4-6 (shipped 2026-04-30) — [Details](milestones/v2.0-ROADMAP.md)
- ✅ **v3.0 Ecosystem Integration** — Phases 7-9 (shipped 2026-05-01) — [Details](milestones/v3.0-MILESTONE-AUDIT.md)

## Phases

- [x] **Phase 7: Obsidian Plugin** — 双向同步与图谱可视化 — COMPLETE
- [x] **Phase 8: Chrome Extension** — 一键剪藏与智能分类 — COMPLETE
- [x] **Phase 9: RSS Subscription** — 自动订阅与增量同步 — COMPLETE

## Phase Details

### Phase 7: Obsidian Plugin — ✅ COMPLETE

**Goal:** 用户可在 Obsidian 中浏览、编辑 SAW 知识库，实现双向同步

**Depends on:** v2.0 API Platform (REST API)

**Requirements:** OBSP-01~07 — All implemented

**Success Criteria:** All 5 criteria met

**Plans:**
- [x] 07-01-PLAN.md — Plugin core implementation
- [x] 07-02-PLAN.md — API client and bidirectional sync logic
- [x] 07-03-PLAN.md — Graph view and confidence badges
- [x] 07-04-PLAN.md — Settings panel and commands

**Delivered:** `plugins/obsidian-smart-agent-wiki/` (24 files, ~2,300 lines)

**UI hint:** yes

---

### Phase 8: Chrome Extension — ✅ COMPLETE

**Goal:** 用户可一键剪藏网页内容到 SAW Vault

**Depends on:** Phase 7, v2.0 API Platform

**Requirements:** CHRE-01~08 — All implemented

**Success Criteria:** All 6 criteria met

**Plans:**
- [x] 08-01-PLAN.md — Extension core (Manifest V3)
- [x] 08-02-PLAN.md — Content extraction (Readability.js)
- [x] 08-03-PLAN.md — Popup UI
- [x] 08-04-PLAN.md — API client and batch operations

**Delivered:** `plugins/chrome-clipper/` (26 files, ~2,750 lines)

**UI hint:** yes

---

### Phase 9: RSS Subscription — ✅ COMPLETE

**Goal:** 用户可订阅 RSS/Atom Feed 并自动摄入新内容

**Depends on:** v2.0 API Platform (ingest endpoint)

**Requirements:** RSSS-01~07 — All implemented

**Success Criteria:** All 6 criteria met

**Plans:**
- [x] 09-01-PLAN.md — Data models and database schema
- [x] 09-02-PLAN.md — FeedManager implementation
- [x] 09-03-PLAN.md — API endpoints
- [x] 09-04-PLAN.md — CLI commands and scheduler

**Delivered:** 7 Python files, ~1,966 lines, 106 tests passing

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Data Cycle | v1.1 | 3/3 | Complete | 2026-04-26 |
| 2. Intelligence & Governance | v1.1 | 3/3 | Complete | 2026-04-27 |
| 3-01. Multi-Agent Foundation | v1.1 | 2/2 | Complete | 2026-04-28 |
| 3-02. Web API Foundation | v1.1 | 3/3 | Complete | 2026-04-29 |
| 3-03. React Frontend | v1.1 | 8/8 | Complete | 2026-04-29 |
| 4. Media Ingestion | v2.0 | 3/3 | Complete | 2026-04-30 |
| 5. Team Deployment | v2.0 | 4/4 | Complete | 2026-04-30 |
| 6. API Platform | v2.0 | 3/3 | Complete | 2026-04-30 |
| 7. Obsidian Plugin | v3.0 | 4/4 | Complete | 2026-05-01 |
| 8. Chrome Extension | v3.0 | 4/4 | Complete | 2026-05-01 |
| 9. RSS Subscription | v3.0 | 4/4 | Complete | 2026-05-01 |

---

*Last updated: 2026-05-01 — v3.0 Ecosystem Integration shipped!*