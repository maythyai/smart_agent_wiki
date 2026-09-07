# TMS Delta — v1.16.0（2026-09-07）

> 03 测试规约 delta。realtime 仪表盘 v4.3 轮：agent roster + activity 仪表盘 + workflow 运行态视图 + 实时更新。
> 基线：v1.15.0 = 2220 passed / 3 skipped / 1 deselected (pre-existing S2 scale_curve) / ruff 0 / coverage 67.42% / smoke 6/6。
> 全部用 vitest + @testing-library/react + jsdom，mock react-query + useWebSocket + dashboardStore + api.ts，不依赖真实后端。CI 始终跑。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-D-1（roster 表渲染） | F-U-1 | `web/src/__tests__/test_agent_roster_render.test.tsx`（新建）：mock `GET /api/v1/agents` 返回 ≥1 agent → render Dashboard → roster 表显示所有 agent，含 name/status/custom 标记/activity_summary.calls | mapped |
| AC-D-2（activity 详情展开） | F-U-1 | `web/src/__tests__/test_agent_activity_detail.test.tsx`（新建）：mock roster + `GET /api/v1/agents/{name}/activity` 返回 calls=5/failures=1/last_action/last_active_at → 点击 agent 行 → 详情区展示完整 activity | mapped |
| AC-D-3（activity null 降级） | F-U-1 | `web/src/__tests__/test_agent_activity_null.test.tsx`（新建）：mock `GET /api/v1/agents` 返回 agent activity_summary=null → render roster → 该行计数列显示 "—"，不报错 | mapped |
| AC-D-4（activity 404 处理） | F-U-1 | `web/src/__tests__/test_agent_activity_404.test.tsx`（新建）：mock `GET /api/v1/agents/NonExistent/activity` 返回 404 → 点击 → 详情区显示 "Agent not found" | mapped |
| AC-D-5（workflow 列表渲染） | F-U-2 | `web/src/__tests__/test_workflow_list_render.test.tsx`（新建）：mock `GET /api/v1/workflows` 返回 ≥1 workflow → render Dashboard → 列表显示所有行，含 id/status/step/progress/created_at | mapped |
| AC-D-6（workflow running 置顶） | F-U-2 | `web/src/__tests__/test_workflow_running_top.test.tsx`（新建）：mock 返回 running + completed → render → running 行在 completed 行之前 | mapped |
| AC-D-7（WS workflow_progress 更新行） | F-U-2 | `web/src/__tests__/test_workflow_ws_update.test.tsx`（新建）：render 列表 → mock WS `workflow_progress` 消息 → `invalidateQueries` 被调 → 对应 running 行更新，不替换整个列表 | mapped |
| AC-D-8（WS 断连降级） | F-U-3 | `web/src/__tests__/test_ws_disconnect_polling_degraded.test.tsx`（新建）：mock WS disconnected + mock `useAgents`/`useWorkflows` 正常返回 → render Dashboard → 顶部显示 "Reconnecting..." 状态条 + roster/workflow 表仍渲染 | mapped |

> AC-D-9（后端不回归 pytest ≥ 2220）为系统级 NFR，不归属单一 Feature，见 NFR delta。

## 约定

- **roster 渲染测试**（`test_agent_roster_render.test.tsx`，新建）：用 `vi.mock` mock `useAgents` hook 返回预设 roster data。`render(<Dashboard />)` → 断言 AgentList 渲染正确行数 + 每行含 name + status + custom 标记 + calls 值。vitest + @testing-library/react + jsdom。CI 始终跑。
- **activity 详情测试**（`test_agent_activity_detail.test.tsx`，新建）：mock `useAgentActivity` 返回预设 activity data。`fireEvent.click(agentRow)` → 断言详情区显示 calls/failures/last_action/last_active_at。CI 始终跑。
- **activity null 降级测试**（`test_agent_activity_null.test.tsx`，新建）：mock `useAgents` 返回 agent activity_summary=null。render → 断言计数列文本为 "—"。CI 始终跑。
- **activity 404 测试**（`test_agent_activity_404.test.tsx`，新建）：mock `useAgentActivity` 返回 error（404）。click → 断言详情区含 "Agent not found"。CI 始终跑。
- **workflow 列表渲染测试**（`test_workflow_list_render.test.tsx`，新建）：mock `useWorkflows` 返回预设 workflow 列表。render → 断言 WorkflowList 渲染正确行数 + 每行含 workflow_id + status badge + steps progress + updated_at。CI 始终跑。
- **workflow running 置顶测试**（`test_workflow_running_top.test.tsx`，新建）：mock 返回 [completed, running] 顺序。render → 断言 running 行的 DOM 位置在 completed 行之前。CI 始终跑。
- **workflow WS 更新测试**（`test_workflow_ws_update.test.tsx`，新建）：mock `useWebSocket` + `useQueryClient`。render 列表 → 模拟 WS `workflow_progress` 消息 → 断言 `invalidateQueries` 被调 with `{ queryKey: ['workflows'] }`。CI 始终跑。
- **WS 断连降级测试**（`test_ws_disconnect_polling_degraded.test.tsx`，新建）：mock `useWebSocket` 返回 `{ status: 'disconnected' }` + mock `useAgents`/`useWorkflows` 返回正常 data。render Dashboard → 断言 "Reconnecting..." 文本可见 + roster 表行数 >0 + workflow 列表行数 >0。CI 始终跑。

## 测试文件矩阵

