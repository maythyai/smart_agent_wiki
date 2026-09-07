---
id: SPEC-F-U-1
title: Agent roster + activity 仪表盘（Dashboard.tsx 接 react-query 拉 GET /api/v1/agents + /agents/{name}/activity）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-dashboard-v1.16.0.md
pms_ref: .csp/product-spec/PMS-dashboard.md
cms_ref: "[无 — 前端无 CMS，ground 自源码]"
feature_id: F-U-1
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md
adr_ref: .csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md
ac_coverage: 4/4
related_tasks: "[.csp/tasks/TASKS-DELTA-v1.16.0.md#T-F-U-1]"
---

# SPEC-F-U-1: Agent roster + activity 仪表盘

## 实现 delta（ground 自源码）

> ADR-016 决策：react-query `useQuery` + `refetchInterval: 15000`（15s polling）。
> 不新增后端端点（v1.15.0 `GET /api/v1/agents` + `GET /api/v1/agents/{name}/activity` 已就绪）。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `web/src/pages/Dashboard.tsx` L28 | `const agents = useStore((s) => s.agents)` — WS 驱动，不消费 REST | 新增 `useAgents()` hook（react-query 拉 `GET /api/v1/agents`），roster 表渲染 REST 数据 + WS agent_status 作 live status 覆盖 |
| `web/src/pages/Dashboard.tsx` | 无 agent activity 详情展开 | 新增 agent 行点击 → `useAgentActivity(name)` hook 拉 `GET /api/v1/agents/{name}/activity`，展开/侧栏展示详情 |
| `web/src/components/dashboard/AgentList.tsx` | 从 `useStore` 读 WS agents，渲染 AgentCard grid | 扩展：接受 REST roster props + WS live status 覆盖，渲染 activity_summary 列（calls/failures/last_active_at），custom 标记 |
| `web/src/components/dashboard/AgentCard.tsx` | 显示 name/status/task/progress（WS 数据） | 扩展：显示 activity_summary.calls / failures / last_active_at + custom 标记；activity null 时显示 "—" |
| `web/src/types/api.ts` L146-151 | `AgentStatus` 仅有 agent/status/task?/progress?（WS 推送用） | 新增 `AgentRosterEntry`（REST 返回类型：name/model_tier/tools_allowed/rule/custom/activity_summary）+ `AgentActivity`（calls/failures/last_action/last_active_at）+ `ActivitySummary`（calls/last_active_at 或 null）类型 |
| `web/src/hooks/`（新建） | 无 agent hooks | 新建 `useAgents.ts`（`useQuery` 拉 `GET /api/v1/agents`，`refetchInterval: 15000`）+ `useAgentActivity.ts`（`useQuery` 拉 `GET /api/v1/agents/{name}/activity`，enabled by click） |

### 不改动

- `web/src/hooks/useWebSocket.ts` — WS 连接管理不变（F-U-3 复用），`useWebSocket.ts:88-89` 已在 WS 消息到达时调 `queryClient.invalidateQueries({ queryKey: ['agents'] })`，自动触发 `useAgents` 重新拉取。
- `web/src/stores/dashboardStore.ts` — zustand slice 不变（WS 推送仍更新 `agents`/`activeWorkflow`），REST 数据走 react-query 缓存不进 store。
- 后端 `src/saw/api/routes/collaborate.py` — `list_agents()`（L419）+ `get_agent_activity()`（L460）不改（v1.15.0 已实现）。

## 维度 1：UI/UX 规格

### 页面/视图清单

| 页面 | 路由 | 布局 | 权限 |
|---|---|---|---|
| Dashboard | `/dashboard` | 单页，agent roster 表 + activity 详情展开/侧栏 | 已认证（JWT） |

### 组件树

```
Dashboard
├── ConnectionStatus（复用，WS 连接状态 + Reconnect）
├── AgentRosterSection（新增区域）
│   ├── AgentList（扩展，REST roster + WS live status 覆盖）
│   │   └── AgentCard（扩展，activity_summary 列 + custom 标记）
│   └── AgentActivityDetail（新增，点击展开详情）
│       ├── calls / failures / last_action / last_active_at
│       └── 空态："no activity recorded" / "Agent not found"
├── WorkflowRuntimeSection（F-U-2 区域，独立）
└── 既有统计卡片 + Quick Actions + Run Workflow（不变）
```

### 交互规格

