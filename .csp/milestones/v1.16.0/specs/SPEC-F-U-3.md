---
id: SPEC-F-U-3
title: 实时更新（复用 useWebSocket/dashboardStore + react-query invalidateQueries polling 15s 刷新）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-dashboard-v1.16.0.md
pms_ref: .csp/product-spec/PMS-dashboard.md
cms_ref: "[无 — 前端无 CMS，ground 自源码]"
feature_id: F-U-3
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md
adr_ref: .csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md
ac_coverage: 1/1
related_tasks: "[.csp/tasks/TASKS-DELTA-v1.16.0.md#T-F-U-3]"
---

# SPEC-F-U-3: 实时更新（polling + WS 双源）

## 实现 delta（ground 自源码）

> ADR-016 决策：react-query `refetchInterval: 15000` polling + 复用既有 `useWebSocket`（WS 消息 → `invalidateQueries`）。
> 依赖 F-U-1（`useAgents` hook）+ F-U-2（`useWorkflows` hook）已建好 react-query 查询。
> 本 Feature 是编排层：WS 连接管理 + polling 降级 + 重连恢复 + 降级横幅。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `web/src/hooks/useWebSocket.ts` L88-89 | `agent_status` case 只调 `invalidateQueries({ queryKey: ['agents'] })` | 扩展：同时调 `invalidateQueries({ queryKey: ['workflows'] })`（WS agent_status 可能伴随 workflow 变化） |
| `web/src/hooks/useWebSocket.ts` L93-96 | `workflow_progress` case 只调 `invalidateQueries({ queryKey: ['agents'] })` | 扩展：同时调 `invalidateQueries({ queryKey: ['workflows'] })`（PRD §3.2 规则 6：WS workflow_progress → 刷新 workflow 列表对应行） |
| `web/src/hooks/useWebSocket.ts` L123 | onopen 只调 `invalidateQueries({ queryKey: ['agents'] })` | 扩展：同时调 `invalidateQueries({ queryKey: ['workflows'] })`（PRD §3.3 规则 5：重连后立即 invalidate 拉最新） |
| `web/src/pages/Dashboard.tsx` | `useWebSocket({ autoConnect: true })` 已有；无 polling 降级逻辑 | 新增 polling 失败计数器（`useRef`）+ 降级横幅渲染 + 手动刷新按钮 |
| `web/src/components/dashboard/ConnectionStatus.tsx` | 显示 WS 连接状态 + Reconnect 按钮 | 扩展：WS 断连时显示 "Reconnecting..." + 降级横幅 "Live updates paused. Data may be stale." |

### 不改动

- `web/src/hooks/useWebSocket.ts` WS 连接逻辑（connect/disconnect/reconnect/heartbeat）——autoConnect + heartbeat + exponential backoff reconnect 不变。
- `web/src/stores/dashboardStore.ts`——zustand slice 不变。
- 后端——不新增 WS 消息类型、不新增 SSE 端点（ADR-016 排除 SSE）。

## 维度 1：UI/UX 规格

### 组件树（F-U-3 编排层）

```
Dashboard
├── ConnectionStatus（扩展）
│   ├── WS connected → 绿色 dot + "Connected"
│   ├── WS connecting → 黄色 dot + "Connecting..."（pulse）
│   ├── WS disconnected → 红色 dot + "Disconnected" + Reconnect 按钮
│   │   └── polling 正常 → "Reconnecting..." 状态条（PRD §3.3 异常处理 1）
│   └── 降级横幅（新增）
│       ├── WS 断连 + polling 正常 → "Reconnecting..."（顶部状态条）
│       ├── WS 断连 + polling 也失败 → "Live updates paused. Data may be stale."
│       └── polling 连续 3 次失败 → "Failed to refresh. Click to retry." + 手动刷新按钮
├── AgentRosterSection（F-U-1，useAgents refetchInterval: 15000）
├── WorkflowRuntimeSection（F-U-2，useWorkflows refetchInterval: 15000）
└── 既有内容（不变）
```

### 交互规格

