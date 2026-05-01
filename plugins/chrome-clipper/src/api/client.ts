/**
 * SAW REST API Client
 *
 * Implements communication with SAW backend endpoints.
 * Endpoints match CONTEXT.md specification (lines 452-456).
 *
 * Per Pitfall 29: CORS must be configured on server for extension origin.
 */

import { AuthManager, AuthConfig } from './auth';
import type {
  ClippedContent,
  ClipResponse,
  TagSuggestionResponse,
} from '../types';

export interface IngestResponse {
  status: string;
  id: string;
  vault_id?: string;
}

export interface AuthVerifyResponse {
  valid: boolean;
  user_id?: string;
  expires_at?: string;
}

export class APIClient {
  private authManager: AuthManager;
  private baseUrl: string;

  constructor(config: AuthConfig) {
    this.authManager = new AuthManager(config);
    this.baseUrl = config.apiUrl;
  }

  /**
   * Make API request with error handling
   */
  async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
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

    // Handle empty responses
    const text = await response.text();
    if (!text) {
      return {} as T;
    }

    return JSON.parse(text) as T;
  }

  /**
   * POST /api/v1/ingest/web — Clip web page content
   */
  async clipPage(content: ClippedContent): Promise<IngestResponse> {
    return this.request<IngestResponse>('POST', '/api/v1/ingest/web', {
      url: content.url,
      title: content.title,
      content: content.content,
      text_content: content.textContent,
      tags: content.tags,
      notes: content.notes,
      source: content.source,
      clipped_at: content.clippedAt,
    });
  }

  /**
   * POST /api/v1/tags/suggest — Suggest tags for content
   */
  async getTagSuggestions(textContent: string): Promise<TagSuggestionResponse> {
    return this.request<TagSuggestionResponse>(
      'POST',
      '/api/v1/tags/suggest',
      {
        content: textContent.slice(0, 1000), // Limit to first 1000 chars
      }
    );
  }

  /**
   * GET /api/v1/auth/verify — Verify API key validity
   */
  async verifyAuth(): Promise<boolean> {
    try {
      await this.request('GET', '/api/v1/auth/verify');
      return true;
    } catch {
      return false;
    }
  }

  /**
   * GET /api/health — Health check (no auth required)
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<AuthConfig>): void {
    this.authManager.updateConfig(config);
    if (config.apiUrl) {
      this.baseUrl = config.apiUrl;
    }
  }

  /**
   * Check if authenticated
   */
  isAuthenticated(): boolean {
    return this.authManager.isAuthenticated();
  }
}

// Singleton instance
let apiClientInstance: APIClient | null = null;

/**
 * Get API client singleton
 */
export function getAPIClient(config?: AuthConfig): APIClient {
  if (!apiClientInstance && config) {
    apiClientInstance = new APIClient(config);
  }
  if (!apiClientInstance) {
    throw new Error('API client not initialized. Call getAPIClient with config first.');
  }
  return apiClientInstance;
}

/**
 * Reset API client singleton (for testing)
 */
export function resetAPIClient(): void {
  apiClientInstance = null;
}
