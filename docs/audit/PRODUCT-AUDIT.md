# Product Audit (聚合) — Smart Agent Wiki @ v1.30.0 (Step 5)

> 2026-09-18. 聚合 Step 1–4 全部 findings（按前缀路由去重）。AUDIT-F(10) / CRITIC-F(4) / GAP-F(8) / BLOCKED(1)。三前缀不重叠，按主跑归属引用。

## 总 findings 清单（按严重度）

### P0（1）
- **AUDIT-F-02** [Step1] test_all_tools_registered 失败（MCP 工具 34≠35）。`快速修复=true`→04/05/06 PATCH v1.30.1。

### P1（2）
- **AUDIT-F-01** [Step1] god-files 膨胀（app.py 755/engine.py 631/compiler.py 663 等 >600 行）。
- **AUDIT-F-03** [Step1] wiki 索引对坏 YAML 不韧（单页致整库索引失败）。

### P2（4）
- **AUDIT-F-04** [Step1] coverage 68.42% 未达 v1.29 宣称 70%。
- **AUDIT-F-05** [Step2] saw web 不服务 SPA（宣称-实现不符，解 E2E gate）。
- **AUDIT-F-06** [Step2] vite proxy 硬编 :8000 与 vLLM 冲突。
- **AUDIT-F-09** [Step2] /integrations 死按钮（图标无可访问名）。`快速修复=true`。
- **CRITIC-F-01** [Step3] Dashboard 按钮与 nav 入口重复。
- **GAP-F-08** [Step4] saw web SPA 挂载（=AUDIT-F-05 重复表述，去重→合并 AUDIT-F-05）。

### P3（3 + critic/gap）
- **AUDIT-F-07** [/integrations 无 nav] `快速修复=true` / **AUDIT-F-08** [404→200] / **AUDIT-F-10** [/graph 空态] `快速修复=true`。
- **CRITIC-F-02/03/04** / **GAP-F-01/03/05/06/07**（空状态/列表/导航一致性）。

### BLOCKED（1）
- **E2E-BLOCKED-01** [Step2] 数据依赖 API 行为 E2E 未验证（vite proxy→vLLM 非 SAW）。解除：saw web 挂 SPA（AUDIT-F-05 修）或 vLLM 移离 :8000。

## 跨前缀去重
- GAP-F-08 ≡ AUDIT-F-05（saw web SPA）→ 合并为 AUDIT-F-05，GAP-F-08 标 duplicate-of:AUDIT-F-05。
- CRITIC-F-03 引用 AUDIT-F-07（不重复 finding 体）。
- CRITIC-F-04 引用 GAP-F-01（空状态一致性）。

## 产物路径
| 步 | 产物 |
|---|---|
| 1 | `.csp/audit/AUDIT-FINDINGS-v1.30.0.json` / `AUDIT-VERDICT-v1.30.0.md` / `coverage.json` |
| 2 | `.csp/verify/ui-test-report.md` + `ui-test-report-5173.json` + `ui-sweep/*.png` |
| 3 | `.csp/critic/PRODUCT-CRITIC-REPORT.md` |
| 4 | `.csp/gap-analysis/GAP-REPORT.md` |
| 5 | `docs/audit/PRODUCT-AUDIT.md`（本文件）+ `docs/analysis/AUDIT-TO-ROADMAP.md` |

## 范围声明（诚实，未审显式列出）
- Mode A 真实用户可用性：BLOCKED。
- 数据依赖 E2E（列表/搜索/图/工作流）：BLOCKED（E2E-BLOCKED-01）。
- 非 P0 模块逐模块 M 深潜（ConnectorSettings/Onboarding/Login/NotFound/Page 编辑器）：未审-预算。
- mutation/fuzz/property 测试：未跑（基建型）。
- 安全重审：未本轮（v1.19.0 AUDIT-F-08 已 confirmed-secure）。
