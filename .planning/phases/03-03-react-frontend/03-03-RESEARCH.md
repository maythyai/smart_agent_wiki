# Phase 03-03: React Frontend - Research

**Researched:** 2026-04-29
**Domain:** React 19, Cytoscape.js, Milkdown, WebSocket
**Confidence:** HIGH

## Summary

This phase implements the React frontend for Smart Agent Wiki, consuming the FastAPI backend from Phase 03-02. The frontend consists of four main features: Search UI (WEB-01), Knowledge Graph visualization (WEB-02), Wiki page editor (WEB-03), and Agent dashboard with real-time WebSocket updates. All features use the existing backend APIs - no backend changes required.

**Primary recommendation:** Use React 19 with Zustand for client state, TanStack Query for server state, and Cytoscape.js with fCoSE layout for graph visualization. Milkdown provides a WYSIWYG Markdown editing experience with citation support.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** React 19 + TypeScript as frontend framework
- **D-02:** Vite as build tool
- **D-03:** TailwindCSS for styling
- **D-04:** React Router for SPA routing
- **D-05:** Search box real-time autocomplete (debounce 300ms)
- **D-06:** Search results: title, snippet, confidence badge, freshness indicator, inline citations
- **D-07:** Pagination: infinite scroll or pagination buttons
- **D-08:** Filters: by type, tag, confidence
- **D-09:** Cytoscape.js for graph visualization
- **D-10:** Graph modes: full (<50), community (50-200), clusters (>200)
- **D-11:** Graph interactions: pan, zoom, drag, click for details
- **D-12:** Graph filters: entity type, relation type, confidence
- **D-13:** Milkdown as WYSIWYG Markdown editor
- **D-14:** Edit mode: view -> edit -> submit for review
- **D-15:** Submit changes via Write Queue API
- **D-16:** Support approve/reject operations via Page API
- **D-17:** Real-time Agent status via WebSocket
- **D-18:** Agent list: name, status, current task, progress
- **D-19:** Workflow execution visualization: steps, duration, results
- **D-20:** WebSocket events: agent_status, workflow_progress, page_updated
- **D-21:** Auto-reconnect with exponential backoff
- **D-22:** Heartbeat detection (30s interval)

### Claude's Discretion
- Frontend directory structure (src/components vs src/pages vs src/hooks)
- State management solution (React Query vs Zustand vs Context)
- Graph layout algorithm selection
- Editor toolbar design
- Error handling and loading states

### Deferred Ideas (OUT OF SCOPE)
None - all Phase 03-03 requirements are in scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WEB-01 | Web UI search interface | SearchBar, SearchResults, Filters components; TanStack Query for API calls |
| WEB-02 | Knowledge graph visualization | Cytoscape.js with fCoSE layout; adaptive modes by node count |
| WEB-03 | Wiki page editor | Milkdown React integration; commonmark + GFM presets; toolbar with slash commands |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Search query input | Browser | - | User interaction, debounce in browser |
| Search results display | Browser | - | Rendering from server response |
| Graph layout computation | Browser | - | fCoSE runs client-side for interactivity |
| Graph data retrieval | API | Browser | Server provides nodes/edges, browser renders |
| Page editing | Browser | API | Browser captures edits, API persists |
| Real-time updates | WebSocket | Browser | Server pushes events, browser updates state |
| Agent status | WebSocket | Browser | Server broadcasts status changes |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.5 | UI framework | [VERIFIED: npm registry 2026-04-29] Latest stable |
| react-dom | 19.2.5 | DOM rendering | [VERIFIED: npm registry 2026-04-29] Matches React version |
| typescript | 6.0.3 | Type safety | [VERIFIED: npm registry 2026-04-29] Latest stable |
| vite | 8.0.10 | Build tool | [VERIFIED: npm registry 2026-04-29] Fast HMR, ESM native |
| tailwindcss | 4.2.4 | Styling | [VERIFIED: npm registry 2026-04-29] Utility-first CSS |
| react-router | 7.14.2 | SPA routing | [VERIFIED: npm registry 2026-04-29] Latest with data routers |
| @tanstack/react-query | 5.100.6 | Server state | [VERIFIED: npm registry 2026-04-29] Handles API caching, reconnection |

