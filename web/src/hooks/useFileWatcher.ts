import { invoke } from '@tauri-apps/api/core';
import { listen, UnlistenFn } from '@tauri-apps/api/event';
import { useEffect, useState, useCallback } from 'react';

interface WatchConfig {
  path: string;
  enabled: boolean;
  file_types: string[];
}

interface WatchedFolder {
  path: string;
  config?: WatchConfig;
}

interface UseFileWatcherReturn {
  watchedFolders: string[];
  addWatchFolder: (path: string, config: WatchConfig) => Promise<void>;
  removeWatchFolder: (path: string) => Promise<void>;
  updateWatchConfig: (path: string, config: WatchConfig) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

/**
 * React hook for file system watching via Tauri IPC.
 *
 * Subscribes to file events and provides folder management functions.
 */
export function useFileWatcher(): UseFileWatcherReturn {
  const [watchedFolders, setWatchedFolders] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Subscribe to file system events
  useEffect(() => {
    let cancelled = false;
    const unlisteners: UnlistenFn[] = [];

    const subscribe = async () => {
      // Listen for file creation events
      const unlistenCreated = await listen<string>('fs:file-created', (event) => {
        console.log('File created:', event.payload);
        // Emit custom event for app to handle
        window.dispatchEvent(new CustomEvent('saw:file-created', {
          detail: { path: event.payload }
        }));
      });
      if (cancelled) { unlistenCreated(); return; }
      unlisteners.push(unlistenCreated);

      // Listen for file modification events
      const unlistenModified = await listen<string>('fs:file-modified', (event) => {
        console.log('File modified:', event.payload);
        window.dispatchEvent(new CustomEvent('saw:file-modified', {
          detail: { path: event.payload }
        }));
      });
      if (cancelled) { unlistenModified(); return; }
      unlisteners.push(unlistenModified);

      // Listen for file deletion events
      const unlistenDeleted = await listen<string>('fs:file-deleted', (event) => {
        console.log('File deleted:', event.payload);
        window.dispatchEvent(new CustomEvent('saw:file-deleted', {
          detail: { path: event.payload }
        }));
      });
      if (cancelled) { unlistenDeleted(); return; }
      unlisteners.push(unlistenDeleted);
    };

    subscribe();

    // Cleanup listeners on unmount
    return () => {
      cancelled = true;
      unlisteners.forEach((unlisten) => unlisten());
    };
  }, []);

  // Fetch watched folders on mount
  useEffect(() => {
    fetchWatchedFolders();
  }, []);

  const fetchWatchedFolders = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const folders = await invoke<string[]>('get_watched_folders');
      setWatchedFolders(folders);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addWatchFolder = useCallback(async (path: string, config: WatchConfig) => {
    setIsLoading(true);
    setError(null);

    try {
      const folders = await invoke<string[]>('add_watch_folder', { path, config });
      setWatchedFolders(folders);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const removeWatchFolder = useCallback(async (path: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const folders = await invoke<string[]>('remove_watch_folder', { path });
      setWatchedFolders(folders);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateWatchConfig = useCallback(async (path: string, config: WatchConfig) => {
    setIsLoading(true);
    setError(null);

    try {
      const folders = await invoke<string[]>('update_watch_config', { path, config });
      setWatchedFolders(folders);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    watchedFolders,
    addWatchFolder,
    removeWatchFolder,
    updateWatchConfig,
    isLoading,
    error,
  };
}