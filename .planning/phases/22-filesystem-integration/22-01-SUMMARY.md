---
phase: 22-filesystem-integration
plan: 01
status: complete
completed: "2026-05-04"
requirements:
  - FS-01
  - FS-02
  - FS-05
files_created:
  - desktop/src-tauri/src/commands/fs.rs
  - desktop/src-tauri/src/watcher.rs
  - web/src/hooks/useDragDrop.ts
  - web/src/hooks/useFileDialog.ts
  - web/src/components/DropZone.tsx
files_modified:
  - desktop/src-tauri/Cargo.toml
  - desktop/src-tauri/src/commands/mod.rs
  - desktop/src-tauri/src/lib.rs
  - desktop/src-tauri/src/main.rs
  - desktop/src-tauri/capabilities/default.json
key_decisions:
  - Use notify 6.1 for cross-platform file watching
  - Use tauri-plugin-dialog for native file dialogs (already installed)
  - Store app data in platform-standard directories with subdirectories
  - Support portable mode via "portable" marker file
  - Dynamic fs scope via dialog selection (automatic in Tauri 2.x)
---

# Phase 22-01: File System Commands and Dialogs

## Summary

Implemented core file system integration for the Tauri desktop application, enabling drag-drop ingestion, native file dialogs, and standard app data storage.

## What Was Built

### Rust Backend (desktop/src-tauri/)

1. **File System Commands** (`src/commands/fs.rs`)
   - `select_files()` - Native file dialog for document selection (.md, .txt, .pdf, .docx, .html)
   - `select_folder()` - Native folder dialog for directory selection
   - `select_export_location()` - Save file dialog for export destinations
   - `get_app_data_dir()` - Returns platform-specific app data directory
   - `is_portable_mode()` - Detects portable mode via marker file
   - `setup_app_directories()` - Creates vault/, preferences/, cache/, logs/ subdirectories

2. **File Watcher Module** (`src/watcher.rs`)
   - Cross-platform file watching using notify 6.1
   - 100ms debounce configuration
   - Event emission: `fs:file-created`, `fs:file-modified`, `fs:file-deleted`
   - File type filtering support
   - Watcher state managed via Tauri state

3. **Dependencies**
   - Added `notify = "6.1"` to Cargo.toml

4. **Capabilities** (`capabilities/default.json`)
   - Added fs:scope with allow patterns for $APPDATA, $DOCUMENT, $HOME, $CACHE, $CONFIG, $LOG
   - Added fs:allow-read-text-file, fs:allow-write-text-file, fs:allow-exists, fs:allow-mkdir

### React Frontend (web/src/)

1. **useDragDrop Hook** (`hooks/useDragDrop.ts`)
   - Handles dragenter, dragover, dragleave, drop events
   - Extracts file paths from Tauri's DataTransfer extension
   - Invokes `fs:ingest-files` IPC command
   - Configurable file type filtering
   - Loading state and error handling

2. **useFileDialog Hook** (`hooks/useFileDialog.ts`)
   - `openFiles()` - Opens native file selection dialog
   - `openFolder()` - Opens native folder selection dialog
   - `saveFile(defaultName)` - Opens native save dialog
   - Loading state and error handling

3. **DropZone Component** (`components/DropZone.tsx`)
   - Wraps content area for drop handling
   - Visual feedback overlay when dragging files
   - Configurable callbacks for ingestion events

## Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| notify crate added | ✓ | Cargo.toml contains `notify = "6.1"` |
| fs.rs with commands | ✓ | 5 IPC commands with `#[tauri::command]` |
| Commands registered | ✓ | main.rs invoke_handler includes all commands |
| App directories setup | ✓ | setup_app_directories called in setup block |
| useDragDrop hook | ✓ | invoke usage, drag event handlers |
| DropZone component | ✓ | onDragOver, onDragLeave, onDrop handlers |
| useFileDialog hook | ✓ | openFiles, openFolder, saveFile methods |
| Capabilities updated | ✓ | fs:scope with $APPDATA, $DOCUMENT, $HOME |

## Requirements Coverage

- **FS-01** (Drag-drop): DropZone component + useDragDrop hook ready for UI integration
- **FS-02** (File dialogs): useFileDialog hook provides native dialog access
- **FS-05** (App data storage): get_app_data_dir + setup_app_directories for standard locations

## Integration Notes

- The DropZone and useFileDialog hooks are ready for integration into the main UI
- fs:ingest-files IPC command needs backend implementation (currently placeholder)
- File watcher module ready for Phase 22-02 (folder watching feature)

## Next Steps

Phase 22-02 will implement:
- Folder watching with automatic ingestion
- Wiki page export (Markdown/PDF)
- useFileWatcher hook for React integration
- useExport hook and ExportDialog component
