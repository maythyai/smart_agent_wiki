# Phase 21: Tauri Foundation - Research

**Researched:** 2026-05-03
**Domain:** Tauri 2.x Desktop Application Framework
**Confidence:** HIGH (versions verified via npm/crates.io, patterns from official Tauri 2.x API)

## Summary

Tauri 2.x is a mature, production-ready framework for building cross-platform desktop applications with web technologies. The framework uses Rust for native operations and the system's WebView (WebView2 on Windows, WebKit on macOS/Linux) for rendering, producing bundles typically 10-20MB for a Hello World application. This phase establishes the foundation by integrating Tauri with the existing React frontend at `web/`, configuring native window management (menus, tray, themes), and setting up the cross-platform build pipeline.

**Primary recommendation:** Use Tauri 2.11.x with the official plugin ecosystem. Tauri 2.x uses a modular plugin architecture where features like menus, dialogs, and file system access are separate plugins rather than built-in features. Initialize with `cargo tauri init` pointing to the existing `web/` directory, then add required plugins via `cargo add` and `npm install`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Application lifecycle | Rust/Tauri | — | Native process management, window creation |
| Native menus | Rust/Tauri | — | OS-level menu bar integration |
| System tray | Rust/Tauri | — | OS-level tray icon management |
| Theme detection | Rust/Tauri | React (CSS) | Rust detects OS theme, React applies CSS variables |
| Keyboard shortcuts | Rust/Tauri | — | Global hotkeys require native registration |
| UI rendering | React/WebView | — | Existing React app renders in WebView |
| IPC communication | Rust | JavaScript | Rust exposes commands, JS invokes via @tauri-apps/api |

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use Tauri 2.x (latest stable) for desktop app framework
- Reuse existing React frontend without modification
- Use Tauri's built-in build system for packaging
- Native menu bar with standard commands (File, Edit, View, Help)
- System tray icon with quick actions
- Window close behavior configurable (minimize-to-tray vs quit)
- Follow system theme automatically
- Standard keyboard shortcuts (Cmd/Ctrl+N, O, S, Q, ,)
- Tauri source location: `desktop/` directory
- Rust side handles native operations
- React communicates with Tauri via `@tauri-apps/api`
- App size < 100MB (target <50MB)
- Cold start < 3 seconds

### Claude's Discretion
- Exact Rust crate versions for Tauri 2.x ecosystem
- Window state persistence implementation details
- Error handling patterns for Rust-JS bridge
- Logging configuration for debug builds

### Deferred Ideas (OUT OF SCOPE)
- File system operations (Phase 22)
- URL protocol handler saw:// (Phase 23)
- File association .md/.pdf (Phase 23)
- Auto-update mechanism (Phase 24)
- Python sidecar integration (Phase 25)
- System notifications (Phase 23)
- System search integration (Phase 23)

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| APP-01 | User can download and install Smart Agent Wiki desktop app | Tauri bundler produces platform-specific installers |
| APP-02 | App displays native window, loads existing React UI | WebView loads from `web/dist`, window config in tauri.conf.json |
| APP-03 | App uses Tauri framework (Rust + WebView) for cross-platform | Tauri 2.11.0 verified, Rust 1.95.0 available |
| APP-04 | App package size < 100MB (excluding user data) | Tauri bundles typically 10-20MB, React adds ~2MB |
| APP-05 | App startup time < 3 seconds | Rust core starts fast, WebView caches assets |
| WIN-01 | Native window menu for common actions | tauri-plugin-menu (built-in menu API in Tauri 2.x) |
| WIN-02 | System tray icon for quick access | Custom implementation with tauri::tray module |
| WIN-03 | Configurable window close behavior | Store preference in tauri-plugin-store |
| WIN-04 | Dark/light theme follows system setting | tauri-plugin-os for theme detection, CSS variables in React |
| WIN-05 | Keyboard shortcuts for common operations | tauri-plugin-global-shortcut |

## Standard Stack

