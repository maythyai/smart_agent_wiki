import { useEffect, useRef } from 'react';
import type { DashboardConnector } from '../../types/integrations';
import { PLATFORM_CONFIG } from '../../types/integrations';
import { IntegrationActions } from './IntegrationActions';
import { PlatformIcon, healthColors, formatRelativeTime } from './IntegrationCard';

interface IntegrationCardExpandedProps {
  connector: DashboardConnector;
  onClose: () => void;
  onDisconnect: (platform: string) => void;
  onSync: (platform: string) => void;
  onReauth: (platform: string) => void;
}

/**
 * IntegrationCardExpanded provides a mobile-friendly expanded view
 * using a bottom sheet pattern with:
 * - Slide-up animation from bottom
 * - Swipe down to dismiss gesture
 * - Backdrop overlay for dismissal
 * - Full connector details and actions
 */
export function IntegrationCardExpanded({
  connector,
  onClose,
  onDisconnect,
  onSync,
  onReauth,
}: IntegrationCardExpandedProps) {
  const config = PLATFORM_CONFIG[connector.platform] || {
    name: connector.platform,
    icon: connector.platform,
    color: 'bg-gray-100',
  };

  const sheetRef = useRef<HTMLDivElement>(null);
  const needsReauth = connector.health_status === 'unhealthy' &&
    connector.last_error?.toLowerCase().includes('token');
  const isSyncing = connector.sync_state === 'syncing';

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  // Swipe down to dismiss gesture
  useEffect(() => {
    if (!sheetRef.current) return;

    let startY = 0;
    const handleTouchStart = (e: TouchEvent) => {
      startY = e.touches[0].clientY;
    };
    const handleTouchEnd = (e: TouchEvent) => {
      const diff = e.changedTouches[0].clientY - startY;
      if (diff > 100) onClose(); // Swipe down threshold
    };

    const sheet = sheetRef.current;
    sheet.addEventListener('touchstart', handleTouchStart);
    sheet.addEventListener('touchend', handleTouchEnd);
    return () => {
      sheet.removeEventListener('touchstart', handleTouchStart);
      sheet.removeEventListener('touchend', handleTouchEnd);
    };
  }, [onClose]);

  return (
    <>
      {/* Backdrop overlay - mobile only */}
      <div
        className="fixed inset-0 bg-black/50 z-40 md:hidden animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Bottom sheet - mobile only */}
      <div
        ref={sheetRef}
        className={`
          fixed z-50 bg-white shadow-xl
          md:hidden
          bottom-0 left-0 right-0
          rounded-t-2xl
          max-h-[90vh] overflow-y-auto
          animate-slide-up
        `}
        role="dialog"
        aria-modal="true"
        aria-labelledby="expanded-card-title"
      >
        {/* Drag indicator handle */}
        <div className="flex justify-center py-2">
          <div className="w-10 h-1 bg-gray-300 rounded-full" />
        </div>

        {/* Header with platform info */}
        <div className="px-4 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`${config.color} p-2 rounded-lg`}>
              <PlatformIcon platform={connector.platform} />
            </div>
            <div>
              <h3 id="expanded-card-title" className="text-lg font-semibold text-gray-900">
                {config.name}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`w-2 h-2 rounded-full ${healthColors[connector.health_status]}`}
                  title={`Health: ${connector.health_status}`}
                />
                <span className="text-sm text-gray-600 capitalize">
                  {connector.health_status}
                </span>
              </div>
            </div>
          </div>
          {/* Close button with touch-friendly sizing */}
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 touch-manipulation flex items-center justify-center"
            aria-label="Close expanded card"
            style={{ minWidth: '44px', minHeight: '44px' }}
          >
            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Connection status badge */}
        {connector.is_connected ? (
          <div className="px-4 pb-3">
            <span className="text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
              Connected
            </span>
          </div>
        ) : (
          <div className="px-4 pb-3">
            <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
              Disconnected
            </span>
          </div>
        )}

        {/* Sync progress bar (only when syncing) */}
        {isSyncing && (
          <div className="px-4 pb-3">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Syncing...</span>
              <span>{connector.items_synced.toLocaleString()} items</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500 animate-pulse"
                style={{ width: '60%' }}
              />
            </div>
          </div>
        )}

        {/* Stats grid */}
        <div className="px-4 py-3 border-t border-gray-100">
          <div className="grid grid-cols-3 gap-4 text-center">
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
        </div>

        {/* Last error message (if any) */}
        {connector.last_error && (
          <div className="px-4 pb-3">
            <div className="p-3 bg-red-50 rounded-lg text-sm text-red-700">
              {connector.last_error}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="px-4 py-4 border-t border-gray-100">
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
      </div>
    </>
  );
}