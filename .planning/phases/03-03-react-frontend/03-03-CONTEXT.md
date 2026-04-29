# Phase 03-03: React Frontend - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning
**Source:** Auto-generated from ROADMAP + REQUIREMENTS + Design Document + Web API Context

<domain>
## Phase Boundary

实现 Smart Agent Wiki 的 React 前端：Search UI、Cytoscape.js 知识图谱、Milkdown Wiki 页面编辑器、Agent 状态仪表板、WebSocket 实时更新。用户可以通过 Web 界面搜索知识库、可视化浏览图谱、审核和编辑 LLM 生成的 Wiki 页面。

此阶段依赖 Phase 03-02 的 Web API 作为后端，复用已实现的 Search API、Graph API、Page API 和 WebSocket 端点。

</domain>

<decisions>
## Implementation Decisions

### 技术栈 (WEB-01~03)
- **D-01:** React 19 + TypeScript 作为前端框架
- **D-02:** Vite 作为构建工具（更快 HMR，ESM 原生支持）
- **D-03:** TailwindCSS 用于快速样式开发
- **D-04:** React Router 用于单页应用路由

### Search UI (WEB-01)
- **D-05:** 搜索框实时自动补全（debounce 300ms）
- **D-06:** 搜索结果展示：标题、摘要、置信度徽章、新鲜度指示、内联引用
- **D-07:** 支持分页加载（无限滚动或分页按钮）
- **D-08:** 过滤器：按类型、标签、置信度筛选

### Knowledge Graph (WEB-02)
- **D-09:** Cytoscape.js 用于图谱可视化
- **D-10:** 图谱模式：全图（<50 节点）→ 社区视图（50-200）→ 主题聚类（>200）
- **D-11:** 交互功能：平移、缩放、拖拽节点、点击查看详情
- **D-12:** 过滤器：按实体类型、关系类型、置信度过滤节点

### Wiki Page Editor (WEB-03)
- **D-13:** Milkdown 作为 WYSIWYG Markdown 编辑器
- **D-14:** 编辑模式：查看 → 编辑 → 提交审核
- **D-15:** 提交变更通过 Write Queue API 持久化
- **D-16:** 支持 approve/reject 操作（调用 Page API）

### Agent Dashboard
- **D-17:** 实时显示 Agent 状态（通过 WebSocket 订阅）
- **D-18:** Agent 列表：名称、状态、当前任务、完成进度
- **D-19:** Workflow 执行可视化：步骤、耗时、结果

### WebSocket 集成
- **D-20:** 事件类型：agent_status、workflow_progress、page_updated
- **D-21:** 自动重连机制（exponential backoff）
- **D-22:** 心跳检测（30s interval）

### Claude's Discretion
- 前端目录结构（src/components vs src/pages vs src/hooks）
- 状态管理方案（React Query vs Zustand vs Context）
- 图谱布局算法选择
- 编辑器工具栏设计
- 错误处理和加载状态

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Document
- `docs/smart_agent_wiki_design.md` — Web UI 设计、Cytoscape.js 集成、Milkdown 编辑器（Section 2.1 引擎五、Section 4.1 技术选型）

### Phase 03-02 Context (API Foundation)
- `.planning/phases/03-02-web-api-foundation/03-02-CONTEXT.md` — API 端点定义、WebSocket 协议
- `.planning/phases/03-02-web-api-foundation/03-02-01-SUMMARY.md` — FastAPI 基础实现
- `.planning/phases/03-02-web-api-foundation/03-02-02-SUMMARY.md` — Search/Graph API 实现
- `.planning/phases/03-02-web-api-foundation/03-02-03-SUMMARY.md` — Page API + CLI web 命令

### Phase 03-01 Context (Agent Foundation)
- `.planning/phases/03-01-multi-agent-foundation/03-01-CONTEXT.md` — Agent 角色、A2A 协议

### Research Documents
- `.planning/research/ARCHITECTURE.md` — Hexagonal architecture、Write Queue 模式
- `.planning/research/PITFALLS.md` — React 陷阱、WebSocket 连接管理

