# Phase 22: File System Integration - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Source:** Requirements-driven + Phase 21 integration

<domain>
## Phase Boundary

This phase implements file system integration for the Tauri desktop app:
1. Drag-and-drop file ingestion (FS-01)
2. Native file dialogs for file/folder selection (FS-02)
3. Folder watching with automatic ingestion (FS-03)
4. Wiki page export to Markdown/PDF (FS-04)
5. Standard app data storage location (FS-05)

**In scope:**
- Tauri IPC commands for file operations
- React hooks for drag-drop handling
- tauri-plugin-fs scope configuration
- tauri-plugin-dialog for file dialogs
- notify crate for folder watching
- Markdown/PDF export functionality
- App data directory management

**Out of scope:**
- URL protocol handler (Phase 23: SYS-01)
- File association (Phase 23: SYS-02)
- System notifications (Phase 23: SYS-03)
- System search integration (Phase 23: SYS-04)
- Background sync (Phase 23: SYS-05)

</domain>

<decisions>
## Implementation Decisions

### Drag and Drop (FS-01)

- **D-22-01**: Use HTML5 drag-drop API in React with Tauri file handling
  - **Why:** Standard web API works in WebView, Tauri provides file path access
  - React component handles drop events, extracts file paths
  - Rust command processes files via tauri-plugin-fs

- **D-22-02**: Support multiple file types for drag-drop
  - **Why:** Users may drag various document types
  - Accept: .md, .txt, .pdf, .docx, .html, .url
  - Reject gracefully with notification for unsupported types

### File Dialogs (FS-02)

- **D-22-03**: Use tauri-plugin-dialog for native file dialogs
  - **Why:** Native dialogs feel right on each platform
  - Already installed in Phase 21
  - Supports file and folder selection modes

- **D-22-04**: Single and multiple file selection modes
  - **Why:** Different ingestion workflows need different selection patterns
  - "Open File" dialog: single or multiple files
  - "Open Folder" dialog: single folder for batch ingestion

### Folder Watching (FS-03)

- **D-22-05**: Use `notify` crate for filesystem watching
  - **Why:** Cross-platform, async-friendly, well-maintained
  - Watches for create, modify, delete events
  - Debounces rapid events (100ms window)

- **D-22-06**: Per-folder watch configuration stored in preferences
  - **Why:** Users may want different watch behaviors per folder
  - Store: path, enabled, file_types, auto_ingest flag
  - Accessible from settings UI

- **D-22-07**: Event handling via Tauri IPC
  - **Why:** React frontend needs to react to file changes
  - Rust emits events: `fs:file-created`, `fs:file-modified`, `fs:file-deleted`
  - React listens via `@tauri-apps/api/event`

### Export Functionality (FS-04)

- **D-22-08**: Markdown export using existing Claim serialization
  - **Why:** Wiki pages are already structured Markdown-compatible
  - Export single page or entire wiki tree
  - Preserve wikilinks as relative links where possible

- **D-22-09**: PDF export via browser print API
  - **Why:** No additional Rust dependencies needed
  - Use WebView's built-in print functionality
  - Electron-style: generate HTML, trigger print dialog

- **D-22-10**: Export location configurable with default
  - **Why:** Users expect control over where exports go
  - Default: ~/Documents/Smart Agent Wiki/Exports/
  - Configurable in preferences

### App Data Storage (FS-05)

- **D-22-11**: Use Tauri's app data directory API
  - **Why:** Standard location per platform, handled by Tauri
  - Windows: `%APPDATA%/com.smart-agent.wiki/`
  - macOS: `~/Library/Application Support/com.smart-agent.wiki/`
  - Linux: `~/.local/share/com.smart-agent.wiki/`

- **D-22-12**: Subdirectory structure for organized storage
  - **Why:** Separate different data types
  - `vault/` - User content (vault database)
  - `preferences/` - App settings (preferences.json)
  - `cache/` - Temporary data (thumbnails, search index)
  - `logs/` - Application logs

