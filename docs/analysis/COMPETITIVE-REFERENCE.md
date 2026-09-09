---
id: COMPETITIVE-REFERENCE
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: active
generated_by: roadmap Phase 0.5（竞品借鉴）
see_also: docs/strategy/ROADMAP.md | docs/strategy/STRATEGY.md
---

# Competitive Reference — 同类开源项目借鉴清单

> 产出自外环 roadmap Phase 0.5。**借鉴非复制**：每条均经"是否适合 SAW 定位 + 差异化"判断，不照抄。开源协议兼容标注：MIT/Apache 可借鉴代码模式；AGPL 仅借鉴思路不引代码。参考项目已 shallow-clone 至 `开源项目参考/`（只读分析，不纳入 SAW 源树）。

## 一、参考项目全景

| 项目 | 路径 | 协议 | 一句话定位 | 与 SAW 关系 |
|---|---|---|---|---|
| **WeKnora** (Tencent) | `开源项目参考/WeKnora` | MIT | 文档→RAG+自主推理 agent+自维护 Wiki+知识图谱+多租户 RBAC | **最接近的直接竞品**（自维护 Wiki+KG+agent），但偏云/腾讯生态 |
| **Khoj** | `开源项目参考/khoj` | AGPL-3.0 | 自托管 AI second brain，多格式索引+RAG 带引用+agents/调度+深度研究 | 同赛道（local-first second brain），但纯 RAG 无编译/治理/code |
| **GraphRAG** (Microsoft) | `开源项目参考/graphrag` | MIT | LLM 生成知识图谱 + 层次社区检测 + global/local/DRIFT 检索 | **技术组件级参考**（claims/code 图的社区化） |
| **Cognee** | `开源项目参考/cognee` | Apache-2.0 | agent 长期记忆平台，ECL 管道+KG/向量统一记忆+矛盾检测 | 记忆层参考（矛盾边、provenance、session distillation） |
| **Letta** (前 MemGPT) | `开源项目参考/letta` | Apache-2.0 | 有状态 agent + 分层记忆 + 自编辑记忆 + sleeptime + Agent File | agent 记忆/状态参考（自编辑、rethink、便携格式） |
| **Potpie** | `开源项目参考/potpie` | Apache-2.0 | 代码库 context graph + task-scoped resolve + 预置 code agent | code intelligence 产品化参考（resolve/record/skills 安装） |

## 二、差异化判断（SAW 的护城河 vs 竞品）

竞品各做 SAW 的一部分，**无一同时覆盖**：
- WeKnora 有自维护 Wiki+KG+agent+RBAC，但无 SAW 的 **四层溯源（Vault→Claims→Wiki→Index）+ Ed25519 审计凭证 + 9 级新鲜度**。
- GraphRAG 有图抽取+社区，但**无治理/信任/本地优先/代码**。
- Letta/Cognee 有 agent 记忆/矛盾，但**无知识编译层、无 claims 锚定原文、无 code graph**。
- Khoj 是 second brain，但**纯检索非编译、无治理**。
- Potpie 是 code context，但**代码 only、无文档知识/信任**。

**SAW 不被吞的护城河 = 溯源 + 治理 + 数据主权三件事的耦合**（STRATEGY 长期愿景）。借鉴的方向是**强化这条护城河**，而非堆砌竞品 feature。

## 三、借鉴清单（feature → SAW 落地 → 拟纳入版本）

> 拟纳入版本为候选，**非定论**，供下一轮 01 PRD 决策。版本号按 SemVer 增量续编（additive=MINOR）。

### A. 强化"知识编译"主线（intelligence-adaptation track）