| 交互 | 触发 | 行为 | 反馈 |
|---|---|---|---|
| roster 自动拉取 | 进入 /dashboard | `useAgents()` 发 `GET /api/v1/agents` | 表格渲染 roster |
| 点击 agent 行 | 点击 AgentCard | `useAgentActivity(name)` 发 `GET /api/v1/agents/{name}/activity` | 展开/侧栏展示详情 |
| 关闭详情 | 点击关闭按钮/再次点击行 | 隐藏详情区 | 返回纯表格 |
| activity null | roster 渲染时 activity_summary=null | 计数列显示 "—" | 无（静默降级） |
| activity 404 | 点击不存在的 agent | 详情区显示 "Agent not found" | 无报错弹窗 |
| activity calls=0 | activity 返回 200 + calls=0 | 详情显示 "no activity recorded" | 无 |
| 5xx 错误 | `GET /api/v1/agents` 返回 5xx | 错误状态条 + Retry 按钮 | "Failed to load agent roster. Retry?" |
| WS agent_status 覆盖 | WS 推送 agent_status | `dashboardStore.agents` 更新 + `invalidateQueries(['agents'])` 触发 REST 重新拉取 | roster 表 live status 列实时更新 |

### 状态设计

| 状态 | 触发 | UI |
|---|---|---|
| Loading | 首次拉取（`useQuery` isLoading） | 骨架屏（spinner / skeleton rows） |
| Empty | roster 为空 + WS connected | "No agents registered"（沿用现有 AgentList 空态） |
| Error | `GET /api/v1/agents` 5xx | 错误状态条 + Retry 按钮 |
| Success | roster 返回 ≥1 agent | 表格渲染 |
| Partial | activity_summary=null | 计数列 "—"（静默降级） |

### 响应式断点

- `xl`（≥1024px）：AgentList 3 列 grid（沿用现有 `lg:grid-cols-3`）
- `md`（≥768px）：AgentList 2 列 grid
- `sm`（<768px）：AgentList 1 列

## 维度 2：数据库 Schema

无 schema 变更。纯前端消费 REST 端点，数据在后端（v1.15.0 `AgentActivityTracker` 内存态 + `workflow_executions` DB 表）。

## 维度 3：API 契约

### `GET /api/v1/agents`（既有端点，复用 v1.15.0）

**响应 200**：
```json
{
  "agents": [
    {
      "name": "Librarian",
      "model_tier": "sonnet",
      "tools_allowed": ["search", "read"],
      "rule": false,
      "custom": false,
      "activity_summary": {
        "calls": 5,
        "last_active_at": "2026-09-07T10:30:00+00:00"
      }
    },
    {
      "name": "MedicalExpert",
      "model_tier": "sonnet",
      "tools_allowed": ["search", "read"],
      "rule": false,
      "custom": true,
      "activity_summary": null
    }
  ],
  "total": 7
}
```

**错误**：
- 401 未认证 → api.ts 自动 refresh/redirect（既有行为）
- 5xx → react-query `onError`，前端显示错误状态条

### `GET /api/v1/agents/{name}/activity`（既有端点，复用 v1.15.0）

**响应 200**（有活动）：
```json
{
  "agent": "Librarian",
  "calls": 5,
  "failures": 1,
  "last_action": "search",
  "last_active_at": "2026-09-07T10:30:00+00:00"
}
```

**响应 200**（无活动）：
```json
{
  "agent": "Guardian",
  "calls": 0,
  "failures": 0,
  "last_action": null,
  "last_active_at": null
}
```

**错误 404**（agent 不在 roster）：
```json
{
  "detail": "Agent 'NonExistent' not found in roster"
}
```

## 维度 4：后端架构

无后端改动。`list_agents()`（`collaborate.py:419`）+ `get_agent_activity()`（`collaborate.py:460`）已由 v1.15.0 实现，返回结构含 `activity_summary` + `custom` 标记。

## 维度 5：前端架构

### 状态管理

| 数据类型 | 管理方式 | 理由 |
|---|---|---|
| REST roster + activity | @tanstack/react-query `useQuery`（server state） | REST 数据是服务端状态，react-query 管理 cache/refetch/loading/error |
| WS agent_status（live status 覆盖） | zustand `dashboardStore.agents`（既有，不变） | WS 推送的实时状态仍由 store 管理 |
| 展开的 agent name | `useState`（local component state） | 纯 UI 状态，不需全局 |

### API 层

复用 `web/src/lib/api.ts` 的 `api.get<T>(path)` 方法（已有 JWT header + 401 refresh + error handling）。

### 关键 Hooks

```typescript
// useAgents.ts（新建）
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface ActivitySummary {
  calls: number;
  last_active_at: string | null;
}

export interface AgentRosterEntry {
  name: string;
  model_tier: string;
  tools_allowed: string[];
  rule: boolean;
  custom: boolean;
  activity_summary: ActivitySummary | null;
}

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: () => api.get<{ agents: AgentRosterEntry[]; total: number }>('/api/v1/agents'),
    refetchInterval: 15000, // ADR-016: 15s polling
  });
}
```