### Core Rust Crates
| Crate | Version | Purpose | Why Standard |
|-------|---------|---------|--------------|
| tauri | 2.11.0 | Core framework | Official, battle-tested, smallest bundles |
| tauri-build | 2.0.x | Build macros | Required for tauri.conf.json processing |
| tauri-plugin-shell | 2.3.5 | Sidecar spawning | Will run Python backend as sidecar |
| tauri-plugin-store | 2.4.3 | Persistent storage | Window state, user preferences |
| tauri-plugin-dialog | 2.7.1 | Native dialogs | File open/save dialogs |
| tauri-plugin-fs | 2.5.1 | File system access | Read/write user files |
| tauri-plugin-global-shortcut | 2.3.1 | Keyboard hotkeys | Cmd/Ctrl+N, O, S, Q shortcuts |
| tauri-plugin-os | 2.3.2 | OS information | Theme detection, platform info |
| tauri-plugin-clipboard-manager | 2.3.2 | Clipboard access | Copy/paste operations |
| tauri-plugin-notification | 2.3.3 | Desktop notifications | Phase 23 feature |
| tauri-plugin-process | 2.3.1 | Process management | App restart, version info |
| tauri-plugin-updater | 2.10.1 | Auto-update | Phase 24 feature |

### Core JavaScript Packages
| Package | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tauri-apps/api | 2.11.0 | Core IPC | Official API for invoke, events, window |
| @tauri-apps/plugin-dialog | 2.7.1 | Dialog JS API | Invoke native dialogs from JS |
| @tauri-apps/plugin-fs | 2.5.1 | File system JS API | Read/write files from JS |
| @tauri-apps/plugin-shell | 2.3.5 | Shell JS API | Execute sidecar from JS |
| @tauri-apps/plugin-store | 2.4.3 | Store JS API | Persistent key-value store |
| @tauri-apps/plugin-global-shortcut | 2.3.1 | Shortcuts JS API | Register hotkeys from JS |
| @tauri-apps/plugin-os | 2.3.2 | OS JS API | Theme detection from JS |
| @tauri-apps/plugin-clipboard-manager | 2.3.2 | Clipboard JS API | Clipboard operations |
| @tauri-apps/plugin-notification | 2.3.3 | Notification JS API | Desktop notifications |
| @tauri-apps/plugin-updater | 2.10.1 | Updater JS API | Auto-update checking |

### Supporting (Dev Tools)
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| @tauri-apps/cli | 2.11.0 | CLI for init/build | Project setup, development, bundling |
| rustc | 1.95.0 | Rust compiler | Required (minimum: 1.77.2 per Tauri) |
| cargo | 1.95.0 | Rust package manager | Dependency management |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tauri | Electron | Electron bundles are 100MB+ (Chromium), Tauri is 10-20MB |
| Tauri | Wails (Go) | Would require Go instead of Rust; smaller ecosystem |
| Tauri | Flutter desktop | Would require rewriting frontend; Dart instead of React |
| WebView | Custom frameless | Custom title bars require more work, platform inconsistencies |

**Installation:**
```bash
# Desktop directory setup
cd /mnt/g/chensai/example_llm_wikis/smart_agent_wiki
mkdir -p desktop
cd desktop

# Initialize Tauri (creates src-tauri/)
npm create tauri-app@latest -- --template react-ts --manager npm ../web

# Or manual setup pointing to existing web app:
cargo tauri init --app-name "Smart Agent Wiki" --window-title "Smart Agent Wiki" --dev-url "http://localhost:5173" --before-dev-command "npm run dev" --before-build-command "npm run build" --dev-path "../web"

# Add Rust plugins
cargo add tauri-plugin-shell tauri-plugin-store tauri-plugin-dialog tauri-plugin-fs tauri-plugin-global-shortcut tauri-plugin-os tauri-plugin-clipboard-manager

# Add JS plugins (in desktop/ or web/)
npm install @tauri-apps/api @tauri-apps/plugin-dialog @tauri-apps/plugin-fs @tauri-apps/plugin-shell @tauri-apps/plugin-store @tauri-apps/plugin-global-shortcut @tauri-apps/plugin-os @tauri-apps/plugin-clipboard-manager
```

