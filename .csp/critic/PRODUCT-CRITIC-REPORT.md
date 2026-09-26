# Product Critic Report — Smart Agent Wiki @ v1.30.0 (Step 3)

> 2026-09-18. 七镜头 A–G + 跨模块聚合。**去重契约**：F/G 可用性违例引用 AUDIT-F（Step1/2，不重跑 Nielsen Mode B）；B IA 引用 Step2 结构 findings；C/D 视觉交互一致性引用 Step4 gap recon M（Step4 已跑 P0 模块，余未审）。本流程专注重复/散乱/定位挑刺（audit 不做）。

## 镜头 A — 定位/重复/散乱（主跑）
- **CRITIC-F-01** [P2 重复/散乱] Dashboard 动作按钮与专用页入口重复。`/dashboard` 6 按钮含 "View Graph"→/graph、"Search Pages"→/pages、"Manage Integrations"→/integrations——与顶部 nav 重复入口。证据: ui-test-report-5173.json /dashboard buttons_sample。建议: dashboard 聚焦"状态/告警/最近活动"而非 nav 替代。
- **CRITIC-F-02** [P3 散乱] 顶部 nav 7 项（pages/search/graph/dashboard/import/templates/timeline）但 router 有 12 路由——/integrations、/onboarding、/page/:slug 无 nav（AUDIT-F-07）。IA 散乱：dashboard 被当二级 hub 用，但 nav 里已有 dashboard。

## 镜头 B — IA（引用 Step2）
- **CRITIC-F-03** [P3 IA] 引用 AUDIT-F-07：/integrations 全功能页无 nav 入口（须手输 URL）。跨模块：integrations ↔ connector-settings 双层路由（/integrations/:platform + /integrations/:platform/settings），IA 较深但入口缺失。

## 镜头 C/D — 视觉交互一致性（引用 Step4 recon M）
- 引用 Step4 GAP-REPORT recon M 命中（本轮 Step4 scoped P0；C/D 批次聚合：各页均有 Search⌘K 一致 ✓；但按钮风格/空状态一致性散——/graph 空无 CTA vs /pages 有"新建页面"，空状态模式不统一，见 GAP-F-01）。

## 镜头 E — 错误/反馈（引用 AUDIT-F）
- 引用 AUDIT-F-03（wiki 索引失败用户不可见——后端日志错误未 surfaced 到 UI）。
- 引用 AUDIT-F-09（/integrations 死按钮，无反馈）。

## 镜头 F/G — 可用性违例（引用 AUDIT-F，不重跑 Nielsen）
- 引用 AUDIT-F-08（404→200，影响可发现性/监控）。
- 引用 AUDIT-F-09（图标按钮无可访问名，a11y 违反 WCAG 4.1.2）。
- 引用 AUDIT-F-10（/graph 空状态违反 Nielsen"系统状态可见性"——用户不知为何空）。

## 跨模块聚合（CROSS-MODULE）
- **重复入口**：dashboard 按钮 ↔ nav（CRITIC-F-01）→ 建议定 dashboard 为"概览+告警"，nav 为"导航"，去 dashboard 的 page-jump 按钮。
- **空状态不统一**：/graph 空（AUDIT-F-10）vs /pages 有 CTA vs /templates 1 按钮（疑似空无 CTA，GAP-F-03）→ 建议 UnifiedEmptyState 组件。
- **API 服务于 SPA 的根本断点**（AUDIT-F-05）横切所有模块：saw web 不挂 SPA → 所有 UI 验证须 vite/desktop → E2E gate 受阻。

## CRITIC-FINDINGS 清单
| ID | 镜头 | 严重度 | 标题 | 引用 |
|---|---|---|---|---|
| CRITIC-F-01 | A 重复 | P2 | Dashboard 按钮与 nav 入口重复 | ui-test-report /dashboard |
| CRITIC-F-02 | A 散乱 | P3 | nav(7) vs router(12) 不一致，dashboard 当二级 hub | router.tsx/App.tsx |
| CRITIC-F-03 | B IA | P3 | /integrations 无 nav 入口 | AUDIT-F-07 |
| CRITIC-F-04 | C/D 一致性 | P3 | 空状态模式不统一（graph/templates vs pages） | GAP-F-01/03 |

## 未验证-范围
- 镜头 C/D 逐模块视觉细节（间距/配色/组件一致性）：本轮仅 P0 批次聚合，非 P0 模块（ConnectorSettings/Onboarding/Login/NotFound）未逐模块过 M。
- Mode A 真实用户可用性：BLOCKED（AUDIT-F-05）。
