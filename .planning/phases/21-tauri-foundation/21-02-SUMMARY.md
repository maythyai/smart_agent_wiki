---
phase: 21-tauri-foundation
plan: 02
subsystem: window-management
tags: [tauri, menu, tray, preferences, ipc]
requires: [21-01]
provides:
  - Native menu bar with File, Edit, View, Help
  - System tray with Show/Hide/Quit actions
  - Configurable window close behavior (minimize-to-tray)
affects: [desktop/src-tauri/src/*]
tech-stack:
  added:
    - tauri::menu (MenuBuilder, SubmenuBuilder, MenuItemBuilder)
    - tauri::tray (TrayIconBuilder)
    - tauri_plugin_store (StoreExt)
    - IPC commands via #[tauri::command]
  patterns:
    - MenuBuilder pattern for native menus
    - TrayIconBuilder pattern for system tray
    - StoreExt for persistent preferences
    - on_window_event for close behavior interception
key-files:
  created:
    - desktop/src-tauri/src/menu.rs
    - desktop/src-tauri/src/tray.rs
    - desktop/src-tauri/src/commands/mod.rs
    - desktop/src-tauri/src/commands/preferences.rs
  modified:
    - desktop/src-tauri/src/main.rs
    - desktop/src-tauri/src/lib.rs
decisions:
  - D-04: Native menu bar with standard commands (implemented)
  - D-05: System tray with quick actions (implemented)
  - D-06: Window close behavior configurable (implemented)
  - D-10: Rust handles native operations (implemented)
metrics:
  duration: 229s
  tasks_completed: 3
  files_created: 4
  files_modified: 2
  completed_date: 2026-05-03
---

# Phase 21 Plan 02: Native Window Management Summary

Native menu bar, system tray, and configurable window close behavior implemented using Tauri 2.x APIs. All features use Rust for native operations and emit events to the React frontend for handling.

## One-liner

Native desktop UX with File/Edit/View/Help menu bar, system tray quick actions, and configurable minimize-to-tray on close via tauri-plugin-store persistence.

## Completed Tasks

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Native menu bar with File, Edit, View, Help menus | 6968ade | menu.rs, main.rs, lib.rs |
| 2 | System tray with Show/Hide/Quit actions | 1411086 | tray.rs, main.rs, lib.rs |
| 3 | Window close behavior with minimize-to-tray option | 9e6a86f | commands/mod.rs, commands/preferences.rs, main.rs, lib.rs |

## Implementation Details

### Task 1: Native Menu Bar

Created `menu.rs` implementing native menu bar per D-04:

- **File menu**: New Wiki (CmdOrCtrl+N), Open Vault (CmdOrCtrl+O), Save (CmdOrCtrl+S), Preferences (CmdOrCtrl+,), Quit (CmdOrCtrl+Q)
- **Edit menu**: Undo (CmdOrCtrl+Z), Redo (CmdOrCtrl+Shift+Z), Cut (CmdOrCtrl+X), Copy (CmdOrCtrl+C), Paste (CmdOrCtrl+V)
- **View menu**: Toggle Sidebar (CmdOrCtrl+B), Reload (CmdOrCtrl+R)
- **Help menu**: Documentation, Keyboard Shortcuts, About Smart Agent Wiki

Menu events are emitted to frontend via `window.emit("menu-event", id)` for React to handle.

### Task 2: System Tray

Created `tray.rs` implementing system tray per D-05:

- Tray icon uses app's default window icon
- Context menu items: Show Window, Hide Window, Quit
- Tray events handled directly in Rust (show/hide window, exit app)
- Tray provides quick access when main window is hidden

### Task 3: Window Close Behavior

Created `commands/preferences.rs` implementing configurable close behavior per D-06:

- `WindowPreferences` struct with `minimize_to_tray: bool` and `theme: String`
- `get_window_preferences` command for frontend to read preferences
- `set_window_preferences` command for frontend to save preferences
- Stored persistently via tauri-plugin-store in `preferences.json`
- Default: `minimize_to_tray: true` (minimize on close, quit via tray/menu)
- `on_window_event` handler intercepts `CloseRequested` and hides window when preference is true

## Requirements Satisfied

| ID | Description | Status |
|----|-------------|--------|
| WIN-01 | Native window menu for common actions | Implemented |
| WIN-02 | System tray icon for quick access | Implemented |
| WIN-03 | Configurable window close behavior | Implemented |

## Deviations from Plan

None - plan executed exactly as written.

## Deferred Items

- Linux WebKitGTK system libraries (javascriptcoregtk-4.1, libsoup-3.0) not installed on WSL environment - compilation requires system packages per RESEARCH.md Pitfall 5
- Runtime verification deferred until system dependencies installed

## Self-Check: PASSED

- All 4 created files exist in src-tauri/src/
- All 3 commits found in git log
- All acceptance criteria verified via grep patterns

## Threat Flags

None - all files in scope per threat_model (T-21-05, T-21-06, T-21-07).

---

*Completed: 2026-05-03*
*Duration: 229 seconds*