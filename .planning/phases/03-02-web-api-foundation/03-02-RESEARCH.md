# Phase 03-02: Web API Foundation - Research

**Researched:** 2026-04-28
**Domain:** FastAPI Web API + WebSocket real-time
**Confidence:** HIGH

## Summary

Phase 03-02 实现 Smart Agent Wiki 的 Web API 基础：FastAPI 服务器、WebSocket 实时更新、Search API、Graph API、Page API。此阶段复用 Phase 01 的 Query Engine 和 Phase 03-01 的 CollaborateEngine，为 Phase 03-03 的 React 前端提供完整的后端 API。

**Primary recommendation:** 使用 FastAPI 应用工厂模式，将现有 Engine 层作为依赖注入，WebSocket 通过 Event Bus 订阅实现实时推送，REST API 遵循 JSON:API 规范返回结构化响应。

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** FastAPI 服务器提供 RESTful API 和 WebSocket 支持
- **D-02:** CLI 命令 `saw web` 启动服务器，默认端口 8000
- **D-03:** 支持 CORS 配置以便前端开发
- **D-04:** WebSocket 端点用于实时更新推送
- **D-05:** 事件类型：agent_status、workflow_progress、page_updated
- **D-06:** 连接管理和心跳检测
- **D-07:** GET /api/search - BM25 + FTS5 搜索
- **D-08:** 返回结果包含 snippet、citation、confidence
- **D-09:** 支持分页和过滤（按类型、标签、置信度）
- **D-10:** GET /api/graph - 获取知识图谱节点和边
- **D-11:** GET /api/graph/{entity} - 获取实体详情和关系
- **D-12:** 支持 BFS/DFS 遍历参数
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

### Deferred Ideas (OUT OF SCOPE)

None — all Phase 03-02 requirements are in scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WEB-01 | Web UI search interface | Search API (D-07~09) + Query Engine 复用 |
| WEB-02 | Knowledge graph visualization (Cytoscape.js) | Graph API (D-10~12) + GraphStore 复用 |
| WEB-03 | Wiki page editor (Milkdown) | Page API (D-13~16) + Write Queue 复用 |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| REST API routing | API Server | — | FastAPI 作为 driving adapter，调用 Engine 层 |
| WebSocket broadcasting | API Server | Event Bus | WebSocket Manager 订阅 Event Bus，按 session 分发 |
| Search query processing | Query Engine | API Server | 复用现有 FTS5 + BM25 逻辑，API 层仅做参数映射 |
| Graph traversal | Query Engine | API Server | 复用现有 BFS/DFS 逻辑，API 层仅做参数映射 |
| Page CRUD | Write Queue | API Server | 所有写入必须经过 Write Queue 持久化，API 层触发入队 |
| Event publication | All Engines | — | 各 Engine 在状态变更时发布事件 |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.136.1 | Web framework | 异步原生、Pydantic v2 验证、自动 OpenAPI；Phase 01 已选型 |
| Pydantic | 2.12.5 | 数据验证 | FastAPI 依赖；定义请求/响应 schema |
| uvicorn | 0.42.0+ | ASGI 服务器 | FastAPI 标准运行时；CLI `saw web` 使用 |
| PyYAML | 6.0+ | 配置文件 | 已在 pyproject.toml；解析 OpenAPI 扩展配置 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28+ | HTTP 客户端 | TestClient 底层依赖；API 测试 |
| pytest-asyncio | 0.24+ | 异步测试 | WebSocket 端点测试 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Flask | 同步模型，WebSocket 支持差，不符合异步架构 |
| FastAPI | Starlette | 更底层，需要手动实现更多功能 |
| uvicorn | hypercorn | 更慢，HTTP/2 对 WebSocket 无增益 |
| Pydantic | dataclasses | 无自动验证、无 JSON Schema 生成 |

**Installation:**
```bash
# 已在 pyproject.toml 中
pip install fastapi pydantic uvicorn httpx pytest-asyncio
```