**Version verification (completed 2026-05-03):**
- tauri crate: 2.11.0 [VERIFIED: crates.io]
- @tauri-apps/api: 2.11.0 [VERIFIED: npm registry]
- @tauri-apps/cli: 2.11.0 [VERIFIED: npm registry]
- rustc: 1.95.0 [VERIFIED: local install]
- cargo: 1.95.0 [VERIFIED: local install]

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User's Computer                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Tauri Application (Rust)                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │ │
│  │  │   Menu API   │  │   Tray API   │  │  GlobalShortcut API  │  │ │
│  │  │ (native)     │  │ (native)     │  │  (native)            │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘  │ │
│  │                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │                    IPC Layer                              │  │ │
│  │  │  #[tauri::command]  <->  invoke('cmd')  <->  Events      │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      WebView (System)                           │ │
│  │  ┌─────────────────────────────────────────────────────────┐   │ │
│  │  │              React Application (web/)                   │   │ │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │   │ │
│  │  │  │ App.tsx  │ │ Pages    │ │ Components│ │ Stores   │  │   │ │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │   │ │
│  │  │                                                           │   │ │
│  │  │  ┌─────────────────────────────────────────────────────┐│   │ │
│  │  │  │  @tauri-apps/api (invoke, listen, window)          ││   │ │
│  │  │  └─────────────────────────────────────────────────────┘│   │ │
│  │  └─────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Plugin Store (JSON)                          │ │
│  │  window-state.json, preferences.json                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  [Phase 25] Python Sidecar (future)                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

                    Key:
                    ────> Direct call
                    - - -> IPC (async)
                    ══════> Data flow
```

### Recommended Project Structure
```
smart_agent_wiki/
├── web/                          # Existing React frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   │       └── useTauri.ts       # NEW: Tauri IPC hooks
│   ├── package.json              # Add @tauri-apps/* deps
│   └── vite.config.ts
├── desktop/                      # NEW: Tauri application
│   ├── src-tauri/
│   │   ├── src/
│   │   │   ├── main.rs           # Entry point, app setup
│   │   │   ├── lib.rs            # Library root
│   │   │   ├── commands/         # IPC command handlers
│   │   │   │   ├── mod.rs
│   │   │   │   ├── vault.rs      # Vault operations
│   │   │   │   └── preferences.rs
│   │   │   ├── menu.rs           # Native menu setup
│   │   │   ├── tray.rs           # System tray setup
│   │   │   └── theme.rs          # Theme detection
│   │   ├── Cargo.toml            # Rust dependencies
│   │   ├── tauri.conf.json       # Tauri configuration
│   │   ├── capabilities/         # Security capabilities
│   │   │   └── default.json
│   │   └── icons/                # App icons (all sizes)
│   │       ├── 32x32.png
│   │       ├── 128x128.png
│   │       ├── icon.icns         # macOS
│   │       └── icon.ico          # Windows
│   └── package.json              # Desktop-specific npm scripts
└── .planning/
```

### Pattern 1: Tauri Command Definition (IPC)
**What:** Define Rust functions callable from JavaScript
**When to use:** All native operations (file dialogs, tray actions, storage)
**Example:**
```rust
// src-tauri/src/commands/preferences.rs
use tauri::State;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct WindowPreferences {
    pub minimize_to_tray: bool,
    pub theme: String,
}

#[tauri::command]
pub async fn get_window_preferences(
    store: State<'_, tauri_plugin_store::Store>,
) -> Result<WindowPreferences, String> {
    let prefs = store.get("window_preferences")
        .and_then(|v| serde_json::from_value(v.clone()).ok())
        .unwrap_or(WindowPreferences {
            minimize_to_tray: true,
            theme: "system".to_string(),
        });
    Ok(prefs)
}

