---
id: SPEC-F-U-2
title: Workflow 运行态视图（新组件拉 GET /api/v1/workflows durable+live + /workflows/{id}/status 步骤进度）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-dashboard-v1.16.0.md
pms_ref: .csp/product-spec/PMS-dashboard.md
cms_ref: "[无 — 前端无 CMS，ground 自源码]"
feature_id: F-U-2
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md
adr_ref: .csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md
ac_coverage: 3/3
related_tasks: "[.csp/tasks/TASKS-DELTA-v1.16.0.md#T-F-U-2]"
---

# SPEC-F-U-2: Workflow 运行态视图

## 实现 delta（ground 自源码）

> ADR-016 决策：react-query `useQuery` + `refetchInterval: 15000`（15s polling）。
> 不新增后端端点（v1.15.0 `GET /api/v1/workflows` + `GET /api/v1/workflows/{id}/status` 已就绪）。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `web/src/pages/Dashboard.tsx` L29 | `const activeWorkflow = useStore((s) => s.activeWorkflow)` — WS 单条活跃流，无历史列表 | 新增 `WorkflowList` 组件区域，`useWorkflows()` hook（react-query 拉 `GET /api/v1/workflows`），渲染最近 workflow 列表 |
| `web/src/components/dashboard/`（新建） | 无 workflow 组件 | 新建 `WorkflowList.tsx`（workflow 列表表格）+ `WorkflowRow.tsx`（单行 + 步骤进度 + live 标记） |
| `web/src/types/api.ts` L153-159 | `WorkflowProgress`（WS 推送用：workflow_id/step/total_steps/current_step/status） | 新增 `WorkflowExecution`（REST 返回类型：workflow_id/status/definition_name/steps_completed/steps_total/updated_at/finished_at/live?）+ `WorkflowListResponse`（workflows[]/total）类型 |
| `web/src/hooks/`（新建） | 无 workflow hooks | 新建 `useWorkflows.ts`（`useQuery` 拉 `GET /api/v1/workflows`，`refetchInterval: 15000`）+ `useWorkflowStatus.ts`（`useQuery` 拉 `GET /api/v1/workflows/{id}/status`，enabled by click） |

### 不改动

- `web/src/hooks/useWebSocket.ts` — WS 连接管理不变。`useWebSocket.ts:93-96` 已在 `workflow_progress` 消息到达时调 `queryClient.invalidateQueries({ queryKey: ['agents'] })`，F-U-2 扩展为同时 `invalidateQueries({ queryKey: ['workflows'] })`（F-U-3 协调，本 Spec 标注改动点）。
- `web/src/stores/dashboardStore.ts` — `activeWorkflow` 不变（WS 推送仍更新单条活跃流 banner），REST 列表数据走 react-query 缓存。
- 后端 `src/saw/api/routes/collaborate.py` — `list_workflows()`（L327）+ `workflow_status()`（L495）不改（v1.15.0 已实现 durable + live merge）。

## 维度 1：UI/UX 规格

### 组件树

```
Dashboard
├── ConnectionStatus（复用）
├── AgentRosterSection（F-U-1 区域，独立）
├── WorkflowRuntimeSection（新增区域）
│   └── WorkflowList（新建）
│       ├── WorkflowRow（新建，单行）
│       │   ├── status badge（running=蓝/completed=绿/failed=红/pending=灰 + 文字标签）
│       │   ├── steps progress（current_step/total_steps + progress bar）
│       │   ├── live 标记（live in-memory workflow 标 "live"）
│       │   └── 点击展开 → steps 详情（GET /workflows/{id}/status）
│       └── 空态："No workflows executed yet"
└── 既有统计卡片 + Quick Actions + Run Workflow + activeWorkflow banner（不变）
```

### 交互规格

| 交互 | 触发 | 行为 | 反馈 |
|---|---|---|---|
| workflow 列表自动拉取 | 进入 /dashboard | `useWorkflows()` 发 `GET /api/v1/workflows?limit=20` | 列表渲染 |
| running 行置顶 | 列表渲染 | running 行排在 completed/failed 行之前 | running 行在第一组 |
| live 标记 | workflow 来自 in-memory（未落 DB） | 行标记 "live" badge | 视觉区分 durable vs live |
| WS workflow_progress 更新行 | WS 推送 workflow_progress | `dashboardStore.activeWorkflow` 更新 + `invalidateQueries(['workflows'])` 触发 REST 重新拉取 | 对应 running 行 current_step/step/status 实时更新 |
| 点击 workflow 行 | 点击 WorkflowRow | `useWorkflowStatus(id)` 发 `GET /api/v1/workflows/{id}/status` | 展开步骤详情 |
| WS 不匹配 | WS workflow_progress 的 workflow_id 不在列表 | 忽略 | 无（可能已过期或来自其他会话） |
| 列表为空 | `GET /api/v1/workflows` 返回空列表 | 显示空状态 | "No workflows executed yet" |
| 5xx 错误 | `GET /api/v1/workflows` 返回 5xx | 错误状态条 + Retry | "Failed to load workflows. Retry?" |

