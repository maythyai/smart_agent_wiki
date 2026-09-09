import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { POLL_INTERVAL_MS } from '../lib/polling';
import type { AgentRosterEntry } from '../types/api';

interface AgentListResponse {
  agents: AgentRosterEntry[];
  total: number;
}

/**
 * Fetch agent roster from REST API with polling fallback (ADR-016).
 *
 * WS agent_status messages invalidate this query via useWebSocket,
 * triggering an immediate refetch in addition to the interval below.
 * POLL_INTERVAL_MS is configurable via VITE_POLL_INTERVAL_MS.
 */
export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get<AgentListResponse>('/api/v1/agents'),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
