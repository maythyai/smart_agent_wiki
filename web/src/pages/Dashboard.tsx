import { useWebSocket } from '../hooks/useWebSocket';
import { AgentList } from '../components/dashboard/AgentList';
import { ConnectionStatus } from '../components/dashboard/ConnectionStatus';
import { useStore } from '../stores';

/**
 * Dashboard page displays agent status and WebSocket connection.
 * Per D-17: Real-time agent status via WebSocket.
 * Per D-18~19: Agent list with name, status, task, progress.
 */
export default function Dashboard() {
  // Initialize WebSocket connection (auto-connects on mount)
  const { reconnect } = useWebSocket({ autoConnect: true });

  // Dashboard state from store (updated via WebSocket)
  const agents = useStore((s) => s.agents);
  const activeWorkflow = useStore((s) => s.activeWorkflow);
  const lastUpdate = useStore((s) => s.lastUpdate);

  // Count agents by status
  const agentCounts = Object.values(agents).reduce(
    (acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Agent Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Monitor agent status and workflow progress in real-time
        </p>
      </div>

      {/* Status bar */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Connection status */}
        <ConnectionStatus onReconnect={reconnect} />

        {/* Agent counts */}
        <div className="flex items-center gap-3 text-sm">
          {agentCounts.running && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
              {agentCounts.running} running
            </span>
          )}
          {agentCounts.error && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              {agentCounts.error} error
            </span>
          )}
          {agentCounts.idle && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-400" />
              {agentCounts.idle} idle
            </span>
          )}
          {agentCounts.completed && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              {agentCounts.completed} completed
            </span>
          )}
        </div>

        {/* Last update timestamp */}
        {lastUpdate && (
          <span className="text-xs text-gray-400 ml-auto">
            Last update: {new Date(lastUpdate).toLocaleTimeString()}
          </span>
        )}
      </div>

      {/* Active workflow banner */}
      {activeWorkflow && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-blue-900">
                Active Workflow: {activeWorkflow.workflow_id}
              </h3>
              <p className="text-sm text-blue-700 mt-1">
                Step {activeWorkflow.current_step}/{activeWorkflow.total_steps}: {activeWorkflow.step}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  activeWorkflow.status === 'running'
                    ? 'bg-blue-100 text-blue-700'
                    : activeWorkflow.status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : activeWorkflow.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-700'
                }`}
              >
                {activeWorkflow.status}
              </span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-3">
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                style={{
                  width: `${Math.min(100, (activeWorkflow.current_step / activeWorkflow.total_steps) * 100)}%`,
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Agent list */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">Agents</h2>
        <AgentList />
      </div>

      {/* Empty state */}
      {Object.keys(agents).length === 0 && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <div className="text-gray-400 mb-3">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-600 mb-1">No Agents Connected</h3>
          <p className="text-sm text-gray-500">
            Start the backend server and agents will appear here
          </p>
        </div>
      )}
    </div>
  );
}