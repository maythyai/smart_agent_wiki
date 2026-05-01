# Roadmap: Smart Agent Wiki

## Milestones

- **v1.1 Collaboration & Visualization** — Phases 1-3 (shipped 2026-04-29) — [Details](milestones/v1.1-ROADMAP.md)
- **v2.0 Extended Ingestion & Team Platform** — Phases 4-6 (shipped 2026-04-30) — [Details](milestones/v2.0-ROADMAP.md)
- **v3.0 Ecosystem Integration** — Phases 7-9 (planning) — Obsidian Plugin, Chrome Extension, RSS Subscription

## Phases

- [ ] **Phase 7: Obsidian Plugin** — 双向同步与图谱可视化
- [ ] **Phase 8: Chrome Extension** — 一键剪藏与智能分类
- [ ] **Phase 9: RSS Subscription** — 自动订阅与增量同步

## Phase Details

### Phase 7: Obsidian Plugin

**Goal:** 用户可在 Obsidian 中浏览、编辑 SAW 知识库，实现双向同步

**Depends on:** v2.0 API Platform (REST API)

**Requirements:** OBSP-01, OBSP-02, OBSP-03, OBSP-04, OBSP-05, OBSP-06, OBSP-07

**Success Criteria** (what must be TRUE):
1. 用户可通过 Obsidian 插件浏览 SAW 知识库内容
2. Wiki 页面在 Obsidian 中可编辑并可同步回 SAW
3. 支持 Obsidian 的双向链接 [[]] 语法
4. 插件可通过 SAW API 认证
5. 知识图谱可视化展示置信度徽章

**Plans:**
- [ ] 07-01-PLAN.md — Plugin core implementation (manifest, entry point, build config)
- [ ] 07-02-PLAN.md — API client and bidirectional sync logic
- [ ] 07-03-PLAN.md — Graph view and confidence badges
- [ ] 07-04-PLAN.md — Settings panel and commands

**UI hint:** yes

---

### Phase 8: Chrome Extension

**Goal:** 用户可一键剪藏网页内容到 SAW Vault

**Depends on:** Phase 7 (establishes TypeScript patterns), v2.0 API Platform

**Requirements:** CHRE-01, CHRE-02, CHRE-03, CHRE-04, CHRE-05, CHRE-06, CHRE-07, CHRE-08

**Success Criteria** (what must be TRUE):
1. 用户点击扩展图标可剪藏当前页面到 SAW Vault
2. 自动提取正文内容（去除导航、广告）
3. 用户可选择剪藏范围（全文/选中内容）
4. 用户可添加标签和备注
5. Manifest V3 合规，可发布到 Chrome Web Store
6. 智能分类建议基于内容分析

**Plans:** TBD

**UI hint:** yes

---

### Phase 9: RSS Subscription

**Goal:** 用户可订阅 RSS/Atom Feed 并自动摄入新内容

**Depends on:** v2.0 API Platform (ingest endpoint)

**Requirements:** RSSS-01, RSSS-02, RSSS-03, RSSS-04, RSSS-05, RSSS-06, RSSS-07

**Success Criteria** (what must be TRUE):
1. 用户可添加 RSS/Atom Feed 订阅
2. 新文章自动摄入到 Vault 层
3. 增量同步只处理新条目，不重复摄入
4. 用户可配置同步频率
5. 内容变更检测触发重新摄入
6. Feed 支持分类管理

**Plans:** TBD

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
| **7. Obsidian Plugin** | **v3.0** | **4/4** | **Planned** | **-** |
| **8. Chrome Extension** | **v3.0** | **0/0** | **Not started** | **-** |
| **9. RSS Subscription** | **v3.0** | **0/0** | **Not started** | **-** |

---

*Last updated: 2026-05-01 — Phase 7 plans created*