| # | 来源 | 借鉴 feature | SAW 差异化落地 | 拟纳入 |
|---|---|---|---|---|
| A1 | WeKnora | **Agent 自蒸馏自维护 Wiki**：agents 把 claims 蒸馏成互链 markdown wiki 页 + 修订历史 + 行级 diff + 一键回滚 | SAW 已有 Wiki 层（手工）+ Writer/Linker agent；落地为 **Writer 自动把高置信 claims 编译成互链 wiki 页**，Linker 自动建链，**复用 SAW 既有 Ed25519 receipt 作修订凭证**（非另造）。差异化：每页每条 claim 可溯源到 Vault 原文——WeKnora 无此溯源链。 | v1.19.0 候选 |
| A2 | GraphRAG | **层次社区检测（Leiden）+ 社区报告**：在 claims/code 图上做层次聚类，每社区 LLM 生成主题报告，支持"整个库在讲什么"全局问答 | SAW claims 图已有但无社区级主题摘要。落地为 **claims/code 图层次社区 + community report**，global search 回答全局性问题。差异化：社区报告锚定 claims（可溯源+置信），非 GraphRAG 的无置信文本社区。 | v1.20.0 候选 |
| A3 | GraphRAG | **DRIFT 检索**：global（社区）+ local（实体邻域）混合，按置信门控扩展深度 | SAW 检索以语义+图为主；落地为 **DRIFT 式混合检索**，用 SAW 置信分级作扩展门控（低置信不扩展）。 | v1.20.0 候选 |
| A4 | Khoj | **深度研究模式**：多步 web+库内 docs 合成，带引用的结构化研究产出 | SAW 已有 Scholar agent + research；落地为**面向用户的"深度研究"产品模式**（Scholar 编排 web 搜索+库内 claims→可溯源研究报告）。差异化：结论锚定库内可信 claims。 | v1.21.0 候选 |
| A5 | Khoj | **调度自动化（automations）**：周期性 agent 任务（如每日摘要） | SAW 有 workflow 编排；落地为**用户可配的周期 automation**（Scholar/Guardian 定时跑）。 | v1.21.0 候选 |

### B. 强化"可信 + 治理"主线（core-trust track）

| # | 来源 | 借鉴 feature | SAW 差异化落地 | 拟纳入 |
|---|---|---|---|---|
| B1 | Cognee | **`contradicts` 图边 + 置信分**：矛盾事实不静默覆盖，写显式 contradicts 边承载双事实+置信 | SAW 已有矛盾检测（Govern engine）；落地为**把矛盾显式建模为 claims 图的 contradicts 边**（带 4 级置信），而非仅告警。差异化：与 Ed25519 receipt 闭环。 | v1.19.0 候选 |
| B2 | Letta | **`memory_rethink` 矛盾时重评**：agent 遇新信息与旧记忆冲突时主动重评 | SAW Guardian agent 可采纳 **rethink 语义**：检测冲突→触发重评→写 contradicts 边（B1）+ receipt。 | v1.19.0 候选 |
| B3 | GraphRAG | **claim 抽取带 status（TRUE/FALSE/SUSPECTED）+ 时间界** | SAW claims 有置信但无显式 TRUE/FALSE/SUSPECTED 状态轴；**复用 SAW 4 级置信 + 9 级新鲜度映射到此状态轴**（不另造维度）。 | v1.20.0 候选 |
| B4 | GraphRAG | **FastGraphRAG NLP 抽取降本**：NLP 名词短语+共现作廉价索引层（成本降 ~1000x） | SAW 摄入用 LLM 抽 claims 成本高；落地为**NLP 廉价预索引层**（名词短语共现图）作 LLM 精抽取的前置/降本路径，LLM 抽取仍为高置信层。 | v1.22.0 候选 |
| B5 | Cognee | **provenance 一等模块 + auto-feedback 自调**：逐轮 LLM 反馈检测调检索权重 | SAW 有 traceability 但 provenance lineage 可更显式；auto-feedback 落地为**检索权重按用户隐式反馈自调**。 | v1.22.0 候选 |

### C. 强化"agent-native + 生态"主线（ecosystem-integration track）

