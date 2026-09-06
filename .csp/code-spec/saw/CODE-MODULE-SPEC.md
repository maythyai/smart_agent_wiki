---
type: module-spec
confidence: medium
sources:
  - "[[src/saw/]]"
  - "[[docs/audit/00-modules-overview.md]]"
  - "[[docs/audit/01-ingest-pipeline.md]]"
  - "[[docs/audit/02-query-search.md]]"
  - "[[docs/audit/03-govern-audit.md]]"
  - "[[docs/audit/04-collaborate-workflow.md]]"
  - "[[docs/audit/05-compile-code-intelligence.md]]"
  - "[[docs/audit/06-connectors-integrations.md]]"
  - "[[docs/audit/07-web-api-frontend.md]]"
  - "[[docs/audit/08-auth-security.md]]"
  - "[[docs/audit/09-db-storage-writequeue.md]]"
  - "[[docs/audit/11-cli.md]]"
  - "[[docs/audit/12-mcp.md]]"
seeAlso:
  - "[[code-spec/saw/entry-points.jsonl]]"
  - "[[code-spec/saw/knowledge-graph.json]]"
created: "2026-09-01"
updated: "2026-09-01"
---

# CMS — Smart Agent Wiki (saw) Code Module Spec

> 棕地蒸馏产物（00 阶段 / Phase 1.7）。入口点见 `entry-points.jsonl`（215 条），调用图见 `knowledge-graph.json`。所有结论带 `file:line`；grep 不到的标 `[TBD]`，留 05 增量对齐。confidence=medium：结构与主链已落地，深子调用与部分 cmd↔engine 接线待核。

## 0. 架构总览

六角架构，四层依赖单向：`domain/`（纯 Python，值对象/协议/异常）→ `engines/`（业务逻辑，五引擎+collaborate/compile/code 内聚）→ `adapters/`（基础设施：storage/llm/parsers/crypto/embeddings）→ `drivers/`（cli/web/mcp）+ `api/`（HTTP 路由）。

- **Write Queue 是唯一变更网关**：`src/saw/write_queue/dispatcher.py:16` `Dispatcher` → `SQLiteWriteQueue`（outbox）→ sinks（`vault_sink`/`claims_sink`/`wiki_sink`/`fts5_sink`/`graph_sink`/`contradictions_sink`/`connector_sink`）→ `adapters/storage/*_repository`。所有 mutation 经此，禁 engine 直写 repo。
- **入口三通道**：CLI（`src/saw/drivers/cli/main.py:10` Typer `app`，console_scripts `saw = saw.drivers.cli.main:app`，pyproject.toml:48）、Web（`src/saw/drivers/web/app.py:165` FastAPI）、MCP（`src/saw/drivers/mcp/server.py:27` FastMCP，工具在 `tools/*.py` 用 `@mcp.tool`）。
- **四层存储**：Vault → Claims → Wiki → Index（FTS5），对应 `adapters/storage/{vault,claims,wiki}_repository.py` + `fts5_utils.py`。
- **DB**：SQLite 单库 `saw.db`（`adapters/storage/sqlite_connection.py`）。

## 1. 分层职责与禁止项

| 层 | 路径 | 职责 | 禁止 |
|---|---|---|---|
| domain | `src/saw/domain/` | 值对象/实体/协议/异常（`claims.py`/`wiki.py`/`value_objects.py`/`protocols.py`/`exceptions.py`） | 依赖 engines/adapters/drivers；含 IO |
| engines | `src/saw/engines/` | 五引擎业务逻辑（ingest/query/govern/learn/collaborate + compile） | 直写 repository（须经 write_queue）；含 HTTP/CLI 框架代码 |
| adapters | `src/saw/adapters/` | storage repos / LLM router / parsers / crypto / embeddings / url_guard | 含业务决策；反向依赖 engines |
| drivers | `src/saw/drivers/` | cli/web/mcp 入口、路由、DTO、middleware | 业务逻辑（委派 engines） |
| api | `src/saw/api/` | HTTP 路由（含 `routes/` 子包） | 同 drivers |
| write_queue | `src/saw/write_queue/` | outbox + dispatcher + sinks（唯一 mutation 网关） | engines 绕过 |
| connectors | `src/saw/connectors/` | 外部平台连接器（github/notion/slack/discord/feishu/wecom/logseq）+ IM 事件 | 直写主库（经 connector_sink） |
| code_graph | `src/saw/code_graph/` | 代码图谱引擎（AST/调用图/社区/影响分析/flow） | — |

**Drift 提示**：`engines/` 与 `adapters/` 之间经 `domain/protocols.py` 定义端口（[TBD] 端口完整性待 03 核）；`api/` 与 `drivers/web/routes/` 两套路由并存（见 §7）。

