---
phase: 7
milestone: v3.0
name: Obsidian Plugin
goal: 用户可在 Obsidian 中浏览、编辑 SAW 知识库，实现双向同步
status: planning
created: 2026-04-30
---

# Phase 7: Obsidian Plugin — CONTEXT

## Phase Goal

用户可在 Obsidian 中浏览、编辑 SAW 知识库内容，实现双向同步。核心价值是让用户在熟悉的 Obsidian 环境中使用 SAW 的知识管理能力。

## Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| OBSP-01 | 用户可通过 Obsidian 插件浏览 SAW 知识库内容 | Table Stakes |
| OBSP-02 | Wiki 页面在 Obsidian 中可编辑并可同步回 SAW | Table Stakes |
| OBSP-03 | 支持 Obsidian 的双向链接 [[]] 语法 | Table Stakes |
| OBSP-04 | 插件可通过 SAW API 认证 | Table Stakes |
| OBSP-05 | 知识图谱可视化（Cytoscape 风格） | Differentiator |
| OBSP-06 | 置信度徽章显示在页面标题旁 | Differentiator |
| OBSP-07 | 矛盾检测提示（高亮冲突的 Claims） | Differentiator |

## Success Criteria

1. 用户可通过 Obsidian 插件浏览 SAW 知识库内容
2. Wiki 页面在 Obsidian 中可编辑并可同步回 SAW
3. 支持 Obsidian 的双向链接 [[]] 语法
4. 插件可通过 SAW API 认证
5. 知识图谱可视化展示置信度徽章

## Dependencies

### External Dependencies
- **v2.0 API Platform** — REST API endpoints for sync operations
- **Obsidian API 1.12.3** — Vault, Workspace, MetadataCache APIs
- **TypeScript 6.0.3** — Plugin language
- **esbuild 0.28.0** — Build tool

### Internal Dependencies
- **Claims DB** — Primary sync target for structured knowledge
- **Vault Layer** — Source documents (read-only in plugin)
- **Governance Engine** — Confidence tiers, freshness, conflict status
- **Query Engine** — Search functionality within Obsidian

## Technical Architecture

### Plugin Structure

```
smart-agent-wiki-plugin/
├── main.ts                 # Plugin entry point
├── settings.ts             # Settings tab definition
├── api/
│   ├── client.ts           # SAW REST API client
│   ├── auth.ts             # JWT authentication
│   └── sync.ts             # Bidirectional sync logic
├── views/
│   ├── graph-view.ts       # Cytoscape.js knowledge graph
│   ├── search-view.ts      # Search modal
│   └── settings-view.ts    # Settings UI
├── commands/
│   ├── sync-command.ts     # Manual sync trigger
│   ├── ingest-command.ts   # One-click ingest current file
│   └── query-command.ts    # Query from command palette
├── utils/
│   ├── frontmatter.ts      # YAML frontmatter parsing
│   ├── wikilinks.ts        # [[]] syntax conversion
│   └── badges.ts           # Confidence badge rendering
├── manifest.json           # Obsidian plugin manifest
├── styles.css              # Custom styles for badges/graph
└── esbuild.config.mjs      # Build configuration
```

### Data Flow: Bidirectional Sync

```
User creates/edits note in Obsidian
    │
    ▼
Plugin's onChange handler (debounced, 5s)
    │
    ▼
GET /api/v1/sync/status?path=note.md
    │
    ├─ If local newer:
    │      PUT /api/v1/wiki/{path}
    │      {
    │        "content": "...",
    │        "frontmatter": {...},
    │        "modified_at": "2026-04-30T..."
    │      }
    │      │
    │      ▼
    │      Claims DB updated -> Wiki layer updated
    │
    └─ If remote newer:
           Vault.modify(file, remote_content)
           │
           ▼
           Obsidian note updated with SAW content
```

### API Integration Points

| SAW Endpoint | Method | Plugin Usage |
|--------------|--------|--------------|
| `/api/v1/sync/status` | GET | Check if local or remote is newer |
| `/api/v1/wiki/{path}` | GET | Fetch wiki page content |
| `/api/v1/wiki/{path}` | PUT | Push local edits to SAW |
| `/api/v1/sync/batch` | POST | Batch sync multiple files |
| `/api/v1/query` | POST | Search from Obsidian command palette |
| `/api/v1/graph` | GET | Fetch graph data for visualization |
| `/api/v1/auth/token` | POST | Obtain JWT token for session |

## Critical Pitfalls to Prevent

### Pitfall 18: Vault.process() Race Condition

**Problem:** Using `cachedRead()` before modification causes stale data overwrite.

