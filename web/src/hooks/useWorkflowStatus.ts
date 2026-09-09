import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { POLL_INTERVAL_MS } from '../lib/polling';
import type { WorkflowStatusDetail } from '../types/api';

/**
 * Fetch workflow step-level status detail from REST API with polling
 * fallback (ADR-016). Enabled only when a workflow row is clicked/expanded.
 */
export function useWorkflowStatus(workflowId: string | null) {
  return useQuery({
    queryKey: ['workflow-status', workflowId],
    queryFn: () =>
      api.get<WorkflowStatusDetail>(
        `/api/v1/workflows/${workflowId}/status`,
      ),
    enabled: !!workflowId,
    refetchInterval: POLL_INTERVAL_MS,
  });
}
