# ADR-016: realtime 仪表盘更新策略（polling + WS 双源）

## 状态：Accepted

## 上下文

v1.16.0 realtime 仪表盘 v4.3 轮（PRD-dashboard-v1.16.0），前端仪表盘需消费 v1.15.0 后端 REST 端点展示 agent roster + activity + workflow 运行态，并实时更新。

PRD §3.3 描述 "SSE / polling" 两种候选，PMS-dashboard 明确"前端框架选型 HOW 留 03"。decomposition F-U-3 按 polling 方案拆解，但 03 可改 SSE，Feature 边界不变。

### 需求驱动

1. **agent activity 计数**（calls/failures/last_action/last_active_at）非 WebSocket 推送数据——WS `agent_status` 只推实时状态（idle/running/completed/error），不推活动计数。需要周期性刷新 `GET /api/v1/agents` + `GET /api/v1/agents/{name}/activity` 才能看到计数变化。
2. **workflow 列表**含 durable DB 历史 + live in-memory 运行态——WS `workflow_progress` 只推活跃流的单条进度，不推历史列表。需要周期性刷新 `GET /api/v1/workflows` 才能看到新创建/完成的 workflow。
3. **WS 断连降级**——WS 断连时 polling 继续工作，保证数据不完全停滞。

### CMS 出处（ground 自源码 + 前端栈）

| 事实 | file:line | 现状 |
|---|---|---|
| `@tanstack/react-query` 5.100.6 已在 dependencies | `web/package.json:14` | react-query 已安装，`useQueryClient` 已在 useWebSocket.ts 使用 |
| `useWebSocket` 已在 WS 消息到达时调 `queryClient.invalidateQueries({ queryKey: ['agents'] })` | `web/src/hooks/useWebSocket.ts:88-89`（agent_status case） | WS 消息已触发 react-query 失效，roster/workflow 查询自动重新拉取 |
| `useWebSocket` WS 重连后立即 `queryClient.invalidateQueries({ queryKey: ['agents'] })` | `web/src/hooks/useWebSocket.ts:123`（onopen） | 重连后自动拉最新，PRD §3.3 规则 5 已由既有代码满足 |
| `dashboardStore` 已有 `agents`/`activeWorkflow`/`lastUpdate` | `web/src/stores/dashboardStore.ts:14-16` | zustand slice 已就绪，WS 推送更新 store |
| Dashboard.tsx 当前 agent 数据来自 WS `agent_status` 非 REST | `web/src/pages/Dashboard.tsx:28` | `const agents = useStore((s) => s.agents)` — WS 驱动，不消费 REST |
| Dashboard.tsx 当前 workflow 仅展示 WS `workflow_progress` 单条活跃流 | `web/src/pages/Dashboard.tsx:29` | `const activeWorkflow = useStore((s) => s.activeWorkflow)` — 无历史列表 |
| Dashboard.tsx 已有 `setInterval(fetchStats, 30000)` polling 统计数据 | `web/src/pages/Dashboard.tsx:62` | 30s polling 范式已在 Dashboard.tsx 使用（统计数据），polling 是既有模式 |
| 后端无 SSE 端点（grep `StreamingResponse\|EventSourceResponse\|text/event-stream` 无命中） | `src/saw/` 全目录 | 后端无 SSE 基建，SSE 需新增端点 + StreamingResponse |
| 后端 WebSocket 路由已挂载 | `src/saw/drivers/web/app.py:298-301` | `ws_router` include_router，WS 基建已就绪 |
| `activity_tracker` lifespan 初始化 | `src/saw/drivers/web/app.py:68-75` | `AgentActivityTracker` + `subscribe(event_bus)` 在 lifespan 启动 |
| CORS allow_origins 含 localhost:3000 | `src/saw/drivers/web/app.py:229-230` | CORS 允许前端访问 REST |
| Vite dev proxy `/api` → 8080 + `/ws` → 8080 | `web/vite.config.ts:15-23` | 前端代理已配，REST + WS 均代理到后端 |
| `GET /api/v1/agents` 返回 roster + activity_summary | `src/saw/api/routes/collaborate.py:419` | `list_agents()` 已实现（v1.15.0），返回 name/model_tier/tools_allowed/rule/custom/activity_summary |
| `GET /api/v1/agents/{name}/activity` 返回活动详情 | `src/saw/api/routes/collaborate.py:460` | `get_agent_activity()` 已实现（v1.15.0），返回 calls/failures/last_action/last_active_at |
| `GET /api/v1/workflows` durable + live merge | `src/saw/api/routes/collaborate.py:327` | `list_workflows()` 已实现，durable DB + live in-memory merge |
| `GET /api/v1/workflows/{id}/status` 步骤进度 | `src/saw/api/routes/collaborate.py:495` | `workflow_status()` 已实现，返回 workflow dict |

