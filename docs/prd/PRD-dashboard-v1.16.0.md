---
id: PRD-dashboard-v1.16.0
title: realtime 仪表盘 v4.3
version: 1.0
status: Approved
date: 2026-09-06
product_type: platform
feature_count: 3
mvp_scope: [agent-roster-dashboard, workflow-runtime-view, realtime-update]
thin_sections: []
upstream_source: .csp/artifacts/retrospective-v1.15.0.md + v1.15.0 后端就绪（GET /api/v1/agents + /agents/{name}/activity + /workflows durable+live merge）
roadmap_ref: docs/strategy/ROADMAP.md#v1.16.0
target_version: v1.16.0
related_pms: [.csp/product-spec/PMS-dashboard.md]
related_specs: [.csp/specs/SPEC-F-U-1.md, .csp/specs/SPEC-F-U-2.md, .csp/specs/SPEC-F-U-3.md]
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
---

# PRD: realtime 仪表盘 v4.3

> 内部 milestone v4.6。承接 v1.15.0 后端 activity 聚合 + workflow REST。本轮做前端实时可视化。

## 1. 背景与目标

### 1.1 背景：为什么现在做？不做会怎样？做了会怎样？

v1.15.0 后端已就绪三组 REST 端点：
- `GET /api/v1/agents` — 返回 agent roster（含自定义角色标记 `custom`）+ 每个角色的 `activity_summary`（calls / failures / last_action / last_active_at）
- `GET /api/v1/agents/{name}/activity` — 单个 agent 的活动聚合详情
- `GET /api/v1/workflows` — durable DB 历史 + live in-memory 运行态 merge（status: running/done/failed/completed，含步骤进度）

但前端 `web/src/pages/Dashboard.tsx` 当前的 agent 数据来自 **WebSocket 推送的 `agent_status` 消息**（`dashboardStore.agents`），**不消费**上述 REST 端点；workflow 仅展示 WebSocket 推送的 `workflow_progress` 单条活跃流，**无历史列表**；agent activity 计数/最近调用**完全不可见**。

不做：OPS/DEV 须用 CLI（`saw agents` / `saw workflow list`）或直接 curl REST 才能看 roster + activity + workflow 历史，前端仪表盘形同半成品。
做了：前端仪表盘成为 agent/workflow 运行态的实时单一视图，OPS 不必切 CLI。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| OPS 运维 | 部署 SAW 实例、监控 agent/workflow 运行态 | 一屏看全 agent roster + 活动计数 + workflow 执行状态 | 日常巡检、故障排查时定位哪个 agent 频繁失败 |
| DEV 开发 | 编写 workflow YAML、调试 agent 角色 | 看 workflow 执行进度 + 步骤状态 + agent 调用分布 | 开发调试 workflow 编排、验证自定义角色是否被调用 |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| 前端仪表盘消费 v1.15.0 REST 端点 | 3 个 REST 端点均被前端调用 | 3/3 | 代码审查 + E2E 测试断言 |
| 不回归后端 | pytest 通过数 | ≥ 2220（v1.15.0 基线） | CI |
| 前端测试通过 | web vitest 通过 | 0 fail | `cd web && npm test` |
| 实时更新生效 | agent activity + workflow 状态变化在仪表盘可见 | 刷新间隔 [TBD] | 手动验证 |

## 2. 需求概述

前端仪表盘消费 v1.15.0 后端 REST 端点，展示 agent roster + activity + workflow 运行态列表，并实时更新。

## 3. 详细功能设计

### 3.1 Agent roster + activity 仪表盘

- **描述**：仪表盘页展示 agent roster 表，每行含角色名、状态、活动计数（calls/failures）、最近调用时间。数据来自 `GET /api/v1/agents`（含 `activity_summary` 字段）。点击某 agent 可展开/跳转详情，调用 `GET /api/v1/agents/{name}/activity` 展示活动聚合详情（calls / failures / last_action / last_active_at）。
- **用户故事**：作为 OPS，我想在仪表盘看到所有 agent 的 roster + 活动计数，以便一屏判断哪个 agent 调用频繁、哪个频繁失败。
- **优先级**：P0
- **业务规则**：
  1. roster 数据源 = `GET /api/v1/agents`（非 WebSocket `agent_status`）；WebSocket 推送的实时状态仍保留用于 live status 覆盖
  2. 每行显示：agent name / status（idle/running/completed/error）/ custom 标记 / activity_summary.calls / activity_summary.failures / activity_summary.last_active_at
  3. `activity_summary` 为 null 时（tracker 未初始化）显示 "—"，不报错
  4. agent 不在 roster 时 activity 详情端点返回 404，前端显示 "agent not found"
  5. activity 详情端点返回 200 + calls=0 时，前端显示 "no activity recorded"
  6. roster 按 status 优先级排序：running > error > completed > idle（沿用现有 AgentList 排序逻辑）
