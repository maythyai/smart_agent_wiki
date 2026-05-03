import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntegrationCard, healthColors, formatRelativeTime } from '../IntegrationCard';
import type { DashboardConnector } from '../../../types/integrations';

// Mock IntegrationActions since it's a separate component
vi.mock('../IntegrationActions', () => ({
  IntegrationActions: () => <div data-testid="integration-actions">Actions</div>,
}));

// Mock IntegrationCardExpanded since it uses complex mobile UI
vi.mock('../IntegrationCardExpanded', () => ({
  IntegrationCardExpanded: () => <div data-testid="card-expanded">Expanded</div>,
}));

const mockConnector: DashboardConnector = {
  platform: 'notion',
  health_status: 'healthy',
  last_sync_at: '2026-05-03T10:00:00Z',
  items_synced: 42,
  error_count: 0,
  is_connected: true,
  sync_direction: 'bidirectional',
  sync_state: 'idle',
  last_error: null,
};

describe('IntegrationCard', () => {
  it('renders connector name', () => {
    render(
      <IntegrationCard
        connector={mockConnector}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    // Both mobile and desktop views show Notion
    const notionElements = screen.getAllByText('Notion');
    expect(notionElements.length).toBeGreaterThan(0);
  });

  it('shows connected status', () => {
    render(
      <IntegrationCard
        connector={mockConnector}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    // Desktop view shows Connected badge
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('shows health indicator with correct color class', () => {
    render(
      <IntegrationCard
        connector={mockConnector}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    // Healthy status should have green class
    const healthDots = screen.getAllByTitle('Health: healthy');
    expect(healthDots[0]).toHaveClass('bg-green-500');
  });

  it('shows disconnected status when not connected', () => {
    const disconnectedConnector = { ...mockConnector, is_connected: false };

    render(
      <IntegrationCard
        connector={disconnectedConnector}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('shows syncing state when syncing', () => {
    const syncingConnector = { ...mockConnector, sync_state: 'syncing' as const };

    render(
      <IntegrationCard
        connector={syncingConnector}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    // Syncing text appears in progress bar
    const syncingElements = screen.getAllByText('Syncing...');
    expect(syncingElements.length).toBeGreaterThan(0);
  });

  it('shows error message when present', () => {
    const errorConnector = {
      ...mockConnector,
      last_error: 'Token expired',
      error_count: 1,
    };

    render(
      <IntegrationCard
        connector={errorConnector}
        onDisconnect={vi.fn()}
        onSync={vi.fn()}
        onReauth={vi.fn()}
      />
    );

    expect(screen.getByText('Token expired')).toBeInTheDocument();
  });
});

describe('healthColors', () => {
  it('maps healthy to green', () => {
    expect(healthColors.healthy).toBe('bg-green-500');
  });

  it('maps degraded to yellow', () => {
    expect(healthColors.degraded).toBe('bg-yellow-500');
  });

  it('maps unhealthy to red', () => {
    expect(healthColors.unhealthy).toBe('bg-red-500');
  });
});

describe('formatRelativeTime', () => {
  it('returns "Never" for null timestamp', () => {
    expect(formatRelativeTime(null)).toBe('Never');
  });

  it('returns "Just now" for recent timestamps', () => {
    const now = new Date().toISOString();
    expect(formatRelativeTime(now)).toBe('Just now');
  });

  it('returns minutes ago for timestamps within an hour', () => {
    const fiveMinsAgo = new Date(Date.now() - 5 * 60000).toISOString();
    expect(formatRelativeTime(fiveMinsAgo)).toBe('5m ago');
  });

  it('returns hours ago for timestamps within a day', () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    expect(formatRelativeTime(twoHoursAgo)).toBe('2h ago');
  });

  it('returns days ago for timestamps within a week', () => {
    const threeDaysAgo = new Date(Date.now() - 3 * 86400000).toISOString();
    expect(formatRelativeTime(threeDaysAgo)).toBe('3d ago');
  });
});