import { Button } from '../ui/Button';

interface IntegrationActionsProps {
  platform: string;
  is_connected: boolean;
  sync_state: string;
  needsReauth?: boolean;
  onDisconnect: (platform: string) => void;
  onSync: (platform: string) => void;
  onReauth: (platform: string) => void;
}

/**
 * Action buttons for integration card:
 * - Disconnect (danger, only when connected)
 * - Sync Now (primary, triggers manual sync)
 * - Re-authorize (secondary, only when OAuth expired)
 * - View Details (ghost, link to detail page)
 *
 * Mobile behavior (per D-10):
 * - Buttons are full-width on mobile in expanded view
 * - Touch targets are minimum 44x44px (handled by Button component)
 * - Proper spacing between buttons
 */
export function IntegrationActions({
  platform,
  is_connected,
  sync_state,
  needsReauth = false,
  onDisconnect,
  onSync,
  onReauth,
}: IntegrationActionsProps) {
  const isSyncing = sync_state === 'syncing';

  return (
    <div className="flex flex-col sm:flex-row gap-2">
      {/* Sync Now button */}
      {is_connected && (
        <Button
          variant="primary"
          size="sm"
          loading={isSyncing}
          disabled={isSyncing}
          onClick={() => onSync(platform)}
          className="w-full sm:w-auto"
        >
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </Button>
      )}

      {/* Re-authorize button */}
      {needsReauth && (
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onReauth(platform)}
          className="w-full sm:w-auto"
        >
          Re-authorize
        </Button>
      )}

      {/* Disconnect button */}
      {is_connected && (
        <Button
          variant="danger"
          size="sm"
          onClick={() => onDisconnect(platform)}
          className="w-full sm:w-auto"
        >
          Disconnect
        </Button>
      )}

      {/* View Details link */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          // Navigate to detail page (future implementation)
          window.location.href = `/integrations/${platform}`;
        }}
        className="w-full sm:w-auto"
      >
        Details
      </Button>
    </div>
  );
}