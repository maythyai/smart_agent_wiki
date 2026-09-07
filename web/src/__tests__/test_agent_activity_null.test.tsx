import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock useStore to return empty WS agents
vi.mock('../stores', () => ({
  useStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ agents: {} }),
}));

import { AgentList } from '../components/dashboard/AgentList';
import type { AgentRosterEntry } from '../types/api';

const mockRosterWithNull: AgentRosterEntry[] = [
  {
    name: 'Guardian',
    model_tier: 'rule',
    tools_allowed: [],
    rule: true,
    custom: false,
    activity_summary: null,
  },
  {
    name: 'Librarian',
    model_tier: 'sonnet',
    tools_allowed: ['search', 'read'],
    rule: false,
    custom: false,
    activity_summary: { calls: 5, last_active_at: '2026-09-07T10:30:00Z' },
  },
];

describe('AC-D-3: Agent activity null degradation', () => {
  it('displays "—" for calls when activity_summary is null', () => {
    render(
      <AgentList
        roster={mockRosterWithNull}
        onSelectAgent={vi.fn()}
        selectedAgent={null}
      />
    );

    // Guardian card rendered
    const guardianCard = screen.getByTestId('agent-card-Guardian');
    expect(guardianCard).toBeInTheDocument();

    // Guardian should show "—" for calls (activity_summary is null)
    expect(guardianCard).toHaveTextContent('—');

    // Librarian should show "5" for calls
    const librarianCard = screen.getByTestId('agent-card-Librarian');
    expect(librarianCard).toHaveTextContent('5');
  });

  it('does not error when all agents have null activity_summary', () => {
    const rosterAllNull: AgentRosterEntry[] = [
      {
        name: 'Guardian',
        model_tier: 'rule',
        tools_allowed: [],
        rule: true,
        custom: false,
        activity_summary: null,
      },
    ];

    expect(() =>
      render(
        <AgentList
          roster={rosterAllNull}
          onSelectAgent={vi.fn()}
          selectedAgent={null}
        />
      )
    ).not.toThrow();
  });
});
