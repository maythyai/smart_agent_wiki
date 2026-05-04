// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod menu;
mod tray;
mod theme;
mod watcher;

use tauri::{Emitter, Manager};
use tauri_plugin_global_shortcut::GlobalShortcutExt;
use tauri_plugin_store::StoreExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            // Setup native menu bar
            let menu = menu::setup_menu(app)?;
            app.set_menu(menu)?;

            // Handle menu events - emit to frontend for processing
            app.on_menu_event(|app, event| {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.emit("menu-event", event.id.as_ref());
                }
            });

            // Setup system tray
            let _tray = tray::setup_tray(app)?;

            // Setup theme detection
            theme::setup_theme_listener(app.handle())?;

            // Setup file watcher state
            watcher::setup_watcher_state(app.handle());

            // Setup app directories
            commands::setup_app_directories(app.handle())?;

            // Setup global keyboard shortcuts
            setup_global_shortcuts(app)?;

            // Handle window close behavior based on preferences
            let window = app.get_webview_window("main")
                .expect("Main window should exist");
            let app_handle = app.handle().clone();

            window.on_window_event(move |event| {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    // Check preference for minimize-to-tray behavior
                    let should_minimize = app_handle.store("preferences.json")
                        .ok()
                        .and_then(|store| store.get("window_preferences"))
                        .and_then(|v| serde_json::from_value::<commands::WindowPreferences>(v.clone()).ok())
                        .map(|p| p.minimize_to_tray)
                        .unwrap_or(true);  // Default: minimize to tray

                    if should_minimize {
                        // Prevent the default close action
                        api.prevent_close();
                        // Hide the window instead
                        if let Some(win) = app_handle.get_webview_window("main") {
                            let _ = win.hide();
                        }
                    }
                    // If minimize_to_tray is false, let it close normally (app exits)
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_window_preferences,
            commands::set_window_preferences,
            theme::get_system_theme,
            commands::select_files,
            commands::select_folder,
            commands::select_export_location,
            commands::get_app_data_dir,
            commands::is_portable_mode,
            commands::add_watch_folder,
            commands::remove_watch_folder,
            commands::get_watched_folders,
            commands::update_watch_config,
            commands::get_export_default_dir,
            commands::export_wiki_markdown,
            commands::export_wiki_pdf,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// Setup global keyboard shortcuts per D-08.
///
/// Registered shortcuts:
/// - Cmd/Ctrl+N: New Wiki (emits "shortcut:new-wiki")
/// - Cmd/Ctrl+O: Open Vault (emits "shortcut:open-vault")
/// - Cmd/Ctrl+S: Save (emits "shortcut:save")
/// - Cmd/Ctrl+Q: Quit (exits app directly)
/// - Cmd/Ctrl+,: Preferences (emits "shortcut:preferences")
fn setup_global_shortcuts(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    use tauri_plugin_global_shortcut::{Shortcut, ShortcutEvent};

    let shortcuts = app.global_shortcut();

    // Define shortcuts with their handlers
    let new_wiki: Shortcut = "CmdOrCtrl+N".try_into()?;
    let open_vault: Shortcut = "CmdOrCtrl+O".try_into()?;
    let save: Shortcut = "CmdOrCtrl+S".try_into()?;
    let quit: Shortcut = "CmdOrCtrl+Q".try_into()?;
    let preferences: Shortcut = "CmdOrCtrl+,".try_into()?;

    // Register all shortcuts
    shortcuts.on_shortcut(new_wiki, |app, _shortcut, _event| {
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.emit("shortcut:new-wiki", ());
        }
    })?;

    shortcuts.on_shortcut(open_vault, |app, _shortcut, _event| {
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.emit("shortcut:open-vault", ());
        }
    })?;

    shortcuts.on_shortcut(save, |app, _shortcut, _event| {
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.emit("shortcut:save", ());
        }
    })?;

    shortcuts.on_shortcut(quit, |app, _shortcut, _event| {
        app.exit(0);
    })?;

    shortcuts.on_shortcut(preferences, |app, _shortcut, _event| {
        if let Some(window) = app.get_webview_window("main") {
            let _ = window.emit("shortcut:preferences", ());
        }
    })?;

    Ok(())
}