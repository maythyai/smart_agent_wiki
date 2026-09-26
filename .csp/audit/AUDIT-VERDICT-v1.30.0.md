# 裁决报告 — Smart Agent Wiki @ v1.30.0 (Step 1 工程结构体检)

> 2026-09-18. 静态扫 + 模块化 + 联动四层测试 + Mode B 可用性启发式。Nielsen Mode A（真实用户）未跑（需 SPA 由 saw web 服务，见 AUDIT-F-05/BLOCKED）。findings: `.csp/audit/AUDIT-FINDINGS-v1.30.0.json`。

## Executive Summary
```
裁决：条件放行（有 1 P0 测试失败 + 1 P1 韧性 + 多 P2/P3）
Critical 0 / High(P0) 1 / P1 2 / P2 4 / P3 3 / BLOCKED 1
一句话依据：ruff 0、tsc clean、coverage 68.42%(gate 67 ✓)；但 test_all_tools_registered 失败(MCP 工具数 34≠35)、wiki 索引对坏 YAML 不韧、saw web 不服务 SPA(宣称-实现不符)；结构性 E2E 全路由可渲染，数据 E2E BLOCKED(环境)。
```

## 1. 模块清单（MODULE-LIST 摘要）
- Python src: 413 文件 / 81968 行（wc）。drivers/{cli,web,mcp} + engines/{ingest,query,govern,learn,collaborate,compile} + code_graph + connectors/{github,notion,logseq} + write_queue/sinks + onboarding + api/。
- Web: 121 tsx/ts 文件 / 12433 行。pages: Home/Search/Graph/Page/Pages/Dashboard/Integrations/ConnectorSettings/Import/Templates/Timeline/Onboarding/Login/NotFound。routes/router.tsx 12 路由。
- API: openapi 114 paths 挂载（/api/pages, /api/search, /api/v1/{health,workflows,connectors,...}, /api/dashboard/stats, /api/timeline, /api/onboarding 等）。
- 入口: CLI 30+ 命令 / MCP 35 工具（实际，见 AUDIT-F-02）/ Web 114 endpoints（见 `.csp/code-spec/saw/entry-points.jsonl`）。

## 2. 四层联动测试
- pytest 全量: 2398 passed / 7 skipped / **1 failed** / 0.0% → 100% pass 除 1（AUDIT-F-02）。
- coverage 68.42%（gate 67 ✓，未达 v1.29 宣称 70%，AUDIT-F-04）。
- smoke 机制: `smoke/` 目录无 pytest 测试（`pytest smoke/`→0 tests）；retrospectives 引用 "smoke 6/6" 但机制为脚本/非发现式（AUDIT-F-02 衍生）。

## 3. 可用性 Mode B 启发式（代码层）
- ✓ a11y skip-link 存在（App.tsx: "Skip to main content" sr-only focus-visible）。
- ✓ dark mode 实现（theme class）。
- ✓ breadcrumb + command palette (⌘K) + quick capture (⇧⌘N)。
- ✗ /integrations 不在 nav（AUDIT-F-07）。
- ✗ /graph 空状态无引导（AUDIT-F-10）。
- ✗ /integrations 死按钮（AUDIT-F-09）。
- ⚠ client-side 404→200（AUDIT-F-08）。

## 4. 工具链健康
| 项 | 结果 |
|---|---|
| build | web/dist 已构建（index.html+assets） |
| types | tsc --noEmit clean |
| lint | ruff check . = All passed (0) |
| tests | 2398 pass / 7 skip / **1 fail** (AUDIT-F-02) |
| coverage | 68.42% (gate 67 ✓，未达宣称 70) |
| security | 未本轮重审（v1.19.0 AUDIT-F-08 已 confirmed-secure） |

## 5. 缺口与下一步（最小互补集）
| 优先级 | 项 | finding | 类型 |
|---|---|---|---|
| P0 | MCP 工具数断言修复 | AUDIT-F-02 | 快速修复→04/05/06 PATCH |
| P1 | wiki 索引对坏 YAML 韧性 | AUDIT-F-03 | 04 task |
| P1 | god-files 拆分 | AUDIT-F-01 | 技术债 |
| P2 | saw web 挂 SPA | AUDIT-F-05 | 04 task（解 E2E-BLOCKED-01） |
| P2 | vite proxy 配置化 | AUDIT-F-06 | 04 task |
| P2 | coverage→70% 真达标 | AUDIT-F-04 | 技术债 |
| P3 | /integrations nav + 死按钮 + graph 空态 + 404 状态 | AUDIT-F-07/09/10/08 | 快速修复→04 |

## 范围声明（诚实）
- Mode A（真实用户可用性）+ 数据依赖 E2E：BLOCKED（AUDIT-F-05/BLOCKED-01），需 saw web 挂 SPA。
- mutation/fuzz/property 测试：未跑（基建型，AUDIT v1.19.0 §6 已记）。
- 前端视觉回归（Step 4 recon M 逐模块）：本轮 scoped 到 P0 模块（见 Step 4 GAP-REPORT），余列未审。
