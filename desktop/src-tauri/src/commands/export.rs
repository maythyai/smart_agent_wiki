//! Export IPC commands for Smart Agent Wiki
//!
//! Provides wiki page export to Markdown and PDF formats.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::Manager;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ExportError {
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    #[error("Export failed: {0}")]
    ExportFailed(String),
}

impl Serialize for ExportError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum ExportFormat {
    Markdown,
    PDF,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExportResult {
    pub path: String,
    pub pages_exported: usize,
    pub errors: Vec<String>,
}

/// Get the default export directory.
///
/// Returns ~/Documents/Smart Agent Wiki/Exports/ or platform equivalent.
#[tauri::command]
pub async fn get_export_default_dir(app: tauri::AppHandle) -> Result<String, String> {
    let documents_dir = app
        .path()
        .document_dir()
        .map_err(|e| format!("Failed to get documents directory: {}", e))?;

    let export_dir = documents_dir.join("Smart Agent Wiki").join("Exports");
    std::fs::create_dir_all(&export_dir)
        .map_err(|e| format!("Failed to create export directory: {}", e))?;

    Ok(export_dir.to_string_lossy().to_string())
}

/// Export wiki pages as Markdown files.
///
/// Creates individual .md files for each page in the specified directory.
/// Note: Full wiki-to-markdown conversion requires backend API (Phase 25).
/// This is a placeholder implementation.
#[tauri::command]
pub async fn export_wiki_markdown(
    app: tauri::AppHandle,
    page_ids: Vec<String>,
    output_dir: String,
) -> Result<ExportResult, String> {
    let output_path = PathBuf::from(&output_dir);
    std::fs::create_dir_all(&output_path)
        .map_err(|e| format!("Failed to create output directory: {}", e))?;

    let mut errors = Vec::new();
    let mut pages_exported = 0;

    for page_id in &page_ids {
        let file_name = format!("{}.md", sanitize_filename(page_id));
        let file_path = output_path.join(&file_name);

        // Placeholder content - real implementation will fetch from backend
        let content = format!(
            "# {}\n\nExported from Smart Agent Wiki.\n\n> Note: Full content integration pending Phase 25 (Backend Sidecar).\n",
            page_id
        );

        if let Err(e) = std::fs::write(&file_path, &content) {
            errors.push(format!("Failed to export {}: {}", page_id, e));
        } else {
            pages_exported += 1;
        }
    }

    Ok(ExportResult {
        path: output_dir,
        pages_exported,
        errors,
    })
}

/// Export wiki page as PDF via WebView print.
///
/// Uses Tauri's built-in print functionality to generate PDF.
/// Note: Full implementation requires HTML generation from wiki content.
#[tauri::command]
pub async fn export_wiki_pdf(
    app: tauri::AppHandle,
    page_id: String,
    output_path: String,
) -> Result<String, String> {
    use tauri::WebviewUrl;

    // Generate HTML content for the page
    let html = format!(
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>{}</title>\
        <style>body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; \
        margin: 2em; line-height: 1.6; }} h1 {{ color: #3b82f6; }}</style></head>\
        <body><h1>{}</h1><p>Exported from Smart Agent Wiki.</p>\
        <p><em>Note: Full content integration pending Phase 25 (Backend Sidecar).</em></p></body></html>",
        page_id, page_id
    );

    // Create a temporary window for printing
    let window_label = format!("print-{}", sanitize_filename(&page_id));

    // Use app data directory for temporary HTML file
    let temp_path = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("Failed to get app data dir: {}", e))?
        .join(&window_label)
        .with_extension("html");

    std::fs::write(&temp_path, &html)
        .map_err(|e| format!("Failed to write temp HTML: {}", e))?;

    let window = tauri::WebviewWindowBuilder::new(
        &app,
        &window_label,
        WebviewUrl::App(temp_path.clone().into()),
    )
    .title("Print Preview")
    .inner_size(800.0, 600.0)
    .build()
    .map_err(|e| format!("Failed to create print window: {}", e))?;

    // Trigger print dialog
    window
        .print()
        .map_err(|e| format!("Failed to trigger print: {}", e))?;

    // Close the window after print dialog
    window
        .close()
        .map_err(|e| format!("Failed to close print window: {}", e))?;

    // Clean up temp file
    let _ = std::fs::remove_file(&temp_path);

    Ok(output_path)
}

/// Sanitize filename to remove unsafe characters.
fn sanitize_filename(name: &str) -> String {
    name.chars()
        .map(|c| {
            if c.is_alphanumeric() || c == '-' || c == '_' || c == '.' {
                c
            } else {
                '_'
            }
        })
        .collect::<String>()
        .trim_matches('_')
        .to_string()
}