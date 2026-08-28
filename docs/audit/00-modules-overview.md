# Smart Agent Wiki — 模块总览与功能清单

> 版本基线：v3.7.0 · 生成日期：2026-08-28
> 用途：作为可用性启发式评估（Mode B）的模块索引与底层数据库/数据联动说明。
> 配套：每个模块对应一份 `docs/audit/NN-<module>.md` 审计报告。

---

## 1. 项目定位与架构

Smart Agent Wiki（SAW，CLI：`saw`）是一个**本地优先（local-first）的多代理知识平台**。核心理念：知识是"编译"的结果而非检索的对象，每条主张（claim）可溯源到原始文档的具体位置。

技术栈：
- 后端：Python 3.11+，六边形架构 `domain → engines → adapters → drivers`
- 前端：React 19 + TypeScript + Vite + Tailwind + Zustand + Cytoscape.js + Milkdown
- 桌面：Tauri 2
- 存储：SQLite（默认，WAL 模式）/ PostgreSQL（团队部署）
- 协议：REST + WebSocket + MCP（24+ 工具）

四层存储架构：**Vault（不可变原始文件）→ Claims（DB）→ Wiki Pages（Markdown）→ Index（FTS5 + Graph）**。

五大引擎：Ingest（摄入）、Query（查询）、Govern（治理）、Learn（学习）、Collaborate（协作）+ Compile（编译）/Code Intelligence（代码智能）。
六个专业化 Agent：Librarian / Writer / Critic / Linker / Scholar / Guardian。

单一变更网关：**Write Queue（SQLite outbox 模式）**，所有写操作经 outbox 分发到各 sink。

---

## 2. 模块清单

| # | 模块 | 关键路径 | 职责 | 审计报告 |
|---|------|----------|------|----------|
| 1 | Ingest 摄入与解析 | `engines/ingest/*`, `ingest/pipeline/*`, `adapters/parsers/*` | 文档/PDF/URL/代码 → claims 的 DAG 流水线（Classify→Parse→Extract→Merge→Validate→Store） | `01-ingest-pipeline.md` |
| 2 | Query 查询与搜索 | `engines/query/*`, `drivers/web/routes/{search,pages,graph}.py`, `web/src/pages/{Search,Pages,Graph}.tsx` | BM25+FTS5 搜索、NL 查询、图谱遍历、对比、tree-mode | `02-query-search.md` |
| 3 | Govern 治理与审计 | `engines/govern/*`, `reconcile/*`, `audit/*`, `api/routes/govern.py` | 置信度、新鲜度、矛盾检测、blast-radius、Ed25519 审计收据 | `03-govern-audit.md` |
| 4 | Collaborate 多代理协作 | `engines/collaborate/*`, `api/routes/collaborate.py`, `workflows/*` | 6 Agent 调度、A2A 协议、工作流编排/执行/恢复 | `04-collaborate-workflow.md` |
| 5 | Compile & 代码智能 | `engines/compile/*`, `analysis/*`, `code_graph/*`, `api/routes/impact.py` | 知识编译、影响分析、执行流检测、过期检测、DAG | `05-compile-code-intelligence.md` |
| 6 | Connectors 集成连接器 | `connectors/*`, `api/{integrations,webhooks,oauth_callback,sync,notion,github,logseq}.py` | Notion/GitHub/Slack/Discord/Feishu/WeCom/Logseq 双向同步、OAuth、Webhook | `06-connectors-integrations.md` |
| 7 | Web API 与前端 UI | `drivers/web/*`, `api/*`, `web/src/*` | FastAPI 路由/中间件、React 页面/组件/状态、实时 WebSocket | `07-web-api-frontend.md` |
| 8 | Auth 与安全 | `auth/*`, `drivers/web/middleware/security.py`, `api/{keys,rate_limit}.py`, `adapters/crypto/*` | JWT、RBAC、API Key、速率限制、输入清洗、安全头、审计日志 | `08-auth-security.md` |
| 9 | DB 与存储层 | `db/*`, `adapters/storage/*`, `write_queue/*` | 表模型、迁移、连接工厂、claims/wiki/vault/fts 仓储、outbox | `09-db-storage-writequeue.md` |
| 10 | 平台支撑 | `plugins/*`, `onboarding/*`, `tutorial/*`, `config/*`, `token_optimizer/*`, `context/*` | 插件系统、引导、教程、配置、Token 优化、上下文加载 | `10-platform-support.md` |
| 11 | CLI 命令行 | `drivers/cli/*` | Typer CLI：init/ingest/query/search/impact/process/staleness/lint/... | `11-cli.md` |
| 12 | MCP Server | `drivers/mcp/*` | 24+ MCP 工具（摄入/查询/治理/代码智能/学习/协作） | `12-mcp.md` |
| 13 | Research / Synthesize / Purpose | `research/*`, `synthesize/*`, `purpose/*` | 自动摄入、Web 搜索、综合、目的驱动 | `13-research-synthesize.md` |

