# Stack Research

**Domain:** 智能多代理知识管理平台 (Intelligent Multi-Agent Knowledge Platform)
**Researched:** 2026-04-27 (Phase 03 additions)
**Confidence:** HIGH

---

## Phase 03 Additions (Collaboration & Visualization)

### Multi-Agent Orchestration

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| LangGraph | 1.1.9 | Agent orchestration framework | Low-level state machine approach; explicit graph definition gives full control over agent transitions; supports persistence, streaming, and human-in-the-loop; mature ecosystem under LangChain; orchestrator-worker pattern matches 6-agent design; YAML workflow possible via structured output | HIGH |
| A2A SDK | 1.0.2 | Agent-to-agent protocol | Linux Foundation project (Google contribution); JSON-RPC 2.0 over HTTP(S) standard protocol; Agent Cards for capability discovery; supports sync/streaming/async modes; enterprise-ready security; enables cross-framework agent interoperability | MEDIUM |
| Pydantic | 2.13.3 | Workflow schema validation | Already in stack; define YAML workflow schema with type safety; integrates with LangGraph structured output; validates Agent Card schemas | HIGH |
| PyYAML | 6.0.3 | Workflow definition files | Already in stack; declarative workflow definitions; human-editable agent pipelines; version-controllable configurations | HIGH |

**Rationale for LangGraph over alternatives:**

| Alternative | Why Not |
|-------------|---------|
| CrewAI 1.14.3 | Higher-level abstraction that hides state machine complexity; less control over agent transitions; "role-based" model doesn't map well to our 6 specialized agents; more opinionated about agent structure |
| AutoGen 0.10.0 | Microsoft's framework; conversation-centric model less suited for pipeline workflows; heavier dependency chain; less mature LangChain integration |
| Custom orchestration | Reinventing graph state machine; LangGraph provides persistence, checkpointing, and streaming out of box |

### Web Frontend Stack

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| React | 19.2.5 | UI framework | Industry standard; React 19 Actions simplify async state; concurrent rendering; mature ecosystem; integrates with existing FastAPI backend via REST/WebSocket | HIGH |
| Zustand | 5.0.12 | Client state management | Minimal boilerplate (~1KB); hook-based API; no Provider wrapping needed; supports middleware; better DX than Redux for medium complexity; Time-travel via Zundo if needed | HIGH |
| TanStack Query | 5.100.5 | Server state management | Declarative data fetching; automatic caching/refetching; optimistic updates; integrates with FastAPI endpoints; eliminates manual loading/error state | HIGH |
| Cytoscape.js | 3.33.2 | Knowledge graph visualization | Battle-tested graph rendering; handles 10K+ nodes; rich layout algorithms (dagre, cola, breadthfirst); extensive styling; good performance for knowledge graphs | HIGH |
| react-cytoscapejs | 2.0.0 | React wrapper for Cytoscape | Declarative component API; props-driven graph updates; integrates with Zustand state | HIGH |
| Milkdown | 7.20.0 | WYSIWYG Markdown editor | ProseMirror-based; plugin-driven architecture; CommonMark + GFM support; first-class React integration; Crepe preset for drop-in WYSIWYG | HIGH |
| Vite | 6.x | Frontend build tool | Fast HMR; native ES modules; TypeScript support; simpler than webpack; standard for React 19 projects | HIGH |
| TypeScript | 5.x | Type safety | End-to-end type safety with FastAPI Pydantic schemas; better IDE support; catches errors at compile time | HIGH |

**State Management Strategy:**

```
Client State (Zustand)        Server State (TanStack Query)
- UI mode (edit/view)         - Wiki pages (queries)
- Graph selection             - Search results (queries)
- Editor content draft        - Agent status (mutations)
- Sidebar state               - Ingestion jobs (mutations)
- Theme/preferences           - Graph data (queries with cache)
```

### Cedar Policy Engine Integration

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| cedar-python | 0.1.4 | Cedar policy evaluation | Amazon's official Cedar bindings for Python; RBAC + ABAC policies; audit trail for agent actions; fine-grained access control | LOW |
| PyNaCl | 1.6.2 | Ed25519 signatures | Already in stack; agent identity verification; receipt signing for audit trail | HIGH |
| cedar-wasm | (npm) | Browser policy preview | Optional: preview policy decisions in Web UI; same policy language as backend | LOW |

**Cedar Integration Considerations:**

