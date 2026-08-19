# Smart Agent Wiki 全项目综合审计报告

> 审计日期：2026-08-19
> 方法：5 个并行 agent（需求文档 / 核心模块 / 工具链API / 前端桌面壳 / 测试）+ 未提交 diff 的 code review（10 条已验证缺陷）交叉汇总。
> 仓库 `/Users/cs/projects/smart_agent_wiki`，含未提交工作区改动（~2700 行 / 46 文件 + 新增 `db/session.py`）。

---

## 一、项目目的与目标

SAW 是一个 **local-first 多代理知识管理平台**，把知识当"编译产物"而非"检索对象"，承诺 **可信 / 可溯源 / 可进化** 三大价值，通过 Ingest→Query→Govern→Learn→Collaborate 五引擎 + SQLite outbox 单一写入网关 + Vault/Claims/Wiki/Index 四层存储覆盖知识全生命周期，交付形态为 Python 后端 + React Web + Tauri 桌面 + FastMCP + CLI（`saw`）。

**一句话定性**：架构骨架完整、表层功能齐全，但核心智能层多处仍是 placeholder/契约断裂，"已发布"徽章与实现真实度存在系统性落差。

---

## 二、四个核心问题

### Q1. 当前产品功能是否满足项目目标？ → 部分满足

| 目标维度 | 满足度 | 证据 |
|---|---|---|
| 骨架与多壳交付 | ✅ 满足 | Web/MCP/CLI/Tauri 四壳齐备，25 个 router / ~110 端点，路由表 13 页基本真实实现 |
| Write Queue 收口设计 | ✅ 满足（设计层） | dispatcher 并行调度 + 指数退避 + crash recovery + dead-letter 完整，测试用真实 SQLite |
| 可信（可溯源） | ⚠️ 不满足 | FTS5 search JOIN 用错列（`c.uuid = f.title`），wiki-only 索引行被丢弃 → 搜不到；import_md 绕过队列直接写，不更新索引 |
| 可进化（知识图谱） | ❌ 不满足 | `graph_sink` 契约断裂（pipeline 发 `{"type":"entity"}`，sink 查 `payload["entity"]`），所有实体/关系写入静默失败 |
| 可信（治理/修剪） | ⚠️ 不满足 | learn 的 `expiry`/`trends.detect_gaps`/`get_growth_patterns` 全是 placeholder；govern 的 `trigger_review`/`get_review_queue` 是 placeholder；prune 因时区 aware/naive 混用对默认时间戳行永远 age=0 |
| 安全承诺 | ❌ 不满足 | README 标 "production-ready security"，但 ROADMAP Phase 39 plans=0/3；WS 无 token 校验、OAuth 回调误挂 auth_dep、`/metrics` 公开 |

**核心矛盾**：README/api_contract 把 Govern、6 Agent、Contradiction Detection、Notion、Security 标 ✅ Shipped，但 `.planning/ROADMAP.md` v3.8 Phase 44/45 明确把 "Agent execute() 返回非空 payload"、"ContradictionDetector 真实查询"、"Governor.freshness_report 返回真实分布"、"Notion fetch_items 返回非空" 列为**尚未完成的成功标准**——文档与实现口径系统性背离。

### Q2. 技术功能实现是否满足产品要求？ → 不完全满足

文档承诺但实现未达的关键点：

1. **FTS5 搜索**（contract §5.3，承诺 hybrid search）→ JOIN 语义错误，wiki 内容搜不到（`engines/query/search.py:67,87,194`）。
2. **知识图谱写入**（承诺可进化）→ graph_sink 契约断裂，静默丢数据（`write_queue/sinks/graph_sink.py:33,48`）。
3. **批量导入**（contract 承诺 write queue 幂等）→ import_md 绕过队列，导入不入索引（`drivers/web/routes/import_md.py:101,187`）。
4. **Govern/Learn 闭环**（contract §5.4/5.5）→ freshness/review/expiry/gaps 多处 placeholder。
5. **Collaborate workflow**（contract §5.6，承诺 6 agent 真实执行）→ team 模式静默 no-op 标 completed；local 模式跨线程 sqlite 崩溃；无源材料时返回 `"(No source material found; stub synthesis.)"` 伪造内容。
6. **OAuth/JWT 安全**（contract §安全）→ OAuth 回调端点误加 auth_dep 必 401；WS 无鉴权。
7. **同步连接器**（contract 承诺双向）→ `_get_sync_direction` 硬编码 pull-only，4 个 IM 连接器的新 push 能力形同虚设。
8. **Team 部署**（PostgreSQL+Redis）→ 三套 `get_db_session` 指向三个不同库（`saw.db` / `.saw/db/claims.db` / `:memory:`），数据不互通；feeds 写入内存库即丢。