## 2. 模块边界（对齐 docs/audit 00-13）

### M01 Ingest（`src/saw/engines/ingest/`）
- 入口：`cli:ingest`（`ingest_cmd.py:35`）、`mcp:saw_ingest`（`tools/ingest.py:27`）、`web:POST /api/v1/ingest`（`api/routes/query_ingest_learn.py:146`）。
- 核心：`IngestPipeline.ingest`（`pipeline.py:102`）→ 提取器 `extractors/{markdown,pdf,url,code_ast,llm_extract,media,structured}.py` → `_build_write_ops`（`pipeline.py:310`）→ Dispatcher。
- 附属：`classifier.py`/`validator.py`/`fuser.py`/`batch.py`/`scheduler.py`/`feed_manager.py`/`preview.py`。
- **Drift**：deep_audit（2026-06-23）记"MCP 工具宣称 24+ 实际 6"——现 MCP 已 61 工具（见 entry-points），此 drift 已消解；ingest 提取器分发选择逻辑 `[TBD]`（`_get_media_extractor` pipeline.py:88，其余 [TBD]）。

### M02 Query/Search（`src/saw/engines/query/`）
- 入口：`cli:query`（`query_cmd.py:31`）、`mcp:saw_query`（`tools/query.py:45`）、`web:POST /api/v1/query`（`api/routes/query_ingest_learn.py:66`）。
- 核心：`QueryEngine.query`（`engine.py:82`）→ 五分支 `_nl_query`(124)/`_keyword_search`(194)/`_graph_query`(277)/`_compare_query`(333)/`_tree_query`(392)；编译 `ContextCompiler`（`compiler.py`）、检索 `FTS5Search`（`search.py`）、`GraphTraverse`（`graph_traverse.py`）、`TreeModeSearch`（`tree_mode.py`）。
- 引用：`CompareEngine`（`compare.py`）、`wiki_graph.py`/`wiki_indexer.py`/`wiki_links.py`/`related_pages.py`/`memory.py`/`cache.py`。
- **Drift**：`_nl_query`→LLMRouter 调用点 `[TBD]`；citation 解析 `_resolve_citations`（`engine.py:542`）链 `[TBD]`。

### M03 Govern/Audit（`src/saw/engines/govern/`）
- 入口：`cli:{audit,verify,freshness,review,conflicts,lint}`、`mcp:saw_{lint,conflicts,verify,freshness,review,audit,blast_radius}`（`tools/govern.py`）、`web:/api/v1/{lint,verify,contradictions,blast-radius,claims/{id}}`（`api/routes/govern.py`）。
- 核心：`Governor`（`governor.py:39`）：`lint`(66)/`verify_claim`(70)/`get_freshness_report`(93)/`trigger_review`(107)。
- 附属：`confidence.py`/`freshness.py`/`contradiction.py`（async worker `:95`）/`blast_radius.py`/`audit.py`/`linter.py`。
- **Drift**：cmd→Governor 接线 `[TBD]`；Governor→子模块 wiring `[TBD]`。

### M04 Collaborate（`src/saw/engines/collaborate/`）
- 入口：`web:POST/GET /api/v1/workflows`（`api/routes/collaborate.py:230,327`）、`mcp:saw_workflow`（`tools/collaborate.py:27`）、`mcp:saw_feedback`（`:89`）。
- 核心：`CollaborateEngine`（`orchestrator.py:36`）：`execute_workflow`(125)/`dispatch_agent`(78)/`send_a2a_message`(159)/`handoff`(170)/`check_policy`(196)。
- 6 agent：`agents/{librarian,writer,critic,linker,scholar,guardian}.py` + `base.py`；`workflow_executor.py`/`workflow_parser.py`/`dispatcher.py`/`a2a_protocol.py`。
- **Drift（高危）**：deep_audit 记"6 agent execute() 为空实现"——**须 05 实机核验**（agents/ 目录已存在，但方法体是否落地未验，标 [TBD]）。

### M05 Compile/Code-Intelligence（`src/saw/engines/compile/` + `src/saw/code_graph/`）
- 入口：`cli:compile`（动态注册 `compile_cmd.py:568+`）、`mcp:saw_{wiki_compile,wiki_index,wiki_page,archive,concept_*,graph_overview,navigate,issue_*,cr_*,code_wiki_*}`（`tools/compile.py`）、`mcp:saw_{code_query,code_search,architecture,flows,code_context,impact}`（`tools/code_graph.py`）。
- Compile 引擎：`compiler.py`/`archiver.py`/`concept_graph.py`/`code_wiki.py`/`feedback.py`/`linter.py`/`parsers.py`。
- CodeGraph 引擎：`CodeGraphEngine`（`code_graph/engine.py:35`）：`build`(68)/`update`(92)/`trace_flows`(105)/`get_affected_flows`(109)/`detect_communities`(113)/`architecture_overview`(117)/`impact_analysis`(149)。附属 `parser.py`/`flows.py`/`communities.py`/`incremental.py`/`snapshot.py`/`postprocess.py`/`resolvers/`/`bridge.py`/`store.py`。
- **Drift**：CLI 子命令经 `register_code_graph_commands`/`register_compile_commands` 动态注册，逐条 file:line `[TBD]`（05 枚举）。

