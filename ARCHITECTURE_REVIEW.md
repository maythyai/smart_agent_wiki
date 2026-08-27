# Smart Agent Wiki — 架构审计报告

**审计日期**: 2026-08-24
**审计范围**: `/Users/cs/projects/smart_agent_wiki` (src/saw,537 Python 文件,~74k 行)
**审计方法**: 1 个 Explore agent 摸清结构 + 5 个 general-purpose agent 并行深挖 12 维度 + 主审对 Critical/High 逐条交叉验证

> **验证说明**: 本报告所有 Critical/High 发现已由主审亲自打开对应行号确认(标注 **[已交叉验证]**),排除误报。Medium/Low 均附 `file:line` 证据并由 agent 读取真实代码得出。可按条目深挖或出修复草案。

---

## 1. 执行摘要

Smart Agent Wiki (SAW) 是一个 local-first 多代理知识平台,采用**六边形架构**(domain → engines → adapters → drivers),宣称五大引擎(Ingest/Query/Govern/Learn/Collaborate)、Write Queue 单一变更网关、Connectors 框架(7 平台)、6 专用 agent、插件 + 事件总线微内核。

**设计意图评价**: 架构意图清晰且文档完备——分层契约、outbox 模式、能力分级(OFFLINE/LIGHTWEIGHT/FULL)、连接器抽象。domain 层(pure Python, protocols/entities/value_objects)确实干净无上行依赖。迁移框架(PRAGMA user_version,幂等)与 FTS5 CJK 预分词(jieba→unicode61)是两处扎实的工程。

**执行落差(原)**: 多个"展示性架构"子系统**从未接线**——Write Queue dispatcher 在 web 模式不启动(所有 web 写静默丢失)、事件总线恒为 None、ConnectorRegistry 从不注册、Govern 引擎不挂载(503)。分层契约被系统性破坏(路由直接 `repo._conn.execute` 裸 SQL、`import sqlite3`、伸手进 engine 私有属性)。两条 Critical 安全路径:`saw web` 默认 `auth_mode="local"`(无鉴权 admin 信任)且 docker-compose 以 `--host 0.0.0.0` 暴露;team 模式下任意 `ApiKey <非空>` 头即获 admin 而无任何 DB 校验。异步层普遍在 `async def` 内做同步 sqlite3/SQLAlchemy 阻塞调用。

**修复落地(2026-08-26)**: Critical 5/5 与 High 17/18 已全部修复并经 302+11 项测试验证(仅 HI-14 密钥轮换需人工)。Write Queue dispatcher 已接线且加 CAS+定期 recover;事件总线(`InMemoryEventBus`)已实现并激活 WS 广播/工作流事件/插件订阅;插件与 7 连接器 bootstrap 已接线;Govern 引擎挂载;工作流条件求值修复+执行态持久化+崩溃恢复;25 个 async 路由改 `def`;SSRF 防护覆盖 4 处采集/投递点;OAuth 假凭据回退移除;容器非 root+真健康检查+资源限制;可观测性具备 request-id 传播+结构化日志+可选 Sentry+Prometheus `/metrics`;分层 SQL 下沉仓储。详见 §6。

**优先级建议(后续)**: 剩余为 Medium 加固项与性能/可伸缩性演进——见 §7 后续任务决策。

---

## 2. 架构成熟度总览(12 维度,5 分制)

| # | 维度 | 评分 | 一句话(修复后) |
|---|------|------|--------|
| 1 | 架构分层与模块边界 | 2→**3/5** | HI-1 将 govern/qil 路由裸 SQL 下沉仓储;但 import_md 仍绕 outbox、路由伸手私有属性(M-2)残留 |
| 2 | API 设计与契约一致性 | 2→**3/5** | ApiKey 绕过 + local 暴露已修;但版本前缀不统一/分页无上限/错误体两套(M-6/7/10/11)残留 |
| 3 | 数据层 | 3→**4/5** | write-queue CAS + 定期 recover + 工作流持久化表已加;但 FK 索引缺失(M-13)、双持久化(M-3)残留 |
| 4 | 异步与并发模型 | 2→**3/5** | 25 个 async→def 修复阻塞;但 feeds 混合 handler、/metrics rglob、health 探针(M-9/10)残留 |
| 5 | 编排/工作流引擎 | 2→**3/5** | 条件求值修复 + 执行态持久化 + 崩溃恢复;但状态枚举(M-16)、rollback(M-14)、死信告警(M-15)残留 |
| 6 | 可扩展性与插件体系 | 1→**3/5** | 事件总线 + 插件 bootstrap + 连接器 bootstrap 全部接线激活;插件事件 emit 与连接器凭据加载为后续 |
| 7 | 安全性 | 2→**4/5** | ApiKey + local + SSRF + OAuth test_token 全修;WeCom 时序/重放(M-24/25)、webhook secret 明文(M-26)、GitHub 空 secret(M-23)残留;HI-14 待人工轮换 |
| 8 | 配置与可部署性 | 2→**4/5** | 静默 in-memory fallback 移除、Dockerfile 本地安装、非 root+真健康检查+资源限制、.pth 根因修复;版本号漂移(M-18)残留 |
| 9 | 可观测性 | 1→**3/5** | request-id 传播 + 结构化日志 + 可选 Sentry + /metrics Prometheus 已就绪;metrics 仍稀疏、trace_id 未入 write_queue/connector 日志 |
| 10 | 性能与可伸缩性 | 2/5 | 未动:SQLite 单文件 + 进程内 Lock 不可水平扩展、采集并发无上限、FULL 能力层系愿景(M-19/20) |
| 11 | 测试与质量 | 2→**3/5** | .pth 根因修复 + 11 个回归测试守护;但缺架构守护测试(M-21)、write-queue 并发测试(M-22) |
| 12 | 代码组织与可维护性 | 3/5 | 未动:14 个 >500 行 god file、事件类重复定义(L-1)、私有属性双名 fallback(M-2) |

**综合(修复后)**: ~**3.2/5**(原 2.0/5)。Critical 5/5、High 17/18 已修复并经测试验证;主写路径不再静默丢数据、主鉴权路径不再绕过、事件总线/插件/连接器/Govern/工作流引擎全部从"展示性"转为"已接线";剩余为 Medium/Low 加固项与性能/可伸缩性演进。

---

## 3. 问题清单(按严重度排列)

### 🔴 Critical