### Graph & Editor

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| cytoscape | 3.33.2 | Graph library | [VERIFIED: npm registry 2026-04-29] Full-featured graph theory |
| cytoscape-fcose | 2.2.0 | fCoSE layout | [CITED: Context7] Best force-directed for quality |
| @milkdown/react | 7.20.0 | Editor React binding | [VERIFIED: npm registry 2026-04-29] Official React integration |
| @milkdown/kit | 7.20.0 | Editor core | [VERIFIED: npm registry 2026-04-29] CommonMark + plugins |

### State Management

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| zustand | 5.0.12 | Client state | Graph selection, editor state, UI toggles |
| @tanstack/react-query | 5.100.6 | Server state | Search results, page content, graph data |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Zustand | Jotai | Jotai is more atomic; Zustand slices pattern is simpler for this scope |
| Cytoscape.js | D3 + react-force-graph | D3 requires more custom code; Cytoscape has built-in interactions |
| Milkdown | TipTap | TipTap is more extensible; Milkdown has better Markdown fidelity out-of-box |
| TanStack Query | SWR | Both excellent; TanStack Query has better mutations API for Write Queue |

**Installation:**

```bash
npm install react@19.2.5 react-dom@19.2.5 react-router@7.14.2 \
  @tanstack/react-query@5.100.6 zustand@5.0.12 \
  cytoscape@3.33.2 cytoscape-fcose@2.2.0 \
  @milkdown/react@7.20.0 @milkdown/kit@7.20.0 \
  tailwindcss@4.2.4 typescript@6.0.3 vite@8.0.10
```

## Architecture Patterns

### System Architecture Diagram

```
+===========================================================================+
|                           Browser (React SPA)                               |
|  +----------------+  +----------------+  +----------------+  +-----------+ |
|  |  SearchBar     |  |  KnowledgeGraph|  |  MilkdownEditor|  | Dashboard | |
|  |  (WEB-01)      |  |  (WEB-02)      |  |  (WEB-03)      |  | (Agent)   | |
|  +-------+--------+  +-------+--------+  +-------+--------+  +-----+-----+ |
|          |                 |                     |                 |       |
|  +-------v-----------------v---------------------v-----------------v-----+ |
|  |                    Zustand Store (Client State)                          | |
|  |  searchQuery | graphSelection | editorState | agentStatus | uiToggles   | |
|  +-------+-----------------+---------------------+-----------------+-----+---+ |
|          |                 |                     |                 |       |
|  +-------v-----------------v---------------------v-----------------v-----+   |
|  |                 TanStack Query (Server State)                          |   |
|  |  useSearch() | useGraph() | usePage() | useAgents()                  |   |
|  +-------+-----------------+---------------------+-----------------+-----+   |
+==========|=================|=====================|===================|=======+
           |                 |                     |                   |
+==========v=================v=====================v===================v=======+
|                           FastAPI Backend (:8000)                            |
|  +----------------+  +----------------+  +----------------+  +-----------+   |
|  | GET /api/search|  | GET /api/graph |  | /api/pages/*   |  | GET /ws    |   |
|  +-------+--------+  +-------+--------+  +-------+--------+  +-----+-----+   |
|          |                 |                     |                 |         |
|  +-------v-----------------v---------------------v-----------------v-----+   |
|  |                          QueryEngine + WriteQueue                        | |
|  +-------------------------------------------------------------------------+   |
+================================================================================+
```

### Recommended Project Structure

