---
id: INTEGRATION-NECESSITY-2026-10-20
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-20
status: active
generated_by: roadmap Phase 2.5 集成必要性审视
see_also: docs/strategy/ROADMAP.md | docs/analysis/COMPETITIVE-REFERENCE.md
---

# 版本功能集成必要性审视表 — 2026-10-20

> Phase 2.5 self-critique gate。以**精简优先**（砍不是留）为默认姿态。已交付 v1.30.1–v1.34.0（8 版）不在审视范围。审视对象 = ROADMAP §2.6 中 v1.34.1–v2.2.0 共 ~18 个 planned 版本的功能。

## 审视维度
1. 定位契合度 2. 用户场景必要性 3. 与现有能力重叠 4. 集成成本vs价值 5. 依赖可行性 6. 攒批合理性 7. 核心场景聚焦度

## 审视裁决汇总
- **纳入** 8 版（v1.34.1–v2.0.0，其中 4 版由原 8 版合并而来）
- **降级** 9 版/功能 → v2.0+ 或 v3.0（远期生态/平台，非当前核心场景）
- **剔除** 0（无完全剔除，均降级到远期）
- **合并** 8→4（原 v1.36+v1.45 合并，v1.43+v1.44 合并，v1.39+v1.40 合并，v1.47 obs→v1.39 合并）

## 审视表

### 纳入（8 版，净版）

| 原版本 | 功能 | 裁决 | 依据 |
|---|---|---|---|
| v1.34.1 | AUDIT-F-04 coverage 70% + AUDIT-F-01 god-files + stale-freshness contamination + CRITIC-F-01 Dashboard 修复(合并) | 纳入+合并 | ① core-trust 锚点 ② 既有 findings 须闭合 ③ 无重叠 ④ 低成本(测试+重构) ⑤ 无外部依赖 ⑥ 同 core-trust 模块可合并 ⑦ 核心质量场景 |
| v1.35 | Structured Context API v1（统一 vector+graph+ontology+state） | 纳入 | ① ★品类定位锚点 ② DEV agent 场景必需 ③ 无重叠(新统一 API) ④ 中成本但高价值 ⑤ 依赖 v1.34 ⑥ 独立版本 ⑦ 核心(agent 可信 context) |
| v1.36+v1.45 | Incremental Graph + Logical-Symbolic Reasoning + Deep Research v2（**合并**） | 纳入+合并 | ① intelligence 锚点 ② 多跳推理+深度研究是核心 ③ 与 v1.10-v1.14 semantic 有部分重叠但增量图+逻辑推理是新 ④ 中成本 ⑤ 依赖 v1.35 ⑥ **同 intelligence track 可合并**——incremental graph + reasoning + deep research 都是"更智能的检索" ⑦ 核心 |
| v1.43+v1.44 | Governed Code Intelligence + Token Optimizer 产品化（**合并**） | 纳入+合并 | ① core-trust+intelligence ② DEV 用户核心痛点(cost+code gov) ③ 与 v1.20 skills 有部分重叠但 governed(溯源+治理)是新 ④ 低成本(既有基建产品化) ⑤ 依赖 v1.36 ⑥ **同 DEV 用户价值可合并**——code intelligence + token cost 都是 DEV 场景 ⑦ 核心(成本+治理) |
| v1.39+v1.40 | RBAC深化 + SSO/OIDC + Plugin SDK v1 stable（**合并**，marketplace 降级） | 纳入+合并 | ① platform 锚点 ② OPS to-B 场景必需 ③ 与 v1.4 RBAC 有深化但 SSO/OIDC 是新 ④ 中成本 ⑤ 依赖 v1.38 ⑥ **同 platform 模块可合并**——RBAC + SSO + plugin SDK 都是平台基建 ⑦ to-B 核心 |
| v1.47(obs部分) | Observability v2 Langfuse-grade + W3C traceparent（**合并入 v1.39**） | 纳入+合并 | ① platform ② OPS 场景 ③ 与 v1.24 langfuse 深化 ④ 低成本 ⑤ 无外部依赖 ⑥ 同 platform/ops 模块 ⑦ 核心(可观测) |
| v1.49 | Pre-v2.0 硬化 + coverage 75% + property/fuzz 基建 | 纳入 | ① core-trust ② 质量门 ③ 无重叠 ④ 低成本 ⑤ 无外部依赖 ⑥ 独立 ⑦ 核心(发布前硬化) |
| v1.50 | v2.0 RC + Context API freeze | 纳入 | ① 品类定位收口 ② API 冻结 ③ 无重叠 ④ 低成本 ⑤ 依赖 v1.49 ⑥ 独立 ⑦ 核心(v2.0 前奏) |

### 降级（9 版/功能 → v2.0+ 或 v3.0）

