---
phase: 03-03-react-frontend
reviewed: 2026-04-29T12:00:00Z
depth: standard
files_reviewed: 42
files_reviewed_list:
  - web/index.html
  - web/package.json
  - web/postcss.config.js
  - web/src/App.tsx
  - web/src/__tests__/PageEditor.test.tsx
  - web/src/__tests__/useWebSocket.test.ts
  - web/src/components/common/ConfidenceBadge.tsx
  - web/src/components/common/FreshnessBadge.tsx
  - web/src/components/common/index.ts
  - web/src/components/dashboard/AgentCard.tsx
  - web/src/components/dashboard/AgentList.tsx
  - web/src/components/dashboard/ConnectionStatus.tsx
  - web/src/components/editor/EditorStatus.tsx
  - web/src/components/editor/EditorToolbar.tsx
  - web/src/components/editor/WikiEditor.tsx
  - web/src/components/editor/index.ts
  - web/src/components/graph/GraphControls.tsx
  - web/src/components/graph/GraphFilters.tsx
  - web/src/components/graph/KnowledgeGraph.tsx
  - web/src/components/graph/NodeDetail.tsx
  - web/src/components/search/ResultCard.tsx
  - web/src/components/search/SearchBar.tsx
  - web/src/components/search/SearchFilters.tsx
  - web/src/components/search/SearchResults.tsx
  - web/src/components/ui/Badge.tsx
  - web/src/components/ui/Input.tsx
  - web/src/components/ui/Pagination.tsx
  - web/src/components/ui/Spinner.tsx
  - web/src/hooks/useDebounce.ts
  - web/src/hooks/useGraph.ts
  - web/src/hooks/usePage.ts
  - web/src/hooks/useSearch.ts
  - web/src/hooks/useWebSocket.ts
  - web/src/index.css
  - web/src/lib/api.ts
  - web/src/main.tsx
  - web/src/pages/Dashboard.tsx
  - web/src/pages/Graph.tsx
  - web/src/pages/Home.tsx
  - web/src/pages/Page.tsx
  - web/src/pages/Search.tsx
  - web/src/routes/router.tsx
  - web/src/stores/dashboardStore.ts
  - web/src/stores/editorStore.ts
  - web/src/stores/graphStore.ts
  - web/src/stores/index.ts
  - web/src/stores/uiStore.ts
  - web/src/types/api.ts
  - web/src/types/cytoscape-fcose.d.ts
  - web/src/types/cytoscape.ts
  - web/src/types/websocket.ts
  - web/src/vite-env.d.ts
  - web/tailwind.config.js
  - web/tsconfig.json
  - web/tsconfig.node.json
  - web/vite.config.ts
findings:
  critical: 4
  warning: 8
  info: 5
  total: 17
status: issues_found
---

# Phase 03-03: Code Review Report

**Reviewed:** 2026-04-29T12:00:00Z
**Depth:** standard
**Files Reviewed:** 42
**Status:** issues_found

## Summary

Reviewed 42 TypeScript/React frontend files implementing the Smart Agent Wiki web interface. The codebase demonstrates solid React patterns with TanStack Query for data fetching, Zustand for state management, and Cytoscape for graph visualization. However, several critical issues were found related to WebSocket reconnection logic, editor state management race conditions, and non-functional UI controls. Type definitions are duplicated across files, and error handling is insufficient in several areas.

## Critical Issues

### CR-01: WebSocket Reconnection Continues After Unmount

