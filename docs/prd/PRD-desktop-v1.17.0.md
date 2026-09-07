---
id: PRD-desktop-v1.17.0
title: desktop 完成 v4.4
version: 1.0
status: Released
date: 2026-09-07
product_type: platform
feature_count: 4
mvp_scope: [desktop-version-bump, web-dashboard-integration, tauri-build-verification, backend-coordination]
thin_sections: []
upstream_source: .csp/artifacts/retrospective-v1.16.0.md + v1.16.0 web 仪表盘就绪
roadmap_ref: docs/strategy/ROADMAP.md#v1.17.0
target_version: v1.17.0
related_pms: [.csp/product-spec/PMS-desktop.md]
related_specs: [.csp/specs/SPEC-F-V-1.md, .csp/specs/SPEC-F-V-2.md, .csp/specs/SPEC-F-V-3.md, .csp/specs/SPEC-F-V-4.md]
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
---

# PRD: desktop 完成 v4.4

**Version**: v1.0 | **Author**: [TBD] | **Date**: 2026-09-07 | **Status**: Approved

## 1. 背景与目标

### 1.1 背景

Smart Agent Wiki 的桌面端（Tauri v2）自初始搭建以来一直停留在 `0.1.0` 版本，独立于 canonical pyproject 版本跟踪。ROADMAP §1.2 规定桌面端在未达 1.0 前以独立 0.x 跟踪，达到 v1.0 后与 canonical 对齐。v1.16.0 已交付 realtime 仪表盘（agent roster + activity + workflow 运行态 + 实时更新），web 前端构建产出（`web/dist`）已就绪。v1.16.0 复盘 finding U4 明确指出"desktop 仍 0.1.0"是 v1.17.0 候选。

桌面端现有代码已是一个功能完整的 Tauri v2 应用——8 个插件（shell/store/dialog/fs/global-shortcut/os/clipboard-manager/process）、16 个 IPC 命令（文件选择/文件夹监听/导出/偏好设置）、原生菜单栏、系统托盘、主题检测、文件监听器、全局快捷键。`tauri.conf.json` 已配置 `frontendDist: "../../web/dist"` 和 `devUrl: "http://localhost:5173"`，即 web 仪表盘集成路径已在配置层面打通。但版本号仍为 0.1.0，`tauri build` 尚未验证产出原生包，且 dev 代理端口（vite proxy → 8080）与 `saw web` 默认端口（8000）存在不一致。

不做会怎样：桌面端无法作为 1.0 产品发布——版本号不体面、构建未验证、端口不一致导致 dev 模式下前后端协同可能断裂。
做了会怎样：桌面端达 1.0，与 canonical 版本对齐，`tauri build` 可产出原生包，用户一键启动桌面应用即可访问 v1.16.0 仪表盘。

### 1.2 目标用户

| 用户角色 | 特征 | 核心需求 | 使用场景 |
|---|---|---|---|
| OPS 运维人员 | 管理多代理系统，关注 agent/workflow 运行态 | 桌面原生应用一键启动，实时查看 agent roster + workflow 状态 | 日常运维、故障排查时打开桌面应用查看仪表盘 |
| 普通用户（非 CLI） | 不熟悉命令行，需要图形界面访问知识库 | 无需终端即可使用 SAW 的核心能力 | 安装桌面应用后直接使用，不运行 `saw web` |

### 1.3 业务目标与成功指标

| 目标 | 指标 | 目标值 | 监控方式 |
|---|---|---|---|
| 桌面端版本对齐 | desktop 版本号 | 1.0.0（package.json + tauri.conf.json + Cargo.toml + web/package.json） | 版本一致性校验 |
| 原生包构建 | `tauri build` 产出 | 至少 1 个原生包产物（macOS .app） | 构建产物存在性检查 |
| web 仪表盘集成 | desktop 内仪表盘可访问 | 仪表盘页在 desktop 内可加载并渲染 | 手动/冒烟验证 |
| 后端不回归 | pytest 通过数 | ≥ 2217 passed（v1.16.0 基线） | CI 测试 |

