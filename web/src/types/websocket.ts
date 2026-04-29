// WebSocket message types (matching backend websocket.py)

export type WSMessageType = 'agent_status' | 'workflow_progress' | 'page_updated' | 'ping' | 'pong';

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
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