**File:** `web/src/hooks/useWebSocket.ts:165-176`
**Issue:** The `ws.onclose` handler schedules a reconnection attempt via `setTimeout`, but this timeout is only cleared when `disconnect()` is explicitly called. If the component unmounts between `onclose` firing and the timeout callback executing, the reconnection will attempt to run on an unmounted component. The cleanup in `useEffect` calls `disconnect()`, but the race condition exists because `onclose` can fire after cleanup starts but before `disconnect` clears the timeout.
**Fix:**
```typescript
// Add a mounted ref to track component lifecycle
const isMountedRef = useRef(true);

// In connect(), wrap reconnection in isMounted check:
ws.onclose = () => {
  setStatus('disconnected');
  setConnectionStatus('disconnected');
  clearHeartbeat();

  if (!isMountedRef.current) return; // Don't reconnect if unmounted

  const delay = getReconnectDelay();
  reconnectTimeoutRef.current = setTimeout(() => {
    if (isMountedRef.current) {
      reconnectAttemptsRef.current++;
      connect();
    }
  }, delay);
};

// In useEffect cleanup:
useEffect(() => {
  // ...
  return () => {
    isMountedRef.current = false;
    disconnect();
  };
}, [autoConnect, connect, disconnect]);
```

### CR-02: WikiEditor Initialization Race Condition

**File:** `web/src/components/editor/WikiEditor.tsx:86-91`
**Issue:** The `isInitializedRef` is set to true after a 100ms `setTimeout` to prevent dirty state from being set during initial render. However, this creates a race condition: if the user types within the first 100ms, `isInitializedRef.current` is false, and the dirty state will not be updated. Conversely, if Milkdown fires `markdownUpdated` before 100ms (possible during initial render with non-empty content), the dirty flag could incorrectly remain false.
**Fix:**
```typescript
// Use a more reliable approach: compare against initial content
const initialContentRef = useRef(initialContent);

// In markdownUpdated callback:
ctx.get(listenerCtx).markdownUpdated((_ctx, markdown, prevMarkdown) => {
  // Only set dirty if content changed AND it's different from initial
  if (markdown !== prevMarkdown && markdown !== initialContentRef.current) {
    setDirty(true);
    contentRef.current = markdown;
  }
});

// Update ref when initialContent prop changes
useEffect(() => {
  initialContentRef.current = initialContent;
  contentRef.current = initialContent;
  setDirty(false); // Reset dirty when content is loaded
}, [initialContent, setDirty]);
```

### CR-03: Save Button Does Not Trigger Actual Save Operation

**File:** `web/src/pages/Page.tsx:143-149`
**Issue:** The "Save Changes" button in Page.tsx only sets `mode` to 'view' and relies on the button's disabled state to check `isDirty`. However, the actual save operation is triggered through `WikiEditor`'s internal `handleSave` callback via keyboard shortcut (Ctrl+S). Clicking this button does NOT call `handleSave` or the `updatePage` mutation. The save operation is never triggered, leading to data loss.
**Fix:**
```typescript
// Add a ref to access WikiEditor's save function
const editorSaveRef = useRef<(() => void) | null>(null);

// In handleSave callback passed to WikiEditor:
<WikiEditorWrapper
  slug={slug || ''}
  initialContent={page.content}
  onSave={(content) => {
    updatePage({ content });
    editorSaveRef.current = null;
  }}
  readOnly={mode === 'view'}
/>

// Then in the save button:
<button
  onClick={() => {
    // Trigger the save through the editor's internal mechanism
    // Or directly call the mutation with current content
    if (editorContentRef.current) {
      updatePage({ content: editorContentRef.current });
    }
    setMode('view');
  }}
  className="..."
  disabled={isSaving || !isDirty}
>
```

### CR-04: Graph Controls Are Non-Functional

**File:** `web/src/pages/Graph.tsx:65-68`
**Issue:** The `onZoomIn`, `onZoomOut`, and `onFit` handlers passed to `GraphControls` are empty functions with comments saying "Handled by Cytoscape internally". However, Cytoscape does NOT handle zoom controls internally - these must be explicitly implemented by calling `cy.zoom()`, `cy.fit()`, etc. on the Cytoscape instance. The buttons in the UI do nothing when clicked.
**Fix:**
```typescript
// In Graph.tsx, expose Cytoscape instance methods:
const cyRef = useRef<Core | null>(null);

// Pass callbacks to KnowledgeGraph to receive cy instance
<KnowledgeGraph
  // ...
  onCyReady={(cy) => { cyRef.current = cy; }}
/>

// Then implement zoom controls:
<GraphControls
  onZoomIn={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
  onZoomOut={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
  onFit={() => cyRef.current?.fit()}
/>
```

