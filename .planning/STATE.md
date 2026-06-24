# Project State

## Last Updated
2026-06-23 20:50

## Current Milestone
**v4.1: Entity Types + MCP Enhancement + Onboarding + Timeline** — COMPLETE ✅

### Completed Phases

#### Phase 53: Object/Entity Type System
- ✅ Backend: `EntityType`, `EntityField`, `EntityTypeRegistry` with 7 built-in types
- ✅ API: `GET /api/entity-types`, `GET /api/entity-types/{id}` endpoints
- ✅ Frontend: `EntityTypeBadge`, `EntityTypeSelector`, `PropertiesEditor` components
- ✅ Integration: `entity_type` and `properties` fields in WikiPage model and API schemas
- ✅ Filtering: Pages list and search support entity type filtering

#### Phase 54: MCP Server Enhancement
- ✅ Resources: 5 MCP resources (pages, page, graph, stats, search)
- ✅ Prompts: 6 prompt templates (summarize, research, compare, gaps, daily review, report)
- ✅ Page CRUD Tools: 5 tools (create, update, delete, read, list) via Write Queue
- ✅ Link Tools: 4 tools (wiki_link, wiki_unlink, backlinks, outlinks)
- ✅ Integration: MCP server initializes wiki_repo and write_queue for new tools

#### Phase 55: Onboarding Flow
- ✅ Backend: 4 starter kits (personal_pkm, team_wiki, research_notebook, project_tracker)
- ✅ API: `GET /api/onboarding/status`, `POST /api/onboarding/seed` endpoints
- ✅ Frontend: 4-step wizard (Welcome, Choose Path, Seeding, Complete)
- ✅ Router: `/onboarding` route added
- ✅ localStorage: First-run detection and completion tracking

#### Phase 56: Timeline View
- ✅ Backend: Timeline API with date grouping and filtering
- ✅ API: `GET /api/timeline`, `POST /api/timeline/daily-note` endpoints
- ✅ Frontend: Timeline page with day groups, filters, and daily note button
- ✅ Components: `TimelineEntry`, `TimelineDayGroup`, `TimelineFilters`, `DailyNoteButton`
- ✅ Router: `/timeline` route added to navigation

#### Phase 52: Template System
- ✅ 5 built-in templates: Daily Note, Meeting Notes, Project Overview, Concept Explainer, Research Summary
- ✅ Backend: `TemplateRegistry` with variable substitution
- ✅ API: `GET /api/templates`, `GET /api/templates/{id}`, `POST /api/templates/{id}/apply`
- ✅ Frontend: Templates gallery page with modal workflow

#### Phase 51: Related Pages
- ✅ Engine: 3-signal relevance scoring (shared tags, shared links, type affinity)
- ✅ API: `GET /api/pages/{slug}/related` endpoint
- ✅ Frontend: `RelatedPagesPanel` component integrated into Page.tsx
- ✅ Score visualization with opacity-based indicators

#### Phase 50: Quick Capture
- ✅ Backend: `POST /api/capture` endpoint with auto-slug generation
- ✅ Frontend: `QuickCapture` modal component with Cmd+Shift+N shortcut
- ✅ Write Queue integration for atomic page creation
- ✅ FTS5 index auto-update on capture

#### Phase 46: Bidirectional Links + Backlinks Panel
- ✅ Wiki link parser (`wiki_links.py`) — supports `[[page]]`, `[[page|alias]]`, `[[page#section]]`
- ✅ Backlinks API endpoint — `GET /api/pages/{slug}/backlinks` returns pages linking TO this page
- ✅ Outlinks API endpoint — `GET /api/pages/{slug}/outlinks` returns pages this page links TO
- ✅ BacklinksPanel component — displays reverse links with context snippets
- ✅ Integrated into Page.tsx

#### Phase 47: FTS5 Full-Text Search + Cmd+K Palette
- ✅ Wiki indexer (`wiki_indexer.py`) — indexes all wiki pages into FTS5 on startup
- ✅ Search API enhanced — `/api/search` now includes wiki pages via FTS5
- ✅ Command Palette component (`CommandPalette.tsx`) — Cmd+K / Ctrl+K quick navigation
- ✅ Integrated into App.tsx with search button in header

