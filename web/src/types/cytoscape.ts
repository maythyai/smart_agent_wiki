import type { NodeSingular, EdgeSingular } from 'cytoscape';
import type cytoscape from 'cytoscape';

// Confidence to color mapping (per D-06)
export function confidenceToColor(confidence: number): string {
  const colors: Record<number, string> = {
    1: '#9E9E9E', // Unverified - gray
    2: '#FFC107', // Single Source - amber
    3: '#4CAF50', // Cross-Validated - green
    4: '#2196F3', // Human Verified - blue
  };
  return colors[confidence] || '#9E9E9E';
}

// Entity type to color mapping
export function entityTypeToColor(type: string): string {
  const colors: Record<string, string> = {
    concept: '#4CAF50',
    entity: '#2196F3',
    document: '#9E9E9E',
    claim: '#FF9800',
    person: '#E91E63',
    organization: '#673AB7',
    location: '#00BCD4',
  };
  return colors[type.toLowerCase()] || '#607D8B';
}

// Edge type to color mapping
export function edgeTypeToColor(type: string): string {
  const colors: Record<string, string> = {
    related_to: '#9E9E9E',
    contradicts: '#F44336',
    supports: '#4CAF50',
    derives_from: '#2196F3',
    mentions: '#FF9800',
  };
  return colors[type.toLowerCase()] || '#9E9E9E';
}

// Full graph style configuration (per RESEARCH.md Pitfall 1)
// Use any[] to avoid complex Cytoscape type issues
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const GRAPH_STYLE: any[] = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': 12,
      'width': 40,
      'height': 40,
      'background-color': (ele: NodeSingular) =>
        confidenceToColor(ele.data('confidence')),
      'border-width': 2,
      'border-color': '#333',
      'text-outline-color': '#fff',
      'text-outline-width': 2,
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#FF5722',
    },
  },
  {
    selector: 'node.highlighted',
    style: {
      'border-width': 3,
      'border-color': '#4CAF50',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': (ele: EdgeSingular) =>
        edgeTypeToColor(ele.data('type')),
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': (ele: EdgeSingular) =>
        edgeTypeToColor(ele.data('type')),
      'arrow-scale': 0.8,
    },
  },
  {
    selector: 'edge[type="contradicts"]',
    style: {
      'line-style': 'dashed',
      'line-color': '#F44336',
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'width': 4,
      'line-color': '#FF5722',
    },
  },
];

// fCoSE layout configuration (per D-10, RESEARCH.md)
export const FCOSE_LAYOUT: cytoscape.LayoutOptions = {
  name: 'fcose',
  animate: true,
  animationDuration: 500,
  idealEdgeLength: 100,
  nodeSeparation: 80,
  quality: 'proof',
  randomize: false,
  fit: true,
  padding: 50,
  nodeDimensionsIncludeLabels: true,
} as cytoscape.LayoutOptions;

// Concentric layout for small graphs (<50 nodes)
export const CONCENTRIC_LAYOUT: cytoscape.LayoutOptions = {
  name: 'concentric',
  animate: true,
  animationDuration: 500,
  fit: true,
  padding: 50,
  minNodeSpacing: 40,
} as cytoscape.LayoutOptions;

// Breadthfirst layout for hierarchical view
export const BREADTHFIRST_LAYOUT: cytoscape.LayoutOptions = {
  name: 'breadthfirst',
  animate: true,
  animationDuration: 500,
  fit: true,
  padding: 50,
  directed: true,
  spacingFactor: 1.5,
} as cytoscape.LayoutOptions;

// Determine view mode based on node count (per D-10)
export function getViewMode(nodeCount: number): 'full' | 'community' | 'clusters' {
  if (nodeCount < 50) return 'full';
  if (nodeCount <= 200) return 'community';
  return 'clusters';
}

// Get layout based on view mode
export function getLayoutForViewMode(viewMode: 'full' | 'community' | 'clusters'): cytoscape.LayoutOptions {
  switch (viewMode) {
    case 'full':
      return FCOSE_LAYOUT;
    case 'community':
      return CONCENTRIC_LAYOUT;
    case 'clusters':
      return BREADTHFIRST_LAYOUT;
    default:
      return FCOSE_LAYOUT;
  }
}