### Project Context
- `.planning/PROJECT.md` — Vision、core value、constraints
- `.planning/REQUIREMENTS.md` — WEB-01~03 需求定义
- `.planning/ROADMAP.md` — Phase 03 定义、Success Criteria

### Backend API Implementation
- `src/saw/drivers/web/app.py` — FastAPI application factory
- `src/saw/drivers/web/routes/search.py` — Search API endpoints
- `src/saw/drivers/web/routes/graph.py` — Graph API endpoints
- `src/saw/drivers/web/routes/pages.py` — Page API endpoints
- `src/saw/drivers/web/websocket.py` — WebSocket connection manager

</canonical_refs>

<code_context>
## Existing Code Insights

### Backend API Endpoints (from 03-02)

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/search | GET | BM25 + FTS5 搜索 |
| /api/search/suggestions | GET | 搜索建议 |
| /api/graph | GET | 知识图谱节点和边 |
| /api/graph/{entity} | GET | 实体详情和关系 |
| /api/pages | GET | Wiki 页面列表 |
| /api/pages/{slug} | GET | 页面内容 |
| /api/pages/{slug} | PUT | 更新页面 |
| /api/pages/{slug} | DELETE | 删除页面 |
| /ws | WS | WebSocket 实时更新 |

### WebSocket Message Format

```json
{
  "event": "agent_status",
  "data": {
    "agent": "Librarian",
    "status": "running",
    "task": "indexing"
  }
}
```

### Search Response Format

```json
{
  "results": [
    {
      "slug": "transformer-architecture",
      "title": "Transformer Architecture",
      "snippet": "...",
      "confidence": 3,
      "freshness": 7,
      "citations": ["claim:uuid-1"]
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 10
}
```

</code_context>

<specifics>
## Specific Ideas

### Frontend Directory Structure

```
src/
├── components/
│   ├── search/
│   │   ├── SearchBar.tsx
│   │   ├── SearchResults.tsx
│   │   └── Filters.tsx
│   ├── graph/
│   │   ├── GraphView.tsx
│   │   ├── NodeDetail.tsx
│   │   └── GraphFilters.tsx
│   ├── editor/
│   │   ├── MilkdownEditor.tsx
│   │   ├── EditorToolbar.tsx
│   │   └── CitationPreview.tsx
│   └── dashboard/
│       ├── AgentCard.tsx
│       ├── WorkflowVisualizer.tsx
│       └── StatusBar.tsx
├── pages/
│   ├── Home.tsx
│   ├── Search.tsx
│   ├── Graph.tsx
│   ├── Page.tsx
│   └── Dashboard.tsx
├── hooks/
│   ├── useWebSocket.ts
│   ├── useSearch.ts
│   └── useGraph.ts
├── services/
│   ├── api.ts
│   └── websocket.ts
└── App.tsx
```

### UI Components Design

**Search Bar:**
- 全宽搜索框，带搜索图标和清除按钮
- 自动补全下拉列表（显示最近搜索和热门建议）
- 加载状态 spinner

**Graph View:**
- Cytoscape.js canvas 占据主要区域
- 右侧面板显示节点详情
- 左上角过滤器面板
- 支持缩放控制（+/-按钮）

**Page Editor:**
- Milkdown 编辑器作为主要内容区域
- 顶部工具栏：粗体、斜体、链接、引用、标题
- 右侧预览面板（可选）
- 底部操作栏：保存草稿、提交审核、取消

### Cytoscape.js Node Styling

```javascript
const nodeStyle = {
  'label': 'data(label)',
  'background-color': ele => confidenceColor(ele.data('confidence')),
  'border-width': 2,
  'border-color': '#333',
  'text-valign': 'center',
  'text-halign': 'center',
  'font-size': 12
};
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 03-03 requirements are in scope.

</deferred>

---

*Phase: 03-03-react-frontend*
*Context gathered: 2026-04-29 via auto-generation*
