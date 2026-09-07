---
id: SPEC-F-V-2
title: web 仪表盘集成验证（frontendDist→web/dist 已 wired，验证 desktop 加载 v1.16.0 仪表盘构建产出）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-desktop-v1.17.0.md
pms_ref: .csp/product-spec/PMS-desktop.md
cms_ref: "[无 — desktop 栈无 CMS，ground 自源码]"
feature_id: F-V-2
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
adr_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
ac_coverage: 2/2
related_tasks: [".csp/tasks/TASKS-DELTA-v1.17.0.md"]
---

# SPEC-F-V-2: web 仪表盘集成验证

## 实现 delta（ground 自源码）

> ADR-017 决策：frontendDist=../../web/dist 已 wired（tauri.conf.json:11），beforeBuildCommand 构建链已配置（tauri.conf.json:9）。
> 本 Feature 为验证性 Feature——frontendDist 路径已 wired，本轮验证为主不改动配置。

### 改动点

无代码改动。本 Feature 为验证性 Feature，验证以下既有配置的正确性：

| 验证项 | 既有配置（ground） | 验证方式 |
|---|---|---|
| frontendDist 路径正确 | `tauri.conf.json:11` = `"../../web/dist"` | 相对于 `desktop/src-tauri/` 解析为项目根 `web/dist/`——验证 `web/dist/index.html` 存在 |
| beforeBuildCommand 构建链 | `tauri.conf.json:9` = `"npm run build --prefix ../web"` | `tauri build` 前自动执行 `tsc -b && vite build` → 产出 `web/dist/index.html` + `web/dist/assets/` |
| beforeDevCommand dev 链 | `tauri.conf.json:8` = `"npm run dev --prefix ../web"` | `tauri dev` 前自动启动 vite dev server（端口 5173） |
| web/dist 构建产出存在 | `web/dist/index.html`（v1.16.0 构建产出） | 文件存在性检查——`index.html` 引用 `assets/index-ZJ-gnL3B.js` + `assets/index-CSZ67bzM.css` |
| @tauri-apps/api 集成 | `web/package.json:11` = `"@tauri-apps/api": "^2.0.0"` | 前端可在 desktop 内调用原生 IPC 命令 |
| devUrl 指向 vite | `tauri.conf.json:10` = `"http://localhost:5173"` | dev 模式 desktop 窗口加载 localhost:5173 |

### 不改动

- `desktop/src-tauri/tauri.conf.json` — 所有配置项不变更（F-V-1 仅 bump version，本 Feature 验证 frontendDist/devUrl/beforeDevCommand/beforeBuildCommand）
- `web/dist/` — 消费 v1.16.0 既有构建产出，不改前端代码
- `web/package.json` — @tauri-apps/api ^2.0.0 既有依赖不变

## 维度 1：UI/UX 规格

### 页面/视图清单

| 页面 | 路由 | 布局 | 权限 |
|---|---|---|---|
| Dashboard | `/dashboard` | 单页，agent roster + activity + workflow 运行态仪表盘（v1.16.0 既有） | 已认证（JWT） |

### 验证状态

| 状态 | 触发 | desktop 窗口行为 |
|---|---|---|
| prod 模式 | `tauri build` → desktop 加载 `web/dist/index.html` | 仪表盘页渲染，agent roster + workflow 列表可见（需 saw web 后端运行） |
| dev 模式 | `tauri dev` → desktop 加载 `http://localhost:5173` | 仪表盘页渲染，前端热更新生效（需 vite dev server + saw web 后端运行） |
| web/dist 不存在 | `tauri build` 触发 `beforeBuildCommand` → npm run build → web/dist | beforeBuildCommand 先执行 web 构建，产出 web/dist 后 Tauri 打包嵌入 |
| web build 失败 | `tsc -b` 类型错误 | tauri build 中止，报错 "beforeBuildCommand failed" |
| frontendDist 路径不存在 | web/dist/index.html 缺失 | tauri build 报错 "frontendDist not found or empty" |
| saw web 未启动 | desktop 窗口打开但 API 请求失败 | 仪表盘显示空态/错误条（v1.16.0 降级逻辑，ADR-016） |

## 维度 2：数据库 Schema

无 schema 变更。desktop 窗口加载 web 前端静态产物。

## 维度 3：API 契约

无新 API。desktop 前端通过以下既有端点获取仪表盘数据（v1.15.0/v1.16.0 实现）：

| 端点 | 方法 | 用途 | 来源 |
|---|---|---|---|
| `/api/v1/agents` | GET | agent roster + activity_summary | `collaborate.py:419` (v1.15.0) |
| `/api/v1/agents/{name}/activity` | GET | agent 活动详情 | `collaborate.py:460` (v1.15.0) |
| `/api/v1/workflows` | GET | workflow 列表 durable + live | `collaborate.py:327` (v1.15.0) |
| `/ws` | WS | 实时推送 agent_status + workflow_progress | `app.py:306` (v1.16.0) |

