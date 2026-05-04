import { invoke } from '@tauri-apps/api/core';
import { useState, useCallback } from 'react';

interface ExportResult {
  path: string;
  pages_exported: number;
  errors: string[];
}

interface UseExportReturn {
  exportMarkdown: (pageIds: string[], outputDir?: string) => Promise<ExportResult | null>;
  exportPdf: (pageId: string, outputPath?: string) => Promise<string | null>;
  getDefaultExportDir: () => Promise<string>;
  isLoading: boolean;
  error: string | null;
}

/**
 * React hook for wiki page export via Tauri IPC.
 *
 * Provides Markdown and PDF export functionality.
 */
export function useExport(): UseExportReturn {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getDefaultExportDir = useCallback(async (): Promise<string> => {
    try {
      const dir = await invoke<string>('get_export_default_dir');
      return dir;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setError(errorMsg);
      return '';
    }
  }, []);

  const exportMarkdown = useCallback(
    async (pageIds: string[], outputDir?: string): Promise<ExportResult | null> => {
      setIsLoading(true);
      setError(null);

      try {
        // Get default export directory if not provided
        const targetDir = outputDir || await getDefaultExportDir();

        const result = await invoke<ExportResult>('export_wiki_markdown', {
          pageIds,
          outputDir: targetDir,
        });

        return result;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        setError(errorMsg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [getDefaultExportDir]
  );

  const exportPdf = useCallback(
    async (pageId: string, outputPath?: string): Promise<string | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const path = await invoke<string>('export_wiki_pdf', {
          pageId,
          outputPath: outputPath || `${pageId}.pdf`,
        });

        return path;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : String(err);
        setError(errorMsg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    exportMarkdown,
    exportPdf,
    getDefaultExportDir,
    isLoading,
    error,
  };
}