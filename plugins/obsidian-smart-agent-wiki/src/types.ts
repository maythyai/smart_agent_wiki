// Plugin settings interface
export interface SAWPluginSettings {
  apiUrl: string;
  apiToken: string;
  syncInterval: number;
  lastSync: Record<string, string>;
  autoSync: boolean;
  conflictStrategy: 'prefer-local' | 'prefer-remote' | 'create-conflict';
  lastQuery?: string;
}

export const DEFAULT_SETTINGS: SAWPluginSettings = {
  apiUrl: 'http://localhost:8000',
  apiToken: '',
  syncInterval: 300000,
  lastSync: {},
  autoSync: true,
  conflictStrategy: 'create-conflict',
  lastQuery: '',
};

// Sync status
export interface SyncStatus {
  path: string;
  local_mtime: number;
  remote_mtime: string;
  status: 'in-sync' | 'local-ahead' | 'remote-ahead' | 'conflict';
}

// API types (matching backend)
export interface PageResponse {
  slug: string;
  title: string;
  content: string;
  frontmatter: Record<string, unknown>;
  confidence: number;
  freshness: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  confidence: number;
  description?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}
