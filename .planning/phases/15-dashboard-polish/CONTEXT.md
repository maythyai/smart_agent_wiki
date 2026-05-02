# Context: Phase 15 - Integration Dashboard + Polish

**Phase:** 15
**Goal:** Users have unified visibility into all connector health and can manage integrations
**Milestone:** v3.1 Third-Party Integrations

---

## Requirements

This phase covers cross-cutting integration, dashboard, documentation, and final polish. No specific requirement IDs from REQUIREMENTS.md - these are integration and UX requirements.

**Dashboard Requirements:**
1. User can view unified dashboard showing all connected platforms
2. Dashboard displays per-connector sync status, last sync time, and health
3. User can disconnect platforms from dashboard
4. User can re-authorize expired OAuth connections
5. System provides clear error messages when sync fails

**Documentation Requirements:**
6. All connector documentation is complete
7. API documentation updated for v3.1 endpoints
8. User guide for platform integration

**Polish Requirements:**
9. All v3.1 features integrated and tested together
10. Performance validated under realistic load
11. Error handling consistent across all connectors

## Success Criteria

1. User can view unified dashboard showing all connected platforms
2. Dashboard displays per-connector sync status, last sync time, and health
3. User can disconnect platforms from dashboard
4. User can re-authorize expired OAuth connections
5. System provides clear error messages when sync fails
6. All connector documentation is complete

## Technical Context

### Existing Architecture (Phase 10-14)

**Implemented Connectors:**
- **Notion:** OAuth, database sync, bidirectional
- **Logseq:** Local file sync, file watching, bidirectional
- **Slack:** Events API, message ingestion
- **Discord:** Gateway WebSocket, message ingestion
- **Feishu:** Webhooks, multi-tenant tokens
- **WeCom:** Webhooks, AES encryption
- **GitHub:** OAuth/App, Issues/Discussions, webhooks

**Core Framework (Phase 10-11):**
- `UnifiedConnectorInterface` — Protocol
- `SyncEngine` — Bidirectional sync
- `HealthMonitor` — Three-tier health status
- `RateLimitManager` — Per-platform limits
- `WebhookVerifier` — Signature verification

### Dashboard Data Sources

Each connector provides:
- `platform_name` — Platform identifier
- `health_status` — HEALTHY/DEGRADED/UNHEALTHY
- `last_sync_at` — Last successful sync time
- `sync_direction` — pull/push/bidirectional
- `items_synced` — Total items synced
- `error_count` — Recent errors
- `is_connected` — OAuth/token status

### Web UI Integration

Existing Web UI components to extend:
- `src/saw/web/components/Dashboard.tsx` — Extend with connector cards
- `src/saw/web/components/Sidebar.tsx` — Add Integrations section
- API endpoints in `src/saw/api/` — Dashboard data endpoints

## Design Decisions (Auto-Decided)

Based on Phase 10-14 implementation and requirements:

1. **Dashboard API:** New endpoint `/api/v1/integrations/dashboard` returns aggregated status for all connectors.

2. **Per-Connector Cards:** Each platform has a card showing:
   - Platform icon (SVG)
   - Connection status (connected/disconnected/expired)
   - Health indicator (color: green/yellow/red)
   - Last sync time
   - Items synced count
   - Error summary (if any)

3. **Actions per Card:**
   - "Disconnect" button → DELETE `/api/v1/integrations/{platform}`
   - "Re-authorize" button (if expired) → GET `/api/v1/oauth/{platform}/authorize`
   - "Sync Now" button → POST `/api/v1/integrations/{platform}/sync`
   - "View Details" link → `/integrations/{platform}` detail page

4. **Error Messages:** Store errors in `connector_sync_log.errors`. Display last 3 errors with timestamps. Use human-readable format.

5. **Documentation Structure:**
   - `docs/integrations/overview.md` — Integration overview
   - `docs/integrations/notion.md` — Notion connector guide
   - `docs/integrations/logseq.md` — Logseq connector guide
   - `docs/integrations/slack.md` — Slack connector guide
   - `docs/integrations/discord.md` — Discord connector guide
   - `docs/integrations/feishu.md` — Feishu connector guide
   - `docs/integrations/wecom.md` — WeCom connector guide
   - `docs/integrations/github.md` — GitHub connector guide

6. **Integration Testing:** Test all connectors together with:
   - Dashboard aggregation
   - Cross-connector sync (no interference)
   - Rate limiting across all platforms
   - Webhook routing to correct handlers

## Dependencies

- **Phase 12-14:** All connector implementations (Complete)
- **Web UI:** v1.1 React frontend (existing)

## Out of Scope

- Real-time WebSocket dashboard updates (deferred)
- Mobile-responsive dashboard (deferred)
- Connector-specific settings pages (Phase 15+)

---

*Context generated: 2026-05-02*
*Auto-decisions based on user instruction to make reasonable choices*