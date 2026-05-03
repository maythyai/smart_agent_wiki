import { useState, useEffect, useCallback } from 'react';

/**
 * Settings response from API
 */
interface SettingsResponse {
  platform: string;
  sync_interval: '5min' | '15min' | '1hr' | '6hr' | 'manual';
  sync_directions: 'inbound_only' | 'outbound_only' | 'bidirectional';
  property_mappings: Record<string, string>;
  rate_limit_override: number | null;
  updated_at: string;
}

/**
 * Settings update request
 */
interface SettingsUpdateRequest {
  sync_interval?: '5min' | '15min' | '1hr' | '6hr' | 'manual';
  sync_directions?: 'inbound_only' | 'outbound_only' | 'bidirectional';
  property_mappings?: Record<string, string>;
  rate_limit_override?: number | null;
}

/**
 * Reauth response from API
 */
interface ReauthResponse {
  platform: string;
  authorize_url: string;
  state: string;
}

const API_BASE = '/api/v1/connectors';

/**
 * Hook for fetching and mutating connector settings.
 * Per D-04-D-06: Settings API endpoints for sync configuration, property mapping, OAuth reauth.
 */
export function useConnectorSettings(platform: string) {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, [platform]);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/${encodeURIComponent(platform)}/settings`);
      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }
      const data: SettingsResponse = await response.json();
      setSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch settings');
    } finally {
      setLoading(false);
    }
  }, [platform]);

  const updateSettings = useCallback(async (update: SettingsUpdateRequest) => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const response = await fetch(`${API_BASE}/${encodeURIComponent(platform)}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to update settings: ${response.statusText}`);
      }
      const data: SettingsResponse = await response.json();
      setSettings(data);
      setSaved(true);
      // Clear saved indicator after 2 seconds
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  }, [platform]);

  const reauthorize = useCallback(async () => {
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/${encodeURIComponent(platform)}/reauth`, {
        method: 'POST',
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to get reauth URL: ${response.statusText}`);
      }
      const data: ReauthResponse = await response.json();
      // Redirect to OAuth authorization URL
      window.location.href = data.authorize_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initiate re-authorization');
    }
  }, [platform]);

  const resetToDefaults = useCallback(async () => {
    await updateSettings({
      sync_interval: '15min',
      sync_directions: 'bidirectional',
      property_mappings: {},
      rate_limit_override: null,
    });
  }, [updateSettings]);

  return {
    settings,
    loading,
    error,
    saving,
    saved,
    updateSettings,
    reauthorize,
    resetToDefaults,
    refresh: fetchSettings,
    clearError: () => setError(null),
  };
}