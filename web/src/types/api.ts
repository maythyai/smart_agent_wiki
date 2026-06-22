// Search API types (matching backend schemas/search.py)
export interface SearchResult {
  slug: string;
  title: string;
  snippet: string;
  confidence: number;  // 1-4
  freshness: number;   // 0-8
  citations: string[];
  score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface SearchParams {
  q: string;
  page?: number;
  per_page?: number;
  type?: string;
  tag?: string;
  min_confidence?: number;
}

// Graph API types (matching backend schemas/graph.py)
export type TraversalMode = 'bfs' | 'dfs';

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

export interface GraphParams {
  depth?: number;
  mode?: TraversalMode;
  type?: string;
  max_nodes?: number;
}

// Page API types (matching backend schemas/pages.py)
export interface PageResponse {
  slug: string;
  title: string;
  content: string;
  frontmatter: Record<string, unknown>;
  confidence: number;
  freshness: number;
}

export interface PageUpdate {
  content: string;
  message?: string;
}

export interface PageCreate {
  slug: string;
  title: string;
  content: string;
  tags?: string[];
  type?: string;
}

export interface PageStatus {
  status: string;
  slug: string;
  op_id?: string;
}

export interface PageListResponse {
  slugs: string[];
  total: number;
}

// WebSocket types - re-exported from shared websocket types
export type { WSMessageType, WSMessage } from './websocket';

// Agent status types
export interface AgentStatus {
  agent: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  task?: string;
  progress?: number;
}

export interface WorkflowProgress {
  workflow_id: string;
  step: string;
  total_steps: number;
  current_step: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
}
