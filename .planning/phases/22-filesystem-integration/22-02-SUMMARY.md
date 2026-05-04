---
phase: 22-filesystem-integration
plan: 02
status: complete
completed: "2026-05-04"
requirements:
  - FS-03
  - FS-04
files_created:
  - desktop/src-tauri/src/commands/export.rs
  - web/src/hooks/useFileWatcher.ts
  - web/src/hooks/useExport.ts
  - web/src/components/ExportDialog.tsx
files_modified:
  - desktop/src-tauri/src/commands/fs.rs
  - desktop/src-tauri/src/commands/mod.rs
  - desktop/src-tauri/src/main.rs
key_decisions:
  - Use notify 6.1 RecommendedWatcher with 100ms debounce
  - Store watchers in Mutex<HashMap> as Tauri managed state
  - PDF export via WebView print() API (no additional dependencies)
  - Markdown export placeholder for backend integration (Phase 25)
  - Emit Tauri events for file changes: fs:file-created, fs:file-modified, fs:file-deleted
---

# Phase 22-02: Folder Watching and Wiki Export

## Summary

Implemented folder watching for automatic file ingestion and wiki page export functionality for the Tauri desktop application.

## What Was Built

### Rust Backend (desktop/src-tauri/)

1. **Watcher IPC Commands** (added to `commands/fs.rs`)
   - `add_watch_folder(path, config)` - Start watching a directory
   - `remove_watch_folder(path)` - Stop watching
   - `get_watched_folders()` - List active watchers
   - `update_watch_config(path, config)` - Modify watch settings

2. **Export Module** (`src/commands/export.rs`)
   - `ExportFormat` enum: Markdown, PDF
   - `ExportResult` struct: path, pages_exported, errors
   - `get_export_default_dir()` - Returns ~/Documents/Smart Agent Wiki/Exports/
   - `export_wiki_markdown(page_ids, output_dir)` - Placeholder Markdown export
   - `export_wiki_pdf(page_id, output_path)` - WebView print-based PDF export
   - `sanitize_filename()` - Safe filename generation

3. **Command Registration**
   - 7 new commands added to invoke_handler

### React Frontend (web/src/)

1. **useFileWatcher Hook** (`hooks/useFileWatcher.ts`)
   - Subscribe to `fs:file-created`, `fs:file-modified`, `fs:file-deleted` events
   - `addWatchFolder(path, config)` - Start watching
   - `removeWatchFolder(path)` - Stop watching
   - `updateWatchConfig(path, config)` - Modify settings
   - Auto-cleanup listeners on unmount
   - Dispatches custom events for app-level handling

2. **useExport Hook** (`hooks/useExport.ts`)
   - `exportMarkdown(pageIds, outputDir?)` - Export to Markdown
   - `exportPdf(pageId, outputPath?)` - Export to PDF
   - `getDefaultExportDir()` - Get default export location
   - Loading and error state management

3. **ExportDialog Component** (`components/ExportDialog.tsx`)
   - Format selection: Markdown (.md) or PDF (.pdf)
   - Location browser integration
   - Page count display
   - Progress indicator during export
   - Success/error feedback

## Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| watcher.rs with RecommendedWatcher | ✓ | notify 6.1 integration |
| fs:file-created/modified/deleted events | ✓ | emit() calls in watcher callback |
| Watch commands registered | ✓ | main.rs invoke_handler |
| useFileWatcher hook | ✓ | listen() + addWatchFolder/removeWatchFolder |
| export.rs module | ✓ | export_wiki_markdown + export_wiki_pdf |
| Export commands registered | ✓ | main.rs invoke_handler |
| useExport hook | ✓ | exportMarkdown + exportPdf |
| ExportDialog component | ✓ | Format selection UI |

## Requirements Coverage

- **FS-03** (Folder watching): Watcher module emits events on file changes, useFileWatcher subscribes and dispatches
- **FS-04** (Wiki export): Markdown and PDF export commands with ExportDialog UI

## Integration Notes

- Full wiki-to-markdown conversion requires backend API (Phase 25)
- PDF export uses WebView print() - opens print dialog for user
- Watcher events dispatched as custom DOM events for app flexibility

## Next Steps

Phase 23 will implement:
- URL protocol handler (saw://)
- File association (.md/.pdf)
- System notifications
- System search integration
- Background sync
