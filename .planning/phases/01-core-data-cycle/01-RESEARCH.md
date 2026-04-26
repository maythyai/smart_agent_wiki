# Phase 1: Core Data Cycle - Research

**Researched:** 2026-04-26
**Domain:** Python CLI 知识管理平台 -- 四层存储 + 摄入管线 + 查询引擎
**Confidence:** HIGH

## Summary

Phase 1 是 Smart Agent Wiki 的基础数据循环：用户可以通过 `saw init` 创建知识库，通过 `saw ingest` 导入文档（Markdown/PDF/URL），通过 `saw query`/`saw search` 查询知识库，每条声明都可溯源到原始文档。核心架构决策已在 CONTEXT.md 中锁定：四层存储（Vault/Claims/Wiki/Index）、Write Queue Outbox 模式、六边形架构（Ports & Adapters）、FTS5 全文搜索、LiteLLM 多模型支持、三层降级策略。

技术栈研究基于项目前期已完成的 STACK.md（28 个包已验证版本）、ARCHITECTURE.md（六边形架构 + Outbox 模式详细设计）、PITFALLS.md（12 个领域陷阱）。Phase 1 需关注的关键风险点：FTS5 外部内容表一致性、Write Queue 孤儿消息恢复、PDF 解析静默失败、FTS5 segment b-tree 膨胀。所有核心库（Typer、SQLModel、LiteLLM、FastMCP、trafilatura、Docling）文档已通过 Context7 验证，版本号已通过 PyPI 交叉确认。

**Primary recommendation:** 先建立 domain 层（纯 Python Protocols）和 Write Queue，再实现 Ingest 引擎 + CLI 驱动器，最后实现 Query 引擎。确保 `saw init && saw ingest doc.md && saw query "..."` 在 5 分钟内可用。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 四层存储：Vault（不可变原件）-> Claims（SQLite）-> Wiki（Markdown+YAML）-> Index（FTS5）。六边形架构（Ports/Adapters）。
- **D-02:** SQLite 默认数据库，WAL 模式并发读写。SQLModel 简单 CRUD，SQLAlchemy Core 复杂查询（SQLModel 0.0.38 是 pre-release）。
- **D-03:** FTS5 `content=''`（外部内容模式）全文搜索。Phase 1 用 `unicode61` tokenizer（CJK jieba 自定义 tokenizer 延后）。
- **D-04:** Write Queue（Outbox）在 SQLite：单一持久入口 -> 并行分发到 Vault/Claims/Wiki/Index sinks。每个 sink 独立跟踪 `op_id` 去重。
- **D-05:** Vault 存储：`vault/` 下 UUID 目录，包含 `original.*`、`transcript.md`、`meta.yaml`。Git 跟踪，摄入后不可修改。
- **D-06:** Wiki 页面：Markdown + YAML frontmatter（type, tags, related, confidence, freshness, record_type）。5 种记录类型：SUMMARY/META/SOURCE/ALIAS/COLLECTION。
- **D-07:** 命名空间组织：`wiki/concepts/`、`wiki/entities/`、`wiki/sources/`、`wiki/collections/`。
- **D-08:** 格式检测 -> 结构化路径（AST/schema 解析，零 LLM）vs 非结构化路径（LLM 提取）。结构化提取用于代码、JSON、表格。
- **D-09:** PDF 解析：3 层降级 -- MinerU -> Docling -> PyMuPDF。前 5 页质量验证。
- **D-10:** 非结构化提取：Phase 1 使用单个 LLM（多 LLM 竞争延迟到 Phase 2）。使用 LiteLLM 可配置模型。
- **D-11:** 每次摄入创建 session 分支 `session/{timestamp}-{source_name}`，用于 git blame 双溯源。成功后合并到 main。
- **D-12:** 摄入输出：结构化 claims -> Claims DB，实体页面 -> Wiki 草稿，关系 -> Graph（SQLite JSONL），索引自动更新。
- **D-13:** BM25 + FTS5 主要搜索。Tree Mode（结构感知）用于层次化文档（锚点检索 -> 树遍历 -> 路径聚合）。
- **D-14:** 上下文编译：在 token 预算内组装相关 Wiki 页面。L0 始终加载索引（~85 行），L1 摘要（~15 主题），L2 按需完整内容。
- **D-15:** 自然语言查询通过 LLM：编译上下文 -> LLM 生成分层答案（L1-L4），带内联引用 `[^claim:uuid]`。
- **D-16:** 图遍历：SQLite 存储 + NetworkX BFS/DFS。轻量图存储为 JSONL edges。
- **D-17:** CLI 用 Typer 构建。命令：`init`、`ingest`、`query`、`search`、`status`。Rich 格式化输出。
- **D-18:** `saw init` 创建 `.saw/` 配置目录、SQLite DB、`vault/`、`wiki/`、初始化 Git 仓库。`--agent <name>` 生成 agent 特定配置。
- **D-19:** `saw status` 显示：页面数、声明数、存储大小、最近摄入、WIP 活跃任务。
- **D-20:** Git 集成：摄入和编辑时自动提交。每次摄入 session 分支后合并到 main。
- **D-21:** LiteLLM 多 LLM 支持。默认模型通过 `.saw/config.yaml` 配置。按任务复杂度路由模型。
- **D-22:** 三层降级：full（LLM+embeddings）-> lightweight（仅 LLM，BM25 搜索）-> offline（BM25+TF-IDF，零 LLM）。启动时自动检测。
- **D-23:** WIP 文件 `.saw/wip.yaml`：活跃任务、下一步、待解决问题。每次会话自动更新。
- **D-24:** Agent 兼容层：`saw init --agent <name>` 从共享模板生成 CLAUDE.md/.cursorrules/AGENTS.md/GEMINI.md。
- **D-25:** 默认本地优先。核心功能无需外部 API。LLM API 调用为可选。