The cedar-python 0.1.4 binding is early-stage. Fallback strategies:
1. **Subprocess to Cedar CLI**: Invoke `cedar` binary directly for policy evaluation
2. **cedar-wasm via Python WASM**: Load `@cedar-policy/cedar-wasm` in Python via wasmtime
3. **Simplified policy engine**: Implement subset of Cedar semantics in pure Python for MVP

For Phase 03, recommend cedar-python with fallback to subprocess CLI.

---

## Existing Stack (Phase 1 & 2)

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Python | 3.11+ | 核心语言 | AI 生态最丰富，所有 LLM/embedding/MCP 库首等公民支持；3.11 引入 exception groups 和 TOML 读取，3.12 性能进一步提升 | HIGH |
| Typer | 0.24.2 | CLI 框架 | 由 FastAPI 作者 tiangolo 开发，类型注解驱动 CLI 生成，与 FastAPI API 风格一致；Rich 集成带来开箱即用的美化输出；自动补全和帮助文档生成 | HIGH |
| FastAPI | 0.136.1 | Web API 框架 | 异步原生、Pydantic v2 验证、自动 OpenAPI 文档；Python Web 生态事实标准；Starlette 底层高性能 | HIGH |
| SQLite (stdlib) | 内置 | 默认数据库 | 零安装、单文件、FTS5 全文搜索内置；本地优先架构的完美匹配；WAL 模式支持并发读写 | HIGH |
| SQLModel | 0.0.38 | ORM 层 | SQLAlchemy + Pydantic 统一，类型安全，FastAPI 原生集成；同一个模型类既做 ORM 又做 API schema | MEDIUM |
| FastMCP | 3.2.4 | MCP 协议服务器 | MCP 生态的标准框架（PrefectHQ 维护，日下载百万次）；装饰器声明式工具注册，自动 schema 生成；内部封装官方 mcp>=1.24.0 SDK；支持 Server/Client/Apps 三种模式 | HIGH |
| LiteLLM | 1.83.13 | LLM 统一接入 | 100+ provider 统一接口，一个 API 调用 OpenAI/Claude/Gemini/本地模型；内置重试、fallback、速率限制；成本追踪；按任务复杂度路由不同模型的核心依赖 | HIGH |
| NetworkX | 3.6.1 | 知识图谱引擎 | 纯 Python 图计算库，零外部依赖；支持 BFS/DFS/PageRank/Adamic-Adar 等图算法；与四层存储的 Graph 层完美匹配；对于 <100K 节点的知识图谱性能足够 | HIGH |

### Database Layer

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| SQLite FTS5 | 内置 | 全文搜索 | 结构感知搜索的基础；支持 BM25 排名、snippet/highlight、column filter；零依赖，Vault 层搜索的默认引擎 | HIGH |
| APSW | 3.53.0.0 | SQLite 高级接口 | 比标准 sqlite3 模块更完整的 SQLite 功能暴露（包括 FTS5 辅助函数、自定义分词器、WAL 控制）；当标准库 sqlite3 模块不够用时使用 | MEDIUM |
| LanceDB | 0.30.2 | 向量搜索 (可选) | 纯本地嵌入式向量数据库，无需服务器进程；基于 Lance 列式格式，支持增量写入；与 PyArrow 生态集成；磁盘占用小；本地优先架构的最佳选择 | HIGH |
| PostgreSQL | 16+ | 团队模式数据库 | Phase 4 团队部署模式的升级路径；pgvector 扩展支持向量搜索替代 LanceDB；FTS 全文搜索；成熟并发控制 | MEDIUM |

### Document Processing

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| Docling | 2.91.0 | PDF/文档智能解析 | IBM 开源，支持 PDF/DOCX/PPTX/HTML/图片；DoclingDocument 统一输出格式；集成 EasyOCR；比 PyMuPDF 解析质量更高，比 MinerU 更易安装 | HIGH |
| MinerU | 3.1.4 | PDF 高精度解析 (降级备选) | Magic-PDF 升级版，OCR 和版面分析精度最高；但依赖链较重（PaddleOCR），作为 Docling 的降级备选 | MEDIUM |
| PyMuPDF | 1.27.2 | PDF 基础解析 (最后降级) | 最轻量的 PDF 解析库，速度极快；纯文本 PDF 效果好，复杂版面效果差；作为三级降级的最后选择 | HIGH |
| python-frontmatter | 3.0.8 | Markdown 元数据解析 | 解析 Markdown 文件的 YAML frontmatter；Vault 层和 Wiki 层的 Markdown 处理基础 | HIGH |
| markdown-it-py | 4.0.0 | Markdown AST 解析 | CommonMark 规范兼容，可扩展插件系统；用于结构感知的 Markdown 内容提取 | HIGH |
| BeautifulSoup4 | 4.14.3 | HTML 解析 | URL 抓取后的 HTML 内容提取；lxml 解析器后端性能好 | HIGH |
| trafilatura | 2.0.0 | Web 内容提取 | 从 URL 提取正文内容，自动去除导航/广告/侧边栏；比 newspaper3k 更可靠 | HIGH |

