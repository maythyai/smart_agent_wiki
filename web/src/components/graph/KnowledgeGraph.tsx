import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { useGraph } from '../../hooks/useGraph';
import { useStore } from '../../stores';
import { slugify } from '../../lib/slugify';
import { GRAPH_STYLE, getLayoutForViewMode, getViewMode } from '../../types/cytoscape';

// Register fCoSE layout
cytoscape.use(fcose);

interface KnowledgeGraphProps {
  entity?: string;
  depth?: number;
  maxNodes?: number;
  onNodeSelect?: (nodeId: string) => void;
  onReady?: (cy: Core) => void;
}

export function KnowledgeGraph({
  entity,
  depth = 2,
  maxNodes = 50,
  onNodeSelect,
  onReady,
}: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const navigate = useNavigate();

  const selectedNode = useStore((s) => s.selectedNode);
  const selectNode = useStore((s) => s.selectNode);
  const viewMode = useStore((s) => s.viewMode);
  const setViewMode = useStore((s) => s.setViewMode);
  const entityTypeFilter = useStore((s) => s.entityTypeFilter);
  const minConfidence = useStore((s) => s.minConfidence);

  const { data, isLoading, isError } = useGraph({
    entity,
    depth,
    max_nodes: maxNodes,
    type: entityTypeFilter ?? undefined,
  });

  // Filter nodes by confidence client-side
  const filteredData = data && {
    nodes: data.nodes.filter(
      (n) => minConfidence === null || n.confidence >= minConfidence
    ),
    edges: data.edges,
  };

  // Update view mode based on node count (per D-10)
  useEffect(() => {
    if (filteredData) {
      const autoViewMode = getViewMode(filteredData.nodes.length);
      setViewMode(autoViewMode);
    }
  }, [filteredData?.nodes.length, setViewMode]);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !filteredData) return;

    // Per RESEARCH.md Pitfall 1: Use batch for initial elements
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: filteredData.nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.label,
            type: n.type,
            confidence: n.confidence,
            description: n.description,
          },
        })),
        edges: filteredData.edges.map((e, i) => ({
          data: {
            id: e.id || `edge-${i}`,
            source: e.source,
            target: e.target,
            type: e.type,
            weight: e.weight,
          },
        })),
      },
      style: GRAPH_STYLE,
      layout: getLayoutForViewMode(viewMode),
      // Per RESEARCH.md Pitfall 1: Performance options
      hideEdgesOnViewport: true,
      textureOnViewport: true,
      motionBlur: true,
      wheelSensitivity: 0.3,
    });

    // Per D-11: Click handler for node selection
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target as NodeSingular;
      const nodeId = node.id();
      selectNode(nodeId);
      onNodeSelect?.(nodeId);
    });

    // Double-click for expansion/navigation
    cyRef.current.on('dbltap', 'node', (evt) => {
      const node = evt.target as NodeSingular;
      const nodeLabel = node.data('label');
      navigate(`/page/${slugify(nodeLabel)}`);
    });

    // Per D-11: Drag support is built-in with Cytoscape

    // Expose the Cytoscape instance to the parent so controls (zoom/fit)
    // can drive it directly — fixes the previous no-op GraphControls handlers.
    onReady?.(cyRef.current);

    return () => {
      cyRef.current?.destroy();
      cyRef.current = null;
    };
  }, [filteredData, viewMode, selectNode, onNodeSelect, navigate, onReady]);

  // Update selection state
  useEffect(() => {
    if (cyRef.current && selectedNode) {
      cyRef.current.nodes().unselect();
      cyRef.current.$(`node[id="${selectedNode}"]`).select();
    }
  }, [selectedNode]);

  // Run layout when view mode changes
  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.layout(getLayoutForViewMode(viewMode)).run();
    }
  }, [viewMode]);

  if (isLoading) {
    return (
      <div className="w-full h-full min-h-[600px] bg-gray-50 rounded-lg flex items-center justify-center">
        <div className="text-gray-500">Loading graph...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="w-full h-full min-h-[600px] bg-red-50 rounded-lg flex items-center justify-center">
        <div className="text-red-500">Failed to load graph</div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[600px] bg-gray-50 rounded-lg"
    />
  );
}