```
web/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── src/
    ├── main.tsx                 # App entry point
    ├── App.tsx                 # Router setup
    ├── routes/
    │   ├── router.tsx          # React Router config
    │   └── loader.ts          # Data loaders
    ├── components/
    │   ├── ui/                 # Base UI (shadcn/ui)
    │   │   ├── Button.tsx
    │   │   ├── Input.tsx
    │   │   ├── Badge.tsx
    │   │   └── Card.tsx
    │   ├── search/             # WEB-01
    │   │   ├── SearchBar.tsx
    │   │   ├── SearchResults.tsx
    │   │   ├── ResultCard.tsx
    │   │   └── SearchFilters.tsx
    │   ├── graph/              # WEB-02
    │   │   ├── KnowledgeGraph.tsx
    │   │   ├── GraphControls.tsx
    │   │   ├── NodeDetail.tsx
    │   │   └── GraphFilters.tsx
    │   ├── editor/             # WEB-03
    │   │   ├── WikiEditor.tsx
    │   │   ├── EditorToolbar.tsx
    │   │   ├── CitationPreview.tsx
    │   │   └── EditorStatus.tsx
    │   └── dashboard/          # Agent status
    │       ├── AgentList.tsx
    │       ├── AgentCard.tsx
    │       └── WorkflowVisualizer.tsx
    ├── pages/
    │   ├── Home.tsx
    │   ├── Search.tsx
    │   ├── Graph.tsx
    │   ├── Page.tsx           # Wiki page view/edit
    │   └── Dashboard.tsx
    ├── stores/
    │   ├── index.ts          # Combined store
    │   ├── graphStore.ts     # Graph selection state
    │   ├── editorStore.ts    # Editor state
    │   └── uiStore.ts        # UI toggles
    ├── hooks/
    │   ├── useWebSocket.ts   # WebSocket connection
    │   ├── useSearch.ts      # Search hook (TanStack Query)
    │   ├── useGraph.ts       # Graph data hook
    │   ├── usePage.ts        # Page CRUD hook
    │   └── useDebounce.ts    # Debounce utility
    ├── lib/
    │   ├── api.ts            # Fetch wrapper
    │   └── ws.ts             # WebSocket manager
    └── types/
        └── api.ts            # API response types
```

### Pattern 1: Zustand Slices Pattern

**What:** Split Zustand store into composable slices, each managing a specific domain of client state.

**When to use:** Multiple independent UI states (graph selection, editor mode, filters).

**Trade-offs:**

- Pro: Clear separation of concerns
- Pro: Easy to test slices independently
- Pro: No prop drilling for global UI state
- Con: Must be careful about slice dependencies

**Example:**

```typescript
// stores/graphStore.ts
import { StateCreator } from 'zustand';

interface GraphState {
  selectedNode: string | null;
  hoveredNode: string | null;
  zoom: number;
  layout: 'fcose' | 'concentric' | 'breadthfirst';
}

interface GraphActions {
  selectNode: (id: string | null) => void;
  setZoom: (zoom: number) => void;
  setLayout: (layout: GraphState['layout']) => void;
}

export type GraphSlice = GraphState & GraphActions;

export const createGraphSlice: StateCreator<GraphSlice> = (set) => ({
  selectedNode: null,
  hoveredNode: null,
  zoom: 1,
  layout: 'fcose',
  selectNode: (id) => set({ selectedNode: id }),
  setZoom: (zoom) => set({ zoom }),
  setLayout: (layout) => set({ layout }),
});

// stores/index.ts
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

// Usage in component
function NodeDetail() {
  const selectedNode = useStore((s) => s.selectedNode);
  const selectNode = useStore((s) => s.selectNode);
  // ...
}
```

### Pattern 2: TanStack Query for Server State

**What:** Use TanStack Query for all API calls, separating server state from client state.

**When to use:** Search results, graph data, page content - anything from the backend.

**Trade-offs:**

- Pro: Automatic caching, background refetch, optimistic updates
- Pro: Built-in loading/error states
- Pro: Handles WebSocket invalidation gracefully
- Con: Additional abstraction over fetch

**Example:**

