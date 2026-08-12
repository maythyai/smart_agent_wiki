# Architecture: Smart Agent Wiki

**系统架构设计文档**

## 目录

1. [架构概览](#架构概览)
2. [分层架构](#分层架构)
3. [核心引擎](#核心引擎)
4. [数据模型](#数据模型)
5. [连接器框架](#连接器框架)
6. [插件系统](#插件系统)
7. [安全体系](#安全体系)
8. [部署架构](#部署架构)

---

## 架构概览

Smart Agent Wiki 是一个 **local-first** 的多代理知识管理平台，采用 **六边形架构**（Hexagonal Architecture）设计。

```
┌─────────────────────────────────────────────────────────┐
│                    Drivers Layer                         │
│  CLI (Typer) │ Web (FastAPI) │ MCP │ Desktop (Tauri)    │
├─────────────────────────────────────────────────────────┤
│                   Adapters Layer                         │
│  Storage │ Connectors │ Plugins │ Crypto │ LLM Gateway  │
├─────────────────────────────────────────────────────────┤
│                   Engines Layer                          │
│  Ingest │ Query │ Govern │ Learn │ Collaborate │ Compile │
├─────────────────────────────────────────────────────────┤
│                    Domain Layer                          │
│  Page │ Claim │ Evidence │ Confidence │ Freshness       │
└─────────────────────────────────────────────────────────┘
```

### 核心原则

1. **Local-first**: 所有数据本地存储，云同步可选
2. **Knowledge provenance**: 每条知识可溯源到原始来源
3. **Multi-agent**: 6 个专业代理协作处理知识
4. **Plugin-extensible**: 通过插件系统扩展功能

---

## 分层架构

### Domain Layer (纯 Python)

领域模型，无外部依赖：

```
src/saw/domain/
├── page.py          # Wiki 页面
├── claim.py         # 知识声明
├── confidence.py    # 置信度枚举 (ConfidenceLevel)
├── freshness.py     # 新鲜度枚举 (FreshnessLevel)
├── graph.py         # 知识图谱
├── value_objects.py # 共享值对象 (WriteOpStatus, ContradictionType, etc.)
├── utils.py         # 工具函数 (utcnow)
└── exceptions.py    # 领域异常
```

> **Note**: `evidence.py` 已合并到 `claim.py`；`contradiction.py` 的检测逻辑位于 `engines/govern/`。

### Engines Layer (业务逻辑)

五大引擎驱动核心功能：

| 引擎 | 职责 | 关键模块 |
|------|------|----------|
| **Ingest** | 摄入外部知识 | media, web, rss, connectors, pipeline |
| **Query** | 查询与检索 | search, compiler, graph_traverse, tree_mode, compare |
| **Govern** | 质量治理 | linter, contradiction, audit |
| **Learn** | 学习与适应 | scheduler, distiller, trends |
| **Collaborate** | 多代理协作 | orchestrator, dispatcher, workflow_parser, workflow_executor |
| **Compile** | 上下文编译 | compiler, wiki_indexer, wiki_links |

### Adapters Layer (基础设施)

连接外部系统：

```
src/saw/adapters/
├── storage/         # SQLite, 文件存储
├── crypto/          # Ed25519, Fernet 加密
├── llm/             # LLM 网关 (LiteLLM)
└── connectors/      # 第三方平台适配器
```

### Drivers Layer (用户界面)

用户交互入口：

| Driver | 技术 | 端口 |
|--------|------|------|
| CLI | Typer | 终端 |
| Web | FastAPI + React | 8000 + 3000 |
| MCP | Model Context Protocol | stdio |
| Desktop | Tauri 2 | native |

---

## 核心引擎

Smart Agent Wiki 包含 **6 个引擎**（含一个文档中未明确标注的 Compile 引擎）。

### Ingest Engine

摄入流程采用 **DAG Pipeline** 架构：

```
Source → Parse → Extract → Validate → Store → Index
```

支持的来源：
- 文件系统 (Markdown, PDF, DOCX)
- Web URL (Readability 提取)
- RSS/Atom Feed
- 连接器 (Notion, GitHub, Slack, etc.)

### Query Engine

查询管道：

```
Query → FTS5 Search → Graph Traverse → Context Compile → LLM Enhance → Response
```

查询模式：
- **Search**: 全文搜索 (FTS5 + BM25)
- **Graph**: 关系遍历 (NetworkX)
- **Tree**: 层级搜索 (parent-child)
- **Compare**: 多源对比
- **Context**: LLM 上下文编译

### Govern Engine

质量治理系统：

- **Confidence Scoring**: 基于证据的置信度评估 (0-1)
- **Freshness Tracking**: 9 级新鲜度系统 (1=fresh, 9=stale)
- **Contradiction Detection**: 自动检测矛盾声明
- **Blast Radius**: 变更影响范围分析
- **Linting**: 知识质量规则检查

### Learn Engine

学习与优化：

- **FSRS Scheduler**: 间隔重复学习调度
- **Distiller**: 知识蒸馏和压缩
- **Trend Analysis**: 主题趋势追踪
- **Adaptive Indexing**: 自适应索引优化

### Collaborate Engine

6 个专业代理角色（DTO 已在 `domain/agent.py` 定义，具体实现由工作流通过 `AgentDispatcher` 按名称字符串派发）：

| Agent | 角色 | 职责 |
|-------|------|------|
| **Librarian** | 图书管理员 | 分类、标签、组织 |
| **Writer** | 写作助手 | 摘要、改写、报告 |
| **Critic** | 评审专家 | 质量检查、矛盾检测 |
| **Linker** | 关联专家 | 发现知识关联 |
| **Scholar** | 研究学者 | 深度分析、文献综述 |
| **Guardian** | 守护代理 | 安全审查、隐私保护 |

### Code Graph Engine

代码结构图生命周期管理，采用 **六阶段生命周期** 架构：

```
Parse → Build → PostProcess → Query → Review → Update
  ↑                                              │
  └──────────────── 增量反馈环路 ─────────────────┘
```

| 阶段 | 职责 | 关键能力 |
|------|------|----------|
| **Parse** | AST 解析源码 | Python ast + TS 启发式，零 LLM 依赖，2MB 文件保护 |
| **Build** | 持久化到 SQLite | WAL 模式，原子文件替换，确定性 UID |
| **PostProcess** | 派生结构计算 | 证据门控裸名解析，签名生成，FTS5 索引 |
| **Query** | 影响分析/搜索 | 加权 BFS (单跳衰减)，FTS5 + LIKE 降级 |
| **Review** | 变更风险评估 | 跨图影响传播，文档过期检测 |
| **Update** | 增量同步 | git-diff + content-hash 双模式，< 2s |

模块结构：

```
src/saw/code_graph/
├── models.py          # CodeNode/CodeEdge 数据模型
├── store.py           # SQLite WAL 存储 + FTS5 + 批量查询
├── parser.py          # 多语言解析器 (Python AST + TS 启发式)
├── incremental.py     # 增量构建编排 (git-diff + hash)
├── engine.py          # 六阶段生命周期编排
├── postprocess.py     # 裸名解析 + 签名 + FTS
├── flows.py           # 执行流追踪 + 关键度评分
├── communities.py     # Leiden/Louvain 社区检测
├── bridge.py          # doc↔code 双向锚定
├── snapshot.py        # 图快照与完整性自检
├── context_tool.py    # token 预算感知上下文组装
├── govern.py          # 代码变更→文档过期治理
├── health.py          # 可观测性 (指标/告警/健康报告)
├── cli.py             # saw code-graph 子命令
├── mcp_tools.py       # MCP 工具定义
└── resolvers/         # 语言特化解析器 (FastAPI/Flask)
```

双图融合设计：Code Graph (代码结构) 与 Wiki Knowledge Graph (知识文档) 通过 Bridge Layer 松耦合连接，支持跨图影响传播和统一社区视图。

---

## 数据模型

### 核心实体

```
┌──────────┐    has_many    ┌──────────┐
│   Page   │───────────────→│  Claim   │
└──────────┘                └──────────┘
                                 │
                            supported_by
                                 ↓
                            ┌──────────┐
                            │ Evidence │
                            └──────────┘
```

### Page

```python
class Page:
    id: str              # UUID
    title: str           # 页面标题
    content: str         # Markdown 内容
    vault_id: str        # 所属 Vault
    parent_id: str       # 父页面 (可选)
    tags: list[str]      # 标签
    created_at: datetime
    updated_at: datetime
```

### Claim

```python
class Claim:
    id: str              # UUID
    page_id: str         # 所属页面
    content: str         # 声明内容
    confidence: float    # 置信度 (0-1)
    freshness: int       # 新鲜度 (1-9)
    source: str          # 来源
    evidence_ids: list   # 支持证据
```

---

## 连接器框架

### 统一连接器协议

```python
class ConnectorProtocol(Protocol):
    async def connect(self, credentials) -> ConnectionStatus: ...
    async def sync(self, direction) -> SyncResult: ...
    async def disconnect(self) -> None: ...
    def health(self) -> HealthStatus: ...
```

### 已实现连接器

| 平台 | 类型 | 同步方向 |
|------|------|----------|
| Notion | OAuth | 双向 |
| GitHub | OAuth | 单向 (in) |
| Slack | OAuth | 单向 (in) |
| Discord | Bot Token | 单向 (in) |
| Feishu | App | 双向 |
| WeCom | Webhook | 单向 (in) |
| Logseq | Local File | 双向 |
| Obsidian | Local File | 双向 |
| RSS/Atom | URL | 单向 (in) |

### Write Queue

所有变更操作通过 **SQLite Outbox** 模式持久化：

```
Mutation → Write Queue (SQLite) → Processor → Apply → Ack
```

保证：
- 原子性：操作要么完全执行，要么不执行
- 持久性：写入后不丢失
- 重试：失败自动重试（指数退避）

---

## 插件系统

### 架构

```
┌─────────────┐
│ Plugin SDK  │  base.py, events.py, registry.py
├─────────────┤
│  Plugin 1   │  markdown-formatter
├─────────────┤
│  Plugin 2   │  word-counter
├─────────────┤
│  Plugin N   │  user plugins...
└─────────────┘
```

### 事件流

```
Engine Event → Event Bus → Plugin Registry → Plugin Handlers
```

### 安全隔离

- 每个插件有独立的 `data_dir`
- 沙箱隔离**计划中** (当前插件拥有完整 Python 解释器权限)
- 插件不能直接访问数据库（通过 `PluginContext` 提供的受限 API 访问）

> **Note**: 事件总线（`subscribe_event` / `publish_event`）尚未连接到引擎层；`PluginContext` 中的回调在 CLI 中为 `lambda x, y: None`。事件类型定义已完成，钩子分发待实现。

---

## 安全体系

### 认证 (SEC-01) ✅

- JWT (access_token + refresh_token)，密钥持久化（`.saw/keys/jwt.key`）
- bcrypt 密码哈希
- Token 刷新与撤销，支持 `local`（单机信任）与 `team`（强制 JWT）两种模式
- 用户与 Refresh Token 持久化（SQLAlchemy，`users` / `refresh_tokens` 表）

### 授权 (SEC-02) ✅

- RBAC: admin / editor / viewer，`require_role` FastAPI 依赖
- Vault-level 权限控制（`PermissionService`）
- **Cedar 策略引擎**：代码已实现（`cedar_policy.py`，python binding + CLI 子进程兜底），尚未接线到路由

### API 安全

- 速率限制中间件（`RateLimitMiddleware`），已注册到 `create_app()` ✅
- 输入清洗（XSS 模式检测，SQL 注入检测），已注册到 `create_app()` ✅
- CORS 策略配置 ✅
- 安全头（CSP, HSTS, X-Frame-Options），已注册到 `create_app()` ✅

### 数据保护

- Fernet 加密（OAuth tokens at rest），密钥持久化（`.saw/keys/fernet.key`）✅
- Ed25519 签名（审计收据），密钥持久化（`.saw/keys/ed25519.key`），统一为 PyNaCl 实现 ✅
- API Key SHA256 哈希存储 ✅
- 迁移框架（`PRAGMA user_version` 驱动，`saw.db.migrations`）✅

---

## 部署架构

### 单机部署 (默认)

```
User → CLI / Web UI → SAW Process → SQLite DB
```

### 团队部署

```
Users → Load Balancer → SAW Web (N instances)
                             ↓
                        Redis (cache + rate limit)
                             ↓
                        Shared SQLite / PostgreSQL
```

### Docker 部署

```yaml
services:
  saw-web:
    image: saw:latest
    ports: ["8000:8000"]
    environment:
      - AUTH_SECRET_KEY=...
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]

  redis:
    image: redis:7-alpine

  saw-frontend:
    image: saw-frontend:latest
    ports: ["3000:3000"]
```

### Tauri Desktop

```
Tauri Shell → WebView (React UI)
     ↓
Python Sidecar (SAW backend)
     ↓
Local SQLite DB
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| Backend | Python 3.11+, FastAPI |
| Frontend | React 19, TypeScript, Vite |
| Database | SQLite (FTS5), Redis (optional) |
| Desktop | Tauri 2 (Rust) |
| LLM | LiteLLM (multi-provider) |
| Crypto | PyNaCl, Fernet, bcrypt |
| Graph | NetworkX |
| Testing | pytest, Vitest |

---

*最后更新: 2026-08-11*
