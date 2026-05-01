/**
 * Authentication Manager for SAW API
 *
 * Handles API token management and authentication headers.
 * Per Pitfall 29: Server must be configured for extension origin in CORS.
 */

export interface AuthConfig {
  apiUrl: string;
  apiToken: string;
}

export class AuthManager {
  private config: AuthConfig;

  constructor(config: AuthConfig) {
    this.config = config;
  }

  /**
   * Get authentication headers for API requests
   */
  getAuthHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${this.config.apiToken}`,
    };
  }

  /**
   * Update authentication configuration
   */
  updateConfig(config: Partial<AuthConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration
   */
  getConfig(): AuthConfig {
    return { ...this.config };
  }

  /**
   * Check if authentication is configured
   */
  isAuthenticated(): boolean {
    return Boolean(
      this.config.apiToken && this.config.apiToken.length > 0
    );
  }

  /**
   * Get API URL
   */
  getApiUrl(): string {
    return this.config.apiUrl;
  }
}