### Claude's Discretion
- 确切 Python 项目结构（src layout vs flat）
- Typer 命令分组和子命令组织
- Claims DB schema 细节（超出核心字段）
- FTS5 索引重建策略
- 错误消息措辞和 CLI 输出格式
- 测试策略和覆盖率目标
- 配置文件格式细节（.saw/config.yaml schema）

### Deferred Ideas (OUT OF SCOPE)
- 多 LLM 竞争提取（2 个 LLM 交叉验证）-- 延迟到 Phase 2
- CJK 自定义 FTS5 tokenizer（jieba）-- 需要原型验证；先用 unicode61，后续升级
- 向量搜索 / embedding 支持 -- 延迟到 Phase 2（可选增强）
- Web UI -- Phase 3
- MCP Server（23 工具）-- Phase 2（Phase 1 仅 agent 兼容层 MCP-03）
- Chrome clipper、RSS、视频/音频摄入 -- Phase 4
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STOR-01 | `saw init` 创建 Vault、Claims DB、Wiki、Index 四层 | D-01/D-05/D-06/D-07 锁定目录结构；Typer `init` command + SQLite `create_engine` + FTS5 `CREATE VIRTUAL TABLE` |
| STOR-02 | 原始文档不可变存储在 Vault UUID 目录 | D-05 锁定 `vault/{uuid}/original.*` + `transcript.md` + `meta.yaml` |
| STOR-03 | 结构化知识声明存储在 Claims SQLite DB，含溯源 | D-02 SQLModel + D-04 Write Queue 保证原子写入 |
| STOR-04 | Wiki 页面为 Markdown + YAML frontmatter | D-06/D-07 锁定记录类型和命名空间 |
| STOR-05 | FTS5 全文索引自动构建和维护 | D-03 FTS5 外部内容模式 + D-04 Write Queue sink 自动更新 |
| STOR-06 | 每条声明溯源到 Vault 原始来源 | D-05 `source_uuid` + 页码/行号/时间戳定位 |
| STOR-07 | Write Queue (Outbox) 确保所有变更通过单一持久入口 | D-04 锁定 Outbox 模式 + per-sink 跟踪 + op_id 去重 |
| INGE-01 | Markdown 文件摄入 + LLM 提取实体/概念/声明 | python-frontmatter 解析 + markdown-it-py AST + LiteLLM 提取 |
| INGE-02 | PDF 摄入 3 层降级解析（MinerU -> Docling -> PyMuPDF） | D-09 锁定降级策略；Docling 2.91.0 主力，PyMuPDF 1.27.2 兜底 |
| INGE-03 | URL 网页摄入 + 内容提取 | trafilatura 2.0.0 `fetch_url` + `extract` 模式 [VERIFIED: Context7] |
| INGE-04 | 结构化数据（代码/JSON/表格）AST/schema 解析零 LLM | D-08 锁定结构化路径；markdown-it-py + 自定义 AST 解析 |
| INGE-05 | 非结构化数据 2 个独立 LLM 交叉验证 | D-10 限制为 Phase 1 单 LLM；交叉验证延迟到 Phase 2 |
| INGE-06 | 摄入产出：结构化 claims -> Claims DB、实体页面 -> Wiki 草稿、Graph 更新 | D-12 锁定输出管线 + D-04 Write Queue 多 sink 分发 |
| INGE-07 | 每次摄入创建 session 分支 git blame 双溯源 | D-11/D-20 锁定 `session/{timestamp}-{source_name}` 分支策略 |
| QUER-01 | BM25 + FTS5 全文搜索 | D-13 锁定；FTS5 `bm25()` 排名函数 + rank-bm25 0.2.2 辅助 |
| QUER-02 | 结构感知 Tree Mode 搜索 | D-13 锁定锚点检索 -> 树遍历 -> 路径聚合；markdown-it-py 提供标题层级 |
| QUER-03 | 自然语言查询 + 分层答案（L1-L4） | D-15 锁定 LiteLLM + `[^claim:uuid]` 内联引用 |
| QUER-04 | 上下文编译在 token 预算内组装相关页面 | D-14 锁定 L0/L1/L2 分层 + token 预算过滤 |
| QUER-05 | 查询结果含内联引用链接到具体 claims 和 Vault 来源 | D-15 `[^claim:uuid]` 引用格式 + D-06 source_uuid 溯源链 |
| QUER-06 | 图遍历 BFS/DFS 实体关系探索 | D-16 NetworkX 3.6.1 BFS/DFS + SQLite JSONL edges 存储 |
| QUER-07 | 比较分析两个或多个 Wiki 页面的异同 | D-15 LLM 对比生成 + D-14 上下文编译多页面组装 |
| CLI-01 | `saw init` 创建空 wiki | Typer 0.24.2 `@app.command()` + Rich 15.0.0 格式化 [VERIFIED: Context7] |
| CLI-02 | `saw ingest <source>` 摄入文档/URL/目录 | Typer 多类型参数 + Ingest 引擎管线 |
| CLI-03 | `saw query <question>` 自然语言查询 | Typer + Query 引擎 + LiteLLM |
| CLI-04 | `saw search <keywords>` BM25/FTS5 搜索 | Typer + FTS5 `MATCH` 查询 |
| CLI-07 | `saw status` 知识库概览 | D-19 页面数/声明数/存储大小/最近摄入/WIP |
| MCP-03 | Agent 兼容层：`saw init --agent <name>` 生成配置 | D-24 共享模板 -> CLAUDE.md/.cursorrules/AGENTS.md/GEMINI.md |
| XCUT-01 | Git 自动提交 + session 分支跟踪 | D-20/D-11 pygit2 1.19.2 + subprocess git |
| XCUT-02 | LiteLLM 多 LLM 支持统一接口 | D-21 LiteLLM 1.83.13 Router + fallback/retry [VERIFIED: Context7] |
| XCUT-03 | 三层降级确保系统可用 | D-22 启动时自动检测能力 -> full/lightweight/offline |
| XCUT-04 | WIP 文件捕获跨会话工作动量 | D-23 `.saw/wip.yaml` 活跃任务/下一步/待解决问题 |
| XCUT-07 | 默认本地优先零外部依赖 | D-25 核心功能无外部 API 要求 |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI 命令解析与输出 | Browser/Client (CLI) | -- | Typer 驱动器是用户入口，负责参数解析和 Rich 输出 |
| 格式检测与路由 | API/Backend (Engine) | -- | Ingest 引擎核心业务逻辑，不依赖任何驱动器 |
| PDF/Markdown/URL 解析 | API/Backend (Adapter) | -- | 解析器是基础设施适配器，可替换 |
| LLM 调用（声明提取、回答生成） | API/Backend (Adapter) | -- | LiteLLM 适配器统一封装，引擎通过 Protocol 调用 |
| 写入持久化 | Database/Storage | -- | Write Queue -> 多 Sink 是存储层核心职责 |
| 全文搜索 | Database/Storage (FTS5) | -- | SQLite FTS5 内置搜索引擎 |
| 知识图谱遍历 | Database/Storage (SQLite+NetworkX) | -- | JSONL edges 持久化在 SQLite，NetworkX 内存图计算 |
| Git 版本控制 | CDN/Static (文件系统) | -- | Vault 和 Wiki 是文件系统上的 Git 仓库 |
| 配置管理 | Database/Storage (.saw/) | -- | YAML 配置文件 + SQLite 元数据 |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | 核心语言 | AI 生态一等公民；3.11+ exception groups、TOML 读取 [VERIFIED: env 3.12.3] |
| Typer | 0.24.2 | CLI 框架 | 类型注解驱动 CLI 生成，Rich 集成美化输出 [VERIFIED: PyPI] |
| SQLModel | 0.0.38 | ORM 层 | SQLAlchemy + Pydantic 统一，简单 CRUD；复杂查询用 SQLAlchemy Core [VERIFIED: PyPI, pre-release] |
| LiteLLM | 1.83.13 | LLM 统一接入 | 100+ provider 统一接口，内置 retry/fallback/速率限制 [VERIFIED: PyPI + Context7] |
| NetworkX | 3.6.1 | 知识图谱 | 纯 Python 图计算，零外部依赖，<100K 节点性能足够 [VERIFIED: PyPI] |
| Pydantic | 2.13.3 | 数据验证 | 所有 schema、配置模型基础 [VERIFIED: PyPI] |
| Pydantic Settings | 2.14.0 | 配置管理 | 环境变量 + .env + 嵌套配置统一管理 [VERIFIED: PyPI] |
| Rich | 15.0.0 | 终端美化 | Typer 内置集成，进度条/表格/语法高亮 [VERIFIED: PyPI] |

