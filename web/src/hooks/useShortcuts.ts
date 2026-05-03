/**
 * Global shortcuts hook for Smart Agent Wiki
 *
 * Listens for keyboard shortcut events from Tauri backend.
 * Per D-08: Standard keyboard shortcuts for common operations.
 * Per WIN-05: Keyboard shortcuts for common operations.
 *
 * Shortcuts handled:
 * - Cmd/Ctrl+N: new-wiki
 * - Cmd/Ctrl+O: open-vault
 * - Cmd/Ctrl+S: save
 * - Cmd/Ctrl+,: preferences
 *
 * Usage:
 * ```tsx
 * useShortcuts({
 *   'new-wiki': () => handleNewWiki(),
 *   'open-vault': () => handleOpenVault(),
 *   'save': () => handleSave(),
 *   'preferences': () => openPreferences(),
 * });
 * ```
 */
import { useEffect } from 'react';
import { listen, UnlistenFn } from '@tauri-apps/api/event';

export type ShortcutHandler = () => void;
export type ShortcutHandlers = Record<string, ShortcutHandler>;

/**
 * Hook for handling global keyboard shortcuts in Tauri.
 *
 * @param handlers - Object mapping shortcut names to handler functions
 *
 * Shortcut names (emitted by Rust backend):
 * - `new-wiki`: Create a new wiki
 * - `open-vault`: Open vault browser
 * - `save`: Save current work
 * - `preferences`: Open preferences dialog
 *
 * Note: Cmd/Ctrl+Q is handled directly by Rust (app exit), not via events.
 */
export function useShortcuts(handlers: ShortcutHandlers): void {
  useEffect(() => {
    // Check if running in Tauri
    const inTauri = typeof window !== 'undefined' && '__TAURI__' in window;
    if (!inTauri) {
      return;
    }

    const unlisteners: Promise<UnlistenFn>[] = [];

    // Register listeners for each shortcut
    Object.entries(handlers).forEach(([shortcut, handler]) => {
      const eventName = `shortcut:${shortcut}`;
      unlisteners.push(
        listen(eventName, () => {
          handler();
        })
      );
    });

    // Cleanup all listeners on unmount
    return () => {
      unlisteners.forEach((p) => p.then((fn) => fn()));
    };
  }, [handlers]);
}