```typescript
// hooks/useSearch.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

interface SearchParams {
  q: string;
  page?: number;
  type?: string;
  min_confidence?: number;
}

export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => api.get('/api/search', { params }),
    enabled: params.q.length > 0, // Only fetch when query exists
    staleTime: 30_000, // Consider fresh for 30s
  });
}

// hooks/usePage.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function usePage(slug: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['page', slug],
    queryFn: () => api.get(`/api/pages/${slug}`),
    enabled: !!slug,
  });

  const mutation = useMutation({
    mutationFn: (content: string) =>
      api.put(`/api/pages/${slug}`, { content }),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['page', slug] });
    },
  });

  return { ...query, updatePage: mutation.mutate };
}
```

### Anti-Patterns to Avoid

- **Mixing server state into Zustand:** Store only UI state (selections, toggles) in Zustand; use TanStack Query for API data
- **Direct DOM manipulation in Cytoscape:** Use React refs properly; don't bypass React's lifecycle
- **Blocking UI during layout computation:** Cytoscape layout should use `animate: true` and not block main thread

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Debounced search | setTimeout + manual state | useDebouncedValue hook or TanStack Query's built-in | Edge cases: cancel pending, cleanup on unmount |
| WebSocket reconnection | Manual reconnect logic | Custom hook with exponential backoff | Edge cases: tab visibility, network changes |
| Graph layout | Custom force simulation | fCoSE extension | Edge cases: compound nodes, disconnected components |
| Editor toolbar | Custom button components | Milkdown Crepe or slash plugin | Integrates with editor state, command system |
| Form state | Manual state + validation | React Hook Form with Zod | Complex validation, dirty checking, submission states |

**Key insight:** WebSocket state synchronization is deceptively complex. Use a dedicated hook that handles visibility changes, network events, and message sequencing.

## Common Pitfalls

### Pitfall 1: Cytoscape Performance at Scale

**What goes wrong:** With >500 nodes, Cytoscape becomes slow. Pan/zoom stutters, layout takes forever. The graph goes from useful to frustrating.

**Why it happens:**

- Every node/edge is a DOM element or canvas draw call
- fCoSE layout is O(n log n) but still slow for thousands of nodes
- No built-in clustering or lazy loading

**How to avoid:**

1. Use `cy.batch()` for all initial element additions
2. Enable `hideEdgesOnViewport: true`, `textureOnViewport: true`
3. Implement adaptive modes (per D-10):
   - `<50 nodes`: Full graph, fCoSE layout
   - `50-200 nodes`: Community view (cluster by entity type)
   - `>200 nodes`: Topic clusters with drill-down
4. Use WebWorker for layout: `cytoscape-layout-worker` extension
5. For `>1000 nodes`, consider switching to `cosmos-over-cytoscape` GPU layout

**Warning signs:**

- Initial render >3 seconds
- Pan/zoom feels jerky
- Browser memory >500MB

### Pitfall 2: React State Desync with WebSocket

**What goes wrong:** WebSocket disconnects (network blip, tab sleep), reconnects, but UI shows stale data. User clicks on a node that no longer exists, or edits a page that's been updated by another agent.

**Why it happens:**

- No acknowledgment/replay mechanism in WebSocket
- Zustand updates on message receipt but doesn't track gaps
- Browser tab sleeping drops WebSocket silently

**How to avoid:**

1. On WebSocket connect, fetch current state via REST (sync point)
2. Implement message sequence numbers; detect gaps on reconnect
3. Show connection status indicator (green/yellow/red)
4. When disconnected, disable actions requiring real-time data
5. Use TanStack Query's `refetchOnReconnect: true` for automatic sync
6. For critical operations (edits), use REST API with optimistic updates

**Example:**

