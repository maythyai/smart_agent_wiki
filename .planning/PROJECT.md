# Smart Agent Wiki

## What This Is

Smart Agent Wiki 是一个下一代智能多代理知识平台，集百家之长，从 181 个 LLM Wiki 开源项目中汲取灵感。它将知识视为编译的结果而非检索的对象，通过四层存储架构（Vault→Claims→Wiki→Index）和五大引擎（摄入、查询、治理、学习、协作），实现知识从摄入到过期修剪的全生命周期管理。面向个人知识工作者和小团队，本地优先，渐进增强。

**v1.1 已发布** — 完整的多代理协作和 Web UI 可视化功能已实现。

## Core Value

**知识可信、可溯源、可进化** — 每一条回答都可以追溯到原始文档的具体位置，且原始文档永不被修改。如果只有一件事必须做好，那就是知识溯源和可信度体系。

## Requirements

### Validated

- ✓ 四层存储架构：Vault(不可变原始层) → Claims(主张层) → Wiki(可变综合层) → Index(索引层) — v1.1
- ✓ 摄入引擎：支持 PDF/Markdown/URL/代码多格式摄入 — v1.1
- ✓ 结构化数据零 LLM 提取（AST 解析代码、schema 解析 JSON/表格） — v1.1
- ✓ LLM 智能提取（单 LLM 模式） — v1.1
- ✓ 查询引擎：5 种查询模式（直接检索/图谱遍历/推理链/对比分析/综述生成） — v1.1
- ✓ 4 信号关联度模型 — v1.1
- ✓ 4 层置信度体系（未验证→单源→交叉验证→人工确认） — v1.1
- ✓ 矛盾检测 + 3 策略自动处理（Superseded/Disputed/Historical） — v1.1
- ✓ 9 级新鲜度系统 — v1.1
- ✓ 学习引擎：训练期自适应 + FSRS 间隔重复 + 趋势感知 — v1.1
- ✓ 认知蒸馏与 SOP 自动提取 — v1.1
- ✓ 知识过期修剪（战术/战略分类） — v1.1
- ✓ 多 Agent 角色化协作（Librarian/Writer/Critic/Linker/Scholar/Guardian） — v1.1
- ✓ A2A 协议 + YAML 工作流编排 — v1.1
- ✓ 密码审计层（Ed25519 签名收据 + Cedar 策略引擎） — v1.1
- ✓ MCP Server（23 个工具） — v1.1
- ✓ CLI 命令行（init/ingest/query/lint/verify/status/web 等） — v1.1
- ✓ Web UI（React + Cytoscape.js 知识图谱可视化 + Milkdown 编辑器） — v1.1
- ✓ 三层优雅降级（全功能→轻量→离线） — v1.1
- ✓ Write Queue (Outbox) 多 Sink 持久化写入 — v1.1
- ✓ 跨会话工作动量（WIP 文件） — v1.1
- ✓ 渐进式记忆深度（L0/L1/L2） — v1.1
- ✓ 16+ 代理兼容层 — v1.1
- ✓ 自适应索引演进（flat→hierarchical→indexed） — v1.1
- ✓ Research-on-Miss 自动研究闭环 — v1.1
- ✓ Git blame 双溯源链 — v1.1

### Active

(None — all v1 requirements shipped)

### Out of Scope

- **Obsidian 插件** — v2 生态完善阶段
- **Tauri 桌面应用** — v2 生态完善阶段
- **P2P 知识共享** — v2 生态完善阶段
- **团队部署模式 (Docker Compose + PostgreSQL)** — v2
- **API 开放平台** — v2
- **多语言支持 (EN/中文/日本語)** — v2
- **OWL-RL 本体推理** — v2
- **实时会议转写 (Soniox)** — 需要特定硬件/服务，后期考虑
- **Video/Audio ingestion (Whisper)** — v2
- **Chrome 剪藏扩展** — v2
- **RSS feed 订阅** — v2