#### CR-1 [安全] ApiKey 鉴权绕过:任意非空 `ApiKey` 头即获 admin [已交叉验证]
- **问题**: team(生产)模式下,`get_current_user_from_token` 对任何 `Authorization: ApiKey <非空>` 头直接返回 `role:"admin"`,从不查询 `api_keys` 表。
- **证据**: `src/saw/drivers/web/middleware/security.py:267-281`(ApiKey 分支返回 admin,注释称"actual verification happens in RateLimitMiddleware"——但该验证不存在);`src/saw/api/keys.py:verify_api_key_header`(仅提取 key 串做限流分桶,不校验);`src/saw/api/rate_limit.py:231-237`(`await self.get_api_key_func(key_str)` 传字符串,但 `verify_api_key_header(request)` 期望 Request 对象 → 签名不匹配,调用即崩);`src/saw/drivers/web/app.py:148-150`(接线处)。
- **影响**: team 模式下攻击者发 `Authorization: ApiKey x` 即获全部受保护路由 admin(pages/govern/sync/connector settings/collaborate 工作流)。默认配置(限流开启)下表现为所有 ApiKey 请求 500(DoS);限流关闭时为直接提权。
- **严重度**: Critical
- **建议**: 在 `get_current_user_from_token` 内调用 `APIKeyService.verify_key()`(DB 查找 + SHA256 比对 + 过期/active 校验),返回 key 的真实权限;修正 `get_api_key_func` 签名为 `async def(key_str)->APIKey|None`。限流与鉴权解耦,不得互为前提。

#### CR-2 [安全] `saw web` 默认 local(无鉴权 admin)模式,docker-compose 以 0.0.0.0 暴露 [已交叉验证]
- **问题**: `create_app_from_config` 调 `create_app(...)` 不传 `auth_mode` → 默认 `"local"`(信任所有未鉴权请求为 admin);compose 显式 `web --host 0.0.0.0`。
- **证据**: `src/saw/drivers/cli/commands/web_cmd.py:70`(`create_app_from_config(cors_origins=..., host=host, port=port)` 无 auth_mode);`src/saw/drivers/web/app.py:445`(`return create_app(...)` 无 auth_mode 参数)与 `:49`(`auth_mode: str = "local"` 默认);`docker-compose.yml`(`command: web --host 0.0.0.0 --port 8000`)。
- **影响**: 官方容器部署把完整 admin API 无鉴权暴露给网络;app.py:98-104 的启动 warning 在容器日志里极易被忽略。
- **严重度**: Critical
- **建议**: `create_app_from_config` 从 `.saw/config.yaml` 或 `SAW_AUTH_MODE` 读 auth_mode 并传入;当 `host==0.0.0.0` 且 `auth_mode=="local"` 时拒绝启动(除非显式 `--dangerously-allow-unauth`)。

#### CR-3 [架构] Write Queue dispatcher 在 web 模式从不启动 → 所有 web 写静默丢失 [已交叉验证]
- **问题**: `enqueue_atomic` 入队后即返回(注释"caller should invoke dispatch_pending"),但 web 应用从不构造 Dispatcher、从不 dispatch;API 返回 200 "queued" 但数据从未落盘到 sink。
- **证据**: `src/saw/drivers/web/app.py:80-82`(write_queue 仅存入 app.state)与 `lifespan:19-33`(仅启动 WS broadcaster,无 dispatcher);`src/saw/write_queue/queue.py:125-128`(`enqueue_atomic` 仅 enqueue);`src/saw/drivers/web/routes/pages.py:187`(`write_queue.enqueue_atomic(ops)` 返回 `PageStatus(status="queued")`);全仓仅 `drivers/cli/commands/ingest_cmd.py` 调 `dispatch_pending`。
- **影响**: 经 web API 的全部变更(页面增删改、模板、capture、timeline、onboarding、collaborate 发布)被静默吞掉;wiki 与 FTS5 实际与 API 报告不一致。主写路径静默数据丢失。
- **严重度**: Critical
- **建议**: 在 `create_app_from_config` 构造 `Dispatcher`(注册 wiki/fts5/claims/graph 等 sink),于 `lifespan` 启动后台 worker 或在 `enqueue_atomic` 后内联 dispatch(如其 docstring 所承诺)。

#### CR-4 [配置] 静默回退内存数据库 → 重启即全量数据丢失 [已交叉验证]
- **问题**: `create_app_from_config` 打开真实 DB 时任何异常都 `except Exception` 回退 `sqlite3.connect(":memory:")`,无错误日志。
- **证据**: `src/saw/drivers/web/app.py:361`(`except Exception: conn = sqlite3.connect(":memory:", check_same_thread=False)`)。
- **影响**: 生产环境瞬时 DB 错误(权限/损坏/磁盘满)使应用"正常"启动但写全丢,重启即空。运维看到健康服务、数据蒸发。
- **严重度**: Critical
- **建议**: 移除兜底 `except Exception`;DB 打不开即 fail-fast。可选特性降级(CollaborateEngine/wiki 索引)记 ERROR 并经 `/health` 暴露降级状态。

#### CR-5 [配置] Dockerfile 从 PyPI 安装而非本地源码 [已交叉验证]
- **问题**: `RUN pip install smart-agent-wiki` 无 `COPY src/`,镜像装的是 PyPI 已发布版本,不含本地未发布代码。
- **证据**: `Dockerfile:28`(`RUN pip install smart-agent-wiki`,无 COPY src/、无 `pip install .`)。
- **影响**: `docker build` 产出镜像与本地代码库不一致;版本号亦冲突(Dockerfile LABEL 3.4.0 vs pyproject 1.0.1 vs app.py 1.1.0 vs health.py 2.0.0)。
- **严重度**: Critical
- **建议**: 改 `COPY . /app && pip install /app`(或多阶段构建本地安装);统一版本号自 `pyproject.toml` 派生。

---

### 🟠 High

#### HI-1 [架构] Govern/Query API 路由裸 SQL 直打 repository 私有 `_conn`,绕过仓储层与 Write Queue [已交叉验证]
- **问题**: 路由 `import sqlite3` 并 `repo._conn.execute(...).fetchall()`/`.commit()`,含直接 `UPDATE claim SET deleted_at=?` 软删(绕过 outbox)与 `UPDATE claim SET confidence=?`。
- **证据**: `src/saw/api/routes/govern.py:11`(`import sqlite3`),`:74`(`conn.execute(sql,params).fetchone()`),`:119-120`/`:158-162`(`UPDATE claim SET confidence` + `.commit()`),`:181-190`(裸 `SELECT * FROM contradictions`),`:234-238`(`UPDATE contradictions` + commit),`:288-289`,`:409-410`;`src/saw/api/routes/query_ingest_learn.py:57,430-436`(`UPDATE claim SET deleted_at` 软删绕 outbox)。
- **影响**: 六边形契约(API→Service→Repository→ORM)被破坏;改后端/改 schema 需改路由;prune 软删绕过 outbox 的幂等/重试/可恢复性,崩溃即半删无恢复。
- **严重度**: High
- **建议**: 在 `ClaimsRepository` protocol 增 `update_confidence`/`list_contradictions`/`soft_delete` 等方法,SQL 全部下沉仓储;路由不得持 `_conn`。

