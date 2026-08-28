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

    if (inTauri) {
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
    }

    // F-WEB-07: web (browser) mode — register native keydown listeners for
    // the same shortcuts (previously Tauri-only, so Cmd+S/O/N/, did nothing
    // in the browser). Only fires when a handler is actually registered.
    const keyMap: Record<string, string> = {
      n: 'new-wiki',
      o: 'open-vault',
      s: 'save',
      ',': 'preferences',
    };
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey)) return;
      const name = keyMap[e.key.toLowerCase()];
      if (name && handlers[name]) {
        e.preventDefault();
        handlers[name]();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [handlers]);
}
