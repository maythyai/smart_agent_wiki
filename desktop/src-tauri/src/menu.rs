//! Native menu bar implementation for Smart Agent Wiki
//!
//! Provides File, Edit, View, and Help menus with standard desktop shortcuts.

use tauri::{
    menu::{Menu, MenuBuilder, MenuItem, MenuItemBuilder, Submenu, SubmenuBuilder},
    App, Manager,
};

/// Setup the native menu bar with File, Edit, View, Help menus.
///
/// Returns the constructed menu to be set on the application.
pub fn setup_menu(app: &App) -> Result<Menu<tauri::Wry>, Box<dyn std::error::Error>> {
    // File menu
    let new_wiki = MenuItemBuilder::with_id("new_wiki", "New Wiki")
        .accelerator("CmdOrCtrl+N")
        .build(app)?;
    let open_vault = MenuItemBuilder::with_id("open_vault", "Open Vault")
        .accelerator("CmdOrCtrl+O")
        .build(app)?;
    let save = MenuItemBuilder::with_id("save", "Save")
        .accelerator("CmdOrCtrl+S")
        .build(app)?;
    let preferences = MenuItemBuilder::with_id("preferences", "Preferences...")
        .accelerator("CmdOrCtrl+,")
        .build(app)?;
    let quit = MenuItemBuilder::with_id("quit", "Quit")
        .accelerator("CmdOrCtrl+Q")
        .build(app)?;

    let file_menu = SubmenuBuilder::new(app, "File")
        .item(&new_wiki)
        .item(&open_vault)
        .separator()
        .item(&save)
        .separator()
        .item(&preferences)
        .separator()
        .item(&quit)
        .build()?;

    // Edit menu
    let undo = MenuItemBuilder::with_id("undo", "Undo")
        .accelerator("CmdOrCtrl+Z")
        .build(app)?;
    let redo = MenuItemBuilder::with_id("redo", "Redo")
        .accelerator("CmdOrCtrl+Shift+Z")
        .build(app)?;
    let cut = MenuItemBuilder::with_id("cut", "Cut")
        .accelerator("CmdOrCtrl+X")
        .build(app)?;
    let copy = MenuItemBuilder::with_id("copy", "Copy")
        .accelerator("CmdOrCtrl+C")
        .build(app)?;
    let paste = MenuItemBuilder::with_id("paste", "Paste")
        .accelerator("CmdOrCtrl+V")
        .build(app)?;

    let edit_menu = SubmenuBuilder::new(app, "Edit")
        .item(&undo)
        .item(&redo)
        .separator()
        .item(&cut)
        .item(&copy)
        .item(&paste)
        .build()?;

    // View menu
    let toggle_sidebar = MenuItemBuilder::with_id("toggle_sidebar", "Toggle Sidebar")
        .accelerator("CmdOrCtrl+B")
        .build(app)?;
    let reload = MenuItemBuilder::with_id("reload", "Reload")
        .accelerator("CmdOrCtrl+R")
        .build(app)?;

    let view_menu = SubmenuBuilder::new(app, "View")
        .item(&toggle_sidebar)
        .item(&reload)
        .build()?;

    // Help menu
    let docs = MenuItemBuilder::with_id("docs", "Documentation")
        .build(app)?;
    let shortcuts = MenuItemBuilder::with_id("shortcuts", "Keyboard Shortcuts")
        .build(app)?;
    let about = MenuItemBuilder::with_id("about", "About Smart Agent Wiki")
        .build(app)?;

    let help_menu = SubmenuBuilder::new(app, "Help")
        .item(&docs)
        .item(&shortcuts)
        .separator()
        .item(&about)
        .build()?;

    // Build the main menu bar
    let menu = MenuBuilder::new(app)
        .item(&file_menu)
        .item(&edit_menu)
        .item(&view_menu)
        .item(&help_menu)
        .build()?;

    Ok(menu)
}