#### HI-2 [架构] 事件总线恒为 None → 跨引擎通信、WS 广播、工作流事件投递全部死代码 [已交叉验证]
- **问题**: `create_app_from_config` 不传 `event_bus` → 默认 None;全仓无 `EventBus` 类。
- **证据**: `src/saw/drivers/web/app.py:445`(无 event_bus 参数);`:30`(`if ... event_bus is not None:` 恒 False → broadcaster 不启动);`src/saw/engines/collaborate/workflow_executor.py:407-414`(`_publish_event` 中 `if self._event_bus and hasattr(...,"publish")` 恒 False,事件仅 debug 日志);全仓 grep `class.*EventBus` 无命中。
- **影响**: 工作流进度事件不发布、WS 仪表盘无实时更新、插件事件系统无投递机制;"微内核+事件总线"为装饰性架构。
- **严重度**: High
- **建议**: 实现 `InMemoryEventBus`(publish/subscribe),于 `create_app_from_config` 实例化并注入 `create_app`/`WorkflowExecutor`/WS manager。

#### HI-3 [架构] `app.state.govern` 从不设置 → Govern 引擎经 API 不可达(503) [已交叉验证]
- **问题**: `create_app` 设 query/collaborate/write_queue/event_bus/wiki_repo/host/port/auth_mode/cedar,但不设 govern;govern 路由依赖 `request.app.state.govern`。
- **证据**: `src/saw/drivers/web/app.py:79-92`(state 赋值块无 govern;仅 `:286` import govern_router);`src/saw/api/routes/govern.py:43-49`(`_contradiction_detector` 取 `app.state.govern`,为 None 时 503)。
- **影响**: 矛盾检测/置信评估/新鲜度跟踪经 web API 不可达;凡调 `_contradiction_detector` 的端点返 503。
- **严重度**: High
- **建议**: `create_app_from_config` 构造 `Governor`(含 ContradictionDetector/ConfidenceAssessor/FreshnessTracker)经 `create_app` 传入并存 `app.state.govern`。

#### HI-4 [扩展] 插件系统在 web 运行时不加载、插件事件从不 emit [已交叉验证]
- **问题**: `PluginRegistry` 仅在 CLI `saw plugin` 命令中实例化管理(list/enable),web 运行时(`create_app`/`create_app_from_config`/各 engine)从不加载已启用插件;6 个插件事件(PageCreated/PageUpdated/...)从不被任何 engine/路由 emit。
- **证据**: `src/saw/drivers/cli/commands/plugin_cmd.py:22,74,102`(仅 CLI 实例化);`src/saw/plugins/registry.py`(discover/load/enable);`create_app`/`create_app_from_config`/engines 内无 `PluginRegistry(` 实例化;`src/saw/plugins/events.py` 6 事件类型全仓无 emit 点。
- **影响**: 第三方插件经 web/agent 运行时不可用;6 个插件事件为死代码。CLI 可"管理"插件但运行时不生效。
- **严重度**: High
- **建议**: `create_app_from_config` 实例化 PluginRegistry→discover→enable 已配置插件,注入带 `subscribe_event`/`publish_event` 的 PluginContext;Write Queue dispatcher 写成功后 emit `PageCreated/PageUpdated`。

#### HI-5 [扩展] 无任何 connector 注册 — ConnectorRegistry 恒空,所有 connector API 返 404 [已交叉验证]
- **问题**: 各 API 路由 `registry = ConnectorRegistry()` 后 `registry.get("github"/"notion"/...)`,但全仓无 `registry.register(connector)` 调用,registry 恒空。
- **证据**: 全仓 grep `registry.register(` 无命中;`src/saw/api/github.py:80-83`(`registry.get("github")` → None → 404 "GitHub connector not registered");`src/saw/api/notion.py:64-70`、`notion_sync.py:79-85`、`sync.py:152-153,210-211`、`connector_settings.py:258-264` 同样返 None/404。
- **影响**: 连接器框架在协议层"开闭原则"友好,但功能上死亡——新增 connector 不止实现 BaseConnector 还需找到 bootstrap 点(不存在);Notion/GitHub/Slack/Logseq API 全部 404。
- **严重度**: High
- **建议**: 增 `register_default_connectors(registry)` bootstrap 于 `create_app_from_config`;更佳用 `importlib.metadata.entry_points` 让 connector 自注册,实现真开闭。

#### HI-6 [数据] `mark_processing` 无 CAS 守卫 → 并发 dispatcher 重复认领/重复执行同一 op [已交叉验证]
- **问题**: `UPDATE write_outbox SET status='processing' ... WHERE op_id=?`(无 `AND status IN('pending','failed')`);get_pending 与 mark_processing 间有锁释放窗口。
- **证据**: `src/saw/write_queue/queue.py:115-121`;`src/saw/write_queue/dispatcher.py:68-70`。
- **影响**: 多 dispatcher(team 部署)重复写 sink(wiki/vault/连接器外部副作用)。sink 设计幂等,但幂等不完美即双写。
- **严重度**: High
- **建议**: 改条件 UPDATE:`... WHERE op_id=? AND status IN('pending','failed')`,检查 `cursor.rowcount`(0 即已被认领,跳过);或 `UPDATE...RETURNING` 原子认领。

#### HI-7 [数据] `get_pending` 排除 `processing` 且 `recover()` 从不被调用 → 崩溃 op 永久滞留(静默写丢失) [已交叉验证]
- **问题**: `WHERE status IN('pending','failed')` 不含 processing;进程在 mark_processing 后、mark_done 前崩溃则 op 永驻 processing,对 get_pending 不可见、不重试、不死信。
- **证据**: `src/saw/write_queue/queue.py:98-108`;`src/saw/write_queue/dispatcher.py:97-112`(`recover()` 存在但全仓无调用)。
- **影响**: OOM/SIGKILL/断电后该写永久丢失,用户无感知。
- **严重度**: High
- **建议**: 启动时调 `dispatcher.recover()`;增定期后台任务按陈旧阈值(如 updated_at > 5min)reset processing→pending;或加 `processing_timeout` 列纳入 get_pending。

