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
