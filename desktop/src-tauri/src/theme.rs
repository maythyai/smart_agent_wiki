//! Theme detection and application for Smart Agent Wiki
//!
//! Detects system theme preference and notifies the frontend via IPC events.
//! Per D-07: App follows system dark/light theme automatically.

use tauri::{AppHandle, Manager, WebviewWindow};

/// Get the current system theme.
///
/// Returns "dark" or "light" based on the OS theme preference.
/// Per WIN-04: Dark/light theme follows system setting.
#[tauri::command]
pub async fn get_system_theme(window: WebviewWindow) -> Result<String, String> {
    let theme = window
        .theme()
        .map_err(|e| format!("Failed to get theme: {}", e))?;

    let theme_str = match theme {
        tauri::Theme::Dark => "dark",
        tauri::Theme::Light => "light",
        _ => "light", // Default to light for unknown themes
    };

    Ok(theme_str.to_string())
}

/// Setup theme listener to emit theme changes to frontend.
///
/// This should be called during app setup to:
/// 1. Emit the initial theme on startup
/// 2. Listen for system theme changes and emit events
///
/// Events emitted:
/// - `theme-changed`: payload is `true` for dark, `false` for light
pub fn setup_theme_listener(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    // Emit initial theme
    if let Some(window) = app.get_webview_window("main") {
        if let Ok(theme) = window.theme() {
            let is_dark = matches!(theme, tauri::Theme::Dark);
            let _ = window.emit("theme-changed", is_dark);
        }
    }

    // Note: Tauri 2.x does not have a built-in theme change event listener.
    // The frontend useTheme hook uses CSS media query listener as a fallback
    // for detecting system theme changes in real-time.
    // On macOS, NSApplicationDidChangeEffectiveBackgroundColorNotification can be used.
    // On Windows, WM_SETTINGCHANGE can be monitored.
    // For cross-platform simplicity, we rely on the frontend's media query listener.

    Ok(())
}