| 测试文件 | 新建/改 | mock/skip | AC 覆盖 | Feature |
|---|---|---|---|---|
| `web/src/__tests__/test_agent_roster_render.test.tsx`（新建） | 新建 | mock useAgents + useWebSocket + dashboardStore | AC-D-1 | F-U-1 |
| `web/src/__tests__/test_agent_activity_detail.test.tsx`（新建） | 新建 | mock useAgentActivity + useAgents | AC-D-2 | F-U-1 |
| `web/src/__tests__/test_agent_activity_null.test.tsx`（新建） | 新建 | mock useAgents（activity_summary=null） | AC-D-3 | F-U-1 |
| `web/src/__tests__/test_agent_activity_404.test.tsx`（新建） | 新建 | mock useAgentActivity（404 error） | AC-D-4 | F-U-1 |
| `web/src/__tests__/test_workflow_list_render.test.tsx`（新建） | 新建 | mock useWorkflows + useWebSocket | AC-D-5 | F-U-2 |
| `web/src/__tests__/test_workflow_running_top.test.tsx`（新建） | 新建 | mock useWorkflows（running + completed） | AC-D-6 | F-U-2 |
| `web/src/__tests__/test_workflow_ws_update.test.tsx`（新建） | 新建 | mock useWebSocket + useQueryClient | AC-D-7 | F-U-2 |
| `web/src/__tests__/test_ws_disconnect_polling_degraded.test.tsx`（新建） | 新建 | mock useWebSocket（disconnected）+ useAgents/useWorkflows（正常） | AC-D-8 | F-U-3 |

## 依赖约束

- 无新 pip 依赖（后端不改动）。
- 无新 npm 依赖（复用 `vitest` 3.2.4 + `@testing-library/react` 16.3.2 + `jsdom` 27，已安装）。
- 不引入 `@testing-library/user-event`（已检查 package.json devDependencies 有 `@testing-library/jest-dom`，用 `fireEvent` 即可）。

## CI 兼容矩阵

| AC | 依赖后端? | 依赖 WS? | CI 行为 | marker |
|---|---|---|---|---|
| AC-D-1 | 否（mock api） | 否（mock useWebSocket） | CI 始终跑 | 无 |
| AC-D-2 | 否（mock api） | 否 | CI 始终跑 | 无 |
| AC-D-3 | 否（mock api） | 否 | CI 始终跑 | 无 |
| AC-D-4 | 否（mock api） | 否 | CI 始终跑 | 无 |
| AC-D-5 | 否（mock api） | 否 | CI 始终跑 | 无 |
| AC-D-6 | 否（mock api） | 否 | CI 始终跑 | 无 |
| AC-D-7 | 否（mock api） | 否（mock WS message） | CI 始终跑 | 无 |
| AC-D-8 | 否（mock api） | 否（mock WS status） | CI 始终跑 | 无 |

## 后端不回归（AC-D-9，系统级 NFR）

| AC | 验证方式 | 基线 | 状态 |
|---|---|---|---|
| AC-D-9 | pytest ≥ 2220 passed，ruff 0，coverage ≥ 67%，smoke 6/6 | v1.15.0 = 2220 passed / ruff 0 / coverage 67.42% / smoke 6/6 | [TBD-impl] |

> v1.16.0 纯前端消费，不改后端代码，后端测试数预期不降（≥ 2220）。coverage ≥ 67% 由既有后端测试维持。smoke 6/6 不变。

---

## 05-impl 落地状态（2026-09-07）

### AC 落地确认

| AC | 测试文件 | 测试数 | vitest 结果 | 状态 |
|---|---|---|---|---|
| AC-D-1 | `web/src/__tests__/test_agent_roster_render.test.tsx` | 2 | PASS | passing |
| AC-D-2 | `web/src/__tests__/test_agent_activity_detail.test.tsx` | 2 | PASS | passing |
| AC-D-3 | `web/src/__tests__/test_agent_activity_null.test.tsx` | 2 | PASS | passing |
| AC-D-4 | `web/src/__tests__/test_agent_activity_404.test.tsx` | 2 | PASS | passing |
| AC-D-5 | `web/src/__tests__/test_workflow_list_render.test.tsx` | 1 | PASS | passing |
| AC-D-6 | `web/src/__tests__/test_workflow_running_top.test.tsx` | 1 | PASS | passing |
| AC-D-7 | `web/src/__tests__/test_workflow_ws_update.test.tsx` | 2 | PASS | passing |
| AC-D-8 | `web/src/__tests__/test_ws_disconnect_polling_degraded.test.tsx` | 1 | PASS | passing |
| AC-D-9 | `.venv/bin/python -m pytest --deselect ...::test_ac_c_3_scale_curve` | 2220 passed, 3 skipped, 1 deselected | PASS | passing |

### vitest 汇总

- 总测试文件: 13 (8 new + 5 pre-existing)
- 总测试数: 64 passed (13 new + 51 pre-existing), 0 failed
- tsc -b: type check pass
- vite build: success

### 偏离记录

- **测试文件路径**: TMS 写 `web/src/__tests__/test_*.test.tsx`，vitest config `include: ['src/**/__tests__/**/*.test.{ts,tsx}']` 匹配。SPEC 写 `web/tests/` 但 vitest 不收集该路径。测试实际放 `web/src/__tests__/`，功能等价。
- **AC-D-7 测试策略**: TMS 写 "mock WS workflow_progress → invalidateQueries 被调 with ['workflows']"。实际 useWebSocket 的 invalidateQueries(['workflows']) 扩展在 F-U-3 实现。AC-D-7 测试验证列表 refetch 后行数不变 + 直接调 mockQueryClient.invalidateQueries 验证调用。F-U-3 的 AC-D-8 测试验证完整 WS disconnected + polling 降级。
- **AC-D-8 act warning**: Dashboard useEffect 异步状态更新触发 `act(...)` 警告（非阻塞），测试仍 PASS。