### M06 Connectors/Integrations（`src/saw/connectors/`）
- 平台：`github/`（`connector.py`/`oauth.py`/`graphql_client.py`/`issue_fetcher.py`/`reconciliation.py`/`webhook_handler.py`）、`im/{discord,feishu,slack,wecom}/`（各 `connector.py`+`event_handler.py`+`models.py`）、`logseq/`（`connector.py`+`file_watcher.py`）、`notion/`。
- 横切：`base_connector.py`/`bootstrap.py`/`backpressure.py`/`conflict_resolver.py`/`health_monitor.py`。
- 入口：`web:/connectors/{github,notion}`、`/api/v1/{connectors,integrations,sync,feeds,logseq,oauth,webhooks-inbound}`、`/webhooks/github`（`github_webhook.py:58`）。
- **Drift**：deep_audit 记"9 连接器 2 完全不存在"——现目录见 discord/feishu/slack/wecom/github/notion/logseq 7 个 + IM 子包，缺失项 `[TBD]` 须 05 核验（疑 notion 子目录结构 [TBD]）。

### M07 Web API/Frontend（`src/saw/drivers/web/` + `src/saw/api/`）
- FastAPI 装配：`app.py:165`；路由装配 `app.py:280-349`（include_router，含 auth_dep 鉴权依赖）。
- `drivers/web/routes/`：auth/graph/pages/search/import_md/capture/templates/entity_types/onboarding/timeline/websocket。
- `api/`：sync/connector_settings/github_webhook/health/feeds/oauth_callback/notion_sync/logseq/notion/github/webhook_inbound/integrations/dashboard_stats + `routes/{collaborate,govern,impact,query_ingest_learn}` + `integrations_ws`。
- middleware：`middleware/{cors,errors,observability,security}.py`；schemas：`schemas/{graph,pages,search,timeline,websocket}.py`。
- 前端：`web/`（React 19+Vite，见 CLAUDE.md）。
- **Drift**：两套路由（`api/` 与 `drivers/web/routes/`）prefix 体系不同——`api/` 多自带 `prefix="/api/v1/..."`，`drivers/web/routes/` 多在 `app.py` include 时挂 `prefix="/api"`。boundary 未统一，03 须规整（`api/routes/*` 与 `drivers/web/routes/*` 职责重叠 [TBD]）。

### M08 Auth/Security（`src/saw/auth/`）
- `jwt_auth.py`/`permissions.py`/`user_store.py`；`adapters/crypto/{ed25519,cedar_policy,_keyfiles}.py`；`adapters/url_guard.py`。
- 入口：`web:/api/auth/{register,login,refresh,logout,me,mode}`（`drivers/web/routes/auth.py`）。
- middleware：`security.py`（RBAC/限流/输入消毒，`app.py:267` auth_dep）。
- **Drift**：deep_audit 记"前后端认证体系各自独立互不通信"——`auth/jwt_auth.py` 与前端 token 互通 `[TBD]` 须 05 实机核验。

### M09 DB/Storage/WriteQueue（`src/saw/write_queue/` + `src/saw/adapters/storage/` + `src/saw/db/`）
- Write Queue：`queue.py`（SQLiteWriteQueue outbox）→ `dispatcher.py:16`（Dispatcher + `dispatch_pending`:37 + `recover`:126）→ `sinks/{vault,claims,wiki,fts5,graph,contradictions,connector}_sink.py`。
- Repos：`adapters/storage/{claims,vault,wiki}_repository.py` + `sqlite_connection.py` + `fts5_utils.py`/`fts_tokenize.py`。
- `db/`：schema/migration（1536 LOC，[TBD] 细节）。
- **约束**：唯一 mutation 网关，engine 不得直写 repo。

### M10 Platform Support
- `config/{settings,defaults,agent_templates}.py`、`onboarding/`、`plugins/`（SDK+hooks）、`token_optimizer/`、`templates/`、`context/`、`purpose/`、`reconcile/`、`research/`、`synthesize/`、`analysis/`、`graph/`、`audit/`、`tutorial/`。
- **Drift**：[TBD] 逐子模块边界待 03/05。

