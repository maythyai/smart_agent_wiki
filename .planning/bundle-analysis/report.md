# Bundle Analysis Report

**Generated:** 2026-05-03
**Tool:** rollup-plugin-visualizer

---

## Summary

| Metric | Value |
|--------|-------|
| Total Bundle Size | 1,410 KB (uncompressed) |
| Gzip Size | 427 KB |
| CSS Size | 34 KB |

---

## Build Output

```
dist/index.html                     0.46 kB │ gzip:   0.31 kB
dist/assets/index-CdzL0us2.css     34.02 kB │ gzip:   7.13 kB
dist/assets/index-CI0Aq6af.js   1,410.27 kB │ gzip: 427.07 kB
```

---

## Large Dependencies Analysis

The bundle size warning indicates the main JS chunk exceeds 500KB. Key contributors:

### Milkdown Editor
- **@milkdown/react**: ~200KB
- **@milkdown/kit**: ~150KB
- **Total Milkdown**: ~350KB (estimated)

### Other Large Dependencies
- **cytoscape**: ~150KB (graph visualization)
- **react + react-dom**: ~140KB
- **@tanstack/react-query**: ~50KB

---

## Optimization Recommendations

### 1. Milkdown Lazy Loading (Recommended)
Milkdown is used only on the Wiki page editor. Implement lazy loading:

```typescript
import { lazy, Suspense } from 'react'

const MilkdownEditor = lazy(() => import('./MilkdownEditorInner'))

function PageEditor() {
  return (
    <Suspense fallback={<div>Loading editor...</div>}>
      <MilkdownEditor />
    </Suspense>
  )
}
```

**Expected savings:** ~300KB from initial bundle

### 2. Cytoscape Lazy Loading
Graph visualization is only used on the Graph page. Similar lazy loading pattern applies.

**Expected savings:** ~140KB from initial bundle

### 3. Code Splitting by Route
Use React Router's lazy loading to split by page:

```typescript
const Graph = lazy(() => import('./pages/Graph'))
const Page = lazy(() => import('./pages/Page'))
```

---

## Decision: Milkdown Lazy Loading

**Status:** RECOMMENDED

Milkdown + dependencies (~350KB) exceed the 100KB threshold defined in D-11. Lazy loading should be implemented in a future optimization phase.

---

## Visualization

Open `stats.html` in a browser to see the full interactive dependency tree:
- File: `.planning/bundle-analysis/stats.html`

---

*Report generated: 2026-05-03*
*Build tool: Vite 8.0.10 + rolldown*