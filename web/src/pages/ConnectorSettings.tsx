import { useParams, useNavigate } from 'react-router';
import { useState, useEffect } from 'react';
import { useConnectorSettings } from '../hooks/useConnectorSettings';
import { SyncConfigSection } from '../components/settings/SyncConfigSection';
import { PropertyMappingEditor } from '../components/settings/PropertyMappingEditor';
import { OAuthStatusSection, getOAuthStatus } from '../components/settings/OAuthStatusSection';
import { Button } from '../components/ui/Button';
import { PLATFORM_CONFIG } from '../types/integrations';

// Platforms that use OAuth (vs local file or webhook)
const OAUTH_PLATFORMS = ['notion', 'slack', 'github', 'feishu'];

// Platforms that support property mapping
const MAPPING_PLATFORMS = ['notion', 'logseq'];

/**
 * Connector Settings page.
 * Per CONF-01: Accessible from Integration Dashboard.
 * Per UI-SPEC.md: Settings page layout with sync config, property mapping, OAuth status.
 */
export default function ConnectorSettings() {
  const { platform } = useParams<{ platform: string }>();
  const navigate = useNavigate();

  // Local state for form values (before saving)
  const [syncInterval, setSyncInterval] = useState<string>('15min');
  const [syncDirection, setSyncDirection] = useState<string>('bidirectional');
  const [propertyMappings, setPropertyMappings] = useState<Record<string, string>>({});

  // Fetch settings from API
  const {
    settings,
    loading,
    error,
    saving,
    saved,
    updateSettings,
    reauthorize,
    resetToDefaults,
    clearError,
  } = useConnectorSettings(platform || '');

  // Sync local state with fetched settings
  useEffect(() => {
    if (settings) {
      setSyncInterval(settings.sync_interval);
      setSyncDirection(settings.sync_directions);
      setPropertyMappings(settings.property_mappings || {});
    }
  }, [settings]);

  // Platform config for display
  const config = PLATFORM_CONFIG[platform || ''] || {
    name: platform || 'Unknown',
    icon: platform || 'default',
    color: 'bg-gray-100',
  };

  // Handlers
  const handleSave = async () => {
    await updateSettings({
      sync_interval: syncInterval as '5min' | '15min' | '1hr' | '6hr' | 'manual',
      sync_directions: syncDirection as 'inbound_only' | 'outbound_only' | 'bidirectional',
      property_mappings: propertyMappings,
    });
  };

  const handleMappingChange = (field: string, property: string) => {
    setPropertyMappings((prev) => ({
      ...prev,
      [field]: property,
    }));
  };

  const handleAddMapping = (field: string, property: string) => {
    setPropertyMappings((prev) => ({
      ...prev,
      [field]: property,
    }));
  };

  const handleReset = async () => {
    setSyncInterval('15min');
    setSyncDirection('bidirectional');
    setPropertyMappings({});
    await resetToDefaults();
  };

  // Mock OAuth status for demo (in real app, would come from connector config)
  const oauthStatus = getOAuthStatus(null); // Default to expired for demo

  // Loading skeleton
  if (loading && !settings) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-24 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header with back button */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/integrations')}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Integrations
        </button>

        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
          {config.name} Settings
        </h1>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-red-700">{error}</span>
          </div>
          <button
            onClick={clearError}
            className="text-red-500 hover:text-red-700 p-1"
            aria-label="Dismiss error"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Success indicator */}
      {saved && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-sm text-green-700">Settings saved successfully!</span>
        </div>
      )}

      {/* Settings sections */}
      <div className="space-y-6">
        {/* Sync Configuration */}
        <SyncConfigSection
          syncInterval={syncInterval}
          syncDirection={syncDirection}
          onIntervalChange={setSyncInterval}
          onDirectionChange={setSyncDirection}
          disabled={saving}
        />

        {/* Property Mappings (only for Notion/Logseq) */}
        {platform && MAPPING_PLATFORMS.includes(platform) && (
          <PropertyMappingEditor
            platform={platform}
            mappings={propertyMappings}
            onMappingChange={handleMappingChange}
            onAddMapping={handleAddMapping}
            disabled={saving}
          />
        )}

        {/* OAuth Status (only for OAuth platforms) */}
        {platform && OAUTH_PLATFORMS.includes(platform) && (
          <OAuthStatusSection
            status={oauthStatus.status}
            expiresInDays={oauthStatus.expiresInDays}
            onReauthorize={reauthorize}
            loading={saving}
          />
        )}
      </div>

      {/* Action buttons */}
      <div className="mt-6 flex flex-col sm:flex-row gap-3">
        <Button
          variant="primary"
          size="md"
          loading={saving}
          onClick={handleSave}
          className="w-full sm:w-auto"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </Button>

        <Button
          variant="secondary"
          size="md"
          disabled={saving}
          onClick={handleReset}
          className="w-full sm:w-auto"
        >
          Reset to Defaults
        </Button>
      </div>

      {/* Last updated */}
      {settings?.updated_at && (
        <p className="mt-4 text-xs text-gray-400">
          Last updated: {new Date(settings.updated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}