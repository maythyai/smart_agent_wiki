import type { ReactNode } from 'react';
import type { DashboardConnector } from '../../types/integrations';
import { PLATFORM_CONFIG } from '../../types/integrations';
import { IntegrationActions } from './IntegrationActions';

interface IntegrationCardProps {
  connector: DashboardConnector;
  onDisconnect: (platform: string) => void;
  onSync: (platform: string) => void;
  onReauth: (platform: string) => void;
}

// Health indicator colors
const healthColors: Record<string, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  unhealthy: 'bg-red-500',
};

// Sync state badge colors
const syncStateColors: Record<string, string> = {
  idle: 'bg-gray-100 text-gray-600',
  syncing: 'bg-blue-100 text-blue-700 animate-pulse',
  paused: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
};

// Format relative time
function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return 'Never';

  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

// Platform icon component
function PlatformIcon({ platform }: { platform: string }) {
  const config = PLATFORM_CONFIG[platform];
  const icon = config?.icon || platform;

  // Simple SVG icons for each platform
  const icons: Record<string, ReactNode> = {
    notion: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path fill="currentColor" d="M4.459 4.217c.103-.115.26-.174.409-.174l12.28.003c.15 0 .306.059.41.174.093.106.137.245.137.384v12.274c0 .139-.044.278-.137.384-.104.115-.26.174-.41.174H4.868c-.15 0-.306-.059-.409-.174-.094-.106-.138-.245-.138-.384V4.601c0-.139.044-.278.138-.384zm5.4 8.34l4.006-4.005-1.414-1.414-2.592 2.592-1.172-1.172-1.414 1.414 2.586 2.585z"/>
      </svg>
    ),
    slack: (
      <svg viewBox="0 0 24 24" className="w-8 h-8">
        <path fill="#E01E5A" d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313z"/>
        <path fill="#36C5F0" d="M8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312z"/>
        <path fill="#2EB67D" d="M18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312z"/>
        <path fill="#ECB22E" d="M15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
      </svg>
    ),
    discord: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="#5865F2">
        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>
      </svg>
    ),
    github: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
        <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
      </svg>
    ),
    logseq: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="#85C8C8">
        <circle cx="12" cy="12" r="10"/>
      </svg>
    ),
    feishu: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="#3370FF">
        <rect x="4" y="4" width="16" height="16" rx="2"/>
      </svg>
    ),
    wecom: (
      <svg viewBox="0 0 24 24" className="w-8 h-8" fill="#0082EF">
        <circle cx="12" cy="12" r="10"/>
      </svg>
    ),
  };

  return icons[icon] || (
    <div className="w-8 h-8 bg-gray-200 rounded flex items-center justify-center text-gray-500 text-xs">
      {platform.slice(0, 2).toUpperCase()}
    </div>
  );
}

/**
 * IntegrationCard displays per-connector status with:
 * - Platform icon and name
 * - Health indicator (color dot)
 * - Connection status badge
 * - Last sync time, items synced count, error count
 * - Action buttons (disconnect, sync, reauthorize)
 */
export function IntegrationCard({
  connector,
  onDisconnect,
  onSync,
  onReauth,
}: IntegrationCardProps) {
  const config = PLATFORM_CONFIG[connector.platform] || {
    name: connector.platform,
    icon: connector.platform,
    color: 'bg-gray-100',
  };

  const needsReauth = connector.health_status === 'unhealthy' &&
    connector.last_error?.toLowerCase().includes('token');

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Header: Platform icon + name + health dot */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`${config.color} p-2 rounded-lg`}>
            <PlatformIcon platform={connector.platform} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{config.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              {/* Health indicator */}
              <span
                className={`w-2 h-2 rounded-full ${healthColors[connector.health_status]}`}
                title={`Health: ${connector.health_status}`}
              />
              {/* Sync state badge */}
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${syncStateColors[connector.sync_state]}`}
              >
                {connector.sync_state}
              </span>
            </div>
          </div>
        </div>

        {/* Connection status */}
        {connector.is_connected ? (
          <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
            Connected
          </span>
        ) : (
          <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
            Disconnected
          </span>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-center">
        <div>
          <p className="text-xs text-gray-500">Last Sync</p>
          <p className="text-sm font-medium text-gray-900">
            {formatRelativeTime(connector.last_sync_at)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Items</p>
          <p className="text-sm font-medium text-gray-900">
            {connector.items_synced.toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Errors</p>
          <p className={`text-sm font-medium ${connector.error_count > 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {connector.error_count}
          </p>
        </div>
      </div>

      {/* Last error (if any) */}
      {connector.last_error && (
        <div className="mb-3 p-2 bg-red-50 rounded text-xs text-red-700 truncate" title={connector.last_error}>
          {connector.last_error}
        </div>
      )}

      {/* Actions */}
      <IntegrationActions
        platform={connector.platform}
        is_connected={connector.is_connected}
        sync_state={connector.sync_state}
        needsReauth={needsReauth}
        onDisconnect={onDisconnect}
        onSync={onSync}
        onReauth={onReauth}
      />
    </div>
  );
}