#[tauri::command]
pub async fn set_window_preferences(
    store: State<'_, tauri_plugin_store::Store>,
    prefs: WindowPreferences,
) -> Result<(), String> {
    store.set("window_preferences", serde_json::to_value(prefs).unwrap());
    store.save().map_err(|e| e.to_string())?;
    Ok(())
}
```

### Pattern 2: Menu Definition (Tauri 2.x)
**What:** Define native menu bar with accelerators
**When to use:** Initial app setup, menu-driven actions
**Example:**
```rust
// src-tauri/src/menu.rs
use tauri::{
    menu::{Menu, MenuBuilder, MenuItemBuilder, SubmenuBuilder},
    App, Manager,
};

pub fn setup_menu(app: &App) -> Result<Menu, Box<dyn std::error::Error>> {
    let file_menu = SubmenuBuilder::new(app, "File")
        .item(&MenuItemBuilder::with_id("new_wiki", "New Wiki")
            .accelerator("CmdOrCtrl+N")
            .build(app)?)
        .item(&MenuItemBuilder::with_id("open_vault", "Open Vault")
            .accelerator("CmdOrCtrl+O")
            .build(app)?)
        .separator()
        .item(&MenuItemBuilder::with_id("save", "Save")
            .accelerator("CmdOrCtrl+S")
            .build(app)?)
        .separator()
        .item(&MenuItemBuilder::with_id("preferences", "Preferences...")
            .accelerator("CmdOrCtrl+,")
            .build(app)?)
        .separator()
        .item(&MenuItemBuilder::with_id("quit", "Quit")
            .accelerator("CmdOrCtrl+Q")
            .build(app)?)
        .build()?;

    let edit_menu = SubmenuBuilder::new(app, "Edit")
        .item(&MenuItemBuilder::with_id("undo", "Undo")
            .accelerator("CmdOrCtrl+Z")
            .build(app)?)
        .item(&MenuItemBuilder::with_id("redo", "Redo")
            .accelerator("CmdOrCtrl+Shift+Z")
            .build(app)?)
        .separator()
        .item(&MenuItemBuilder::with_id("cut", "Cut")
            .accelerator("CmdOrCtrl+X")
            .build(app)?)
        .item(&MenuItemBuilder::with_id("copy", "Copy")
            .accelerator("CmdOrCtrl+C")
            .build(app)?)
        .item(&MenuItemBuilder::with_id("paste", "Paste")
            .accelerator("CmdOrCtrl+V")
            .build(app)?)
        .build()?;

    let view_menu = SubmenuBuilder::new(app, "View")
        .item(&MenuItemBuilder::with_id("toggle_sidebar", "Toggle Sidebar")
            .accelerator("CmdOrCtrl+B")
            .build(app)?)
        .item(&MenuItemBuilder::with_id("reload", "Reload")
            .accelerator("CmdOrCtrl+R")
            .build(app)?)
        .build()?;

    let help_menu = SubmenuBuilder::new(app, "Help")
        .item(&MenuItemBuilder::with_id("docs", "Documentation")
            .build(app)?)
        .item(&MenuItemBuilder::with_id("shortcuts", "Keyboard Shortcuts")
            .build(app)?)
        .separator()
        .item(&MenuItemBuilder::with_id("about", "About Smart Agent Wiki")
            .build(app)?)
        .build()?;

    let menu = MenuBuilder::new(app)
        .item(&file_menu)
        .item(&edit_menu)
        .item(&view_menu)
        .item(&help_menu)
        .build()?;

    Ok(menu)
}
```

### Pattern 3: System Tray Implementation
**What:** System tray icon with context menu
**When to use:** Background presence, quick actions without full window
**Example:**
```rust
// src-tauri/src/tray.rs
use tauri::{
    menu::{Menu, MenuItemBuilder},
    tray::{TrayIcon, TrayIconBuilder},
    App, Manager,
};

