//! File system IPC commands for Smart Agent Wiki
//!
//! Provides native file dialogs, app data directory access, and portable mode detection.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::Manager;
use tauri_plugin_dialog::DialogExt;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum FsError {
    #[error("Dialog operation failed: {0}")]
    DialogError(String),
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

impl Serialize for FsError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WatchConfig {
    pub path: String,
    pub enabled: bool,
    pub file_types: Vec<String>,
}

/// Open native file dialog for selecting multiple documents.
///
/// Supported file types: .md, .txt, .pdf, .docx, .html
#[tauri::command]
pub async fn select_files(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    let paths = app
        .dialog()
        .file()
        .add_filter("Documents", &["md", "txt", "pdf", "docx", "html"])
        .blocking_pick_files();

    match paths {
        Some(paths) => Ok(paths.iter().map(|p| p.to_string()).collect()),
        None => Ok(vec![]),
    }
}

/// Open native folder dialog for selecting a directory.
#[tauri::command]
pub async fn select_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let path = app
        .dialog()
        .file()
        .blocking_pick_file();

    match path {
        Some(path) => Ok(Some(path.to_string())),
        None => Ok(None),
    }
}

/// Open save file dialog for export location selection.
#[tauri::command]
pub async fn select_export_location(
    app: tauri::AppHandle,
    default_name: String,
) -> Result<Option<String>, String> {
    let path = app
        .dialog()
        .file()
        .set_file_name(&default_name)
        .add_filter("Markdown", &["md"])
        .add_filter("PDF", &["pdf"])
        .blocking_save_file();

    match path {
        Some(path) => Ok(Some(path.to_string())),
        None => Ok(None),
    }
}

/// Get the app data directory path for user data storage.
///
/// Returns platform-specific standard location:
/// - Windows: `%APPDATA%/com.smart-agent.wiki/`
/// - macOS: `~/Library/Application Support/com.smart-agent.wiki/`
/// - Linux: `~/.local/share/com.smart-agent.wiki/`
#[tauri::command]
pub async fn get_app_data_dir(app: tauri::AppHandle) -> Result<String, String> {
    let app_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data directory: {}", e))?;

    Ok(app_dir.to_string_lossy().to_string())
}

/// Check if portable mode is enabled.
///
/// Portable mode is detected by presence of a `portable` file
/// next to the executable. When enabled, data is stored in
/// `./data/` instead of system app data directory.
#[tauri::command]
pub async fn is_portable_mode() -> Result<bool, String> {
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()));

    if let Some(dir) = exe_dir {
        if dir.join("portable").exists() {
            return Ok(true);
        }
    }

    Ok(false)
}

/// Setup app directories on first launch.
///
/// Creates standard subdirectories:
/// - vault/ - User content database
/// - preferences/ - App settings
/// - cache/ - Temporary data (thumbnails, index)
/// - logs/ - Application logs
pub fn setup_app_directories(app: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let app_data = get_data_dir(app)?;

    // Create subdirectories
    let dirs = ["vault", "preferences", "cache", "logs"];
    for dir in dirs {
        std::fs::create_dir_all(app_data.join(dir))?;
    }

    Ok(())
}

/// Get data directory, respecting portable mode.
pub fn get_data_dir(app: &tauri::AppHandle) -> Result<PathBuf, Box<dyn std::error::Error>> {
    // Check for portable marker
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()));

    if let Some(dir) = exe_dir {
        if dir.join("portable").exists() {
            return Ok(dir.join("data"));
        }
    }

    // Default: system app data directory
    Ok(app.path().app_data_dir()?)
}

// ============================================================================
// Folder Watcher Commands
// ============================================================================

/// Add a folder to the watch list.
///
/// Returns the list of currently watched folders after adding.
#[tauri::command]
pub async fn add_watch_folder(
    app: tauri::AppHandle,
    path: String,
    config: WatchConfig,
) -> Result<Vec<String>, String> {
    crate::watcher::start_watching(app.clone(), path, config.file_types)?;
    Ok(crate::watcher::get_watched_folders(&app))
}

/// Remove a folder from the watch list.
#[tauri::command]
pub async fn remove_watch_folder(app: tauri::AppHandle, path: String) -> Result<Vec<String>, String> {
    crate::watcher::stop_watching(&app, &path)?;
    Ok(crate::watcher::get_watched_folders(&app))
}

/// Get list of currently watched folders.
#[tauri::command]
pub async fn get_watched_folders(app: tauri::AppHandle) -> Result<Vec<String>, String> {
    Ok(crate::watcher::get_watched_folders(&app))
}

/// Update watch configuration for a folder.
#[tauri::command]
pub async fn update_watch_config(
    app: tauri::AppHandle,
    path: String,
    config: WatchConfig,
) -> Result<Vec<String>, String> {
    // Stop existing watcher and restart with new config
    let _ = crate::watcher::stop_watching(&app, &path);
    if config.enabled {
        crate::watcher::start_watching(app.clone(), path, config.file_types)?;
    }
    Ok(crate::watcher::get_watched_folders(&app))
}