## 决策

选择候选 ②：**react-query refetchInterval polling + 复用既有 WebSocket**。

- F-U-1/F-U-2 用 `@tanstack/react-query` `useQuery` 拉 REST 端点（`GET /api/v1/agents` + `GET /api/v1/workflows`），设置 `refetchInterval: 15000`（15s）。
- F-U-3 复用既有 `useWebSocket` hook（autoConnect + heartbeat + exponential backoff reconnect），WS 消息到达时 `queryClient.invalidateQueries` 已由既有代码实现（`useWebSocket.ts:88-89,123`）。
- polling interval 锁定 **15s**（PRD §3.3 规则 4 要求默认不低于 10s；15s 是 10s 下限以上的合理平衡值，兼顾新鲜度与后端负载）。
- WS 断连时 polling 继续（react-query refetchInterval 不依赖 WS 连接状态）；WS 重连后 `useWebSocket.ts:123` 已自动 `invalidateQueries` 拉最新。
- polling 连续 3 次失败（react-query `onError` + 计数器）→ 降级横幅 + 手动刷新按钮。

## 备选方案

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① SSE（Server-Sent Events，StreamingResponse 单向推送，复用 event_bus） | 服务端主动推送，延迟最低（<1s）；单向连接比 WS 轻量；复用 `InMemoryEventBus` 订阅机制 | **需新增后端端点**（`GET /api/v1/dashboard/stream` + `StreamingResponse`/`EventSourceResponse`），后端无 SSE 基建（grep 确认无 `StreamingResponse`/`text/event-stream`）；需处理连接管理/心跳/断线重连；前端需 `EventSource` API 或 `@microsoft/fetch-event-source` 库（新依赖）；与既有 WS 双连接重叠（WS 已推送 agent_status/workflow_progress） | 排除：需新后端端点 + 新前端依赖 + 与既有 WS 重叠 |
| ② react-query refetchInterval polling + 复用 WS（选） | **react-query 原生能力**（`refetchInterval`，零新依赖）；**无新后端端点**（复用 v1.15.0 既有 REST）；Dashboard.tsx 已有 30s polling 范式（`setInterval(fetchStats, 30000)`）；useWebSocket 已在 WS 消息到达时调 `invalidateQueries`（既有代码）；WS 断连时 polling 自动降级（react-query 独立于 WS）；实现最简（`refetchInterval` 一行配置） | polling 延迟 = interval（15s），非实时推送；每次 polling 全量拉取（非增量），后端承受周期性请求 | agent activity + workflow 列表实时性要求中等（非亚秒级），15s 可接受 ✓ |
| ③ 纯复用既有 WebSocket（不 polling） | 无新代码，WS 已连接 | WS 只推 `agent_status`/`workflow_progress`/`page_updated`，**不推 activity 计数**（calls/failures/last_action）和 **workflow 历史列表**；agent activity 变化不可见；新创建的 workflow 不可见（WS 只推活跃流进度）；PRD §3.3 规则 4 明确要求"对 REST 端点周期性 polling 刷新" | 排除：WS 数据覆盖不全，activity 计数 + workflow 历史不可见 |

## 理由