### Document Processing

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Docling | 2.91.0 | PDF 智能解析 | IBM 开源，支持 PDF/DOCX/PPTX/HTML/图片，统一输出格式 [VERIFIED: PyPI] |
| PyMuPDF | 1.27.2 | PDF 基础解析（降级备选） | 最轻量 PDF 解析，纯文本 PDF 效果好，速度极快 [VERIFIED: PyPI] |
| python-frontmatter | 1.1.0 | Markdown YAML frontmatter 解析 | 解析 Markdown 文件元数据 [VERIFIED: PyPI, note: version differs from STACK.md 3.0.8] |
| markdown-it-py | 4.0.0 | Markdown AST 解析 | CommonMark 兼容，可扩展插件系统 [VERIFIED: PyPI from STACK.md] |
| trafilatura | 2.0.0 | Web 内容提取 | 从 URL 提取正文，自动去除导航/广告/侧边栏 [VERIFIED: PyPI + Context7] |
| BeautifulSoup4 | 4.14.3 | HTML 解析 | trafilatura 底层 + URL 抓取后清理 [VERIFIED: STACK.md] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rank-bm25 | 0.2.2 | BM25 算法 | 与 FTS5 互补用于混合搜索评分 |
| PyYAML | 6.0.3 | YAML 处理 | .saw/config.yaml、wip.yaml、meta.yaml 读写 |
| platformdirs | 4.9.6 | 跨平台路径 | .saw/ 配置目录定位 |
| pygit2 | 1.19.2 | Git 操作 | git blame 双溯源链；session 分支创建/合并 [VERIFIED: PyPI] |
| httpx | 0.28.1 | HTTP 客户端 | URL 抓取、API 调用 |
| hatchling | 1.29.0 | 构建后端 | pyproject.toml 打包 |

### Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 9.0.3 | 测试框架 |
| ruff | 0.15.12 | Linter + Formatter |

### Version Discrepancy Note

python-frontmatter 在 STACK.md 中记录为 3.0.8，但 PyPI 最新版本为 1.1.0。STACK.md 版本可能来源于其他渠道或笔误。以 PyPI 验证为准：使用 1.1.0。如果需要 YAML frontmatter 高级功能，可考虑 `markdown-frontmatter` 或直接用 PyYAML 解析。

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLModel 0.0.38 | SQLAlchemy Core only | SQLModel 提供类型安全 + Pydantic 统一；但 beta 状态意味着 API 可能变化。复杂查询路径直接用 Core 是安全网 |
| Docling (主力 PDF) | PyMuPDF only | Docling 质量更高但依赖链重（2-3GB）；PyMuPDF 轻量但复杂版面效果差。3 层降级策略平衡了两者 |
| Typer CLI | Click | Click 更成熟；但 Typer 类型注解驱动开发效率更高，与 FastAPI 风格统一 |

**Installation:**
```bash
# 核心框架
pip install typer==0.24.2 sqlmodel==0.0.38 litellm==1.83.13 networkx==3.6.1
pip install pydantic==2.13.3 pydantic-settings==2.14.0 rich==15.0.0

# 文档处理
pip install docling==2.91.0 PyMuPDF==1.27.2 python-frontmatter==1.1.0
pip install markdown-it-py==4.0.0 trafilatura==2.0.0 beautifulsoup4==4.14.3

# 搜索
pip install rank-bm25==0.2.2

# 工具
pip install PyYAML==6.0.3 platformdirs==4.9.6 pygit2==1.19.2 httpx==0.28.1

# 开发
pip install pytest==9.0.3 ruff==0.15.12 hatchling==1.29.0
```