- **D-22-13**: Portable mode detection and handling
  - **Why:** Users may want to run from USB drive
  - Detect `portable` file next to executable
  - Use `./data/` directory instead of system location

### Architecture

- **D-22-14**: Rust commands for all file operations
  - **Why:** Security (capabilities), performance, error handling
  - `fs:ingest-files` - Process dragged files
  - `fs:select-files` - Open file dialog
  - `fs:select-folder` - Open folder dialog
  - `fs:export-wiki` - Export to file
  - `fs:get-app-data-dir` - Get storage location

- **D-22-15**: React hooks wrap Tauri APIs
  - **Why:** Ergonomic React integration, centralize error handling
  - `useDragDrop()` - Handle drag-drop events
  - `useFileWatcher()` - Subscribe to file events
  - `useExport()` - Export functionality

### Security

- **D-22-16**: FS scope limited to user-selected paths
  - **Why:** Least privilege principle
  - tauri-plugin-fs scope is dynamic
  - Dialog selection automatically adds to scope

- **D-22-17**: Validate all file paths before processing
  - **Why:** Prevent path traversal attacks
  - Check path is within allowed scope
  - Reject symlinks pointing outside scope

### Claude's Discretion

- Exact `notify` crate version and configuration
- Debounce timing for folder watching
- Export file naming convention
- Error message formatting for users

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Project overview, tech stack, constraints
- `.planning/STATE.md` — Current milestone and progress
- `.planning/REQUIREMENTS.md` — FS-01~05 requirements

### Phase 21 Context (Prerequisite)
- `desktop/src-tauri/src/main.rs` — Tauri app entry point
- `desktop/src-tauri/Cargo.toml` — Current Rust dependencies
- `desktop/src-tauri/capabilities/default.json` — Security permissions

### Existing Frontend
- `web/src/hooks/` — Existing React hooks pattern
- `web/src/services/api.ts` — API communication pattern

### Tauri Documentation (to be researched)
- tauri-plugin-fs scope configuration
- tauri-plugin-dialog API
- notify crate documentation
- Tauri app data directory API

</canonical_refs>

<specifics>
## Specific Ideas

1. **Drag-drop React component:**
   ```tsx
   // web/src/components/DropZone.tsx
   const DropZone: React.FC = () => {
     const handleDrop = async (e: React.DragEvent) => {
       e.preventDefault();
       const files = Array.from(e.dataTransfer.files);
       const paths = files.map(f => (f as any).path).filter(Boolean);
       if (paths.length > 0) {
         await invoke('fs:ingest-files', { paths });
       }
     };
     // ...
   };
   ```

2. **File watcher Rust module:**
   ```rust
   // desktop/src-tauri/src/watcher.rs
   use notify::{Watcher, RecursiveMode, Event};
   use tauri::Manager;

   pub fn start_watching(app: &AppHandle, path: &Path) -> Result<()> {
       let (tx, rx) = std::sync::mpsc::channel();
       // Watch and emit events to frontend
   }
   ```

3. **Export command:**
   ```rust
   #[tauri::command]
   async fn export_wiki(page_id: String, format: ExportFormat) -> Result<String> {
       // Generate Markdown/PDF and return file path
   }
   ```

4. **App data directory structure:**
   ```
   com.smart-agent.wiki/
   ├── vault/
   │   └── vault.db
   ├── preferences/
   │   └── preferences.json
   ├── cache/
   │   └── search_index.db
   └── logs/
       └── app.log
   ```

</specifics>

<deferred>
## Deferred Ideas

- URL protocol saw:// (Phase 23: SYS-01)
- File association .md/.pdf (Phase 23: SYS-02)
- System notifications (Phase 23: SYS-03)
- System search integration (Phase 23: SYS-04)
- Background sync (Phase 23: SYS-05)
- Auto-update mechanism (Phase 24: DIST-02)
- Python sidecar integration (Phase 25: BACK-01~05)

</deferred>

---

*Phase: 22-filesystem-integration*
*Context gathered: 2026-05-03*
