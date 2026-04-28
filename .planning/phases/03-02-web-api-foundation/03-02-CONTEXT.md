# Phase 03-02: Web API Foundation - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning
**Source:** Auto-generated from ROADMAP + REQUIREMENTS + Design Document

<domain>
## Phase Boundary

实现 Smart Agent Wiki 的 Web API 基础：FastAPI 服务器、WebSocket 实时更新、Search API、Graph API、Page API。用户可以通过 Web 界面搜索知识库、浏览图谱、编辑 Wiki 页面。

此阶段依赖 Phase 03-01 的 CollaborateEngine 作为后端，为 Phase 03-03 的 React 前端提供 API。

</domain>

<decisions>
## Implementation Decisions

### FastAPI Server (WEB-01)
- **D-01:** FastAPI 服务器提供 RESTful API 和 WebSocket 支持
- **D-02:** CLI 命令 `saw web` 启动服务器，默认端口 8000
- **D-03:** 支持 CORS 配置以便前端开发

### WebSocket Real-time (WEB-01)
- **D-04:** WebSocket 端点用于实时更新推送
- **D-05:** 事件类型：agent_status、workflow_progress、page_updated
- **D-06:** 连接管理和心跳检测

### Search API (WEB-01)
- **D-07:** GET /api/search - BM25 + FTS5 搜索
- **D-08:** 返回结果包含 snippet、citation、confidence
- **D-09:** 支持分页和过滤（按类型、标签、置信度）

### Graph API (WEB-02)
- **D-10:** GET /api/graph - 获取知识图谱节点和边
- **D-11:** GET /api/graph/{entity} - 获取实体详情和关系
- **D-12:** 支持 BFS/DFS 遍历参数

### Page API (WEB-03)
- **D-13:** GET /api/pages - 列出 Wiki 页面
- **D-14:** GET /api/pages/{slug} - 获取页面内容
- **D-15:** PUT /api/pages/{slug} - 更新页面（通过 Write Queue）
- **D-16:** DELETE /api/pages/{slug} - 删除页面

### Claude's Discretion
- FastAPI 路由的具体组织方式
- WebSocket 消息格式详细设计
- 错误响应格式和状态码
- API 版本控制策略
- 认证和授权方案（如需要）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Document
- `docs/smart_agent_wiki_design.md` — Web API 设计、端点定义、WebSocket 协议（Section 2.1 引擎五、Section 4.3 MCP 工具清单）

### Phase 03-01 Context (Foundation)
- `.planning/phases/03-01-multi-agent-foundation/03-01-CONTEXT.md` — Phase 03-01 的设计决策
- `.planning/phases/03-01-multi-agent-foundation/03-01-01-SUMMARY.md` — Agent、Dispatcher、A2A 协议实现
- `.planning/phases/03-01-multi-agent-foundation/03-01-02-SUMMARY.md` — Workflow、Policy、CollaborateEngine 实现

### Research Documents
- `.planning/research/ARCHITECTURE.md` — Hexagonal architecture、Write Queue 模式
- `.planning/research/PITFALLS.md` — FastAPI 陷阱、WebSocket 连接管理

### Project Context
- `.planning/PROJECT.md` — Vision、core value、constraints
- `.planning/REQUIREMENTS.md` — WEB-01~03 需求定义
- `.planning/ROADMAP.md` — Phase 03 定义、Success Criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets from Phase 01/02/03-01
- **Domain Layer**: Claims DB、Wiki pages、Graph、Index
- **Write Queue**: Outbox pattern for durable mutations
- **Query Engine**: Search、NL Query、Graph traversal
- **CollaborateEngine**: Agent dispatch、Workflow execution、Policy check
- **MCP Server**: FastMCP integration patterns

### Integration Points
- **Search API**: 复用 QueryEngine 的 search 方法
- **Graph API**: 复用 GraphStore 的 traversal 方法
- **Page API**: 通过 Write Queue 持久化变更
- **WebSocket**: 推送 Agent 和 Workflow 状态更新

### Established Patterns
- Hexagonal architecture with ports/adapters
- FastAPI routing and dependency injection
- Async/await for concurrent operations
- Pydantic models for request/response validation

</code_context>

<specifics>
## Specific Ideas

### API Endpoints Design

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

### WebSocket Event Types

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
      "snippet": "The transformer architecture...",
      "confidence": 3,
      "freshness": 7,
      "citations": ["claim:uuid-1", "claim:uuid-2"]
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 10
}
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 03-02 requirements are in scope.

</deferred>

---

*Phase: 03-02-web-api-foundation*
*Context gathered: 2026-04-28 via auto-generation*