## Architecture Patterns

### System Architecture Diagram

```
+====================================================================+
|                    Driving Adapters (Phase 1)                        |
|          CLI (Typer + Rich)  |  Agent Compat Layer (MCP-03)         |
+==============+================+=====================================+
               |                |
+==============v================v=====================================+
|                    Composition Root (DI Container)                   |
|    Initializes engines with protocol-injected adapters               |
+==============+================+=====================================+
               |                |
+==============v================v=====================================+
|                    Engines (Pure Business Logic)                     |
|   +----------------+   +----------------+                           |
|   | Ingest Engine  |   | Query Engine   |                           |
|   | (pipeline,     |   | (search,       |                           |
|   |  classifier,   |   |  compiler,     |                           |
|   |  extractors,   |   |  graph,        |                           |
|   |  fuser)        |   |  compare)      |                           |
|   +-------+--------+   +-------+--------+                           |
+===========|======================|==================================+
            |                      |
+===========v======================v==================================+
|                    Write Queue (Outbox Pattern)                      |
|    SQLite Outbox -> Parallel Dispatch -> Per-Sink Tracking           |
+===+===========+============+===========+=============+===============+
    |           |            |           |             |
+---v---+ +-----v------+ +--v-------+ +-v---------+ +-v-----------+
|Vault  | |Claims DB   | |Wiki Pages| |FTS5 Index | |Graph (JSONL)|
|(Git)  | |(SQLite)    | |(Markdown)| |(SQLite)   | |(SQLite)     |
+-------+ +------------+ +----------+ +-----------+ +-------------+
    |           |            |           |             |
    +-----------+------------+-----------+-------------+
                           |
                    Git Auto-Commit
                  (session branches)
```

### Recommended Project Structure

```
smart_agent_wiki/
+-- src/saw/
|   +-- domain/                        # 纯 Python Protocols + 值对象
|   |   +-- protocols.py               # Engine 接口协议定义
|   |   +-- value_objects.py           # ClaimRef, WikiPageRef, Confidence 等值对象
|   |   +-- events.py                  # 领域事件
|   |   +-- exceptions.py              # 领域异常
|   |   +-- claims.py                  # Claim 实体模型
|   |   +-- wiki.py                    # WikiPage, PageType 模型
|   |   +-- entities.py                # Entity, EntityRelation 模型
|   +-- engines/
|   |   +-- ingest/
|   |   |   +-- pipeline.py            # IngestPipeline 主编排器
|   |   |   +-- classifier.py          # 格式检测（AST/schema/text/PDF）
|   |   |   +-- extractors/
|   |   |   |   +-- markdown.py        # Markdown 提取器
|   |   |   |   +-- pdf.py             # PDF 3 层降级解析
|   |   |   |   +-- url.py             # Web 内容提取（trafilatura）
|   |   |   |   +-- code_ast.py        # 零 LLM AST 提取
|   |   |   +-- fuser.py               # 新旧 claim 比较与融合
|   |   |   +-- validator.py           # 去重、完整性校验
|   |   +-- query/
|   |       +-- engine.py              # QueryEngine 主引擎
|   |       +-- search.py              # BM25 + FTS5 搜索
|   |       +-- compiler.py            # 上下文编译 + token 预算
|   |       +-- graph_traverse.py      # NetworkX BFS/DFS
|   |       +-- compare.py             # 多页面比较
|   +-- write_queue/
|   |   +-- queue.py                   # WriteQueue Protocol + SQLite Outbox
|   |   +-- dispatcher.py              # 并行 sink 分发 + 重试
|   |   +-- sinks/
|   |       +-- vault_sink.py          # 文件系统 + git commit
|   |       +-- claims_sink.py         # Claims DB 写入
|   |       +-- wiki_sink.py           # Markdown 文件写入
|   |       +-- fts5_sink.py           # FTS5 索引更新
|   |       +-- graph_sink.py          # JSONL edges 写入
|   +-- adapters/
|   |   +-- storage/
|   |   |   +-- sqlite_connection.py   # SQLite 连接池 + WAL + PRAGMA
|   |   |   +-- claims_repository.py   # Claims DB CRUD + 复杂查询
|   |   |   +-- vault_repository.py    # Vault 文件操作
|   |   |   +-- wiki_repository.py     # Wiki 页面读写
|   |   +-- llm/
|   |   |   +-- router.py              # LiteLLM 模型路由
|   |   |   +-- prompts/               # YAML prompt 模板
|   |   +-- parsers/
|   |       +-- pdf_parser.py          # 3 层降级：Docling -> PyMuPDF
|   |       +-- markdown_parser.py     # frontmatter + markdown-it-py
|   |       +-- html_parser.py         # BeautifulSoup4 + trafilatura
|   +-- drivers/
|   |   +-- cli/
|   |       +-- main.py                # Typer app 入口
|   |       +-- commands/
|   |           +-- init_cmd.py        # saw init
|   |           +-- ingest_cmd.py      # saw ingest
|   |           +-- query_cmd.py       # saw query
|   |           +-- search_cmd.py      # saw search
|   |           +-- status_cmd.py      # saw status
|   +-- config/
|       +-- settings.py                # Pydantic Settings (.saw/config.yaml)
|       +-- defaults.py                # 默认配置值
|       +-- agent_templates.py         # Agent 兼容层模板
+-- tests/
|   +-- unit/                          # 引擎单元测试（mocked adapters）
|   +-- integration/                   # 多引擎集成测试
|   +-- e2e/                           # CLI 端到端测试
|   +-- fixtures/                      # 样本文档、期望 claims
+-- pyproject.toml
```

### Pattern 1: Hexagonal Architecture (Ports and Adapters)

**What:** 核心领域（engines + protocols）无外部系统知识。所有 I/O 通过适配器接口。驱动器（CLI）向内调用，被驱动适配器（storage/LLM/parsers）向外被调用。

