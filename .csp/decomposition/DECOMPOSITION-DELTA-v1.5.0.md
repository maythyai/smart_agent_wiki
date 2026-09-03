# Decomposition Delta — v1.5.0（2026-09-03）

> 新一轮 02 拆解 delta。源自 PRD-intelligence-adaptation-v1.5.0（Approved）+ retrospective-v1.4.0.md findings H1/H2/H4/H5。
> intelligence-adaptation track 新增 F-I-1..4（智能新能力 CLI surface）；tech-debt 续 F-Z-6..9（H1/H2/H4/H5）。
> ground 结论：4 新能力的引擎层均**已实现**，本轮 gap = CLI surface + 小幅引擎延伸（resume）+ 债务收口。无巨石新引擎。

## 新增 Feature

| id | name | domain | priority | complexity | depends_on | wave | blocked_by | source | AC |
|---|---|---|---|---|---|---|---|---|---|
| F-I-1 | workflow CLI（run/validate/resume/status）+ INTERRUPTED 续跑 | intelligence-adaptation | P0 | M | F-I-4 | 1 | — | roadmap §v1.5.0-1 | AC-WF-1 |
| F-I-2 | Learn CLI（distill 在线 + gaps） | intelligence-adaptation | P0 | S | — | 1 | — | roadmap §v1.5.0-2 | AC-LR-1/2 |
| F-I-3 | Token bench CLI（实测节省 %） | intelligence-adaptation | P1 | S | — | 1 | — | roadmap §v1.5.0-3 | AC-TK-1 |
| F-I-4 | agent 角色一致性 lint（workflow 声明 agent ∈ 注册集） | intelligence-adaptation | P1 | S | — | 1 | — | roadmap §v1.5.0-4 | AC-AG-1 |
| F-Z-6 | ruff F841 收口（27 死赋值手修 + 启用） | tech-debt | P1 | M | — | 3 | I-1/I-4/Z-7 | retro H1 | AC-LINT-2(v1.4)续 |
| F-Z-7 | workspace 全查询路径路由（QueryEngine/IngestPipeline 注入 scope） | tech-debt | P0 | L | — | 2 | — | retro H2 | AC-WS-3 |
| F-Z-8 | Cedar policy reload CLI（`saw policy reload`） | tech-debt | P2 | S | — | 1 | — | retro H4 | AC-SEC-5续 |
| F-Z-9 | query 子模块测试 + coverage fail_under 60→65 | tech-dept | P1 | M | — | 1 | — | retro H5 | AC-COV-1 |

## 原子 Feature → Spec 映射（03 1:1）
- F-I-1 → SPEC-F-I-1（workflow CLI + resume 状态机延伸）
- F-I-2 → SPEC-F-I-2（learn CLI surface）
- F-I-3 → SPEC-F-I-3（token bench 场景）
- F-I-4 → SPEC-F-I-4（agent 角色 lint）
- F-Z-6 → SPEC-F-Z-6（F841 审计策略 + 启用）
- F-Z-7 → SPEC-F-Z-7（workspace scope 注入点清单）
- F-Z-8 → SPEC-F-Z-8（policy reload CLI）
- F-Z-9 → SPEC-F-Z-9（query 测试 + 棘轮上调）
> 8 原子 Feature = 8 Spec（穷尽门控）。F-I-1/I-4 共享 workflow 域但 AC 独立，分 Spec。

## DAG delta
- 新增 subgraph WI（I-1..I-4）+ WZ3（Z-6..Z-9）。
- I-4 → I-1（workflow lint 是 run 前校验前置；lint 复用 parser.validate + get_available_agents）。
- Z-6（F841 全库修）共享资源，**串行末位**（所有 src 改动后），虚线依赖 I-1/I-4/Z-7。
- Z-7（workspace 路由）触 QueryEngine/IngestPipeline 多 repo，**串行 Wave 2**（防并行冲突）。
- Z-9（query 测试）独立（test 文件），Wave 1 并行；coverage 棘轮上调在 Z-6 后最终核验。
- 无新环；Z-6/Z-7 串行不进并行组。

## Wave 重排（v1.5.0）
- **Wave 1（并行，不同文件）**：F-I-2（learn_cmd.py）/ F-I-3（token_cmd.py）/ F-Z-8（policy_cmd.py）/ F-I-1+F-I-4（workflow_cmd.py + workflow_executor.py resume）/ F-Z-9（tests/query/* 新测试）
- **Wave 2**：F-Z-7（workspace scope 注入——QueryEngine + repos 串行）
- **Wave 3**：F-Z-6（ruff F841 27 文件手修 + 启用——串行末位，全 src 改动后）

## 共享资源串行
- workflow_executor.py（F-I-1 resume + F-I-4 lint 校验调用）：同 Wave 1，同文件 → bundle 为一逻辑提交，不并行 split。
- QueryEngine / repos（F-Z-7 workspace scope）：串行 Wave 2。
- ruff F841 全库修（F-Z-6）：串行末位 Wave 3。

## NFR delta
- **可测性**：F-I-2 distill 在线路径 CI 无 LLM → mock LLMRouter；F-I-3 bench 须确定性（固定语料，非随机）。
- **可维护**：F-Z-6 F841 修须逐文件审（drop-assign vs delete no-op，副作用 RHS 不盲删）——沿用 v1.4.0 Z-4 F401 审计纪律。
- **安全**：F-Z-8 policy reload 须 admin-only（复用 RBAC），CLI 本地无鉴权（local-first）。
- **兼容**：F-Z-7 workspace scope 注入须 default workspace（单机向后兼容，不破坏既有无 ws 调用）。

## 下游消费
- → 03：F-I-1 resume 状态机延伸需 ADR（INTERRUPTED→resume 续跑语义）；F-Z-7 workspace scope 注入点需 ADR（注入策略：repo 层 vs engine 层）。8 Spec 1:1。
- → 04：~10 Task（I-1/I-4 bundle + I-2 + I-3 + Z-6 + Z-7 + Z-8 + Z-9 + migration 核验）；Z-7 串行 Wave 2，Z-6 串行末位 Wave 3。