---

## 3. 各模块功能详述

### 3.1 Ingest 摄入与解析
- **DAG 流水线**：`ingest/pipeline/` 定义 6 阶段（Classify → Parse → Extract → Merge → Validate → Store），使用 Kahn 拓扑排序做 DAG 验证与循环检测。
- **抽取器**（`engines/ingest/extractors/`）：Markdown、PDF（Docling/PyMuPDF）、URL（trafilatura）、代码 AST（零 LLM）、媒体。
- **批处理与调度**：`batch.py`、`scheduler.py`、`feed_manager.py`（RSS 订阅）、`preview.py`（摄入预览）、`fuser.py`（合并去重）。
- **校验**：`engines/ingest/validator.py` + `ingest/pipeline/validator.py`。

### 3.2 Query 查询与搜索
- **引擎编排**：`engines/query/engine.py`（`QueryEngine`）统一调度 search/compiler/graph/compare/tree_mode。
- **搜索**：`search.py`（FTS5 + BM25）、`tree_mode.py`（树形）、`wiki_indexer.py`（索引 wiki 页）、`wiki_graph.py`/`wiki_links.py`/`related_pages.py`。
- **NL 查询**：`compiler.py`（ContextCompiler，分层答案 L1-L4 + 内联引用）、`memory.py`（跨会话记忆）、`cache.py`（LRU+TTL，默认 300s/1000）。
- **图谱/对比**：`graph_traverse.py`（DFS 遍历）、`compare.py`（对比分析）。
- **前端**：Search / Pages / Graph 页面 + CommandPalette（⌘K）。

### 3.3 Govern 治理与审计
- **治理器**：`engines/govern/governor.py`（`Governor`）。
- **置信度**（4 层）：`confidence.py`；**新鲜度**（9 级）：`freshness.py`；**矛盾检测**：`contradiction.py`；**blast-radius**：`blast_radius.py`；**linter**：`linter.py`；**审计**：`audit.py`。
- **对账**：`reconcile/`（detector/strategies/audit/engine）。
- **审计签名**：`adapters/crypto/ed25519.py`（Ed25519 审计收据）。

### 3.4 Collaborate 多代理协作
- **6 Agent**：`engines/collaborate/agents/`（librarian/writer/critic/linker/scholar/guardian + base）。
- **调度**：`dispatcher.py`（`AgentDispatcher`）、`orchestrator.py`（`CollaborateEngine`）。
- **A2A 协议**：`a2a_protocol.py`（`A2AAdapter`）。
- **工作流**：`workflow_parser.py`、`workflow_executor.py`（`WorkflowExecutor`，崩溃恢复见 `workflow_executions` 表）。
- **YAML 工作流定义**：仓库根 `workflows/`。

### 3.5 Compile & 代码智能
- **编译**：`engines/compile/`（compiler/concept_graph/code_wiki/archiver/linter/parsers/feedback）。
- **代码智能**：`analysis/`（impact/process/staleness）、`code_graph/`（知识图谱存储）。
- **风险分级**：WILL_BREAK → LIKELY_AFFECTED → MAY_NEED_TESTING（BFS）。

### 3.6 Connectors 集成连接器
- **框架**：`connectors/`（base_connector/protocol/registry/bootstrap/sync_engine/backpressure/conflict_resolver/rate_limiter/retry_handler/health_monitor/oauth_handler/token_refresh/token_encryption/webhook_verifier/sync_status/sync_logger）。
- **连接器**：notion/、github/、im/{slack,discord,feishu,wecom}/、logseq/。
- **API**：`api/integrations.py`、`integrations_ws.py`、`webhooks.py`、`webhook_inbound.py`、`oauth_callback.py`、`sync.py`、`notion*.py`、`github*.py`、`logseq.py`、`connector_settings.py`。
- **前端**：Integrations / ConnectorSettings 页面。

### 3.7 Web API 与前端 UI
- **后端**：`drivers/web/app.py`（FastAPI 工厂，注入 Query/Collaborate/WriteQueue/EventBus/Govern/Plugins）；`drivers/web/routes/`（auth/pages/search/graph/import_md/capture/templates/entity_types/onboarding/timeline/websocket）；`api/`（feeds/dashboard_stats/keys/rate_limit/graphql/bulk/health）。
- **中间件栈**（注册顺序）：CORS → 错误处理器 → 安全头 → request-id/可观测 → 审计日志 → 输入清洗 → 速率限制。
- **实时**：`drivers/web/websocket.py`（WebSocket 广播，消费 EventBus）。
- **前端**：`web/src/`（App 布局、pages、components/{dashboard,editor,graph,search,layout,entity,links,related,timeline,integrations,settings,capture,common,ui}、stores/{auth,dashboard,editor,graph,ui,integrations}、hooks、lib/api.ts、routes）。