## 2. 需求概述

桌面端 0.1.0→1.0.0，集成 web 仪表盘，验证 `tauri build` 产出原生包。

## 3. 详细功能设计

### 3.1 desktop 版本 bump + 配置收敛

- **描述**：将 desktop 三个版本文件（`desktop/package.json`、`desktop/src-tauri/tauri.conf.json`、`desktop/src-tauri/Cargo.toml`）从 `0.1.0` 提升到 `1.0.0`，同时将 `web/package.json` 从 `0.1.0` 提升到 `1.0.0`。审查 `tauri.conf.json` 配置项一致性——`frontendDist`、`devUrl`、`beforeDevCommand`、`beforeBuildCommand`、`bundle` 配置无遗留废弃字段。
- **用户故事**：作为发布工程师，我想桌面端版本号达到 1.0.0，以便与 canonical pyproject 版本对齐，标记桌面端为稳定产品。
- **优先级**：P0
- **业务规则**：
  1. 版本号 `0.1.0` → `1.0.0`，四文件同步：`desktop/package.json`、`desktop/src-tauri/tauri.conf.json`、`desktop/src-tauri/Cargo.toml`、`web/package.json`
  2. 版本对齐遵循 ROADMAP §1.6 多平台一致性规则——desktop 达 1.0 后与 canonical 对齐
  3. `tauri.conf.json` 的 `$schema` 保持 `https://schema.tauri.app/config/2`（Tauri v2 schema）
  4. `Cargo.toml` 的 `rust-version` 保持 `1.77.2`，`edition` 保持 `2021`
  5. 配置收敛：`frontendDist` = `../../web/dist`、`devUrl` = `http://localhost:5173`、`beforeDevCommand` = `npm run dev --prefix ../web`、`beforeBuildCommand` = `npm run build --prefix ../web`——这些已有配置不变更，仅审查确认一致性
  6. `bundle.targets` 保持现有目标列表（`msi/nsis/dmg/app/deb/rpm/appimage`），不缩减——跨平台覆盖是 1.0 的基线
- **交互流程**：入口（修改 4 文件版本号）→ 步骤（审查 tauri.conf.json 全字段）→ 成功反馈（4 文件 version=1.0.0 + 配置一致性确认）→ 失败处理（版本不一致 → 校验失败，配置冲突 → 回滚）
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| Cargo.toml 版本与 tauri.conf.json 不一致 | 构建时 Tauri 报错 | "Cargo.toml version must match tauri.conf.json version" |
| web/package.json 版本未同步 | 版本一致性校验失败 | "web/package.json version 0.1.0 != desktop 1.0.0, must align" |

### 3.2 web 仪表盘集成（frontendDist 指向 web/dist）

- **描述**：确认 `tauri.conf.json` 的 `frontendDist: "../../web/dist"` 配置正确指向 v1.16.0 web 构建产出。`beforeBuildCommand` 在 `tauri build` 前自动执行 `npm run build --prefix ../web` 构建 web 前端到 `web/dist`，desktop 加载该产物作为原生窗口内容。dev 模式下 `devUrl: "http://localhost:5173"` 加载 vite dev server，支持热更新。
- **用户故事**：作为 OPS 运维人员，我想在桌面应用内直接看到 agent roster + activity + workflow 运行态仪表盘，以便无需浏览器即可监控多代理系统。
- **优先级**：P0
- **业务规则**：
  1. `frontendDist` 路径 `../../web/dist` 相对于 `desktop/src-tauri/`，解析为项目根 `web/dist/`——已有配置，不变更
  2. `beforeBuildCommand` = `npm run build --prefix ../web`：`tauri build` 前自动构建 web 前端（`tsc -b && vite build`），产出 `web/dist/index.html` + `web/dist/assets/`
  3. `beforeDevCommand` = `npm run dev --prefix ../web`：`tauri dev` 前自动启动 vite dev server（端口 5173）
  4. dev 模式：desktop 窗口加载 `http://localhost:5173`（vite dev server），前端热更新生效
  5. prod 模式：desktop 窗口加载 `web/dist` 静态产物，无 dev server 依赖
  6. web 前端已集成 `@tauri-apps/api`（v2.0.0+），可在 desktop 内调用原生 IPC 命令
  7. `web/dist/` 当前已有 v1.16.0 构建产出（`index.html` + `assets/`），构建命令幂等覆盖
