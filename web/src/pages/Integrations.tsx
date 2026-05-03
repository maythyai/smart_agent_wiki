import { useIntegrations } from '../hooks/useIntegrations';
import { useIntegrationWebSocket } from '../hooks/useIntegrationWebSocket';
import { IntegrationList } from '../components/integrations/IntegrationList';
import { ConnectionIndicator } from '../components/integrations/ConnectionIndicator';

/**
 * Integration Dashboard page.
 * Per 15-01: Unified visibility into all connector health and management controls.
 * Per 16-02: Real-time updates via WebSocket.
 */
export default function Integrations() {
  const {
    connectors,
    systemHealth,
    loading,
    error,
    lastUpdate,
    handleDisconnect,
    handleSync,
    handleReauth,
    clearErrors,
    refresh,
  } = useIntegrations();

  // WebSocket for real-time updates
  const platforms = connectors.map((c) => c.platform);
  const wsStatus = useIntegrationWebSocket({ platforms });

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header with WebSocket status */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integration Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Manage platform connections and monitor sync status
          </p>
        </div>
        <ConnectionIndicator status={wsStatus.status} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-700">{error}</span>
          </div>
          <button
            onClick={clearErrors}
            className="text-red-500 hover:text-red-700"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* System health summary */}
      {systemHealth && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800">System Health</h2>
            <button
              onClick={refresh}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>

          {/* Status counts */}
          <div className="flex items-center gap-6 mt-3">
            {systemHealth.healthy_count > 0 && (
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-sm text-gray-600">
                  {systemHealth.healthy_count} healthy
                </span>
              </div>
            )}
            {systemHealth.degraded_count > 0 && (
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="text-sm text-gray-600">
                  {systemHealth.degraded_count} degraded
                </span>
              </div>
            )}
            {systemHealth.unhealthy_count > 0 && (
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-sm text-gray-600">
                  {systemHealth.unhealthy_count} unhealthy
                </span>
              </div>
            )}
          </div>

          {/* Last update timestamp */}
          {lastUpdate && (
            <p className="text-xs text-gray-400 mt-2">
              Last updated: {new Date(lastUpdate).toLocaleTimeString()}
            </p>
          )}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && connectors.length === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 bg-gray-200 rounded-lg" />
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-24 mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-16" />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="h-8 bg-gray-100 rounded" />
                <div className="h-8 bg-gray-100 rounded" />
                <div className="h-8 bg-gray-100 rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Integration list */}
      {!loading || connectors.length > 0 ? (
        <IntegrationList
          connectors={connectors}
          onDisconnect={handleDisconnect}
          onSync={handleSync}
          onReauth={handleReauth}
        />
      ) : null}
    </div>
  );
}