**When to use:** 整个系统。多个入口点（CLI + 后续 MCP/Web）共享引擎逻辑；多个存储后端（SQLite + 后续 PostgreSQL）需要隔离替换。

**Example:**
```python
# domain/protocols.py -- Port 定义
from typing import Protocol

class ClaimsRepository(Protocol):
    def get_by_id(self, uuid: str) -> Claim | None: ...
    def insert(self, claim: Claim) -> str: ...
    def search(self, query: str, limit: int) -> list[Claim]: ...

class WriteQueue(Protocol):
    def enqueue(self, ops: list[WriteOp]) -> None: ...
    def enqueue_atomic(self, ops: list[WriteOp]) -> None: ...

# adapters/storage/claims_repository.py -- Adapter 实现
import sqlite3

class SQLiteClaimsRepository:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(str(db_path))
    def get_by_id(self, uuid: str) -> Claim | None:
        row = self._conn.execute(
            "SELECT * FROM claim WHERE uuid=?", (uuid,)
        ).fetchone()
        return Claim.from_row(row) if row else None

# engines/ingest/pipeline.py -- Engine 依赖 Protocol
class IngestPipelineImpl:
    def __init__(self, claims: ClaimsRepository, queue: WriteQueue):
        self._claims = claims
        self._queue = queue
```

### Pattern 2: Write Queue / Outbox Pattern

**What:** 所有存储变更通过单一 Write Queue。引擎将写入操作入队到持久 SQLite outbox 表。Dispatcher 取出待处理操作并并行分发到多个 sink。每个 sink 独立重试。

**When to use:** 任何写入多个存储位置且不能丢失的场景。每次摄入至少写入 3 个 sink（Vault + Claims + FTS5）。

**Example:**
```python
# write_queue/queue.py
@dataclass
class WriteOp:
    op_id: str           # UUID, 用于去重
    session_id: str      # 关联写入组
    sink_name: str       # "vault" | "claims" | "fts5" | ...
    payload: dict        # sink 特定数据
    status: str          # "pending" | "dispatched" | "done" | "failed"

class WriteQueueImpl:
    def enqueue(self, ops: list[WriteOp]) -> None:
        """原子性插入所有操作。全有或全无。"""
        with self._conn:
            for op in ops:
                self._conn.execute(
                    "INSERT INTO write_outbox "
                    "(op_id, session_id, sink_name, payload, status) "
                    "VALUES (?, ?, ?, ?, 'pending')",
                    (op.op_id, op.session_id, op.sink_name,
                     json.dumps(op.payload))
                )
```

### Pattern 3: Three-Tier Degradation

**What:** 系统在三种能力级别运行：full（LLM + embeddings + vector）、lightweight（仅 LLM + BM25）、offline（BM25 + TF-IDF，零 LLM）。启动时自动检测。

**When to use:** 个人知识工具的用户可能在飞机上、弱网环境或资源受限机器上使用。系统必须优雅降级而非失败。

**Example:**
```python
# config/settings.py
from enum import IntEnum

class CapabilityTier(IntEnum):
    FULL = 3        # LLM + embeddings + vector
    LIGHTWEIGHT = 2 # LLM + BM25 only
    OFFLINE = 1     # BM25 + TF-IDF only

def detect_tier() -> CapabilityTier:
    tier = CapabilityTier.OFFLINE  # 基础能力
    if _llm_available():
        tier = CapabilityTier.LIGHTWEIGHT
    if _embeddings_available():
        tier = CapabilityTier.FULL
    return tier
```

### Pattern 4: Session Branch Git Provenance

**What:** 每次摄入创建 `session/{timestamp}-{source_name}` Git 分支。摄入完成后合并到 main。git blame 提供 wiki 编辑到处理会话的追溯链。

**Example:**
```python
# adapters/storage/vault_repository.py
import subprocess
from datetime import datetime

class VaultRepository:
    def create_session_branch(self, source_name: str) -> str:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        branch = f"session/{ts}-{source_name}"
        subprocess.run(["git", "checkout", "-b", branch], check=True)
        return branch

    def merge_session(self, branch: str) -> None:
        subprocess.run(["git", "checkout", "main"], check=True)
        subprocess.run(["git", "merge", "--no-ff", branch], check=True)
```

### Anti-Patterns to Avoid

- **Engine 直接 import 另一个 Engine：** 引擎间通过 Protocol 通信或 Event Bus，不直接 import。测试隔离性依赖此边界。
- **绕过 Write Queue 直接写存储：** 任何"只是一次写入"的捷径都会破坏崩溃恢复和审计链。
- **每个代码路径都调 LLM：** 结构化数据用 AST/schema 零 LLM；搜索用 BM25/TF-IDF；策略用 Cedar 规则。LLM 仅用于非结构化文本提取和查询回答。
- **SQLite PRAGMA 忽略：** 无 WAL 模式 = 并发读写阻塞；无 mmap = 大结果集慢。必须从第一天配置正确 PRAGMA。
- **God Engine：** Ingest 不应包含搜索、置信度评估或 wiki 生成逻辑。五引擎职责严格分离。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF 解析 | 自写 PDF 文本提取 | Docling + PyMuPDF | PDF 格式复杂性：多栏、表格、公式、扫描 OCR。Docling 处理版面分析，PyMuPDF 处理纯文本 |
| Web 内容提取 | 正则表达式清理 HTML | trafilatura | 自动去除导航/广告/侧边栏，正文提取准确率高 [VERIFIED: Context7] |
| LLM 调用统一 | 自写 provider 适配器 | LiteLLM | 100+ provider 统一接口，内置 retry/fallback/速率限制/成本追踪 [VERIFIED: Context7] |
| CLI 框架 | 自写参数解析 | Typer | 类型注解驱动 CLI 生成，Rich 集成，自动补全 [VERIFIED: Context7] |
| BM25 搜索算法 | 自写 TF-IDF 排名 | SQLite FTS5 + rank-bm25 | FTS5 是 C 实现内置 SQLite，rank-bm25 是纯 Python 验证过的 BM25 实现 |
| YAML 解析 | 自写 YAML 解析器 | PyYAML + python-frontmatter | YAML 规范复杂；frontmatter 解析有边界情况 |
| Markdown AST | 正则表达式解析 Markdown | markdown-it-py | CommonMark 规范兼容，标题层级、代码块、表格等结构提取 |
| 配置管理 | 自写 .env/config 解析 | Pydantic Settings | 类型验证、嵌套配置、环境变量覆盖、默认值 |
| Git 操作 | 自写 Git 命令封装 | pygit2 | libgit2 绑定，提供 git blame、分支操作等底层 API |
| 图遍历 | 自写 BFS/DFS | NetworkX | 纯 Python、零外部依赖、BFS/DFS/PageRank 等算法开箱即用 |
| ORM / 数据库 | 原生 SQL 字符串拼接 | SQLModel + SQLAlchemy Core | 参数化查询防注入，类型安全，迁移管理 |

