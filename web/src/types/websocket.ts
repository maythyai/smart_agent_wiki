// WebSocket message types (matching backend websocket.py)

export type WSMessageType = 'agent_status' | 'workflow_progress' | 'page_updated' | 'ping' | 'pong';

export interface WSMessage {
  type: WSMessageType;
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface AgentStatus {
  agent: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  task: string | null;
  progress: number;
}

export interface WorkflowProgress {
  workflow_id: string;
  step: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration_ms: number;
}

export interface PageUpdatedEvent {
  slug: string;
  updated_at: string;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

// Integration WebSocket types (matching backend integrations_ws.py)
export type IntegrationWSMessageType = 'connector_health' | 'sync_progress' | 'connection_status' | 'ping' | 'subscribed' | 'unsubscribed';

export interface IntegrationWSMessage {
  type: IntegrationWSMessageType;
  platform?: string;
  data?: ConnectorHealthData | SyncProgressData | ConnectionStatusData;
}

export interface ConnectorHealthData {
  status: 'healthy' | 'degraded' | 'unhealthy';
  last_success_at: string | null;
  last_failure_at: string | null;
  consecutive_failures: number;
  last_error: string | null;
}

export interface SyncProgressData {
  state: 'idle' | 'syncing' | 'paused' | 'error';
  items_synced: number;
  items_total: number;
  completion_percent: number;
  last_error: string | null;
}

export interface ConnectionStatusData {
  connected: boolean;
  client_id?: string;
  server_time?: string;
}