---
id: AUDIT-VERDICT-v1.19.0
project: smart-agent-wiki
milestone: v1.19.0
commit: 07b6b17
last_updated: 2026-09-09
mode: heuristic-review
see_also: .csp/audit/AUDIT-FINDINGS-v1.19.0.json | .csp/audit/MODULE-LIST-v1.19.0.md
---

# 裁决报告 — Smart Agent Wiki @ v1.19.0

## Executive Summary
```
裁决：放行（production-ready）
致命 0 / 严重 0 / 一般 2 / 提示 4 / 缺口 0（P0/P1 需求均有测试映射）
一句话依据：Critical/High=0；v1.19.0 已修 activity 路由 P0 + T4 解耦 + S4 拆分；安全基线达标；gate 全绿；剩余全为 Low/Medium gate 项（PRD/infra/risk-gated）或已 roadmap 技术债。
```

## 1. 项目目标 vs 现状对照
| 需求域 | 风险级 | 现状 | 依据 |
|---|---|---|---|
| 四层溯源（Vault→Claims→Wiki→Index） | P0 | 满足 | M1/M2 + claims_repo 锚定 page_number/line_number |
| 治理信任闭环（置信+新鲜度+矛盾+receipt） | P0 | 满足 | M3 Governor + ed25519.py |
| 多代理协作 | P0 | 满足 | M4 6 agent + workflow_executor |
| per-request workspace 隔离 | P0 | 满足 | W1/W2 审计确认（compiler.py:68 effective_workspace_id contextvar） |
| local-first + MCP agent-native | P0 | 满足 | M7 MCP 64+ tools + SSH push |
| 安全可审计 | P0 | 满足 | AUDIT-F-08（无注入/密钥/吞错；RBAC+限流+审计日志） |
| agent activity 路由 | P1 | 满足（v1.19.0 修复） | AUDIT-F-01 已 fixed |

## 2. 技术实现 vs 产品要求
实现达标。S4 已拆 engine.py（881→635，semantic mixin）；语义检索 scale-driven ANN/cosine 切换；Write Queue dispatcher 重启恢复 + DLQ 告警。偏差点：coverage 67.76% 踩线（AUDIT-F-04）。

## 3. 技术模块缺陷清单
| ID | 严重度 | 模块 | 复现/证据 | 受影响需求 | 状态 |
|---|---|---|---|---|---|
| AUDIT-F-01 | Critical→fixed | M7 CLI | `saw agents activity` 修前恒打印 roster | agent-link P1 | fixed-v1.19.0 |
| AUDIT-F-02 | Medium→fixed | M4/M7 | CLI→web import | observability | fixed-v1.19.0 |
| AUDIT-F-03 | Low→fixed | M2 | engine.py 881 行 | maintainability | fixed-v1.19.0 |
| AUDIT-F-04 | Medium | 全局 | cov 67.76%/gate 67 | test-gate | open→v1.20 |
| AUDIT-F-05 | Low | M4 | activity 不持久化 | (PRD rule 6 设计) | deferred-PRD |
| AUDIT-F-06 | Low | M7 web | banner SPEC drift | dashboard | deferred-risk |
| AUDIT-F-07 | Low | desktop/CI | 签名/vLLM/Playwright | desktop/release | deferred-infra |
| AUDIT-F-08 | — | 全局 | 安全基线确认达标 | security | confirmed-secure |

## 4. 联动测试结果
`未验证-范围`：本次未实跑四层 round-trip（需运行 web 实例 + browser + trace 截图）。结构验证（代码层）：REST→CollaborateEngine→dispatcher→Write Queue→sinks→DB→WS broadcast→UI 链路完整（app.py + workflow_executor.py + sinks/*），trace_id contextvar 贯穿（observability.py:30）。**建议补位**（需基建）：Mode A 真实用户四层联动 + Playwright E2E（U1）。

## 5. 需求可追溯缺口
P0/P1 需求均有测试映射（见 §1）。`单层-happy` 缺口：`未验证-范围`——未逐条建 R1..Rn→方法矩阵（需 PMS AC 全量映射，本聚焦审计未展开）。已知薄覆盖模块（cov 报告）：tutorial/demo_content 46%、wiki_sink 69%、connector_sink 72%（AUDIT-F-04 补位目标）。

## 6. 测试资产盲点
| 能力 | 现状 | 补位 |
|---|---|---|
| unit/integration | 有（2329） | — |
| property/fuzz/mutation | 无 | 建议基建：hypothesis/atheris/mutmut（需基建，本次只列不跑） |
| 跨层联动（四层 round-trip） | 结构完整，未实跑 | 需运行实例 + Playwright（U1） |
| chaos/canary/visual-regression | 无 | 需基建 |

## 7. 工具链健康度
| 项 | 证据 | 结论 |
|---|---|---|
| build | `pyproject.toml` + CI 已产 wheel/tar.gz（v1.19.0 release assets） | ✅ |
| types | mypy 配置在（`.mypy_cache` 存在）；`未验证-范围` 未跑全量 | 🟡 部分 |
| lint | `ruff check .` = All checks passed（0） | ✅ |
| tests | pytest 2329 pass/7 skip/0 fail | ✅ |
| security | AUDIT-F-08（无注入/密钥/命令注入/吞错）；RBAC+限流+审计 | ✅ |
| diff | manifest hub diff 0/0/0（content_hash git blob） | ✅ |

## 8. 可用性审查汇总（Mode B heuristic-review）
`未验证-范围`：本次未逐模块跑 Nielsen 10 启发式（聚焦在安全/CR/性能）。已知可用性项：U6（banner SPEC drift，Low，行为正确）→ deferred。建议补位：Mode A 真实用户测试 + a11y 扫描。

## 9. 风险与下一步（最小互补集优先）
| 优先级 | 项 | 类型 | 建议版本 |
|---|---|---|---|
| P2 | AUDIT-F-04 coverage→70%（补 CLI 功能测试） | 本次可执行 | v1.20.0 技术债 batch |
| P3 | AUDIT-F-06 banner 归位 | 需小心重构 | v1.21.0+ |
| P3 | AUDIT-F-05 activity 持久化 | 需 01-PRD 决策 | [TBD-PRD] |
| P3 | AUDIT-F-07 desktop 签名/vLLM/Playwright | 需 CI 基建 | [TBD-infra] |
| — | 补 mutation/fuzz/property | 需基建 | v1.21.0+ |

## Roadmap bump 建议
- **v1.20.0**：技术债 batch——coverage→70% + mutation/fuzz 基建起步（AUDIT-F-04）。与既有竞品借鉴候选 v1.20 合并或择一。
- AUDIT-F-05/06/07 已分别归 [TBD-PRD]/v1.21+/[TBD-infra]，不新增版本号。
- **不发版**：本审计不改代码（AUDIT-F-01/02/03 已在 v1.19.0 修；AUDIT-F-04 等走 roadmap→05）。v1.19.0 为当前 release。

## 范围声明（诚实）
本审计为**聚焦**（G/F/H/I + 前序 W/S/T/U/V 合成），非全量 9 维 × 逐模块可用性 × 实跑四层联动。D 前端深度 / E 测试深度矩阵 / 实跑联动 / mutation/fuzz 标 `未验证-范围`，不下"全面通过"不可证伪结论。完整审计需后续专项（Mode A 用户测试 + 基建型测试 + 全 PMS AC 矩阵）。
