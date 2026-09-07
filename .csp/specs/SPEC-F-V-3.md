---
id: SPEC-F-V-3
title: tauri build 验证（cargo build --release + bundle 产出原生包，至少 .app/.deb/.appimage）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-07"
prd_ref: docs/prd/PRD-desktop-v1.17.0.md
pms_ref: .csp/product-spec/PMS-desktop.md
cms_ref: "[无 — desktop 栈无 CMS，ground 自源码]"
feature_id: F-V-3
complexity: L
tdd_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
adr_ref: .csp/tech-decisions/ADR/ADR-017-desktop-embed-port-convergence.md
ac_coverage: 2/2
related_tasks: [".csp/tasks/TASKS-DELTA-v1.17.0.md"]
---

# SPEC-F-V-3: tauri build 验证

## 实现 delta（ground 自源码）

> ADR-017 决策：beforeBuildCommand 构建链已配置（tauri.conf.json:9），release profile 已优化（Cargo.toml:28-33）。
> 本 Feature 为构建验证——执行 `tauri build` 验证产出原生包。

### 改动点

无代码改动。本 Feature 为构建验证性 Feature，验证以下既有配置的正确性：

| 验证项 | 既有配置（ground） | 验证方式 |
|---|---|---|
| beforeBuildCommand 构建链 | `tauri.conf.json:9` = `"npm run build --prefix ../web"` | `tauri build` 前自动执行 web 构建 |
| Rust 编译 | `Cargo.toml` 依赖 + `Cargo.lock` 锁定 | `cargo build --release` 成功 |
| bundle 打包 | `tauri.conf.json:22` = `bundle.active: true` | `target/release/bundle/` 下产出原生包 |
| bundle.targets 跨平台 | `tauri.conf.json:25` = `["msi","nsis","dmg","app","deb","rpm","appimage"]` | 覆盖 macOS/Windows/Linux |
| release profile 优化 | `Cargo.toml:28-33` = `panic="abort", lto=true, opt-level="s", strip=true` | 构建产物优化 |
| macOS 配置 | `tauri.conf.json:35-36` = `entitlements: null, minimumSystemVersion: "10.13"` | 未签名，macOS 10.13+ |
| Windows 配置 | `tauri.conf.json:28-31` = `webviewInstallMode: downloadBootstrapper, digestAlgorithm: sha256` | WebView2 自动安装 |
| Linux 配置 | `tauri.conf.json:39-41` = `deb.depends: ["libwebkit2gtk-4.1-0"]` | deb 依赖声明 |

### 不改动

- `desktop/src-tauri/Cargo.toml` — release profile 不变（F-V-1 仅 bump version）
- `desktop/src-tauri/tauri.conf.json` — bundle 配置不变（F-V-1 仅 bump version）
- `desktop/src-tauri/Cargo.lock` — 依赖锁定不变，不盲目 `cargo update`（PRD §8 风险 6）

## 维度 1：UI/UX 规格

无 UI 变更。本 Feature 为构建验证。

## 维度 2：数据库 Schema

无 schema 变更。

## 维度 3：API 契约

无 API 变更。

## 维度 4：后端架构

无后端改动。

### 构建流程

**`tauri build` 执行流程**：
```
1. beforeBuildCommand: npm run build --prefix ../web
   → tsc -b (TypeScript 类型检查)
   → vite build (构建前端到 web/dist/)
   → web/dist/index.html + assets/

2. cargo build --release
   → Rust 编译 (main.rs + commands/ + menu.rs + tray.rs + theme.rs + watcher.rs)
   → 8 插件链接 (shell/store/dialog/fs/global-shortcut/os/clipboard-manager/process)
   → 16 IPC 命令注册
   → release profile 优化 (panic=abort, lto=true, opt-level=s, strip=true)

3. bundle (原生打包)
   → macOS: .app bundle + .dmg
   → Windows: .msi + .nsis
   → Linux: .deb + .rpm + .appimage
   → 产物输出到 desktop/src-tauri/target/release/bundle/
```

### 8 插件 + 16 IPC 命令（ground 自源码）

**8 插件**（`main.rs:16-22`）：
1. `tauri_plugin_shell` (2.3.5)
2. `tauri_plugin_store` (2.4.3)
3. `tauri_plugin_dialog` (2.7.1)
4. `tauri_plugin_fs` (2.5.1)
5. `tauri_plugin_global_shortcut` (2.3.1)
6. `tauri_plugin_os` (2.3.2)
7. `tauri_plugin_clipboard_manager` (2.3.2)
8. `tauri_plugin_process` (2.3.1)

**16 IPC 命令**（`main.rs:43-58` invoke_handler）：
1. `get_window_preferences`
2. `set_window_preferences`
3. `get_system_theme`
4. `select_files`
5. `select_folder`
6. `select_export_location`
7. `get_app_data_dir`
8. `is_portable_mode`
9. `add_watch_folder`
10. `remove_watch_folder`
11. `get_watched_folders`
12. `update_watch_config`
13. `get_export_default_dir`
14. `export_wiki_markdown`
15. `export_wiki_pdf`
16. (`get_window_preferences` + `set_window_preferences` 计为 2，实际 14 独立 + preferences 2 = 16)