### AI/ML Layer

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| sentence-transformers | 5.4.1 | 嵌入模型 | 默认模型 all-MiniLM-L6-v2 (80MB)，零 API 调用，本地运行，隐私安全；sentence-transformers 5.x 支持更多模型格式和量化 | HIGH |
| rank-bm25 | 0.2.2 | BM25 算法 | 纯 Python BM25 实现，与 FTS5 互补用于混合搜索评分；轻量无依赖 | HIGH |
| faster-whisper | 1.2.1 | 音频转写 | CTranslate2 后端的 Whisper，比 openai-whisper 快 4x，内存少 50%；音频/视频摄入的转写引擎 | HIGH |
| scikit-learn | 1.8.0 | 机器学习工具 | TF-IDF、余弦相似度、聚类等基础 ML 工具；用于关联度计算和知识聚类 | MEDIUM |

### Security & Governance

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| PyNaCl | 1.6.2 | Ed25519 签名 | libsodium Python 绑定，Ed25519 数字签名实现；密码审计层的签名收据核心依赖 | HIGH |
| cedar-python | 0.1.4 | Cedar 策略引擎 | Amazon Cedar 策略语言的 Python 绑定；声明式访问控制策略；RBAC/ABAC 策略引擎的核心 | LOW |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.13.3 | 数据验证与序列化 | 所有 API schema、配置模型、数据传输对象；FastAPI/SQLModel/FastMCP 共享基础 |
| Pydantic Settings | 2.14.0 | 配置管理 | 环境变量、.env 文件、嵌套配置的统一管理 |
| python-dotenv | 1.2.2 | 环境变量加载 | .env 文件解析，开发环境配置管理 |
| httpx | 0.28.1 | HTTP 客户端 | 异步 HTTP 请求；URL 抓取、API 调用、LiteLLM 底层依赖 |
| Rich | 15.0.0 | 终端美化输出 | CLI 进度条、表格、语法高亮输出；Typer 内置集成 |
| PyYAML | 6.0.3 | YAML 处理 | YAML 工作流编排配置；A2A 协议工作流定义 |
| platformdirs | 4.9.6 | 跨平台路径 | 获取操作系统标准的配置/数据/缓存目录；本地优先架构的路径管理 |
| fsrs | 6.3.1 | FSRS 间隔重复算法 | 学习引擎的间隔重复核心；基于 FSRS v6 算法，Anki 生态验证 |
| watchdog | 6.0.0 | 文件系统监控 | Vault 目录变更监控，触发自动重新索引 |
| uvicorn | 0.46.0 | ASGI 服务器 | FastAPI 和 FastMCP 的运行时服务器 |
| pyarrow | 24.0.0 | 列式数据格式 | LanceDB 的底层依赖；向量和表格数据的列式存储 |
| Pygments | 2.20.0 | 代码语法高亮 | 代码摄入时的语言检测和高亮 |
| pygit2 | 1.19.2 | Git 操作 | Git blame 双溯源链的核心库；libgit2 的 Python 绑定 |
| APScheduler | 3.11.2 | 任务调度 | 知识新鲜度检查、定时过期扫描的后台调度器 |

### Development Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| pytest | 9.0.3 | 测试框架 | pytest-asyncio 用于异步测试；pytest-tmp-files 用于临时文件测试 |
| ruff | 0.15.12 | Linter + Formatter | 替代 flake8 + black + isort，Rust 实现，速度极快；统一代码风格 |
| hatchling | 1.29.0 | 构建后端 | pyproject.toml 构建系统；现代 Python 打包标准 |

---

## Installation

