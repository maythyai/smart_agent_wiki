---
id: STRATEGY
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-02
status: active
tracks: [core-trust, platform-team, ecosystem-integration, intelligence-adaptation]
north_star: trustworthy-claim coverage
version_scheme: SemVer
see_also: docs/strategy/ROADMAP.md | docs/prd/PRD-INDEX.md | .csp/manifest.json
---

# Strategy: Smart Agent Wiki

> 战略锚点（Anchor, not plan）。回答"产品是什么/为什么/为谁"。功能细节归 01 PRD/spec，排期归任务管理。下游 01 PRD 读本文件 ground 价值与定位。

## 1. Target problem（诊断）

知识管理被当成"检索的对象"而非"编译的产物"。后果是三个不对称：

- **不可溯源**：AI agent 与搜索器给出的答案无法回溯到原文位置，无法验证真伪。RAG 把片段拼出来，却不知片段从哪来、是否过时、是否与其它来源冲突。
- **不可信**：知识一旦入库即冻结——无置信分级、无新鲜度、无矛盾检测、无审计凭证。用户无法判断一条 claim 值不值得信。
- **不可演进**：本地知识库（Notion/Obsidian/Logseq 等）各自为政，缺乏从摄入到失效修剪的全生命周期治理；扩展与集成靠人工搬运。

现状痛点的不对称在于：**算力与模型已过剩，瓶颈转移到"信任 + 溯源 + 治理"**——尤其当 AI agent 成为知识的主要消费者时，"可验证"比"能回答"更稀缺。

## 2. Our approach（指导方针）

**知识即编译，非检索对象**（Knowledge as compilation, not retrieval）。四层存储 + 治理引擎 + 多代理协作构成解法，差异化选择是：

- **四层存储溯源**：Vault → Claims → Wiki → Index，每条 claim 锚定原文精确位置。这是"可验证"的物理基础，而非黑盒 RAG。
- **治理引擎做信任闭环**：4 级置信 + 9 级新鲜度 + 矛盾检测 + Ed25519 审计凭证。把"信不信"从主观判断变成可检查的状态。
- **多代理协作做演进**：6 个专业 agent（Librarian/Writer/Critic/Linker/Scholar/Guardian）经 workflow 编排，覆盖摄入→治理→学习全链路，知识可持续更新而非冻结。
- **Local-first + Agent-native**：数据本地、云同步可选；MCP server（61+ tools）使 SAW 成为 Claude Code/Cursor/Copilot 等代理的可信知识后端。
- **可扩展**：插件系统 + 连接器框架（GitHub/Notion/Slack/Discord/飞书/企业微信/Logseq）。

**为什么是现在**：AI agent 大规模落地，"答案可信度"成为生产级瓶颈；MCP 协议成熟，local-first + agent-native 的组合窗口打开。错过窗口，知识层会被云上 RAG 黑盒统一吞没。

## 3. Who it's for（为谁）

不是"所有用户"，是三类有明确痛点的角色：

| 角色 | 特征 | 核心需求 | 场景 |
|---|---|---|---|
| 知识工作者 KW | 个人研究者/写作者，local-first 偏好 | 导入资料→查询→得到可溯源答案 | 日常知识沉淀、文献综述 |
| 开发者 DEV | 扩展/集成 SAW 的工程师 | 清晰能力边界、可复现 API/CLI/MCP、可扩展插件 | 二次开发、连接器集成、MCP 接入 |
| 平台运维者 OPS | 自托管团队部署者 | 可观测、可审计、可限流、可健康巡检 | 部署、监控、安全合规 |

## 4. Key metrics（北极星）

**北极星指标**：trustworthy-claim coverage —— 库中"可溯源 + 有置信分级 + 新鲜"的 claim 占比。它直接反映"知识即编译"的核心价值：可信知识的密度。

**子指标（记录"哪些重要、在哪看"，不编造量级）**：

- 核心链路冒烟通过率（ingest→compile→query→govern→learn）— CI 冒烟 job
- 宣称-实现一致率（README/docs vs 代码）— 自动 diff 校验
- 审计 receipt 覆盖率（高危操作产凭证）— receipt 统计
- 核心引擎链路测试覆盖率 — CI coverage 报告

> 业务量级（DAU/装机量）`[TBD]`：开源项目未提供，不臆造。

## 5. Tracks（连贯行动主线）

1. **核心体验与可信地基（core-trust）**：把"可运行"打磨为"端到端可用、宣称一致、安全可审计、测试有门禁"。地基先稳，再谈扩张。
2. **平台化与团队协作（platform-team）**：从单机 local-first 走向可自托管的多用户平台——RBAC 深化、团队部署、可观测闭环、多租户隔离。
3. **生态与集成（ecosystem-integration）**：稳定插件 SDK + 连接器框架 + MCP surface，让 SAW 成为 agent 生态的可信知识后端，而非孤岛。
4. **智能与自适应（intelligence-adaptation）**：代理编排 workflow、Learn（distill/trends）、Token 优化真实落地，让知识库自我演进。

## 6. Not working on（聚焦的代价）

- **不做云优先 / SaaS 托管**：坚持 local-first，数据主权归用户。云同步可选，但不是托管替代。
- **不做通用 RAG 聊天机器人**：SAW 是知识编译与治理层，不是又一个 chatbot 前端。
- **不做厂商锁定**：连接器与插件开放，不绑单一生态。
- **不做排期与功能堆砌**：战略只给方向 + 版本主题，详细 PRD 归 01，排期归任务管理。