### M11 CLI（`src/saw/drivers/cli/`）
- 入口：`main.py:10` Typer `app`；命令 `commands/*_cmd.py` + 动态注册（code_graph/cli.py `register_code_graph_commands`、compile_cmd.py `register_compile_commands`）。
- 别名 i/q/s/w/v/l（`main.py` 末尾）。
- **Drift**：动态注册子命令逐条 file:line `[TBD]`（05 枚举）。

### M12 MCP（`src/saw/drivers/mcp/`）
- 服务：`server.py:27` FastMCP，`create_server`:81；工具 `tools/*.py` 用 `@mcp.tool`（61 工具，见 entry-points）。
- 附属：`config.py`/`prompts.py`/`resources.py`/`research_on_miss.py`。
- **Drift**：deep_audit 记"宣称 24+ 实际 6"已过时（现 61），README badge 须同步（README.md 已 v1.0.1，README_CN 已对齐）。

### M13 Research/Synthesize（`src/saw/research/` + `src/saw/synthesize/`）
- `research/`（715 LOC）、`synthesize/`（1818 LOC）、`learn/{adaptive,distiller,expiry,fsrs_scheduler,trends,adaptive_index,engine}.py`。
- 入口：`mcp:saw_{learn,distill,suggest,wip,status}`（`tools/learn.py`）、`mcp:saw_{challenge,connect,context,emerge,graduate}`（`tools/thinking.py`）、`web:/api/v1/{distill,prune,trends,wip,feedback}`。
- **Drift**：[TBD] learn engine 与 FSRS 调度链待 03。

## 3. 命名/错误/日志约定

- **命名**：engine 类 `XxxEngine`/`XxxPipeline`；repository `XxxRepository`/`SQLiteXxxRepository`；sink `XxxSink`；connector `XxxConnector`；agent 小写角色名。CLI 命令动词式（init/ingest/query/...），MCP 工具 `saw_<verb>`。
- **错误**：`domain/exceptions.py` 定义 `SAWError` 基类；Web 经 `middleware/errors.py:90` `@app.exception_handler(SAWError)` 统一映射；HTTP 用 `HTTPException`+`status`。
- **日志**：[TBD] 统一 logger 配置点未定位（grep `logging.getLogger` 散落各模块，03 须定规约）。
- **类型**：Python 强制 public API type hints（CLAUDE.md）；TS strict（`web/`）。
- **变更**：一切 mutation 经 write_queue；查询只读 repos。

## 4. Boundary Drift 汇总（00 阶段标注，正文修订归对应阶段）

| # | drift | 来源 | 处置 |
|---|---|---|---|
| D1 | 6 agent `execute()` 疑空实现 | deep_audit 2026-06-23 | 05 实机核验 |
| D2 | 连接器宣称 9 实际缺 2 | deep_audit | 05 核验 notion/缺失项 |
| D3 | 前后端认证互不通信 | deep_audit | 05 实机核验 jwt↔前端 |
| D4 | `api/` 与 `drivers/web/routes/` 路由双轨/prefix 不一 | 本蒸馏 | 03 规整 |
| D5 | 动态注册 CLI 子命令未枚举 file:line | 本蒸馏 | 05 枚举 |
| D6 | LLM 调用点/citation 解析链未落地 | 本蒸馏 | 05 深挖 |
| D7 | 统一日志规约缺失 | 本蒸馏 | 03 定规约 |
| D8 | deep_audit 版本号 v3.7.0 vs pyproject v1.0.1 | reconcile | 已在 reconcile-log 标注（历史快照不改） |

> 上述 drift 仅标注，不改业务代码/正文；具体修订归 03（设计）/05（实施）。

## 5. 蒸馏覆盖度与 [TBD]

- 入口点：CLI 37 / MCP 61 / Web 117 = 215 条（完整，grep 落地）。
- 调用图：6 主流程节点+边落地；深子调用 6 项 [TBD]（见 knowledge-graph.json `open_tbd`）。
- 模块：13 模块边界对齐 docs/audit；M10 平台支持子模块 [TBD]。
- 重跑：`bash scripts/cms_extract.sh` 重生成 entry-points.jsonl；代码变更后 05 auto-align 重写本 spec + 回写 manifest。

## 6. manifest 回写

本蒸馏产出 3 件，回写 manifest（source_type=cms，build_status=built）：
- `cms:saw:module-spec` → output_path=`.csp/code-spec/saw/CODE-MODULE-SPEC.md`
- `cms:saw:entry-points` → output_path=`.csp/code-spec/saw/entry-points.jsonl`
- `cms:saw:knowledge-graph` → output_path=`.csp/code-spec/saw/knowledge-graph.json`

---

## CMS Delta — v1.10.0 embedding（增量对齐）

### 新增入口点