| 原版本 | 功能 | 裁决 | 依据 | 去向 |
|---|---|---|---|---|
| v1.37 | Claim Exchange Format v0（联邦互操作种子） | 降级 | ① 偏离当前 local-first 核心场景 ② 目标用户(单机/小团队)不需跨实例交换 ③ 无重叠 ④ 中成本(格式设计) ⑤ 无前置 ⑥ 独立 ⑦ **非核心场景(联邦是 v3.0 生态)** | → v2.0+（远期生态） |
| v1.38 | Multi-Agent Orchestration(A2A) + Sleeptime | 降级 | ① A2A 是 platform/生态非 local-first 核心 ② 目标用户不需多 agent A2A ③ 与既有 6 agent+workflow 有重叠 ④ 高成本(A2A 协议) ⑤ 无前置 ⑥ 独立 ⑦ **非核心(多 agent 编排是平台级)** | → v2.0+（platform）；sleeptime → 合并 Learn 引擎既有 distill |
| v1.40(marketplace) | Plugin Marketplace v1（registry） | 降级 | ① ecosystem 非当前核心 ② 当前用户基数不支持 marketplace ③ 与 plugin system 有重叠 ④ 高成本(registry 基建) ⑤ 无前置 ⑥ 独立 ⑦ **非核心(生态,非编译/治理)** | → v2.0+（生态阶段）；Plugin SDK v1 stable 留 v1.39 |
| v1.41 | Skill Sandbox(Docker/E2B) | 降级 | ① ecosystem ② 非核心场景 ③ 无重叠 ⑤ 高成本(Docker/E2B 基建) ⑦ **非核心(沙箱是平台基建)** | → v2.0+（需 Docker infra） |
| v1.42(IM SDK) | IM Serving 全链路(飞书/Slack/企微 SDK) | 降级 | ① ecosystem ② 非核心(local-first 不需 IM serving) ③ 与 v1.30 webhook 有部分重叠 ④ 高成本(多 SDK) ⑦ **非核心(IM 是生态触达)** | → v2.0+（生态触达）；Obsidian 双向 sync → 如预算允许合并 v1.39 |
| v1.46 | Agent Self-Evolution + Dreaming | 降级 | ① intelligence 但非当前核心 ② 目标用户不需 dreaming ③ 与 Learn distill 有重叠 ④ 高成本(dreaming 需 batch infra) ⑦ **非核心(自演进是高级)** | → v2.0+；auto-distill trends 留 Learn 引擎既有 |
| v1.48 | Federated Knowledge Graph v0 | 降级 | ① ecosystem/生态 ② 非核心(联邦是 v3.0) ③ 与 v1.37 exchange 有重叠 ⑦ **非核心** | → v3.0（生态/开放） |
| v1.42(Obsidian sync) | Obsidian 双向 sync | 降级(可合并) | ① ecosystem ② KW 用户有需求但非 P0 ③ 与 v1.28 Obsidian 有重叠 ⑦ 边缘(KW 触达) | → 可合并 v1.39 或 defer v2.0+ |
| Phase F-H (v2.1–v3.3) | 生态深化/自治/标准/行业包/边缘/知识资产 | 降级 | ① 全部 v2.0+/v3.0 远期 ② 当前无场景 ⑦ **全部非当前核心** | → 远期方向（Phase 3），不产 SPEC |

## 净版版本序列（Phase 2.5 后）

| 版本 | 主题 | Track | 原版本来源 |
|---|---|---|---|
| v1.34.1 | coverage 70% + god-files + stale-freshness + Dashboard 修复 | core-trust | v1.34.1 + CRITIC-F-01 合并 |
| v1.35.0 | Structured Context API v1（★品类定位） | intelligence | v1.35 不变 |
| v1.36.0 | Incremental Graph + Reasoning + Deep Research v2 | intelligence | v1.36 + v1.45 合并 |
| v1.37.0 | Governed Code Intelligence + Token Optimizer | core-trust+intelligence | v1.43 + v1.44 合并 |
| v1.38.0 | RBAC深化 + SSO/OIDC + Plugin SDK v1 + Observability v2 | platform | v1.39 + v1.40(SDK) + v1.47(obs) 合并 |
| v1.39.0 | Pre-v2.0 硬化 + coverage 75 + property/fuzz | core-trust | v1.49 不变 |
| v1.40.0 | v2.0 RC + Context API freeze | intelligence | v1.50 不变 |
| v2.0.0 | 平台化 MAJOR（仅真实 breaking） | platform | v2.0.0 不变 |

**降级到 v2.0+**：Claim Exchange, Multi-Agent A2A, Plugin Marketplace, Skill Sandbox, IM SDK, Self-Evolution, Federated KG, Phase F–H。