**Prevention:**
- Use `Vault.process()` for ALL atomic read-modify-write operations
- Never use `cachedRead()` when intending to modify
- Example:
  ```typescript
  // WRONG
  const content = await this.app.vault.cachedRead(file);
  await this.app.vault.modify(file, modifyContent(content));

  // RIGHT
  await this.app.vault.process(file, (content) => modifyContent(content));
  ```

### Pitfall 19: Event Listener Memory Leaks

**Problem:** Event listeners continue firing after plugin unload.

**Prevention:**
- Always use `this.registerEvent()` inside plugin class
- Use `this.registerDomEvent()` for DOM events
- Use `this.registerInterval()` for timers
- Example:
  ```typescript
  // WRONG
  this.app.vault.on('modify', (file) => this.handleModify(file));

  // RIGHT
  this.registerEvent(
    this.app.vault.on('modify', (file) => this.handleModify(file))
  );
  ```

### Pitfall 20: Incorrect File Type Checking

**Problem:** Operations crash when passed TFolder instead of TFile.

**Prevention:**
- Always check `instanceof TFile` before file operations
- Handle both TFile and TFolder cases
- Example:
  ```typescript
  const abstractFile = this.app.vault.getAbstractFileByPath('some/path');
  if (abstractFile instanceof TFile) {
    const content = await this.app.vault.read(abstractFile);
  } else if (abstractFile instanceof TFolder) {
    // Handle folder case
  }
  ```

### Pitfall 28: Bidirectional Sync State Corruption

**Problem:** Simultaneous changes in Obsidian and SAW cause unresolvable conflicts.

**Prevention:**
- Establish clear authority model: SAW is source of truth for metadata, local file for content
- Use last-write-wins with timestamp comparison
- Generate conflict files for manual resolution when both sides changed
- Show diff UI for user to choose winner or merge
- Track change vectors for conflict detection

### Pitfall 30: Schema Mismatch Between Sources

**Problem:** Obsidian notes and SAW wiki pages have incompatible metadata structures.

**Prevention:**
- Design unified source-agnostic schema
- Use YAML frontmatter for SAW metadata in Obsidian notes
- Implement adapter that normalizes Obsidian notes to SAW format
- Preserve Obsidian-specific frontmatter fields during sync

## Key Design Decisions

### 1. Sync Strategy: Last-Write-Wins with Conflict Files

**Decision:** When both local (Obsidian) and remote (SAW) have modifications since last sync, generate a conflict file with suffix `.conflict`.

**Rationale:** Simpler than CRDT/OT, aligns with Obsidian Sync behavior, user has explicit control.

**Implementation:**
- Store last-sync timestamp in plugin settings per file
- Compare local modified_at vs remote modified_at vs last_sync_at
- If both changed: create `note.md.conflict` with remote content, keep local
- User can then compare and merge manually

### 2. Wikilink Conversion: Preserve Obsidian Syntax

**Decision:** SAW wiki links are converted to Obsidian `[[]]` syntax on sync. Obsidian `[[]]` links are converted to SAW format on push.

**Rationale:** Users expect Obsidian-native link syntax; SAW's internal format should not leak.

**Implementation:**
- Pull: Convert SAW links `[[entity:Transformer]]` to Obsidian `[[Transformer]]`
- Push: Convert Obsidian `[[Transformer]]` to SAW format based on entity resolution
- Preserve link metadata in frontmatter for accurate conversion

### 3. Confidence Badge: Inline CSS Styling

**Decision:** Confidence tier shown as colored badge next to page title in file explorer and graph view.

**Rationale:** Visual indicator of trustworthiness; leverages Obsidian's CSS custom properties.