**Key insight:** Phase 1 的所有基础设施问题都有成熟的 Python 库解决方案。核心创新不在基础设施层，而在领域层：四层存储、声明溯源、写入队列、三层降级。应将工程时间投资在领域逻辑而非重复造轮子。

## Common Pitfalls

### Pitfall 1: FTS5 外部内容表不一致

**What goes wrong:** FTS5 `content=''` 模式下，内容表更新但 FTS5 索引未更新（或反之），查询返回过期或缺失结果。FTS5 文档明确警告："It is the responsibility of the user to ensure that the content table and the FTS5 index are consistent." [CITED: sqlite.org/fts5.html]

**Why it happens:** Write Queue 写入 Wiki Pages sink 成功但 FTS5 sink 失败或延迟。FTS5 索引不反映新内容。

**How to avoid:**
1. 所有写入通过 Write Queue，per-sink 完成跟踪
2. `saw status` 检查内容表 vs FTS5 表行数一致性
3. 一致性不匹配时触发 `INSERT INTO fts_index(fts_index) VALUES('rebuild')`
4. 关键操作中，内容表 + FTS5 更新在同一 SQLite 事务中

**Warning signs:** `saw search` 返回少于预期的结果；内容表和 FTS5 表行数不匹配

### Pitfall 2: Write Queue 孤儿消息

**What goes wrong:** 系统在写入部分 sink 后崩溃。重启后 6 个 sink 的 2^6 = 64 种部分完成状态。没有幂等 sink 则重试产生重复，没有 per-sink 跟踪则丢失写入。

**How to avoid:**
1. 每个 outbox 消息有唯一 op_id，每个 sink 跟踪最后处理的消息 ID
2. Sink 幂等：Vault 用内容寻址（hash = ID），Claims DB 用 `INSERT OR IGNORE` + UUID PK
3. 每消息状态机：`PENDING -> PROCESSING -> [SINK_OK, ...] -> COMPLETED`
4. Vault 先写（source of truth），Git commit 最后写

**Warning signs:** `saw status` 显示 PROCESSING 状态消息；Vault 文件数和 Claims 记录数不匹配

### Pitfall 3: FTS5 Segment B-Tree 膨胀

**What goes wrong:** FTS5 每次写入事务创建新 segment b-tree。无合并则查询性能随 segment 数线性退化。`automerge` 仅在写入时触发，`crisismerge` 默认阈值 16 太高。 [CITED: sqlite.org/fts5.html]

**How to avoid:**
1. 设置 `automerge=8`、`crisismerge=4`：`INSERT INTO fts_index(fts_index, rank) VALUES('automerge', 8)`
2. 批量写入：Write Queue 积累后批量 flush 到 FTS5
3. 重度摄入后调用 `INSERT INTO fts_index(fts_index) VALUES('optimize')`
4. `detail=column`（牺牲 NEAR/phrase 查询换取一半索引大小）-- 需在 CREATE TABLE 时决定

**Warning signs:** `saw search` 超过 500ms；FTS5 segment 数超过 50

### Pitfall 4: PDF 解析静默失败

**What goes wrong:** PDF 被成功解析但提取文本丢失 20% 内容（表格、公式、多栏布局）。解析报告成功但提取文本不完整。错误数据流入 Claims 提取。

**How to avoid:**
1. 解析后计算质量指标：字符数、词数、段落数。与 PDF 元数据（页数、文件大小）比较
2. 提取词数 < 预期 50% 时标记为低质量
3. Vault `meta.yaml` 记录 `parser: docling` 或 `parser: pymupdf`，下游可据此调整置信度
4. 对长文档提供用户审核提取文本的选项

**Warning signs:** 提取文本包含乱码；claim 提取产生异常高的"模糊"源标记；用户反馈 claim 与原始 PDF 矛盾

### Pitfall 5: SQLModel 0.0.x API 变化

**What goes wrong:** SQLModel 仍是 pre-release，API 可能有 breaking changes。复杂查询可能触及未测试路径。

**How to avoid:**
1. 简单 CRUD 用 SQLModel（类型安全 + Pydantic 统一）
2. 复杂查询直接用 SQLAlchemy Core（`select()`, `where()`, `func`）
3. 关键数据路径（Claims repository）准备 Core 回退实现
4. 锁定 SQLModel 版本，升级前在测试套件中验证

**Warning signs:** SQLModel 升级后测试失败；复杂查询返回意外结果

### Pitfall 6: LiteLLM 阻塞调用在异步上下文

**What goes wrong:** 在 FastAPI/MCP 的 async handler 中调用 `litellm.completion()`（同步），阻塞事件循环，所有请求排队。

**How to avoid:** 始终使用 `await litellm.acompletion()` 异步调用 [VERIFIED: Context7]。Phase 1 CLI 是同步的所以暂时不是问题，但代码应为 Phase 2 MCP 准备好异步接口。

**Warning signs:** 并发请求时延迟线性增长；事件循环阻塞告警

## Code Examples

### Typer CLI 应用结构