- **交互流程**：入口（`tauri build` 触发 `beforeBuildCommand`）→ 步骤（vite build → web/dist → Tauri 打包嵌入）→ 成功反馈（desktop 窗口打开后仪表盘页可访问，agent roster + workflow 列表渲染）→ 失败处理（web build 失败 → tauri build 中止；frontendDist 路径不存在 → tauri build 报错）
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| web/dist 不存在或为空 | `beforeBuildCommand` 先执行 web 构建；若构建失败则 tauri build 中止 | "beforeBuildCommand failed: npm run build --prefix ../web" |
| vite build 类型错误 | `tsc -b` 报类型错误，web build 失败 | "TypeScript compilation errors in web frontend" |
| 仪表盘页在 desktop 内空白 | 检查 frontendDist 路径 + web/dist/index.html 存在性 | "frontendDist not found or empty, check web build output" |

### 3.3 tauri build 验证（产 .app/.dmg）

- **描述**：执行 `tauri build` 验证桌面端可产出原生包。`tauri.conf.json` 的 `bundle.targets` 已配置 `["msi", "nsis", "dmg", "app", "deb", "rpm", "appimage"]`，覆盖 macOS（.app/.dmg）、Windows（.msi/.nsis）、Linux（.deb/.rpm/.appimage）。本轮验证至少 macOS .app 产出成功（当前运行环境为 Linux，验证 .deb 或 .appimage 产出；macOS .app 为声明性目标，实际产出依赖目标平台）。
- **用户故事**：作为发布工程师，我想 `tauri build` 成功产出原生包，以便用户安装桌面应用而非通过命令行运行。
- **优先级**：P0
- **业务规则**：
  1. `tauri build` 执行流程：`beforeBuildCommand`（web 构建）→ Rust 编译（`cargo build --release`）→ 原生打包（bundle targets）
  2. Rust 工具链已安装（`cargo`/`rustc` 可用），`Cargo.toml` 依赖已锁定（`Cargo.lock` 存在）
  3. `bundle.active = true`，打包启用
  4. macOS 配置：`minimumSystemVersion: "10.13"`，`entitlements: null`（未签名——签名/公证非本轮目标，defer）
  5. Windows 配置：`webviewInstallMode` = `downloadBootstrapper`（silent），`digestAlgorithm: "sha256"`
  6. Linux 配置：`deb.depends: ["libwebkit2gtk-4.1-0"]`
  7. 构建产物输出到 `desktop/src-tauri/target/release/bundle/` 目录
  8. 签名/公证明确非本轮目标——defer 到后续版本（需 Apple Developer ID + notarytool）
  9. release profile 已优化：`panic = "abort"`, `codegen-units = 1`, `lto = true`, `opt-level = "s"`, `strip = true`
- **交互流程**：入口（`cd desktop && npm run tauri:build`）→ 步骤（web build → cargo build --release → bundle）→ 成功反馈（`target/release/bundle/` 下产出原生包）→ 失败处理（Rust 编译错误 → 中止；web build 错误 → 中止；打包工具缺失 → 报错）
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| Rust 编译错误（类型/借用/依赖） | cargo 报错，tauri build 中止 | "cargo build --release failed, check Rust compilation errors" |
| 系统缺少 webkit2gtk（Linux） | cargo 编译 tauri 依赖时链接失败 | "Install libwebkit2gtk-4.1-dev and re-run" |
| 磁盘空间不足 | 打包阶段失败 | "Insufficient disk space for bundle output" |

