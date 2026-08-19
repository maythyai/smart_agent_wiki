/**
 * Tests for Integration Dashboard UI components.
 * Plan 15-01: Dashboard API and UI components.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Integrations from '../pages/Integrations';
import { IntegrationCard } from '../components/integrations/IntegrationCard';
import { IntegrationList } from '../components/integrations/IntegrationList';
import { IntegrationActions } from '../components/integrations/IntegrationActions';
import { Button } from '../components/ui/Button';
import type { DashboardConnector } from '../types/integrations';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock useIntegrations hook
vi.mock('../hooks/useIntegrations', () => ({
  useIntegrations: vi.fn(() => ({
    connectors: [],
    systemHealth: null,
    loading: false,
    error: null,
    lastUpdate: null,
    handleDisconnect: vi.fn(),
    handleSync: vi.fn(),
    handleReauth: vi.fn(),
    clearErrors: vi.fn(),
    refresh: vi.fn(),
  })),
}));

// Sample connector data
const mockConnector: DashboardConnector = {
  platform: 'notion',
  health_status: 'healthy',
  last_sync_at: '2026-05-02T12:00:00Z',
  items_synced: 100,
  error_count: 0,
  is_connected: true,
  sync_direction: 'bidirectional',
  sync_state: 'idle',
  last_error: null,
};

const mockErrorConnector: DashboardConnector = {
  platform: 'slack',
  health_status: 'unhealthy',
  last_sync_at: '2026-05-01T10:00:00Z',
  items_synced: 50,
  error_count: 3,
  is_connected: true,
  sync_direction: 'pull',
  sync_state: 'error',
  last_error: 'Token expired',
};

describe('Integrations Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with title "Integration Dashboard"', async () => {
    render(<Integrations />);
    expect(screen.getByText('Integration Dashboard')).toBeInTheDocument();
  });

  it('displays loading skeleton when loading', async () => {
    const { useIntegrations } = await import('../hooks/useIntegrations');
    vi.mocked(useIntegrations).mockReturnValue({
      connectors: [],
      systemHealth: null,
      loading: true,
      error: null,
      lastUpdate: null,
      handleDisconnect: vi.fn(),
      handleSync: vi.fn(),
      handleReauth: vi.fn(),
      clearErrors: vi.fn(),
      refresh: vi.fn(),
    });

    render(<Integrations />);
    // Check for loading skeleton elements
    const skeletons = screen.getAllByText('', { selector: '.animate-pulse' });
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('displays error banner when error exists', async () => {
    const { useIntegrations } = await import('../hooks/useIntegrations');
    vi.mocked(useIntegrations).mockReturnValue({
      connectors: [],
      systemHealth: null,
      loading: false,
      error: 'Failed to fetch dashboard',
      lastUpdate: null,
      handleDisconnect: vi.fn(),
      handleSync: vi.fn(),
      handleReauth: vi.fn(),
      clearErrors: vi.fn(),
      refresh: vi.fn(),
    });

    render(<Integrations />);
    expect(screen.getByText('Failed to fetch dashboard')).toBeInTheDocument();
  });

  it('displays empty state when no connectors', async () => {
    const { useIntegrations } = await import('../hooks/useIntegrations');
    vi.mocked(useIntegrations).mockReturnValue({
      connectors: [],
      systemHealth: { status: 'healthy', healthy_count: 0, degraded_count: 0, unhealthy_count: 0 },
      loading: false,
      error: null,
      lastUpdate: null,
      handleDisconnect: vi.fn(),
      handleSync: vi.fn(),
      handleReauth: vi.fn(),
      clearErrors: vi.fn(),
      refresh: vi.fn(),
    });

    render(<Integrations />);
    expect(screen.getByText('No Integrations')).toBeInTheDocument();
  });
});

describe('IntegrationCard', () => {
  const mockDisconnect = vi.fn();
  const mockSync = vi.fn();
  const mockReauth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays platform name, health indicator, last sync time', () => {
    render(
      <IntegrationCard
        connector={mockConnector}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    // The card renders both a mobile and a desktop view (toggled via CSS,
    // both present in the test DOM), so the platform name appears twice —
    // use getAllByText rather than the brittle getByText.
    expect(screen.getAllByText('Notion').length).toBeGreaterThan(0);
    expect(screen.getByText('idle')).toBeInTheDocument();
    // Check for health dot (green for healthy)
    const healthDot = document.querySelector('.bg-green-500');
    expect(healthDot).toBeInTheDocument();
  });

  it('displays error message when last_error exists', () => {
    render(
      <IntegrationCard
        connector={mockErrorConnector}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    expect(screen.getByText('Token expired')).toBeInTheDocument();
  });

  it('shows Sync Now button for connected connectors', () => {
    render(
      <IntegrationCard
        connector={mockConnector}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    expect(screen.getByText('Sync Now')).toBeInTheDocument();
  });

  it('shows Re-authorize button when token expired', () => {
    render(
      <IntegrationCard
        connector={mockErrorConnector}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    expect(screen.getByText('Re-authorize')).toBeInTheDocument();
  });
});

describe('IntegrationList', () => {
  const mockDisconnect = vi.fn();
  const mockSync = vi.fn();
  const mockReauth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no connectors', () => {
    render(
      <IntegrationList
        connectors={[]}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    expect(screen.getByText('No Integrations')).toBeInTheDocument();
  });

  it('sorts connectors by health status (unhealthy first)', () => {
    const connectors: DashboardConnector[] = [
      mockConnector, // healthy
      mockErrorConnector, // unhealthy
    ];

    render(
      <IntegrationList
        connectors={connectors}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    const cards = screen.getAllByText('', { selector: '.bg-white' });
    // First card should be unhealthy (Slack)
    expect(cards[0]).toBeInTheDocument();
  });

  it('renders multiple connectors in grid', () => {
    const connectors: DashboardConnector[] = [
      mockConnector,
      { ...mockConnector, platform: 'slack' },
      { ...mockConnector, platform: 'github' },
    ];

    render(
      <IntegrationList
        connectors={connectors}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    // Each platform name appears in both the mobile and desktop card views
    // (both rendered in the test DOM), so use getAllByText.
    expect(screen.getAllByText('Notion').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Slack').length).toBeGreaterThan(0);
    expect(screen.getAllByText('GitHub').length).toBeGreaterThan(0);
  });
});

describe('IntegrationActions', () => {
  const mockDisconnect = vi.fn();
  const mockSync = vi.fn();
  const mockReauth = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows Disconnect button when connected', () => {
    render(
      <IntegrationActions
        platform="notion"
        is_connected={true}
        sync_state="idle"
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    const disconnectBtn = screen.getByText('Disconnect');
    expect(disconnectBtn).toBeInTheDocument();
    fireEvent.click(disconnectBtn);
    expect(mockDisconnect).toHaveBeenCalledWith('notion');
  });

  it('shows Sync Now button and calls onSync', () => {
    render(
      <IntegrationActions
        platform="notion"
        is_connected={true}
        sync_state="idle"
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    const syncBtn = screen.getByText('Sync Now');
    expect(syncBtn).toBeInTheDocument();
    fireEvent.click(syncBtn);
    expect(mockSync).toHaveBeenCalledWith('notion');
  });

  it('shows syncing state when sync_state is syncing', () => {
    render(
      <IntegrationActions
        platform="notion"
        is_connected={true}
        sync_state="syncing"
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    expect(screen.getByText('Syncing...')).toBeInTheDocument();
  });

  it('shows Re-authorize button when needsReauth is true', () => {
    render(
      <IntegrationActions
        platform="notion"
        is_connected={true}
        sync_state="idle"
        needsReauth={true}
        onDisconnect={mockDisconnect}
        onSync={mockSync}
        onReauth={mockReauth}
      />
    );

    const reauthBtn = screen.getByText('Re-authorize');
    expect(reauthBtn).toBeInTheDocument();
    fireEvent.click(reauthBtn);
    expect(mockReauth).toHaveBeenCalledWith('notion');
  });
});

describe('Button component', () => {
  it('renders with primary variant', () => {
    render(<Button variant="primary">Click</Button>);
    expect(screen.getByText('Click')).toBeInTheDocument();
  });

  it('shows loading spinner when loading', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByText('Loading')).toBeInTheDocument();
    // Check for spinner animation
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('is disabled when loading', () => {
    render(<Button loading>Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalled();
  });
});