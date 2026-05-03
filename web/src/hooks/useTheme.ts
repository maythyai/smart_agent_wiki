/**
 * Theme hook for Smart Agent Wiki
 *
 * Provides theme detection and application for the desktop app.
 * Per D-07: App follows system dark/light theme automatically.
 * Per WIN-04: Dark/light theme follows system setting.
 *
 * In Tauri mode: Uses IPC to get theme from Rust backend and listens for changes.
 * In web mode: Falls back to CSS media query for system preference.
 */
import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen, UnlistenFn } from '@tauri-apps/api/event';

export interface UseThemeResult {
  /** Whether the current theme is dark */
  isDark: boolean;
  /** Whether the theme detection is ready */
  isReady: boolean;
}

/**
 * Hook for detecting and applying system theme.
 *
 * In Tauri:
 * - Calls `get_system_theme` command to get initial theme
 * - Listens for `theme-changed` events from Rust backend
 * - Applies `dark` class to document root element
 *
 * In web browser:
 * - Uses `prefers-color-scheme` media query
 * - Listens for changes to system preference
 */
export function useTheme(): UseThemeResult {
  const [isDark, setIsDark] = useState(false);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if running in Tauri
    const inTauri = typeof window !== 'undefined' && '__TAURI__' in window;

    if (!inTauri) {
      // Web browser mode: use CSS media query
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      setIsDark(mediaQuery.matches);
      setIsReady(true);

      const handler = (e: MediaQueryListEvent) => setIsDark(e.matches);
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }

    // Tauri mode: get theme from backend
    let unlisten: UnlistenFn | null = null;

    const init = async () => {
      try {
        // Get initial theme
        const theme = await invoke<string>('get_system_theme');
        setIsDark(theme === 'dark');
        setIsReady(true);

        // Listen for theme changes from Rust
        unlisten = await listen<boolean>('theme-changed', (event) => {
          setIsDark(event.payload);
        });
      } catch {
        // Fallback to light theme on error
        setIsReady(true);
      }
    };

    init();

    return () => {
      if (unlisten) {
        unlisten();
      }
    };
  }, []);

  // Apply dark class to document root
  useEffect(() => {
    if (isReady) {
      document.documentElement.classList.toggle('dark', isDark);
    }
  }, [isDark, isReady]);

  return { isDark, isReady };
}
