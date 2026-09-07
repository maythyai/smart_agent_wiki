import { useAgentActivity } from '../../hooks/useAgentActivity';

interface AgentActivityDetailProps {
  agentName: string | null;
  onClose?: () => void;
}

/**
 * AgentActivityDetail displays agent activity data fetched from
 * GET /api/v1/agents/{name}/activity (REST, 15s polling).
 *
 * States:
 * - Loading: spinner
 * - Error (404): "Agent not found"
 * - Success + calls=0: "no activity recorded"
 * - Success + calls>0: full activity details (calls/failures/last_action/last_active_at)
 */
export function AgentActivityDetail({ agentName, onClose }: AgentActivityDetailProps) {
  const { data, isError, isLoading } = useAgentActivity(agentName);

  if (!agentName) return null;

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-gray-300 border-t-gray-600 dark:border-gray-600 dark:border-t-gray-300 rounded-full animate-spin" />
          <p className="text-sm text-gray-500 dark:text-gray-400">Loading activity...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-red-800 dark:text-red-300">{agentName}</h4>
          <p className="text-sm text-red-600 dark:text-red-400">Agent not found</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="px-2 py-1 text-xs font-medium text-red-600 hover:text-red-800 dark:hover:text-red-200 hover:bg-red-100 dark:hover:bg-red-900/40 rounded transition-colors"
            aria-label="Close activity detail"
          >
            Close
          </button>
        )}
      </div>
    );
  }

  if (!data) return null;

  // calls=0: no activity recorded
  if (data.calls === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{data.agent}</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">no activity recorded</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-800 dark:text-gray-300 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            aria-label="Close activity detail"
          >
            Close
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
      <div className="space-y-1">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{data.agent}</h4>
        <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span>
            Calls: <span className="font-medium text-gray-700 dark:text-gray-200">{data.calls}</span>
          </span>
          <span>
            Failures: <span className="font-medium text-gray-700 dark:text-gray-200">{data.failures}</span>
          </span>
          <span>
            Last action: <span className="font-medium text-gray-700 dark:text-gray-200">{data.last_action ?? '—'}</span>
          </span>
          <span>
            Last active:{' '}
            <span className="font-medium text-gray-700 dark:text-gray-200">
              {data.last_active_at ? new Date(data.last_active_at).toLocaleString() : '—'}
            </span>
          </span>
        </div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-800 dark:text-gray-300 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
          aria-label="Close activity detail"
        >
          Close
        </button>
      )}
    </div>
  );
}

export default AgentActivityDetail;