## Context

**项目来源**: 基于 Karpathy 的 LLM Wiki 概念，分析了社区 666 条评论和 181 个衍生项目，识别出 25 个高质量参考项目。

**技术生态**:
- Python 3.11+ 为核心语言
- SQLite 为默认数据库（FTS5 全文搜索），PostgreSQL 用于团队模式
- LiteLLM 统一 100+ LLM 接入，按任务复杂度路由不同模型
- FastMCP 实现 MCP 协议服务器
- 可选向量存储：LanceDB/ChromaDB/FAISS
- PDF 解析：Docling → PyMuPDF 二级降级
- React 19 + Vite 8 + TypeScript 6 前端
- FastAPI + WebSocket 实时通信

**已发布版本**:
- v1.1 (2026-04-29): 完整多代理协作 + Web UI 可视化

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
| 四层存储 (Vault→Claims→Wiki→Index) | 兼顾溯源（逐字存储）与可用性（可变综合） | ✓ Good |
| 结构化零 LLM 提取 | 代码用 AST、JSON/表格用 schema，节省 token 成本 | ✓ Good |
| LLM 智能提取 | 单 LLM 模式先落地，多 LLM 交叉验证可后置 | ✓ Acceptable |
| 4 层置信度 × 3 级来源标记正交组合 | 页面级置信度 + 主张级来源标记 | ✓ Good |
| 多 Agent 按需调度 | Librarian(Haiku) 跑量, Writer(Sonnet) 质量, Scholar(Opus) 深度, Guardian(规则) 零成本 | ✓ Good |
| Write Queue Outbox 模式 | 单入口 → 持久化 outbox → 多 Sink 并行 | ✓ Good |
| 三层降级 (全功能→轻量→离线) | 系统在任何降级级别都可用 | ✓ Good |
| 自适应索引演进 | flat(≤50页) → hierarchical(≤200页) → indexed(>200页) | ✓ Good |
| Git blame 双溯源链 | Claims→Vault + git blame→session branch | ✓ Good |
| 16+ 代理兼容 | 每个代理一个配置文件 | ✓ Good |
| Cedar 策略引擎 | 实验性 cedar-python + CLI fallback | ✓ Acceptable |
| React 19 + Zustand | 前端技术栈现代且稳定 | ✓ Good |

## Current Milestone: v2.0 Extended Ingestion & Team Platform

**Goal:** 扩展知识摄入渠道（视频/音频）并支持团队协作部署模式

**Target features:**
- **Video/Audio Ingestion** — 使用 Whisper 转录视频和音频内容，扩展知识来源
- **Team Deployment** — Docker Compose + PostgreSQL + Redis 支持多用户团队模式
- **API Platform** — 开放 API 供第三方集成

## Current State

**Shipped Version:** v1.1 (2026-04-29)
**Current Milestone:** v2.0 (Planning)

**v1.1 Stats:**
- Phases: 5 (01, 02, 03-01, 03-02, 03-03)
- Plans: 19
- Tests: 430+ passing
- Python LOC: ~16,100
- TypeScript LOC: ~3,662

**Tech Debt:**
1. Phase VERIFICATION.md files missing (Phase 02, 03-01, 03-02, 03-03) — non-blocking
2. React frontend tests deferred (vitest not installed) — non-blocking
3. Bundle size 1.36MB (Milkdown adds significant weight) — acceptable

## Evolution

This document evolves at phase transitions and milestone boundaries.

**v1.1 Milestone Review (2026-04-29):**
- All 65 v1 requirements shipped and validated
- Core value (知识可信、可溯源、可进化) achieved
- Multi-agent collaboration working with 6 specialized agents
- Web UI fully functional with search, graph, editor, dashboard
- MCP Server exposing 23 tools for agent integration
- Next: v2 planning for extended features

---

*Last updated: 2026-04-29 after v1.1 milestone*