### Q3. 技术模块功能缺陷

**🔴 P0（阻断主功能链路）**

| # | 位置 | 缺陷 |
|---|---|---|
| 1 | `api/routes/collaborate.py:252` | `_run_via_engine` 检查 `hasattr(engine,"execute")`，但 `CollaborateEngine` 只有 `execute_workflow`/`execute_workflow_definition` → team 模式工作流静默标 "completed" 不执行任何 agent |
| 2 | `api/routes/collaborate.py:107` | `asyncio.to_thread(query.query,...)` 在线程池跑，但 sqlite3 连接在主线程创建且 `check_same_thread=True`（`drivers/web/app.py:326`）→ local 模式每个 workflow 在 search 步即 `ProgrammingError` 崩溃 |
| 3 | `write_queue/sinks/graph_sink.py:33,48` | 契约不匹配，所有实体/关系写入被跳过 → 知识图谱构建静默失败 |
| 4 | `engines/query/search.py:67,87,194` | FTS5 JOIN 用 `f.title`（实为 doc_id），wiki-only 索引行搜不到 + 每行额外 `SELECT 1 FROM claim WHERE uuid=?` 过滤掉 wiki slug |
| 5 | `drivers/web/app.py:160`（state 未挂 `wiki_repo`）→ `routes/onboarding.py:18`、`timeline.py:26` | `saw web` 下 `GET /api/onboarding/status`、`/api/timeline` 必 500 |
| 6 | `drivers/web/routes/import_md.py:101,187` | 绕过 WriteQueue 直接 `wiki_repo.write`，不触发 FTS5Sink → 导入的页面搜索不到 |

**🟠 P1（功能降级/数据不一致）**

| # | 位置 | 缺陷 |
|---|---|---|
| 7 | `api/health.py:69` | `get_health_monitor` 用 `except Exception` 包住 `yield` → handler 抛 404 等异常被吞成 503 "Health monitor unavailable" |
| 8 | `api/routes/collaborate.py:57` | `_set_step` 把 per-step "completed" 写进整条 workflow status → 第 1/4 步完成就标 completed + 设 completed_at |
| 9 | `api/integrations.py:372` | `_get_sync_direction` 硬编码 pull-only → 4 个 IM 连接器新加的 push 永不触发 |
| 10 | `wecom/connector.py:129` + `sync_engine.py:389` | WeCom webhook 无 msgid → put_item 返回 ""，sync_engine 记为错误 → 每次成功推送都报"Sync completed with errors"，pushed_count=0 |
| 11 | `write_queue/sinks/wiki_sink.py:43` | write 前先 `repo.read(path)`，read 对损坏文件抛 StorageError → 该路径永久写不进（原本会覆盖修复） |
| 12 | `api/routes/query_ingest_learn.py:338` | prune 用 aware `now` 减 naive `created_at`（SQLite 默认 `datetime('now')`）→ TypeError 被吞 → age_days=0，这类 claim 永不修剪 |
| 13 | `api/routes/collaborate.py:235` | `asyncio.create_task` 不保留引用 → 任务可能被 GC 静默取消，workflow 卡 "running" |
| 14 | `api/feeds.py:147` | `create_engine("sqlite:///:memory:")` 每请求新建内存库 → feeds 写入即丢 |
| 15 | `db/config.py:22` vs `app.py:332` | 双数据库（`saw.db` vs `.saw/db/claims.db`），connector/feeds 与 claims 数据无法 join |
| 16 | learn `expiry.py:109` / `trends.py:55,100` / govern `governor.py:108` | 全 placeholder，expiry/gap/review-queue 永远空 |
| 17 | `api/oauth_callback.py`（经 `app.py:221` 挂 auth_dep） | OAuth authorize/callback 端点误加 auth_dep → 回调无 Bearer token 必 401，OAuth 流程断裂 |
| 18 | `db/session.py:30` | 懒初始化 engine/factory/create_all 单例无锁 → 并发首请求可能建多个引擎、`database is locked` |

**🟡 P2（架构/质量）**：`govern.py`/`query_ingest_learn.py` 裸 SQL 直达 `repo._conn` 越层；4 个 IM 连接器 `transform_from_claim` 复制粘贴；`supports_push` 类属性与 @property 重复定义（属性死代码）；`_get_sync_direction` 应从 `connector.supports_push` 派生而非硬编码；MCP 与 Web 各自独立初始化引擎，"converge into drivers/" 仅目录层收敛运行时仍双路径。

### Q4. 前端点击 → 后端接口 → 数据库 → 界面效果 联动是否顺畅？ → 不顺畅

**断链地图：**