| # | 来源 | 借鉴 feature | SAW 差异化落地 | 拟纳入 |
|---|---|---|---|---|
| C1 | Potpie | **`resolve <task>` 任务级上下文召回**：改代码前精准拉取 agent 该读的上下文 | SAW 已有 impact analysis；落地为 **MCP `saw_resolve` 原语**（任务→召回相关 claims/code/wiki 上下文），区别于 impact（事后影响）的是 resolve 是**事前准备**。 | v1.19.0 候选 |
| C2 | Potpie | **`record` 持久学习/决策**：agent 把决策/约定写入图 | SAW Linker/Scholar 可 **`saw_record`** 把决策/约定持久化进 claims/wiki（带 receipt）。 | v1.19.0 候选 |
| C3 | Potpie | **coding-harness skills 安装**：往 Claude Code/Codex/Cursor/OpenCode 装 SAW skills | **直接填补已删 phase-29 的真实需求**（轻量 skills 非 in-product phase）：交付一个 `.claude/skills/saw-*` 包，教 harness 何时调 `saw_resolve`/`saw_impact`/`saw_staleness`。 | v1.19.0 候选 |
| C4 | Letta | **Agent File (.af) 便携状态格式**：agent 人格+记忆+工具配置序列化为可分享文件 | **闭合 ROADMAP 既有 backlog T3**（自定义角色分享/导入）。落地为 SAW 的 `saw agents export/import`，复用既有自定义角色（v1.15）。 | v1.20.0 候选 |
| C5 | Khoj/WeKnora | **IM channel serving + Obsidian/Emacs 插件 reach** | SAW 有 connectors（摄入侧）但 serving 侧弱；落地为**经 IM（飞书/Slack/企微）serve Q&A** + **Obsidian 插件**（SAW 的 KW 用户即 Obsidian/Logseq 用户）。差异化：答案带可溯源 claims。 | v1.21.0 候选 |
| C6 | WeKnora | **skill sandbox（Docker/E2B）执行 agent 代码** | SAW Collaborate agent 可采纳**沙箱执行**做代码操作（与 Guardian receipt 闭环）。 | v1.22.0 候选 |

### D. 强化"平台化"主线（platform-team track）

| # | 来源 | 借鉴 feature | SAW 差异化落地 | 拟纳入 |
|---|---|---|---|---|
| D1 | WeKnora | **Langfuse 式 trace 可观测 + W3C traceparent** | SAW 有 trace_id 贯穿但可视化弱；落地为**Langfuse 接入或等价 trace UI**（复用 SAW 既有 trace_id）。 | v1.20.0 候选 |
| D2 | WeKnora | **task-queue dashboard + worker-pool 治理**（队列深度/并发/失败重试） | SAW Write Queue 是唯一变更网关；落地为**Write Queue 运维 dashboard**（深度/背压/失败重试可视化）。 | v1.21.0 候选 |
| D3 | Letta | **heartbeat 事件**：定时跑 agent "大脑"做主动记忆管理 | SAW workflow 可加 **heartbeat-driven 主动巡检**（Guardian 定时跑新鲜度/矛盾巡检）。 | v1.22.0 候选 |

## 四、不借鉴（明确拒绝，聚焦代价）

| 来源 | feature | 不借鉴理由 |
|---|---|---|
| Khoj | 云托管/SaaS（已下线） | SAW 红线：local-first，数据主权 |
| Khoj | 图像生成 / voice TTS | 偏离"知识编译"核心，非 SAW 定位 |
| WeKnora | 腾讯生态连接器（飞书 wiki/IMA 等强绑定） | SAW 不做厂商锁定；通用连接器框架已覆盖 |
| GraphRAG | 全 LLM 抽取（无 NLP 廉价层）作唯一路径 | 成本高；SAW 采 NLP+LLM 分层（B4），不全 LLM |
| Letta | OS 虚拟内存隐喻全套（分页/FIFO 淘汰） | SAW 已有四层存储+Write Queue，不引入第二套内存抽象 |

## 五、协议合规备忘

- MIT（WeKnora/GraphRAG）、Apache-2.0（Cognee/Letta/Potpie）：可借鉴代码模式，引用时标来源。
- **AGPL-3.0（Khoj）**：仅借鉴产品思路，**不引入任何 Khoj 代码**，避免 AGPL 网络传染。SAW 自身协议以 LICENSE 为准。
- 各参考项目 clone 仅为只读分析，不纳入 SAW 源树（`开源项目参考/` 已 .gitignore）。

> 下一步：本清单的"拟纳入版本"作为 ROADMAP v1.19.0+ 候选主题输入；具体取舍由下一轮 01 PRD 决策（01 读 ROADMAP 定位版本主题）。
