# Decomposition Delta — v1.4.0（2026-09-03）

> 新一轮 02 拆解 delta。源自 PRD-platform-team-v1.4.0 + retrospective-v1.3.0.md findings G1/G3。
> platform-team track 新增 F-P-1..4；tech-debt 续 F-Z-4（G1 ruff）/F-Z-5（G3 heavy-SDK）。

## 新增 Feature

| id | name | domain | priority | complexity | depends_on | wave | blocked_by | source |
|---|---|---|---|---|---|---|---|---|
| F-P-1 | RBAC 深化（Cedar 热加载 + 权限矩阵 e2e） | platform-team | P0 | M | — | 1 | — | roadmap §v1.4.0-1 |
| F-P-2 | 团队部署（docker-compose.prod） | platform-team | P1 | S | — | 1 | — | roadmap §v1.4.0-2 |
| F-P-3 | 可观测生产闭环（saw health + receipt audit） | platform-team | P1 | M | — | 1 | — | roadmap §v1.4.0-3 |
| F-P-4 | 多工作空间隔离（schema 前缀 + 授权绑定） | platform-team | P0 | M | F-P-1 | 2 | — | roadmap §v1.4.0-4 |
| F-Z-4 | ruff 收口续（F401 import 审计 + F841 修） | tech-debt | P1 | M | — | 3 | P-1/P-3/P-4 | retro G1 |
| F-Z-5 | heavy-SDK learn 测试 importorskip | tech-debt | P2 | S | — | 1 | — | retro G3 |

## DAG delta
- 新增 subgraph WP（P1..P4）+ WZ2（Z4/Z5）。
- P1→P4（RBAC 授权 scope 是 workspace 绑定的前置）。
- Z4（ruff F401/F841）共享资源，**串行末位**（所有 src 改动后），虚线依赖 P4。
- Z5 独立（test 文件），Wave 1 并行。
- 无新环；Z4 串行不进并行组。

## Wave 重排（v1.4.0）
- **Wave 1（并行）**：F-P-1, F-P-2, F-P-3, F-Z-5（不同文件；P-1 RBAC / P-2 deploy / P-3 obs CLI / Z-5 test）
- **Wave 2**：F-P-4（migration v8 串行共享，依赖 P-1）
- **Wave 3**：F-Z-4（ruff F401/F841 串行末位，所有 src 改动后）

## 共享资源串行
- migration v8（F-P-4 workspace schema 前缀）：串行，Wave 2。
- ruff F401/F841 全库修（F-Z-4）：串行末位，Wave 3。

## 下游消费
- → 03：F-P-4 隔离方案需 ADR（schema 前缀 vs 分库——已选 schema 前缀，迁移成本低）；Cedar 热加载方案；无新 spec（platform 新域，direct task 或简 spec）。
- → 04：6 Task（P-1..4 + Z-4/5）；migration v8 + ruff 串行排 Wave。