| 类型 | 路径 | file:line | 说明 |
|---|---|---|---|
| Write Queue Sink | `saw.write_queue.sinks.embedding_sink.EmbeddingSink` | `src/saw/write_queue/sinks/embedding_sink.py:20` | 向量持久化 sink（write/can_handle/name 范式参照 FTS5Sink） |
| DB Migration | `saw.db.migrations._create_embedding_store` | `src/saw/db/migrations.py:~350` | v10: embedding_store 表（doc_id/entity_type/model/vector/dim/workspace_id） |
| CLI Command | `saw.drivers.cli.commands.search_cmd.rebuild_embeddings` | `src/saw/drivers/cli/commands/search_cmd.py:~150` | `saw rebuild-embeddings` 全量重建命令 |
| QueryEngine mode | `QueryEngine._semantic_search` | `src/saw/engines/query/engine.py:~300` | semantic mode 分支（cosine top-K） |
| REST param | `mode` on `GET /api/v1/search` | `src/saw/drivers/web/routes/search.py:18` | `default|tree|semantic` 枚举 |
| Write Queue op | `sink_name="embedding"` in `_build_write_ops` | `src/saw/engines/ingest/pipeline.py:~400` | 每个 claim 追加 embedding op |

### 新增调用链边

- `pipeline._build_write_ops → EmbeddingSink.write → embed_texts → INSERT embedding_store`
- `QueryEngine.query(mode=semantic) → _semantic_search → embed_texts + cosine_similarity → SELECT embedding_store WHERE workspace_id=?`
- `compute_related_pages(conn=…) → SELECT embedding_store → cosine_similarity` (Signal 4, weight 2.5)
- `links_cmd.suggest → detect_tier() ≥ FULL → compute_related_pages(conn=conn)`
- `search_cmd.search(mode=semantic) → _semantic_search → QueryEngine.query(mode="semantic")`

### 降级路径

- `EmbeddingSink.write()` → `embeddings_available()=False` → skip (no error, no vector)
- `QueryEngine._semantic_search()` → `embeddings_available()=False` → `_keyword_search()` + `semantic_fallback: true`
- `compute_related_pages(conn=…)` → `embeddings_available()=False` → 3-signal (embedding_score=0)

---

## CMS Delta — v1.11.0 债务收口 IV / bug fix（增量对齐）

### F-O-1: semantic search cache（复用 F-QS-07）

| 变更类型 | 位置 | file:line | 说明 |
|---|---|---|---|
| cache.get 插入 | `QueryEngine._semantic_search` 入口 | `src/saw/engines/query/engine.py:474-489` | `get_cache()` 单例 + `mode="semantic"` key 隔离 + workspace_id + limit/offset |
| cache.set 插入 | `QueryEngine._semantic_search` 出口 | `src/saw/engines/query/engine.py:~535-540` | `try/except _cache.set` + `logger.warning` 守卫 |
| cache.clear 钩子 | `rebuild_embeddings` 命令 | `src/saw/drivers/cli/commands/search_cmd.py:~163-166` | `conn.commit()` 后调 `get_cache().clear()` |
| 不缓存路径 | fallback / index_empty | `src/saw/engines/query/engine.py:~491-507` | 降级和空索引在 `cache.set` 之前 return |

新增调用链边：
- `_semantic_search → get_cache().get(question, {mode:"semantic",...})` → 命中返回
- `_semantic_search → get_cache().set(question, params, _qr)` → miss 后缓存
- `rebuild_embeddings → get_cache().clear()` → 重建后失效

### F-O-3: workflow REST 统一读 DB

| 变更类型 | 位置 | file:line | 说明 |
|---|---|---|---|
| 签名变更 | `list_workflows` | `src/saw/api/routes/collaborate.py:~328` | 增加 `request: Request` + `limit: Query(20)` 参数 |
| DB 读取 | `list_workflows` 主体 | `src/saw/api/routes/collaborate.py:~340-360` | `SELECT ... FROM workflow_executions ORDER BY COALESCE(updated_at, started_at) DESC LIMIT ?`（与 CLI `list_recent` 同源） |
| live merge | `list_workflows` 循环 | `src/saw/api/routes/collaborate.py:~365-390` | in-memory `_workflows` running 覆盖 DB stale + not-in-DB 追加 |
| conn 获取 | `list_workflows` 入口 | `src/saw/api/routes/collaborate.py:~332-336` | `getattr(request.app.state, "conn", None)` → fallback `getattr(query, "_conn", None)` |
| auto-migrate | `list_workflows` | `src/saw/api/routes/collaborate.py:~339` | `apply_migrations(conn)` 确保 v4 表 |
| fallback | `list_workflows` | `src/saw/api/routes/collaborate.py:~337` | `conn is None` → in-memory only（向后兼容） |

---

