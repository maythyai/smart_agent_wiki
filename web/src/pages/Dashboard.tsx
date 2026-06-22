import { useWebSocket } from '../hooks/useWebSocket';
import { AgentList } from '../components/dashboard/AgentList';
import { ConnectionStatus } from '../components/dashboard/ConnectionStatus';
import { useStore } from '../stores';
import { useState, useEffect } from 'react';

interface StatsData {
  total_pages: number;
  recent_edits: number;
  active_agents: number;
  uptime_hours: number;
}

/**
 * Dashboard page displays agent status and WebSocket connection.
 * Per D-17: Real-time agent status via WebSocket.
 * Per D-18~19: Agent list with name, status, task, progress.
 * v3.6 Enhancement: Statistics cards and quick actions.
 */
export default function Dashboard() {
  // Initialize WebSocket connection (auto-connects on mount)
  const { reconnect, status: wsStatus } = useWebSocket({ autoConnect: true });

  // Dashboard state from store (updated via WebSocket)
  const agents = useStore((s) => s.agents);
  const activeWorkflow = useStore((s) => s.activeWorkflow);
  const lastUpdate = useStore((s) => s.lastUpdate);

  // Statistics state
  const [stats, setStats] = useState<StatsData>({
    total_pages: 0,
    recent_edits: 0,
    active_agents: 0,
    uptime_hours: 0,
  });

  // Fetch statistics periodically
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/dashboard/stats');
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agent Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Monitor agent status and workflow progress in real-time
        </p>
      </div>

      {/* Connecting state */}
      {wsStatus === 'connecting' && (
        <div className="flex items-center gap-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
          <div className="w-5 h-5 border-2 border-yellow-300 border-t-yellow-600 rounded-full animate-spin" />
          <p className="text-sm text-yellow-800 dark:text-yellow-300">Connecting to agent server...</p>
        </div>
      )}

      {/* Disconnected error state */}
      {wsStatus === 'disconnected' && (
        <div className="flex items-center justify-between bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="text-red-500">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M18.364 5.636a9 9 0 010 12.728M5.636 5.636a9 9 0 000 12.728M12 12h.01" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-red-800 dark:text-red-300">Disconnected from server</p>
              <p className="text-xs text-red-600 dark:text-red-400">Agent updates are paused. Reconnecting automatically.</p>
            </div>
          </div>
          <button
            onClick={reconnect}
            className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-xs font-medium"
          >
            Reconnect
          </button>
        </div>
      )}

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

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Total Pages</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stats.total_pages}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Recent Edits (24h)</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stats.recent_edits}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Active Agents</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stats.active_agents}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Uptime</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{stats.uptime_hours}h</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6 border border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => window.location.href = '/graph'}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View Graph
          </button>
          <button
            onClick={() => window.location.href = '/search'}
            className="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Search Pages
          </button>
          <button
            onClick={() => window.location.href = '/integrations'}
            className="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Manage Integrations
          </button>
        </div>
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
      {Object.keys(agents).length === 0 && wsStatus === 'connected' && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-8 text-center">
          <div className="text-gray-400 dark:text-gray-500 mb-3">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300 mb-1">No Agents Running</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Start the backend server and agents will appear here
          </p>
        </div>
      )}
    </div>
  );
}