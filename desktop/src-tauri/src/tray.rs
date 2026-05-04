//! System tray implementation for Smart Agent Wiki
//!
//! Provides a system tray icon with quick actions for show/hide window and quit.

use tauri::{
    menu::{Menu, MenuItemBuilder, PredefinedMenuItem},
    tray::{TrayIcon, TrayIconBuilder},
    App, Manager,
};

/// Setup the system tray icon with a context menu.
///
/// Returns the constructed tray icon for the application.
pub fn setup_tray(app: &App) -> Result<TrayIcon, Box<dyn std::error::Error>> {
    // Create tray menu items
    let show_item = MenuItemBuilder::with_id("tray_show", "Show Window")
        .enabled(true)
        .build(app)?;
    let hide_item = MenuItemBuilder::with_id("tray_hide", "Hide Window")
        .build(app)?;
    let quit_item = MenuItemBuilder::with_id("tray_quit", "Quit")
        .build(app)?;
    let separator = PredefinedMenuItem::separator(app)?;

    // Build the tray menu
    let tray_menu = Menu::new(app)?;
    tray_menu.append(&show_item)?;
    tray_menu.append(&hide_item)?;
    tray_menu.append(&separator)?;
    tray_menu.append(&quit_item)?;

    // Create the tray icon with the app's default window icon
    let tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&tray_menu)
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "tray_show" => {
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
                "tray_hide" => {
                    if let Some(window) = app.get_webview_window("main") {
                        let _ = window.hide();
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