```
[前端点击]
   │  ✅ 无 404 死按钮（所有调用端点后端都存在且方法匹配）
   │  ❌ team 模式大面失效：Dashboard stats、整个 Integrations/ConnectorSettings 页
   │     用裸 fetch 不带 Authorization 头 → 401 静默失败，UI 显示全 0（D-1/D-2/D-4）
   ▼
[后端接口]
   │  ❌ 三套 get_db_session 指向三个库 → connector/feeds 与 claims 数据不通
   │  ❌ app.state 未挂 wiki_repo/govern/event_bus/collaborate → onboarding/timeline 必 500、
   │     WS broadcaster 不启动（event_bus=None）、govern 端点静默降级
   ▼
[数据库]
   │  ❌ graph_sink 契约断裂 → 图谱数据不落库
   │  ❌ import_md 绕过队列 → 索引不更新
   │  ❌ FTS5 JOIN bug → wiki 内容查不出
   ▼
[界面效果]
   ❌ page_updated payload slug 带 ".md" 后缀（collaborate.py:194），前端 queryKey 用 bare slug
      → invalidateQueries(['page','foo.md']) 命中不了 ['page','foo'] → 实时刷新失效，需手 reload
   ❌ workflow 失败时前端只 console.error，无 toast/横幅，用户无感知
```

**端到端实证（Dashboard "Run Workflow" 主推功能）：**
点击 Run → `POST /api/v1/workflows` → `_run_workflow` → `asyncio.to_thread(query.query)` → **sqlite3 跨线程 ProgrammingError**（local 模式）或 **静默 no-op 标 completed**（team 模式）→ 前端 `catch` 只 `console.error`，按钮复位但无任何反馈。**这条主链路是断的。**

唯一顺畅的部分：local 模式下 pages CRUD、search、graph 可视化、entity-types、templates、capture 等基础编辑链路端到端可用（前提是不依赖 team 鉴权与 collaborate）。

---

## 三、测试情况

- **规模**：1700 个测试 / 124 文件，收集 0 error（需 `PYTHONPATH=src`，否则 95 个 collection error）。
- **覆盖好的**：query/govern/learn/ingest 引擎、write_queue、connectors（每个连接器有测试），部分用真实 SQLite + FTS5（高质量）。
- **🔴 开箱即跑失败**：`.venv` 的 editable-install pth 指向旧路径 `/Users/cs/projects/one_more_try/smart_agent_wiki/src`，新人/CI 直接跑会误判测试全挂。**已实测 1 failed**：`test_lint_returns_health_report`（mock 配置不完整，`Mock object is not iterable`）。
- **P0 测试缺口**：新增的 `db/session.py`（121 行）零测试；`api/routes/` 4 个新路由文件（含 `_run_workflow` 121 行异步逻辑）无直接单元测试，仅 H1 集成测端点返回码。
- **质量隐患**：9 处 `assert True` + 1 处 `assert result is not None or result is None`（永真式）；`classify_contradiction` 3 个测试 mock 预设返回值后断言等于预设值（同义反复）；collaborate orchestrator 全 mock 只测透传；总 mock 引用 1045 处。

---

## 四、建议优先级（按"修了立刻止血"排序）

1. **P0 修主链路**：collaborate 的 #1（`execute`→`execute_workflow_definition`）+ #2（连接 `check_same_thread=False` 或在线程 owning 的连接上跑）+ #3 graph_sink 契约 + #4 FTS5 JOIN。这 4 条修完，"可溯源/可进化"和主推功能才真正可用。
2. **P0 修装配**：`create_app_from_config` 把 `wiki_repo`/`govern`/`event_bus` 挂到 app.state（#5）；统一 `get_db_session` 到 `saw.db.session`，废掉 feeds 的 `:memory:` 和双库（#14/#15）。
3. **P0 修鉴权**：OAuth 回调去掉 auth_dep（#17）；WS 加 token 校验；前端 Dashboard/Integrations 改走 `api.ts` 带 JWT（D-1/D-2）。
4. **P0 修环境**：重建 `.venv` 或 `pytest.ini` 加 `pythonpath = src`；补 `db/session.py` 与 `api/routes/` 测试。
5. **P1 修数据一致**：page_updated slug 去 `.md` 后缀（W-1）；trigger_sync 从 `connector.supports_push` 派生方向；WeCom put_item 返回非空 id 或 sync_engine 容忍空 id。
6. **P1 补 stub**：learn expiry/trends、govern freshness/review-queue 至少返回真实聚合（路由层已有 SQL 实现，可下沉到 engine）。
7. **P2 文档诚实化**：README 给 Govern/Agents/Contradiction/Security/Notion 加 maturity 分级或去掉 ✅；同步 api_contract 到 v4.1；补 CHANGELOG。