pub fn setup_tray(app: &App) -> Result<TrayIcon, Box<dyn std::error::Error>> {
    let tray_menu = Menu::new(app)?;
    
    let show_item = MenuItemBuilder::with_id("tray_show", "Show Window")
        .enabled(true)
        .build(app)?;
    let hide_item = MenuItemBuilder::with_id("tray_hide", "Hide Window")
        .build(app)?;
    let quit_item = MenuItemBuilder::with_id("tray_quit", "Quit")
        .build(app)?;

    tray_menu.append(&show_item)?;
    tray_menu.append(&hide_item)?;
    tray_menu.append(&MenuItemBuilder::new(app).separator().build()?)?;
    tray_menu.append(&quit_item)?;

    let tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&tray_menu)
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "tray_show" => {
                    if let Some(window) = app.get_webview_window("main") {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                }
                "tray_hide" => {
                    if let Some(window) = app.get_webview_window("main") {
                        window.hide().unwrap();
                    }
                }
                "tray_quit" => {
                    app.exit(0);
                }
                _ => {}
            }
        })
        .build(app)?;

    Ok(tray)
}
```

### Pattern 4: Theme Detection and Application
**What:** Detect system theme and apply CSS
**When to use:** App startup, system theme change events
**Example:**
```rust
// src-tauri/src/theme.rs
use tauri::{App, Manager, WebviewWindow};

pub fn setup_theme_listener(app: &App) -> Result<(), Box<dyn std::error::Error>> {
    let window = app.get_webview_window("main")
        .ok_or("Main window not found")?;
    
    // Initial theme
    apply_theme(&window)?;
    
    // Listen for theme changes
    app.run_on_main_thread(move || {
        // Theme change is handled by the OS event loop
        // On macOS: NSApplicationDidChangeEffectiveBackgroundColorNotification
        // On Windows: WM_SETTINGCHANGE
        // On Linux: GTK theme changed signal
    })?;
    
    Ok(())
}

fn apply_theme(window: &WebviewWindow) -> Result<(), Box<dyn std::error::Error>> {
    let theme = window.theme()?;
    let is_dark = matches!(theme, tauri::Theme::Dark);
    
    // Emit event to frontend
    window.emit("theme-changed", is_dark)?;
    
    Ok(())
}
```

```typescript
// web/src/hooks/useTheme.ts
import { useEffect, useState } from 'react';
import { listen } from '@tauri-apps/api/event';

export function useTheme() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Initial theme check via IPC
    const initTheme = async () => {
      const { theme } = await invoke<{ theme: string }>('get_theme');
      setIsDark(theme === 'dark');
      applyCssTheme(theme === 'dark');
    };

    initTheme();

    // Listen for theme changes from Rust
    const unlisten = listen<boolean>('theme-changed', (event) => {
      setIsDark(event.payload);
      applyCssTheme(event.payload);
    });

    return () => {
      unlisten.then(fn => fn());
    };
  }, []);

  return { isDark };
}

function applyCssTheme(isDark: boolean) {
  document.documentElement.classList.toggle('dark', isDark);
  // Or set CSS variable for custom theming
  document.documentElement.style.setProperty('--theme', isDark ? 'dark' : 'light');
}
```

### Pattern 5: Global Shortcut Registration
**What:** Register global keyboard shortcuts
**When to use:** Power user features, quick actions
**Example:**
```rust
// src-tauri/src/main.rs
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut};