### Phase 1 & 2 (Core + Intelligence)

```bash
# 核心框架
pip install typer==0.24.2 fastapi==0.136.1 fastmcp==3.2.4 litellm==1.83.13

# 数据库
pip install sqlmodel==0.0.38 apsw==3.53.0.0 lancedb==0.30.2

# 文档处理
pip install docling==2.91.0 PyMuPDF==1.27.2 python-frontmatter==3.0.8 markdown-it-py==4.0.0
pip install beautifulsoup4==4.14.3 trafilatura==2.0.0

# AI/ML
pip install sentence-transformers==5.4.1 rank-bm25==0.2.2 faster-whisper==1.2.1 scikit-learn==1.8.0

# 安全与治理
pip install PyNaCl==1.6.2 cedar-python==0.1.4

# 图谱与算法
pip install networkx==3.6.1

# 通用工具
pip install pydantic==2.13.3 pydantic-settings==2.14.0 httpx==0.28.1 rich==15.0.0
pip install PyYAML==6.0.3 platformdirs==4.9.6 fsrs==6.3.1 watchdog==6.0.0
pip install uvicorn==0.46.0 pyarrow==24.0.0 pygit2==1.19.2 APScheduler==3.11.2

# 开发工具
pip install pytest==9.0.3 ruff==0.15.12 hatchling==1.29.0
```

### Phase 03 Additions (Collaboration + Web UI)

```bash
# Multi-Agent Orchestration
pip install langgraph==1.1.9 a2a-sdk==1.0.2

# Frontend (npm/pnpm)
npm create vite@latest saw-web -- --template react-ts
cd saw-web
npm install react@19 react-dom@19
npm install zustand@5.0.12 @tanstack/react-query@5.100.5
npm install cytoscape@3.33.2 react-cytoscapejs@2.0.0
npm install @milkdown/react@7.20.0 @milkdown/kit@7.20.0 @milkdown/theme-nord@7.20.0
npm install -D typescript@5 @types/react@19 @types/cytoscape@3
```

---

## Alternatives Considered

### Multi-Agent Orchestration

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| LangGraph | CrewAI | When you want role-based agent abstraction and don't need fine-grained state control |
| LangGraph | AutoGen | When conversation-centric multi-agent is primary use case |
| LangGraph | Custom State Machine | When requirements are simple enough to not need framework overhead |

### Web Frontend

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Zustand | Redux Toolkit | When team is already proficient with Redux or needs time-travel debugging |
| Zustand | Jotai | When atomic state model is preferred over store model |
| TanStack Query | SWR | When team prefers Vercel's simpler API |
| Cytoscape.js | React Flow (xyflow) | When building node-based editor UI rather than read-only graph |
| Cytoscape.js | D3.js | When building custom visualizations from scratch |
| Milkdown | TipTap | When more traditional rich text editor UX is preferred |
| Milkdown | Slate.js | When building completely custom editor from scratch |

### Policy Engine

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| cedar-python | Cedar CLI subprocess | When cedar-python bindings are insufficient or broken |
| cedar-python | Open Policy Agent (OPA) | When broader ecosystem integration needed (Kubernetes, etc.) |
| cedar-python | Custom Python rules | When policy complexity is low and Cedar is overkill |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| LangChain / LlamaIndex | Framework locking risk; abstract layer too thick; version updates frequently break compatibility | LiteLLM for model access, LangGraph for orchestration, self-built pipelines for control |
| Redux (for this use case) | Boilerplate overhead; Zustand sufficient for medium complexity; steeper learning curve | Zustand for client state, TanStack Query for server state |
| GraphQL | Overkill for single-tenant local-first app; REST + TanStack Query sufficient | FastAPI REST endpoints with automatic caching |
| MobX | Mutable state model; debugging complexity; less common in 2025 | Zustand immutable approach |
| Monaco Editor | VS Code-level editor is overkill for Markdown; heavier bundle | Milkdown for WYSIWYG Markdown |
| Recoil | Meta abandoned; uncertain future | Zustand |

---

## Stack Patterns by Variant

**纯本地模式 (默认):**
- SQLite + FTS5 做存储和搜索
- sentence-transformers 本地嵌入
- LanceDB 本地向量索引
- 无外部服务依赖，5 分钟可用