| 交互 | 触发 | 行为 | 反馈 |
|---|---|---|---|
| 页面挂载 → WS + REST | Dashboard mount | `useWebSocket({ autoConnect: true })` 连接 WS；`useAgents`/`useWorkflows` 首次拉取 + `refetchInterval: 15000` 启动 | 首屏数据 + WS 连接 |
| WS agent_status 到达 | WS 推送 | `dashboardStore.updateAgent()` + `invalidateQueries(['agents'], ['workflows'])` | roster live status 实时更新 + REST refetch |
| WS workflow_progress 到达 | WS 推送 | `dashboardStore.updateWorkflow()` + `invalidateQueries(['agents'], ['workflows'])` | activeWorkflow banner 实时更新 + workflow 列表 refetch |
| WS 断连 + polling 正常 | WS onclose | `setStatus('disconnected')`；polling 继续（react-query refetchInterval 不依赖 WS） | 顶部 "Reconnecting..." 状态条；roster/workflow 仍 15s 周期刷新 |
| WS 重连成功 | WS onopen | `setStatus('connected')` + `invalidateQueries(['agents'], ['workflows'])` 立即拉最新 | 状态条恢复绿色；roster/workflow 立即刷新 |
| polling 失败（5xx） | react-query onError | 不阻塞页面；下次 interval 自动重试 | 无即时提示（react-query 默认 refetch on error） |
| polling 连续 3 次失败 | 计数器到 3 | 降级横幅 + 手动刷新按钮 | "Failed to refresh. Click to retry." |
| WS 断连 + polling 也失败 | WS disconnected + polling 3 次失败 | 完全降级横幅 | "Live updates paused. Data may be stale." |
| 手动刷新 | 点击 Retry 按钮 | `queryClient.invalidateQueries()` 全量刷新 + 重置失败计数器 | 立即拉取最新 |

### 状态设计

| 状态 | 触发 | UI |
|---|---|---|
| WS connected + polling ok | 正常运行 | 绿色 ConnectionStatus |
| WS connecting | 首次连接/重连中 | 黄色 "Connecting..." |
| WS disconnected + polling ok | WS 断连 | "Reconnecting..." 状态条 + roster/workflow 仍刷新 |
| WS disconnected + polling 3x fail | 双源都断 | "Live updates paused. Data may be stale." 降级横幅 |
| polling 3x fail + WS connected | polling 故障 | "Failed to refresh. Click to retry." 横幅 |

## 维度 2：数据库 Schema

无 schema 变更。

## 维度 3：API 契约

无新 API 契约。复用 F-U-1（`GET /api/v1/agents`）+ F-U-2（`GET /api/v1/workflows`）+ WS（`/ws/{sessionId}?token=...`）。

## 维度 4：后端架构

无后端改动。

## 维度 5：前端架构

### 状态管理

| 数据类型 | 管理方式 | 理由 |
|---|---|---|
| WS 连接状态 | `useWebSocket` hook `status` state + `dashboardStore.connectionStatus` | 既有逻辑不变 |
| polling 失败计数 | `useRef(0)`（Dashboard.tsx local ref） | 不需全局，Dashboard 组件内管理 |
| 降级横幅可见性 | `useState`（Dashboard.tsx local state） | 纯 UI 状态 |

### 关键逻辑

#### polling 失败计数器（Dashboard.tsx 新增）

```typescript
const pollingFailCount = useRef(0);
const [showPollingDegraded, setShowPollingDegraded] = useState(false);
const [showFullDegraded, setShowFullDegraded] = useState(false);

// react-query onError 回调（通过 useAgents/useWorkflows 的 onError 选项）
// F-U-1/F-U-2 hooks 需暴露 onError 回调，或在 Dashboard.tsx 用 useEffect 监听 isError
useEffect(() => {
  if (agentsQuery.isError) {
    pollingFailCount.current += 1;
    if (pollingFailCount.current >= 3) {
      setShowPollingDegraded(true);
      if (wsStatus === 'disconnected') {
        setShowFullDegraded(true);
      }
    }
  } else if (agentsQuery.isSuccess) {
    pollingFailCount.current = 0;
    setShowPollingDegraded(false);
    setShowFullDegraded(false);
  }
}, [agentsQuery.isError, agentsQuery.isSuccess, wsStatus]);
```