- **交互流程**：进入仪表盘页 → 自动拉取 roster → 表格渲染 → 点击某行 → 拉取 activity 详情 → 展开/侧栏显示 → 关闭返回表格
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| `GET /api/v1/agents` 返回 5xx | 显示错误状态条 + 重试按钮 | "Failed to load agent roster. Retry?" |
| `GET /api/v1/agents/{name}/activity` 返回 404 | 详情区显示 not-found | "Agent not found" |
| activity_summary 为 null | 计数列显示 "—" | 无（静默降级） |

### 3.2 Workflow 运行态视图

- **描述**：仪表盘页展示最近 workflow 执行列表，每行含 workflow_id / status（running/done/failed/completed）/ 当前步骤 / 步骤进度 / 创建时间。数据来自 `GET /api/v1/workflows`（durable DB + live in-memory merge）。活跃 workflow 的实时步骤进度仍由 WebSocket `workflow_progress` 消息驱动。
- **用户故事**：作为 DEV，我想在仪表盘看到最近 workflow 执行列表 + 状态 + 步骤进度，以便调试 workflow 编排时快速定位失败步骤。
- **优先级**：P0
- **业务规则**：
  1. 列表数据源 = `GET /api/v1/workflows`（durable + live merge），默认 limit=20 最近执行
  2. 每行显示：workflow_id / status / workflow name（若返回） / current_step / total_steps / created_at / completed_at
  3. status 映射：running=蓝 / completed=绿 / failed=红 / pending/queued=灰
  4. running 状态行置顶，其余按 created_at 降序
  5. live in-memory merge 的 workflow（尚未落 DB）也展示，标记 "live" 以区分 durable
  6. WebSocket `workflow_progress` 消息到达时更新对应 running 行的 current_step/step/status（不替换整个列表，只更新匹配行）
- **交互流程**：进入仪表盘 → 拉取 workflow 列表 → 渲染表格 → running 行实时更新（WS 推送）→ 点击行展开步骤详情（若返回含 steps）
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| `GET /api/v1/workflows` 返回 5xx | 显示错误状态条 + 重试 | "Failed to load workflows. Retry?" |
| workflow 列表为空 | 显示空状态 | "No workflows executed yet" |
| WS workflow_progress 对应的 workflow_id 不在列表 | 忽略（可能已过期或来自其他会话） | 无 |

### 3.3 实时更新（SSE / polling）

- **描述**：agent activity + workflow 状态变化在仪表盘实时可见。复用现有 WebSocket 基建（`useWebSocket` hook + `agent_status`/`workflow_progress`/`page_updated` 消息类型），并补充对 REST 端点的周期性 polling 刷新（interval [TBD]），确保非 WebSocket 推送的数据（如 activity 计数）也定期更新。
- **用户故事**：作为 OPS，我想仪表盘的 agent activity 计数和 workflow 状态自动刷新，而不必手动 F5。
- **优先级**：P0
- **业务规则**：
  1. WebSocket 连接保持（沿用 `useWebSocket` autoConnect + heartbeat + exponential backoff reconnect）
  2. WS `agent_status` 消息 → 更新 dashboardStore.agents（现有行为，保留）
  3. WS `workflow_progress` 消息 → 更新 dashboardStore.activeWorkflow + 刷新 workflow 列表对应行（3.2 规则 6）
  4. REST polling：对 `GET /api/v1/agents` + `GET /api/v1/workflows` 周期性刷新（interval [TBD]，默认不低于 10s 避免打满后端），刷新通过 @tanstack/react-query invalidateQueries 实现
  5. WS 断连时 polling 继续工作（降级模式），重连后立即 invalidate 一次拉最新
  6. polling 失败（5xx）不阻塞页面，下次 interval 自动重试；连续 3 次失败显示降级提示
- **交互流程**：页面挂载 → WS 连接 + 首次 REST 拉取 → WS 推送实时更新 + polling 周期刷新 → 断连降级 → 重连恢复
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| WS 断连 + polling 正常 | 顶部显示 "Reconnecting..." 状态条（沿用 ConnectionStatus 组件） | WS 断连提示 |
| WS 断连 + polling 也失败 | 显示降级横幅 "Live updates paused. Data may be stale." | 降级提示 |
| polling 连续 3 次失败 | 显示错误横幅 + 手动刷新按钮 | "Failed to refresh. Click to retry." |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 前端测试 | web vitest 全 pass | `cd web && npm test` 0 fail |
| 后端不回归 | pytest ≥ 2220 passed，ruff 0，coverage ≥ 67%，smoke 6/6 | CI 全绿 |
| 实时延迟 | WS 推送 → UI 更新 < 1s；polling interval [TBD] | 手动验证 |
| 兼容性 | 复用现有前端栈（react-router / zustand / react-query / tailwind），不引入新框架 | 依赖 diff 为空 |
| 可访问性 | 状态色标同时有文字标签（不只是颜色） | 代码审查 |
| 暗色模式 | 新增组件支持 dark: 前缀（沿用现有 Tailwind dark mode 范式） | 代码审查 |