### 状态设计

| 状态 | 触发 | UI |
|---|---|---|
| Loading | 首次拉取 | 骨架屏 |
| Empty | workflows 为空 | "No workflows executed yet" |
| Error | 5xx | 错误状态条 + Retry |
| Success | workflows ≥1 | 列表渲染，running 置顶 |

### status 色标 + 文字标签（可访问性）

| status | 颜色 | 文字标签 |
|---|---|---|
| running | 蓝（`bg-blue-100 text-blue-700`） | "running" |
| completed | 绿（`bg-green-100 text-green-700`） | "completed" |
| failed | 红（`bg-red-100 text-red-700`） | "failed" |
| pending/queued | 灰（`bg-gray-100 text-gray-700`） | "pending" |

## 维度 2：数据库 Schema

无 schema 变更。后端 `workflow_executions` 表（v4 migration, `migrations.py:189`）已由 v1.15.0 使用，前端只消费 REST。

## 维度 3：API 契约

### `GET /api/v1/workflows`（既有端点，复用 v1.15.0）

**响应 200**：
```json
{
  "workflows": [
    {
      "workflow_id": "abc-123-def",
      "definition_name": "knowledge_review",
      "name": "knowledge_review",
      "workflow": "knowledge_review",
      "status": "running",
      "steps_completed": 2,
      "steps_total": 4,
      "updated_at": "2026-09-07T10:30:00+00:00",
      "finished_at": null
    },
    {
      "workflow_id": "prev-456-ghi",
      "definition_name": "knowledge_review",
      "name": "knowledge_review",
      "workflow": "knowledge_review",
      "status": "completed",
      "steps_completed": 4,
      "steps_total": 4,
      "updated_at": "2026-09-07T09:00:00+00:00",
      "finished_at": "2026-09-07T09:05:00+00:00"
    }
  ],
  "total": 2
}
```

**live 标记**：来自 in-memory merge（尚未落 DB）的 workflow 也在列表中。后端 `list_workflows()`（`collaborate.py:327`）已实现 durable + live merge，前端根据 `finished_at === null && status === 'running'` 标记 "live"（区分 durable running vs live running 待确认——后端 live merge 的 workflow 无 `finished_at` 且可能不在 DB）。

### `GET /api/v1/workflows/{id}/status`（既有端点，复用 v1.15.0）

**响应 200**：
```json
{
  "workflow_id": "abc-123-def",
  "workflow": "knowledge_review",
  "status": "running",
  "current_step": 2,
  "steps_total": 4,
  "steps": [
    { "name": "search", "agent": "Librarian", "status": "completed" },
    { "name": "synthesize", "agent": "Scholar", "status": "completed" },
    { "name": "review", "agent": "Critic", "status": "running" },
    { "name": "publish", "agent": "Writer", "status": "pending" }
  ],
  "started_at": "2026-09-07T10:25:00+00:00"
}
```

**错误 404**：
```json
{
  "detail": "Workflow 'nonexistent' not found"
}
```

## 维度 4：后端架构

无后端改动。`list_workflows()`（`collaborate.py:327`）已实现 durable DB + live in-memory merge，读取 `workflow_executions` 表 + 合并 `_workflows` in-memory dict。`workflow_status()`（`collaborate.py:495`）返回 `_workflows` 中的 workflow dict。

## 维度 5：前端架构

### 状态管理

| 数据类型 | 管理方式 | 理由 |
|---|---|---|
| REST workflow 列表 | @tanstack/react-query `useQuery`（server state） | REST 数据是服务端状态 |
| WS workflow_progress（单条活跃流） | zustand `dashboardStore.activeWorkflow`（既有，不变） | WS 推送的活跃流仍由 store 管理，用于 banner |
| 展开的 workflow_id | `useState`（local component state） | 纯 UI 状态 |

### 关键 Hooks

