import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DashboardConnector, DashboardResponse, ConnectorError, SyncTriggerResponse } from '../types/integrations';

interface IntegrationsState {
  connectors: DashboardConnector[];
  systemHealth: DashboardResponse['system_health'] | null;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;

  // Actions
  fetchDashboard: () => Promise<void>;
  disconnectPlatform: (platform: string) => Promise<void>;
  triggerSync: (platform: string) => Promise<SyncTriggerResponse>;
  getErrors: (platform: string) => Promise<ConnectorError[]>;
  clearErrors: () => void;
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

      fetchDashboard: async () => {
        set({ loading: true, error: null });
        try {
          const response = await fetch(`${API_BASE}/dashboard`);
          if (!response.ok) {
            throw new Error(`Failed to fetch dashboard: ${response.statusText}`);
          }
          const data: DashboardResponse = await response.json();
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
          const response = await fetch(`${API_BASE}/${encodeURIComponent(platform)}`, {
            method: 'DELETE',
          });
          if (!response.ok && response.status !== 204) {
            throw new Error(`Failed to disconnect: ${response.statusText}`);
          }
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
          const response = await fetch(`${API_BASE}/${encodeURIComponent(platform)}/sync`, {
            method: 'POST',
          });
          if (!response.ok) {
            throw new Error(`Failed to trigger sync: ${response.statusText}`);
          }
          const data: SyncTriggerResponse = await response.json();

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
          const response = await fetch(`${API_BASE}/${encodeURIComponent(platform)}/errors`);
          if (!response.ok) {
            throw new Error(`Failed to fetch errors: ${response.statusText}`);
          }
          return await response.json();
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
    }),
    {
      name: 'integrations-storage',
      partialize: (state) => ({
        lastUpdate: state.lastUpdate,
      }),
    }
  )
);
