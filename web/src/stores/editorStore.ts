import { StateCreator } from 'zustand';

// Editor state (per D-13~16)
interface EditorState {
  mode: 'view' | 'edit' | 'preview';
  isDirty: boolean;
  lastSaved: string | null;
  showCitationPreview: boolean;
}

interface EditorActions {
  setMode: (mode: EditorState['mode']) => void;
  setDirty: (dirty: boolean) => void;
  setLastSaved: (timestamp: string | null) => void;
  toggleCitationPreview: () => void;
}

export type EditorSlice = EditorState & EditorActions;

export const createEditorSlice: StateCreator<EditorSlice> = (set) => ({
  mode: 'view',
  isDirty: false,
  lastSaved: null,
  showCitationPreview: false,
  setMode: (mode) => set({ mode }),
  setDirty: (dirty) => set({ isDirty: dirty }),
  setLastSaved: (timestamp) => set({ lastSaved: timestamp }),
  toggleCitationPreview: () => set((s) => ({ showCitationPreview: !s.showCitationPreview })),
});