**Colors:**
- Layer 1 (Unverified): Gray (#808080)
- Layer 2 (Single Source): Bronze (#CD7F32)
- Layer 3 (Cross-Validated): Silver (#C0C0C0)
- Layer 4 (Human Verified): Gold (#FFD700)

**Implementation:**
- Add CSS class `.saw-confidence-{tier}` to file items
- Use CSS variables for consistent styling
- Update badge on sync completion

### 4. Graph View: Cytoscape.js Embedded View

**Decision:** Custom view using Cytoscape.js (same library as Web UI) embedded in Obsidian sidebar.

**Rationale:** Consistent graph experience across platforms; Obsidian's built-in graph lacks confidence/freshness visualization.

**Implementation:**
- Create custom `SmartAgentWikiGraphView` extending `ItemView`
- Fetch graph data from `/api/v1/graph` endpoint
- Apply same styling rules as Web UI (confidence colors, type shapes)
- Support click-to-navigate to wiki pages

## Implementation Patterns (from Obsidian API)

### Plugin Entry Point

```typescript
import { Plugin } from 'obsidian';

export default class SmartAgentWikiPlugin extends Plugin {
  async onload() {
    // Initialize settings
    await this.loadSettings();

    // Register commands
    this.addCommand({
      id: 'saw-sync',
      name: 'Sync with Smart Agent Wiki',
      callback: () => this.syncAllFiles()
    });

    // Register view
    this.registerView('saw-graph-view', (leaf) => new GraphView(leaf));

    // Register event handlers with auto-cleanup
    this.registerEvent(
      this.app.vault.on('modify', (file) => this.onFileModify(file))
    );

    // Add settings tab
    this.addSettingTab(new SAWSettingsTab(this.app, this));
  }

  onunload() {
    // Auto-cleaned by registerEvent/registerView patterns
  }
}
```

### Settings Pattern

```typescript
interface SAWPluginSettings {
  apiUrl: string;
  apiKey: string;
  syncInterval: number;
  lastSync: Record<string, string>; // path -> timestamp
}

const DEFAULT_SETTINGS: SAWPluginSettings = {
  apiUrl: 'http://localhost:8000',
  apiKey: '',
  syncInterval: 300000, // 5 minutes
  lastSync: {}
};

class SAWSettingsTab extends PluginSettingTab {
  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName('API URL')
      .setDesc('Smart Agent Wiki server URL')
      .addText(text => text
        .setPlaceholder('http://localhost:8000')
        .setValue(this.plugin.settings.apiUrl)
        .onChange(async (value) => {
          this.plugin.settings.apiUrl = value;
          await this.plugin.saveSettings();
        }));
  }
}
```

## UI Components

### 1. Settings Panel
- API URL configuration
- API Key input (JWT token)
- Sync interval configuration
- Manual sync trigger button
- Connection status indicator

### 2. Search Modal
- Command palette integration
- Search input with autocomplete
- Results list with confidence badges
- Click to open file or navigate to graph node

### 3. Graph View
- Sidebar view with Cytoscape.js
- Node styling by confidence tier
- Edge styling by relationship type
- Click-to-navigate to file
- Filter controls (by type, confidence, freshness)

### 4. Confidence Badges
- Inline badge in file explorer
- Color-coded by tier
- Hover tooltip with confidence derivation
- Badge in graph view node

### 5. Conflict Resolution UI
- Side-by-side diff view
- Accept local / Accept remote / Merge options
- Save merged result to both sides

## Test Strategy

### Unit Tests
- API client authentication
- Wikilink conversion bidirectional
- Frontmatter parsing
- Sync status comparison logic
- Badge CSS generation

### Integration Tests
- Full sync cycle: modify in Obsidian -> push to SAW -> pull back
- Conflict detection and resolution
- Graph data fetch and render
- Search query from Obsidian

### Manual Verification
- Install plugin in Obsidian vault
- Connect to local SAW instance
- Create/edit/sync multiple files
- Verify badges appear correctly
- Verify graph shows correct data
- Verify conflict files generated properly

## File Deliverables

| File | Purpose |
|------|---------|
| `.planning/phases/07-obsidian-plugin/PLAN-01.md` | Plugin core implementation |
| `.planning/phases/07-obsidian-plugin/PLAN-02.md` | API client and sync logic |
| `.planning/phases/07-obsidian-plugin/PLAN-03.md` | Graph view and badges |
| `.planning/phases/07-obsidian-plugin/PLAN-04.md` | Settings and commands |
| `.planning/phases/07-obsidian-plugin/VERIFICATION.md` | Test checklist |
| `.planning/phases/07-obsidian-plugin/SUMMARY.md` | Phase summary |

## Timeline Estimate

| Plan | Estimated Duration |
|------|-------------------|
| PLAN-01: Plugin Core | 1 day |
| PLAN-02: API Client & Sync | 1 day |
| PLAN-03: Graph View & Badges | 1 day |
| PLAN-04: Settings & Commands | 0.5 day |
| Integration & Testing | 0.5 day |
| **Total** | **4 days** |

## Notes

- **Phase 7 is marked with UI hint** — requires UI design for graph view, badges, and conflict resolution
- Obsidian plugin development is TypeScript-only — no Python backend changes needed
- All backend API endpoints needed for sync already exist in v2.0 API Platform (except `/api/v1/sync/*` which will be added)
- Plugin will be released as open-source Obsidian community plugin

---
*Context created: 2026-04-30*
*Phase: 7 — Obsidian Plugin*
*Milestone: v3.0 Ecosystem Integration*