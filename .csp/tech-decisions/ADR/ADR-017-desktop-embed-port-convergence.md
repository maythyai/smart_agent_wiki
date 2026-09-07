# ADR-017: desktop 嵌入策略 + 端口收敛

## 状态：Accepted

## 上下文

v1.17.0 desktop 完成 v4.4 轮（PRD-desktop-v1.17.0），桌面端 Tauri v2 从 0.1.0→1.0.0 版本对齐。PRD §3.4 明确要求 03 技术方案解决两个问题：

1. **desktop 与 saw 后端的协同模式**：dev 模式下 vite dev server（5173）代理 `/api` + `/ws` 到 saw 后端；prod 模式下 desktop 加载 `web/dist` 静态产物，需连接 saw 后端。PRD §3.4 规则 4 明确"prod 模式 saw 后端可独立运行（用户手动 `saw web`）或 desktop 内嵌启动（sidecar 模式）——具体实现方案留 03 技术方案"。
2. **端口收敛**：vite proxy target 为 `http://localhost:8080`（`web/vite.config.ts:18`），而 `saw web` 默认端口为 8000（`src/saw/drivers/cli/commands/web_cmd.py:25`）——端口不一致，dev 模式下 API 请求 502。

### 需求驱动

1. **dev 模式协同**：`tauri dev` 启动 vite dev server（5173），前端通过 vite proxy 访问 saw 后端 REST `/api` + WS `/ws`。当前 proxy target 8080 ≠ saw web 默认 8000 → API 请求失败。
2. **prod 模式协同**：`tauri build` 产出原生包，desktop 窗口加载 `web/dist` 静态产物，无 vite dev server 代理——前端需直连 saw 后端。
3. **CORS 扩展**：saw web 默认 CORS origins 为 `localhost:3000,127.0.0.1:3000`（`web_cmd.py:33`），desktop dev 模式使用 5173 → CORS 拒绝。
4. **WS 路径一致**：saw 后端 WS 路由挂载在 `/ws` prefix（`app.py:306`），vite proxy `/ws` 代理到后端——路径一致，仅端口需收敛。

### CMS 出处（ground 自源码 + desktop 栈）

| 事实 | file:line | 现状 |
|---|---|---|
| `desktop/package.json` version=0.1.0 | `desktop/package.json:4` | `"version": "0.1.0"` → 需 bump 1.0.0 |
| `desktop/src-tauri/tauri.conf.json` version=0.1.0 | `desktop/src-tauri/tauri.conf.json:5` | `"version": "0.1.0"` → 需 bump 1.0.0 |
| `desktop/src-tauri/Cargo.toml` version=0.1.0 | `desktop/src-tauri/Cargo.toml:3` | `version = "0.1.0"` → 需 bump 1.0.0 |
| `web/package.json` version=0.1.0 | `web/package.json:4` | `"version": "0.1.0"` → 需 bump 1.0.0 |
| `frontendDist` 指向 web/dist | `desktop/src-tauri/tauri.conf.json:11` | `"frontendDist": "../../web/dist"` → web 集成已配置 |
| `devUrl` 指向 vite dev server | `desktop/src-tauri/tauri.conf.json:10` | `"devUrl": "http://localhost:5173"` → dev 模式已配置 |
| `beforeBuildCommand` 触发 web 构建 | `desktop/src-tauri/tauri.conf.json:9` | `"beforeBuildCommand": "npm run build --prefix ../web"` → 构建链已配置 |
| `beforeDevCommand` 触发 vite dev | `desktop/src-tauri/tauri.conf.json:8` | `"beforeDevCommand": "npm run dev --prefix ../web"` → dev 构建链已配置 |
| vite proxy `/api` → 8080 | `web/vite.config.ts:18` | `target: 'http://localhost:8080'` → proxy 目标 8080（端口不一致 bug） |
| vite proxy `/ws` → 8080 | `web/vite.config.ts:21` | `target: 'ws://localhost:8080'` → WS proxy 目标 8080（端口不一致 bug） |
| saw web 默认端口 8000 | `src/saw/drivers/cli/commands/web_cmd.py:25` | `port: int = typer.Option(8000, "--port", "-p", ...)` → 端口不一致 (8080 vs 8000) |
| saw web 默认 CORS origins | `src/saw/drivers/cli/commands/web_cmd.py:33` | `cors_origins: str = typer.Option("http://localhost:3000,http://127.0.0.1:3000", ...)` → 需加 localhost:5173 |
| saw 后端 WS 路由 /ws prefix | `src/saw/drivers/web/app.py:306` | `app.include_router(integrations_ws_router, prefix="/ws", ...)` → WS 路径与 vite proxy /ws 一致 |
| saw 后端 CORS allow_origins 默认 3000 | `src/saw/drivers/web/app.py:229-230`（`create_app` 函数 `origins = cors_origins or ["http://localhost:3000", ...]`） | CORS 默认允许前端访问 REST |
| `web/dist/index.html` 构建产出存在 | `web/dist/index.html` | v1.16.0 构建产出（index.html + assets/）已就绪 |
| bundle.targets 含 macOS .app/.dmg | `desktop/src-tauri/tauri.conf.json:25` | `"targets": ["msi","nsis","dmg","app","deb","rpm","appimage"]` → 跨平台目标已配置 |
| desktop 已有 8 插件 + 16 IPC 命令 | `desktop/src-tauri/src/main.rs:16-22,43-58` | 8 plugin init + 16 invoke_handler → 完整桌面应用已搭建 |
| Cargo.lock 存在（依赖锁定） | `desktop/src-tauri/Cargo.lock` | 136688B → 依赖已锁定 |
| tauri v2 schema | `desktop/src-tauri/tauri.conf.json:2` | `"$schema": "https://schema.tauri.app/config/2"` → Tauri v2 |
| web 已集成 @tauri-apps/api | `web/package.json:11` | `"@tauri-apps/api": "^2.0.0"` → 前端可调用 desktop IPC |
| release profile 已优化 | `desktop/src-tauri/Cargo.toml:28-33` | `panic="abort", lto=true, opt-level="s", strip=true` → 构建优化已配置 |
| `create_app` cors_origins 参数 | `src/saw/drivers/web/app.py:229`（`create_app(... cors_origins: list[str] | None = None, ...)`） | CORS origins 可通过参数注入，不硬编码 |

