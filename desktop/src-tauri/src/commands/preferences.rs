//! Window preferences commands for Smart Agent Wiki
//!
//! Provides persistent storage for window behavior preferences using tauri-plugin-store.

use serde::{Deserialize, Serialize};
use tauri::AppHandle;
use tauri_plugin_store::StoreExt;

/// Window behavior preferences stored persistently.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowPreferences {
    /// Whether to minimize to tray instead of quitting on window close.
    pub minimize_to_tray: bool,
    /// UI theme preference: "system", "light", or "dark".
    pub theme: String,
}

impl Default for WindowPreferences {
    fn default() -> Self {
        Self {
            minimize_to_tray: true,  // Default: minimize to tray on close
            theme: "system".to_string(),
        }
    }
}

/// Get window preferences from persistent storage.
#[tauri::command]
pub async fn get_window_preferences(
    app: AppHandle,
) -> Result<WindowPreferences, String> {
    let store = app.store("preferences.json")
        .map_err(|e| e.to_string())?;

    let prefs = store.get("window_preferences")
        .and_then(|v| serde_json::from_value(v.clone()).ok())
        .unwrap_or_default();

    Ok(prefs)
}

/// Set window preferences in persistent storage.
#[tauri::command]
pub async fn set_window_preferences(
    app: AppHandle,
    prefs: WindowPreferences,
) -> Result<(), String> {
    let store = app.store("preferences.json")
        .map_err(|e| e.to_string())?;

    store.set("window_preferences", serde_json::to_value(prefs.clone()).unwrap());
    store.save().map_err(|e| e.to_string())?;

    Ok(())
}