### 3.4 后端协同（dev proxy + prod 模式）

- **描述**：明确 desktop 与 saw 后端服务器的协同模式。dev 模式下，vite dev server（5173）代理 `/api` 和 `/ws` 到 saw 后端；prod 模式下，desktop 加载 `web/dist` 静态产物，需连接独立运行的 saw 服务器或内嵌后端。当前 vite proxy 配置目标端口为 8080，而 `saw web` 默认端口为 8000——存在端口不一致，需在本轮收敛。
- **用户故事**：作为开发者，我想 dev 模式下 desktop 前端自动代理到 saw 后端，prod 模式下用户可配置后端地址，以便开发时无缝协同、生产时灵活部署。
- **优先级**：P1
- **业务规则**：
  1. dev 模式：vite dev server（5173）代理 `/api` → saw 后端，`/ws` → saw 后端 WebSocket——当前 proxy target 为 `http://localhost:8080` / `ws://localhost:8080`
  2. `saw web` 默认端口 8000（`web_cmd.py` line 25），vite proxy 目标 8080——**端口不一致**，需收敛（方案：proxy target 改为 8000，或文档约定 `saw web --port 8080`；具体 HOW 留 03 技术方案）
  3. prod 模式：desktop 加载 `web/dist` 静态产物，无 vite dev server 代理——前端需直连 saw 后端（用户配置地址或默认 localhost:8000）
  4. prod 模式下 saw 后端可独立运行（用户手动 `saw web`）或 desktop 内嵌启动（sidecar 模式）——具体实现方案留 03 技术方案
  5. CORS 配置：`saw web` 默认 CORS origins 为 `localhost:3000,127.0.0.1:3000`——desktop dev 模式使用 5173，需在 CORS 允许列表中添加 `localhost:5173`（具体 HOW 留 03）
  6. WebSocket 路由：saw 后端 WS 路由挂载在 `/ws` prefix（`app.py` line 306），vite proxy `/ws` 代理到后端——路径一致，仅端口需收敛
- **交互流程**：入口（dev: `tauri dev` → vite 5173 → proxy → saw 8080/8000；prod: desktop → web/dist → saw 独立/内嵌）→ 步骤（端口收敛 + CORS 扩展 + prod 连接配置）→ 成功反馈（dev 模式仪表盘数据加载 + WS 实时更新生效；prod 模式仪表盘可访问）→ 失败处理（端口不一致 → API 请求 502；CORS 未配 → 请求被拒）
- **异常处理**：

| 场景 | 处理 | 用户提示 |
|---|---|---|
| saw 后端未启动 | 前端 API 请求失败，仪表盘显示空态/错误条 | "Cannot connect to server. Is `saw web` running?" |
| CORS 未允许 5173 | 浏览器控制台 CORS 错误，API 请求被拒 | "CORS policy blocked request from localhost:5173" |
| WS 连接失败 | 仪表盘降级为 polling 模式（v1.16.0 已有降级逻辑） | "Live updates paused, showing cached data" |

## 4. 非功能要求

| 类别 | 要求 | 验收标准 |
|---|---|---|
| 构建成功 | `tauri build` 无错误完成 | 构建退出码 0，`target/release/bundle/` 下产出至少 1 个原生包 |
| 后端不回归 | v1.16.0 后端测试基线不回归 | pytest ≥ 2217 passed（v1.16.0 基线），ruff 0，coverage ≥ 67% |
| 前端不回归 | v1.16.0 前端测试基线不回归 | vitest 64 passed（13 files），tsc -b + vite build success |
| 包大小 [TBD] | 桌面包产物大小合理 | 原生包大小 `[TBD]` MB（首次基线，无回归阈值） |
| 启动时间 | desktop 窗口首次渲染 < 3 秒 | 从应用启动到窗口可见 < 3 秒（本地环境） |
| 版本一致性 | 4 文件版本号一致 | package.json / tauri.conf.json / Cargo.toml / web/package.json 均为 1.0.0 |