dev 模式：vite proxy `/api` + `/ws` → saw web 后端（端口收敛后 8000，F-V-4 改动）。
prod 模式：前端直连 saw web 后端（`VITE_API_BASE_URL` 配置，默认 `http://localhost:8000`）。

## 维度 4：后端架构

无后端改动。desktop 消费 v1.15.0/v1.16.0 既有 REST + WS 端点。

## 维度 5：前端架构

### 状态管理

无前端代码改动。v1.16.0 既有：
- `@tanstack/react-query` 5.100.6（`web/package.json:14`）— useQuery + refetchInterval 15s polling
- `zustand` 5.0.12（`web/package.json`）— dashboardStore WS 推送状态
- `useWebSocket` hook（`web/src/hooks/useWebSocket.ts`）— WS 连接管理 + invalidateQueries

### @tauri-apps/api 集成

`web/package.json:11` = `"@tauri-apps/api": "^2.0.0"`，前端已集成 Tauri IPC API。desktop 内前端可调用：
- `@tauri-apps/api/window` — 窗口控制
- `@tauri-apps/api/event` — 事件监听（menu-event / shortcut 事件）
- `@tauri-apps/api/shell` — shell 命令（plugin:shell）

### 路由

`/dashboard` 路由已存在（v1.16.0 router.tsx 挂载 Dashboard 页）。

## 维度 6：基础设施需求

### 构建链

**prod 模式构建链**：
```
tauri build
  → beforeBuildCommand: npm run build --prefix ../web
    → tsc -b (TypeScript 类型检查)
    → vite build (构建前端到 web/dist/)
      → web/dist/index.html + web/dist/assets/index-*.js + index-*.css
  → cargo build --release (Rust 编译)
  → bundle (打包原生包，嵌入 web/dist 静态产物)
```

**dev 模式构建链**：
```
tauri dev
  → beforeDevCommand: npm run dev --prefix ../web
    → vite (启动 dev server, 端口 5173, 热更新)
  → desktop 窗口加载 http://localhost:5173
```

### 环境变量

| 变量 | 用途 | dev 值 | prod 值 |
|---|---|---|---|
| `VITE_API_BASE_URL` | REST API 基地址 | vite proxy 代理（不设值，走相对路径 /api） | `http://localhost:8000`（或用户配置） |
| `VITE_WS_URL` | WebSocket 地址 | vite proxy 代理（不设值，走相对路径 /ws） | `ws://localhost:8000/ws`（或用户配置） |

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-W-1 | `test_web_dist_integration.py`（新建）：检查 `web/dist/index.html` 存在 + 引用 assets/ → 验证 tauri.conf.json frontendDist 指向正确 → 模拟 tauri build 构建链（beforeBuildCommand 执行 → web/dist 产出 → Tauri 可嵌入） | unit（pytest + 文件检查 + json.load tauri.conf.json） | web/dist/index.html 存在且非空；tauri.conf.json frontendDist="../../web/dist"；beforeBuildCommand 存在且为 npm run build |
| AC-W-2 | `test_web_dev_integration.py`（新建）：检查 tauri.conf.json devUrl=http://localhost:5173 + beforeDevCommand=npm run dev → 验证 dev 模式 desktop 窗口加载 localhost:5173 | unit（pytest + json.load tauri.conf.json） | tauri.conf.json devUrl="http://localhost:5173"；beforeDevCommand="npm run dev --prefix ../web" |

### CI 兼容

全部用 Python pytest 运行（文件检查 + json parse），不依赖 Rust/Tauri 工具链。CI 始终跑。

> 注：AC-W-1 的完整验证（desktop 窗口打开后仪表盘页可访问，agent roster + workflow 列表渲染）需 05 实施后手动/冒烟验证——CI 中仅验证配置正确性 + web/dist 产出存在性。

## 维度 8：安全考量

- `web/dist` 为本地构建产物，无外部加载。
- `@tauri-apps/api` IPC 调用受 `desktop/src-tauri/capabilities/default.json` 权限控制（PRD ground G20）。
- `app.security.csp = null`（tauri.conf.json:24）—dev/prod 模式 CSP 关闭，后续可加固（defer）。

## 实现就绪度

- [x] frontendDist 路径验证点明确（../../web/dist → 项目根 web/dist/）
- [x] beforeBuildCommand/beforeDevCommand 构建链验证点明确
- [x] web/dist 构建产出存在性验证（index.html + assets/）
- [x] @tauri-apps/api ^2.0.0 集成验证
- [x] AC 覆盖 2/2
- [ ] 05 实施后 tauri build/dev 验证通过
