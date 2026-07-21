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
  entity_type: string;
  properties: Record<string, unknown>;
}

export interface PageUpdate {
  content: string;
  message?: string;
  entity_type?: string;
  properties?: Record<string, unknown>;
}

export interface PageCreate {
  slug: string;
  title: string;
  content: string;
  tags?: string[];
  type?: string;
  entity_type?: string;
  properties?: Record<string, unknown>;
}

export interface PageStatus {
  status: string;
  slug: string;
  op_id?: string;
}

export interface PageListResponse {
  pages: PageResponse[];
  slugs: string[];
  total: number;
}

// Quick Capture types
export interface QuickCaptureRequest {
  title: string;
  content?: string;
  tags?: string[];
}

export interface QuickCaptureResponse {
  slug: string;
  title: string;
  status: string;
}

// Entity Type types
export interface EntityField {
  name: string;
  field_type: string;
  required: boolean;
  description: string;
  options: string[];
}

export interface EntityType {
  id: string;
  name: string;
  icon: string;
  description: string;
  fields: EntityField[];
  color: string;
}

// Related Pages types
export interface RelatedPage {
  slug: string;
  title: string;
  score: number;
  reasons: string[];
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
