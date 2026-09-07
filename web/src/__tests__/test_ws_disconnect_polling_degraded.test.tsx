import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock useWebSocket: WS disconnected, polling still works
vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: vi.fn(() => ({
    status: 'disconnected',
    reconnect: vi.fn(),
    send: vi.fn(),
  })),
}));

// Mock useAgents: REST polling returns data successfully
vi.mock('../hooks/useAgents', () => ({
  useAgents: vi.fn(() => ({
    data: {
      agents: [
        {
          name: 'Librarian',
          model_tier: 'sonnet',
          tools_allowed: ['search', 'read'],
          rule: false,
          custom: false,
          activity_summary: { calls: 5, last_active_at: '2026-09-07T10:30:00Z' },
        },
      ],
      total: 1,
    },
    isError: false,
    isLoading: false,
    isSuccess: true,
    refetch: vi.fn(),
  })),
}));

// Mock useWorkflows: REST polling returns data successfully
vi.mock('../hooks/useWorkflows', () => ({
  useWorkflows: vi.fn(() => ({
    data: {
      workflows: [
        {
          workflow_id: 'wf-001',
          definition_name: 'knowledge_review',
          name: 'knowledge_review',
          workflow: 'knowledge_review',
          status: 'running',
          steps_completed: 2,
          steps_total: 4,
          updated_at: '2026-09-07T10:30:00Z',
          finished_at: null,
        },
      ],
      total: 1,
    },
    isError: false,
    isLoading: false,
    isSuccess: true,
    refetch: vi.fn(),
  })),
}));

vi.mock('../hooks/useWorkflowStatus', () => ({
  useWorkflowStatus: vi.fn(() => ({
    data: undefined,
    isLoading: false,
  })),
}));

// Mock useStore: empty WS agents, disconnected status
vi.mock('../stores', () => ({
  useStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      agents: {},
      activeWorkflow: null,
      lastUpdate: null,
      connectionStatus: 'disconnected',
    }),
}));

// Mock api to prevent real network calls (stats fetch)
vi.mock('../lib/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({
      total_pages: 0,
      recent_edits: 0,
      active_agents: 0,
      uptime_hours: 0,
    }),
    post: vi.fn().mockResolvedValue({}),
  },
}));

import Dashboard from '../pages/Dashboard';

describe('AC-D-8: WS disconnect polling degraded', () => {
  it('shows "Reconnecting..." banner and renders roster + workflow data from polling', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    );

    // "Reconnecting..." banner visible (WS disconnected, polling ok)
    expect(screen.getByText('Reconnecting...')).toBeInTheDocument();

    // Agent roster still rendered from REST polling data
    expect(screen.getByTestId('agent-card-Librarian')).toBeInTheDocument();

    // Workflow list still rendered from REST polling data
    expect(screen.getByTestId('workflow-row-wf-001')).toBeInTheDocument();

    // Full degradation banner NOT shown (polling is working)
    expect(screen.queryByText('Live updates paused. Data may be stale.')).not.toBeInTheDocument();
  });
});