#### HI-8 [编排] `_eval_condition` 用 `bool(Template.render())` → step 条件恒真,条件分支静默失效 [已交叉验证]
- **问题**: Jinja2 渲染 `{{ confidence > 3 }}` 为字符串 `"True"`/`"False"`,`bool("False")==True`(非空串恒真)。
- **证据**: `src/saw/engines/collaborate/workflow_executor.py:382-399`(`return bool(Template(f"{{{{ {condition} }}}}").render(**context))`),`:217`(调用处 `if step.condition and not self._eval_condition(...): return {"skipped": True}`)。
- **影响**: YAML 工作流带 `condition` 的步骤从不跳过;条件分支完全失效(仅当引用未定义变量时渲染空串才"偶然"为 False)。
- **严重度**: High
- **建议**: 用 Jinja2 `Environment.compile_expression`(返回原生 bool),或 `result.strip().lower()=="true"`,或换 `simpleeval` 做布尔求值。

#### HI-9 [编排] 工作流无崩溃续跑 — 全部执行态在内存,workflow_id 不持久化 [已交叉验证]
- **证据**: `src/saw/engines/collaborate/workflow_executor.py:92-96`(`workflow_id=str(uuid.uuid4())` 不入库,`context=dict(inputs)` 仅内存);`execute_definition:99-155` 无中间态持久化,仅完成时返 `WorkflowResult`。
- **影响**: 长任务(ingest/多代理协作/compile)崩溃即从头重跑,重做昂贵 LLM 调用与重摄入;无执行审计轨迹。
- **严重度**: High
- **建议**: 持久化 `workflow_executions` 表(workflow_id/definition/current_step/context_json/status/started/updated);启动扫描 `status='running'` 续跑或标记 failed;每步完成后更新行。

#### HI-10 [异步] `async def` 路由内同步 SQLAlchemy Session 调用阻塞事件循环 [已交叉验证]
- **证据**: `src/saw/api/feeds.py:194`(`async def list_feeds`)`:197`(`db: Session = Depends(get_db_session)` 同步 Session)`:203-209`(`db.query(Feed).all()`)`:214-216`(per-feed `db.query(FeedEntry).count()` N+1);`:347-348`(`db.commit()`/`db.refresh()`);`get_db_session` 为同步生成器(由 `create_engine(check_same_thread=False)` 支撑)。
- **影响**: 每个查询阻塞单线程事件循环;负载下整个进程停滞(其他请求/WS/后台任务不推进)。
- **严重度**: High
- **建议**: 改为普通 `def`(FastAPI 以线程池跑)或迁 `AsyncSession`+`await session.execute(...)`。

#### HI-11 [异步] `async def` govern/learn 路由内裸同步 `conn.execute/.commit` [已交叉验证]
- **证据**: `src/saw/api/routes/govern.py:119,158-162,181-189,234-238,288,409`;`src/saw/api/routes/query_ingest_learn.py:62,299,317,336,344,351`(共享 `check_same_thread=False` sqlite3 连接)。
- **影响**: lint/blast-radius/trends/prune(扫每行 claim)冻结事件循环;并发 WS 广播与其他请求停滞。
- **严重度**: High
- **建议**: `await run_in_threadpool(...)` 或改 `def`;确保共享连接仅单线程触达(当前 async 循环 + worker 线程共享已是数据竞态风险)。

#### HI-12 [安全] SSRF:采集/下载/webhook 投递对用户 URL 无内网阻断 [已交叉验证]
- **问题**: URL 摄入(`trafilatura.fetch_url`)、RSS feed 与 entry-link 抓取(`httpx`)、出站 webhook 投递均直采用户 URL,无 169.254.169.254/127.0.0.1/10/8/192.168/16/::1 阻断,无 DNS TOCTOU 防护。
- **证据**: `src/saw/adapters/parsers/html_parser.py:37`(`trafilatura.fetch_url(url)`);`src/saw/ingest/extractors/url.py:38` + `src/saw/ingest/pipeline.py:108-111`(URL 路由);`src/saw/engines/ingest/feed_manager.py:150,207,452`(`await self._http.get(url/feed.url/link)`);`src/saw/api/webhooks.py:257-261`(`self.http_client.post(webhook.url, ...)`)。
- **影响**: 认证用户(或 local 模式任何人)提交 `http://169.254.169.254/latest/meta-data/iam/security-credentials/` 即外泄云实例凭据;或探内网服务(`http://localhost:8000/api/...`);webhook 投递还会把含敏感 claim 的事件 payload 发往内网。
- **严重度**: High
- **建议**: 实现 URL 校验器:解析主机 IP,拒绝 private/loopback/link-local;在 `IngestPipeline` 路由 URL 前与 webhook 创建/投递时校验;考虑自定义 httpx transport 在连接层按解析 IP 拒绝(防 DNS rebinding)。

#### HI-13 [安全] OAuth `exchange_code` 失败静默回退硬编码 `test_token` 并作为有效凭据存储 [已交叉验证]
- **证据**: `src/saw/connectors/oauth_handler.py:278-282`(`except Exception: # Fallback for testing without real OAuth; token = {"access_token": "test_token", "expires_in": 3600}`),:285-292 计算过期并加密入库。
- **影响**: token 端点不可达(DNS/超时/错误重定向)时存假 token;连接器"已认证"但凭据无效;宽 `except` 吞真实错误,排障无门。
- **严重度**: High
- **建议**: 移除 test-token fallback,失败即抛 `OAuthError`;若需测试模式以显式 `test_mode` flag 门控。

#### HI-14 [配置] `.env` 磁盘存真实(非占位)`AUTH_SECRET_KEY`/`SAW_ENCRYPTION_KEY`(已 gitignore,未入库) [已交叉验证]
- **证据**: `.env:12`(`AUTH_SECRET_KEY=<64 hex 真值>`),`.env:17`(`SAW_ENCRYPTION_KEY=<base64 真值>`)。`.gitignore` 已忽略 `.env`/`.saw/`/`*.key`(`git ls-files` 确认未跟踪)。
- **影响**: 虽未提交 git,但密钥以明文存盘;若机器共享/备份/截屏即泄露。AUTH_SECRET_KEY 用于 JWT 签名,泄露即伪造任意 token。
- **严重度**: High
- **建议**: 立即轮换两把密钥;改用 secrets manager 或仅以 `.env.example` + 环境注入,杜绝开发机明文落盘。(注:本报告不重现密钥原文。)