### 3.8 Auth 与安全
- **认证**：`auth/jwt_auth.py`（access/refresh token 对）、`auth/user_store.py`、`auth/permissions.py`（RBAC：admin/editor/viewer）。
- **中间件**：`drivers/web/middleware/security.py`（SecurityHeaders / AuditLog / InputSanitizer / get_current_user / require_role）。
- **API Key / 限流**：`api/keys.py`、`api/rate_limit.py`（`RateLimitMiddleware`）。
- **密码学**：`adapters/crypto/`（ed25519、cedar_policy、_keyfiles）。
- **认证模式**：`local`（单用户，信任本地为 admin）/ `team`（要求 JWT，生产）。

### 3.9 DB 与存储层（详见第 4 节）
- **数据库**：`db/`（模型 + 迁移 + 配置 + 会话）。
- **存储适配器**：`adapters/storage/`（sqlite_connection/claims_repository/wiki_repository/vault_repository/fts5_utils/fts_tokenize）。
- **Write Queue**：`write_queue/`（queue/dispatcher/sinks/{wiki,fts5,claims,graph,contradictions,vault,connector}）。

### 3.10 平台支撑
- **插件**：`plugins/`（base/registry/events/event_bus，沙箱 `data_dir`，6 事件类型）。
- **引导**：`onboarding/`；**教程**：`tutorial/`（5 步交互式 + demo_content）。
- **配置**：`config/`（settings/defaults/agent_templates）。
- **Token 优化**：`token_optimizer/`（anatomy/cerebrum/buglog/session_tracker/token_ledger）。
- **上下文**：`context/loader.py`。

### 3.11 CLI 命令行
- `drivers/cli/main.py`（Typer 入口）+ `commands/`（init/ingest/query/search/impact/process/staleness/lint/conflicts/freshness/verify/review/audit/compile/feed/plugin/tutorial/docs/mcp/web/status/ingest_media）。
- `config_tui.py`（TUI 配置）、`completion.py`（shell 补全）、`error_handler.py`（友好错误）。

### 3.12 MCP Server
- `drivers/mcp/server.py`（FastMCP）+ `tools/`（ingest/query/govern/code_graph/learn/collaborate/compile/emerge/connect/links/thinking/context/pages/challenge/graduate/impact）+ `config.py`/`prompts.py`/`resources.py`/`research_on_miss.py`。

### 3.13 Research / Synthesize / Purpose
- `research/`（research_engine/auto_ingest/web_search）、`synthesize/`、`purpose/`（目的驱动的研究与综合）。

---

## 4. 数据库层与数据联动（专节）

### 4.1 两套数据库

SAW 实际存在两套数据库抽象：

**A. 核心知识库（SQLite，原生 `sqlite3`）**
- 由 `src/saw/db/migrations.py` 的 `apply_migrations(conn)` 管理，基于 `PRAGMA user_version` 的版本化迁移框架，单事务内顺序应用、幂等（`IF NOT EXISTS` + 列存在性检查）。
- 当前迁移版本 v1–v5：
  - **v1 基线**：`claim`、`claim_relation`、`entity`、`entity_relation`、`fts_index`（FTS5 虚拟表）、`write_outbox`、`sink_tracking`、`contradictions`。
  - **v2**：`write_outbox.next_retry_at` 列（指数退避）。
  - **v3**：`claim.last_accessed` 列（新鲜度按访问衰减）。
  - **v4**：`workflow_executions` 表（工作流崩溃恢复，HI-9）。
  - **v5**：图谱表 FK/过滤索引（M-13，避免全表扫描）。
- 连接配置（`drivers/web/app.py`）：`PRAGMA journal_mode=WAL`、`busy_timeout=5000`、`foreign_keys=ON`；测试模式用 `:memory:`。

**B. 团队/认证库（SQLAlchemy 2.0，支持 PostgreSQL）**
- 由 `src/saw/db/models.py` 等 ORM 模型定义，`Base.metadata.create_all` 幂等建表。
- 表：`users`、`vaults`、`claims`（SQLAlchemy 版）、`vault_permissions`、`audit_logs`、`refresh_tokens`、`system_config`、`feeds`/`feed_entries`、`connector_configs`/`connector_sync_logs`、`sync_states`/`sync_logs`/`conflict_records`、`notion_*`/`logseq_*`/`github_*` 同步游标与配置。
- 配置：`db/config.py`（`DatabaseConfig.from_env()`，读 `DATABASE_URL`/`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`/`DB_ECHO`；自动 SQLite↔Postgres + asyncpg/aiosqlite）。
- 会话：`db/session.py`（`get_db_session()` FastAPI 依赖，懒加载引擎单例 + 首次调用 `_ensure_schema()` 建表）。
- 另有 `adapters/storage/sqlite_connection.py`（SQLModel 引擎 + WAL PRAGMA 监听器，64MB cache/mmap）。

