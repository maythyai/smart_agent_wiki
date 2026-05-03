# Phase 21: Tauri Foundation - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning
**Source:** Requirements-driven + Technical research

<domain>
## Phase Boundary

This phase establishes the Tauri desktop application foundation:
1. Application framework setup (Tauri + Rust + WebView)
2. Native window management (menus, tray, themes)
3. React UI integration with Tauri
4. Cross-platform build configuration

**In scope:**
- Tauri project initialization
- Window creation and configuration
- Native menu implementation
- System tray integration
- Theme detection and application
- Keyboard shortcuts

**Out of scope:**
- File system operations (Phase 22)
- URL protocol handlers (Phase 23)
- Distribution and updates (Phase 24)
- Python sidecar integration (Phase 25)

</domain>

<decisions>
## Implementation Decisions

### Application Framework

- **D-01**: Use Tauri 2.x (latest stable) for desktop app framework
  - **Why:** Tauri 2.x has improved security, smaller bundles, and better cross-platform support
  - **Rust backend** handles native functionality
  - **WebView2 (Windows)/WebKit (macOS/Linux)** renders existing React UI

- **D-02**: Reuse existing React frontend without modification
  - **Why:** Current web/ directory contains working React + Vite app
  - Tauri loads the same static files via `tauri.conf.json` configuration
  - No changes to React code needed for basic integration

- **D-03**: Use Tauri's built-in build system for packaging
  - **Why:** Tauri CI/CD integrates with GitHub Actions
  - Produces .msi/.exe (Windows), .dmg/.app (macOS), .deb/.rpm/.AppImage (Linux)

### Window Management

- **D-04**: Native menu bar with standard commands
  - **Why:** Desktop users expect native menu bar (File, Edit, View, Help)
  - Use Tauri's Menu API for cross-platform menus
  - Implement: New Wiki, Open Vault, Save, Export, Preferences, About

- **D-05**: System tray icon with quick actions
  - **Why:** Quick access without full app window
  - Show/hide window, quick ingest, recent wikis
  - Use Tauri's SystemTray API

- **D-06**: Window close behavior configurable
  - **Why:** Some users prefer minimize-to-tray, others prefer quit
  - Default: minimize to tray on close, quit on Cmd/Ctrl+Q
  - Store preference in Tauri's app storage

- **D-07**: Follow system theme automatically
  - **Why:** Desktop apps should respect OS theme preference
  - Use Tauri's Theme API to detect system theme
  - Apply dark/light theme to React UI via CSS variables

- **D-08**: Standard keyboard shortcuts
  - **Why:** Power users rely on keyboard navigation
  - Cmd/Ctrl+N: New Wiki
  - Cmd/Ctrl+O: Open Vault
  - Cmd/Ctrl+S: Save (sync)
  - Cmd/Ctrl+Q: Quit
  - Cmd/Ctrl+,: Preferences

### Architecture

- **D-09**: Tauri source location: `desktop/` directory
  - **Why:** Keep desktop app separate from web app
  - Shared frontend: Tauri loads from `../web/dist` in dev, bundles in production

- **D-10**: Rust side handles native operations
  - **Why:** Rust provides secure, performant native integration
  - File dialogs, tray menu, window state, theme detection

- **D-11**: React communicates with Tauri via `@tauri-apps/api`
  - **Why:** Standard Tauri IPC pattern
  - Invoke Rust commands from JavaScript
  - Listen to Rust events in React

### Performance Targets

- **D-12**: App size < 100MB (excluding user data)
  - **Why:** Tauri produces small bundles (~10-20MB for Hello World)
  - React frontend adds ~2MB
  - Target: <50MB for base app

- **D-13**: Cold start < 3 seconds
  - **Why:** Desktop apps should feel instantaneous
  - Tauri's Rust core starts fast
  - WebView loads cached React bundle

### Claude's Discretion

- Exact Rust crate versions for Tauri 2.x ecosystem
- Window state persistence implementation details
- Error handling patterns for Rust-JS bridge
- Logging configuration for debug builds

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Project overview, tech stack, constraints
- `.planning/STATE.md` — Current milestone and progress
- `.planning/REQUIREMENTS.md` — v3.3 requirements (APP-01~05, WIN-01~05)

### Existing Frontend
- `web/src/` — Existing React frontend
- `web/vite.config.ts` — Vite build configuration
- `web/package.json` — Frontend dependencies

### Tauri Documentation (to be researched)
- Tauri 2.x getting started guide
- Tauri Menu API
- Tauri SystemTray API
- Tauri Theme API
- Cross-platform build configuration

</canonical_refs>

<specifics>
## Specific Ideas

1. **Tauri project structure:**
   ```
   desktop/
   ├── src-tauri/
   │   ├── src/
   │   │   ├── main.rs
   │   │   ├── lib.rs
   │   │   ├── menu.rs
   │   │   ├── tray.rs
   │   │   └── theme.rs
   │   ├── Cargo.toml
   │   ├── tauri.conf.json
   │   └── icons/
   ├── package.json
   └── README.md
   ```

2. **Menu structure:**
   - File: New Wiki, Open Vault, Save, Export, Preferences, Quit
   - Edit: Undo, Redo, Cut, Copy, Paste
   - View: Toggle Sidebar, Toggle Dark Mode, Reload
   - Help: Documentation, Keyboard Shortcuts, About

3. **Tray menu:**
   - Show/Hide Window
   - Quick Ingest
   - Recent Wikis (submenu)
   - Quit

4. **Window configuration:**
   - Minimum size: 800x600
   - Default size: 1280x800
   - Resizable, maximizable, minimizable
   - Title bar with app name

</specifics>

<deferred>
## Deferred Ideas

- File system operations (Phase 22: FS-01~05)
- URL protocol handler saw:// (Phase 23: SYS-01)
- File association .md/.pdf (Phase 23: SYS-02)
- Auto-update mechanism (Phase 24: DIST-02)
- Python sidecar integration (Phase 25: BACK-01~05)
- System notifications (Phase 23: SYS-03)
- System search integration (Phase 23: SYS-04)

</deferred>

---

*Phase: 21-tauri-foundation*
*Context gathered: 2026-05-03*