#### HI-15 [配置] 容器以 root 运行、假健康检查、无资源限制 [已交叉验证]
- **证据**: `Dockerfile`(无 USER,以 root);`Dockerfile HEALTHCHECK` `CMD saw --version`(不检 DB/HTTP);`docker-compose.yml`(无 mem_limit/cpus/deploy.resources,healthcheck 同样 `saw --version`)。
- **影响**: root 容器提权风险;web 挂起或 DB 不可达时健康检查仍 healthy,k8s/Docker 不重启;单容器可 OOM 宿主。
- **严重度**: High
- **建议**: 加非 root `USER`;healthcheck 改 `curl -f http://localhost:8000/health/ready`(curl 已装);加 `deploy.resources.limits`。

#### HI-16 [可观测] 无 Sentry、无结构化日志、trace_id 不跨组件 [已交叉验证]
- **证据**: 全仓 grep `sentry_sdk|SENTRY_DSN` 零命中;grep `structlog|pythonjsonlogger|JsonFormatter` 仅 `audit/service.py:278` 一处无关 `json.loads`;`trace_id|request_id` 仅 `engines/collaborate/a2a_protocol.py:54` 与 `domain/agent.py:20`,HTTP 中间件/write_queue/connector 均无。
- **影响**: 生产错误仅纯文本日志(无 Sentry 捕获);日志聚合无法解析;跨组件(HTTP→write_queue→connector)请求无法关联。
- **严重度**: High
- **建议**: 加 Sentry SDK(环境 DSN);加 request-ID 中间件生成/传播 `X-Request-Id` 并注入所有日志与 write_queue/connector;team 模式上 `structlog`/`python-json-logger`。

#### HI-17 [可观测] `/metrics` 返回 JSON 非 Prometheus 文本格式,且假称兼容 [已交叉验证]
- **证据**: `src/saw/drivers/web/health.py:106-107`(docstring "Prometheus-compatible metrics endpoint"),`async def metrics` 返回 JSON dict(`saw_users_total`/`saw_pages_total`/`saw_claims_total`/`saw_version`,无 `# HELP`/`# TYPE`,无 `text/plain; version=0.0.4`);`:127` 同步 `Path(".").rglob("*.md")` 计数(阻塞事件循环)。
- **影响**: Prometheus/Grafana 无法 scrape;指标极稀疏(3 gauge,无 latency histogram/error counter);/metrics 公开(无 auth_dep),外部 scraper 可拖垮服务。
- **严重度**: High
- **建议**: 用 `prometheus_client` 生成 exposition 格式;补 request latency histogram 与 error counter;缓存 page count 并 `run_in_threadpool`;gate `/metrics`。

#### HI-18 [测试] 95 测试收集期报错,被 `pythonpath` workaround 掩盖 [已交叉验证]
- **证据**: `pyproject.toml [tool.pytest.ini_options]` 注释:"the broken editable-install .pth in the committed .venv points at another project, so `import saw` fails and 95 tests error at collection time. Pinning pythonpath here makes the suite runnable."
- **影响**: workaround 掩盖真实环境问题;在 `pytest` 外(或无 pythonpath pin 的 CI)即见 95 收集错误;根因(.pth 损坏)未修。
- **严重度**: High
- **建议**: 修根因——删虚拟环境内 stale `.pth`,或文档化 `uv sync`/`pip install -e .` 干净流程;修后移除 `pythonpath` workaround。

---

### 🟡 Medium(节选表)

| ID | 维度 | 问题(一句话) | 证据 file:line |
|----|------|--------------|------------------|
| M-1 | 分层 | `import_md.py` 绕过 Write Queue 直写 `wiki_repo.write` | `drivers/web/routes/import_md.py:131,165` |
| M-2 | 分层 | 路由伸手进 QueryEngine 私有 `_wiki_repo`/`_claims_repo`(双名 fallback) | `drivers/web/routes/pages.py:81,89`;`api/routes/govern.py:60`;`api/routes/query_ingest_learn.py:48`;`import_md.py:42`;`drivers/web/health.py:122` |
| M-3 | 分层 | 双持久化(裸 sqlite3 vs SQLAlchemy AsyncSession)无共享事务边界 | `app.py:319-321`;`db/session.py:67-72`;`api/connector_settings.py:14-15` |
| M-4 | 维护 | 14 个 >500 行 god file(compiler.py 701、parser.py 680、starter_kits.py 673、github/connector.py 661…) | 见 §2 表 |
| M-5 | 分层 | feedback/WIP 直写文件系统、prune 裸 SQL 软删,绕 outbox | `api/routes/query_ingest_learn.py:318-325,430-436,455-461` |
| M-6 | 契约 | 错误体两套:HTTPException 走 `{"detail"}` 绕过 RFC7807;500 内插 `{e}` 泄内部异常 | `middleware/errors.py`(未注册 HTTPException handler);`query_ingest_learn.py:73` 等 |
| M-7 | 契约 | 分页无上限(list_feeds/list_contradictions/list_pages 返全量含全文/get_trends) | `api/feeds.py:204-211`;`govern.py:181-190`;`pages.py:45-95` |
| M-8 | 契约 | `bulk.py`/`graphql.py` 从不注册(Phase-6 API 平台不可达,死代码) | `app.py` 无 include;两文件无 `router=APIRouter` |
| M-9 | 异步 | `/metrics`+dashboard 在 `async def` 内同步 `Path(".").rglob("*.md")`+`f.stat()`,且 /metrics 无 auth | `api/dashboard_stats.py:48-56`;`drivers/web/health.py:118-128` |
| M-10 | 异步 | `/health/ready` 每探针 `create_engine`+`SELECT 1` 同步,Redis 慢即自伤 DoS | `drivers/web/health.py:18-34,39-52,84` |
| M-11 | 契约 | API 版本前缀不统一(/api vs /api/v1/feeds vs /api/dashboard vs root /health) | `app.py`;`feeds.py`/`govern.py`/`sync.py`/`integrations.py`/`dashboard_stats.py` |
| M-12 | 契约 | Pydantic 校验绕过:content 经 query string 传、`request: Request=None` 默认 | `api/routes/query_ingest_learn.py:228-235,280-285` |
| M-13 | 数据 | claim_relation/entity_relation/contradictions 的 FK/过滤列无索引 → 全表扫 | `db/migrations.py:57-71,77-85,148-158`;`govern.py:119-120,181-190,354`;`query/graph_traverse.py:63` |
| M-14 | 编排 | `on_failure="rollback"` 被解析器接受但执行器只实现 `abort`(静默按 abort 行为) | `workflow_parser.py:49`;`workflow_executor.py:131-133` |
| M-15 | 编排 | 死信队列无主动监控/告警,op 静默累积 | `queue.py:276-292`;`govern.py:446`(仅被动 count) |
| M-16 | 编排 | WorkflowResult.status 为裸字符串无枚举无迁移校验,执行期从不置 running | `workflow_executor.py:38,139,147` |
| M-17 | 数据 | CodeGraphStore 读方法(get_outgoing_edges/find_nodes_by_name)不持 `_lock`,共享连接非线程安全 | `code_graph/store.py:44,131,151,167,200` |
| M-18 | 配置 | 4 处版本号不一致(1.0.1/3.4.0/1.1.0/2.0.0) | `pyproject.toml`;`Dockerfile` LABEL;`app.py:48`;`health.py:108` |
| M-19 | 性能 | FULL 能力层系愿景——无向量库依赖、`sentence_transformers` 不在 requirements、仅检测可导入 | `config/settings.py:117-122`;`engines/learn/adaptive_index.py:217` |
| M-20 | 性能 | 研究/自动摄入抓取无并发上限(`max_concurrent_tasks` 存而不用) | `research/research_engine.py:50`;`research/auto_ingest.py` |
| M-21 | 测试 | 无架构守护测试(循环依赖/分层违反/god file 体积阈值) | `tests/` 无相关用例;`connectors/sync_engine.py:86` 注释规避循环 |
| M-22 | 测试 | write-queue 仅单线程 happy path,无并发 dispatch/崩溃恢复/多 worker 竞态测试 | `tests/unit/write_queue/test_queue.py`(136 行) |
| M-23 | 安全 | GitHub webhook secret 默认空串且端点仍以空 secret 做 HMAC(可伪造) | `api/github_webhook.py:44`(对比 `webhook_inbound.py:177-180` 有空守卫) |
| M-24 | 安全 | WeCom 签名用 `==` 非 `hmac.compare_digest`(时序攻击) | `connectors/im/wecom/crypto.py:81` |
| M-25 | 安全 | WeCom 无时间戳新鲜度校验(可无限重放) | `connectors/im/wecom/connector.py:201`;`crypto.py:75-76` |
| M-26 | 安全 | webhook HMAC 签名 secret 明文存 DB(对比 API key 哈希、OAuth Fernet 加密) | `api/webhooks.py:48,115-117` |
| M-27 | 安全 | InputSanitizer 仅查 query params,不查 body(SQL 注入"检测"为装饰性;实际 SQL 已参数化) | `middleware/security.py:239-251` |
| M-28 | 数据 | code_graph 的 `code_nodes_fts` 用裸 `porter unicode61`,无 Python 侧 CJK 预分词 → 中文代码注释/docstring 检索失效(回退 LIKE 全表扫) | `code_graph/store.py:34-37,39-52,209,219` |

