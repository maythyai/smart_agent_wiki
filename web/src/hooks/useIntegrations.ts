import { useEffect, useRef } from 'react';
import { useIntegrationsStore } from '../stores/integrationsStore';

/**
 * Hook for integration dashboard with automatic refresh.
 * Polls every 30 seconds when page is visible.
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

  const refreshIntervalRef = useRef<number | null>(null);

  // Initial fetch
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Auto-refresh every 30s when visible
  useEffect(() => {
    const startPolling = () => {
      refreshIntervalRef.current = window.setInterval(() => {
        if (document.visibilityState === 'visible') {
          fetchDashboard();
        }
      }, 30000);
    };

    const stopPolling = () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
    };

    // Start polling
    startPolling();

    // Handle visibility changes
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        fetchDashboard();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    return () => {
      stopPolling();
      document.removeEventListener('visibilitychange', handleVisibility);
    };
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