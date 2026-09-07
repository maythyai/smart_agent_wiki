---
id: SPEC-F-V-1
title: desktop 1.0 版本 bump + 配置收敛（4 文件 0.1.0→1.0.0 + tauri.conf.json 字段一致性审查）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-desktop-v1.17.0.md
pms_ref: .csp/product-spec/PMS-desktop.md
cms_ref: "[无 — desktop 栈无 CMS，ground 自源码]"
feature_id: F-V-1
complexity: S
tdd_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
adr_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
ac_coverage: 2/2
related_tasks: [".csp/tasks/TASKS-DELTA-v1.17.0.md"]
---

# SPEC-F-V-1: desktop 1.0 版本 bump + 配置收敛

## 实现 delta（ground 自源码）

> ADR-017 决策：desktop 嵌入策略 ③ Hybrid（dev proxy + prod external，sidecar defer），端口收敛 vite proxy 8080→8000。
> 本 Feature 为版本 bump + 配置审查，不涉及运行时代码改动。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `desktop/package.json:4` | `"version": "0.1.0"` | `"version": "1.0.0"` |
| `desktop/src-tauri/tauri.conf.json:5` | `"version": "0.1.0"` | `"version": "1.0.0"` |
| `desktop/src-tauri/Cargo.toml:3` | `version = "0.1.0"` | `version = "1.0.0"` |
| `web/package.json:4` | `"version": "0.1.0"` | `"version": "1.0.0"` |

### 不改动（配置一致性审查确认）

| 配置项 | 现状（ground） | 审查结论 |
|---|---|---|
| `$schema` | `desktop/src-tauri/tauri.conf.json:2` = `"https://schema.tauri.app/config/2"` | 保持 Tauri v2 schema ✓ |
| `frontendDist` | `tauri.conf.json:11` = `"../../web/dist"` | 路径正确，解析为项目根 web/dist/ ✓ |
| `devUrl` | `tauri.conf.json:10` = `"http://localhost:5173"` | 指向 vite dev server，dev 模式正确 ✓ |
| `beforeDevCommand` | `tauri.conf.json:8` = `"npm run dev --prefix ../web"` | tauri dev 前自动启动 vite dev server ✓ |
| `beforeBuildCommand` | `tauri.conf.json:9` = `"npm run build --prefix ../web"` | tauri build 前自动构建 web 前端 ✓ |
| `bundle.active` | `tauri.conf.json:22` = `true` | 打包启用 ✓ |
| `bundle.targets` | `tauri.conf.json:25` = `["msi","nsis","dmg","app","deb","rpm","appimage"]` | 跨平台目标完整，不缩减 ✓ |
| `Cargo.toml rust-version` | `desktop/src-tauri/Cargo.toml:7` = `"1.77.2"` | 保持不变 ✓ |
| `Cargo.toml edition` | `desktop/src-tauri/Cargo.toml:6` = `"2021"` | 保持不变 ✓ |
| `[profile.release]` | `Cargo.toml:28-33` = `panic="abort", codegen-units=1, lto=true, opt-level="s", strip=true` | 构建优化已配置 ✓ |
| `bundle.macOS.minimumSystemVersion` | `tauri.conf.json:36` = `"10.13"` | macOS 最低版本 ✓ |
| `bundle.macOS.entitlements` | `tauri.conf.json:35` = `null` | 未签名（defer 后续版本）✓ |
| `bundle.windows.webviewInstallMode` | `tauri.conf.json:28-30` = `{"type": "downloadBootstrapper", "silent": true}` | Windows WebView2 安装模式 ✓ |
| `bundle.windows.digestAlgorithm` | `tauri.conf.json:31` = `"sha256"` | Windows 签名摘要算法 ✓ |
| `bundle.linux.deb.depends` | `tauri.conf.json:39-41` = `["libwebkit2gtk-4.1-0"]` | Linux deb 依赖 ✓ |

## 维度 1：UI/UX 规格

无 UI 变更。本 Feature 为版本号修改 + 配置审查。

## 维度 2：数据库 Schema

无 schema 变更。版本号修改为静态文件操作。

## 维度 3：API 契约

无 API 变更。

## 维度 4：后端架构

无后端改动。

## 维度 5：前端架构

无前端代码改动。

## 维度 6：基础设施需求

### 版本一致性校验

4 文件版本号必须一致：
- `desktop/package.json:4` version
- `desktop/src-tauri/tauri.conf.json:5` version
- `desktop/src-tauri/Cargo.toml:3` version
- `web/package.json:4` version

校验方式：`grep -n '"version"' desktop/package.json desktop/src-tauri/tauri.conf.json web/package.json` + `grep -n '^version' desktop/src-tauri/Cargo.toml` → 全部输出 `1.0.0`。

### tauri.conf.json 配置一致性审查

审查 `tauri.conf.json` 全字段（`$schema`/`productName`/`version`/`identifier`/`build`/`app`/`bundle`/`plugins`）无废弃字段。Tauri v2 schema 字段：
- `build.beforeDevCommand` / `build.devUrl` / `build.beforeBuildCommand` / `build.frontendDist` — Tauri v2 build 配置 ✓
- `app.withGlobalTauri` / `app.windows` / `app.security.csp` — Tauri v2 app 配置 ✓
- `bundle.active` / `bundle.icon` / `bundle.targets` / `bundle.windows` / `bundle.macOS` / `bundle.linux` — Tauri v2 bundle 配置 ✓
- `plugins.shell.open` — Tauri v2 plugin 配置 ✓

无废弃字段。

### 环境变量

无新环境变量。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-V-1 | `test_version_consistency.py`（新建）：grep 4 文件 version 字段 → 断言全部 = `1.0.0` | unit（pytest + subprocess/grep） | desktop/package.json version=1.0.0, tauri.conf.json version=1.0.0, Cargo.toml version=1.0.0, web/package.json version=1.0.0 |
| AC-V-2 | `test_tauri_config_consistency.py`（新建）：parse tauri.conf.json → 断言 frontendDist=../../web/dist, devUrl=http://localhost:5173, bundle.active=true, $schema=https://schema.tauri.app/config/2, 无废弃字段 | unit（pytest + json.load） | 所有配置项符合预期值 |

### CI 兼容

全部用 Python pytest 运行，不依赖 Rust/Tauri 工具链。CI 始终跑。

## 维度 8：安全考量

- 版本号变更不引入安全风险。
- Cargo.toml 依赖不盲目 update（使用 Cargo.lock 锁定版本，PRD §8 风险 6）。
- `app.security.csp = null`（`tauri.conf.json:24`）—桌面端 dev 模式 CSP 关闭，prod 模式可后续加固（defer）。

## 实现就绪度

- [x] 4 文件版本号改动点明确（0.1.0→1.0.0）
- [x] tauri.conf.json 配置审查清单完整（15 项全 ✓）
- [x] 无废弃字段（Tauri v2 schema 字段全核对）
- [x] AC 覆盖 2/2
- [ ] 05 实施后版本一致性校验 + 配置审查测试通过
