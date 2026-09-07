import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { AgentActivity } from '../types/api';

/**
 * Fetch agent activity detail (calls/failures/last_action/last_active_at)
 * from REST API with 15s polling (ADR-016).
 *
 * Enabled only when an agent is selected (clicked) in the roster.
 */
export function useAgentActivity(agentName: string | null) {
  return useQuery({
    queryKey: ['agent-activity', agentName],
    queryFn: () => api.get<AgentActivity>(`/api/v1/agents/${agentName}/activity`),
    enabled: !!agentName,
    refetchInterval: 15000,
  });
}