1. **PRD 对齐**：PRD §3.3 规则 4 明确"REST polling：对 `GET /api/v1/agents` + `GET /api/v1/workflows` 周期性刷新（interval [TBD]，默认不低于 10s），刷新通过 @tanstack/react-query invalidateQueries 实现"。候选 ② 是 PRD 指定的主路径。
2. **react-query 原生**：`refetchInterval` 是 `@tanstack/react-query` 内置能力（`web/package.json:14` 已安装 5.100.6），零新依赖。F-U-1/F-U-2 的 `useQuery` 只需加 `refetchInterval: 15000` 一行。
3. **无新后端端点**：复用 v1.15.0 既有 `GET /api/v1/agents`（`collaborate.py:419`）+ `GET /api/v1/workflows`（`collaborate.py:327`），PMS 明确"不新增后端端点"。SSE（候选 ①）需新增 `StreamingResponse` 端点，违反 PMS 约束。
4. **既有代码复用**：`useWebSocket.ts:88-89` 已在 WS `agent_status`/`workflow_progress` 消息到达时调 `queryClient.invalidateQueries({ queryKey: ['agents'] })`；`useWebSocket.ts:123` WS 重连后已自动 `invalidateQueries`。PRD §3.3 规则 2/3/5 已由既有代码满足。
5. **既有范式一致**：Dashboard.tsx:62 已有 `setInterval(fetchStats, 30000)` polling 统计数据的范式。react-query `refetchInterval` 是同一模式的声明式升级（替代手动 `setInterval`）。
6. **候选 ① 淘汰理由**：需新增后端 `StreamingResponse` 端点（PMS 约束禁止）+ 前端 `EventSource`/`@microsoft/fetch-event-source` 新依赖（PRD §4 兼容性要求"依赖 diff 为空"）+ 与既有 WS 双连接重叠。
7. **候选 ③ 淘汰理由**：WS 不推 activity 计数（calls/failures）和 workflow 历史列表，PRD §3.1/§3.2 核心需求不可见。
8. **interval 锁定 15s 理由**：PRD §3.3 规则 4 要求"默认不低于 10s 避免打满后端"；15s 在 10s 下限以上，兼顾数据新鲜度（OPS 看到的 activity 计数延迟 ≤15s）与后端负载（单客户端 4 次/min REST 请求，roster + workflow 两个端点）。

## 后果

### 正面
- F-U-1/F-U-2 用 react-query `useQuery` + `refetchInterval: 15000` 实现 REST 拉取 + 周期刷新，零新依赖。
- F-U-3 复用既有 `useWebSocket`（WS 消息 → `invalidateQueries` 已实现）+ polling 降级（WS 断连时 polling 继续）。
- agent activity 计数（calls/failures）每 15s 刷新可见，workflow 历史列表每 15s 刷新可见。
- WS 推送的实时状态（agent_status idle/running、workflow_progress 步骤进度）仍 <1s 到达（WS 推送 + `invalidateQueries` 触发 react-query 重新拉取）。
- polling 失败不阻塞页面（react-query `onError` + 降级横幅）。

### 负面
- polling 延迟 = 15s（非实时推送），agent activity 计数变化最多 15s 后才可见。可接受（PRD §3.3 规则 4 标 [TBD]，03 锁定 15s）。
- 每次 polling 全量拉取 roster（~10 agents）+ workflow 列表（limit=20），数据量小（agent 数量有限内置 6 + 自定义，workflow 默认 limit=20），后端负载可控。

### 风险
- WS + polling 双源数据冲突（PRD §8 风险 2）——WS 推送为实时增量（agent_status/workflow_progress），polling 为全量刷新；polling 刷新后 WS 增量覆盖最新值，时间戳优先。react-query `invalidateQueries` 后自动重新拉取 REST 全量，WS 推送的 store 状态随后覆盖，无冲突。
- polling 连续失败（后端 5xx）——react-query `onError` 回调 + 连续 3 次失败计数器 → 降级横幅 + 手动刷新按钮。下次 interval 自动重试（react-query 默认行为）。

## 关联 Feature

- F-U-1（agent roster + activity 仪表盘——`useQuery` 拉 `GET /api/v1/agents` + `GET /api/v1/agents/{name}/activity`，本 ADR 决策：`refetchInterval: 15000`）
- F-U-2（workflow 运行态视图——`useQuery` 拉 `GET /api/v1/workflows`，本 ADR 决策：`refetchInterval: 15000`）
- F-U-3（实时更新——复用 `useWebSocket` + react-query `invalidateQueries`/`refetchInterval` polling 降级，本 ADR 决策：polling + WS 双源策略）

## 关联 ADR

- ADR-001（Python 3.11 + Typer + FastAPI，Accepted）——后端 REST 端点复用既有框架。
- ADR-015（agent 角色注册表 + 活动聚合，Accepted）——`GET /api/v1/agents` + `GET /api/v1/agents/{name}/activity` 端点由 ADR-015 实现（v1.15.0），本轮纯前端消费。

## [TBD] 留尾

- polling interval 15s 为当前锁定值，后续可根据实际后端负载监控数据调整（若 OPS 反馈 15s 太慢可降至 10s，若后端负载高可升至 30s）。
- SSE 作为后续升级路径（若 OPS 需要亚秒级 activity 计数刷新），需新增后端 `StreamingResponse` 端点 + 前端 `EventSource`，本轮不做。
