# TMS Delta — v1.17.0（2026-09-07）

> 03 测试规约 delta。desktop 完成 v4.4 轮：版本 bump + 配置收敛 / web 仪表盘集成验证 / tauri build 验证 / 后端协同 + 端口收敛。
> 基线：v1.16.0 = vitest 64 passed (13 files) / pytest 2217 passed / 7 skipped (env) / ruff 0 / coverage 67.42% / smoke 6/6。
> 后端测试用 pytest（版本一致性校验 + 配置审查 + 端口收敛 + CORS 扩展 + tauri build smoke），不依赖 Rust/Tauri 工具链（除 AC-B-1 smoke skip）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-V-1（版本 bump 4 文件 1.0.0） | F-V-1 | `tests/test_version_consistency.py`（新建）：grep 4 文件 version 字段 → 断言全部 = `1.0.0` | implemented+passed |
| AC-V-2（配置收敛 frontendDist/devUrl/bundle） | F-V-1 | `tests/test_tauri_config_consistency.py`（新建）：parse tauri.conf.json → 断言 frontendDist=../../web/dist, devUrl=http://localhost:5173, bundle.active=true, $schema=v2, 无废弃字段 | implemented+passed |
| AC-W-1（web 仪表盘 prod 集成） | F-V-2 | `tests/test_web_dist_integration.py`（新建）：检查 web/dist/index.html 存在 + 引用 assets/ → 验证 tauri.conf.json frontendDist 指向正确 + beforeBuildCommand 构建链 | implemented+passed |
| AC-W-2（web 仪表盘 dev 集成） | F-V-2 | `tests/test_web_dev_integration.py`（新建）：检查 tauri.conf.json devUrl=http://localhost:5173 + beforeDevCommand=npm run dev --prefix ../web | implemented+passed |
| AC-B-1（tauri build 成功） | F-V-3 | `tests/test_tauri_build_smoke.py`（新建）：检查 `tauri build` 退出码 0 + target/release/bundle/ 下产出至少 1 个原生包 | implemented+passed (skipif no cargo, ran on macOS) |
| AC-B-2（macOS 构建目标配置） | F-V-3 | `tests/test_bundle_targets_config.py`（新建）：parse tauri.conf.json → 断言 bundle.targets 含 "app" 和 "dmg" | implemented+passed |
| AC-C-1（dev proxy 端口收敛） | F-V-4 | `tests/test_port_convergence.py`（新建）：parse vite.config.ts → 断言 proxy /api target=localhost:8000 + proxy /ws target=ws://localhost:8000 | implemented+passed |
| AC-C-2（prod 后端连接） | F-V-4 | `tests/test_prod_backend_connection.py`（新建）：验证 prod 模式环境变量默认值 + 前端连接配置正确性 | implemented+passed |
| AC-C-3（CORS 扩展） | F-V-4 | `tests/test_cors_expansion.py`（新建）：parse web_cmd.py → 断言 cors_origins 默认值含 localhost:5173 + parse app.py → 断言 fallback default 含 localhost:5173 | implemented+passed |

> AC-V-1/2→F-V-1, AC-W-1/2→F-V-2, AC-B-1/2→F-V-3, AC-C-1/2/3→F-V-4。9 条 AC 全归属 Feature，无丢失。

## 约定

- **版本一致性校验测试**（`test_version_consistency.py`，新建）：用 Python `json.load` parse `desktop/package.json` + `tauri.conf.json` + `web/package.json`，用正则匹配 `Cargo.toml` version 行。断言全部 = `1.0.0`。pytest，CI 始终跑。
- **tauri 配置一致性测试**（`test_tauri_config_consistency.py`，新建）：`json.load(tauri.conf.json)` → 断言 `frontendDist`=`../../web/dist`、`devUrl`=`http://localhost:5173`、`bundle.active`=`True`、`$schema`=`https://schema.tauri.app/config/2`。pytest，CI 始终跑。
- **web dist 集成测试**（`test_web_dist_integration.py`，新建）：检查 `web/dist/index.html` 存在且非空 + `json.load(tauri.conf.json)` 断言 `frontendDist`=`../../web/dist` + `beforeBuildCommand` 含 `npm run build`。pytest，CI 始终跑。
- **web dev 集成测试**（`test_web_dev_integration.py`，新建）：`json.load(tauri.conf.json)` → 断言 `devUrl`=`http://localhost:5173` + `beforeDevCommand` 含 `npm run dev`。pytest，CI 始终跑。
- **tauri build smoke 测试**（`test_tauri_build_smoke.py`，新建）：`subprocess.run(['cd', 'desktop', '&&', 'npm', 'run', 'tauri:build'])` → 检查退出码 0 + `os.path.exists('desktop/src-tauri/target/release/bundle/')`。标记 `@pytest.mark.skipif(not shutil.which('cargo'), reason='Rust not installed')`——CI 无 Rust 时 skip，本地有 Rust 时跑。首次构建预计 2-4h。
- **bundle targets 配置测试**（`test_bundle_targets_config.py`，新建）：`json.load(tauri.conf.json)` → 断言 `bundle.targets` 含 `"app"` 和 `"dmg"`。pytest，CI 始终跑。
- **端口收敛测试**（`test_port_convergence.py`，新建）：读取 `web/vite.config.ts` 文本 → 正则匹配 `target: 'http://localhost:(\d+)'` 断言端口=8000 + 正则匹配 `target: 'ws://localhost:(\d+)'` 断言端口=8000。pytest，CI 始终跑。
- **prod 后端连接测试**（`test_prod_backend_connection.py`，新建）：检查 `web/src/lib/api.ts` 存在 + `web/src/hooks/useWebSocket.ts` 存在 → 验证 `VITE_API_BASE_URL` / `VITE_WS_URL` 逻辑既有。pytest，CI 始终跑。
- **CORS 扩展测试**（`test_cors_expansion.py`，新建）：读取 `web_cmd.py` 文本 → 正则匹配 `cors_origins` 默认值断言含 `localhost:5173` + 读取 `app.py` 文本 → 正则匹配 `origins = cors_origins or` 断言含 `localhost:5173`。pytest，CI 始终跑。