#### Phase 48: Graph Real Data from Wiki Pages
- ✅ Wiki graph builder (`wiki_graph.py`) — builds nodes/edges from wiki pages and [[wiki-links]]
- ✅ Graph API updated — `/api/graph` now uses wiki pages as primary source
- ✅ Falls back to entity graph if wiki is empty
- ✅ BFS subgraph traversal from any page

#### Phase 49: Markdown/Obsidian Import
- ✅ Import API endpoints — `POST /api/import/markdown` (multiple files) and `POST /api/import/zip`
- ✅ Frontmatter parsing — extracts title, tags, metadata
- ✅ Wiki link resolution — resolves `[[wiki-links]]` between imported files
- ✅ Import page UI (`Import.tsx`) — drag-and-drop, file upload, ZIP upload
- ✅ Progress and result display

## Architecture Changes

### New Files (v4.1)
**Backend (src/saw/):**
- `domain/entity_types.py` — EntityType, EntityField, EntityTypeRegistry
- `onboarding/starter_kits.py` — 4 starter kit definitions
- `drivers/web/routes/entity_types.py` — Entity type API endpoints
- `drivers/web/routes/onboarding.py` — Onboarding status and seed endpoints
- `drivers/web/routes/timeline.py` — Timeline API endpoints
- `drivers/web/schemas/timeline.py` — Timeline API schemas
- `drivers/mcp/resources.py` — MCP resources for reading wiki data
- `drivers/mcp/prompts.py` — MCP prompt templates
- `drivers/mcp/tools/pages.py` — Page CRUD MCP tools
- `drivers/mcp/tools/links.py` — Wiki link MCP tools

**Frontend (web/src/):**
- `hooks/useEntityTypes.ts` — Entity types query hook
- `hooks/useOnboarding.ts` — Onboarding status and seed hooks
- `hooks/useTimeline.ts` — Timeline query and daily note hooks
- `components/entity/EntityTypeBadge.tsx` — Type badge display
- `components/entity/EntityTypeSelector.tsx` — Type selection UI
- `components/entity/PropertiesEditor.tsx` — Dynamic properties form
- `components/timeline/TimelineEntry.tsx` — Entry card renderer
- `components/timeline/TimelineDayGroup.tsx` — Day group renderer
- `components/timeline/TimelineFilters.tsx` — Filter controls
- `components/timeline/DailyNoteButton.tsx` — Daily note creator
- `pages/Onboarding.tsx` — 4-step onboarding wizard
- `pages/Timeline.tsx` — Timeline view page

### Modified Files (v4.1)
- `domain/wiki.py` — WikiPage extended with entity_type and properties
- `adapters/storage/wiki_repository.py` — Serialize/deserialize entity_type and properties
- `drivers/web/schemas/pages.py` — PageResponse/PageCreate/PageUpdate extended
- `drivers/web/routes/pages.py` — Entity type filtering in list_pages
- `drivers/web/app.py` — Register entity_types, onboarding, timeline routers
- `drivers/mcp/server.py` — Initialize wiki_repo and write_queue
- `drivers/mcp/tools/__init__.py` — Register pages and links modules
- `routes/router.tsx` — Add onboarding and timeline routes
- `App.tsx` — Add Timeline to navigation
- `types/api.ts` — Add EntityType, EntityField, timeline types
- `pages/Pages.tsx` — Entity type filter and badge display
- `pages/Page.tsx` — Entity type badge and properties editor

### New Files (v4.0)
**Backend (src/saw/):**
- `drivers/web/routes/capture.py` — Quick capture endpoint
- `drivers/web/routes/templates.py` — Template management endpoints
- `engines/query/related_pages.py` — Related pages calculator
- `templates/registry.py` — Template registry and loader
- `templates/*.md` — 5 built-in template files