```typescript
// useWorkflows.ts（新建）
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface WorkflowExecution {
  workflow_id: string;
  definition_name: string;
  name: string;
  workflow: string;
  status: 'running' | 'completed' | 'failed' | 'pending' | 'interrupted';
  steps_completed: number;
  steps_total: number;
  updated_at: string | null;
  finished_at: string | null;
}

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: () => api.get<{ workflows: WorkflowExecution[]; total: number }>(
      '/api/v1/workflows', { limit: 20 }
    ),
    refetchInterval: 15000, // ADR-016: 15s polling
  });
}
```

```typescript
// useWorkflowStatus.ts（新建）
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface WorkflowStep {
  name: string;
  agent: string;
  status: string;
}

export interface WorkflowStatusDetail {
  workflow_id: string;
  workflow: string;
  status: string;
  current_step: number;
  steps_total: number;
  steps: WorkflowStep[];
  started_at: string;
}

export function useWorkflowStatus(workflowId: string | null) {
  return useQuery({
    queryKey: ['workflow-status', workflowId],
    queryFn: () => api.get<WorkflowStatusDetail>(
      `/api/v1/workflows/${workflowId}/status`
    ),
    enabled: !!workflowId,
    refetchInterval: 15000,
  });
}
```

### 排序逻辑（running 置顶 + created_at 降序）

```typescript
const sortedWorkflows = [...workflows].sort((a, b) => {
  // running 置顶
  const aRunning = a.status === 'running' ? 0 : 1;
  const bRunning = b.status === 'running' ? 0 : 1;
  if (aRunning !== bRunning) return aRunning - bRunning;
  // 其余按 updated_at 降序
  return (b.updated_at || '').localeCompare(a.updated_at || '');
});
```

### WS workflow_progress 增量更新（PRD §3.2 规则 6）

WS `workflow_progress` 消息到达时（`useWebSocket.ts:93-96`）：
1. `dashboardStore.activeWorkflow` 更新（既有行为）
2. `queryClient.invalidateQueries({ queryKey: ['workflows'] })` 触发 REST 重新拉取（F-U-3 扩展 useWebSocket，本 Spec 标注改动点）

不替换整个列表——react-query `invalidateQueries` 后自动 refetch，返回的数据中对应 running 行的 `steps_completed`/`status` 已更新。WS 推送的 `current_step`/`step` 先于 REST refetch 到达，通过 `dashboardStore.activeWorkflow` 在 banner 中实时展示。

## 维度 6：基础设施需求

无新依赖。复用 `@tanstack/react-query` 5.100.6 + `tailwindcss` 4.2.4。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-D-5 | `test_workflow_list_render.test.tsx`：mock `GET /api/v1/workflows` 返回 ≥1 workflow → render Dashboard → 列表显示所有行，含 id/status/step/progress/created_at | unit（vitest + @testing-library/react） | 行数 == workflow 数；每行含 workflow_id + status badge + steps progress + updated_at |
| AC-D-6 | `test_workflow_running_top.test.tsx`：mock 返回 running + completed → render → running 行在 completed 行之前 | unit（vitest） | running 行的 DOM 位置在 completed 行之前 |
| AC-D-7 | `test_workflow_ws_update.test.tsx`：render 列表 → mock WS `workflow_progress` 消息 → `invalidateQueries` 被调 → 对应 running 行更新 | unit（vitest，mock useWebSocket + queryClient） | `invalidateQueries` 被调 with `['workflows']`；列表不整体替换（react-query refetch 后行数不变） |

### CI 兼容

全部用 `vi.mock` mock react-query + api.ts + useWebSocket + dashboardStore，不依赖真实后端。vitest + jsdom 运行。

## 维度 8：安全考量

- 纯前端消费既有 REST 端点，认证沿用 JWT + CORS。
- workflow_id 作为 URL path 参数，后端已有 `Path(...)` 校验（`collaborate.py:495`）。
- 无新攻击面。

## 暗色模式

新增 `WorkflowList`/`WorkflowRow` 组件支持 `dark:` 前缀。

## 可访问性

- status 色标同时有文字标签（不只是颜色）。
- WorkflowRow 可点击（`role="button"` + `tabIndex={0}`）。

## 实现就绪度

- [x] REST 返回类型定义明确（WorkflowExecution / WorkflowStatusDetail / WorkflowStep）
- [x] react-query hooks 伪代码完整（useWorkflows + useWorkflowStatus）
- [x] 组件树覆盖全状态（Loading/Empty/Error/Success）
- [x] 排序逻辑明确（running 置顶 + updated_at 降序）
- [x] WS 增量更新机制明确（invalidateQueries 不替换列表）
- [x] 异常处理覆盖（5xx 错误条 / 空状态 / WS 不匹配忽略）
- [x] AC 覆盖 3/3
- [ ] 05 实施后 vitest 验证
