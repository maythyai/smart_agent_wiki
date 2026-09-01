# Task Breakdown Summary — 供 05 实施消费

## 项目概览
- 上游：20 Spec（1:1 decomposition 20 Feature），5 PMS 模块
- Task：20（1:1 Spec，S×8 / M×12），3 Wave，DAG 无环
- 关键路径：T-F-A-1-1 → T-F-A-2-1 → T-F-A-5-1 → T-F-A-6-1 → T-F-E-3-1
- 估时：S/M 粒度，人日 [TBD]（无团队速率，见 assumptions）

## Task 类型分派矩阵
| 类型 | Task | 推荐分派 |
|---|---|---|
| backend-cli | T-F-A-1-1 | 后端 |
| test | T-F-A-2/3/4/5-1 | QA/后端 |
| infra-ci | T-F-A-6-1, T-F-E-1/2/3-1 | DevOps |
| infra-script | T-F-B-1-1, T-F-B-2-1 | 后端 |
| doc | T-F-B-3-1 | Tech Writer |
| test-security | T-F-C-1/3/4-1 | 安全/QA |
| backend-security | T-F-C-2-1, T-F-C-5-1 | 后端安全 |
| backend | T-F-D-1/2/3-1 | 后端 |

## 拆解门控
- [x] Spec 完整性：20 Spec == 20 Feature（03 穷尽门控通过）
- [x] 每个 P0/P1 Feature Spec 有 ≥1 Task（20/20）
- [x] Task 粒度 ≤4h（S/M）
- [x] DAG 无环（实机校验）
- [x] Task 依赖与 decomposition Feature 依赖一致
- [x] Wave 划分合理（共享 ci.yml 串行）
- [x] 每 Task acceptance 非空（指向 AC）
- [x] 不越 PMS 边界（5 模块）

## 05 实施指引
- Lead 按 `WAVE-PLAN.md` 组建子 Agent 团队；Wave 1 可 10 路并行（worktree 隔离）。
- 每 Task 一个 commit；完成后续写 commit + 追溯矩阵。
- 复用优先：棕地 hardening，多数 Task 在既有文件加 delta，不重造（CMS 标"复用"）。
- 共享文件 ci.yml 串行（T-F-A-6-1→T-F-E-2-1→T-F-E-3-1），禁并行写。

## assumptions / [TBD]
- 估时无团队速率 → S/M 表达，人日 [TBD]。
- T-F-C-5-1 前端 token 互通实机核验后定补齐范围。
- T-F-E-1-1 coverage 基线数值实测后定阈值。
- T-F-A-1-1 / T-F-C-1-1 命令名 [TBD]。

## manifest 回写
- tasks 索引 item：`.csp/tasks/TASK-BREAKDOWN-SUMMARY.md`（source_type=doc, kind=feature, built）
- 单 Task 经 WBS 索引（不入 manifest，避免膨胀）
