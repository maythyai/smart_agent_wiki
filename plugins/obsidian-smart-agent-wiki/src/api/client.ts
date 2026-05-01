import { AuthManager, AuthConfig } from './auth';
import { PageResponse, GraphResponse } from '../types';

export interface SyncStatusResponse {
  path: string;
  local_mtime: number;
  remote_mtime: string;
  status: 'in-sync' | 'local-ahead' | 'remote-ahead' | 'conflict';
}

export interface PageListResponse {
  slugs: string[];
  total: number;
}

export interface SyncBatchRequest {
  files: Array<{
    path: string;
    content: string;
    modified_at: string;
  }>;
}

export interface IngestRequest {
  path: string;
  content: string;
  title: string;
  tags: string[];
  type: string;
  force: boolean;
}

export interface IngestResponse {
  status: string;
  id: string;
}

export class APIClient {
  private authManager: AuthManager;
  private baseUrl: string;

  constructor(config: AuthConfig) {
    this.authManager = new AuthManager(config);
    this.baseUrl = config.apiUrl;
  }

  async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const headers = this.authManager.getAuthHeaders();

    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Page operations
  async listPages(): Promise<PageListResponse> {
    return this.request<PageListResponse>('GET', '/api/pages');
  }

  async getPage(slug: string): Promise<PageResponse> {
    return this.request<PageResponse>('GET', `/api/pages/${slug}`);
  }

  async updatePage(slug: string, content: string, message?: string): Promise<{ status: string; op_id: string }> {
    return this.request('PUT', `/api/pages/${slug}`, { content, message });
  }

  async createPage(slug: string, title: string, content: string): Promise<{ status: string; op_id: string }> {
    return this.request('POST', '/api/pages', { slug, title, content });
  }

  // Sync operations
  async getSyncStatus(path: string, localMtime: number): Promise<SyncStatusResponse> {
    const params = new URLSearchParams({
      path,
      local_mtime: String(localMtime),
    });
    return this.request<SyncStatusResponse>('GET', `/api/v1/sync/status?${params}`);
  }

  async batchSync(files: SyncBatchRequest['files']): Promise<{ results: SyncStatusResponse[] }> {
    return this.request('POST', '/api/v1/sync/batch', { files });
  }

  // Graph operations
  async getGraph(depth: number = 2, maxNodes: number = 50): Promise<GraphResponse> {
    const params = new URLSearchParams({
      depth: String(depth),
      max_nodes: String(maxNodes),
    });
    return this.request<GraphResponse>('GET', `/api/graph?${params}`);
  }

  // Query operations
  async search(query: string, page: number = 1): Promise<{
    results: Array<{
      slug: string;
      title: string;
      snippet: string;
      confidence: number;
      score: number;
    }>;
    total: number;
  }> {
    const params = new URLSearchParams({
      q: query,
      page: String(page),
    });
    return this.request('GET', `/api/search?${params}`);
  }

  // Ingest operation - public method
  async ingestFile(request: IngestRequest): Promise<IngestResponse> {
    return this.request<IngestResponse>('POST', '/api/v1/ingest', request);
  }

  // Config update
  updateConfig(config: Partial<AuthConfig>): void {
    this.authManager.updateConfig(config);
    if (config.apiUrl) {
      this.baseUrl = config.apiUrl;
    }
  }
}