```typescript
// hooks/useWebSocket.ts
export function useWebSocket(sessionId: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    setStatus('connecting');
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttempts.current = 0;
      // Sync point: refetch current state
      queryClient.refetchQueries({ queryKey: ['agents'] });
      queryClient.refetchQueries({ queryKey: ['graph'] });
    };

    ws.onclose = () => {
      setStatus('disconnected');
      // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;
      setTimeout(connect, delay);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      // Route to appropriate query invalidation
      if (message.type === 'agent_status' || message.type === 'workflow_progress') {
        queryClient.invalidateQueries({ queryKey: ['agents'] });
      } else if (message.type === 'page_updated') {
        queryClient.invalidateQueries({ queryKey: ['page', message.payload.slug] });
        queryClient.invalidateQueries({ queryKey: ['graph'] });
      }
    };

    wsRef.current = ws;
  }, [sessionId, queryClient]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  // Heartbeat
  useEffect(() => {
    if (status !== 'connected') return;
    const interval = setInterval(() => {
      wsRef.current?.send(JSON.stringify({ type: 'ping' }));
    }, 30000); // Per D-22: 30s interval
    return () => clearInterval(interval);
  }, [status]);

  return { status, send: (msg: any) => wsRef.current?.send(JSON.stringify(msg)) };
}
```

### Pitfall 3: Milkdown Content State Management

**What goes wrong:** Content in Milkdown editor doesn't sync properly with React state. User types, but `getMarkdown()` returns old content. Or initial content loads but never updates when props change.

**Why it happens:**

- Milkdown's internal ProseMirror state is separate from React state
- Must use `defaultValueCtx` only on initial load
- Need to use `listenerCtx.markdownUpdated` for change detection

**How to avoid:**

1. Initialize editor with `defaultValueCtx` once
2. Use `markdownUpdated` listener to sync to parent state
3. To programmatically set content, use `editor.action(replaceAll(markdown))`
4. Handle loading states properly - don't render Milkdown until content is ready

**Example:**

```typescript
// components/editor/WikiEditor.tsx
function WikiEditor({ slug, initialContent, onSave }: WikiEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [isReady, setIsReady] = useState(false);

  const { loading, get } = useEditor((root) => {
    return Editor.make()
      .config((ctx) => {
        ctx.set(rootCtx, root);
        ctx.set(defaultValueCtx, initialContent);
        ctx.get(listenerCtx).markdownUpdated((ctx, md) => {
          setContent(md); // Sync to React state
        });
      })
      .use(commonmark)
      .use(gfm)
      .use(history)
      .use(listener);
  }, [initialContent]); // Re-initialize when content changes

  useEffect(() => {
    setIsReady(!loading);
  }, [loading]);

  // To set content externally:
  const setContentExternally = (markdown: string) => {
    const editor = get();
    if (editor) {
      editor.action(replaceAll(markdown));
    }
  };

  return (
    <div>
      {loading && <div>Loading editor...</div>}
      <Milkdown />
    </div>
  );
}
```

## Code Examples

### Search Component with Debounce

```typescript
// components/search/SearchBar.tsx
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { useSearch } from '../../hooks/useSearch';
import { Input } from '../ui/Input';
import { Spinner } from '../ui/Spinner';

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const navigate = useNavigate();

  // Debounce per D-05: 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data, isLoading, isError } = useSearch({ q: debouncedQuery });

  const handleSelect = (slug: string) => {
    navigate(`/page/${slug}`);
  };

  return (
    <div className="relative w-full max-w-2xl">
      <Input
        type="search"
        placeholder="Search knowledge base..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full"
      />
      {isLoading && <Spinner className="absolute right-3 top-3" />}
      {data?.results && data.results.length > 0 && debouncedQuery && (
        <ul className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg">
          {data.results.slice(0, 5).map((result) => (
            <li
              key={result.slug}
              onClick={() => handleSelect(result.slug)}
              className="p-3 hover:bg-gray-100 cursor-pointer"
            >
              <div className="font-medium">{result.title}</div>
              <div className="text-sm text-gray-600 truncate">{result.snippet}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

### Cytoscape.js Graph Component

```typescript
// components/graph/KnowledgeGraph.tsx
import { useEffect, useRef, useCallback } from 'react';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { useGraphStore } from '../../stores/graphStore';
import { useGraph } from '../../hooks/useGraph';

// Register fCoSE layout
cytoscape.use(fcose);

