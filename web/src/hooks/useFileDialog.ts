import { invoke } from '@tauri-apps/api/core';
import { useState, useCallback } from 'react';

interface UseFileDialogReturn {
  openFiles: () => Promise<string[]>;
  openFolder: () => Promise<string | null>;
  saveFile: (defaultName: string) => Promise<string | null>;
  isLoading: boolean;
  error: string | null;
}

/**
 * React hook for native file dialogs via Tauri IPC.
 *
 * Provides methods for opening files, folders, and save dialogs.
 */
export function useFileDialog(): UseFileDialogReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openFiles = useCallback(async (): Promise<string[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const paths = await invoke<string[]>('select_files');
      return paths;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const openFolder = useCallback(async (): Promise<string | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const path = await invoke<string | null>('select_folder');
      return path;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveFile = useCallback(async (defaultName: string): Promise<string | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const path = await invoke<string | null>('select_export_location', {
        defaultName,
      });
      return path;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    openFiles,
    openFolder,
    saveFile,
    isLoading,
    error,
  };
}