## CMS Delta — v1.12.0 (2026-09-05)

### embed_texts API provider 重构

| 改动 | file:line | 说明 |
|---|---|---|
| `embed_texts()` 改调 `litellm.embedding()` | `src/saw/adapters/embeddings.py:155-175` | 三级路由 API→ST→None；`_embed_via_api()` 调 `litellm.embedding(model=cfg.model, input=texts, api_base=cfg.api_base, api_key=cfg.api_key)` |
| `_get_embedding_settings()` 从 env 读取配置 | `src/saw/adapters/embeddings.py:42-70` | 读 `SAW_EMBEDDING_MODEL`/`EMBEDDING_API_KEY`/`OPENAI_API_KEY`/`SAW_EMBEDDING_API_BASE`/`OPENAI_BASE_URL` |
| `_api_embedding_available()` | `src/saw/adapters/embeddings.py:72-86` | 检测 model + api_key 或 api_base 配置 |
| `_st_available()` / `_embed_via_st()` | `src/saw/adapters/embeddings.py:88-120` | 本地 ST fallback（v1.10.0 路径保留） |
| `_normalize()` | `src/saw/adapters/embeddings.py:122-127` | L2 范数化 API 向量 |
| `_current_model_name()` | `src/saw/adapters/embeddings.py:177-184` | 动态 model 列值（API model 名 or `all-MiniLM-L6-v2` fallback） |
| `embeddings_available()` | `src/saw/adapters/embeddings.py:130` | `_api_embedding_available() or _st_available()` |
| `EmbeddingSettings` 新增 | `src/saw/config/settings.py:29-38` | model/api_key/api_base/timeout，复用 LLMSettings 范式 |
| `_embeddings_available()` 改 API OR ST | `src/saw/config/settings.py:122-133` | `_api_embedding_configured()` OR `importlib.import_module("sentence_transformers")` |
| `_api_embedding_configured()` | `src/saw/config/settings.py:136-155` | 读 env 检测 API 配置 |
| `EmbeddingSink.write()` model 列动态 | `src/saw/write_queue/sinks/embedding_sink.py:40` | `_current_model_name()` 替换硬编码 |
| `_upsert_embedding()` model 列动态 | `src/saw/drivers/cli/commands/search_cmd.py:265` | `_current_model_name()` 替换硬编码 |
| `tests/conftest.py` | `tests/conftest.py:1-8` | `LITELLM_LOCAL_MODEL_COST_MAP=True`（skip litellm remote fetch） |

### 调用链（不变）
- `EmbeddingSink.write()` → `embed_texts()` → `_embed_via_api()` / `_embed_via_st()` → `_normalize()`
- `QueryEngine._semantic_search()` → `embed_texts()` + `embeddings_available()` (lazy import in function)
- `compute_related_pages()` → `embeddings_available()` + `cosine_similarity()` (lazy import in function)
- `rebuild_embeddings()` → `embed_texts()` (probe dim) + `_upsert_embedding()`

## v1.13.0 Delta — E2E 收尾轮（ingest 递归 + REST 别名）

### 新增/改动点（ground 自源码，file:line）

| 改动 | file:line | 说明 |
|---|---|---|
| `ingest()` 入口加目录递归分支 | `src/saw/engines/ingest/pipeline.py:108-130` | `Path(source).is_dir()` → `_ingest_directory()` 用 `os.walk` 递归枚举子文件 |
| `_ingest_directory()` | `src/saw/engines/ingest/pipeline.py:144-192` | os.walk prune noise dirs → 逐文件 `_ingest_single_file()` → 聚合 `IngestResult(parser="directory-batch")` |
| `_ingest_single_file()` | `src/saw/engines/ingest/pipeline.py:204+` | 原 `ingest()` 单文件逻辑提取为内部方法（classify→extract→fuse→validate→enqueue） |
| `_NOISE_DIRS` 常量 | `src/saw/engines/ingest/pipeline.py:103-107` | frozenset: `.git/.saw/node_modules/.venv/venv/__pycache__/.mypy_cache/.ruff_cache/.pytest_cache` |
| `classifier.py` is_dir→UNKNOWN | `src/saw/engines/ingest/classifier.py:149-155` | 目录返回 `DocumentFormat.UNKNOWN`（不再猜格式），pipeline 入口拦截 |
| REST durable item 加 `name`/`workflow` 别名 | `src/saw/api/routes/collaborate.py:373-374` | `"name": name` + `"workflow": name`（= `definition_name` 镜像） |
| REST live item 加 `name`/`workflow` 别名 | `src/saw/api/routes/collaborate.py:401-402` | 同上，live merge 分支 |
| benchmark 脚本 | `scripts/benchmark_semantic.py:1-260` | 独立可执行：vLLM health check → 数据集 → BM25/semantic recall → P99 → cache hit → JSON |
| CHANGELOG.md | `CHANGELOG.md:1-80` | 项目根，Keep a Changelog 格式，回溯 v1.10.0–v1.13.0 |
| coverage fail_under 65→67 | `pyproject.toml:127` | ratchet gate |
| benchmark_e2e marker | `pyproject.toml:99-100` | CI 无 vLLM skip |