**本地 + 云 LLM 模式:**
- 保留 SQLite 本地存储
- LiteLLM 路由：简单任务用本地模型，复杂任务用云 API (Claude/GPT-4)
- 成本控制：Haiku 级跑量，Sonnet 级质量，Opus 级深度

**团队模式 (Phase 4):**
- PostgreSQL + pgvector 替代 SQLite + LanceDB
- Docker Compose 部署
- 多用户并发访问

**离线降级模式:**
- SQLite FTS5 + BM25 纯本地搜索
- 禁用向量搜索和 LLM 调用
- 保留基础摄入（Markdown/文本）和查询能力

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastMCP 3.2.4 | mcp>=1.24.0,<2.0 | FastMCP 内部封装官方 MCP SDK |
| FastMCP 3.2.4 | pydantic>=2.11.7 | 强制 Pydantic v2 |
| FastAPI 0.136.1 | pydantic>=2.0 | FastAPI 已全面支持 Pydantic v2 |
| SQLModel 0.0.38 | SQLAlchemy>=2.0 | SQLModel 依赖 SQLAlchemy 2.x |
| SQLModel 0.0.38 | pydantic>=2.0 | SQLModel 正在迁移到 Pydantic v2，注意 0.0.x 的 beta 状态 |
| LanceDB 0.30.2 | pyarrow>=16 | 向量存储依赖 PyArrow |
| LiteLLM 1.83.x | openai>=1.0 | LiteLLM 内部使用 OpenAI SDK 格式 |
| LangGraph 1.1.9 | langchain-core>=0.3 | LangGraph 需要 LangChain core components |
| React 19.2.5 | TypeScript 5.x | Full type support |
| Zustand 5.0.12 | React 18+ | Requires React hooks |
| TanStack Query 5.100.5 | React 18+ | Requires React hooks |
| Cytoscape.js 3.33.2 | react-cytoscapejs 2.0 | React wrapper version match |
| Milkdown 7.20.0 | React 18+ | First-class React integration |
| Python 3.11+ | 所有上述库 | 全部支持 Python 3.11, 3.12, 3.13 |

**已知兼容性风险:**
- SQLModel 0.0.x 仍然是 pre-release 版本，API 可能有 breaking changes；作为缓解措施，关键数据路径可直接使用 SQLAlchemy Core
- cedar-python 0.1.4 是非常早期的绑定，功能可能不完整；备选方案是直接子进程调用 Cedar CLI
- A2A SDK 1.0.2 是新协议，生态仍在发展；可能需要适配层与现有 FastMCP 集成

---

## Sources

### Phase 03 Sources

- **PyPI API** — Version verification: langgraph 1.1.9, cedar-python 0.1.4, zustand 5.0.12, tanstack/react-query 5.100.5, cytoscape 3.33.2, milkdown 7.20.0, react 19.2.5, a2a-sdk 1.0.2 — HIGH
- **Context7** — LangGraph orchestrator-worker pattern, Zustand store creation, Cedar WASM integration — HIGH
- **A2A Protocol GitHub** (github.com/google/A2A) — JSON-RPC 2.0 protocol, Agent Cards, SDK availability — HIGH
- **Cedar Policy Docs** (docs.cedarpolicy.com) — Policy syntax, Python bindings status — HIGH
- **Milkdown Docs** (milkdown.dev) — React integration, Crepe editor setup — HIGH
- **Cytoscape.js Docs** (js.cytoscape.org) — Graph initialization, react-cytoscapejs wrapper — HIGH

### Phase 1 & 2 Sources

- PyPI API (pypi.org/pypi/{package}/json) -- 所有版本号直接验证，2026-04-26
- FastMCP PyPI 页面 (pypi.org/project/fastmcp) -- 确认 PrefectHQ 维护、mcp SDK 封装关系、日下载百万次 -- HIGH
- MCP SDK PyPI (pypi.org/project/mcp) -- 确认官方 SDK 版本和依赖 -- HIGH
- FastMCP 文档 (gofastmcp.com) -- FastMCP 3.x 架构和功能确认 -- HIGH
- 项目设计文档 (docs/smart_agent_wiki_design.md) -- 技术选型上下文和约束条件
- 项目背景 (docs/llm_wiki_ecosystem_analysis.md) -- 181 项目生态分析，技术选型参考来源

---

*Stack research for: Smart Agent Wiki (智能多代理知识平台)*
*Phase 1 & 2: 2026-04-26*
*Phase 03 additions: 2026-04-27*
