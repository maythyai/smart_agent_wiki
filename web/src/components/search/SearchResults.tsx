import { ResultCard } from './ResultCard';
import { Pagination } from '../ui/Pagination';
import { Spinner } from '../ui/Spinner';
import type { SearchResponse } from '../../types/api';

interface SearchResultsProps {
  data: SearchResponse | undefined;
  isLoading: boolean;
  isError: boolean;
  page: number;
  onPageChange: (page: number) => void;
}

export function SearchResults({ data, isLoading, isError, page, onPageChange }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-700">Failed to load search results. Please try again.</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  if (data.results.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <p className="text-gray-600">No results found. Try a different search term.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        Found {data.total} result{data.total !== 1 ? 's' : ''}
      </p>

      <div className="space-y-4">
        {data.results.map((result) => (
          <ResultCard key={result.slug} result={result} />
        ))}
      </div>

      {/* Pagination per D-07 */}
      <Pagination
        page={page}
        perPage={data.per_page}
        total={data.total}
        hasMore={data.has_more}
        onPageChange={onPageChange}
      />
    </div>
  );
}