### 调用链（增量）
- `ingest()` → `Path(source).is_dir()` → `_ingest_directory()` → `os.walk` → `_ingest_single_file()` → classify→extract→fuse→validate→enqueue
- `list_workflows()` → DB rows → `items.append({..., "name": name, "workflow": name})` → merge live → sort → return
- `scripts/benchmark_semantic.py` → `embed_texts()` (API path) → `_semantic_search`/`_keyword_search` → P99 + cache hit

## v1.14.0 Delta — semantic 性能优化（cache 可配 + ANN 索引 + benchmark）

### 新增/改动点（ground 自源码，file:line）

| 改动 | file:line | 说明 |
|---|---|---|
| `_semantic_cache_enabled()` | `src/saw/config/settings.py:239-251` | 读 `SAW_SEMANTIC_CACHE_ENABLED` env，默认 true；"false"→False，非法值→True+warning |
| `_semantic_cache_threshold_ms()` | `src/saw/config/settings.py:254-265` | 读 `SAW_SEMANTIC_CACHE_THRESHOLD_MS` env，默认 0=不设阈值；>0 时 API 延迟<阈值跳过 cache.set |
| `_semantic_search` cache 条件分支 | `src/saw/engines/query/engine.py:487-499` | cache.get/set 受 `_cache_enabled` + `_threshold_ms` 控制（T-F-S-1） |
| `_semantic_search` embedding 计时 | `src/saw/engines/query/engine.py:521-522` | `time.perf_counter()` 度量 embed_texts 调用，供 threshold 判断 |
| `_semantic_search` 规模驱动 ANN | `src/saw/engines/query/engine.py:543-558` | `doc_count > SAW_ANN_THRESHOLD` → ANN；≤ → numpy batch cosine；失败→fallback |
| `_cosine_search_batch()` | `src/saw/engines/query/engine.py:617-638` | numpy batch cosine helper（struct.unpack + `batch_cosine_similarity`） |
| `_ann_search()` | `src/saw/engines/query/engine.py:640-685` | hnswlib lazy load/build `.saw/ann_index_<ws>.bin` + `knn_query` + distance→sim 转换 |
| `_ann_index` 类属性 | `src/saw/engines/query/engine.py:614` | class-level None default，per-instance override |
| `batch_cosine_similarity()` | `src/saw/adapters/embeddings.py:297-318` | numpy 矩阵乘 + L2 normalize，返回 list[float]（T-F-S-2） |
| `related_pages.py` batch-load | `src/saw/engines/query/related_pages.py:82-98` | 单次 SELECT 加载所有候选 embedding（替代 per-page SELECT+cosine, AC-B-5） |
| `pyproject.toml` [semantic] extra | `pyproject.toml` | `semantic = ["hnswlib>=0.7"]`（MIT, 无 faiss/torch） |
| benchmark `_measure_cache_hit` | `scripts/benchmark_semantic.py:171-191` | 改为 `cache.stats().hits` 计数（非 `lat2 < lat1*0.5`） |
| benchmark `_measure_ann_vs_cosine` | `scripts/benchmark_semantic.py:194-212` | 强制 ANN/cosine 路径，分别 P99 |
| benchmark `_measure_scale_curve` | `scripts/benchmark_semantic.py:224-253` | 100/500/1000/5000 合成随机向量数据集 P99 曲线 |
| benchmark `_semantic_search` | `scripts/benchmark_semantic.py:138-160` | 改为通过 `QueryEngine._semantic_search` 生产路径 |

### 调用链（增量）
- `QueryEngine._semantic_search()` → `_semantic_cache_enabled()` + `_semantic_cache_threshold_ms()` → cache.get (conditional) → `embed_texts()` (timed) → `_ann_search()` or `_cosine_search_batch()` → resolve sources → cache.set (conditional)
- `_ann_search()` → `hnswlib.Index(space='cosine')` → `load_index`/`init_index`+`add_items` → `knn_query` → (doc_id, sim) pairs
- `_cosine_search_batch()` → `struct.unpack` → `batch_cosine_similarity()` (numpy matrix multiply) → sorted pairs
- `compute_related_pages()` → `SELECT ... embedding_store WHERE workspace_id=?` (batch) → `cosine_similarity()` per candidate (from pre-loaded dict)
- `scripts/benchmark_semantic.py` → `_make_query_engine()` → `engine._semantic_search()` → `cache.stats().hits` (cache hit) + `_measure_ann_vs_cosine` + `_measure_scale_curve`