## 决策

### 决策一：desktop 嵌入策略——选择候选 ③ Hybrid（dev proxy + prod external）

- **dev 模式**：vite dev server（5173）proxy `/api` + `/ws` → saw web 后端（端口收敛后 8000）。开发者同时运行 `tauri dev` + `saw web`。
- **prod 模式**：desktop 加载 `web/dist` 静态产物，前端直连 saw web 后端（`localhost:8000` 默认）。用户须先运行 `saw web` 再启动桌面应用。
- **sidecar 明确 defer**：desktop 内嵌 saw server（sidecar）需捆绑 Python 运行时 + saw 包（PyInstaller/pyoxidizer 产出 standalone executable），配置 Tauri sidecar feature——工程量超出 v1.17.0 "1.0 bump + 配置收敛"范围。明确 defer 到后续版本（v2.0 候选）。
- **prod 连接地址**：前端通过 `VITE_API_BASE_URL` 环境变量（既有，`api.ts:3`）配置后端地址。prod 构建时默认 `http://localhost:8000`，用户可通过 `.env` 覆盖。

### 决策二：端口收敛——vite proxy target 8080→8000

- 将 `web/vite.config.ts` proxy target 从 `http://localhost:8080` 改为 `http://localhost:8000`（`/api` proxy L18 + `/ws` proxy L21），与 `saw web` 默认端口 8000（`web_cmd.py:25`）对齐。
- 不修改 `saw web` 默认端口（8000 是 D-02 约定，`web_cmd.py:23` docstring 标注 "Per D-02: Default port 8000"），而是让 vite proxy 适配 saw web 的既有默认端口。
- 理由：`saw web` 端口 8000 是项目约定（D-02），有文档和代码注释支撑；vite proxy 8080 是无文档的随意值，应向约定收敛。

### 决策三：CORS 扩展——默认 origins 添加 localhost:5173

- 将 `web_cmd.py:33` 的 `cors_origins` 默认值从 `"http://localhost:3000,http://127.0.0.1:3000"` 改为 `"http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"`。
- 同时更新 `app.py:229`（`create_app` 函数）的 fallback default 从 `["http://localhost:3000", "http://127.0.0.1:3000"]` 改为 `["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"]`。
- 不放宽到 `0.0.0.0` 或 `*`——仅添加 dev 模式 vite dev server 端口 5173。

