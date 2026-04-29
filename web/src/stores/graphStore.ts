import { StateCreator } from 'zustand';

// Graph selection and view state (per D-10~12)
interface GraphState {
  selectedNode: string | null;
  hoveredNode: string | null;
  zoom: number;
  layout: 'fcose' | 'concentric' | 'breadthfirst';
  viewMode: 'full' | 'community' | 'clusters';
  entityTypeFilter: string | null;
  relationTypeFilter: string | null;
  minConfidence: number | null;
}

interface GraphActions {
  selectNode: (id: string | null) => void;
  hoverNode: (id: string | null) => void;
  setZoom: (zoom: number) => void;
  setLayout: (layout: GraphState['layout']) => void;
  setViewMode: (mode: GraphState['viewMode']) => void;
  setEntityTypeFilter: (type: string | null) => void;
  setRelationTypeFilter: (type: string | null) => void;
  setMinConfidence: (level: number | null) => void;
}

export type GraphSlice = GraphState & GraphActions;

export const createGraphSlice: StateCreator<GraphSlice> = (set) => ({
  selectedNode: null,
  hoveredNode: null,
  zoom: 1,
  layout: 'fcose',
  viewMode: 'full',
  entityTypeFilter: null,
  relationTypeFilter: null,
  minConfidence: null,
  selectNode: (id) => set({ selectedNode: id }),
  hoverNode: (id) => set({ hoveredNode: id }),
  setZoom: (zoom) => set({ zoom }),
  setLayout: (layout) => set({ layout }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setEntityTypeFilter: (type) => set({ entityTypeFilter: type }),
  setRelationTypeFilter: (type) => set({ relationTypeFilter: type }),
  setMinConfidence: (level) => set({ minConfidence: level }),
});