# UI E2E Test Report — Smart Agent Wiki @ v1.30.0 (Step 2)

> 2026-09-18. Playwright 1.63 + chromium headless. 证据: `.csp/verify/ui-test-report-5173.json` + `.csp/verify/ui-sweep/*.png`。

## 环境
- **后端 A (saw web)**: `127.0.0.1:9133` — Python FastAPI，openapi 114 paths 挂载，API 正常（`/api/auth/mode`→`{auth_mode:local,authenticated:true}`），但 `/`=404（**SPA 不由 saw web 服务**，见 AUDIT-F-05）。
- **前端 (vite dev)**: `http://localhost:5173`（IPv6）— 真实 vite.config.ts，proxy /api→:8000。**注意: :8000 被用户 vLLM (Qwen2.5-1.5B) 占用**，故 SPA 的 /api 调用全 404（环境伪影，非产品 bug）。SPA 结构正常渲染。

## 路由 sweep 结果（12 路由）

| 路由 | http | 按钮 | 死按钮(空文+启用) | main 内容 | console err | net 4xx |
|---|---|---|---|---|---|---|
| / | 200 | 1 (Search⌘K) | 0 | ✓ | 2 | 2 (api/auth/mode×2) |
| /search | 200 | 1 | 0 | ✓ | 2 | 2 |
| /graph | 200 | 0 | 0 | ✗ 空 | 0 | 0 |
| /pages | 200 | 2 (Search⌘K, 新建页面) | 0 | ✓ | 6 | 6 (auth/mode, entity-types) |
| /dashboard | 200 | 6 (Reconnect,View Graph,Search Pages,Manage Integrations,Run…) | 0 | ✓ | 8 | 8 (auth/mode, workflows) |
| /integrations | 200 | 2 (Search⌘K, **空**) | **1** | ✓ | 8 | 4 |
| /import | 200 | 3 (Select .md Files, Upload .zip) | 0 | ✓ | 2 | 2 |
| /templates | 200 | 1 | 0 | ✓ | 4 | 4 (templates) |
| /timeline | 200 | 2 (Today's Note) | 0 | ✓ | 6 | 6 (timeline) |
| /login | 200 | 1 (登录) | 0 | ✗ | 0 | 0 |
| /onboarding | 200 | 2 (Get Started→, Skip) | 0 | ✗ | 2 | 2 (onboarding/status) |
| /not-a-route-xyz | 200 | 3 (返回首页,浏览所有页面,搜索) | 0 | ✗(NotFound) | 0 | 0 |

> net 4xx 列的 `/api/*` 404 全部来自 vite proxy→vLLM 环境伪影，**非产品 finding**。结构性 finding 见下。

## Step 2 确认 findings（消费 Step 1 疑似）

- **AUDIT-F-09** [/integrations 死按钮] 空文本+启用按钮 1 个（图标按钮缺可访问名，截图 integrations.png）。`快速修复=true`。
- **AUDIT-F-10** [/graph 空状态] 0 按钮 + 无 main 内容，空数据无 CTA/引导。`快速修复=true`。
- **AUDIT-F-08** [404 返 200] /not-a-route-xyz → http 200（客户端路由不设 404 状态）。
- **AUDIT-F-05/06** [saw web 不服务 SPA + vite proxy 冲突] 实机确认：saw web :9133 `/`=404；vite proxy→vLLM:8000。

## 未验证-范围（BLOCKED）
- **数据依赖 API 行为**：因 vite proxy→vLLM 非 SAW，所有 /api 调用 404，无法验证列表加载/搜索召回/图渲染/工作流执行等数据行为。
- **解除条件**：saw web 挂 SPA（AUDIT-F-05 修复后直驱）或 vLLM 移离 :8000 或临时改 vite proxy。
- **已覆盖**：路由可达性、SPA 渲染、按钮清单、console error、network 4xx、截图、404 行为、死按钮检测。

## 证据
- JSON: `.csp/verify/ui-test-report-5173.json` + `.csp/verify/ui-test-report.json`（:9133 API-only 版）
- 截图: `.csp/verify/ui-sweep/{root,search,graph,pages,dashboard,integrations,import,templates,timeline,login,onboarding,definitely-not-a-route-xyz}.png`
- sweep 脚本: `.csp/verify/saw_e2e_sweep.py` / `saw_e2e_sweep_5173.py`