## 5. 数据需求

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| dashboard_roster_loaded | GET /api/v1/agents 成功 | agent_count, has_activity_summary | 监控 roster 加载成功率 |
| dashboard_agent_detail_opened | 点击 agent 行展开详情 | agent_name, calls, failures | 监控 activity 详情使用 |
| dashboard_workflow_list_loaded | GET /api/v1/workflows 成功 | workflow_count, running_count | 监控 workflow 列表加载 |
| dashboard_ws_status_changed | WS 状态变化 | from_status, to_status | 监控连接稳定性 |
| dashboard_polling_degraded | polling 连续 3 次失败 | endpoint, error_count | 监控降级频率 |

## 6. 验收标准

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-D-1 | roster 表渲染 | 后端 GET /api/v1/agents 返回 ≥1 agent | 打开仪表盘页 | roster 表显示所有 agent，含 name/status/custom 标记/activity_summary.calls |
| AC-D-2 | activity 详情 | roster 表已渲染 | 点击某 agent 行 | 调用 GET /api/v1/agents/{name}/activity，展示 calls/failures/last_action/last_active_at |
| AC-D-3 | activity 为 null | 某 agent activity_summary=null | roster 渲染 | 该行计数列显示 "—"，不报错 |
| AC-D-4 | activity 404 | 点击不存在的 agent | GET activity 返回 404 | 详情区显示 "Agent not found" |
| AC-D-5 | workflow 列表渲染 | 后端 GET /api/v1/workflows 返回 ≥1 workflow | 打开仪表盘页 | workflow 列表显示所有行，含 id/status/step/progress/created_at |
| AC-D-6 | workflow running 置顶 | 列表含 running + completed | 渲染 | running 行在 completed 行之前 |
| AC-D-7 | WS workflow_progress 更新 | 列表已渲染，WS 推送 workflow_progress | WS 消息到达 | 对应 running 行的 current_step/step/status 实时更新，不替换整个列表 |
| AC-D-8 | WS 断连降级 | WS 断连，polling 正常 | 断连发生 | 顶部显示 "Reconnecting..."，roster/workflow 仍周期刷新 |
| AC-D-9 | 后端不回归 | v1.16.0 代码合入 | pytest 运行 | ≥ 2220 passed，ruff 0，coverage ≥ 67% |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 02 需求拆解 | [TBD] | 本 PRD Approved | — |
| 03 技术方案 | [TBD] | 02 done | 前端框架锁定（03 决定 polling interval / SSE 选型） |
| 04 任务拆解 | [TBD] | 03 done | — |
| 05 实施 | [TBD] | 04 done | WS + polling 协调复杂度 |
| 06 发布 | [TBD] | 05 done | — |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 前端框架选型延后（03 锁定） | 中 | 中 | 本 PRD 只描述 WHAT，前端框架 HOW 留 03；ground 现有栈供 03 参考 |
| WS + polling 双源数据冲突（同一字段被两路更新） | 中 | 中 | WS 推送为实时增量，polling 为全量刷新；polling 刷新后 WS 增量覆盖最新值，时间戳优先 |
| activity_summary 为 null（tracker 未初始化场景） | 低 | 低 | 业务规则 3 已处理：显示 "—" |
| 后端 workflow live merge 语义复杂（durable + live 同 id 冲突） | 低 | 中 | 3.2 规则 5 标记 "live" 以区分；merge 逻辑后端已实现（v1.15.0），前端只消费 |
| N3/K2（per-request workspace）续留 | 低 | 低 | 不在本版本范围，defer v2.0 |
| S1-S4/T1-T4 续留 | 低 | 低 | 不在本版本范围，defer 后续 |

## 附录：ground 自源码 + 前端栈

| claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|
| 前端栈：React 19.2.5 + react-dom 19.2.5 | web/package.json:16-17 | dependencies react/react-dom | TRUE |
| 路由：react-router 7.14.2 | web/package.json:18 | dependencies react-router | TRUE |
| 状态库：zustand 5.0.12 | web/package.json:19 | dependencies zustand | TRUE |
| HTTP/server-state：@tanstack/react-query 5.100.6 | web/package.json:14 | dependencies @tanstack/react-query | TRUE |
| 样式：tailwindcss 4.2.4 + @tailwindcss/postcss | web/package.json:24,25 | devDependencies tailwindcss + @tailwindcss/postcss | TRUE |
| 构建：vite 8.0.10 + @vitejs/plugin-react 6.0.1 | web/package.json:27,28 | devDependencies vite + plugin-react | TRUE |
| 测试：vitest 3.2.4 + @testing-library/react 16.3.2 + jsdom 27 | web/package.json:29,31,32 | devDependencies vitest + testing-library + jsdom | TRUE |
| 编辑器：@milkdown/kit 7.20.0 + @milkdown/react 7.20.0 | web/package.json:12-13 | dependencies milkdown | TRUE |
| 图谱：cytoscape 3.33.2 + cytoscape-fcose 2.2.0 | web/package.json:15-16 | dependencies cytoscape | TRUE |
| 桌面：@tauri-apps/api 2.0.0 | web/package.json:15 | dependencies @tauri-apps/api | TRUE |
| 现有 Dashboard 页已存在 | web/src/pages/Dashboard.tsx:1 | 路由 /dashboard 已挂载（router.tsx） | TRUE |
| 现有 AgentCard/AgentList/ConnectionStatus 组件已存在 | web/src/components/dashboard/AgentCard.tsx:1 / AgentList.tsx:1 / ConnectionStatus.tsx:1 | 3 个 dashboard 组件 | TRUE |
| 现有 useWebSocket hook（heartbeat + reconnect + agent_status/workflow_progress/page_updated） | web/src/hooks/useWebSocket.ts:1 | WS 管理已就绪 | TRUE |
| 现有 dashboardStore（agents/activeWorkflow/lastUpdate） | web/src/stores/dashboardStore.ts:1 | zustand slice 已就绪 | TRUE |
| Dashboard 当前 agent 数据来自 WS `agent_status` 非 REST | web/src/pages/Dashboard.tsx:28 | `const agents = useStore((s) => s.agents)` — WS 驱动 | TRUE |
| Dashboard 当前 workflow 仅展示 WS `workflow_progress` 单条活跃流 | web/src/pages/Dashboard.tsx:29 | `const activeWorkflow = useStore((s) => s.activeWorkflow)` — 无历史列表 | TRUE |
| Dashboard 不消费 GET /api/v1/agents（REST） | web/src/pages/Dashboard.tsx:1-260 | grep 无 /api/v1/agents 调用 | TRUE |
| REST GET /api/v1/agents（roster + activity_summary） | src/saw/api/routes/collaborate.py:419 | @router.get("/agents") 已实现（v1.15.0） | TRUE |
| REST GET /api/v1/agents/{name}/activity | src/saw/api/routes/collaborate.py:460 | @router.get("/agents/{agent_name}/activity") 已实现（v1.15.0） | TRUE |
| REST GET /api/v1/workflows（durable + live merge） | src/saw/api/routes/collaborate.py:327 | @router.get("/workflows") 已实现，docstring "durable DB + live in-memory merge" | TRUE |
| REST POST /api/v1/workflows | src/saw/api/routes/collaborate.py:230 | @router.post("/workflows") 已实现 | TRUE |
| REST GET /api/v1/workflows/{id}/status | src/saw/api/routes/collaborate.py:495 | @router.get("/workflows/{workflow_id}/status") 已实现 | TRUE |
| 后端 CORS 配置 | src/saw/drivers/web/app.py:229-230 | CORSMiddleware allow_origins=["http://localhost:3000",...] | TRUE |
| 后端 WebSocket 路由挂载 | src/saw/drivers/web/app.py:298-301 | ws_router include_router | TRUE |
| 后端 activity_tracker lifespan 初始化 | src/saw/drivers/web/app.py:68-75 | AgentActivityTracker + subscribe(event_bus) | TRUE |
| Vite dev proxy /api → 8080 + /ws → 8080 | web/vite.config.ts:15-23 | server.proxy /api + /ws | TRUE |
| AgentStatus 类型（agent/status/task?/progress?） | web/src/types/api.ts:146-151 | 无 activity_summary 字段 | TRUE |
| WorkflowProgress 类型（workflow_id/step/total_steps/current_step/status） | web/src/types/api.ts:153-159 | WS 推送用，REST 返回结构不同 | TRUE |

### 下一步建议

- [ ] 进入需求拆解 → 把 3 功能模块翻成 Feature 清单 + 依赖图 + NFR，落 .csp/decomposition/
- [ ] 进入 03 技术方案 → 读 PRD + PMS + 前端栈 ground 表，决定 polling interval / SSE 选型 / 组件拆分
- [ ] 前端框架锁定在 03（本 PRD 只 ground 现有栈，不规定 HOW）
- [ ] 既有 PRD PRD-agent-link-v1.15.0 标 Released（已 Approved，本版本发布时 06 标 Released）

当前产物：docs/prd/PRD-dashboard-v1.16.0.md（status: Approved）+ .csp/product-spec/PMS-dashboard.md（ready）+ docs/prd/PRD-INDEX.md 已登记。已写 .csp/lifecycle-state.json：01 done，current_stage=02-decomposition。
