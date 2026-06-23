import { useState, useRef } from 'react';
import { useNavigate } from 'react-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface ImportResponse {
  status: string;
  imported: number;
  skipped: number;
  errors: number;
  imported_files: string[];
  skipped_files: string[];
  error_details: Array<{ file: string; error: string }>;
}

/**
 * Import page for uploading Markdown/Obsidian vaults.
 * Supports:
 * - Multiple .md file upload
 * - ZIP archive upload
 * - Drag-and-drop
 */
export default function Import() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState<ImportResponse | null>(null);

  // Import markdown files mutation
  const importMdMutation = useMutation<ImportResponse, Error, File[]>({
    mutationFn: async (files: File[]) => {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));
      return api.post<ImportResponse>('/api/import/markdown', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['pages'] });
    },
  });

  // Import ZIP mutation
  const importZipMutation = useMutation<ImportResponse, Error, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<ImportResponse>('/api/import/zip', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ['pages'] });
    },
  });

  const handleMdFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files).filter((f) => f.name.endsWith('.md'));
    if (fileArray.length > 0) {
      importMdMutation.mutate(fileArray);
      setResult(null);
    }
  };

  const handleZipFile = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const zipFile = Array.from(files).find((f) => f.name.endsWith('.zip'));
    if (zipFile) {
      importZipMutation.mutate(zipFile);
      setResult(null);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const firstFile = files[0];
      if (firstFile.name.endsWith('.zip')) {
        importZipMutation.mutate(firstFile);
      } else {
        const mdFiles = Array.from(files).filter((f) => f.name.endsWith('.md'));
        if (mdFiles.length > 0) {
          importMdMutation.mutate(mdFiles);
        }
      }
      setResult(null);
    }
  };

  const isLoading = importMdMutation.isPending || importZipMutation.isPending;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Import Knowledge
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Import Markdown files or an Obsidian vault into your wiki
        </p>
      </div>

      {/* Drag and drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center transition-colors
          ${dragActive
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
        `}
      >
        <svg className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
          Drag and drop files here
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          .md files or .zip archive
        </p>

        <div className="flex gap-3 justify-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
              text-white rounded-lg font-medium"
          >
            Select .md Files
          </button>
          <button
            onClick={() => zipInputRef.current?.click()}
            disabled={isLoading}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50
              text-white rounded-lg font-medium"
          >
            Upload .zip Archive
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".md"
          onChange={(e) => handleMdFiles(e.target.files)}
          className="hidden"
        />
        <input
          ref={zipInputRef}
          type="file"
          accept=".zip"
          onChange={(e) => handleZipFile(e.target.files)}
          className="hidden"
        />
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
            <p className="text-blue-700 dark:text-blue-300 font-medium">
              Importing files...
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {(importMdMutation.isError || importZipMutation.isError) && (
        <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-600 dark:text-red-400 font-medium">Import failed</p>
          <p className="text-sm text-red-500 dark:text-red-500 mt-1">
            {importMdMutation.error?.message || importZipMutation.error?.message}
          </p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-6 p-6 bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Import Complete
          </h3>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {result.imported}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Imported</p>
            </div>
            <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
              <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                {result.skipped}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Skipped</p>
            </div>
            <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {result.errors}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Errors</p>
            </div>
          </div>

          {result.imported_files.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Imported pages:
              </p>
              <div className="flex flex-wrap gap-2">
                {result.imported_files.map((slug) => (
                  <button
                    key={slug}
                    onClick={() => navigate(`/page/imported/${slug}`)}
                    className="px-2 py-1 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600
                      dark:text-blue-400 rounded hover:bg-blue-100 dark:hover:bg-blue-900/50"
                  >
                    {slug}
                  </button>
                ))}
              </div>
            </div>
          )}

          {result.error_details.length > 0 && (
            <details className="mb-4">
              <summary className="text-sm font-medium text-red-600 dark:text-red-400 cursor-pointer">
                View error details ({result.error_details.length})
              </summary>
              <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/10 rounded text-xs font-mono">
                {result.error_details.map((err, i) => (
                  <div key={i} className="mb-1">
                    <span className="font-semibold">{err.file}:</span> {err.error}
                  </div>
                ))}
              </div>
            </details>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => navigate('/pages')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
            >
              View All Pages
            </button>
            <button
              onClick={() => {
                setResult(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
                if (zipInputRef.current) zipInputRef.current.value = '';
              }}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700
                dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg"
            >
              Import More
            </button>
          </div>
        </div>
      )}

      {/* Help section */}
      <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
          Supported Formats
        </h3>
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>Standard Markdown (.md) files</span>
          </li>
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>Obsidian vaults with YAML frontmatter</span>
          </li>
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>ZIP archives containing nested .md files</span>
          </li>
          <li className="flex items-start gap-2">
            <svg className="w-5 h-5 text-green-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>[[wiki-links]] are automatically resolved</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