## 备选方案

### 决策一对比：desktop 嵌入策略

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① desktop 内嵌 saw server（sidecar，prod 单进程） | prod 用户体验最佳——一键启动桌面应用即可访问仪表盘，无需手动 `saw web`；后端生命周期与 desktop 绑定 | **需捆绑 Python 运行时 + saw 包**（PyInstaller/pyoxidizer 产出 standalone executable，~50-100MB 额外体积）；需配置 Tauri sidecar feature（`tauri.conf.json` sidecar 配置 + `tauri-plugin-shell` spawn）；需处理进程生命周期管理（启动/停止/崩溃恢复）；工程量大，超出 v1.17.0 "1.0 bump + 配置收敛"范围 | 排除：工程量超出 v1.17.0 范围，sidecar 明确 defer |
| ② desktop 代理到外部 saw server（dev proxy + prod 用户启 server） | 实现最简——dev: vite proxy 已有（仅端口收敛）；prod: 前端直连，无 sidecar 复杂度；无新依赖；与 PMS "复用既有 Tauri v2 + vite proxy" 一致 | **prod 模式用户须手动运行 `saw web`**——非 CLI 用户不友好；桌面应用依赖外部进程，若 saw web 未启动则仪表盘显示空态/错误条 | 可接受：v1.17.0 目标为 "1.0 bump + 配置收敛 + tauri build 验证"，sidecar 为后续增强；PRD §3.4 异常处理已覆盖 "saw 后端未启动 → 仪表盘显示空态/错误条" |
| ③ Hybrid（dev proxy + prod external，sidecar defer）（选） | dev: vite proxy 路径最简（仅端口收敛 8080→8000）；prod: external saw web（用户手动 `saw web`），前端直连 localhost:8000；sidecar 作为明确后续路径（v2.0 候选）；实现量最小；无新依赖；与 PRD §3.4 规则 4 + PMS "复用既有" 一致 | prod 模式用户须手动运行 `saw web`（同候选 ②）；sidecar 未实现，非 CLI 用户体验不完美 | 选：v1.17.0 最合适的方案——dev proxy 已有仅端口收敛，prod external 最简，sidecar defer 有明确路径 |

### 决策二对比：端口收敛方案

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① vite proxy target 改为 8000（选） | 向 `saw web` 既有约定（D-02: port 8000）收敛；修改量最小（vite.config.ts 2 行）；不破坏 `saw web` 默认行为；文档/代码注释一致（web_cmd.py:23 "Per D-02"） | 若开发者习惯 `saw web --port 8080`，需改为默认端口或文档说明 | 选：向约定收敛，修改量最小 |
| ② 文档约定 `saw web --port 8080` | 不改代码，仅文档 | 开发者须记住加 `--port 8080`；vite proxy 仍指向 8080；与 `saw web` 默认 8000 不一致；非收敛而是适配 | 排除：不是收敛而是 workaround，开发者体验差 |

### 决策三对比：CORS 扩展方式

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① 修改默认 cors_origins 添加 localhost:5173（选） | dev 模式 `saw web` 默认即允许 5173，开发者无需额外参数；修改量最小（web_cmd.py 1 行 + app.py 1 行 fallback） | 默认 origins 列表增长；若其他前端框架使用不同端口仍需手动加 | 选：dev 模式 vite dev server 端口 5173 是 tauri.conf.json devUrl 固定值，添加到默认列表合理 |
| ② 文档约定 `saw web --cors http://localhost:5173` | 不改代码 | 开发者须记住加 `--cors` 参数；CORS 默认值不含 5173 → 每次都需手动 | 排除：不是收敛而是 workaround，开发者体验差 |

## 理由

