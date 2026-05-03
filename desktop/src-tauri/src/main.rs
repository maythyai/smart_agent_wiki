// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod menu;
mod tray;

use tauri::Manager;
use tauri_plugin_store::StoreExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_global_shortcut::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            // Setup native menu bar
            let menu = menu::setup_menu(app)?;
            app.set_menu(&menu)?;

            // Handle menu events - emit to frontend for processing
            app.on_menu_event(|app, event| {
                if let Some(window) = app.get_webview_window("main") {
                    let _ = window.emit("menu-event", event.id.as_ref());
                }
            });

            // Setup system tray
            let _tray = tray::setup_tray(app)?;

            // Handle window close behavior based on preferences
            let window = app.get_webview_window("main")
                .expect("Main window should exist");
            let app_handle = app.handle().clone();

            window.on_window_event(move |event| {
                if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                    // Check preference for minimize-to-tray behavior
                    let should_minimize = app_handle.store("preferences.json")
                        .ok()
                        .and_then(|store| store.get("window_preferences").cloned())
                        .and_then(|v| serde_json::from_value::<commands::WindowPreferences>(v).ok())
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
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}