```typescript
// useAgentActivity.ts（新建）
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface AgentActivity {
  agent: string;
  calls: number;
  failures: number;
  last_action: string | null;
  last_active_at: string | null;
}

export function useAgentActivity(agentName: string | null) {
  return useQuery({
    queryKey: ['agent-activity', agentName],
    queryFn: () => api.get<AgentActivity>(`/api/v1/agents/${agentName}/activity`),
    enabled: !!agentName, // 仅在点击展开时拉取
    refetchInterval: 15000, // ADR-016: 15s polling
  });
}
```

### 路由

无新路由。`/dashboard` 已存在（router.tsx 已挂载 Dashboard 页）。

### AgentList 排序逻辑（复用 + 扩展）

```typescript
// 沿用现有 status 优先级排序（running > error > completed > idle）
// 新增：REST roster 数据 + WS live status 合并
const sortedAgents = Object.values(rosterFromREST).sort((a, b) => {
  // WS live status 覆盖 REST status
  const wsStatusA = wsAgents[a.name]?.status || a.status || 'idle';
  const wsStatusB = wsAgents[b.name]?.status || b.status || 'idle';
  const priority = { running: 0, error: 1, completed: 2, idle: 3 };
  return (priority[wsStatusA] ?? 4) - (priority[wsStatusB] ?? 4);
});
```

## 维度 6：基础设施需求

无新依赖。复用 `@tanstack/react-query` 5.100.6（已安装，`web/package.json:14`）+ `zustand` 5.0.12（已安装）+ `tailwindcss` 4.2.4（已安装）。

### 环境变量

无新环境变量。`VITE_API_BASE_URL` 既有（`api.ts:3`），`VITE_WS_URL` 既有（`useWebSocket.ts:24`）。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-D-1 | `test_agent_roster_render.test.tsx`：mock `GET /api/v1/agents` 返回 ≥1 agent → render Dashboard → roster 表显示所有 agent，含 name/status/custom 标记/activity_summary.calls | unit（vitest + @testing-library/react） | 表行数 == agent 数；每行含 name + status + custom 标记 + calls 值 |
| AC-D-2 | `test_agent_activity_detail.test.tsx`：mock roster + `GET /api/v1/agents/{name}/activity` 返回 calls=5/failures=1/last_action/last_active_at → 点击 agent 行 → 详情区展示完整 activity | unit（vitest） | 详情区显示 calls=5, failures=1, last_action, last_active_at |
| AC-D-3 | `test_agent_activity_null.test.tsx`：mock `GET /api/v1/agents` 返回 agent activity_summary=null → render roster → 该行计数列显示 "—"，不报错 | unit（vitest） | 计数列文本为 "—"；无 console.error |
| AC-D-4 | `test_agent_activity_404.test.tsx`：mock `GET /api/v1/agents/NonExistent/activity` 返回 404 → 点击 → 详情区显示 "Agent not found" | unit（vitest） | 详情区文本含 "Agent not found" |

### CI 兼容

全部用 `vi.mock` mock react-query + api.ts + dashboardStore，不依赖真实后端。vitest + jsdom 运行。CI 始终跑。

## 维度 8：安全考量

- 纯前端消费既有 REST 端点，认证沿用既有 JWT（`api.ts` 自动附 Authorization header）+ CORS（`app.py:229-230`）。
- agent name 作为 URL path 参数（`/agents/{name}/activity`），后端已有 `Path(...)` 校验（`collaborate.py:460`）。
- 无新攻击面。

## 暗色模式

新增组件支持 `dark:` 前缀（沿用现有 Tailwind dark mode 范式，如 `dark:bg-gray-800` `dark:text-white`）。

## 可访问性

- 状态色标同时有文字标签（如 `running` 文字 + 蓝色 badge，不只是颜色）。
- roster 表行可点击（`role="button"` + `tabIndex={0}` + `onKeyDown` Enter/Space）。

## 实现就绪度

- [x] REST 返回类型定义明确（AgentRosterEntry / AgentActivity / ActivitySummary）
- [x] react-query hooks 伪代码完整（useAgents + useAgentActivity）
- [x] 组件树覆盖全状态（Loading/Empty/Error/Partial/Success）
- [x] 排序逻辑复用现有 AgentList 范式
- [x] 异常处理覆盖（5xx 错误条 / activity null "—" / activity 404 "Agent not found" / calls=0 "no activity recorded"）
- [x] AC 覆盖 4/4
- [ ] 05 实施后 vitest 验证
