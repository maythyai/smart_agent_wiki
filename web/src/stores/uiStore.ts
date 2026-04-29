import { StateCreator } from 'zustand';

// UI toggles and global state
interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
}

interface UIActions {
  toggleSidebar: () => void;
  setTheme: (theme: UIState['theme']) => void;
  setConnectionStatus: (status: UIState['connectionStatus']) => void;
}

export type UISlice = UIState & UIActions;

export const createUISlice: StateCreator<UISlice> = (set) => ({
  sidebarOpen: false,
  theme: 'light',
  connectionStatus: 'connecting',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
});