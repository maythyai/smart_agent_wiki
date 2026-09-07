import { useState } from 'react';
import { useWorkflows } from '../../hooks/useWorkflows';
import { useWorkflowStatus } from '../../hooks/useWorkflowStatus';
import { WorkflowRow } from './WorkflowRow';

/**
 * WorkflowList renders recent workflow executions from REST API
 * (durable DB + live in-memory merge) with 15s polling (ADR-016).
 *
 * Features:
 * - Running workflows sorted to top
 * - Live marker for in-memory workflows
 * - Click to expand step-level status detail
 * - Empty state + error state with Retry
 */
export function WorkflowList() {
  const workflowsQuery = useWorkflows();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const statusQuery = useWorkflowStatus(expandedId);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  if (workflowsQuery.isLoading) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
        <div className="w-8 h-8 border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm text-gray-500 dark:text-gray-400">Loading workflows...</p>
      </div>
    );
  }

  if (workflowsQuery.isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center justify-between">
        <p className="text-sm text-red-800 dark:text-red-300">Failed to load workflows.</p>
        <button
          onClick={() => workflowsQuery.refetch()}
          className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-xs font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  const workflows = workflowsQuery.data?.workflows ?? [];

  if (workflows.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">No workflows executed yet</p>
      </div>
    );
  }

  // Sort: running first, then by updated_at DESC
  const sorted = [...workflows].sort((a, b) => {
    const aRunning = a.status === 'running' ? 0 : 1;
    const bRunning = b.status === 'running' ? 0 : 1;
    if (aRunning !== bRunning) return aRunning - bRunning;
    return (b.updated_at ?? '').localeCompare(a.updated_at ?? '');
  });

  return (
    <div className="space-y-2">
      {sorted.map((wf) => (
        <WorkflowRow
          key={wf.workflow_id}
          workflow={wf}
          isExpanded={expandedId === wf.workflow_id}
          onClick={() => toggleExpand(wf.workflow_id)}
          steps={expandedId === wf.workflow_id ? statusQuery.data?.steps : undefined}
          isLoadingSteps={
            expandedId === wf.workflow_id && statusQuery.isLoading
          }
        />
      ))}
    </div>
  );
}

export default WorkflowList;
