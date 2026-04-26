# Stack Research

**Domain:** 智能多代理知识管理平台 (Intelligent Multi-Agent Knowledge Platform)
**Researched:** 2026-04-26
**Confidence:** HIGH

## Recommended Stack

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

## Installation

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

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Typer | Click | Click 更成熟稳定，但 Typer 类型注解驱动开发效率更高，与 FastAPI 风格统一 |
| Typer | Cyclopts | Cyclopts 是 Typer 的潜在替代（FastMCP 3.x 已采用），但 Typer 生态更成熟 |
| FastAPI | Starlette | Starlette 更底层灵活，但 FastAPI 的 Pydantic 集成和自动文档对知识平台价值更大 |
| FastAPI | Litestar | Litestar 性能略优且类型安全更好，但生态和社区规模远小于 FastAPI |
| SQLModel | SQLAlchemy Core | SQLModel 学习曲线更平缓，SQLAlchemy Core 更灵活；当需要复杂查询优化时回退到 Core |
| LanceDB | ChromaDB | ChromaDB 1.x 默认启动服务器进程，对本地优先架构不友好；LanceDB 纯嵌入式，零服务器 |
| Docling | MinerU | MinerU 精度更高但依赖链重（PaddleOCR），安装复杂；Docling 是更好的默认选择 |
| FastMCP | mcp (官方 SDK) | FastMCP 3.x 内部封装了官方 mcp SDK，提供更高层抽象；需要底层控制时直接用 mcp SDK |
| NetworkX | iGraph | iGraph C 核心性能更高（>100K 节点），但 NetworkX 纯 Python 更易安装调试；Phase 4 可迁移 |
| sentence-transformers | OpenAI Embeddings API | OpenAI 质量更高但需 API 调用和费用；本地优先原则下 sentence-transformers 是默认 |
| PyNaCl | cryptography (Ed25519) | cryptography 库也支持 Ed25519 且更全面，但 PyNaCl API 更简洁；两者可共存 |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| ChromaDB (默认) | 1.x 版本默认启动服务器进程，违背本地优先原则；依赖链重（onnxruntime, tokenizers 等） | LanceDB 作为默认，ChromaDB 仅在用户显式选择时支持 |
| LangChain / LlamaIndex | 框架锁定风险高，抽象层过厚导致调试困难，版本更新频繁破坏兼容性 | LiteLLM 做模型接入，自建摄入/查询管线保持控制力 |
| Elasticsearch / Meilisearch | 外部服务依赖，违背零安装本地优先原则 | SQLite FTS5 + rank-bm25 混合搜索 |
| Neo4j / ArangoDB | 图数据库服务器依赖过重，本地优先架构不友好 | NetworkX 内存图 + SQLite 持久化 |
| FAISS | Facebook 的向量索引库，安装依赖复杂（特别是 GPU 版本），Python API 不够 Pythonic | LanceDB 封装了 FAISS 功能且 API 更友好 |
| Whoosh | 已停止维护（最后更新 2017），纯 Python 性能差 | SQLite FTS5（C 实现，内置标准库） |
| newspaper3k | 已停止维护，对现代网站解析效果差 | trafilatura |
| openai-whisper | 比 faster-whisper 慢 4x，内存占用高 | faster-whisper（CTranslate2 后端） |
| dataclasses (stdlib) | 功能有限，不支持嵌套验证和序列化 | Pydantic 模型 |

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
| Python 3.11+ | 所有上述库 | 全部支持 Python 3.11, 3.12, 3.13 |

**已知兼容性风险:**
- SQLModel 0.0.x 仍然是 pre-release 版本，API 可能有 breaking changes；作为缓解措施，关键数据路径可直接使用 SQLAlchemy Core
- cedar-python 0.1.4 是非常早期的绑定，功能可能不完整；备选方案是直接子进程调用 Cedar CLI 或自实现简化版策略引擎
- Docling 2.x 的依赖链较重（涉及深度学习模型下载），首次安装后约 2-3GB 磁盘空间

## Sources

- PyPI API (pypi.org/pypi/{package}/json) -- 所有版本号直接验证，2026-04-26
- FastMCP PyPI 页面 (pypi.org/project/fastmcp) -- 确认 PrefectHQ 维护、mcp SDK 封装关系、日下载百万次 -- HIGH
- MCP SDK PyPI (pypi.org/project/mcp) -- 确认官方 SDK 版本和依赖 -- HIGH
- FastMCP 文档 (gofastmcp.com) -- FastMCP 3.x 架构和功能确认 -- HIGH
- 项目设计文档 (docs/smart_agent_wiki_design.md) -- 技术选型上下文和约束条件
- 项目背景 (docs/llm_wiki_ecosystem_analysis.md) -- 181 项目生态分析，技术选型参考来源

---
*Stack research for: Smart Agent Wiki (智能多代理知识平台)*
*Researched: 2026-04-26*