### 🟢 Low(节选)

| ID | 问题 | 证据 |
|----|------|------|
| L-1 | `IngestCompleted` 在 domain/events.py 与 plugins/events.py 重复定义,字段名不一致(claim_count vs claims_created) | `domain/events.py:43-47`;`plugins/events.py:56-61` |
| L-2 | register/login 可经 409 枚举邮箱,且仅套用通用限流 | `drivers/web/routes/auth.py:76-99,121+` |
| L-3 | LLM router 重试用 `time.sleep`(异步路径即阻塞事件循环) | `adapters/llm/router.py:122,98,365` |
| L-4 | `fts_index.title` 存 UUID 却被 FTS5 索引(应 UNINDEXED) | `db/migrations.py:54-60`;`adapters/storage/claims_repository.py:131` |
| L-5 | FTS5 DDL 在 migrations.py 与 claims_repository.py 重复(漂移隐患) | `claims_repository.py:26-34` |
| L-6 | get_pending 难以完全利用 idx_outbox_status(retry_count/next_retry_at 为扫描后过滤) | `queue.py:98-108`;`migrations.py:140` |
| L-7 | API key 哈希比对用 `==`(应 compare_digest) | `api/keys.py:30,56` |
| L-8 | CORS `allow_credentials=True` 配 `methods/headers ["*"]`,origins 经 CLI 可配 | `app.py:120-126` |
| L-9 | JWT 无 kid/轮换机制,密钥泄露即永久伪造 | `auth/jwt_auth.py:53-62,128-137`;`adapters/crypto/_keyfiles.py:73-80` |

---

## 4. 改进路线图

### 短期止血(1–2 周)
- **CR-1/CR-2**: 修复 ApiKey 鉴权(接 `APIKeyService.verify_key` + 修正 `get_api_key_func` 签名);`create_app_from_config` 读 auth_mode,0.0.0.0+local 拒绝启动。
- **CR-3**: web 模式接线 Write Queue dispatcher(lifespan 启 worker 或 enqueue_atomic 内联 dispatch)。
- **CR-4**: 移除 in-memory 静默 fallback,DB 打不开即 fail-fast。
- **CR-5**: Dockerfile 改 `COPY . /app && pip install /app`,统一版本号。
- **HI-15**: 容器非 root + 真 healthcheck + 资源限制。
- **HI-14**: 轮换 .env 内 JWT/加密密钥。
- **HI-18**: 修 .pth 根因,移除 pythonpath workaround。

### 中期加固(1–2 月)
- **HI-1/HI-11/M-5/M-2**: SQL 下沉仓储,路由不持 `_conn`/不伸手私有属性;prune/feedback 走 outbox。
- **HI-10/HI-11/M-9/M-10**: 异步路由内同步 DB 调用改 `def` 或 `run_in_threadpool`;`/metrics`/dashboard/health 探针 offload + 复用连接池。
- **HI-12**: SSRF 防护——URL 校验器阻断内网/云元数据,webhook/feed/采集统一接入。
- **HI-13**: 移除 OAuth test_token fallback。
- **HI-6/HI-7**: write-queue CAS 认领 + 启动 recover + 陈旧阈值后台任务。
- **HI-8/HI-9/M-14/M-16/M-15**: 工作流条件求值修复 + 执行态持久化 + 状态枚举 + 死信告警 + 实现/拒绝 rollback。
- **M-7/M-11/M-6/M-12**: 分页加 hard cap、统一 `/api/v1`、统一 RFC7807 错误体、content 入 body model。
- **HI-16/HI-17**: Sentry + 结构化日志 + request-id 中间件;`/metrics` 改 Prometheus 格式。