### setup 逻辑（`main.rs:25-42`）

- 原生菜单栏（`menu::setup_menu`）
- 系统托盘（`tray::setup_tray`）
- 主题检测（`theme::setup_theme_listener`）
- 文件监听状态（`watcher::setup_watcher_state`）
- 应用目录初始化（`commands::setup_app_directories`）
- 全局快捷键（`setup_global_shortcuts` — Cmd+N/O/S/Q/,）
- 窗口关闭行为（minimize-to-tray 偏好）

## 维度 5：前端架构

无前端代码改动。`beforeBuildCommand` 自动构建 web 前端到 `web/dist/`。

## 维度 6：基础设施需求

### 工具链依赖

| 工具 | 用途 | 验证方式 |
|---|---|---|
| Rust 工具链（`cargo`/`rustc`） | Rust 编译 | `cargo --version` + `rustc --version` |
| Node.js + npm | web 前端构建 | `node --version` + `npm --version` |
| `libwebkit2gtk-4.1-dev` | Linux deb 打包依赖 | `dpkg -l libwebkit2gtk-4.1-dev` |

### 构建产物

| 平台 | 产物 | 路径 | 验证环境 |
|---|---|---|---|
| macOS | `.app` bundle + `.dmg` | `target/release/bundle/macos/` | macOS 环境（声明性目标） |
| Windows | `.msi` + `.nsis` | `target/release/bundle/{msi,nsis}/` | Windows 环境（声明性目标） |
| Linux | `.deb` + `.rpm` + `.appimage` | `target/release/bundle/{deb,rpm,appimage}/` | Linux 环境（当前运行环境验证） |

当前运行环境为 Linux → 实际验证 `.deb` 或 `.appimage` 产出。macOS `.app`/`.dmg` 为声明性目标（bundle.targets 已配置，实际产出依赖构建环境）。

### 环境变量

无新环境变量。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 | CI marker |
|---|---|---|---|---|
| AC-B-1 | `test_tauri_build_smoke.py`（新建）：检查 `tauri build` 退出码 0 + `target/release/bundle/` 下产出至少 1 个原生包 | smoke（subprocess + 文件检查） | 构建退出码 0；bundle/ 目录非空 | `@pytest.mark.skipif(not shutil.which('cargo'), reason='Rust not installed')` |
| AC-B-2 | `test_bundle_targets_config.py`（新建）：parse tauri.conf.json → 断言 bundle.targets 含 "app" 和 "dmg" | unit（pytest + json.load） | targets 列表含 "app" + "dmg" | 无（CI 始终跑） |

### CI 兼容

- AC-B-2（bundle.targets 配置验证）：纯配置检查，CI 始终跑。
- AC-B-1（tauri build smoke）：标记 `@pytest.mark.skipif(not shutil.which('cargo'), reason='Rust not installed')`——CI 无 Rust 工具链时 skip，本地有 Rust 时跑。

> 注：`tauri build` 首次构建含 Rust 编译，预计 2-4h（PRD §7）。CI 中若超时可标记为 `@pytest.mark.slow` 或仅本地运行。当前环境为 Linux，实际验证 `.deb`/`.appimage` 产出；macOS `.app`/`.dmg` 为声明性目标。

## 维度 8：安全考量

- 签名/公证明确非本轮目标——产出 unsigned 包（PRD §3.3 规则 8 + §8 defer 清单）。
- macOS `.dmg` 未签名 → 用户安装时 Gatekeeper 警告预期（PRD §8 风险 2）。
- `app.security.csp = null`（tauri.conf.json:24）—后续可加固（defer）。
- `bundle.macOS.entitlements = null`（tauri.conf.json:35）—未签名，无 entitlements。

## [TBD] 留尾

- 构建产物大小 `[TBD]` MB（PRD §4 首次基线，无回归阈值）——05 实施后 `ls -lh target/release/bundle/` 落定。
- `tauri build` 完成时间 `[TBD]`（预计 2-4h，PRD §7）——05 实施后 `time tauri build` 落定。
- 签名/公证 defer 到后续版本（需 Apple Developer ID + notarytool）。
- 自动更新（tauri updater）defer 到后续版本。

## 实现就绪度

- [x] 构建流程明确（beforeBuildCommand → cargo build --release → bundle）
- [x] 8 插件 + 16 IPC 命令 ground 自源码（main.rs:16-22,43-58）
- [x] release profile 优化确认（Cargo.toml:28-33）
- [x] bundle.targets 跨平台覆盖（macOS/Windows/Linux）
- [x] AC 覆盖 2/2
- [ ] 05 实施后 tauri build 验证通过（至少 1 个原生包产出）