## Warnings

### WR-01: Unused State Variable

**File:** `web/src/pages/Search.tsx:18`
**Issue:** The `inputQuery` state variable is declared with `useState` and its setter `setInputQuery` is called, but the value `inputQuery` itself is never read. The state is unnecessary since the query is managed via URL search params.
**Fix:**
```typescript
// Remove the unused state entirely
// const [inputQuery, setInputQuery] = useState(query); // DELETE

// Update handleSearch to not use setInputQuery:
const handleSearch = (newQuery: string) => {
  setSearchParams((params) => {
    params.set('q', newQuery);
    params.set('page', '1');
    if (!newQuery) params.delete('q');
    return params;
  });
};
```

### WR-02: API Error Response Body Discarded

**File:** `web/src/lib/api.ts:35-37`
**Issue:** When the API returns an error response, only the status code and text are included in the error message. The response body likely contains useful error details (validation errors, specific error codes) that are discarded. This makes debugging API issues difficult.
**Fix:**
```typescript
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  // ... existing code ...

  if (!response.ok) {
    let errorMessage = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorBody = await response.json();
      if (errorBody.detail || errorBody.message) {
        errorMessage = errorBody.detail || errorBody.message;
      }
    } catch {
      // Response body not JSON, use default message
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
```

### WR-03: WebSocket Error Not Handled

**File:** `web/src/hooks/useWebSocket.ts:178-179`
**Issue:** The `ws.onerror` handler only logs the error to console without any recovery mechanism or user notification. WebSocket errors could indicate network issues, authentication failures, or server problems that should be communicated to the user.
**Fix:**
```typescript
ws.onerror = (err) => {
  console.error('WebSocket error:', err);
  setStatus('disconnected');
  setConnectionStatus('disconnected');
  // Optionally: trigger a notification to the user
  // or attempt immediate reconnect
};
```

### WR-04: Suggestions API Response Not Validated

**File:** `web/src/components/search/SearchBar.tsx:39-44`
**Issue:** The API response for suggestions is assumed to be `string[]` without validation. If the API returns an unexpected structure (error object, null, different array), the `.map()` call could fail. Additionally, slugs are generated by replacing spaces with hyphens without validation.
**Fix:**
```typescript
const fetchSuggestions = async () => {
  setIsLoadingSuggestions(true);
  try {
    const titles = await api.get<unknown>('/api/search/suggestions', {
      q: debouncedQuery,
      limit: 5,
    });
    // Validate response is an array of strings
    if (Array.isArray(titles) && titles.every(t => typeof t === 'string')) {
      setSuggestions(
        titles.map(title => ({
          title,
          slug: encodeURIComponent(title.toLowerCase().replace(/\s+/g, '-'))
        }))
      );
    } else {
      setSuggestions([]);
    }
  } catch {
    setSuggestions([]);
  } finally {
    setIsLoadingSuggestions(false);
  }
};
```

### WR-05: Duplicate Type Definitions

**File:** `web/src/types/api.ts` and `web/src/types/websocket.ts`
**Issue:** Types `AgentStatus`, `WorkflowProgress`, `WSMessage`, and `WSMessageType` are defined in both files with slight differences. In `api.ts`, `AgentStatus.task` is optional (`task?: string`) while in `websocket.ts` it's `task: string | null`. This creates type inconsistencies and potential runtime issues.
**Fix:**
```typescript
// Keep all shared types in one file (api.ts)
// Remove duplicates from websocket.ts
// Export from a single source:
// types/websocket.ts should only contain WebSocket-specific types not in api.ts
```

### WR-06: Slug Generation May Produce Invalid Slugs

