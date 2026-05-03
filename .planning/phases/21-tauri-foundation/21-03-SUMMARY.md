---
phase: 21-tauri-foundation
plan: 03
subsystem: desktop
tags: [theme, keyboard-shortcuts, tauri, react-hooks]
dependency_graph:
  requires:
    - 21-02-window-management
  provides:
    - theme-detection
    - global-shortcuts
  affects:
    - web/src/hooks/
tech_stack:
  added:
    - tauri-plugin-global-shortcut (Rust registration)
    - tauri-plugin-os (theme detection)
  patterns:
    - IPC event emission (Rust -> React)
    - CSS media query fallback (web mode)
key_files:
  created:
    - desktop/src-tauri/src/theme.rs
    - web/src/hooks/useTheme.ts
    - web/src/hooks/useShortcuts.ts
  modified:
    - desktop/src-tauri/src/main.rs
    - desktop/src-tauri/src/lib.rs
    - desktop/src-tauri/capabilities/default.json
decisions:
  - id: D-07
    outcome: "App follows system theme automatically via tauri-plugin-os"
  - id: D-08
    outcome: "Standard keyboard shortcuts registered globally"
metrics:
  duration: "5 minutes"
  completed_date: "2026-05-03"
---

# Phase 21 Plan 03: Theme Detection & Keyboard Shortcuts Summary

## One-Liner

System theme detection (dark/light) and global keyboard shortcuts (Cmd/Ctrl+N/O/S/Q/,) implemented with Rust-to-React IPC event emission.

## Implementation

### Task 1: Theme Detection

**Rust Side (`theme.rs`):**
- Created `get_system_theme` command that returns "dark" or "light" based on OS preference
- Created `setup_theme_listener` that emits initial theme via `theme-changed` event
- Uses `window.theme()` from tauri's WebviewWindow API

**React Side (`useTheme.ts`):**
- Detects Tauri vs web browser context
- In Tauri: invokes `get_system_theme` command and listens for `theme-changed` events
- In web browser: falls back to `prefers-color-scheme` media query
- Applies `dark` class to `document.documentElement` for CSS styling

### Task 2: Global Keyboard Shortcuts

**Rust Side (`main.rs`):**
- Created `setup_global_shortcuts` function using `GlobalShortcutExt`
- Registered 5 shortcuts:
  - `CmdOrCtrl+N` -> emits `shortcut:new-wiki`
  - `CmdOrCtrl+O` -> emits `shortcut:open-vault`
  - `CmdOrCtrl+S` -> emits `shortcut:save`
  - `CmdOrCtrl+Q` -> exits app directly (`app.exit(0)`)
  - `CmdOrCtrl+,` -> emits `shortcut:preferences`

**React Side (`useShortcuts.ts`):**
- Accepts handler map: `{ 'new-wiki': () => ..., 'save': () => ... }`
- Listens for `shortcut:*` events from Rust backend
- Only active in Tauri context (no-op in web browser)

## Files Modified

| File | Change |
|------|--------|
| `desktop/src-tauri/src/theme.rs` | Created - theme detection commands |
| `desktop/src-tauri/src/main.rs` | Added theme module, setup calls, shortcut registration |
| `desktop/src-tauri/src/lib.rs` | Uncommented theme module export |
| `desktop/src-tauri/capabilities/default.json` | Added `global-shortcut:allow-unregister` |
| `web/src/hooks/useTheme.ts` | Created - React theme hook |
| `web/src/hooks/useShortcuts.ts` | Created - React shortcuts hook |

## Requirements Met

| ID | Description | Status |
|----|-------------|--------|
| WIN-04 | Dark/light theme follows system setting | ✓ Complete |
| WIN-05 | Keyboard shortcuts for common operations | ✓ Complete |

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface

No new threat flags identified. All keyboard shortcuts trigger internal app actions only.

## Self-Check: PASSED

| Check | Status |
|-------|--------|
| `theme.rs` exists | ✓ FOUND |
| `useTheme.ts` exists | ✓ FOUND |
| `useShortcuts.ts` exists | ✓ FOUND |
| `mod theme` in main.rs | ✓ FOUND |
| Shortcuts registered | ✓ FOUND |
| Commit 75e4b2f (theme) | ✓ FOUND |
| Commit b505d10 (shortcuts) | ✓ FOUND |

---

*Completed: 2026-05-03*
