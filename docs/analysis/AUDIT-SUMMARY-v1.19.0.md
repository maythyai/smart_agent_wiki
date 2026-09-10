---
id: AUDIT-SUMMARY-v1.19.0
project: smart-agent-wiki
milestone: v1.19.0
last_updated: 2026-09-09
mode: heuristic-review
see_also: .csp/audit/AUDIT-VERDICT-v1.19.0.md | .csp/audit/AUDIT-FINDINGS-v1.19.0.json
---

# 审计摘要 — Smart Agent Wiki @ v1.19.0

> 人类可读摘要，链回全文 `.csp/audit/AUDIT-VERDICT-v1.19.0.md`。

## 裁决：放行（production-ready）

**一句话**：Critical/High=0；v1.19.0 已修 P0（agents activity 路由）+ T4 解耦 + S4 拆分；安全基线达标；gate 全绿（2329 pass / ruff 0 / cov 67.76% / vitest 64）。剩余全为 Low/Medium gate 项或已 roadmap 技术债，非阻断。

## 本周期已修（fixed-in-v1.19.0）
- **AUDIT-F-01**（Critical→fixed）：`saw agents activity` 从未真正路由（v1.15.0 回归，callback 拦截子命令）。
- **AUDIT-F-02**（Medium→fixed）：CLI→web 单例耦合 → 移至 collaborate 模块。
- **AUDIT-F-03**（Low→fixed）：engine.py god-file 881→635（semantic mixin 拆分，逻辑不变）。

## 安全基线（AUDIT-F-08，实证达标）
- SQL：参数化占位符（`placeholders="?,?,?"`+`tuple()` 绑定，非注入）。
- 无硬编码密钥 / 无 shell=True 命令注入 / 无 bare-except 静默吞错。
- 生产 print()=0（仅 tutorial/demo 模块）。
- RBAC + 限流 + 审计日志 + Ed25519 receipt 已就位。

## 待办（gate 性质，非阻断）
| ID | 严重度 | 项 | 归属 |
|---|---|---|---|
| AUDIT-F-04 | Medium | coverage 67.76%→70%（补 CLI 功能测试） | v1.20.0 技术债 batch |
| AUDIT-F-05 | Low | activity 持久化 | [TBD-PRD]（rule 6） |
| AUDIT-F-06 | Low | banner SPEC drift | v1.21.0+ |
| AUDIT-F-07 | Low | desktop 签名/vLLM/Playwright | [TBD-infra] |

## 范围声明（诚实）
聚焦审计（G 安全 + F 代码审查 + H 性能 + I 可观测/文档 drift + 前序 W/S/T/U/V 合成）。D 前端深度 / E 测试深度矩阵 / 实跑四层联动 / mutation/fuzz/property 标 `未验证-范围`——不糊"全面通过"。完整审计需后续专项（Mode A 用户测试 + 基建型测试 + 全 PMS AC 矩阵）。

## 结论
v1.19.0 达项目企业生产标准，可上线（已发布）。本审计不改代码/不发版（审计 role §红线）；findings 已带版本 bump 建议回流 roadmap，修复归 05/06。
