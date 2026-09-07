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

// Agent roster (REST GET /api/v1/agents, v1.15.0)
export interface ActivitySummary {
  calls: number;
  last_active_at: string | null;
}

export interface AgentRosterEntry {
  name: string;
  model_tier: string;
  tools_allowed: string[];
  rule: boolean;
  custom: boolean;
  activity_summary: ActivitySummary | null;
}

// Agent activity detail (REST GET /api/v1/agents/{name}/activity, v1.15.0)
export interface AgentActivity {
  agent: string;
  calls: number;
  failures: number;
  last_action: string | null;
  last_active_at: string | null;
}

// Workflow execution (REST GET /api/v1/workflows, v1.15.0)
export interface WorkflowExecution {
  workflow_id: string;
  definition_name: string;
  name: string;
  workflow: string;
  status: 'running' | 'completed' | 'failed' | 'pending' | 'interrupted';
  steps_completed: number;
  steps_total: number;
  updated_at: string | null;
  finished_at: string | null;
}

export interface WorkflowListResponse {
  workflows: WorkflowExecution[];
  total: number;
}

// Workflow status detail (REST GET /api/v1/workflows/{id}/status, v1.15.0)
export interface WorkflowStep {
  name: string;
  agent: string;
  status: string;
}

export interface WorkflowStatusDetail {
  workflow_id: string;
  workflow: string;
  status: string;
  current_step: number;
  steps_total: number;
  steps: WorkflowStep[];
  started_at: string;
}
