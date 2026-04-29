import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { SearchResponse, SearchParams } from '../types/api';

interface UseSearchParams extends Omit<SearchParams, 'q'> {
  query: string;
  enabled?: boolean;
}

/**
 * TanStack Query hook for search API.
 * @param params Search parameters including query, page, filters
 * @returns Query result with data, isLoading, isError, refetch
 */
export function useSearch(params: UseSearchParams) {
  const {
    query,
    page = 1,
    per_page = 10,
    type,
    tag,
    min_confidence,
    enabled = true,
  } = params;

  // Build query params, omitting undefined values
  const queryParams: Record<string, string | number | undefined> = {
    q: query,
    page,
    per_page,
    type,
    tag,
    min_confidence,
  };

  return useQuery<SearchResponse>({
    queryKey: ['search', queryParams],
    queryFn: () => api.get<SearchResponse>('/api/search', queryParams),
    enabled: enabled && query.length > 0, // Per D-05: only fetch when query exists
    staleTime: 30_000, // Consider fresh for 30s
  });
}