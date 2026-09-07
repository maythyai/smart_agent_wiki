import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock useStore to return empty WS agents (roster data comes via props)
vi.mock('../stores', () => ({
  useStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ agents: {} }),
}));

import { AgentList } from '../components/dashboard/AgentList';
import type { AgentRosterEntry } from '../types/api';

const mockRoster: AgentRosterEntry[] = [
  {
    name: 'Librarian',
    model_tier: 'sonnet',
    tools_allowed: ['search', 'read'],
    rule: false,
    custom: false,
    activity_summary: { calls: 5, last_active_at: '2026-09-07T10:30:00Z' },
  },
  {
    name: 'MedicalExpert',
    model_tier: 'sonnet',
    tools_allowed: ['search', 'read'],
    rule: false,
    custom: true,
    activity_summary: { calls: 3, last_active_at: '2026-09-07T09:00:00Z' },
  },
  {
    name: 'Guardian',
    model_tier: 'rule',
    tools_allowed: [],
    rule: true,
    custom: false,
    activity_summary: null,
  },
];

describe('AC-D-1: Agent roster render', () => {
  it('renders all agents from REST roster with name, status, custom marker, and calls', () => {
    render(
      <AgentList
        roster={mockRoster}
        onSelectAgent={vi.fn()}
        selectedAgent={null}
      />
    );

    // All 3 agents rendered
    expect(screen.getByTestId('agent-card-Librarian')).toBeInTheDocument();
    expect(screen.getByTestId('agent-card-MedicalExpert')).toBeInTheDocument();
    expect(screen.getByTestId('agent-card-Guardian')).toBeInTheDocument();

    // Custom marker for MedicalExpert
    expect(screen.getByText('custom')).toBeInTheDocument();

    // Calls value for Librarian (5)
    expect(screen.getByText('5')).toBeInTheDocument();
    // Calls value for MedicalExpert (3)
    expect(screen.getByText('3')).toBeInTheDocument();

    // Status text labels (all idle since no WS data)
    expect(screen.getAllByText('idle').length).toBe(3);
  });

  it('shows empty state when roster is empty', () => {
    render(
      <AgentList
        roster={[]}
        onSelectAgent={vi.fn()}
        selectedAgent={null}
      />
    );

    expect(screen.getByText('No agents registered')).toBeInTheDocument();
  });
});
