import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { GraphResponse, GraphParams } from '../types/api';

interface UseGraphParams extends GraphParams {
  entity?: string;
  enabled?: boolean;
}

/**
 * TanStack Query hook for graph API.
 * @param params Graph parameters including depth, mode, type, max_nodes
 * @returns Query result with data (GraphResponse), isLoading, isError
 */
export function useGraph(params: UseGraphParams = {}) {
  const {
    entity,
    depth = 2,
    mode = 'bfs',
    type,
    max_nodes = 50,
    enabled = true,
  } = params;

  const queryParams: Record<string, string | number | undefined> = {
    depth,
    mode,
    type,
    max_nodes,
  };

  // Use entity endpoint if specified, else use general graph endpoint
  const endpoint = entity
    ? `/api/graph/${encodeURIComponent(entity)}`
    : '/api/graph';

  return useQuery<GraphResponse>({
    queryKey: ['graph', entity, queryParams],
    queryFn: () => api.get<GraphResponse>(endpoint, queryParams),
    enabled,
    staleTime: 60_000, // Graph data is stable for 1min
  });
}

/**
 * Hook for fetching entity subgraph.
 * @param entity Entity ID or name to traverse from
 * @param depth Traversal depth (default 2, max 5)
 */
export function useEntityGraph(entity: string | null, depth: number = 2) {
  return useQuery<GraphResponse>({
    queryKey: ['graph', 'entity', entity, depth],
    queryFn: () => api.get<GraphResponse>(`/api/graph/${encodeURIComponent(entity!)}`, {
      depth,
      max_nodes: 50,
    }),
    enabled: !!entity,
    staleTime: 60_000,
  });
}
