# PMS: desktop — 桌面端完成模块

> 产品说明书（PMS）living baseline。模块边界 = PRD §3 模块边界，下游 02/03 不得越界。

## 模块边界

| 维度 | 内容 |
|---|---|
| **slug** | desktop |
| **边界一句话** | 桌面端 Tauri v2 0.1.0→1.0.0 版本对齐 + web 仪表盘集成（frontendDist→web/dist）+ tauri build 验证（产原生包）+ 后端协同（dev proxy + prod 模式） |
| **做什么** | 版本号 bump（4 文件）、配置收敛审查、web 构建产出嵌入验证、tauri build 原生包产出验证、dev/prod 模式后端协同端口收敛 + CORS 扩展 |
| **不做什么** | 代码签名/公证（defer）、自动更新（defer）、新增 IPC 命令（复用既有 16 命令）、新增 Tauri 插件（复用既有 8 插件）、前端仪表盘功能变更（消费 v1.16.0 既有产物） |
| **优先级** | P0 |
| **关联 PRD** | docs/prd/PRD-desktop-v1.17.0.md |
| **关联 Spec** | SPEC-F-V-1.md, SPEC-F-V-2.md, SPEC-F-V-3.md, SPEC-F-V-4.md（03 技术方案产出） |
| **状态** | ready |

## 验收形态

| AC ID | 场景 | 验收要点 |
|---|---|---|
| AC-V-1 | 版本 bump | 4 文件（package.json/tauri.conf.json/Cargo.toml/web/package.json）version=1.0.0 |
| AC-V-2 | 配置收敛 | frontendDist/devUrl/beforeDevCommand/beforeBuildCommand/bundle 配置一致，无废弃字段 |
| AC-W-1 | web 仪表盘 prod 集成 | tauri build 后 desktop 内仪表盘页可访问，agent roster + workflow 列表渲染 |
| AC-W-2 | web 仪表盘 dev 集成 | tauri dev 后 desktop 窗口加载 localhost:5173，仪表盘渲染，热更新生效 |
| AC-B-1 | tauri build 成功 | 构建退出码 0，target/release/bundle/ 下产出至少 1 个原生包 |
| AC-B-2 | macOS 构建目标 | bundle.targets 含 "app"/"dmg"，macOS 环境产出 .app bundle |
| AC-C-1 | dev proxy 端口收敛 | vite proxy target 与 saw web 端口对齐 |
| AC-C-2 | prod 后端连接 | prod 模式 frontend 可连接 saw 后端，仪表盘数据加载 |
| AC-C-3 | CORS 扩展 | CORS 允许列表包含 localhost:5173 |

## 对外接口契约摘要

| 接口 | 方向 | 说明 |
|---|---|---|
| desktop → saw web REST /api/v1/* | desktop 前端 → saw 后端 | dev: vite proxy；prod: 直连（复用 v1.15.0/v1.16.0 既有 REST 端点） |
| desktop → saw web WS /ws | desktop 前端 → saw 后端 | dev: vite proxy ws:true；prod: 直连（复用 v1.16.0 既有 WS 路由） |
| desktop → web/dist 静态产物 | Tauri webview ← web/dist | tauri.conf.json frontendDist 指向，prod 模式加载 |
| desktop → vite dev server 5173 | Tauri webview ← localhost:5173 | tauri.conf.json devUrl 指向，dev 模式加载 |
| saw web CORS | saw 后端 → desktop 前端 | 需扩展允许 localhost:5173（dev 模式） |

## 模块组件清单

| 组件 | 路径 | 角色 |
|---|---|---|
| Tauri 配置 | desktop/src-tauri/tauri.conf.json | 版本号 + frontendDist/devUrl/build config + bundle targets |
| Cargo 配置 | desktop/src-tauri/Cargo.toml | Rust 依赖 + release profile |
| desktop package | desktop/package.json | npm scripts (tauri:dev/tauri:build) + @tauri-apps/cli |
| web package | web/package.json | web 前端依赖 + 版本号 |
| Rust 入口 | desktop/src-tauri/src/main.rs | 8 插件 + 16 IPC 命令 + setup 逻辑 |
| IPC 命令 | desktop/src-tauri/src/commands/ | fs/preferences/export 命令 |
| 原生 UI | desktop/src-tauri/src/menu.rs, tray.rs, theme.rs | 菜单/托盘/主题 |
| 文件监听 | desktop/src-tauri/src/watcher.rs | 文件夹监听 |
| 权限 | desktop/src-tauri/capabilities/default.json | Tauri v2 capability 权限声明 |
| vite 代理 | web/vite.config.ts | dev 模式 /api + /ws 代理配置 |
| saw 后端入口 | src/saw/drivers/web/app.py | FastAPI create_app + CORS + WS 路由 |
| saw web CLI | src/saw/drivers/cli/commands/web_cmd.py | `saw web` 命令（host/port/cors 参数） |

## 变更历史

| 日期 | 变更 | 来源 |
|---|---|---|
| 2026-09-07 | 初始创建 | PRD-desktop-v1.17.0（v1.17.0 周期 01-prd） |
