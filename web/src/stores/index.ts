import { create } from 'zustand';
import { createGraphSlice, GraphSlice } from './graphStore';
import { createEditorSlice, EditorSlice } from './editorStore';
import { createUISlice, UISlice } from './uiStore';
import { createDashboardSlice, DashboardSlice } from './dashboardStore';

type StoreState = GraphSlice & EditorSlice & UISlice & DashboardSlice;

export const useStore = create<StoreState>()((...a) => ({
  ...createGraphSlice(...a),
  ...createEditorSlice(...a),
  ...createUISlice(...a),
  ...createDashboardSlice(...a),
}));

// Re-export slices for type access
export type { GraphSlice, EditorSlice, UISlice, DashboardSlice };