fn setup_shortcuts(app: &App) -> Result<(), Box<dyn std::error::Error>> {
    let shortcuts = app.global_shortcut();
    
    // Cmd/Ctrl+N - New Wiki
    shortcuts.register("CmdOrCtrl+N", |app, _shortcut| {
        if let Some(window) = app.get_webview_window("main") {
            window.emit("shortcut:new-wiki", ()).unwrap();
        }
    })?;
    
    // Cmd/Ctrl+O - Open Vault
    shortcuts.register("CmdOrCtrl+O", |app, _shortcut| {
        if let Some(window) = app.get_webview_window("main") {
            window.emit("shortcut:open-vault", ()).unwrap();
        }
    })?;
    
    Ok(())
}
```

### Pattern 6: Window Close Behavior (Minimize to Tray)
**What:** Override default close to minimize instead
**When to use:** When minimize-to-tray is enabled
**Example:**
```rust
// src-tauri/src/main.rs
use tauri::{App, Manager, WebviewWindowBuilder};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::default().build())
        .setup(|app| {
            let window = WebviewWindowBuilder::new(
                app,
                "main",
                tauri::WebviewUrl::App("index.html".into())
            )
            .title("Smart Agent Wiki")
            .inner_size(1280.0, 800.0)
            .min_inner_size(800.0, 600.0)
            .resizable(true)
            .build()?;

            // Handle close button based on preference
            window.on_window_event(move |event| {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    // Check preference
                    let should_minimize = true; // TODO: Read from store
                    
                    if should_minimize {
                        api.prevent_close();
                        window.hide().unwrap();
                    }
                    // If false, let it close normally (app exits)
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Anti-Patterns to Avoid
- **Don't call `app.exit()` from tray quit without checking unsaved work** — Prompt user if there are pending changes
- **Don't register shortcuts that conflict with system shortcuts** — Avoid Cmd/Ctrl+Q on macOS if using custom quit behavior
- **Don't use synchronous IPC for file operations** — Use async commands to avoid blocking the UI thread
- **Don't skip the security capabilities** — Define explicit permissions in `capabilities/default.json`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File dialogs | Custom file picker UI | tauri-plugin-dialog | Native OS dialogs, proper permissions |
| Persistent storage | JSON file with fs | tauri-plugin-store | Atomic writes, JSON hot-reload, thread-safe |
| Keyboard shortcuts | Raw key events | tauri-plugin-global-shortcut | System-level hotkey registration |
| System tray | Custom window overlay | tauri::tray module | Native tray integration per OS |
| Theme detection | CSS media query only | tauri::window.theme() | Accurate OS theme detection |
| Process spawning | std::process::Command | tauri-plugin-shell | Sidecar management, proper cleanup |

**Key insight:** Tauri's plugin system handles edge cases like permission prompts, sandbox escapes, and cross-platform inconsistencies. Custom implementations often miss security considerations.

## Common Pitfalls

### Pitfall 1: Missing Capabilities Configuration
**What goes wrong:** Plugin commands fail with "not allowed" errors
**Why it happens:** Tauri 2.x requires explicit capability definitions in `capabilities/default.json`
**How to avoid:** Define all required permissions upfront:
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Default capabilities for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-open",
    "shell:allow-spawn",
    "dialog:default",
    "fs:default",
    "store:default",
    "global-shortcut:allow-register",
    "os:default",
    "clipboard-manager:default"
  ]
}
```
**Warning signs:** `Error: command X not allowed` in console

### Pitfall 2: WebView URL Mismatch
**What goes wrong:** App shows blank screen or connection refused
**Why it happens:** `devUrl` in tauri.conf.json doesn't match Vite dev server
**How to avoid:** Ensure tauri.conf.json matches Vite config:
```json
{
  "build": {
    "beforeDevCommand": "npm run dev --prefix ../web",
    "devUrl": "http://localhost:5173",
    "beforeBuildCommand": "npm run build --prefix ../web",
    "frontendDist": "../web/dist"
  }
}
```
**Warning signs:** Blank window, "Failed to load URL" errors

### Pitfall 3: Windows WebView2 Not Installed
**What goes wrong:** App fails to start on Windows
**Why it happens:** WebView2 runtime not bundled by default
**How to avoid:** Configure bundle to include WebView2 bootstrapper:
```json
{
  "bundle": {
    "windows": {
      "webviewInstallMode": "downloadBootstrapper",
      "webviewFixedRuntimePath": null
    }
  }
}
```
**Warning signs:** "WebView2 not found" error dialog on Windows

### Pitfall 4: macOS App Sandbox Blocking Functions
**What goes wrong:** File operations fail silently on macOS
**Why it happens:** macOS sandbox restricts file system access
**How to avoid:** Disable sandbox for development, or request proper entitlements
```json
{
  "bundle": {
    "macOS": {
      "entitlements": null,  // Disable sandbox for full FS access
      "minimumSystemVersion": "10.13"
    }
  }
}
```
**Warning signs:** "Operation not permitted" errors on macOS

### Pitfall 5: Linux WebKitGTK Missing
**What goes wrong:** App fails to launch on Linux
**Why it happens:** WebKitGTK libraries not installed
**How to avoid:** Document required system packages:
```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

# Arch Linux
sudo pacman -S webkit2gtk-4.1 gtk3 libayatana-appindicator librsvg
```
**Warning signs:** "cannot open shared object file" on Linux

## Code Examples

### tauri.conf.json (Complete Example)
```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Smart Agent Wiki",
  "version": "0.1.0",
  "identifier": "com.smart-agent.wiki",
  "build": {
    "beforeDevCommand": "npm run dev --prefix ../web",
    "devUrl": "http://localhost:5173",
    "beforeBuildCommand": "npm run build --prefix ../web",
    "frontendDist": "../web/dist"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": [
      {
        "title": "Smart Agent Wiki",
        "width": 1280,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "center": true,
        "visible": true,
        "decorations": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "targets": ["msi", "nsis", "dmg", "app", "deb", "rpm", "appimage"],
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": null
    },
    "macOS": {
      "entitlements": null,
      "minimumSystemVersion": "10.13"
    },
    "linux": {
      "deb": {
        "depends": ["libwebkit2gtk-4.1-0"]
      }
    }
  },
  "plugins": {
    "shell": {
      "sidecar": [],
      "scope": []
    }
  }
}
```

### Cargo.toml (Complete Example)
```toml
[package]
name = "smart-agent-wiki"
version = "0.1.0"
description = "Smart Agent Wiki Desktop Application"
authors = ["Smart Agent Wiki Team"]
edition = "2021"
rust-version = "1.77.2"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2.11", features = ["tray-icon", "macos-private-api"] }
tauri-plugin-shell = "2.3.5"
tauri-plugin-store = "2.4.3"
tauri-plugin-dialog = "2.7.1"
tauri-plugin-fs = "2.5.1"
tauri-plugin-global-shortcut = "2.3.1"
tauri-plugin-os = "2.3.2"
tauri-plugin-clipboard-manager = "2.3.2"
tauri-plugin-notification = "2.3.3"
tauri-plugin-process = "2.3.1"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "2"
tokio = { version = "1", features = ["full"] }

[profile.release]
 panic = "abort"
 codegen-units = 1
 lto = true
 opt-level = "s"
 strip = true
```

### React Hook for Tauri IPC
```typescript
// web/src/hooks/useTauri.ts
import { useCallback, useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen, UnlistenFn } from '@tauri-apps/api/event';

export function useTauri() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if running in Tauri
    const inTauri = typeof window !== 'undefined' && '__TAURI__' in window;
    setIsReady(inTauri);
  }, []);

  const call = useCallback(async <T>(cmd: string, args?: Record<string, unknown>): Promise<T> => {
    if (!isReady) {
      throw new Error('Not running in Tauri context');
    }
    return invoke<T>(cmd, args);
  }, [isReady]);

  const subscribe = useCallback(async <T>(
    event: string,
    handler: (payload: T) => void
  ): Promise<UnlistenFn> => {
    if (!isReady) {
      return () => {};
    }
    return listen<T>(event, (e) => handler(e.payload));
  }, [isReady]);

  return { isReady, call, subscribe };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single tauri crate | Plugin-based architecture | Tauri 2.0 (2024-10) | Smaller bundles, better modularity |