## 5. 数据需求

| 事件名 | 触发条件 | 关键属性 | 用途 |
|---|---|---|---|
| desktop_app_launched | 用户启动桌面应用 | platform, version, launch_mode (dev/prod) | 验证桌面端使用量 |
| dashboard_viewed | 用户访问仪表盘页 | agent_count, workflow_count | 验证仪表盘使用率 |
| tauri_build_completed | `tauri build` 完成 | success, duration, artifact_count, artifact_size | 构建健康度监控 |
| backend_connection_status | desktop 连接 saw 后端 | status (connected/failed), port, mode (dev/prod) | 协同可用性监控 |

## 6. 验收标准

| ID | 场景 | Given | When | Then |
|---|---|---|---|---|
| AC-V-1 | 版本 bump | desktop/package.json version=0.1.0, tauri.conf.json version=0.1.0, Cargo.toml version=0.1.0, web/package.json version=0.1.0 | 版本号提升到 1.0.0 | 4 文件 version 均为 1.0.0，版本一致性校验通过 |
| AC-V-2 | 配置收敛 | tauri.conf.json 有 frontendDist/devUrl/beforeDevCommand/beforeBuildCommand/bundle 配置 | 审查配置一致性 | frontendDist=../../web/dist, devUrl=http://localhost:5173, bundle.active=true, 无废弃字段 |
| AC-W-1 | web 仪表盘 prod 集成 | web/dist 包含 v1.16.0 仪表盘构建产出（index.html + assets/） | `tauri build` 执行，desktop 加载 web/dist | desktop 窗口打开后仪表盘页可访问，agent roster + workflow 列表渲染 |
| AC-W-2 | web 仪表盘 dev 集成 | vite dev server 运行在 5173，saw 后端运行 | `tauri dev` 执行 | desktop 窗口加载 localhost:5173，仪表盘渲染，前端热更新生效 |
| AC-B-1 | tauri build 成功 | Rust 工具链已装，Cargo.lock 存在，web 前端可构建 | `tauri build` 执行 | 构建退出码 0，`target/release/bundle/` 下产出至少 1 个原生包 |
| AC-B-2 | macOS 构建目标 | tauri.conf.json bundle.targets 包含 "app" 和 "dmg" | 构建在 macOS 环境执行 | 产出 .app bundle（至少）；.dmg 为声明性目标，实际产出依赖构建环境 |
| AC-C-1 | dev proxy 端口收敛 | vite proxy target=8080, saw web default port=8000 | 端口一致性审查 | proxy target 与 saw web 端口对齐（proxy→8000 或文档约定 saw web --port 8080） |
| AC-C-2 | prod 后端连接 | prod 模式 desktop 加载 web/dist，无 dev proxy | 用户配置或默认 saw 后端地址 | 前端可连接 saw 后端，仪表盘数据加载，WS 实时更新生效（或降级为 polling） |
| AC-C-3 | CORS 扩展 | saw web CORS origins 默认 localhost:3000 | desktop dev 模式使用 5173 | CORS 允许列表包含 localhost:5173，API 请求不被 CORS 拒绝 |

## 7. 排期估算

| 阶段 | 预估工作量 | 依赖 | 风险 |
|---|---|---|---|
| 版本 bump + 配置收敛 | 0.5h | 无 | 低（4 文件版本号修改 + 审查） |
| web 仪表盘集成验证 | 1h | 版本 bump | 低（frontendDist 已配置，验证为主） |
| tauri build 验证 | 2-4h | 版本 bump + web 集成 | 中（Rust 编译 + 系统依赖 webkit2gtk） |
| 后端协同（端口收敛 + CORS） | 1h | 无 | 低（配置修改 + 验证） |
| 测试 + 回归验证 | 1h | 全部 | 低（后端 pytest + 前端 vitest 不回归） |

