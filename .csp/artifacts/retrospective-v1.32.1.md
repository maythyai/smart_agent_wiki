# 复盘 — v1.32.1 数据驻留 + 合规 profile（2026-10-14）

> 07 闭环校验。feat MINOR（v1.32.0 deferred 项）。前置：06-ship done（v1.32.1 tagged @b25ba83, pushed, Release）。

## 闭环校验：✅ 通过
| 链路 | 状态 | 证据 |
|---|---|---|
| PRD→Spec | ✅ | PRD-compliance-profile-v1.32.1 Approved；SPEC-F-COMPLIANCE-PROFILE 1 feat 1:1 |
| Spec→Task | ✅ | src/saw/compliance/profile.py (ComplianceProfile + loader + compliance_status) + MCP + REST + app.state 接线 |
| AC→测试 | ✅ | test_profile(5) + TestComplianceProfileRoute(1) + expected_tools 39 |
| commit→tag | ✅ | v1.32.1 @b25ba83 |
| 测试/lint | ✅ | pytest 2420/0 fail；ruff 0；cov 68.42%；tsc clean |
| 构建+Release | ✅ | wheel+sdist；https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.32.1 |

## 度量
- 1 feat done（合规 profile + on-prem 断言）
- pytest 2420 passed（+6）
- MCP 工具 38→39
- feat MINOR（additive）

## Findings（回流）
- 强制执行 + per-workspace 物理绑定 → deferred v1.39（附解除条件：workspace 物理隔离）。
- 续留：AUDIT-F-01/04/06/08 + CRITIC-F-01 + E2E-BLOCKED-01 + stale-freshness contamination。

## 教训
- 合规 profile 用 opt-in（缺 YAML → default 无约束，不 block 启动）——合规声明是"加约束"，缺声明不应破坏既有 local-first 体验。
- on-prem 断言用"显式暴露违规"而非"block 启动"——networked+on_prem 声明时 on_prem_satisfied=False 但仍启动，让运维看到违规而非卡死。强制 block 留 v1.39（多租户场景才需硬约束）。

## 下游衔接 → v1.33.0
- v1.33.0 (feat MINOR，**P1**，解 E2E-BLOCKED-01)：saw web 挂 SPA（StaticFiles + SPA fallback）+ vite proxy 配置化（env）+ 404→200 修正。入口清单：AUDIT-F-05/06/08 + E2E-BLOCKED-01 解除条件。
