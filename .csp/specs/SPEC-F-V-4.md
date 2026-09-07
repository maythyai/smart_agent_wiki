---
id: SPEC-F-V-4
title: 后端协同 + 端口收敛（vite proxy 8080 vs saw web 8000 错配统一 + CORS 扩展 + prod 模式连接）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-desktop-v1.17.0.md
pms_ref: .csp/product-spec/PMS-desktop.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-V-4
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
adr_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
ac_coverage: 3/3
related_tasks: [".csp/tasks/TASKS-DELTA-v1.17.0.md"]
---

# SPEC-F-V-4: 后端协同 + 端口收敛

## 实现 delta（ground 自源码）

> ADR-017 决策：
> - 决策二：端口收敛 vite proxy target 8080→8000（向 saw web 默认端口 D-02 约定收敛）
> - 决策三：CORS 扩展——默认 origins 添加 localhost:5173
> - 决策一：prod 模式 external saw web（用户手动 `saw web`），sidecar defer

### 改动点

| 文件 | 现状（ground） | 改为 | ADR 决策 |
|---|---|---|---|
| `web/vite.config.ts:18` | `target: 'http://localhost:8080'` | `target: 'http://localhost:8000'` | 决策二：proxy /api target 8080→8000 |
| `web/vite.config.ts:21` | `target: 'ws://localhost:8080'` | `target: 'ws://localhost:8000'` | 决策二：proxy /ws target 8080→8000 |
| `src/saw/drivers/cli/commands/web_cmd.py:33` | `"http://localhost:3000,http://127.0.0.1:3000"` | `"http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"` | 决策三：CORS 默认 origins 添加 localhost:5173 |
| `src/saw/drivers/web/app.py:229` | `origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000"]` | `origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]` | 决策三：CORS fallback default 添加 localhost:5173 |

### 不改动

- `src/saw/drivers/cli/commands/web_cmd.py:25` — `port: int = typer.Option(8000, ...)` 不变（D-02 约定，saw web 默认端口 8000）
- `src/saw/drivers/web/app.py:306` — `app.include_router(integrations_ws_router, prefix="/ws", ...)` 不变（WS 路径 /ws 与 vite proxy 一致）
- `web/vite.config.ts:14` — `server.port: 5173` 不变（vite dev server 端口，tauri.conf.json devUrl 指向）
- 不新增后端 REST 端点（复用 v1.15.0/v1.16.0 既有端点）

## 维度 1：UI/UX 规格

无 UI 变更。本 Feature 为配置收敛。

## 维度 2：数据库 Schema

无 schema 变更。

## 维度 3：API 契约

无新 API。dev/prod 模式连接路径：

### dev 模式（vite proxy）

| 路径 | proxy 配置 | 目标 |
|---|---|---|
| `/api/*` | `vite.config.ts:16-19` proxy `/api` → `http://localhost:8000`（收敛后） | saw web REST 端点 |
| `/ws` | `vite.config.ts:20-23` proxy `/ws` → `ws://localhost:8000`（收敛后），`ws: true` | saw web WS 路由（`/ws` prefix） |

### prod 模式（直连）

| 路径 | 前端配置 | 目标 |
|---|---|---|
| REST API | `VITE_API_BASE_URL` = `http://localhost:8000`（默认） | saw web REST 端点 |
| WebSocket | `VITE_WS_URL` = `ws://localhost:8000/ws`（默认） | saw web WS 路由 |

prod 模式无 vite proxy，前端通过环境变量 `VITE_API_BASE_URL`（既有，`api.ts:3`）+ `VITE_WS_URL`（既有，`useWebSocket.ts:24`）直连 saw web 后端。

## 维度 4：后端架构

### CORS 配置

**修改前**（ground）：
- `web_cmd.py:33`：`cors_origins: str = typer.Option("http://localhost:3000,http://127.0.0.1:3000", ...)`
- `app.py:229`：`origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000"]`

**修改后**：
- `web_cmd.py:33`：`cors_origins: str = typer.Option("http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173", ...)`
- `app.py:229`：`origins = cors_origins or ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]`

CORS 配置在 `create_app` 函数中通过 `CORSMiddleware` 注入（`app.py:230-235`）：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### WS 路由（不变）

WS 路由挂载在 `/ws` prefix（`app.py:306`）：
```python
app.include_router(integrations_ws_router, prefix="/ws", tags=["websocket"])
```

vite proxy `/ws` 代理到后端 `/ws` prefix——路径一致，仅端口需收敛。

### prod 模式后端协同