**Frontend (web/src/):**
- `components/capture/QuickCapture.tsx` — Quick capture modal
- `components/related/RelatedPagesPanel.tsx` — Related pages display
- `hooks/useCapture.ts` — Capture mutation hook
- `hooks/useRelated.ts` — Related pages query hook
- `pages/Templates.tsx` — Template gallery page

### Modified Files (v4.0)
- `drivers/web/app.py` — Register capture and templates routers
- `drivers/web/routes/pages.py` — Add `/related` endpoint
- `drivers/web/schemas/pages.py` — Add QuickCapture schemas
- `App.tsx` — Integrate QuickCapture, add Templates nav link
- `pages/Page.tsx` — Add RelatedPagesPanel
- `routes/router.tsx` — Add /templates route
- `types/api.ts` — Add QuickCapture, RelatedPage types

### New Files (v3.9)
**Backend (src/saw/):**
- `engines/query/wiki_links.py` — Wiki link parser and slugify
- `engines/query/wiki_indexer.py` — FTS5 wiki page indexer
- `engines/query/wiki_graph.py` — Graph builder from wiki pages
- `drivers/web/routes/import_md.py` — Markdown/ZIP import endpoints

**Frontend (web/src/):**
- `components/links/BacklinksPanel.tsx` — Backlinks display component
- `components/search/CommandPalette.tsx` — Cmd+K command palette
- `pages/Import.tsx` — Import page UI

### Modified Files
- `drivers/web/routes/pages.py` — Added backlinks/outlinks endpoints
- `drivers/web/routes/graph.py` — Updated to use wiki graph builder
- `drivers/web/app.py` — Register import router, wiki indexer on startup
- `web/src/App.tsx` — Add CommandPalette, Import nav link
- `web/src/routes/router.tsx` — Add /import route
- `web/src/pages/Page.tsx` — Integrate BacklinksPanel

## Key Features Delivered

1. **Entity Type System** — User-facing page classification (person, project, concept, meeting, reference, bookmark) with structured properties
2. **MCP Server Enhancement** — 5 resources, 6 prompts, 9 new tools for comprehensive AI integration
3. **Onboarding Flow** — 4-step wizard with 4 starter kits for new user setup
4. **Timeline View** — Chronological page view with daily note creation
5. **Bidirectional Linking** — Obsidian-style `[[wiki-links]]` with automatic backlink resolution
6. **Full-Text Search** — FTS5 indexing with BM25 ranking, Cmd+K quick access
7. **Real Graph Visualization** — Graph now shows actual wiki page connections
8. **Markdown Import** — Bulk import from Obsidian vaults or any markdown files
9. **Quick Capture** — Frictionless page creation with Cmd+Shift+N
10. **Related Pages** — AI-powered page recommendations
11. **Template System** — 5 built-in templates for common use cases

## Verification Status

### Code Quality
- ✅ All new code follows existing patterns
- ✅ Type hints on all public APIs
- ✅ Proper error handling
- ✅ Consistent naming conventions

### Integration Points
- ✅ Entity types integrated into WikiPage model
- ✅ MCP server initializes new tools with wiki_repo and write_queue
- ✅ Onboarding starter kits create pages via Write Queue
- ✅ Timeline API groups pages by date with filtering
- ✅ Frontend components integrated into pages and navigation

## Next Steps (Recommended)

### v4.2: Semantic Features
- Embedding-based semantic search
- AI-powered content summarization
- Smart linking suggestions

### v4.3: Agent Visualization
- Agent activity dashboard
- Real-time agent status display
- Workflow visualization

### v4.4: Desktop App Completion
- Phase 23-25: System integration, distribution, sidecar

## Notes

All v4.1 features successfully implemented:
1. ✅ Object/Entity Type System — 7 built-in types with structured properties
2. ✅ MCP Server Enhancement — 14 new MCP capabilities (5 resources + 6 prompts + 9 tools)
3. ✅ Onboarding Flow — 4 starter kits with interactive wizard
4. ✅ Timeline View — Chronological view with daily note creation

The platform now has comprehensive knowledge management features, AI integration, and user onboarding.
