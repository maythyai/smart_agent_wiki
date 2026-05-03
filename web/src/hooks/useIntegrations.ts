import { useEffect } from 'react';
import { useIntegrationsStore } from '../stores/integrationsStore';

/**
 * Hook for integration dashboard.
 * Initial fetch on mount; real-time updates via WebSocket (useIntegrationWebSocket).
 * Per 16-02: No more 30-second polling - WebSocket pushes updates.
 */
export function useIntegrations() {
  const {
    connectors,
    systemHealth,
    loading,
    error,
    lastUpdate,
    fetchDashboard,
    disconnectPlatform,
    triggerSync,
    clearErrors,
  } = useIntegrationsStore();

  // Initial fetch on mount
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Handlers for actions
  const handleDisconnect = async (platform: string) => {
    try {
      await disconnectPlatform(platform);
      // Refresh to confirm removal
      await fetchDashboard();
    } catch (err) {
      console.error('Disconnect failed:', err);
    }
  };

  const handleSync = async (platform: string) => {
    try {
      const result = await triggerSync(platform);
      if (result.sync_started) {
        // Refresh after short delay to show syncing state
        setTimeout(() => fetchDashboard(), 1000);
      }
      return result;
    } catch (err) {
      console.error('Sync trigger failed:', err);
      return null;
    }
  };

  const handleReauth = async (platform: string) => {
    try {
      const response = await fetch(`/api/v1/integrations/${encodeURIComponent(platform)}/reauth`);
      if (!response.ok) {
        throw new Error('Failed to get reauth URL');
      }
      const data = await response.json();
      // Redirect to OAuth
      window.location.href = data.authorize_url;
    } catch (err) {
      console.error('Reauth failed:', err);
    }
  };

  return {
    connectors,
    systemHealth,
    loading,
    error,
    lastUpdate,
    handleDisconnect,
    handleSync,
    handleReauth,
    clearErrors,
    refresh: fetchDashboard,
  };
}