## 8. 风险与依赖

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| Rust 系统依赖缺失（webkit2gtk） | 中 | 高（tauri build 失败） | 提前检查 `libwebkit2gtk-4.1-dev` 已装 |
| 签名/公证缺失（macOS .dmg 未签名） | 高 | 中（用户安装时 Gatekeeper 警告） | 明确 defer 到后续版本，本轮产出 unsigned 包 |
| 端口不一致（vite proxy 8080 vs saw web 8000） | 高 | 中（dev 模式 API 502） | 本轮收敛端口，统一为 8000 或文档约定 8080 |
| prod 模式后端连接方式未定 | 中 | 中（prod 模式仪表盘不可用） | 本轮明确 prod 模式 saw 后端独立运行或 sidecar，具体实现留 03 |
| Cargo.lock 依赖漂移 | 低 | 低（cargo update 风险） | 使用 Cargo.lock 锁定版本，不盲目 update |
| 前端 `@tauri-apps/api` 版本不匹配 | 低 | 低（IPC 调用失败） | web/package.json 已有 `@tauri-apps/api: ^2.0.0`，与 tauri 2.x 兼容 |

### 依赖

- **前置依赖**：v1.16.0 基线（web 仪表盘就绪，`web/dist` 构建产出存在）
- **工具链依赖**：Rust 工具链（`cargo`/`rustc` 已装），Node.js + npm（web 构建用）
- **系统依赖**：Linux 构建 webkit2gtk-4.1-dev（deb 打包依赖）

### 明确非本轮目标（defer）

- **代码签名 / 公证**：macOS Apple Developer ID 签名 + notarytool 公证——需 Apple Developer 账号 + 配置，defer 到后续版本
- **自动更新**（tauri updater）：defer 到后续版本
- **N3/S/T/U 续留 findings**：per-request workspace（N3/K2）、ANN 大规模 benchmark（S1/S2）、COVERAGE-REPORT 状态更新（S3）、engine.py 拆分（S4）、agent activity 持久化（T1）、links apply undo（T2）、自定义角色分享（T3）、agents_cmd CLI 结构（T4）、Playwright E2E（U1）、polling interval 可配（U2）、vLLM-unreachable skip（U3）、vitest 路径偏离（U5）、ConnectionStatus 横幅位置（U6）——均 Low/P3，defer

## 附录

### ground 自源码 + desktop 栈