#### 手动刷新

```typescript
const handleManualRefresh = () => {
  queryClient.invalidateQueries(); // 全量刷新
  pollingFailCount.current = 0;
  setShowPollingDegraded(false);
  setShowFullDegraded(false);
};
```

#### useWebSocket 扩展（invalidateQueries for workflows）

```typescript
// useWebSocket.ts handleMessage — agent_status case 扩展
case 'agent_status': {
  const agentStatus = message.payload as unknown as AgentStatus;
  updateAgent(agentStatus);
  queryClient.invalidateQueries({ queryKey: ['agents'] });
  queryClient.invalidateQueries({ queryKey: ['workflows'] }); // 新增
  break;
}

// useWebSocket.ts handleMessage — workflow_progress case 扩展
case 'workflow_progress': {
  const workflowProgress = message.payload as unknown as WorkflowProgress;
  updateWorkflow(workflowProgress);
  queryClient.invalidateQueries({ queryKey: ['agents'] });
  queryClient.invalidateQueries({ queryKey: ['workflows'] }); // 新增
  break;
}

// useWebSocket.ts onopen 扩展
ws.onopen = () => {
  // ... 既有逻辑
  queryClient.invalidateQueries({ queryKey: ['agents'] });
  queryClient.invalidateQueries({ queryKey: ['workflows'] }); // 新增
  // ...
};
```

### 降级横幅渲染（Dashboard.tsx 新增）

```tsx
{/* WS 断连降级 */}
{wsStatus === 'disconnected' && !showFullDegraded && (
  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
    <p className="text-sm text-yellow-800 dark:text-yellow-300">Reconnecting...</p>
  </div>
)}

{/* polling 3x 失败降级 */}
{showPollingDegraded && !showFullDegraded && (
  <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4 mb-6 flex items-center justify-between">
    <p className="text-sm text-orange-800 dark:text-orange-300">Failed to refresh. Click to retry.</p>
    <button onClick={handleManualRefresh} className="px-3 py-1.5 bg-orange-600 text-white rounded-lg text-xs font-medium">Retry</button>
  </div>
)}

{/* 完全降级 */}
{showFullDegraded && (
  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
    <p className="text-sm text-red-800 dark:text-red-300">Live updates paused. Data may be stale.</p>
  </div>
)}
```

## 维度 6：基础设施需求

无新依赖。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-D-8 | `test_ws_disconnect_polling_degraded.test.tsx`：mock WS disconnected + mock `useAgents`/`useWorkflows` 正常返回 → render Dashboard → 顶部显示 "Reconnecting..." 状态条 + roster/workflow 表仍渲染（数据来自 polling） | unit（vitest + @testing-library/react，mock useWebSocket + react-query） | "Reconnecting..." 文本可见；roster 表行数 >0；workflow 列表行数 >0 |

### CI 兼容

全部用 `vi.mock` mock react-query（`useQuery` 返回预设 data/isError/isSuccess）+ useWebSocket（预设 wsStatus）+ dashboardStore，不依赖真实后端。vitest + jsdom 运行。

## 维度 8：安全考量

- WS 连接复用既有 `useWebSocket`（含 JWT token 附 `?token=` 参数，`useWebSocket.ts:109-110`）。
- polling REST 请求复用既有 `api.ts`（含 JWT Authorization header + 401 refresh）。
- 无新攻击面。

## 暗色模式

降级横幅组件支持 `dark:` 前缀。

## 可访问性

- 降级横幅有文字标签（不只是颜色变化）。
- Retry 按钮有 `aria-label`。

## 实现就绪度

- [x] polling 失败计数器伪代码完整（useRef + 3 次阈值）
- [x] 降级横幅渲染逻辑明确（3 种降级状态）
- [x] useWebSocket 扩展点明确（invalidateQueries for ['workflows']）
- [x] 手动刷新逻辑完整
- [x] AC 覆盖 1/1
- [ ] 05 实施后 vitest 验证