1. **PRD 对齐**：PRD §3.4 规则 4 明确"prod 模式 saw 后端可独立运行或 sidecar——具体 HOW 留 03"。候选 ③ 给出了明确决策：dev proxy + prod external，sidecar defer。PRD §3.4 规则 2 明确"端口不一致需收敛"，候选 ①（proxy→8000）是修改量最小的收敛方案。
2. **PMS 约束**：PMS-desktop 明确"复用既有 Tauri v2 + vite proxy + saw 后端 WS/CORS，不引入新库"。候选 ① sidecar 需新增打包工具链（PyInstaller/pyoxidizer），违反 PMS 约束。候选 ③ 无新依赖。
3. **修改量最小**：端口收敛仅改 `vite.config.ts` 2 行（L18 + L21 proxy target 8080→8000）；CORS 扩展仅改 `web_cmd.py` 1 行（L33 默认值）+ `app.py` 1 行（L229 fallback default）。总改动 4 行，配置收敛量最小。
4. **向约定收敛**：`saw web` 端口 8000 是 D-02 约定（`web_cmd.py:23` docstring "Per D-02: Default port 8000"），有文档和代码注释支撑。vite proxy 8080 是无文档的随意值，应向约定收敛而非反向。
5. **sidecar defer 合理**：sidecar 需捆绑 Python 运行时（~30-50MB）+ saw 包 + 配置 Tauri sidecar feature + 进程生命周期管理——这是一个独立的工程任务，不适合在 "1.0 bump + 配置收敛" 轮次中完成。明确 defer 到 v2.0 候选。
6. **prod 降级已覆盖**：PRD §3.4 异常处理已覆盖"saw 后端未启动 → 前端 API 请求失败，仪表盘显示空态/错误条"。v1.16.0 已有 WS 断连降级 polling 逻辑（ADR-016），prod 模式 saw web 未启动时仪表盘会优雅降级。
7. **WS 路径无需修改**：saw 后端 WS 路由 `/ws` prefix（`app.py:306`）与 vite proxy `/ws` 路径一致，仅端口需收敛，路径无变更。

## 后果

### 正面
- dev 模式协同打通：`tauri dev` → vite 5173 → proxy /api + /ws → saw web 8000，开发者只需同时运行 `tauri dev` + `saw web`。
- prod 模式明确：desktop 加载 web/dist，前端直连 localhost:8000（`VITE_API_BASE_URL` 配置），用户须先运行 `saw web`。
- CORS 扩展：dev 模式 `saw web` 默认允许 localhost:5173，开发者无需额外 `--cors` 参数。
- 端口收敛：vite proxy 8080→8000，与 `saw web` 默认端口对齐，消除端口不一致 bug。
- sidecar defer 有明确路径：v2.0 候选实现 sidecar（PyInstaller + Tauri sidecar feature），prod 用户体验升级。

### 负面
- prod 模式用户须手动运行 `saw web`——非 CLI 用户不友好。缓解：v1.16.0 已有降级逻辑（仪表盘空态/错误条），且桌面应用窗口仍可打开，仅数据不可用。
- sidecar 未实现——桌面应用不自包含后端。缓解：明确 defer，v2.0 候选。

### 风险
- prod 模式 saw web 未启动 → 仪表盘空态/错误条（PRD §3.4 异常处理已覆盖，v1.16.0 降级逻辑已有）。
- CORS 扩展后默认 origins 列表增长（3 条），不影响安全性（仅 localhost dev 端口）。
- `VITE_API_BASE_URL` prod 构建时需正确设置（若用户部署到非 localhost 环境需覆盖）。

## 关联 Feature

- F-V-1（desktop 1.0 版本 bump + 配置收敛——本 ADR 决策：4 文件 0.1.0→1.0.0 + tauri.conf.json 配置一致性审查）
- F-V-2（web 仪表盘集成验证——本 ADR 决策：frontendDist=../../web/dist 已 wired，验证为主不改动配置）
- F-V-3（tauri build 验证——本 ADR 决策：beforeBuildCommand 构建链已配置，验证产出原生包）
- F-V-4（后端协同 + 端口收敛——本 ADR 决策：dev proxy 8080→8000 收敛 + CORS 添加 localhost:5173 + prod external saw web + sidecar defer）

## 关联 ADR

- ADR-001（Python 3.11 + Typer + FastAPI，Accepted）——saw web 后端框架复用。
- ADR-016（realtime 仪表盘更新策略 polling + WS 双源，Accepted）——v1.16.0 仪表盘 WS/polling 降级逻辑复用，prod 模式 saw web 未启动时降级生效。

## [TBD] 留尾

- sidecar 实现细节（PyInstaller standalone executable + Tauri sidecar feature + 进程生命周期管理）——defer 到 v2.0 候选。
- prod 模式 `VITE_API_BASE_URL` 用户配置 UI（desktop 偏好设置中配置后端地址）——defer 到后续版本。
- prod 模式自动检测 saw web 是否运行（desktop 启动时 health check）——defer 到后续版本。
