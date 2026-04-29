import { StateCreator } from 'zustand';
import type { AgentStatus, WorkflowProgress } from '../types/api';

// Dashboard state for agent and workflow tracking (per D-17~19)
interface DashboardState {
  agents: Record<string, AgentStatus>;
  activeWorkflow: WorkflowProgress | null;
  lastUpdate: string | null;
}

interface DashboardActions {
  updateAgent: (status: AgentStatus) => void;
  updateWorkflow: (progress: WorkflowProgress) => void;
  clearWorkflow: () => void;
  resetDashboard: () => void;
}

export type DashboardSlice = DashboardState & DashboardActions;

export const createDashboardSlice: StateCreator<DashboardSlice> = (set) => ({
  agents: {},
  activeWorkflow: null,
  lastUpdate: null,

  updateAgent: (status) =>
    set((state) => ({
      agents: {
        ...state.agents,
        [status.agent]: status,
      },
      lastUpdate: new Date().toISOString(),
    })),

  updateWorkflow: (progress) =>
    set({
      activeWorkflow: progress,
      lastUpdate: new Date().toISOString(),
    }),

  clearWorkflow: () =>
    set({
      activeWorkflow: null,
    }),

  resetDashboard: () =>
    set({
      agents: {},
      activeWorkflow: null,
      lastUpdate: null,
    }),
});