**Version verification:**
```bash
pip show fastapi pydantic uvicorn | grep -E "^(Name|Version):"
```

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Driving Adapters                               │
│   CLI (Typer)   │   MCP Server   │   [Web API (FastAPI)]   │ Obsidian │
└───────┬────────┴───────┬────────┴──────────┬───────────────┴────┬─────┘
        │                │                      │                   │
        v                v                      v                   v
┌───────────────────────────────────────────────────────────────────────┐
│                         API Gateway Layer                               │
│    ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│    │ REST Routes │    │ WebSocket   │    │ Middleware              │  │
│    │ /api/*      │    │ /ws/{sid}   │    │ CORS, Error, Logging    │  │
│    └──────┬──────┘    └──────┬──────┘    └─────────────────────────┘  │
└───────────┼──────────────────┼──────────────────────────────────────────┘
            │                  │
            v                  v
┌───────────────────────────────────────────────────────────────────────┐
│                          Engine Layer                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │
│  │ Query   │ │ Govern  │ │ Learn   │ │ Ingest  │ │ Collaborate     │ │
│  │ Engine  │ │ Engine  │ │ Engine  │ │ Engine  │ │ Engine         │ │
│  │ [复用]  │ │ [复用]  │ │ [复用]  │ │ [复用]  │ │ [复用]         │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────────────┘ │
│       │           │           │           │            │              │
│       v           v           v           v            v              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                     Event Bus (asyncio.Queue)                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
            │
            v
┌───────────────────────────────────────────────────────────────────────┐
│                      Write Queue (Outbox Pattern)                      │
│           Durable SQLite outbox -> parallel dispatch to sinks          │
└───────────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
src/saw/
├── drivers/
│   ├── cli/           # 已有：Typer CLI
│   ├── mcp/           # 已有：FastMCP server
│   └── web/           # [新增] FastAPI Web API
│       ├── __init__.py
│       ├── app.py           # Application factory
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── search.py    # GET /api/search
│       │   ├── graph.py     # GET /api/graph, /api/graph/{entity}
│       │   ├── pages.py     # GET/PUT/DELETE /api/pages/*
│       │   └── websocket.py # WS /ws/{session_id}
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── search.py    # SearchRequest, SearchResponse
│       │   ├── graph.py     # GraphRequest, GraphResponse
│       │   └── page.py     # PageResponse, PageUpdate
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── cors.py      # CORS 配置
│       │   └── errors.py    # 统一错误处理 (RFC 7807)
│       └── websocket.py     # ConnectionManager
├── engines/
│   ├── query/         # 已有：QueryEngine, Search, Graph
│   ├── collaborate/   # 已有：CollaborateEngine
│   └── ...
└── domain/
    └── events.py      # 已有：事件定义
```

### Pattern 1: Application Factory

**What:** 使用工厂函数创建 FastAPI app，注入 Engine 依赖，支持测试时使用 mock。

**When to use:** 所有 FastAPI 项目，便于测试和依赖管理。

**Example:**
```python
# drivers/web/app.py
from typing import TYPE_CHECKING
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from saw.engines.query.engine import QueryEngine
    from saw.engines.collaborate.orchestrator import CollaborateEngine
    from saw.write_queue.queue import WriteQueue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: startup/shutdown."""
    # Startup: 启动 WebSocket 广播任务
    from .websocket import manager
    manager.set_event_bus(app.state.event_bus)
    await manager.start_broadcaster()
    yield
    # Shutdown: 清理资源
    await manager.stop_broadcaster()


def create_app(
    query: "QueryEngine",
    collaborate: "CollaborateEngine",
    write_queue: "WriteQueue",
    event_bus,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Create FastAPI application with injected dependencies.

    Args:
        query: Query engine for search/graph operations.
        collaborate: Collaboration engine for agent workflows.
        write_queue: Write queue for durable mutations.
        event_bus: Event bus for cross-engine communication.
        cors_origins: Allowed CORS origins (default: localhost:3000 for dev).

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="Smart Agent Wiki",
        version="1.1.0",
        description="Web API for knowledge management",
        lifespan=lifespan,
    )

    # Store engines in app.state for dependency injection
    app.state.query = query
    app.state.collaborate = collaborate
    app.state.write_queue = write_queue
    app.state.event_bus = event_bus

    # CORS 配置 (per D-03)
    origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from .routes import search, graph, pages, websocket
    app.include_router(search.router, prefix="/api", tags=["search"])
    app.include_router(graph.router, prefix="/api", tags=["graph"])
    app.include_router(pages.router, prefix="/api", tags=["pages"])
    app.include_router(websocket.router, tags=["websocket"])

    return app
```

### Pattern 2: Connection Manager for WebSocket

**What:** 管理多个 WebSocket 连接，支持按 session_id 定向广播。

**When to use:** 实时更新推送，agent 进度跟踪。

**Example:**
```python
# drivers/web/websocket.py
import asyncio
import json
from typing import TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

from fastapi import WebSocket

if TYPE_CHECKING:
    from saw.domain.events import ContradictionFound, ClaimsReady, IngestCompleted


@dataclass
class WSMessage:
    type: str
    payload: dict
    timestamp: str

    def json(self) -> str:
        return json.dumps({
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })


class ConnectionManager:
    """WebSocket connection manager per D-04, D-06."""

    def __init__(self):
        # session_id -> set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {}
        self._event_bus = None
        self._broadcast_task: asyncio.Task | None = None

    def set_event_bus(self, event_bus) -> None:
        """Set event bus for subscription."""
        self._event_bus = event_bus

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """Accept new connection and add to session group (per D-06)."""
        await websocket.accept()
        if session_id not in self._connections:
            self._connections[session_id] = set()
        self._connections[session_id].add(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """Remove connection from session group."""
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)

    async def broadcast(self, session_id: str, message: WSMessage) -> None:
        """Send message to all connections in session (per D-04)."""
        if session_id in self._connections:
            for ws in self._connections[session_id]:
                try:
                    await ws.send_text(message.json())
                except Exception:
                    # Connection closed, will be cleaned up
                    pass

    async def start_broadcaster(self) -> None:
        """Start event subscription task."""
        if self._event_bus is None:
            return
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    async def stop_broadcaster(self) -> None:
        """Stop event subscription task."""
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

    async def _broadcast_loop(self) -> None:
        """Subscribe to events and broadcast to sessions."""
        async for event in self._event_bus.subscribe():
            msg = self._event_to_message(event)
            # Broadcast to all sessions (or filter by event.session_id)
            for session_id in self._connections:
                await self.broadcast(session_id, msg)

    def _event_to_message(self, event) -> WSMessage:
        """Convert domain event to WebSocket message (per D-05)."""
        # Map event types to WebSocket event names
        event_type_map = {
            "AgentProgress": "agent_status",
            "WorkflowStep": "workflow_progress",
            "PageUpdated": "page_updated",
            "ContradictionFound": "page_updated",  # Trigger UI refresh
        }
        return WSMessage(
            type=event_type_map.get(type(event).__name__, "unknown"),
            payload=event.__dict__ if hasattr(event, "__dict__") else {},
            timestamp=datetime.utcnow().isoformat(),
        )


manager = ConnectionManager()
```

### Pattern 3: Search API Implementation

**What:** REST endpoint 复用 Query Engine，返回结构化响应。

**When to use:** GET /api/search (per D-07~09)。

**Example:**
```python
# drivers/web/routes/search.py
from fastapi import APIRouter, Depends, Request, Query
from pydantic import BaseModel, Field

router = APIRouter()


class SearchRequest(BaseModel):
    """Search query parameters (per D-07~09)."""
    q: str = Field(..., min_length=1, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Results per page")
    type: str | None = Field(None, description="Filter by page type")
    tag: str | None = Field(None, description="Filter by tag")
    min_confidence: int | None = Field(None, ge=1, le=4, description="Min confidence level")


class SearchResult(BaseModel):
    """Single search result (per D-08)."""
    slug: str
    title: str
    snippet: str
    confidence: int = Field(..., ge=1, le=4)
    freshness: int = Field(..., ge=0, le=8)
    citations: list[str]


class SearchResponse(BaseModel):
    """Paginated search results."""
    results: list[SearchResult]
    total: int
    page: int
    per_page: int


def get_query_engine(request: Request):
    """Dependency: get QueryEngine from app.state."""
    return request.app.state.query


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    type: str | None = None,
    tag: str | None = None,
    min_confidence: int | None = None,
    engine = Depends(get_query_engine),
) -> SearchResponse:
    """Search knowledge base using BM25 + FTS5 (per D-07)."""
    # Map API params to Query Engine params
    claims = engine.search(
        query=q,
        limit=per_page,
        offset=(page - 1) * per_page,
        filters={"type": type, "tag": tag} if type or tag else None,
    )

    # Convert to response format
    results = [
        SearchResult(
            slug=c.slug,
            title=c.title,
            snippet=c.content[:200] + "..." if len(c.content) > 200 else c.content,
            confidence=c.confidence.value,
            freshness=c.freshness.value,
            citations=[f"claim:{c.uuid}"],
        )
        for c in claims
    ]

    return SearchResponse(
        results=results,
        total=engine.count(query=q),  # Approximate total
        page=page,
        per_page=per_page,
    )
```

### Pattern 4: Graph API Implementation

**What:** REST endpoint 复用 Graph Store，支持 BFS/DFS 遍历参数。

**When to use:** GET /api/graph, /api/graph/{entity} (per D-10~12)。

**Example:**
```python
# drivers/web/routes/graph.py
from fastapi import APIRouter, Depends, Request, Path
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter()


class TraversalMode(str, Enum):
    bfs = "bfs"
    dfs = "dfs"


class GraphRequest(BaseModel):
    """Graph query parameters (per D-10~12)."""
    depth: int = Field(2, ge=1, le=5, description="Traversal depth")
    mode: TraversalMode = Field(TraversalMode.bfs, description="BFS or DFS")
    type: str | None = Field(None, description="Filter by entity type")


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    confidence: int


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str


class GraphResponse(BaseModel):
    """Graph data for Cytoscape.js."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]


def get_query_engine(request: Request):
    return request.app.state.query


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    depth: int = Query(2, ge=1, le=5),
    mode: TraversalMode = Query(TraversalMode.bfs),
    type: str | None = None,
    engine = Depends(get_query_engine),
) -> GraphResponse:
    """Get knowledge graph nodes and edges (per D-10)."""
    # Use GraphStore to get subgraph
    graph = engine.graph.traverse(
        start_nodes=None,  # All nodes
        depth=depth,
        mode=mode.value,
    )

    nodes = [
        GraphNode(id=n.id, label=n.label, type=n.type, confidence=n.confidence)
        for n in graph.nodes
    ]
    edges = [
        GraphEdge(id=e.id, source=e.source, target=e.target, type=e.type)
        for e in graph.edges
    ]

    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/graph/{entity}", response_model=GraphResponse)
async def get_entity_subgraph(
    entity: str = Path(..., description="Entity ID or slug"),
    depth: int = Query(2, ge=1, le=5),
    mode: TraversalMode = Query(TraversalMode.bfs),
    engine = Depends(get_query_engine),
) -> GraphResponse:
    """Get entity details and relationships (per D-11~12)."""
    graph = engine.graph.traverse(
        start_nodes=[entity],
        depth=depth,
        mode=mode.value,
    )

    # Same conversion as above
    ...
```

### Pattern 5: Page API Implementation

**What:** REST endpoint 处理 Wiki 页面 CRUD，写入通过 Write Queue。

**When to use:** GET/PUT/DELETE /api/pages/* (per D-13~16)。

**Example:**
```python
# drivers/web/routes/pages.py
from fastapi import APIRouter, Depends, Request, HTTPException, Path
from pydantic import BaseModel, Field

router = APIRouter()


class PageResponse(BaseModel):
    """Wiki page content (per D-14)."""
    slug: str
    title: str
    content: str
    frontmatter: dict
    confidence: int
    freshness: int


class PageUpdate(BaseModel):
    """Page update request (per D-15)."""
    content: str
    message: str | None = None  # Commit message


def get_query_engine(request: Request):
    return request.app.state.query

def get_write_queue(request: Request):
    return request.app.state.write_queue


@router.get("/pages")
async def list_pages(
    engine = Depends(get_query_engine),
) -> list[str]:
    """List all wiki page slugs (per D-13)."""
    return engine.wiki.list_pages()


@router.get("/pages/{slug}", response_model=PageResponse)
async def get_page(
    slug: str = Path(..., description="Page slug"),
    engine = Depends(get_query_engine),
) -> PageResponse:
    """Get page content (per D-14)."""
    page = engine.wiki.read(slug)
    if page is None:
        raise HTTPException(status_code=404, detail="Page not found")

    return PageResponse(
        slug=slug,
        title=page.frontmatter.get("title", slug),
        content=page.content,
        frontmatter=page.frontmatter,
        confidence=page.confidence.value,
        freshness=page.freshness.value,
    )


@router.put("/pages/{slug}")
async def update_page(
    slug: str = Path(...),
    update: PageUpdate = ...,
    write_queue = Depends(get_write_queue),
) -> dict:
    """Update page via Write Queue (per D-15)."""
    from saw.domain.wiki import WikiPage

    page = WikiPage(
        path=slug,
        content=update.content,
        frontmatter={},  # Preserve existing or update
    )

    write_queue.enqueue_atomic([
        {"sink": "wiki", "op": "write", "page": page},
        # Also trigger index update
        {"sink": "fts5", "op": "upsert", "slug": slug, "content": update.content},
    ])

    return {"status": "queued", "slug": slug}


@router.delete("/pages/{slug}")
async def delete_page(
    slug: str = Path(...),
    write_queue = Depends(get_write_queue),
) -> dict:
    """Delete page via Write Queue (per D-16)."""
    write_queue.enqueue_atomic([
        {"sink": "wiki", "op": "delete", "slug": slug},
        {"sink": "fts5", "op": "delete", "slug": slug},
    ])

    return {"status": "queued", "slug": slug}
```

### Anti-Patterns to Avoid

- **在路由中直接调用 LLM:** 违反架构分层，应通过 CollaborateEngine dispatch agent
- **WebSocket 存储业务状态:** WebSocket 仅做传输，状态应在 Engine 层
- **跳过 Write Queue 直接写入:** 破坏持久化保证，必须通过 Write Queue
- **返回裸异常:** 应使用 RFC 7807 Problem Details 格式

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket 广播 | 自定义连接列表 | ConnectionManager + Event Bus | 边缘情况：断线重连、心跳、广播原子性 |
| CORS 配置 | 手动设置 headers | FastAPI CORSMiddleware | 预检请求、credentials、多种 origin |
| 错误响应 | 自定义 JSON 格式 | RFC 7807 Problem Details | 标准化错误格式，客户端可解析 |
| 分页逻辑 | 偏移量计算 | FastAPI-Pagination 或 skip/limit 参数 | 边界检查、总数字段、游标分页 |

**Key insight:** FastAPI 已提供大部分基础设施，重点是正确注入 Engine 依赖和遵循架构分层。

## Common Pitfalls

### Pitfall 1: WebSocket 连接未清理导致内存泄漏

**What goes wrong:** 客户端断开连接时未从 ConnectionManager 移除，导致 `_connections` 无限增长。心跳检测失效时，服务器仍向已关闭的连接发送消息。

**Why it happens:**
- `WebSocketDisconnect` 异常在某些情况下不抛出
- 客户端网络中断时服务器无感知
- 未实现心跳机制

**How to avoid:**
1. 在 WebSocket 端点使用 `try/finally` 确保清理
2. 实现心跳：每 30 秒发送 ping，超时未响应则断开
3. 定期清理超时连接（per PITFALLS.md Pattern 16）

**Warning signs:**
- 服务器内存持续增长
- `WebSocket.send_text` 抛出异常但连接仍在管理器中

### Pitfall 2: 依赖注入在 WebSocket 端点中不可用

**What goes wrong:** WebSocket 端点使用 `Depends()` 时，依赖在连接建立时解析，但连接期间可能状态已改变。

**Why it happens:**
- WebSocket 是长连接，依赖生命周期与连接绑定
- 使用 `app.state` 而非函数参数更可靠

**How to avoid:**
1. WebSocket 端点直接从 `websocket.app.state` 获取依赖
2. 不要在 WebSocket 端点使用 `Depends()` 获取可变状态

**Warning signs:**
- WebSocket 端点抛出依赖解析异常
- 状态在不同连接间串扰

### Pitfall 3: CORS 预检请求失败

**What goes wrong:** 前端开发服务器（如 Vite）发送预检请求（OPTIONS），但服务器返回 405 或未正确处理 headers。

**Why it happens:**
- CORS Middleware 未正确配置 `allow_methods=["*"]`
- 缺少 `allow_headers=["*"]` 或特定 headers
- `allow_credentials=True` 与 `allow_origins=["*"]` 冲突

**How to avoid:**
1. 开发环境使用明确的 origins 列表
2. 生产环境通过环境变量配置
3. 测试预检请求：`curl -X OPTIONS -H "Origin: http://localhost:3000" http://localhost:8000/api/search`

**Warning signs:**
- 前端控制台显示 CORS 错误
- POST/PUT 请求失败但 GET 成功

### Pitfall 4: API 错误响应不一致

**What goes wrong:** 不同端点返回不同格式的错误响应，前端难以统一处理。

**Why it happens:**
- FastAPI 默认错误格式与自定义异常混合
- 未使用统一的异常处理器

**How to avoid:**
1. 使用 RFC 7807 Problem Details 格式
2. 全局异常处理器转换所有异常
3. Pydantic 验证错误使用默认 422 格式

```python
# middleware/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "type": "validation_error",
            "title": "Request validation failed",
            "status": 422,
            "detail": exc.errors(),
        },
    )
```

## Code Examples

### WebSocket Endpoint with Heartbeat

```python
# drivers/web/routes/websocket.py
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    from saw.drivers.web.websocket import manager

    await manager.connect(websocket, session_id)

    heartbeat_task = asyncio.create_task(heartbeat(websocket))

    try:
        while True:
            data = await websocket.receive_json()
            # Handle client messages (e.g., subscribe to specific topics)
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(websocket, session_id)


async def heartbeat(websocket: WebSocket, timeout: int = 30):
    """Send periodic pings, close if no response."""
    import time
    last_pong = time.monotonic()

    while True:
        await asyncio.sleep(timeout)
        try:
            await websocket.send_json({"type": "ping"})
            # In real implementation, track pong responses
        except Exception:
            break  # Connection closed
```

### RFC 7807 Error Handler

```python
# drivers/web/middleware/errors.py
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from saw.domain.exceptions import SawError


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent error responses."""

    @app.exception_handler(SawError)
    async def saw_error_handler(request: Request, exc: SawError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "type": "https://smart-agent.wiki/errors/business",
                "title": exc.__class__.__name__,
                "status": 400,
                "detail": str(exc),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "type": "https://smart-agent.wiki/errors/validation",
                "title": "Request validation failed",
                "status": 422,
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the full exception for debugging
        import logging
        logging.exception("Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "type": "https://smart-agent.wiki/errors/internal",
                "title": "Internal server error",
                "status": 500,
                "detail": "An unexpected error occurred",
            },
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flask + gevent | FastAPI + asyncio | 2018+ | 原生异步，WebSocket 一等公民 |
| 全局变量存储依赖 | app.state 依赖注入 | FastAPI 0.68+ | 测试友好，多租户支持 |
| 手动 CORS headers | CORSMiddleware | 内置 | 预检请求自动处理 |
| 自定义错误 JSON | RFC 7807 Problem Details | 行业标准 | 客户端可解析 |

**Deprecated/outdated:**
- `@app.on_event("startup")`: 使用 `lifespan` 上下文管理器替代
- 同步数据库调用: FastAPI 要求 async，使用 SQLAlchemy async session

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | FastAPI 0.136.1 API 稳定，无 breaking changes | Standard Stack | 低风险 — 版本已发布 |
| A2 | Pydantic v2 API 足够稳定用于响应模型 | Standard Stack | 低风险 — 已广泛采用 |
| A3 | WebSocket 心跳间隔 30 秒足够检测断连 | Code Examples | 中风险 — 可能需要根据网络环境调整 |
| A4 | Event Bus 已有 subscribe 方法 | Pattern 2 | **已验证：** subscribe() 不存在，需实现回调机制 |

## Open Questions (RESOLVED)

**Resolution Date:** 2026-04-28

1. **Event Bus 订阅机制细节** — RESOLVED
   - **Finding:** Event Bus 尚未实现 subscribe() 方法。当前 domain/events.py 仅定义了事件数据类（ContradictionFound, ClaimsReady, WriteFailed, IngestCompleted）。
   - **Decision:** WebSocket ConnectionManager 将使用轮询机制检查事件队列，或通过回调函数接收事件。Phase 03-02 实现时需在 lifespan 中初始化事件监听器。
   - **Action:** 在 ConnectionManager 中实现 `set_event_callback()` 方法，由各 Engine 在状态变更时调用。

2. **Write Queue 状态查询** — RESOLVED
   - **Finding:** SQLiteWriteQueue 已有 `get_sink_status(op_id) -> dict[str, str]` 方法，返回每个 sink 的完成状态。
   - **Decision:** API 层通过 `get_sink_status(op_id)` 查询写入状态。PUT/DELETE 端点返回 op_id，前端可通过轮询或 WebSocket 推送状态更新。
   - **Action:** Page API 返回的 PageStatus 已包含 op_id，前端可用此查询状态。


## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | Runtime | ✓ | 3.12 | — |
| FastAPI | Web framework | ✓ | 0.136.1 | — |
| Pydantic | Validation | ✓ | 2.12.5 | — |
| uvicorn | ASGI server | ✓ | 0.42.0 | — |
| httpx | Testing | ✓ | 0.28+ | — |
| pytest | Testing | ✓ | 8.0+ | — |
| pytest-asyncio | Async testing | ✓ | 0.24+ | — |

**Missing dependencies with no fallback:**
- None — all dependencies are available

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/drivers/web/ -x` |
| Full suite command | `pytest tests/ -v --cov=src/saw/drivers/web` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WEB-01 | Search API returns results | unit | `pytest tests/unit/drivers/web/test_search_api.py -x` | ❌ Wave 0 |
| WEB-01 | Search supports pagination | unit | `pytest tests/unit/drivers/web/test_search_api.py::test_search_pagination -x` | ❌ Wave 0 |
| WEB-01 | Search filters by type/tag | unit | `pytest tests/unit/drivers/web/test_search_api.py::test_search_filters -x` | ❌ Wave 0 |
| WEB-02 | Graph API returns nodes/edges | unit | `pytest tests/unit/drivers/web/test_graph_api.py -x` | ❌ Wave 0 |
| WEB-02 | Graph traversal BFS/DFS | unit | `pytest tests/unit/drivers/web/test_graph_api.py::test_graph_traversal -x` | ❌ Wave 0 |
| WEB-03 | Page API CRUD operations | unit | `pytest tests/unit/drivers/web/test_pages_api.py -x` | ❌ Wave 0 |
| WEB-03 | Page updates via Write Queue | unit | `pytest tests/unit/drivers/web/test_pages_api.py::test_page_write_queue -x` | ❌ Wave 0 |
| D-04 | WebSocket connects | integration | `pytest tests/integration/test_websocket.py -x` | ❌ Wave 0 |
| D-05 | WebSocket broadcasts events | integration | `pytest tests/integration/test_websocket.py::test_ws_broadcast -x` | ❌ Wave 0 |
| D-06 | WebSocket heartbeat | integration | `pytest tests/integration/test_websocket.py::test_ws_heartbeat -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/unit/drivers/web/ -x --tb=short`
- **Per wave merge:** `pytest tests/ -v --cov=src/saw/drivers/web --cov-report=term-missing`
- **Phase gate:** Full suite green, 80%+ coverage on new code

### Wave 0 Gaps
- [ ] `tests/unit/drivers/web/__init__.py` — package init
- [ ] `tests/unit/drivers/web/test_search_api.py` — Search API unit tests
- [ ] `tests/unit/drivers/web/test_graph_api.py` — Graph API unit tests
- [ ] `tests/unit/drivers/web/test_pages_api.py` — Page API unit tests
- [ ] `tests/unit/drivers/web/test_websocket.py` — WebSocket unit tests (mocked)
- [ ] `tests/integration/test_websocket.py` — WebSocket integration tests
- [ ] `tests/conftest.py` — shared fixtures (mock engines)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | 无用户认证，纯本地工具 |
| V3 Session Management | no | 无传统 session，WebSocket session_id 仅用于分组 |
| V4 Access Control | yes | Cedar Policy Engine (Phase 03-01 已实现) |
| V5 Input Validation | yes | Pydantic 模型验证所有输入 |
| V6 Cryptography | no | 无加密需求，Audit 已在 Phase 02 实现 |
| V7 Error Handling | yes | RFC 7807 统一错误格式 |
| V8 Data Protection | no | 无敏感数据暴露，已通过 Write Queue 保护 |
| V9 Logging | yes | 结构化日志，请求追踪 |

### Known Threat Patterns for FastAPI + WebSocket

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Input injection (path/query) | Tampering | Pydantic validation + 类型强制 |
| WebSocket message injection | Tampering | JSON schema validation，拒绝未知 type |
| CORS bypass | Spoofing | 明确配置 origins，禁用 `*` + credentials |
| Unbounded request body | Denial | FastAPI 默认限制 + Pydantic Field 约束 |
| WebSocket memory leak | Denial | ConnectionManager 清理 + 心跳超时 |
| Path traversal | Tampering | Path 参数验证，拒绝 `..` 和绝对路径 |

## Sources

### Primary (HIGH confidence)
- FastAPI WebSocket Documentation (https://fastapi.tiangolo.com/advanced/websockets/) — Connection Manager pattern, error handling
- FastAPI Testing Documentation (https://fastapi.tiangolo.com/tutorial/testing/) — TestClient patterns
- FastAPI WebSocket Testing (https://fastapi.tiangolo.com/advanced/testing-websockets/) — WebSocket testing with TestClient
- FastAPI Middleware Documentation (https://fastapi.tiangolo.com/tutorial/middleware/) — CORS configuration
- FastAPI Body Documentation (https://fastapi.tiangolo.com/tutorial/body/) — Pydantic model patterns
- PITFALLS.md (`.planning/research/PITFALLS.md`) — WebSocket state desync, CORS issues

### Secondary (MEDIUM confidence)
- ARCHITECTURE.md (`.planning/research/ARCHITECTURE.md`) — Phase 03 architecture patterns
- STACK.md (`.planning/research/STACK.md`) — FastAPI version verification

### Tertiary (LOW confidence)
- None — all claims verified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Version verified, API stable
- Architecture: HIGH — Based on existing hexagonal architecture
- Pitfalls: HIGH — Based on official FastAPI documentation

**Research date:** 2026-04-28
**Valid until:** 2026-07-28 (3 months — FastAPI stable)
