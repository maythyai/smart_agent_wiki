---
id: PRD-saw-web-spa-v1.33.0
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-15
status: approved
roadmap_ref: ROADMAP
target_version: v1.33.0
type: feature
see_also: .csp/audit/AUDIT-FINDINGS-v1.30.0.json (AUDIT-F-05/06/08) | .csp/verify/ui-test-report.md (E2E-BLOCKED-01)
---

# PRD — v1.33.0 saw web 挂 SPA + proxy 配置化 + 404 (feat MINOR, P1)

## 四读前置（已执行）
1. **① 规范**: `.csp/agent-conventions/` 缺，用 `prompts/` 等价物（prevention-norms.md / e2e-deep-audit.md / version-management.md / 06-verify-ship.md）。05 遵 G-01~G-08（无 spec 不写码 / 证据先于断言 / 动态门控禁 not-run）。
2. **② findings 折入**: AUDIT-F-05（saw web 不挂 SPA，**本版核心**）/ AUDIT-F-06（vite proxy 硬编 :8000）/ AUDIT-F-08（客户端 404→200）→ 入口清单作验收项。E2E-BLOCKED-01（数据依赖 E2E）解除条件=v1.33 saw web 挂 SPA → **本版解除**。
3. **③ 对账**: lifecycle `released-v1.32.1 / next_cycle v1.33.0` = ROADMAP v1.32.1 shipped / v1.33.0 planned。无漂移。
4. **④ BLOCKED**: E2E-BLOCKED-01 解除条件满足（本版挂 SPA）→ 并入入口作验收。

## 背景
AUDIT-F-05（v1.30.0 审计 P2）：`saw web`（create_app_from_config）不挂 SPA——app.py 无 StaticFiles/mount/index.html，`/`=404。用户跑 `saw web` 看不到 UI，须另跑 `npm run dev` 或 desktop。README 宣称 `saw web → UI` 与实现不符。这同时是 E2E-BLOCKED-01 的根因（vite proxy→:8000=vLLM 非 SAW，数据 E2E 不可跑）。

## 目标
`saw web` 单命令即服务 API + SPA（web/dist）→ 用户/CI/E2E 不需另起 vite dev。解 E2E-BLOCKED-01。

## 功能清单
1. **saw web 挂 SPA**（AUDIT-F-05）：app.py mount `web/dist` 静态 + SPA fallback（非 `/api/*` 且非静态资源 → 返回 index.html，HTTP 200 SPA 模式）。
2. **vite proxy env-config**（AUDIT-F-06）：vite.config.ts proxy target 走 `VITE_API_TARGET` env（默认 :8000），dev 可指向任意 saw web 端口。
3. **NotFound noindex**（AUDIT-F-08）：NotFound 组件加 `<meta name="robots" content="noindex">`（SPA 404→200 是标准模式，noindex 防索引；server 仍返 200 因 SPA 路由客户端解析）。
4. **Playwright smoke**（解 E2E-BLOCKED-01）：E2E 测试 `saw web` 服务 SPA（GET / → 200 + root div）+ /api/auth/mode 200（数据 E2E gate 证据）。

## Given-When-Then 验收
- **GWT-1** (AUDIT-F-05): Given `web/dist` 已构建 + `saw web` 运行；When `GET /`；Then 200 + 含 `<div id="root">`（SPA served）。When `GET /api/v1/compliance`；Then 200 JSON（API 不被 fallback 拦截）。
- **GWT-2** (AUDIT-F-06): Given `VITE_API_TARGET=http://127.0.0.1:9133`；When `npm run dev`；Then vite proxy /api→:9133（env 覆盖默认）。
- **GWT-3** (AUDIT-F-08): Given 未知路由 `/xyz`；When SPA 渲染 NotFound；Then DOM 含 `<meta name="robots" content="noindex">`。
- **GWT-4** (E2E-BLOCKED-01 解除): Playwright smoke `saw web :9133` → GET / 200 + root div + GET /api/auth/mode 200。数据 E2E gate 绿。

## 成功指标
- pytest 0 fail / ruff 0 / tsc clean / vitest pass。
- Playwright smoke pass（saw web 服务 SPA + API）。
- 双闸门 exit 0（version_integrity + findings_closure，AUDIT-F-05/06/08 closed 带验证）。

## 非目标
- 全量数据依赖 E2E（列表/搜索/图渲染）：smoke 证 gate 可达，全量留后续。
- desktop 签名/跨平台（V1/V2）：留 v1.33.1。

## 风险
- SPA fallback 拦截 /api：须 fallback 只对非 /api 路径（catch-all 排除 /api 前缀）。
- web/dist 未构建时 `/` 仍 404：fallback 检测 dist/index.html 存在，不存在则不挂（graceful）。
