import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock useWorkflows: completed BEFORE running (unsorted input)
vi.mock('../hooks/useWorkflows', () => ({
  useWorkflows: vi.fn(() => ({
    data: {
      workflows: [
        {
          workflow_id: 'completed-first',
          definition_name: 'knowledge_review',
          name: 'knowledge_review',
          workflow: 'knowledge_review',
          status: 'completed',
          steps_completed: 4,
          steps_total: 4,
          updated_at: '2026-09-07T09:00:00Z',
          finished_at: '2026-09-07T09:05:00Z',
        },
        {
          workflow_id: 'running-second',
          definition_name: 'knowledge_review',
          name: 'knowledge_review',
          workflow: 'knowledge_review',
          status: 'running',
          steps_completed: 1,
          steps_total: 4,
          updated_at: '2026-09-07T10:30:00Z',
          finished_at: null,
        },
      ],
      total: 2,
    },
    isError: false,
    isLoading: false,
  })),
}));

vi.mock('../hooks/useWorkflowStatus', () => ({
  useWorkflowStatus: vi.fn(() => ({
    data: undefined,
    isLoading: false,
  })),
}));

import { WorkflowList } from '../components/dashboard/WorkflowList';

describe('AC-D-6: Workflow running top sort', () => {
  it('places running workflow before completed workflow', () => {
    const { container } = render(<WorkflowList />);

    // Get all workflow rows in DOM order
    const rows = container.querySelectorAll('[data-testid^="workflow-row-"]');
    expect(rows.length).toBe(2);

    // First row should be running, second should be completed
    expect(rows[0]).toHaveAttribute('data-testid', 'workflow-row-running-second');
    expect(rows[1]).toHaveAttribute('data-testid', 'workflow-row-completed-first');
  });
});