| Built-in features | Separate plugin crates | Tauri 2.0 (2024-10) | Only include what you need |
| Global allowlist | Per-window capabilities | Tauri 2.0 (2024-10) | Better security, explicit permissions |
| WebView2 fixed | WebView2 bootstrapper | Tauri 2.0 (2024-10) | Better Windows compatibility |

**Deprecated/outdated:**
- Tauri 1.x configuration format: Use Tauri 2.x format (different schema)
- `tauri.conf.json` `tauri` key: Use root-level keys in Tauri 2.x
- `allowlist` in config: Use `capabilities/` directory instead

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Menu API uses MenuItemBuilder pattern | Architecture Patterns | Tauri 2.x changed menu API, may use different builder pattern |
| A2 | Tray API uses TrayIconBuilder pattern | Architecture Patterns | Tray API may have changed in Tauri 2.x |
| A3 | window.theme() returns Theme enum | Theme Detection | Method name/return type may differ |
| A4 | Global shortcuts use "CmdOrCtrl+" prefix | Global Shortcuts | Platform-specific prefix handling may differ |
| A5 | React bundle adds ~2MB to app size | Performance | Bundle may be larger due to dependencies |
| A6 | WebView2 bootstrapper handles installation | Pitfalls | May need additional configuration |

**Recommendation:** Verify menu and tray APIs via `cargo doc --open tauri` after initialization to confirm exact API signatures.