prod 模式下 desktop 加载 `web/dist` 静态产物，无 vite dev server 代理。前端直连 saw web 后端：
- 用户须先运行 `saw web`（默认 localhost:8000）
- 前端通过 `VITE_API_BASE_URL` + `VITE_WS_URL` 环境变量配置后端地址
- saw web 未启动 → 前端 API 请求失败，仪表盘显示空态/错误条（v1.16.0 降级逻辑，ADR-016）
- WS 连接失败 → 仪表盘降级为 polling 模式（v1.16.0 降级逻辑，ADR-016）

## 维度 5：前端架构

### vite proxy 配置（修改后）

```typescript
// web/vite.config.ts（修改后）
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 收敛后（原 8080）
      changeOrigin: true,
    },
    '/ws': {
      target: 'ws://localhost:8000',  // 收敛后（原 8080）
      ws: true,
    },
  },
},
```

### 环境变量

| 变量 | dev 值 | prod 值 | 来源 |
|---|---|---|---|
| `VITE_API_BASE_URL` | 不设（走 vite proxy 相对路径 /api） | `http://localhost:8000` | `api.ts:3`（既有） |
| `VITE_WS_URL` | 不设（走 vite proxy 相对路径 /ws） | `ws://localhost:8000/ws` | `useWebSocket.ts:24`（既有） |

## 维度 6：基础设施需求

### 服务依赖

| 服务 | 用途 | dev 模式 | prod 模式 |
|---|---|---|---|
| saw web | REST API + WS 后端 | vite proxy → localhost:8000 | 前端直连 localhost:8000 |
| vite dev server | dev 热更新 + proxy | localhost:5173 | 不需要（prod 加载 web/dist） |

### 环境变量清单

无新环境变量。`VITE_API_BASE_URL` + `VITE_WS_URL` 既有。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-C-1 | `test_port_convergence.py`（新建）：parse vite.config.ts → 断言 proxy /api target=localhost:8000 + proxy /ws target=ws://localhost:8000 | unit（pytest + 正则/文本匹配） | vite proxy /api target 包含 "8000"（非 "8080"）；vite proxy /ws target 包含 "8000"（非 "8080"） |
| AC-C-2 | `test_prod_backend_connection.py`（新建）：验证 prod 模式环境变量默认值 + 前端连接配置正确性（VITE_API_BASE_URL / VITE_WS_URL 既有逻辑不变） | unit（pytest + 文件检查） | api.ts VITE_API_BASE_URL 逻辑正确；useWebSocket.ts VITE_WS_URL 逻辑正确 |
| AC-C-3 | `test_cors_expansion.py`（新建）：parse web_cmd.py → 断言 cors_origins 默认值含 localhost:5173 + parse app.py → 断言 fallback default 含 localhost:5173 | unit（pytest + 正则/文本匹配） | web_cmd.py cors_origins 默认值含 "localhost:5173"；app.py fallback origins 含 "localhost:5173" |

### CI 兼容

全部用 Python pytest 运行（文本匹配 + 文件检查），不依赖 Rust/Tauri/vite 工具链。CI 始终跑。

## 维度 8：安全考量

- CORS 扩展仅添加 `localhost:5173`（dev 模式 vite dev server 端口），不放宽到 `0.0.0.0` 或 `*`（PRD §3.4 规则 5 安全要求）。
- prod 模式后端地址用户配置（`VITE_API_BASE_URL`），不硬编码非 localhost 地址。
- WS 连接使用 `ws://` 协议（localhost），prod 部署到远程服务器应升级 `wss://`（defer）。
- saw web 后端 `auth_mode` 机制（`app.py:242-255`）：local 模式信任本地请求，team 模式要求 JWT——prod 部署到非 loopback 端口自动拒绝 local 模式（`app.py:298-304`）。

## 降级策略（复用 v1.16.0，ADR-016）

| 场景 | 降级行为 | 来源 |
|---|---|---|
| saw web 未启动 | 前端 API 请求失败，仪表盘显示空态/错误条 | PRD §3.4 异常处理 |
| CORS 未配 | 浏览器控制台 CORS 错误，API 请求被拒 | PRD §3.4 异常处理 |
| WS 连接失败 | 仪表盘降级为 polling 模式（react-query refetchInterval 15s 继续） | ADR-016（v1.16.0） |
| WS 重连成功 | `useWebSocket.ts:123` 自动 `invalidateQueries` 拉最新 | ADR-016（v1.16.0） |

## 实现就绪度

- [x] 端口收敛改动点明确（vite.config.ts 2 行 8080→8000）
- [x] CORS 扩展改动点明确（web_cmd.py 1 行 + app.py 1 行 添加 localhost:5173）
- [x] prod 模式连接明确（external saw web，VITE_API_BASE_URL/VITE_WS_URL 配置）
- [x] WS 路径无需修改（/ws prefix 一致）
- [x] 降级策略复用 v1.16.0 既有逻辑
- [x] AC 覆盖 3/3
- [ ] 05 实施后端口收敛 + CORS 扩展 + 连接验证通过
