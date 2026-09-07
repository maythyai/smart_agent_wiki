import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock useAgentActivity to return error state (404)
vi.mock('../hooks/useAgentActivity', () => ({
  useAgentActivity: vi.fn(() => ({
    data: undefined,
    isError: true,
    isLoading: false,
  })),
}));

import { AgentActivityDetail } from '../components/dashboard/AgentActivityDetail';

describe('AC-D-4: Agent activity 404 handling', () => {
  it('displays "Agent not found" when activity query returns 404', () => {
    render(
      <AgentActivityDetail
        agentName="NonExistent"
        onClose={vi.fn()}
      />
    );

    // Agent name shown
    expect(screen.getByText('NonExistent')).toBeInTheDocument();
    // "Agent not found" message
    expect(screen.getByText('Agent not found')).toBeInTheDocument();
    // Close button
    expect(screen.getByText('Close')).toBeInTheDocument();
  });

  it('calls onClose when Close button is clicked', () => {
    const onClose = vi.fn();
    render(
      <AgentActivityDetail agentName="NonExistent" onClose={onClose} />
    );

    screen.getByText('Close').click();
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
