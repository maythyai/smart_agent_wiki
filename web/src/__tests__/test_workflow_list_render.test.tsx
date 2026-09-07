import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock useWorkflows to return preset data
vi.mock('../hooks/useWorkflows', () => ({
  useWorkflows: vi.fn(() => ({
    data: {
      workflows: [
        {
          workflow_id: 'abc-123',
          definition_name: 'knowledge_review',
          name: 'knowledge_review',
          workflow: 'knowledge_review',
          status: 'running',
          steps_completed: 2,
          steps_total: 4,
          updated_at: '2026-09-07T10:30:00Z',
          finished_at: null,
        },
        {
          workflow_id: 'prev-456',
          definition_name: 'knowledge_review',
          name: 'knowledge_review',
          workflow: 'knowledge_review',
          status: 'completed',
          steps_completed: 4,
          steps_total: 4,
          updated_at: '2026-09-07T09:00:00Z',
          finished_at: '2026-09-07T09:05:00Z',
        },
      ],
      total: 2,
    },
    isError: false,
    isLoading: false,
  })),
}));

// Mock useWorkflowStatus (not expanded by default)
vi.mock('../hooks/useWorkflowStatus', () => ({
  useWorkflowStatus: vi.fn(() => ({
    data: undefined,
    isLoading: false,
  })),
}));

import { WorkflowList } from '../components/dashboard/WorkflowList';

describe('AC-D-5: Workflow list render', () => {
  it('renders all workflow rows with id, status, steps, and timestamp', () => {
    render(<WorkflowList />);

    // Both workflow rows rendered
    expect(screen.getByTestId('workflow-row-abc-123')).toBeInTheDocument();
    expect(screen.getByTestId('workflow-row-prev-456')).toBeInTheDocument();

    // Status text labels (accessibility: not just color)
    expect(screen.getByText('running')).toBeInTheDocument();
    expect(screen.getByText('completed')).toBeInTheDocument();

    // Steps progress
    expect(screen.getByText('2/4 steps')).toBeInTheDocument();
    expect(screen.getByText('4/4 steps')).toBeInTheDocument();

    // Live marker for running workflow with finished_at=null
    expect(screen.getByText('live')).toBeInTheDocument();
  });
});
