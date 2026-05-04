//! IPC command handlers for Smart Agent Wiki
//!
//! This module exposes Rust functions callable from the frontend via Tauri IPC.

pub mod export;
pub mod fs;
pub mod preferences;

pub use export::*;
pub use fs::*;
pub use preferences::*;