### 长期演进(2–6 月)
- **HI-2/HI-4/HI-5**: 事件总线、PluginRegistry、ConnectorRegistry 在 `create_app_from_config` 接线;connector 改 entry_points 自注册;让"微内核"从展示性变为可用。
- **HI-3**: 接入 Govern 引擎(contradiction/confidence/freshness)。
- **M-3**: 统一持久化(二选一),消除双 DB/双迁移框架。
- **M-4**: 拆分 14 个 god file(compiler.py→scanner/compiler/index_manager/log_manager;github/connector.py→auth/api_client/transformer)。
- **M-19**: FULL 能力层落地——加 `sentence-transformers` 可选依赖 + 实向量检索,或从文档移除 FULL 宣称。
- **M-21/M-22**: 架构守护测试(分层/循环依赖/file-size 阈值)+ write-queue 并发/崩溃恢复测试。
- **M-13/M-17/M-28**: 补 FK 索引迁移、CodeGraphStore 读连接隔离、code_graph FTS5 CJK 预分词。

---

## 5. 整体结论

SAW 的架构意图与文档质量远超其执行成熟度。六边形分层、outbox 单一变更网关、能力分级、连接器抽象与 FTS5 CJK 预分词都是扎实的工程决策,domain 层确实保持了纯 Python 无上行依赖的纪律。但执行落差集中在两类:(1)**"定义了但从未接线"的子系统**——Write Queue dispatcher(主写路径静默丢数据)、事件总线(恒 None)、ConnectorRegistry(从不注册)、PluginRegistry(web 运行时不加载)、Govern 引擎(503),使"微内核 + 事件总线 + 连接器框架"在关键面上沦为展示性架构;(2)**主写与主鉴权路径上的 Critical 缺陷**——`saw web` 默认无鉴权 admin 且 compose 以 0.0.0.0 暴露、team 模式任意 ApiKey 头即获 admin、静默回退内存 DB,三者叠加意味着当前形态**不可用于任何网络化部署**。

优先级建议:先按短期止血项关闭 CR-1~CR-5 与 HI-15(这 6 项即可消除"静默数据丢失"与"无鉴权暴露"两类 Critical);再以中期加固项修复异步阻塞、SSRF、工作流引擎正确性与契约一致性;最后以长期演进项让插件/事件总线/连接器从"展示性"转为"可用",并补架构守护测试防止边界再次侵蚀。domain 层与迁移框架是值得保留的资产,其余子系统需补齐"最后一公里"的接线与集成测试。

---

## 6. 修复落地状态(更新于 2026-08-26)

> 短期/中期/长期路线图中标注为"已修复"的项均已落地、编译通过、并经 302 项既有测试 + 11 项新增回归测试(`tests/unit/test_critical_fixes.py`)验证零回归。下表为执行结果。

### Critical(5/5 已修复)
| ID | 落地 | 关键改动 |
|----|------|----------|
| CR-1 | ✅ | `keys.py` 新增 `verify_api_key_sync`/`verify_api_key_for_rate_limit`(DB+SHA256+过期校验);`security.py` ApiKey 分支改为真校验、返真实 role;`app.py` 限流回调重接 |
| CR-2 | ✅ | `create_app_from_config` 读 `SAW_AUTH_MODE`/config;非回环 host+local 拒启;compose 设 `SAW_AUTH_MODE=team` |
| CR-3 | ✅ | `queue.py` `enqueue_atomic` 内联 dispatch;`create_app_from_config` 构造 Dispatcher 注册 5 sink + `recover()`;lifespan 启动 drain |
| CR-4 | ✅ | 移除 `:memory:` 静默兜底,DB 打不开即 fail-fast |
| CR-5 | ✅ | Dockerfile `COPY . /app && pip install /app` + `.dockerignore` |

### High(17/18 已修复,HI-14 待人工)
| ID | 落地 | 关键改动 |
|----|------|----------|
| HI-1 | ✅ | `claims_repository.py` 新增 update_confidence/soft_delete_claim/list_contradictions/resolve_contradiction/count_relations(含写锁);govern/qil 路由替换裸 SQL |
| HI-2 | ✅ | 新建 `plugins/event_bus.py`(`InMemoryEventBus`:publish/publish_nowait/subscribe/add_subscriber);接线 WorkflowExecutor+Dispatcher+WS+create_app;WS 兼容 dict 事件 |
| HI-3 | ✅ | `create_app_from_config` 设 `app.state.govern = Governor(...)` |
| HI-4 | ✅ | lifespan 启动 `PluginRegistry.discover+enable`,PluginContext.subscribe_event/publish_event 绑总线 |
| HI-5 | ✅ | 新建 `connectors/bootstrap.py`(`register_default_connectors`);lifespan 调用,7 平台全注册(不再 404) |
| HI-6 | ✅ | `mark_processing` 加 CAS `WHERE status IN('pending','failed')`+返 bool;dispatcher 检查 skip |
| HI-7 | ✅ | lifespan 60s 周期 `recover()` 后台任务 + 启动 recover |
| HI-8 | ✅ | `_eval_condition` 改 `Environment.compile_expression` 原生 bool |
| HI-9 | ✅ | 迁移 v4 `workflow_executions` 表;`_persist_workflow` upsert;启动 `_recover_stranded_workflows` 标记滞留 running→interrupted |
| HI-10/11 | ✅ | govern(8)+qil(11)+feeds(6)共 25 个 async→def |
| HI-12 | ✅ | 新建 `adapters/url_guard.py`(`assert_safe_url`/`_async`,阻断 private/loopback/云元数据);html_parser+feed_manager×3+webhooks 接线 |
| HI-13 | ✅ | `oauth_handler.py` 移除 test_token 回退,抛 `OAuthError` |
| HI-14 | ⚠️ | `.env` 内 `AUTH_SECRET_KEY`/`SAW_ENCRYPTION_KEY` 需**人工轮换**(代码无法代劳) |
| HI-15 | ✅ | Dockerfile 非 root `USER saw` + `curl -f /health/ready` healthcheck;compose `deploy.resources.limits` + 真 healthcheck + 非 root volume 路径 |
| HI-16 | ✅ | 新建 `middleware/observability.py`(`RequestContextMiddleware` X-Request-Id 传播+contextvar;`init_observability` JSON 日志+可选 Sentry);create_app 注册 |
| HI-17 | ✅ | `/metrics` 改 Prometheus text/plain 0.0.4,补 outbox pending/dead-letter gauge |
| HI-18 | ✅ | `.venv` `.pth` 已正确指向本项目;移除 `pyproject.toml` `pythonpath=["src"]` workaround |

