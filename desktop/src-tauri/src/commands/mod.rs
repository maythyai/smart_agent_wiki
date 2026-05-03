//! IPC command handlers for Smart Agent Wiki
//!
//! This module exposes Rust functions callable from the frontend via Tauri IPC.

pub mod preferences;
pub use preferences::*;