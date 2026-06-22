import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router';
import { SearchBar } from '../components/search/SearchBar';
import { SearchResults } from '../components/search/SearchResults';
import { SearchFilters } from '../components/search/SearchFilters';
import { useSearch } from '../hooks/useSearch';

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const page = parseInt(searchParams.get('page') ?? '1', 10);
  const type = searchParams.get('type') ?? undefined;
  const tag = searchParams.get('tag') ?? undefined;
  const minConfidence = searchParams.get('min_confidence')
    ? parseInt(searchParams.get('min_confidence')!, 10)
    : undefined;

  const [, setInputQuery] = useState(query);

  const { data, isLoading, isError, error, refetch } = useSearch({
    query,
    page,
    per_page: 10,
    type,
    tag,
    min_confidence: minConfidence,
    enabled: query.length > 0,
  });

  // Sync input with URL on mount
  useEffect(() => {
    setInputQuery(query);
  }, [query]);

  const handleSearch = (newQuery: string) => {
    setInputQuery(newQuery);
    setSearchParams((params) => {
      params.set('q', newQuery);
      params.set('page', '1');
      if (!newQuery) params.delete('q');
      return params;
    });
  };

  const handlePageChange = (newPage: number) => {
    setSearchParams((params) => {
      params.set('page', String(newPage));
      return params;
    });
  };

  const handleTypeChange = (newType: string | undefined) => {
    setSearchParams((params) => {
      if (newType) params.set('type', newType);
      else params.delete('type');
      params.set('page', '1');
      return params;
    });
  };

  const handleTagChange = (newTag: string | undefined) => {
    setSearchParams((params) => {
      if (newTag) params.set('tag', newTag);
      else params.delete('tag');
      params.set('page', '1');
      return params;
    });
  };

  const handleMinConfidenceChange = (level: number | undefined) => {
    setSearchParams((params) => {
      if (level !== undefined) params.set('min_confidence', String(level));
      else params.delete('min_confidence');
      params.set('page', '1');
      return params;
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Search</h1>
        <SearchBar
          onSearch={handleSearch}
          placeholder="Search knowledge base..."
          autoFocus={!query}
        />
      </div>

      {query && (
        <div className="flex gap-8">
          {/* Filters sidebar */}
          <aside className="w-64 flex-shrink-0">
            <SearchFilters
              type={type}
              tag={tag}
              minConfidence={minConfidence}
              onTypeChange={handleTypeChange}
              onTagChange={handleTagChange}
              onMinConfidenceChange={handleMinConfidenceChange}
            />
          </aside>

          {/* Results */}
          <main className="flex-1">
            {isLoading && (
              <div className="flex items-center justify-center py-16">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">Searching...</p>
                </div>
              </div>
            )}

            {isError && !isLoading && (
              <div className="text-center py-16">
                <div className="text-red-500 mb-3">
                  <svg className="w-10 h-10 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">Search failed</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {error instanceof Error ? error.message : 'Something went wrong. Please try again.'}
                </p>
                <button
                  onClick={() => refetch()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  Retry
                </button>
              </div>
            )}

            {!isLoading && !isError && data && data.results.length === 0 && (
              <div className="text-center py-16">
                <div className="text-gray-400 dark:text-gray-500 mb-3">
                  <svg className="w-10 h-10 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">No results found</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  No results found for &ldquo;{query}&rdquo;. Try different keywords or filters.
                </p>
              </div>
            )}

            {!isLoading && !isError && data && data.results.length > 0 && (
              <SearchResults
                data={data}
                isLoading={isLoading}
                isError={isError}
                page={page}
                onPageChange={handlePageChange}
              />
            )}
          </main>
        </div>
      )}

      {!query && (
        <div className="text-center py-12">
          <p className="text-gray-600">Enter a search term to find knowledge.</p>
        </div>
      )}
    </div>
  );
}