import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../lib/api';
import type { DashboardConnector, DashboardResponse, ConnectorError, SyncTriggerResponse } from '../types/integrations';
import type { ConnectorHealthData, SyncProgressData } from '../types/websocket';

interface IntegrationsState {
  connectors: DashboardConnector[];
  systemHealth: DashboardResponse['system_health'] | null;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
  wsConnected: boolean;

  // Actions
  fetchDashboard: () => Promise<void>;
  disconnectPlatform: (platform: string) => Promise<void>;
  triggerSync: (platform: string) => Promise<SyncTriggerResponse>;
  getErrors: (platform: string) => Promise<ConnectorError[]>;
  clearErrors: () => void;
  // WebSocket actions
  updateConnectorHealth: (platform: string, data: ConnectorHealthData) => void;
  updateSyncProgress: (platform: string, data: SyncProgressData) => void;
  setWsConnected: (connected: boolean) => void;
}

const API_BASE = '/api/v1/integrations';

export const useIntegrationsStore = create<IntegrationsState>()(
  persist(
    (set, get) => ({
      connectors: [],
      systemHealth: null,
      loading: false,
      error: null,
      lastUpdate: null,
      wsConnected: false,

      fetchDashboard: async () => {
        set({ loading: true, error: null });
        try {
          const data = await api.get<DashboardResponse>(`${API_BASE}/dashboard`);
          set({
            connectors: data.connectors,
            systemHealth: data.system_health,
            loading: false,
            lastUpdate: new Date().toISOString(),
          });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : 'Failed to fetch dashboard',
            loading: false,
          });
        }
      },

      disconnectPlatform: async (platform: string) => {
        try {
          // api.delete sends no body by default; a 204 has no JSON body.
          await api.delete(`${API_BASE}/${encodeURIComponent(platform)}`);
          // Remove from local state
          const connectors = get().connectors.filter((c) => c.platform !== platform);
          set({ connectors });
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : 'Failed to disconnect platform',
          });
          throw err;
        }
      },

      triggerSync: async (platform: string): Promise<SyncTriggerResponse> => {
        try {
          const data = await api.post<SyncTriggerResponse>(
            `${API_BASE}/${encodeURIComponent(platform)}/sync`,
            {},
          );

          // Update connector state to syncing if started
          if (data.sync_started) {
            const connectors = get().connectors.map((c) =>
              c.platform === platform ? { ...c, sync_state: 'syncing' as const } : c
            );
            set({ connectors });
          }

          return data;
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : 'Failed to trigger sync',
          });
          throw err;
        }
      },

      getErrors: async (platform: string): Promise<ConnectorError[]> => {
        try {
          return await api.get<ConnectorError[]>(
            `${API_BASE}/${encodeURIComponent(platform)}/errors`,
          );
        } catch (err) {
          set({
            error: err instanceof Error ? err.message : 'Failed to fetch errors',
          });
          throw err;
        }
      },

      clearErrors: () => {
        set({ error: null });
      },

      // WebSocket actions for real-time updates
      updateConnectorHealth: (platform, data) => {
        set((state) => ({
          connectors: state.connectors.map((c) =>
            c.platform === platform
              ? {
                  ...c,
                  health_status: data.status,
                  last_error: data.last_error,
                  // Note: consecutive_failures not in DashboardConnector, but health_status reflects it
                }
              : c
          ),
          lastUpdate: new Date().toISOString(),
        }));
      },

      updateSyncProgress: (platform, data) => {
        set((state) => ({
          connectors: state.connectors.map((c) =>
            c.platform === platform
              ? {
                  ...c,
                  sync_state: data.state,
                  items_synced: data.items_synced,
                  // Note: items_total and completion_percent not in DashboardConnector
                  // but items_synced provides progress indication
                }
              : c
          ),
          lastUpdate: new Date().toISOString(),
        }));
      },

      setWsConnected: (connected) => {
        set({ wsConnected: connected });
      },
    }),
    {
      name: 'integrations-storage',
      partialize: (state) => ({
        lastUpdate: state.lastUpdate,
      }),
    }
  )
);