### 4.2 系统参数管理
- `system_config` 表（key TEXT PK / value TEXT / updated_at）——键值对式系统配置存储。
- 运行时配置来源优先级：环境变量 → `.saw/config.yaml`（auth_mode、path 等）→ 默认值。
- `db/config.py` 通过 `os.environ` 读取 DB 相关参数；`config/settings.py`、`config/defaults.py` 提供应用级默认。

### 4.3 表管理（迁移与生命周期）
- **单一迁移入口**：`apply_migrations(conn)` —— `SQLiteClaimsRepository._init_schema`、`SQLiteWriteQueue._create_tables`、`saw init` 全部委托于此（替代了过去分散的 `ALTER TABLE` try/except 与 `CREATE TABLE IF NOT EXISTS` 散点，C4 审计发现）。
- **幂等性保证**：所有 DDL 用 `IF NOT EXISTS`；列增量用 `PRAGMA table_info` 列存在性检查。
- **团队库建表**：`create_all` 幂等，`session.py` 首次访问时触发。
- **崩溃恢复**：启动时 `_recover_stranded_workflows` 将遗留 `running` 工作流标记为 `interrupted`（HI-9）；Write Queue `recover()` 复位 `processing` 残留 + `dispatch_pending()` 排空（CR-3/HI-7），后台每 60s 复跑。

### 4.4 前后端与数据联动
完整数据流（以一次写操作为例）：

```
React 组件 (web/src/components)
  └─ Zustand store (web/src/stores/*)        // 客户端状态
       └─ api client (web/src/lib/api.ts)    // fetch 封装，携带 JWT
            └─ FastAPI 路由 (drivers/web/routes | api/*)   // 依赖注入 get_current_user
                 └─ 引擎层 (engines/*)        // 业务逻辑
                      └─ Write Queue (write_queue/queue.py)  // enqueue_atomic → outbox
                           └─ Dispatcher → Sinks              // 分发到多个 sink
                                ├─ WikiSink   (wiki_repo → .md 文件)
                                ├─ FTS5Sink   (fts_index)
                                ├─ ClaimsSink (claims_repo → claim 表)
                                ├─ GraphSink  (claim_relation/entity_relation)
                                ├─ ContradictionsSink (contradictions)
                                └─ VaultSink/ConnectorSink
```

- **读路径**：前端 → API → QueryEngine → FTS5Search/GraphTraverse → SQLite（只读）。
- **实时联动**：写操作经 EventBus → WebSocket 广播器 → 前端实时更新。
- **单一变更网关**：所有 mutation 必须入 outbox，由 Dispatcher 分发到各 sink，保证多存储一致性 + op_id 去重 + per-sink 状态跟踪 + 指数退避重试 + 死信队列。
- **并发安全**：共享 `sqlite3.Connection`（`check_same_thread=False`）+ `threading.Lock` 串行化所有 mutation；WAL 模式允许并发读。
- **CORS**：默认允许 `localhost:3000`/`127.0.0.1:3000`（开发）。

### 4.5 存储适配器（`adapters/storage/`）
- `claims_repository.py`：claim 的 CRUD + FTS5 同步 + 置信度/新鲜度。
- `wiki_repository.py`：wiki 页（Markdown 文件）读写。
- `vault_repository.py`：不可变原始文件。
- `fts5_utils.py` / `fts_tokenize`：FTS5 索引工具与分词。

---

## 5. 完成度总体观察（基于代码与注释）

代码中大量 `# pragma: no cover` 防御性守卫与 "previously X was broken, now fixed" 注释（CR-/HI-/M-/C4- 等编号），表明项目处于**活跃迭代 + 持续补漏**阶段：
- 多处"先前路由未挂载/引擎未注入导致 500/503/404"的修复（HI-1~HI-4、CR-2~CR-4），说明 wiring 完整性是历史薄弱点，现已大量修补但仍有 `pragma: no cover` 的容错分支。
- 认证模式 `local` 在非回环绑定下会硬启动失败（安全护栏），但默认仍为 `local`。
- 离线模式（`llm=None`）下 Agent 走启发式回退、QueryEngine 走离线分支——核心功能可用但能力降级。

> 详细可用性发现见各模块审计报告。
