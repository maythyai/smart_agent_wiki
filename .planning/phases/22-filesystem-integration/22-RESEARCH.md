# Phase 22: File System Integration - Research

**Researched:** 2026-05-03
**Status:** Complete

## Crate Versions

### File System Watching

| Crate | Version | Purpose |
|-------|---------|---------|
| `notify` | 6.1.1 | Cross-platform filesystem watcher |
| `notify-types` | 1.0.0 | Event types for notify |

### Export Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| `horrorshow` | 0.8.4 | HTML template for PDF export (lightweight) |
| `printpdf` | 0.7.0 | PDF generation (alternative, more control) |

**Decision:** Use WebView print API for PDF export (D-22-09) - no additional Rust PDF dependencies needed.

## Tauri Plugin APIs

### tauri-plugin-fs (2.5.1) - Already installed

```rust
use tauri_plugin_fs::FsExt;

// Read file
let contents = app.fs().read_text(path)?;

// Write file
app.fs().write(path, contents)?;

// Check scope
app.fs().has_scope(&path)?;
```

**Scope configuration in capabilities:**
```json
{
  "fs": {
    "scope": {
      "allow": [{ "path": "$APPDATA/**" }],
      "deny": [{ "path": "$APPDATA/secret/**" }]
    }
  }
}
```

### tauri-plugin-dialog (2.7.1) - Already installed

```rust
use tauri_plugin_dialog::DialogExt;

// Open single file
let path = app.dialog().file().blocking_pick_file();

// Open multiple files
let paths = app.dialog().file().blocking_pick_files();

// Open folder
let path = app.dialog().directory().blocking_pick_folder();

// Save file dialog
let path = app.dialog().file().blocking_save_file();
```

### Tauri App Data Directory

```rust
use tauri::Manager;

// Get app data directory
let app_dir = app.path().app_data_dir()?;
// Returns: 
//   Windows: C:\Users\<user>\AppData\Roaming\com.smart-agent.wiki
//   macOS: ~/Library/Application Support/com.smart-agent.wiki
//   Linux: ~/.local/share/com.smart-agent.wiki

// Get app config directory
let config_dir = app.path().app_config_dir()?;

// Get app cache directory
let cache_dir = app.path().app_cache_dir()?;

// Get app log directory
let log_dir = app.path().app_log_dir()?;
```

## notify Crate Configuration

```rust
use notify::{Config, Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use std::path::Path;
use std::time::Duration;

// Create watcher with debounce
let (tx, rx) = std::sync::mpsc::channel();

let config = Config::default()
    .with_poll_interval(Duration::from_millis(100))
    .with_compare_contents(false);

let mut watcher = RecommendedWatcher::new(tx, config)?;

// Watch directory recursively
watcher.watch(Path::new("/path/to/watch"), RecursiveMode::Recursive)?;

// Handle events
for event in rx {
    match event.kind {
        EventKind::Create(_) => {
            // Emit to frontend: fs:file-created
        }
        EventKind::Modify(_) => {
            // Emit to frontend: fs:file-modified
        }
        EventKind::Remove(_) => {
            // Emit to frontend: fs:file-deleted
        }
        _ => {}
    }
}
```

**Key patterns:**
- Use `RecommendedWatcher` for platform-native watcher
- `RecursiveMode::Recursive` for deep folder watching
- Debounce with `poll_interval` config (100ms per D-22-05)
- Filter events by `EventKind`

## React Drag-Drop Integration

```tsx
import { invoke } from '@tauri-apps/api/core';

interface DropZoneProps {
  onIngestStart?: () => void;
  onIngestComplete?: (count: number) => void;
}

export const DropZone: React.FC<DropZoneProps> = ({ onIngestStart, onIngestComplete }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    // Extract file paths from DataTransfer
    const items = Array.from(e.dataTransfer.items);
    const files = items.filter(item => item.kind === 'file');
    
    if (files.length === 0) {
      console.warn('No files in drop event');
      return;
    }

    // Get paths (Tauri provides path property on File objects)
    const paths: string[] = files
      .map(item => item.getAsFile())
      .filter((f): f is File => f !== null)
      .map(f => (f as any).path)
      .filter((path): path is string => path !== undefined);

    if (paths.length > 0) {
      onIngestStart?.();
      try {
        const result = await invoke<{ count: number }>('fs:ingest-files', { paths });
        onIngestComplete?.(result.count);
      } catch (error) {
        console.error('Ingestion failed:', error);
      }
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={isDragging ? 'dropzone-active' : 'dropzone'}
    >
      {/* Drop zone UI */}
    </div>
  );
};
```

