import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntegrationList } from '../IntegrationList';
import type { DashboardConnector } from '../../../types/integrations';

// Mock IntegrationCard to simplify tests
vi.mock('../IntegrationCard', () => ({
  IntegrationCard: ({ connector }: { connector: DashboardConnector }) => (
    <div data-testid={`card-${connector.platform}`}>
      {connector.platform} - {connector.health_status}
    </div>
  ),
}));

const mockConnectors: DashboardConnector[] = [
  {
    platform: 'notion',
    health_status: 'healthy',
    last_sync_at: '2026-05-03T10:00:00Z',
    items_synced: 42,
    error_count: 0,
    is_connected: true,
    sync_direction: 'bidirectional',
    sync_state: 'idle',
    last_error: null,
  },
  {
    platform: 'slack',
    health_status: 'unhealthy',
    last_sync_at: '2026-05-03T09:00:00Z',
    items_synced: 100,
    error_count: 5,
    is_connected: true,
    sync_direction: 'pull',
    sync_state: 'error',
    last_error: 'Connection failed',
  },
  {
    platform: 'github',
    health_status: 'degraded',
    last_sync_at: '2026-05-03T08:00:00Z',
    items_synced: 25,
    error_count: 1,
    is_connected: true,
    sync_direction: 'bidirectional',
    sync_state: 'paused',
    last_error: null,
  },
];

describe('IntegrationList', () => {
  it('renders list of connectors', () => {
    render(
      <IntegrationList
        connectors={mockConnectors}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    expect(screen.getByTestId('card-notion')).toBeInTheDocument();
    expect(screen.getByTestId('card-slack')).toBeInTheDocument();
    expect(screen.getByTestId('card-github')).toBeInTheDocument();
  });

  it('sorts connectors by health status (unhealthy first)', () => {
    render(
      <IntegrationList
        connectors={mockConnectors}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    const cards = screen.getAllByTestId(/card-/);
    // unhealthy (slack) should be first
    expect(cards[0]).toHaveTextContent('slack');
    // degraded (github) should be second
    expect(cards[1]).toHaveTextContent('github');
    // healthy (notion) should be last
    expect(cards[2]).toHaveTextContent('notion');
  });

  it('shows empty state when no connectors', () => {
    render(
      <IntegrationList
        connectors={[]}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    expect(screen.getByText('No Integrations')).toBeInTheDocument();
    expect(screen.getByText('Connect platforms to sync your knowledge base')).toBeInTheDocument();
  });
});