import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock useAgentActivity to return preset activity data
vi.mock('../hooks/useAgentActivity', () => ({
  useAgentActivity: vi.fn(() => ({
    data: {
      agent: 'Librarian',
      calls: 5,
      failures: 1,
      last_action: 'search',
      last_active_at: '2026-09-07T10:30:00Z',
    },
    isError: false,
    isLoading: false,
  })),
}));

import { AgentActivityDetail } from '../components/dashboard/AgentActivityDetail';

describe('AC-D-2: Agent activity detail expand', () => {
  it('displays full activity details when agent is selected', () => {
    render(
      <AgentActivityDetail
        agentName="Librarian"
        onClose={vi.fn()}
      />
    );

    // Agent name
    expect(screen.getByText('Librarian')).toBeInTheDocument();
    // Calls
    expect(screen.getByText('5')).toBeInTheDocument();
    // Failures
    expect(screen.getByText('1')).toBeInTheDocument();
    // Last action
    expect(screen.getByText('search')).toBeInTheDocument();
    // Close button
    expect(screen.getByText('Close')).toBeInTheDocument();
  });

  it('renders nothing when agentName is null', () => {
    const { container } = render(
      <AgentActivityDetail agentName={null} onClose={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });
});