```python
# drivers/cli/main.py
import typer
from rich.console import Console

app = typer.Typer(
    name="saw",
    help="Smart Agent Wiki - 智能多代理知识平台",
    no_args_is_help=True,
)
console = Console()

# 使用 app.add_typer() 组织子命令
# [VERIFIED: Context7 /websites/typer_tiangolo]

@app.callback()
def main():
    """Smart Agent Wiki CLI"""
    pass

# drivers/cli/commands/init_cmd.py
from typer import Typer
init_app = Typer(help="初始化知识库")

@init_app.command()
def init(
    path: str = typer.Argument(".", help="Wiki 目录路径"),
    agent: str | None = typer.Option(None, "--agent", help="Agent 兼容层: claude-code, cursor, copilot, gemini"),
):
    """创建空 wiki 并初始化所有存储层"""
    from saw.config.settings import WikiSettings
    settings = WikiSettings(path=path, agent=agent)
    # 初始化 .saw/, vault/, wiki/, SQLite DB, Git repo
    ...
```

### SQLModel + SQLite 连接配置

```python
# adapters/storage/sqlite_connection.py
from sqlmodel import create_engine, Session
from pathlib import Path

def create_wiki_engine(db_path: Path):
    """创建优化配置的 SQLite 引擎"""
    url = f"sqlite:///{db_path}"

    def _set_pragma(conn):
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")      # 并发读写
        cursor.execute("PRAGMA cache_size=-64000")      # 64MB 缓存
        cursor.execute("PRAGMA mmap_size=67108864")     # 64MB mmap
        cursor.execute("PRAGMA synchronous=NORMAL")     # 平衡安全与性能
        cursor.execute("PRAGMA busy_timeout=5000")      # 5s 锁等待
        cursor.execute("PRAGMA foreign_keys=ON")        # 外键约束

    engine = create_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # SQLAlchemy 2.x event system for PRAGMA
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        _set_pragma(dbapi_connection)

    return engine
# [VERIFIED: Context7 /websites/sqlmodel_tiangolo]
```

### FTS5 索引创建与查询

```python
# Claims DB schema 包含 FTS5 虚拟表
FTS5_CREATE = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
USING fts5(
    title,
    content,
    tags,
    content='',                -- 外部内容模式
    tokenize='unicode61',      -- Phase 1: 英文优先
    detail=column              -- 牺牲 NEAR/phrase 换取性能
);

-- 设置 segment 合并策略
INSERT INTO fts_index(fts_index, rank) VALUES('automerge', 8);
INSERT INTO fts_index(fts_index, rank) VALUES('crisismerge', 4);
"""

# 搜索查询
def search_claims(conn, query: str, limit: int = 10):
    """BM25 排名全文搜索"""
    results = conn.execute("""
        SELECT
            wiki_id, title, content, tags,
            bm25(fts_index) as rank
        FROM fts_index
        WHERE fts_index MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit)).fetchall()
    return results
# [CITED: sqlite.org/fts5.html]
```

### Write Queue Outbox 模式

```python
# write_queue/queue.py
import uuid
import json
from datetime import datetime, timezone

class WriteOp:
    def __init__(self, sink_name: str, payload: dict, session_id: str):
        self.op_id = str(uuid.uuid4())
        self.session_id = session_id
        self.sink_name = sink_name
        self.payload = payload
        self.status = "pending"
        self.created_at = datetime.now(timezone.utc).isoformat()

class SQLiteWriteQueue:
    def __init__(self, conn):
        self._conn = conn
        self._create_table()

    def _create_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS write_outbox (
                op_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                sink_name TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                retry_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(op_id)
            )
        """)

    def enqueue(self, ops: list[WriteOp]) -> None:
        """原子性入队所有操作"""
        with self._conn:
            for op in ops:
                self._conn.execute(
                    "INSERT INTO write_outbox "
                    "(op_id, session_id, sink_name, payload, status, created_at) "
                    "VALUES (?, ?, ?, ?, 'pending', ?)",
                    (op.op_id, op.session_id, op.sink_name,
                     json.dumps(op.payload), op.created_at)
                )
```

### Trafilatura URL 内容提取

```python
# adapters/parsers/html_parser.py
from trafilatura import fetch_url, extract

def extract_from_url(url: str) -> dict:
    """从 URL 提取正文内容"""
    downloaded = fetch_url(url)
    if not downloaded:
        raise ValueError(f"Failed to fetch URL: {url}")

    # 提取正文 + 元数据
    result = extract(downloaded, include_links=True, include_tables=True)

    return {
        "url": url,
        "content": result,
        "format": "html",
    }
# [VERIFIED: Context7 /adbar/trafilatura]
```

### LiteLLM 模型路由