**File:** `web/src/components/graph/NodeDetail.tsx:64`
**Issue:** The slug is generated by converting the label to lowercase and replacing spaces with hyphens. This does not handle special characters, non-ASCII characters, or multiple consecutive spaces, which could produce invalid or inconsistent slugs.
**Fix:**
```typescript
function labelToSlug(label: string): string {
  return label
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-')      // Replace spaces with hyphens
    .replace(/-+/g, '-');      // Collapse multiple hyphens
}

// Usage:
<Link to={`/page/${labelToSlug(nodeData.label)}`}>
```

### WR-07: Unused Parameter Masked with Underscore

**File:** `web/src/components/editor/WikiEditor.tsx:27`
**Issue:** The `slug` parameter is prefixed with underscore (`slug: _slug`) to suppress TypeScript's unused variable warning. This hides the fact that `slug` should probably be used for page identification, cache keys, or logging. The underscore pattern is an anti-pattern that masks potential bugs.
**Fix:**
```typescript
// Either use the parameter:
export function WikiEditor({
  slug,
  initialContent,
  onSave,
  readOnly = false,
}: WikiEditorProps) {
  // Use slug for logging, cache keys, or remove from interface
  console.debug(`WikiEditor mounted for slug: ${slug}`);
  // ...
}

// Or remove from interface if truly not needed
```

### WR-08: Filter Value State Inconsistency

**File:** `web/src/components/graph/GraphFilters.tsx:54`
**Issue:** The select value uses `entityTypeFilter ?? ''` for display, but `onChange` uses `e.target.value || null`. This creates inconsistency: empty string is displayed but null is stored. The filter state should consistently use either empty string or null.
**Fix:**
```typescript
// Be consistent with null for "no filter":
<select
  value={entityTypeFilter ?? ''}
  onChange={(e) => setEntityTypeFilter(e.target.value || null)}
>
```

## Info

### IN-01: Duplicate Constants Across Files

**File:** Multiple files
**Issue:** `CONFIDENCE_LABELS` is defined in `ConfidenceBadge.tsx`, `ResultCard.tsx`, and `NodeDetail.tsx`. `FRESHNESS_LABELS` is defined in `FreshnessBadge.tsx` and `ResultCard.tsx`. This is code duplication that should be consolidated.
**Fix:** Create a `constants.ts` file in `src/lib/` or `src/types/` and export these constants for reuse.

### IN-02: Non-Null Assertion on Root Element

**File:** `web/src/main.tsx:17`
**Issue:** `document.getElementById('root')!` uses a non-null assertion. While typically safe in React apps, it will crash with a cryptic error if the element doesn't exist.
**Fix:**
```typescript
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found. Ensure index.html contains <div id="root"></div>');
}
createRoot(rootElement).render(/* ... */);
```

### IN-03: Catch Block Returns Generic Error

**File:** `web/src/components/editor/EditorStatus.tsx:84`
**Issue:** The `formatTime` function catches any error and returns 'unknown'. This could mask unexpected errors and makes debugging difficult.
**Fix:**
```typescript
function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return 'invalid';
    }
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (error) {
    console.warn('Failed to format timestamp:', timestamp, error);
    return 'unknown';
  }
}
```

### IN-04: NavLink ClassName Logic Duplicated

**File:** `web/src/App.tsx:10-27`
**Issue:** The `NavLink` className function `({ isActive }) => isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600'` is repeated three times. This could be extracted to a helper function.
**Fix:**
```typescript
const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600';

// Usage:
<NavLink to="/search" className={navLinkClass}>Search</NavLink>
```

### IN-05: Graph Controls Zoom State Not Connected

**File:** `web/src/components/graph/GraphControls.tsx:10-13`
**Issue:** The `GraphControls` component reads `viewMode` and `layout` from the store, but the zoom state (`zoom`) is read but never updated by the zoom buttons. The zoom controls are disconnected from the store state.
**Fix:** Connect the zoom controls to the store's `setZoom` action when implementing the actual zoom functionality (related to CR-04).

---

_Reviewed: 2026-04-29T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
