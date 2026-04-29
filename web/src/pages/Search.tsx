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

  const { data, isLoading, isError } = useSearch({
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
            <SearchResults
              data={data}
              isLoading={isLoading}
              isError={isError}
              page={page}
              onPageChange={handlePageChange}
            />
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