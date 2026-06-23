import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import type { SearchResponse } from '../../types/api';

// Global state for command palette
let globalSetIsOpen: ((open: boolean) => void) | null = null;

/**
 * Open the command palette programmatically.
 */
export function openCommandPalette() {
  globalSetIsOpen?.(true);
}

/**
 * Cmd+K command palette for quick navigation and search.
 * Obsidian/Notion-style universal action launcher.
 */
export function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Register global opener
  useEffect(() => {
    globalSetIsOpen = setIsOpen;
    return () => { globalSetIsOpen = null; };
  }, []);

  // Search pages via FTS5
  const { data: searchResults, isLoading } = useQuery<SearchResponse>({
    queryKey: ['cmdk-search', query],
    queryFn: () => api.get<SearchResponse>('/api/search', { q: query, per_page: 8 }),
    enabled: isOpen && query.length >= 2,
    staleTime: 10_000,
  });

  // Keyboard shortcut: Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSelect = useCallback((slug: string) => {
    setIsOpen(false);
    navigate(`/page/${slug}`);
  }, [navigate]);

  const handleSearchFull = useCallback(() => {
    if (query.trim()) {
      setIsOpen(false);
      navigate(`/search?q=${encodeURIComponent(query)}`);
    }
  }, [navigate, query]);

  if (!isOpen) return null;

  const results = searchResults?.results ?? [];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={() => setIsOpen(false)}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
        <div
          className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-xl shadow-2xl
            border dark:border-gray-700 overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b dark:border-gray-700">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSearchFull();
              }}
              placeholder="Search knowledge base..."
              className="flex-1 bg-transparent border-none outline-none text-gray-900
                dark:text-white placeholder-gray-400 text-base"
            />
            <kbd className="hidden md:inline-block px-2 py-1 text-xs font-mono
              bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div className="max-h-80 overflow-y-auto">
            {isLoading && (
              <div className="px-4 py-3 text-sm text-gray-500">Searching...</div>
            )}

            {!isLoading && query.length >= 2 && results.length === 0 && (
              <div className="px-4 py-3 text-sm text-gray-500">
                No results for "{query}"
              </div>
            )}

            {!isLoading && results.map((result) => (
              <button
                key={result.slug}
                onClick={() => handleSelect(result.slug)}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700
                  border-b dark:border-gray-700 last:border-b-0 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {result.title}
                  </span>
                  <span className="text-xs text-gray-400 ml-auto">
                    {result.confidence > 0 && `●`.repeat(result.confidence)}
                  </span>
                </div>
                {result.snippet && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2 ml-6">
                    {result.snippet}
                  </p>
                )}
              </button>
            ))}

            {!isLoading && query.length >= 2 && results.length > 0 && (
              <button
                onClick={handleSearchFull}
                className="w-full px-4 py-3 text-left hover:bg-blue-50 dark:hover:bg-blue-900/20
                  text-blue-600 dark:text-blue-400 text-sm font-medium"
              >
                View all results →
              </button>
            )}

            {/* Quick actions */}
            {!isLoading && query.length < 2 && (
              <div className="py-2">
                <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                  Quick Actions
                </div>
                <button
                  onClick={() => { setIsOpen(false); navigate('/pages'); }}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700
                    text-gray-700 dark:text-gray-300"
                >
                  📄 Browse All Pages
                </button>
                <button
                  onClick={() => { setIsOpen(false); navigate('/graph'); }}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700
                    text-gray-700 dark:text-gray-300"
                >
                  🔗 View Knowledge Graph
                </button>
                <button
                  onClick={() => { setIsOpen(false); navigate('/dashboard'); }}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700
                    text-gray-700 dark:text-gray-300"
                >
                  📊 Dashboard
                </button>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50
            flex items-center justify-between text-xs text-gray-500">
            <span>
              <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">↑↓</kbd> navigate
              <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded ml-2">↵</kbd> select
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">⌘K</kbd> toggle
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