**Key patterns:**
- `e.dataTransfer.items` for file extraction
- `(f as any).path` to access Tauri-provided file path
- Visual feedback with `isDragging` state
- Error handling for IPC failures

## Export Implementation

### Markdown Export (Rust)

```rust
#[derive(serde::Serialize)]
pub struct ExportResult {
    path: String,
    pages_exported: usize,
}

#[tauri::command]
pub async fn export_wiki_markdown(
    app: AppHandle,
    page_ids: Vec<String>,
    output_dir: String,
) -> Result<ExportResult, String> {
    // Ensure output directory exists
    let output_path = PathBuf::from(&output_dir);
    std::fs::create_dir_all(&output_path).map_err(|e| e.to_string())?;

    // Fetch pages from backend API
    // Convert to Markdown format
    // Write files

    Ok(ExportResult {
        path: output_dir,
        pages_exported: page_ids.len(),
    })
}
```

### PDF Export (WebView Print)

```rust
#[tauri::command]
pub async fn export_wiki_pdf(
    app: AppHandle,
    page_id: String,
    output_path: String,
) -> Result<String, String> {
    // Generate HTML content
    let html = generate_page_html(page_id)?;

    // Open print window
    let window = WebviewWindowBuilder::new(
        &app,
        "print-window",
        WebviewUrl::External(html.into()),
    )
    .title("Print Preview")
    .build()?;

    // Trigger print dialog
    window.print()?;

    Ok(output_path)
}
```

## Capabilities Update

```json
{
  "fs": {
    "scope": {
      "allow": [
        { "path": "$APPDATA/**" },
        { "path": "$DOCUMENT/**" },
        { "path": "$HOME/**" }
      ],
      "deny": []
    }
  },
  "dialog": {
    "open": true,
    "save": true
  }
}
```

**Key points:**
- `$APPDATA/**` for app data directory
- `$DOCUMENT/**` for export target
- `$HOME/**` for user files (with explicit user selection)
- Dynamic scope via `dialog` selection

## App Data Directory Structure

```rust
use std::path::PathBuf;

pub fn setup_app_directories(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let app_data = app.path().app_data_dir()?;
    
    // Create subdirectories
    let dirs = ["vault", "preferences", "cache", "logs"];
    for dir in dirs {
        std::fs::create_dir_all(app_data.join(dir))?;
    }

    Ok(())
}
```

**Portable mode detection:**
```rust
pub fn get_data_dir(app: &AppHandle) -> PathBuf {
    // Check for portable marker
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()));
    
    if let Some(dir) = exe_dir {
        if dir.join("portable").exists() {
            return dir.join("data");
        }
    }

    // Default: system app data directory
    app.path().app_data_dir().expect("App data dir should exist")
}
```

## File Dialog IPC Commands

```rust
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
pub async fn select_files(app: AppHandle) -> Result<Vec<String>, String> {
    let paths = app.dialog()
        .file()
        .add_filter("Documents", &["md", "txt", "pdf", "docx", "html"])
        .blocking_pick_files();

    match paths {
        Some(paths) => Ok(paths.iter().map(|p| p.to_string()).collect()),
        None => Ok(vec![]),
    }
}

#[tauri::command]
pub async fn select_folder(app: AppHandle) -> Result<Option<String>, String> {
    let path = app.dialog()
        .directory()
        .blocking_pick_folder();

    match path {
        Some(path) => Ok(Some(path.to_string())),
        None => Ok(None),
    }
}

#[tauri::command]
pub async fn select_export_location(app: AppHandle, default_name: String) -> Result<Option<String>, String> {
    let path = app.dialog()
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
```

---

*Phase: 22-filesystem-integration*
*Research completed: 2026-05-03*