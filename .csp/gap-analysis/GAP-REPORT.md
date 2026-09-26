# Gap Report — Smart Agent Wiki @ v1.30.0 (Step 4 单模块缺口深潜)

> 2026-09-18. 全界面自动巡检 + 逐模块 M1–M8 深潜，scoped P0 模块。**去重契约**：U1–U7+M1–M8 主跑；F2/F5 状态覆盖/a11y 引用 AUDIT-F（不重跑 Mode A/B）；Phase4 联动引用 Step2 e2e 结构 findings。findings 前缀 GAP-F-NN。

## 巡检范围（P0 高频/高危优先）
| 模块 | 路由 | 按钮数 | 状态 |
|---|---|---|---|
| Home | / | 1 | ✓ 渲染 |
| Pages | /pages | 2 (新建页面) | ✓ |
| Search | /search | 1 | ✓ |
| Graph | /graph | 0 | ✗ 空（AUDIT-F-10）|
| Dashboard | /dashboard | 6 | ✓ |
| Import | /import | 3 | ✓ |
| Templates | /templates | 1 | ✓ 疑似空 |
| Timeline | /timeline | 2 (Today's Note) | ✓ |
| Integrations | /integrations | 2 (含死按钮) | ✗ AUDIT-F-09 |

## recon M 命中（供 critic C/D 引用）
- M-一致性-01: 各页 Search⌘K 按钮一致 ✓。
- M-一致性-02: 空状态不统一（/graph 无 CTA vs /pages 有"新建页面" vs /templates 仅 1 按钮）→ GAP-F-01。

## GAP-FINDINGS
| ID | 模块 | 严重度 | 缺口/增强 | 证据 | 引用 |
|---|---|---|---|---|---|
| GAP-F-01 | Graph | P3 | 空状态无 CTA + 无"导入/创建页"引导；建议空态展示"Import 文档 / 新建页面"入口 + graph 预览提示 | ui-test /graph | AUDIT-F-10 |
| GAP-F-02 | Dashboard | P3 | 动作按钮当 nav 用（重复入口）；建议改为状态卡片（队列深度/最近 ingest/矛盾数/freshness）+ 告警 | ui-test /dashboard | CRITIC-F-01 |
| GAP-F-03 | Templates | P3 | 仅 1 按钮（Search⌘K），疑似无"创建模板/应用模板"主操作可见；建议显式模板列表 + apply 入口 | ui-test /templates | — |
| GAP-F-04 | Integrations | P2 | 死按钮（图标无可访问名）+ 平台列表空状态未验证（API BLOCKED）；建议补 aria-label + 平台连接引导 | ui-test /integrations | AUDIT-F-09 |
| GAP-F-05 | Pages | P3 | "新建页面" ✓ 但无批量操作/搜索过滤可见；建议列表内搜索 + 批量标签 | ui-test /pages | — |
| GAP-F-06 | Import | P3 | 2 上传按钮（.md/.zip）但未见拖拽区/进度反馈（数据依赖未验证）；建议 dropzone + ingest job 进度（接 /api/ingest/{job_id}/status） | ui-test /import | — |
| GAP-F-07 | Timeline | P3 | "Today's Note" ✓ 但无日期导航/空态；建议日历条 + 空态引导 | ui-test /timeline | — |
| GAP-F-08 | 全局 | P2 | saw web 不服务 SPA（根本缺口）——所有 UI 增强依赖此先修 | AUDIT-F-05 | — |

## 缺口增强目录（能加什么）
1. **UnifiedEmptyState 组件**：统一空状态模式（图标+说明+CTA），解 GAP-F-01/03/05/07。
2. **Dashboard 状态卡**：接 /api/dashboard/stats + /api/v1/workflows + /api/v1/contradictions，展示队列/工作流/矛盾/freshness 实时（GAP-F-02）。
3. **saw web SPA 挂载**：app.py 加 StaticFiles(web/dist) + SPA fallback（GAP-F-08，解 E2E-BLOCKED-01）。
4. **Import dropzone + job 进度**：接 /api/ingest/{job_id}/status（GAP-F-06）。
5. **Templates 显式列表+apply**：接 /api/templates（GAP-F-03）。

## 未验证-范围（CROSS-MODULE-UI）
- 非聚变模块未逐模块深潜：ConnectorSettings/Onboarding/Login/NotFound/Page(编辑器)——数据依赖 + 预算。Onboarding/Login 结构已 sweep（ui-test-report），但 M 级细节未过。
- 数据依赖行为（列表加载/搜索/图渲染/工作流）：BLOCKED（E2E-BLOCKED-01）。
