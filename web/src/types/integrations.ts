/**
 * Integration Dashboard Types
 * Plan 15-01: Dashboard API and UI components
 */

export interface DashboardConnector {
  platform: string;
  health_status: 'healthy' | 'degraded' | 'unhealthy';
  last_sync_at: string | null;
  items_synced: number;
  error_count: number;
  is_connected: boolean;
  sync_direction: 'pull' | 'push' | 'bidirectional';
  sync_state: 'idle' | 'syncing' | 'paused' | 'error';
  last_error: string | null;
}

export interface DashboardResponse {
  connectors: DashboardConnector[];
  system_health: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    healthy_count: number;
    degraded_count: number;
    unhealthy_count: number;
  };
}

export interface ConnectorError {
  timestamp: string;
  error_message: string;
  error_type?: string;
}

export interface SyncTriggerResponse {
  platform: string;
  sync_started: boolean;
  message: string;
}

export interface ReauthResponse {
  platform: string;
  authorize_url: string;
  state: string;
}

// Platform icons and display names
export const PLATFORM_CONFIG: Record<string, { name: string; icon: string; color: string }> = {
  notion: { name: 'Notion', icon: 'notion', color: 'bg-gray-100' },
  logseq: { name: 'Logseq', icon: 'logseq', color: 'bg-purple-100' },
  slack: { name: 'Slack', icon: 'slack', color: 'bg-orange-100' },
  discord: { name: 'Discord', icon: 'discord', color: 'bg-indigo-100' },
  feishu: { name: 'Feishu', icon: 'feishu', color: 'bg-blue-100' },
  wecom: { name: 'WeCom', icon: 'wecom', color: 'bg-green-100' },
  github: { name: 'GitHub', icon: 'github', color: 'bg-gray-800' },
};
