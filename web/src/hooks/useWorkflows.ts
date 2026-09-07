import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { WorkflowListResponse } from '../types/api';

/**
 * Fetch workflow list (durable DB + live in-memory merge) from REST API
 * with 15s polling (ADR-016).
 *
 * WS workflow_progress messages invalidate this query via useWebSocket,
 * triggering an immediate refetch in addition to the 15s interval.
 */
export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () =>
      api.get<WorkflowListResponse>('/api/v1/workflows', { limit: 20 }),
    refetchInterval: 15000,
  });
}
