import { create } from 'zustand';
import { createGraphSlice, GraphSlice } from './graphStore';
import { createEditorSlice, EditorSlice } from './editorStore';
import { createUISlice, UISlice } from './uiStore';

type StoreState = GraphSlice & EditorSlice & UISlice;

export const useStore = create<StoreState>()((...a) => ({
  ...createGraphSlice(...a),
  ...createEditorSlice(...a),
  ...createUISlice(...a),
}));

// Re-export slices for type access
export type { GraphSlice, EditorSlice, UISlice };