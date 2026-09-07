# PMS: dashboard — realtime 仪表盘 v4.3

> 产品说明书（PMS）living baseline。下游 02 拆解 / 03 技术方案不得越出本模块边界。

## 模块边界

### 做什么（IN-SCOPE）

前端仪表盘消费 v1.15.0 后端 REST 端点，展示 agent roster + activity + workflow 运行态列表，并实时更新。三组功能：

1. **Agent roster + activity 仪表盘** — 消费 `GET /api/v1/agents`（roster + activity_summary）+ `GET /api/v1/agents/{name}/activity`（详情），展示 roster 表 + 点击展开 activity 详情
2. **Workflow 运行态视图** — 消费 `GET /api/v1/workflows`（durable + live merge），展示最近执行列表 + 状态 + 步骤进度，running 行由 WS `workflow_progress` 实时更新
3. **实时更新** — 复用现有 WebSocket 基建（`useWebSocket` + `agent_status`/`workflow_progress`）+ REST 周期 polling 刷新，WS 断连时 polling 降级

### 不做什么（OUT-OF-SCOPE）

- 后端新增 REST 端点（v1.15.0 已就绪，本轮纯前端消费）
- 后端 activity 持久化（T1 finding，defer v2.0）
- per-request workspace 注入（N3/K2，defer v2.0）
- 桌面端独立仪表盘（desktop v0.1.0 独立 0.x 跟踪）
- agent activity DB 持久化层（T1）
- links apply undo/rollback（T2）
- 自定义角色分享/导入导出（T3）
- 前端框架选型 HOW（polling interval / SSE vs polling / 组件拆分 — 留 03 技术方案）

## 验收形态

| 验收点 | 来源 | AC |
|---|---|---|
| roster 表渲染 | PRD §3.1 | AC-D-1 |
| activity 详情展开 | PRD §3.1 | AC-D-2 |
| activity null 降级 | PRD §3.1 | AC-D-3 |
| activity 404 处理 | PRD §3.1 | AC-D-4 |
| workflow 列表渲染 | PRD §3.2 | AC-D-5 |
| workflow running 置顶 | PRD §3.2 | AC-D-6 |
| WS workflow_progress 实时更新 | PRD §3.2 | AC-D-7 |
| WS 断连降级 | PRD §3.3 | AC-D-8 |
| 后端不回归 | PRD §4 | AC-D-9 |

## 对外接口契约摘要

本模块为**纯前端消费方**，不对外暴露接口。消费的后端端点：

| 端点 | 方法 | 用途 | 来源 |
|---|---|---|---|
| `/api/v1/agents` | GET | roster + activity_summary | v1.15.0 F-T-1/F-T-3 |
| `/api/v1/agents/{name}/activity` | GET | 单 agent 活动详情 | v1.15.0 F-T-3 |
| `/api/v1/workflows` | GET | durable + live workflow 列表 | v1.11.0 M3 / v1.15.0 |
| `/ws`（WebSocket） | WS | agent_status / workflow_progress / page_updated 推送 | v1.4.0 D-04 |

## 关联 PRD

- PRD-dashboard-v1.16.0（status: Approved）

## 关联 Spec

- .csp/specs/SPEC-F-U-1.md（agent roster + activity 仪表盘，F-U-1，Approved）
- .csp/specs/SPEC-F-U-2.md（workflow 运行态视图，F-U-2，Approved）
- .csp/specs/SPEC-F-U-3.md（实时更新，F-U-3，Approved）

## 状态

- **ready**（边界已定，待 02 拆解 + 03 技术方案）

## 续留 findings（不在本模块范围，defer）

| finding | 来源 | 说明 |
|---|---|---|
| N3/K2 | v1.7.0 K2 | per-request workspace 注入，defer v2.0 |
| T1 | v1.15.0 | agent activity 不持久化，defer v2.0 |
| T2 | v1.15.0 | links apply 无 undo，defer |
| T3 | v1.15.0 | 自定义角色无分享机制，defer |
| S1-S4 | v1.14.0 | ANN 小规模 / scale_curve / COVERAGE-REPORT / engine.py god-file |
| O2 | v1.11.0 | coverage 余量薄 67.42% |
| O4 | v1.11.0 | tag 指向 reconcile 非 release |
| R3 | v1.13.0 | benchmark CI skip |