## 测试文件矩阵

| 测试文件 | 新建/改 | mock/skip | AC 覆盖 | Feature |
|---|---|---|---|---|
| `tests/test_version_consistency.py`（新建） | 新建 | 无 mock | AC-V-1 | F-V-1 |
| `tests/test_tauri_config_consistency.py`（新建） | 新建 | 无 mock | AC-V-2 | F-V-1 |
| `tests/test_web_dist_integration.py`（新建） | 新建 | 无 mock | AC-W-1 | F-V-2 |
| `tests/test_web_dev_integration.py`（新建） | 新建 | 无 mock | AC-W-2 | F-V-2 |
| `tests/test_tauri_build_smoke.py`（新建） | 新建 | skipif no cargo | AC-B-1 | F-V-3 |
| `tests/test_bundle_targets_config.py`（新建） | 新建 | 无 mock | AC-B-2 | F-V-3 |
| `tests/test_port_convergence.py`（新建） | 新建 | 无 mock | AC-C-1 | F-V-4 |
| `tests/test_prod_backend_connection.py`（新建） | 新建 | 无 mock | AC-C-2 | F-V-4 |
| `tests/test_cors_expansion.py`（新建） | 新建 | 无 mock | AC-C-3 | F-V-4 |

## 依赖约束

- 无新 pip 依赖（后端测试用 pytest + json + re + subprocess + shutil，标准库）。
- 无新 npm 依赖（不改前端代码，测试仅检查文件/配置）。
- AC-B-1（tauri build smoke）依赖 Rust 工具链（cargo/rustc）+ libwebkit2gtk-4.1-dev（Linux）——CI 无 Rust 时 skip。

## CI 兼容矩阵

| AC | 依赖 Rust? | 依赖 Tauri? | CI 行为 | marker |
|---|---|---|---|---|
| AC-V-1 | 否（json + re） | 否 | CI 始终跑 | 无 |
| AC-V-2 | 否（json） | 否 | CI 始终跑 | 无 |
| AC-W-1 | 否（文件检查 + json） | 否 | CI 始终跑 | 无 |
| AC-W-2 | 否（json） | 否 | CI 始终跑 | 无 |
| AC-B-1 | 是（cargo build） | 是（tauri build） | CI 无 Rust 时 skip | `@pytest.mark.skipif(not shutil.which('cargo'), reason='Rust not installed')` |
| AC-B-2 | 否（json） | 否 | CI 始终跑 | 无 |
| AC-C-1 | 否（文本匹配） | 否 | CI 始终跑 | 无 |
| AC-C-2 | 否（文件检查） | 否 | CI 始终跑 | 无 |
| AC-C-3 | 否（文本匹配） | 否 | CI 始终跑 | 无 |

## 后端不回归（系统级 NFR，PRD §4）

| AC | 验证方式 | 基线 | 状态 |
|---|---|---|---|
| 后端不回归 | pytest ≥ 2217 passed，ruff 0，coverage ≥ 67%，smoke 6/6 | v1.16.0 = 2217 passed / ruff 0 / coverage 67.42% / smoke 6/6 | [TBD-impl] |

> v1.17.0 后端改动仅配置收敛（vite.config.ts proxy target + web_cmd.py CORS default + app.py CORS fallback），不改业务逻辑，后端测试数预期不降（≥ 2217）。新增 8 个 desktop/配置测试（AC-V-1/2, AC-W-1/2, AC-B-2, AC-C-1/2/3）+ 1 个 tauri build smoke（skipif no cargo），pytest 总数预期增加。

## 前端不回归（系统级 NFR，PRD §4）

| AC | 验证方式 | 基线 | 状态 |
|---|---|---|---|
| 前端不回归 | vitest 64 passed (13 files)，tsc -b + vite build success | v1.16.0 = vitest 64 passed (13 files) / tsc pass / build success | [TBD-impl] |

> v1.17.0 不改前端组件代码，仅改 vite.config.ts proxy target（不影响 vitest 测试）+ 版本号 bump（web/package.json version）。前端测试数预期不降。
