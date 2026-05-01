export interface AuthConfig {
  apiToken: string;
  apiUrl: string;
}

export class AuthManager {
  private config: AuthConfig;
  private tokenExpiry: number | null = null;

  constructor(config: AuthConfig) {
    this.config = config;
  }

  getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Use API token directly as Bearer token
    if (this.config.apiToken) {
      headers['Authorization'] = `Bearer ${this.config.apiToken}`;
    }

    return headers;
  }

  updateConfig(config: Partial<AuthConfig>): void {
    this.config = { ...this.config, ...config };
  }

  isAuthenticated(): boolean {
    return !!this.config.apiToken;
  }
}