| # | claim | file:line | 现状 | TRUE/FALSE |
|---|---|---|---|---|
| G1 | desktop/package.json version=0.1.0 | desktop/package.json:4 | `"version": "0.1.0"` → 需 bump 1.0.0 | TRUE |
| G2 | desktop/src-tauri/tauri.conf.json version=0.1.0 | desktop/src-tauri/tauri.conf.json:5 | `"version": "0.1.0"` → 需 bump 1.0.0 | TRUE |
| G3 | desktop/src-tauri/Cargo.toml version=0.1.0 | desktop/src-tauri/Cargo.toml:3 | `version = "0.1.0"` → 需 bump 1.0.0 | TRUE |
| G4 | web/package.json version=0.1.0 | web/package.json:4 | `"version": "0.1.0"` → 需 bump 1.0.0 | TRUE |
| G5 | frontendDist 指向 web/dist | desktop/src-tauri/tauri.conf.json:11 | `"frontendDist": "../../web/dist"` → web 集成已配置 | TRUE |
| G6 | devUrl 指向 vite dev server | desktop/src-tauri/tauri.conf.json:10 | `"devUrl": "http://localhost:5173"` → dev 模式已配置 | TRUE |
| G7 | beforeBuildCommand 触发 web 构建 | desktop/src-tauri/tauri.conf.json:9 | `"beforeBuildCommand": "npm run build --prefix ../web"` → 构建链已配置 | TRUE |
| G8 | vite proxy /api → 8080 | web/vite.config.ts:18 | `target: 'http://localhost:8080'` → proxy 目标 8080 | TRUE |
| G9 | saw web 默认端口 8000 | src/saw/drivers/cli/commands/web_cmd.py:25 | `port: int = typer.Option(8000, ...)` → 端口不一致 (8080 vs 8000) | TRUE |
| G10 | web/dist 构建产出存在 | web/dist/index.html | v1.16.0 构建产出（index.html + assets/）已就绪 | TRUE |
| G11 | bundle.targets 含 macOS .app/.dmg | desktop/src-tauri/tauri.conf.json:25 | `"targets": ["msi","nsis","dmg","app","deb","rpm","appimage"]` → 跨平台目标已配置 | TRUE |
| G12 | desktop 已有 8 插件 + 16 IPC 命令 | desktop/src-tauri/src/main.rs:16-22,43-58 | 8 plugin init + 16 invoke_handler → 完整桌面应用已搭建 | TRUE |
| G13 | Cargo.lock 存在（依赖锁定） | desktop/src-tauri/Cargo.lock | 136688B → 依赖已锁定 | TRUE |
| G14 | tauri v2 schema | desktop/src-tauri/tauri.conf.json:2 | `"$schema": "https://schema.tauri.app/config/2"` → Tauri v2 | TRUE |
| G15 | web 已集成 @tauri-apps/api | web/package.json:11 | `"@tauri-apps/api": "^2.0.0"` → 前端可调用 desktop IPC | TRUE |
| G16 | pyproject canonical=1.16.0 | pyproject.toml:7 | `version = "1.16.0"` → desktop 1.0.0 后对齐 | TRUE |
| G17 | saw 后端 CORS 默认 3000 | src/saw/drivers/cli/commands/web_cmd.py:33 | `cors_origins: "http://localhost:3000,..."` → 需加 5173 | TRUE |
| G18 | saw 后端 WS 路由 /ws prefix | src/saw/drivers/web/app.py:306 | `app.include_router(integrations_ws_router, prefix="/ws", ...)` → WS 路径与 vite proxy 一致 | TRUE |
| G19 | release profile 已优化 | desktop/src-tauri/Cargo.toml:28-33 | `panic="abort", lto=true, opt-level="s", strip=true` → 构建优化已配置 | TRUE |
| G20 | capabilities/default.json 权限配置 | desktop/src-tauri/capabilities/default.json:8-26 | core/shell/dialog/fs/store/global-shortcut/os/clipboard/process 权限 → 完整权限已配置 | TRUE |

### 下一步建议

- [ ] 进入需求拆解 → 把 4 功能模块翻成 Feature 清单 + 依赖图 + NFR，落 .csp/decomposition/
- [ ] desktop 版本 bump + 配置收敛（G1-G4, G5-G7）为 Wave 1 先行项
- [ ] tauri build 验证（G11, G13, G19）依赖版本 bump 完成
- [ ] 后端协同端口收敛（G8-G9, G17-G18）可并行
- [ ] 进入 03 技术方案 → 读 PRD + decomposition + PMS，按需选型（prod 模式 saw 后端嵌入 vs 独立）+ 产出 TDD + Spec
- [ ] 签名/公证明确 defer——后续版本需 Apple Developer ID

当前产物：docs/prd/PRD-desktop-v1.17.0.md（status: Approved）+ .csp/product-spec/PMS-desktop.md（ready）+ docs/prd/PRD-INDEX.md 已登记 + .csp/product-spec/PMS-INDEX.md 已登记。已写 .csp/lifecycle-state.json：01 done，current_stage=02-decomposition。
