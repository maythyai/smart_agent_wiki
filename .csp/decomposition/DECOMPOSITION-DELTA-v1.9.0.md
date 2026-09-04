# Decomposition Delta — v1.9.0（2026-09-04）

> 新一轮 02 拆解 delta。源自 PRD-agent-viz-v1.9.0 + retrospective-v1.8.0.md（L1-L3 deferred）。
> agent-viz track：3 Feature（F-M-1..3），workflow/agent 可见性，复用 v1.5.0 基建。

## 新增 Feature

| id | name | domain | priority | complexity | depends_on | wave | source | AC |
|---|---|---|---|---|---|---|---|---|
| F-M-1 | workflow list durable（saw workflow list） | agent-viz | P0 | S | — | 1 | roadmap §v4.3 | AC-WF-3 |
| F-M-2 | agent roster CLI（saw agents） | agent-viz | P1 | S | — | 1 | roadmap §v4.3 | AC-AG-2 |
| F-M-3 | agent roster REST（GET /api/v1/agents） | agent-viz | P1 | S | — | 1 | roadmap §v4.3 | AC-API-1 |

## 原子 Feature → Spec 映射（03 1:1）
- F-M-1 → SPEC-F-M-1（workflow list）
- F-M-2 → SPEC-F-M-2（agents CLI）
- F-M-3 → SPEC-F-M-3（agents REST）
> 3 原子 Feature = 3 Spec。

## DAG delta
- F-M-1 / F-M-2 / F-M-3 互相独立（F-M-2/F-M-3 共享 build_default_agents 数据源但不同 surface）。
- 无新环；无依赖。

## Wave 重排（v1.9.0）
- **Wave 1（全并行）**：F-M-1（workflow_cmd 加 list）/ F-M-2（agents_cmd.py）/ F-M-3（collaborate router 加 /agents）

## 共享资源串行
- workflow_cmd.py（F-M-1 加 list 子命令到 v1.5.0 既有文件）：独立改，不并行 split。
- build_default_agents（F-M-2/F-M-3 共用数据源）：只读，不冲突。

## NFR delta
- **兼容**：F-M-1 list 查 workflow_executions 表（v4），无 schema 变更。
- **鉴权**：F-M-3 GET /api/v1/agents 用 auth_dep（authenticated 只读）。
- **可测**：F-M-1 用 in-memory DB + seed workflow_executions 行；F-M-2/F-M-3 用 build_default_agents 静态 roster。

## 下游消费
- → 03：无 ADR（复用基建）；3 Spec 1:1。
- → 04：~3 Task；全 Wave 1。
