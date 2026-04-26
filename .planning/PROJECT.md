# Smart Agent Wiki

## What This Is

Smart Agent Wiki 是一个下一代智能多代理知识平台，集百家之长，从 181 个 LLM Wiki 开源项目中汲取灵感。它将知识视为编译的结果而非检索的对象，通过四层存储架构（Vault→Claims→Wiki→Index）和五大引擎（摄入、查询、治理、学习、协作），实现知识从摄入到过期修剪的全生命周期管理。面向个人知识工作者和小团队，本地优先，渐进增强。

## Core Value

**知识可信、可溯源、可进化** — 每一条回答都可以追溯到原始文档的具体位置，且原始文档永不被修改。如果只有一件事必须做好，那就是知识溯源和可信度体系。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] 四层存储架构：Vault(不可变原始层) → Claims(主张层) → Wiki(可变综合层) → Index(索引层)
- [ ] 摄入引擎：支持 PDF/Markdown/URL/代码/音频/视频等多格式摄入
- [ ] 结构化数据零 LLM 提取（AST 解析代码、schema 解析 JSON/表格）
- [ ] 非结构化数据多 LLM 竞争提取 + 交叉验证
- [ ] 查询引擎：5 种查询模式（直接检索/图谱遍历/推理链/对比分析/综述生成）
- [ ] 4 信号关联度模型（直接链接/来源重叠/Adamic-Adar/类型亲和）
- [ ] 4 层置信度体系（未验证→单源→交叉验证→人工确认）
- [ ] 矛盾检测 + 3 策略自动处理（Superseded/Disputed/Historical）
- [ ] 9 级新鲜度系统
- [ ] 学习引擎：训练期自适应(前30天) + FSRS 间隔重复 + 趋势感知
- [ ] 认知蒸馏与 SOP 自动提取
- [ ] 知识过期修剪（战术/战略分类）
- [ ] 多 Agent 角色化协作（Librarian/Writer/Critic/Linker/Scholar/Guardian）
- [ ] A2A 协议 + YAML 工作流编排
- [ ] 密码审计层（Ed25519 签名收据 + Cedar 策略引擎）
- [ ] MCP Server（23 个工具）
- [ ] CLI 命令行（init/ingest/query/lint/verify/status/prune 等）
- [ ] Web UI（React + Cytoscape.js 知识图谱可视化 + Milkdown 编辑器）
- [ ] 三层优雅降级（全功能→轻量→离线）
- [ ] Write Queue (Outbox) 多 Sink 持久化写入
- [ ] 跨会话工作动量（WIP 文件）
- [ ] 渐进式记忆深度（L0/L1/L2）
- [ ] 16+ 代理兼容层
- [ ] 自适应索引演进（flat→hierarchical→indexed）
- [ ] Research-on-Miss 自动研究闭环
- [ ] Chrome 剪藏扩展
- [ ] Git blame 双溯源链

### Out of Scope

- **Obsidian 插件** — Phase 4 生态完善阶段
- **Tauri 桌面应用** — Phase 4 生态完善阶段
- **P2P 知识共享** — Phase 4 生态完善阶段
- **团队部署模式 (Docker Compose + PostgreSQL)** — Phase 4
- **API 开放平台** — Phase 4
- **多语言支持 (EN/中文/日本語)** — Phase 4
- **OWL-RL 本体推理** — Phase 4
- **实时会议转写 (Soniox)** — 需要特定硬件/服务，后期考虑

## Context

**项目来源**: 基于 Karpathy 的 LLM Wiki 概念，分析了社区 666 条评论和 181 个衍生项目，识别出 25 个高质量参考项目。

**技术生态**:
- Python 3.11+ 为核心语言
- SQLite 为默认数据库（FTS5 全文搜索），PostgreSQL 用于团队模式
- LiteLLM 统一 100+ LLM 接入，按任务复杂度路由不同模型
- FastMCP 实现 MCP 协议服务器
- 可选向量存储：LanceDB/ChromaDB/FAISS
- PDF 解析：MinerU → Docling → PyMuPDF 三级降级

**已有研究**: 本仓库包含完整的设计文档 (`docs/smart_agent_wiki_design.md`)、181 项目生态分析 (`docs/llm_wiki_ecosystem_analysis.md`)、远程项目审计发现 (`docs/remote_project_audit_findings.md`)，以及 Karpathy 原始概念和评论分析。

**关键参考项目**:
- Knowledge Pipeline — 编译范式、矛盾检测
- Multi-Agent Wiki — 多代理治理、[APPLE] 欺骗分类学
- Memex — 3 策略冲突处理
- codesight — AST 零 LLM 提取
- llm-wiki1 — FSRS 间隔重复、10 Agent 分工
- scopeblind-gateway — Ed25519 + Cedar 密码审计
- unified-memory-ai-agents — 三层认知、WIP 动量、知识过期
- TreeSearch — 结构感知 FTS5 搜索
- ContextLattice — 多 Sink 持久化写入
- MindOS — A2A 协议、YAML 工作流、Echo 认知蒸馏

## Constraints

- **Tech Stack**: Python 3.11+, Typer, FastAPI, SQLite, FastMCP — 选择理由：生态最丰富，AI 库最全
- **Local-first**: 默认纯本地运行，零外部依赖可选
- **渐进增强**: 5 分钟可用（init → ingest → query），功能渐进解锁
- **日运行成本**: 单用户模式 < $0.5/天（通过多模型路由控制）
- **部署模式**: 纯本地 / 本地+云LLM / 团队(Docker Compose)
- **嵌入模型**: 默认 all-MiniLM-L6-v2 (80MB)，零 API，隐私安全

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 四层存储 (Vault→Claims→Wiki→Index) | 兼顾溯源（逐字存储）与可用性（可变综合），双轨不互斥 | — Pending |
| 结构化零 LLM 提取 | 代码用 AST、JSON/表格用 schema，节省 token 成本 | — Pending |
| 非结构化多 LLM 竞争 | 同一文档 2 个 LLM 独立提取交叉验证减少幻觉 | — Pending |
| 4 层置信度 × 3 级来源标记正交组合 | 页面级置信度 + 主张级来源标记，精细可信度管理 | — Pending |
| 多 Agent 按需调度 | Librarian(Haiku) 跑量, Writer(Sonnet) 质量, Scholar(Opus) 深度, Guardian(规则) 零成本 | — Pending |
| Write Queue Outbox 模式 | 单入口 → 持久化 outbox → 多 Sink 并行，确保写入不丢失 | — Pending |
| 三层降级 (全功能→轻量→离线) | 系统在任何降级级别都可用，知识库不会变成"只读废墟" | — Pending |
| 自适应索引演进 | flat(≤50页) → hierarchical(≤200页) → indexed(>200页) | — Pending |
| Git blame 双溯源链 | Claims→Vault + git blame→session branch，比 anchor cites 更可靠 | — Pending |
| 16+ 代理兼容 | 核心逻辑在 CLI/MCP，不绑定特定代理，每个代理一个配置文件 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-26 after initialization*