### Medium — 批次 A 已修复(2026-08-26)
| ID | 落地 | 关键改动 |
|----|------|----------|
| M-6 | ✅ | `errors.py` 注册 `StarletteHTTPException` handler → RFC 7807;5xx detail 屏蔽(不再内插 `{e}` 泄内部) |
| M-7 | ✅ | `list_feeds`/`list_pages`/`list_contradictions` 加 `Query(50,ge=1,le=200)`+offset;list_pages 切片前不物化全文 |
| M-23 | ✅ | `github_webhook.py` 空 `GITHUB_WEBHOOK_SECRET` 返 503(对齐 webhook_inbound 守卫) |
| M-24 | ✅ | `wecom/crypto.py` `verify_signature` 用 `hmac.compare_digest`(替 `==`) |
| M-25 | ✅ | WeCom 加 300s 时间戳新鲜度校验(对齐 Slack/Feishu,防重放) |
| M-26 | ✅ | `webhooks.py` create 时 Fernet 加密 secret 入库 + sign 时解密(列扩 String(512));明文 legacy fallback |
| M-18 | ✅ | 版本号自 `importlib.metadata.version("smart-agent-wiki")` 派生(app/health);Dockerfile LABEL 改 1.0.1 |

### 新增模块/资产
`adapters/url_guard.py`、`plugins/event_bus.py`、`drivers/web/middleware/observability.py`、`connectors/bootstrap.py`、`tests/unit/test_critical_fixes.py`(15 回归测试)、`.dockerignore`、迁移 v4。

---

## 7. 后续任务决策

> Critical/High 已清零(除人工 HI-14)。剩余为 Medium 加固项与性能/可伸缩性演进。按**风险/收益/成本**排序,决策如下三批次:

### 批次 A — 契约与安全加固(下一轮,中优先,1–2 天)
高收益、低风险、单点改动:
1. **M-6 错误体统一 RFC 7807**:`errors.py` 注册 `StarletteHTTPException` handler,500 不再内插 `{e}`。安全+契约双收。
2. **M-7 分页 hard cap**:`list_feeds`/`list_contradictions`/`list_pages`/`get_trends` 加 `Query(50, ge=1, le=200)`,list_pages 不返全文。防 DoS。
3. **M-23 GitHub webhook 空 secret 守卫**:`github_webhook.py` 空 secret 返 503(对齐 webhook_inbound 已有守卫)。
4. **M-24/M-25 WeCom 加固**:`crypto.py` 用 `compare_digest`(替 `==`)+ 时间戳新鲜度(对齐 Slack/Feishu)。
5. **M-26 webhook secret 加密**:用现有 `TokenEncryption` 加密入库。
6. **M-18 版本号统一**:自 `pyproject.toml` 派生,删散落的硬编码版本。

### 批次 B — 数据层与异步收尾(中优先,2–3 天)
7. **M-13 FK 索引迁移 v5**:`claim_relation`/`entity_relation`/`contradictions` 加索引,治 blast-radius/图遍历全表扫。
8. **M-9/M-10 可观测探针异步**:`/metrics` rglob 与 `/health/ready` 的 `create_engine+SELECT 1` 改 `run_in_threadpool`+复用连接池;`/metrics` 加 auth。
9. **M-17 CodeGraphStore 读连接隔离**:用只读连接(`query_only=ON`)做读,WAL 不阻塞写。
10. **M-28 code_graph FTS5 CJK 预分词**:接入 `tokenize_for_fts`/`build_match_query`。
11. **feeds 混合 handler**:`create_feed`/`poll_feed`/`import_opml` 的同步 DB 段 `run_in_threadpool`(HI-10/11 残余)。

### 批次 C — 可伸缩性与重构(长期,1–2 月,需设计)
12. **M-3 统一持久化**:消除裸 sqlite3 与 SQLAlchemy AsyncSession 双栈双迁移(大重构,需评审)。
13. **M-19 FULL 能力层落地**:`sentence-transformers` 可选依赖 + 实向量检索,或文档移除 FULL 宣称。
14. **M-4 god file 拆分**:14 个 >500 行文件(compiler/parser/github-connector 等)按职责拆。
15. **M-21/M-22 测试守护**:架构守护测试(分层/循环依赖/file-size 阈值)+ write-queue 并发/崩溃恢复测试。
16. **M-15/M-16 工作流加固**:死信告警 + WorkflowStatus 枚举/迁移校验 + 实现/拒绝 `on_failure="rollback"`(M-14)。

### 决策
- **批次 A 已完成(2026-08-26)**:M-6/7/18/23/24/25/26 全部落地,15 项回归测试通过,309 项测试零回归。安全 + 契约加固到位。
- **批次 B 已完成(2026-08-27)**:M-13 FK 索引迁移 v5、M-9/M-10 探针 threadpool offload+复用连接池、M-17 CodeGraphStore 读方法加锁、M-28 code_graph FTS CJK 预分词、feeds 混合 handler sync DB offload。全套 1752 passed 0 fail。
- **批次 C 已完成(2026-08-27)**:
  - M-21 架构守护测试(分层/循环导入/file-size 750 阈值)+ M-22 write-queue 并发/崩溃恢复测试。
  - M-16 WorkflowStatus str-enum + 迁移表 + validate_workflow_transition + _persist_workflow 校验非法迁移。
  - M-19 真实 embeddings 适配器(adapters/embeddings.py)+ adaptive_index 语义聚类(带 fallback)+ sentence-transformers 入 [learn] extra。
  - M-4 god file 拆分:compiler.py 701→626(纯解析函数提取至 compile/parsers.py,行为保持);守护测试防增长;其余 13 文件为增量债务(守护已挡增长)。
  - M-3 持久化统一:出具 ADR(`docs/ADR-persistence-unification.md`)——双栈现状/三选项/推荐分阶段(先 UnifiedStore facade+同文件,后 Option A 旗后迁移)+ 待评审开放问题。标记"需评审",不盲改。
- **HI-14 人工轮换密钥**请同步进行(不阻塞代码,但网络化部署前必须完成)。
- **全套 1763 passed, 0 failed**(从 hang 死到 84s 跑完)。

---

*所有 Critical/High 证据均经主审亲自打开行号交叉验证,排除误报。§6 修复项均经编译+302/11 测试验证。Medium/Low 附 `file:line` 证据。可按条目深挖或出修复草案。*
