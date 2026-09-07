import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { AgentRosterEntry } from '../types/api';

interface AgentListResponse {
  agents: AgentRosterEntry[];
  total: number;
}

/**
 * Fetch agent roster from REST API with 15s polling (ADR-016).
 *
 * WS agent_status messages invalidate this query via useWebSocket,
 * triggering an immediate refetch in addition to the 15s interval.
 */
export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get<AgentListResponse>('/api/v1/agents'),
    refetchInterval: 15000,
  });
}
