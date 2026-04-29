import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router';
import { KnowledgeGraph } from '../components/graph/KnowledgeGraph';
import { GraphControls } from '../components/graph/GraphControls';
import { NodeDetail } from '../components/graph/NodeDetail';
import { GraphFilters } from '../components/graph/GraphFilters';
import { useStore } from '../stores';
import { useGraph } from '../hooks/useGraph';
import type { GraphNode } from '../types/api';

export default function Graph() {
  const [searchParams, setSearchParams] = useSearchParams();
  const entity = searchParams.get('entity') ?? undefined;
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedNode = useStore((s) => s.selectedNode);
  const selectNode = useStore((s) => s.selectNode);

  const { data, refetch } = useGraph({
    entity,
    depth: 2,
    max_nodes: 100,
  });

  // Find selected node data for detail panel
  const [selectedNodeData, setSelectedNodeData] = useState<GraphNode | null>(null);

  useEffect(() => {
    if (selectedNode && data) {
      const node = data.nodes.find((n) => n.id === selectedNode);
      setSelectedNodeData(node ?? null);
    } else {
      setSelectedNodeData(null);
    }
  }, [selectedNode, data]);

  const handleNodeSelect = useCallback((nodeId: string) => {
    selectNode(nodeId);
    setSearchParams((params) => {
      params.set('node', nodeId);
      return params;
    });
  }, [selectNode, setSearchParams]);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Graph</h1>
          <p className="text-sm text-gray-500">
            {data ? `${data.total_nodes} nodes, ${data.total_edges} edges` : 'Loading...'}
          </p>
        </div>
      </header>

      <div className="flex-1 flex">
        {/* Left sidebar: Filters and Controls */}
        <aside className="w-64 border-r bg-gray-50 p-4 space-y-4 overflow-y-auto">
          <GraphFilters onRefresh={handleRefresh} />
          <GraphControls
            onZoomIn={() => {/* Handled by Cytoscape internally */}}
            onZoomOut={() => {/* Handled by Cytoscape internally */}}
            onFit={() => {/* Handled by Cytoscape internally */}}
          />
        </aside>

        {/* Main graph area */}
        <main className="flex-1 relative" ref={containerRef}>
          <KnowledgeGraph
            entity={entity}
            depth={2}
            maxNodes={100}
            onNodeSelect={handleNodeSelect}
          />

          {/* Right panel: Node detail */}
          <div className="absolute top-4 right-4 w-72">
            <NodeDetail
              nodeData={selectedNodeData ? {
                id: selectedNodeData.id,
                label: selectedNodeData.label,
                type: selectedNodeData.type,
                confidence: selectedNodeData.confidence,
                description: selectedNodeData.description,
              } : undefined}
            />
          </div>
        </main>
      </div>
    </div>
  );
}