//! File system watcher for Smart Agent Wiki
//!
//! Monitors folders for file changes and emits events to the frontend.

use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use std::collections::HashMap;
use std::path::Path;
use std::sync::Mutex;
use std::time::Duration;
use tauri::{AppHandle, Emitter, Manager};

/// Active file watchers indexed by path
pub type Watchers = Mutex<HashMap<String, RecommendedWatcher>>;

/// Setup file watcher state in the app
pub fn setup_watcher_state(app: &AppHandle) {
    app.manage(Watchers::default());
}

/// Start watching a folder for file changes.
///
/// Emits events to frontend:
/// - `fs:file-created` when new files are detected
/// - `fs:file-modified` when files are modified
/// - `fs:file-deleted` when files are deleted
pub fn start_watching(
    app: AppHandle,
    path: String,
    file_types: Vec<String>,
) -> Result<(), String> {
    let watchers = app
        .try_state::<Watchers>()
        .ok_or("Watcher state not initialized")?;

    let config = Config::default()
        .with_poll_interval(Duration::from_millis(100))
        .with_compare_contents(false);

    let app_handle = app.clone();
    let types = file_types.clone();

    let mut watcher = RecommendedWatcher::new(
        move |result: Result<Event, notify::Error>| {
            if let Ok(event) = result {
                if let Some(path) = event.paths.first() {
                    // Filter by file type if specified
                    if !types.is_empty() {
                        let ext = path.extension().and_then(|e| e.to_str());
                        if let Some(ext) = ext {
                            if !types.contains(&ext.to_string()) {
                                return;
                            }
                        }
                    }

                    let path_str = path.to_string_lossy().to_string();
                    let _ = match event.kind {
                        EventKind::Create(_) => {
                            app_handle.emit("fs:file-created", &path_str)
                        }
                        EventKind::Modify(_) => {
                            app_handle.emit("fs:file-modified", &path_str)
                        }
                        EventKind::Remove(_) => {
                            app_handle.emit("fs:file-deleted", &path_str)
                        }
                        _ => Ok(()),
                    };
                }
            }
        },
        config,
    )
    .map_err(|e| format!("Failed to create watcher: {}", e))?;

    watcher
        .watch(Path::new(&path), RecursiveMode::Recursive)
        .map_err(|e| format!("Failed to start watching: {}", e))?;

    let mut watchers = watchers.lock().unwrap();
    watchers.insert(path.clone(), watcher);

    Ok(())
}

/// Stop watching a folder.
pub fn stop_watching(app: &AppHandle, path: &str) -> Result<(), String> {
    let watchers = app
        .try_state::<Watchers>()
        .ok_or("Watcher state not initialized")?;

    let mut watchers = watchers.lock().unwrap();
    if watchers.remove(path).is_some() {
        Ok(())
    } else {
        Err(format!("Not watching path: {}", path))
    }
}

/// Get list of currently watched folders.
pub fn get_watched_folders(app: &AppHandle) -> Vec<String> {
    let watchers = app.try_state::<Watchers>();

    match watchers {
        Some(watchers) => {
            let watchers = watchers.lock().unwrap();
            watchers.keys().cloned().collect()
        }
        None => vec![],
    }
}