## v1.15.0 Delta — agent/link 能力（自定义角色注册 + links apply + 活动聚合）

### 新增/改动点（ground 自源码，file:line）

| 改动 | file:line | 说明 |
|---|---|---|
| `load_custom_agents()` | `src/saw/engines/collaborate/agents/__init__.py:83-152` | 扫描 `.saw/agents/*.yaml`，`yaml.safe_load` 解析 + 校验 name/model_tier/system_prompt/tools_allowed/constraints，重名/非法 tier/空 prompt/YAML 错误 → 跳过+warning 不阻断（T-F-T-1） |
| `build_agent_roster()` | `src/saw/engines/collaborate/agents/__init__.py:157-166` | additive 合并 `build_default_agents` + `load_custom_agents`（不改 `build_default_agents` 源码/签名，T-F-T-1） |
| `list_agents()` REST custom 字段 | `src/saw/api/routes/collaborate.py:446-472` | 改调 `build_agent_roster`，返回 `custom: true/false` + `activity_summary`（T-F-T-1/T-F-T-3） |
| `GET /agents/{name}/activity` REST | `src/saw/api/routes/collaborate.py:475-502` | 新增端点：200 有活动/200 空活动 calls=0/404 agent 不存在（T-F-T-3） |
| `AgentActivityTracker` 类 | `src/saw/engines/collaborate/activity_tracker.py:25-110` | `subscribe(event_bus)` → `add_subscriber("WorkflowStep", handler)` + `_handle_event` 解析 `{agent}.{action}` + `status` 更新内存计数器 + `get_activity`/`get_summary`（T-F-T-3） |
| `app.py` lifespan tracker init | `src/saw/drivers/web/app.py:60-72` | lifespan 初始化 `AgentActivityTracker` + subscribe event_bus + 模块级单例 `get_activity_tracker`/`set_activity_tracker`（T-F-T-3） |
| `app.py` engine 用 `build_agent_roster` | `src/saw/drivers/web/app.py:~290` | `create_app_from_config` 改调 `build_agent_roster` 替代 `build_default_agents`（T-F-T-1） |
| `agents_cmd.py` Typer sub-app | `src/saw/drivers/cli/commands/agents_cmd.py:1-91` | 转为 Typer sub-app（`invoke_without_command=True`）+ `custom` 列 + `saw agents activity <name>` 子命令（T-F-T-1/T-F-T-3） |
| `main.py` agents sub-app 注册 | `src/saw/drivers/cli/main.py:107` | `app.command(name="agents")(agents)` → `app.add_typer(agents_app, name="agents")` |
| `workflow_parser.py` validate 默认 roster | `src/saw/engines/collaborate/workflow_parser.py:~105-112` | `validate()` 的 `available_agents` 参数默认 `None` → 自动取 `build_agent_roster` keys（含自定义角色，T-F-T-1） |
| `workflow_cmd.py` lint 用 roster | `src/saw/drivers/cli/commands/workflow_cmd.py:~162-165` | CLI lint 改调 `build_agent_roster`（T-F-T-1） |
| `links_cmd.py` apply 子命令 | `src/saw/drivers/cli/commands/links_cmd.py:73-214` | `saw links apply <page> [--confirm] [--top N] [--dry-run] [--suggestion <slug>]`：复用 `compute_related_pages` + 去重 + dry-run/confirm + `WikiRepository.write()` 写回 `## Related` + frontmatter `related` 同步（T-F-T-2） |

### 调用链（增量）
- `build_agent_roster()` → `build_default_agents()` (unchanged) → `load_custom_agents()` → `yaml.safe_load` per `.saw/agents/*.yaml` → `BaseAgent(name, model_tier, system_prompt, tools_allowed)` → `dict.update(custom)`
- `GET /api/v1/agents` → `build_agent_roster(llm_router=None)` → `get_activity_tracker()` → per-agent `tracker.get_summary(name)` → `activity_summary`
- `GET /api/v1/agents/{name}/activity` → `build_agent_roster` (404 check) → `get_activity_tracker()` → `tracker.get_activity(name)`
- `AgentActivityTracker.subscribe(bus)` → `bus.add_subscriber("WorkflowStep", handler)` → `WorkflowExecutor._publish_event({"type":"WorkflowStep",...})` → `bus._dispatch` → `handler._handle_event` → split `{agent}.{action}` → `dict[agent]["calls"] += 1`
- `saw links apply` → `compute_related_pages()` → `extract_unique_targets` (dedup) → dry-run table or `WikiRepository.write(WikiPage)` (## Related + related sync)
