import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { POLL_INTERVAL_MS } from '../lib/polling';
import type { WorkflowListResponse } from '../types/api';

/**
 * Fetch workflow list (durable DB + live in-memory merge) from REST API
 * with polling fallback (ADR-016).
 *
 * WS workflow_progress messages invalidate this query via useWebSocket,
 * triggering an immediate refetch in addition to the interval below.
 */
export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () =>
      api.get<WorkflowListResponse>('/api/v1/workflows', { limit: 20 }),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