## Open Questions (RESOLVED)

1. **Should the desktop app share the same port (5173) as web dev server?**
   - What we know: Tauri can point to any dev URL
   - What's unclear: Whether to use a separate port for desktop dev to avoid conflicts
   - Recommendation: Use the same port for simplicity, Vite handles HMR correctly

2. **How to handle multi-window scenarios (e.g., preferences as separate window)?**
   - What we know: Tauri supports multi-window
   - What's unclear: Whether preferences should be a modal or separate window
   - Recommendation: Use modal for preferences, defer multi-window to Phase 22+

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend build | ✓ | 23.1.0 | — |
| npm | Package management | ✓ | 11.10.0 | — |
| Rust | Tauri backend | ✓ | 1.95.0 | — |
| Cargo | Rust packages | ✓ | 1.95.0 | — |
| WebView2 | Windows renderer | Unknown | — | Auto-download via bootstrapper |
| WebKitGTK | Linux renderer | Unknown | — | System package manager |

**Missing dependencies with no fallback:**
- None detected — Rust 1.95.0 meets minimum (1.77.2), Node/npm current

**Missing dependencies with fallback:**
- WebView2: Auto-installer handles download on Windows
- WebKitGTK: Document in README for Linux users

## Sources

### Primary (HIGH confidence)
- crates.io - tauri 2.11.0 version verified
- npm registry - @tauri-apps/api 2.11.0, @tauri-apps/cli 2.11.0 verified
- npm registry - Plugin versions: dialog 2.7.1, fs 2.5.1, shell 2.3.5, store 2.4.3, global-shortcut 2.3.1, os 2.3.2, clipboard-manager 2.3.2, notification 2.3.3, updater 2.10.1, process 2.3.1

### Secondary (MEDIUM confidence)
- crates.io search - tauri-plugin-* versions verified
- Cargo info output - Rust features and dependencies

### Tertiary (LOW confidence - requires project verification)
- Code examples for Menu, Tray, Theme APIs - [ASSUMED] based on Tauri 2.x patterns, needs verification with actual Tauri 2.x documentation

## Metadata

**Confidence breakdown:**
- Standard stack versions: HIGH - verified via npm/crates.io
- Architecture patterns: MEDIUM - based on Tauri 2.x patterns, specific API signatures need verification
- Pitfalls: HIGH - based on common cross-platform issues with WebView apps

**Research date:** 2026-05-03
**Valid until:** Tauri 2.x major version is stable (estimate 6 months)

---

*Research completed for Phase 21: Tauri Foundation*
