# Interface Architecture — 接口架构（源自 CMS entry-points）

## 三入口（既有，不新增）
| 入口 | 框架 | 位置 | 数量 |
|---|---|---|---|
| CLI | Typer | `drivers/cli/main.py:10` | 37（含子命令+别名） |
| REST/WebSocket | FastAPI | `drivers/web/app.py:165` + `api/` | 117 路由 |
| MCP | FastMCP | `drivers/mcp/server.py:27` | 61 工具 |

## 接口风格
- REST：`/api/v1/*`（`api/` 多自带 prefix）；`drivers/web/routes/*` 在 `app.py` include 时挂 `/api`。
- WebSocket：`/ws/{session_id}`、`/ws/integrations`。
- MCP：stdio（`create_server` `server.py:81`）。

## 版本策略
`/api/v1/`；破坏性变更新版本，旧版维护 6 个月，废弃提前 3 个月标 `Deprecated`。既有路由多在 v1。

## 鉴权体系（JWT 中心）
- REST：Bearer token（`auth_dep`，`app.py:267` 挂 protected 路由）。
- WebSocket：握手 token。
- MCP：local 模式免鉴权；远程 [TBD]。
- 服务间：API Key [TBD]（多连接器集成）。

## 路由双轨（Drift D4，KEY-CHALLENGES 详述）
`api/`（自带 prefix）与 `drivers/web/routes/`（include 时挂 prefix）两套并存，prefix 体系不一。硬化不重构双轨（归后续），但 F-C-1 安全自检须覆盖两套。

## 错误格式
统一 `{error:{code,message,details:[{field,message}]}}`（`middleware/errors.py:90` `@app.exception_handler(SAWError)`）。HTTP 用 `HTTPException`+`status`。

## 限流
`api/rate_limit.py:24`：默认 100/h、1000/d，env `RATE_LIMIT_HOUR`/`RATE_LIMIT_DAY` 覆盖。超限 429 + Retry-After（F-C-3）。
