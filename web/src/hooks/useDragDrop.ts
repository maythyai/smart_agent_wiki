import { invoke } from '@tauri-apps/api/core';
import { useState, useCallback } from 'react';

interface IngestResult {
  count: number;
}

interface UseDragDropOptions {
  onIngestStart?: () => void;
  onIngestComplete?: (count: number) => void;
  onIngestError?: (error: Error) => void;
  allowedTypes?: string[];
}

interface UseDragDropReturn {
  isDragging: boolean;
  handleDragOver: (e: React.DragEvent) => void;
  handleDragLeave: (e: React.DragEvent) => void;
  handleDrop: (e: React.DragEvent) => Promise<void>;
}

/**
 * React hook for handling file drag-and-drop in Tauri.
 *
 * Extracts file paths from dropped files and invokes the Rust backend
 * for ingestion.
 */
export function useDragDrop(options: UseDragDropOptions = {}): UseDragDropReturn {
  const [isDragging, setIsDragging] = useState(false);
  const { onIngestStart, onIngestComplete, onIngestError, allowedTypes } = options;

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    // Extract file items from DataTransfer
    const items = Array.from(e.dataTransfer.items);
    const fileItems = items.filter(item => item.kind === 'file');

    if (fileItems.length === 0) {
      console.warn('No files in drop event');
      return;
    }

    // Get file paths (Tauri provides path property on File objects)
    const files = fileItems
      .map(item => item.getAsFile())
      .filter((f): f is File => f !== null);

    const paths: string[] = files
      .map(f => (f as any).path)
      .filter((path): path is string => path !== undefined);

    // Filter by allowed file types if specified
    let filteredPaths = paths;
    if (allowedTypes && allowedTypes.length > 0) {
      filteredPaths = paths.filter(path => {
        const ext = path.split('.').pop()?.toLowerCase();
        return ext && allowedTypes.includes(ext);
      });
    }

    if (filteredPaths.length === 0) {
      console.warn('No valid files after filtering');
      return;
    }

    onIngestStart?.();

    try {
      const result = await invoke<IngestResult>('fs:ingest-files', {
        paths: filteredPaths,
      });
      onIngestComplete?.(result.count);
    } catch (error) {
      console.error('Ingestion failed:', error);
      onIngestError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }, [onIngestStart, onIngestComplete, onIngestError, allowedTypes]);

  return {
    isDragging,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  };
}