const GRAPH_STYLE = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': 12,
      'width': 40,
      'height': 40,
    },
  },
  {
    selector: 'node[type="concept"]',
    style: { 'background-color': '#4CAF50' },
  },
  {
    selector: 'node[type="entity"]',
    style: { 'background-color': '#2196F3' },
  },
  {
    selector: 'node[type="document"]',
    style: { 'background-color': '#9E9E9E' },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#FF5722',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#ccc',
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#ccc',
    },
  },
  {
    selector: 'edge[type="contradicts"]',
    style: {
      'line-color': '#F44336',
      'line-style': 'dashed',
    },
  },
];

interface KnowledgeGraphProps {
  depth?: number;
  maxNodes?: number;
}

export function KnowledgeGraph({ depth = 2, maxNodes = 50 }: KnowledgeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const selectedNode = useGraphStore((s) => s.selectedNode);
  const selectNode = useGraphStore((s) => s.selectNode);

  const { data, isLoading } = useGraph({ depth, max_nodes: maxNodes });

  useEffect(() => {
    if (!containerRef.current || !data) return;

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: data.nodes.map((n) => ({
          data: { id: n.id, label: n.label, type: n.type, confidence: n.confidence },
        })),
        edges: data.edges.map((e, i) => ({
          data: { id: e.id || `edge-${i}`, source: e.source, target: e.target, type: e.type, weight: e.weight },
        })),
      },
      style: GRAPH_STYLE,
      layout: { name: 'fcose', animate: true, idealEdgeLength: 100 },
    });

    // Click handler for node selection
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target as NodeSingular;
      selectNode(node.id());
    });

    // Double-click for expansion
    cyRef.current.on('dblclick', 'node', async (evt) => {
      const node = evt.target as NodeSingular;
      // Trigger subgraph fetch (handled by parent component via store)
    });

    return () => cyRef.current?.destroy();
  }, [data, selectNode]);

  // Update selection state
  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.nodes().unselect();
      if (selectedNode) {
        cyRef.current.$(`node[id="${selectedNode}"]`).select();
      }
    }
  }, [selectedNode]);

  return (
    <div ref={containerRef} className="w-full h-full min-h-[600px] bg-gray-50 rounded-lg" />
  );
}
```

### WebSocket Hook

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WSMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

export function useWebSocket(sessionId: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    setStatus('connecting');
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

    ws.onopen = () => {
      setStatus('connected');
      reconnectAttempts.current = 0;
      // Sync: refetch current state (per Pattern 2)
      queryClient.refetchQueries({ queryKey: ['agents'] });
      queryClient.refetchQueries({ queryKey: ['graph'] });
    };

    ws.onclose = () => {
      setStatus('disconnected');
      // Exponential backoff: 1s, 2s, 4s, ... max 30s (per D-21)
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectAttempts.current++;
      setTimeout(connect, delay);
    };

    ws.onmessage = (event) => {
      const message: WSMessage = JSON.parse(event.data);
      // Route events to query invalidation
      switch (message.type) {
        case 'agent_status':
        case 'workflow_progress':
          queryClient.invalidateQueries({ queryKey: ['agents'] });
          break;
        case 'page_updated':
          queryClient.invalidateQueries({ queryKey: ['page', message.payload.slug] });
          queryClient.invalidateQueries({ queryKey: ['graph'] });
          break;
      }
    };

    wsRef.current = ws;
  }, [sessionId, queryClient]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
  }, [connect]);

  // Heartbeat (per D-22: 30s interval)
  useEffect(() => {
    if (status !== 'connected') return;
    heartbeatRef.current = setInterval(() => {
      wsRef.current?.send(JSON.stringify({ type: 'ping' }));
    }, 30000);
    return () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
    };
  }, [status]);

  const send = useCallback((message: unknown) => {
    wsRef.current?.send(JSON.stringify(message));
  }, []);

  return { status, send };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Class components | Hooks + Function components | React 16.8 (2019) | Simpler mental model, easier testing |
| Redux with actions/reducers | Zustand with slices | ~2022 | Less boilerplate, better TypeScript |
| SWR | TanStack Query v5 | ~2023 | Better mutations API, devtools |
| Default Cytoscape layouts | fCoSE extension | ~2021 | Better quality for most graphs |
| TipTap | Milkdown | ~2023 | Better Markdown fidelity, ProseMirror base |

**Deprecated/outdated:**

- **createClass:** Use function components with hooks
- **componentWillReceiveProps:** Use useEffect with dependencies
- **connect from React-Redux:** Use hooks from react-redux or Zustand
- **force-directed layout (vanilla):** Use fCoSE for better quality and speed

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TanStack Query handles WebSocket reconnection gracefully with refetchOnReconnect | Pattern 2 | May need manual invalidation logic |
| A2 | fCoSE layout quality is acceptable for knowledge graphs up to 500 nodes | Pitfall 1 | May need cosmos-over-cytoscape GPU layout for larger graphs |
| A3 | Milkdown commonmark preset covers all Wiki page formatting needs | Code Examples | May need additional plugins for tables, math |
| A4 | WebSocket message types match backend event names exactly | WebSocket Hook | Message routing will fail silently |

## Open Questions

1. **Should the graph use WebGL renderer for >500 nodes?**
   - What we know: Cytoscape has `cytoscape-canvas` and `cosmos-over-cytoscape` extensions
   - What's unclear: Performance trade-offs, setup complexity
   - Recommendation: Start with canvas renderer, benchmark at 500 nodes, upgrade if needed

2. **How should editor handle concurrent edits?**
   - What we know: Write Queue provides durability; WebSocket broadcasts updates
   - What's unclear: Conflict resolution strategy (last-write-wins vs. merge)
   - Recommendation: Last-write-wins initially; add conflict detection in Phase 4

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Node.js | Build/runtime | Check | - | - |
| npm | Package management | Check | - | pnpm/yarn |
| Chrome/Firefox | Browser runtime | Check | - | - |

**Dependencies to verify at runtime:**

```bash
# Check Node.js version (need >=18 for native fetch)
node --version
npm --version
```

## Validation Architecture

**Skipped:** Per `.planning/config.json`, `workflow.nyquist_validation` is `false`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Backend handles; frontend uses session cookie |
| V3 Session Management | yes | Use httpOnly cookies; validate session in WebSocket |
| V4 Access Control | no | Backend enforces; frontend shows/hides based on state |
| V5 Input Validation | yes | Zod schemas for all form inputs |
| V6 Cryptography | no | HTTPS only; no client-side crypto |

### Known Threat Patterns for React + WebSocket

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via Markdown content | Tampering | DOMPurify sanitize before render; Milkdown handles |
| WebSocket hijacking | Spoofing | Validate session_id on server; use wss:// in production |
| CSRF on mutations | Tampering | Use SameSite cookies; validate origin header |
| Sensitive data in localStorage | Information disclosure | Store only non-sensitive UI preferences |

## Sources

### Primary (HIGH confidence)

- /reactjs/react.dev - React 19 hooks (use(), useOptimistic, useFormStatus, Actions)
- /pmndrs/zustand - Slices pattern, persist middleware, async actions
- /cytoscape/cytoscape.js - Layout algorithms (fCoSE, CoSE, concentric), performance docs
- /milkdown/milkdown - React integration (useEditor, MilkdownProvider), GFM preset

### Secondary (MEDIUM confidence)

- WebSearch: "TanStack Query WebSocket invalidation" - verified with official docs
- WebSearch: "Cytoscape.js large graph performance" - verified with GitHub issues

### Tertiary (LOW confidence)

None - all critical claims verified through primary sources

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - All versions verified from npm registry (2026-04-29)
- Architecture: HIGH - Based on established patterns from Zustand and TanStack Query docs
- Pitfalls: HIGH - WebSocket desync documented in PITFALLS.md; Cytoscape performance from official docs
- Code examples: MEDIUM - Based on Context7 docs but not tested in this codebase

**Research date:** 2026-04-29
**Valid until:** 2026-05-29 (React ecosystem changes frequently)
