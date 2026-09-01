# Tech Stack Overview — Smart Agent Wiki 硬化项目

> 棕地，技术栈**已定→复用**为主。本表记录既有选型 + 硬化新增项，每项 ADR 留存理由。决策因子：需求匹配 40% + 团队能力 20% + 生态 15% + 运维 15% + 成本 10%。

## 全景表

| 层次 | 技术选择 | 版本 | 用途 | 来源 | ADR |
|---|---|---|---|---|---|
| 主语言/运行时 | Python | 3.11+ | 后端/engines/agents | 既有 | ADR-001 |
| CLI 框架 | Typer + Rich | — | `saw` CLI | 既有（`drivers/cli/main.py:10`） | ADR-001 |
| Web 框架 | FastAPI | — | REST/WebSocket | 既有（`drivers/web/app.py:165`） | ADR-001 |
| MCP | FastMCP | 3.2.4 | 61 工具 | 既有（`drivers/mcp/server.py:27`） | ADR-001 |
| 数据库 | SQLite | — | 四层存储（Vault/Claims/Wiki/Index） | 既有（`sqlite_connection.py`） | ADR-002 |
| 搜索引擎 | SQLite FTS5 | — | 关键词检索 + BM25 | 既有（`fts5_utils.py`） | ADR-002 |
| 缓存 | 进程内 + SQLite | — | query cache | 既有（`engines/query/cache.py`） | ADR-002 |
| 变更网关 | Write Queue (SQLite outbox) | — | 唯一 mutation 网关 | 既有（`write_queue/`） | ADR-002 |
| AI/LLM | LLMRouter（多 provider） | — | NL query / agent | 既有（`adapters/llm/router.py`） | — |
| 实时通信 | WebSocket (FastAPI) | — | 协作/集成 WS | 既有 | — |
| 任务调度 | asyncio + APScheduler [TBD] | — | contradiction worker / feed poll | 既有 async；cron [TBD] | — |
| 可观测性 | 自建 middleware（JSON log + trace_id + /metrics） | — | 日志/监控/健康 | 既有（`middleware/observability.py`） | ADR-003 |
| 认证 | JWT（双 token）+ bcrypt | — | auth | 既有（`auth/jwt_auth.py`） | ADR-004 |
| 授权 | RBAC + Cedar Policy | — | 权限矩阵 | 既有（`auth/permissions.py` + `cedar_policy.py`） | ADR-004 |
| 审计 | Ed25519 签名 receipt | — | 操作可审计 | 既有（`adapters/crypto/ed25519.py`） | ADR-004 |
| 限流 | 自建中间件（per-key+匿名） | — | API 防刷 | 既有（`api/rate_limit.py`） | ADR-004 |
| 前端 | React 19 + Vite + TS + Cytoscape + Milkdown | — | Web UI | 既有 | — |
| 桌面 | Tauri 2 | — | 桌面 app | 既有（Phase 21-22 done） | — |
| 测试 | pytest + ruff | — | 单测/lint/coverage | 既有（128 测试） | — |
| CI | GitHub Actions | — | ci.yml/release.yml | 既有 | — |

## 架构图（Mermaid）

```mermaid
graph TB
  subgraph Drivers
    CLI[Typer CLI]
    WEB[FastAPI Web]
    MCP[FastMCP]
  end
  subgraph Engines
    IN[Ingest] | Q[Query] | G[Govern] | L[Learn] | CO[Collaborate/Compile]
  end
  subgraph Gateway
    WQ[Write Queue outbox → sinks]
  end
  subgraph Adapters
    ST[SQLite+FTS5 repos]
    LLM[LLMRouter]
    CR[Ed25519/Cedar/bcrypt]
  end
  CLI --> Engines
  WEB --> Engines
  MCP --> Engines
  Engines --> WQ
  WQ --> ST
  Engines --> LLM
  WEB --> CR
```

## 选型门控
- [x] 每被触发维度有选择（棕地全复用，无新触发维度需选）
- [x] ADR ≥3（001 语言/框架、002 DB/搜索、003 可观测、004 安全）
- [x] 技术栈一致性（全栈既有，无冲突）
- [x] 与 NFR 匹配（性能/安全/可用性均由既有栈承载，硬化只补闭环）