```python
# adapters/llm/router.py
import litellm
from saw.config.settings import LLMSettings

class LLMRouter:
    def __init__(self, settings: LLMSettings):
        self._settings = settings

    async def extract_claims(self, text: str, system_prompt: str) -> dict:
        """使用配置的提取模型提取 claims"""
        response = await litellm.acompletion(
            model=self._settings.extraction_model,  # e.g. "claude-3-sonnet"
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,  # 低温度确保稳定输出
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def answer_query(self, context: str, question: str) -> str:
        """使用配置的查询模型回答问题"""
        response = await litellm.acompletion(
            model=self._settings.query_model,  # e.g. "gpt-4o"
            messages=[
                {"role": "system", "content": "..."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
        )
        return response.choices[0].message.content
# [VERIFIED: Context7 /berriai/litellm]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Click CLI | Typer 类型注解 CLI | Typer 0.9+ (2023) | 减少 60% 样板代码，类型安全，与 FastAPI 风格统一 |
| PyMuPDF only PDF | Docling 智能解析 | Docling 2.x (2024) | 版面分析、OCR、多格式支持；PyMuPDF 降级为兜底 |
| raw SQL strings | SQLModel ORM | SQLModel 0.0.22+ | Pydantic + SQLAlchemy 统一，但仍在 beta |
| 全局 LLM 配置 | LiteLLM Router 路由 | LiteLLM 1.x | 按任务复杂度路由不同模型，成本优化 |
| ChromaDB 默认 | LanceDB 嵌入式 | LanceDB 0.3+ (2024) | 零服务器进程，本地优先架构更友好 |
| newspaper3k | trafilatura | newspaper3k 停维 2019 | 更可靠的正文提取，活跃维护 |
| sqlite3 标准 FTS | FTS5 + automerge | SQLite 3.9+ (2015) | BM25 排名、snippet/highlight、segment 合并 |

**Deprecated/outdated:**
- newspaper3k: 停维，现代网站解析效果差 -> 使用 trafilatura
- Whoosh: 停维 2017，纯 Python 性能差 -> 使用 SQLite FTS5
- FAISS 直接使用: 安装复杂，API 不够 Pythonic -> LanceDB 封装（Phase 2）
- dataclasses 做数据验证: 无嵌套验证/序列化 -> Pydantic v2

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | python-frontmatter 正确版本是 1.1.0（STACK.md 记录 3.0.8 可能是笔误） | Standard Stack | 如果 3.0.8 确实存在且有 API 变化，可能需要调整代码 |
| A2 | MinerU PDF 解析器在 Phase 1 可作为可选依赖（Docling 主力） | Pitfall 4 | MinerU 依赖链重（PaddleOCR），安装可能失败 |
| A3 | Phase 1 `unicode61` tokenizer 对英文内容足够；CJK 用户可接受延迟到 Phase 2 | D-03 | 如果 Phase 1 就有大量中文内容摄入，搜索质量会差 |
| A4 | SQLite 单文件数据库足够应对个人用户（<1K 页面、<50K claims） | Architecture | 如果超出规模需要迁移到 PostgreSQL |
| A5 | pygit2 在目标平台可用（需要 libgit2 系统依赖） | Code Examples | 如果 libgit2 不可用，需回退到 subprocess git 命令 |
| A6 | Docling 2.91.0 的 API 稳定且文档充分 | Standard Stack | Docling 快速迭代，API 可能变化 |

## Open Questions

1. **python-frontmatter 版本不一致**
   - What we know: STACK.md 记录 3.0.8，PyPI 最新 1.1.0
   - What's unclear: 是否存在不同包名或分支
   - Recommendation: 使用 PyPI 验证版本 1.1.0；如果需要高级 frontmatter 功能，直接用 PyYAML 解析

2. **FTS5 `detail=column` vs `detail=full` 决策**
   - What we know: `detail=column` 索引小一半但不支持 NEAR/phrase 查询 [CITED: sqlite.org/fts5.html]
   - What's unclear: Phase 1 是否需要 NEAR/phrase 查询（如 `"machine learning"` 短语匹配）
   - Recommendation: 使用 `detail=column`，Phase 1 主要是关键词搜索不需要 phrase query。后续可重建。

3. **INGE-05 (2 个独立 LLM 交叉验证) 与 D-10 (Phase 1 单 LLM) 的冲突**
   - What we know: REQUIREMENTS.md 要求 INGE-05，但 CONTEXT.md D-10 明确延迟到 Phase 2
   - What's unclear: INGE-05 是否应从 Phase 1 requirement 列表中移除
   - Recommendation: 按 CONTEXT.md locked decision 执行：Phase 1 单 LLM，INGE-05 延迟到 Phase 2 实现

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | 全部 | Yes | 3.12.3 | -- |
| Git | XCUT-01 session branches | Yes | 2.43.0 | -- |
| SQLite + FTS5 | STOR-05 full-text search | Yes | 3.45.1 | -- |
| pip | 包管理 | Yes | 24.0 | -- |
| libgit2 | pygit2 绑定 | Unknown | -- | subprocess git 命令 |
| Docling models | PDF 智能解析 | Unknown | -- | PyMuPDF 轻量解析 |

**Missing dependencies with no fallback:**
- None identified (核心功能全部可用)

**Missing dependencies with fallback:**
- libgit2/pygit2: 如果不可用，回退到 subprocess 调用 git 命令。功能等价但错误处理需额外工作。
- Docling 模型: 首次使用时自动下载（~2-3GB）。如果下载失败，降级到 PyMuPDF。

## Sources

### Primary (HIGH confidence)
- Context7 /websites/typer_tiangolo -- Typer callback、subcommands、Rich panels
- Context7 /websites/sqlmodel_tiangolo -- SQLModel engine creation、Session、select patterns
- Context7 /berriai/litellm -- Router load balancing、acompletion、fallbacks
- Context7 /adbar/trafilatura -- fetch_url、extract patterns
- PyPI registry -- 所有包版本验证 (2026-04-26)
- sqlite.org/fts5.html -- FTS5 external content、automerge、crisismerge、detail option

### Secondary (MEDIUM confidence)
- .planning/research/STACK.md -- 28 包技术选型与版本兼容性
- .planning/research/ARCHITECTURE.md -- 六边形架构、Outbox 模式、引擎数据流
- .planning/research/PITFALLS.md -- 12 个领域陷阱（FTS5、Write Queue、PDF、LiteLLM）
- .planning/research/FEATURES.md -- 功能依赖图、MVP 建议
- docs/smart_agent_wiki_design.md -- 完整架构设计、5 引擎、23 附录决策

### Tertiary (LOW confidence)
- MinerU API 稳定性 -- 未在本次研究中通过 Context7 验证
- Docling 2.91.0 API 细节 -- 未在 Context7 中深度查询
- pygit2 libgit2 系统依赖可用性 -- 需在目标环境验证

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- 所有核心包版本通过 PyPI 验证，API 模式通过 Context7 确认
- Architecture: HIGH -- 六边形 + Outbox 模式已在 ARCHITECTURE.md 详细设计，代码示例来自官方文档
- Pitfalls: HIGH -- 12 个陷阱来源包括 SQLite 官方文档、LiteLLM Router 文档、181 项目生态审计

**Research date:** 2026-04-26
**Valid until:** 2026-05-26 (30 days -- 稳定技术栈)
