import type { DashboardConnector } from '../../types/integrations';
import { IntegrationCard } from './IntegrationCard';

interface IntegrationListProps {
  connectors: DashboardConnector[];
  onDisconnect: (platform: string) => void;
  onSync: (platform: string) => void;
  onReauth: (platform: string) => void;
}

/**
 * Sort connectors by health status:
 * unhealthy first, then degraded, then healthy
 */
function sortConnectors(connectors: DashboardConnector[]): DashboardConnector[] {
  const healthOrder = { unhealthy: 0, degraded: 1, healthy: 2 };
  return [...connectors].sort((a, b) => {
    return (healthOrder[a.health_status] ?? 2) - (healthOrder[b.health_status] ?? 2);
  });
}

/**
 * IntegrationList displays connector cards in a responsive grid.
 * - 3 columns on desktop (lg)
 * - 2 columns on tablet (md)
 * - 1 column on mobile
 */
export function IntegrationList({
  connectors,
  onDisconnect,
  onSync,
  onReauth,
}: IntegrationListProps) {
  const sortedConnectors = sortConnectors(connectors);

  if (connectors.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 sm:p-8 text-center">
        <div className="text-gray-400 mb-3">
          <svg className="w-10 h-10 sm:w-12 sm:h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
        </div>
        <h3 className="text-base sm:text-lg font-medium text-gray-600 mb-1">No Integrations</h3>
        <p className="text-sm text-gray-500">
          Connect platforms to sync your knowledge base
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      {sortedConnectors.map((connector) => (
        <IntegrationCard
          key={connector.platform}
          connector={connector}
          onDisconnect={onDisconnect}
          onSync={onSync}
          onReauth={onReauth}
        />
      ))}
    </div>
  );
}