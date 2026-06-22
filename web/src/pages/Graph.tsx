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

  const { data, refetch, isLoading, isError, error } = useGraph({
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
      <header className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Knowledge Graph</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {isLoading
              ? 'Loading...'
              : isError
                ? 'Error loading graph'
                : data
                  ? `${data.total_nodes} nodes, ${data.total_edges} edges`
                  : 'Loading...'}
          </p>
        </div>
      </header>

      <div className="flex-1 flex">
        {/* Left sidebar: Filters and Controls */}
        <aside className="w-64 border-r dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-4 space-y-4 overflow-y-auto">
          <GraphFilters onRefresh={handleRefresh} />
          <GraphControls
            onZoomIn={() => {/* Handled by Cytoscape internally */}}
            onZoomOut={() => {/* Handled by Cytoscape internally */}}
            onFit={() => {/* Handled by Cytoscape internally */}}
          />
        </aside>

        {/* Main graph area */}
        <main className="flex-1 relative" ref={containerRef}>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900 z-10">
              <div className="flex flex-col items-center gap-3">
                <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                <p className="text-sm text-gray-500 dark:text-gray-400">Loading graph data...</p>
              </div>
            </div>
          )}

          {isError && !isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900 z-10">
              <div className="text-center">
                <div className="text-red-500 mb-3">
                  <svg className="w-10 h-10 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">Failed to load graph</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {error instanceof Error ? error.message : 'Could not load graph data. Please try again.'}
                </p>
                <button
                  onClick={() => refetch()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {!isLoading && !isError && data && data.nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-gray-900 z-10">
              <div className="text-center">
                <div className="text-gray-400 dark:text-gray-500 mb-3">
                  <svg className="w-10 h-10 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">No entities in the graph yet</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Start by creating pages and linking entities to build the knowledge graph.
                </p>
              </div>
            </div>
          )}

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