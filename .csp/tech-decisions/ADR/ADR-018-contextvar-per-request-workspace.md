# ADR-018: contextvar per-request workspace 注入 + O4 tag 流程修复

## 状态：Accepted

## 上下文

v1.18.0 per-request workspace 注入 + O4 tag 流程修复（PRD-per-request-ws-v1.18.0），2 Feature（F-W-1 per-request workspace contextvar 注入 + F-W-2 O4 tag 流程修复）。PRD §3.1 要求 web 多租户路径支持请求级 workspace 隔离，PRD §3.2 要求修复 06 tag 流程（tag 指向 release commit 非 reconcile commit）。

### 需求驱动

1. **per-request workspace 隔离**（N3/K2 续留 4 轮 → v1.18.0 闭合）：`QueryEngine` 在 `create_app_from_config` 中以 `workspace_id="default"` 构造为启动单例（`engine.py:59`），所有 web 请求共享同一 workspace scope。多租户 web 部署时请求 A（workspace=team-a）与请求 B（workspace=team-b）读到同一 workspace 数据——**跨 workspace 泄漏**。PRD §3.1 要求请求级隔离，不改 QueryEngine 公开构造签名（additive MINOR，非 MAJOR）。
2. **O4 tag 流程修复**（续留自 v1.11.0 07-retro）：v1.17.0 tag `@e391611` 指向 reconcile commit（`chore(csp): v1.17.0 reconcile planning artifacts`），release commit `1cca7dc` 在 tag 之后。tag 应指向包含全部 release artifacts 的 release commit。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| QueryEngine 构造签名有 workspace_id="default" | `src/saw/engines/query/engine.py:59` | `workspace_id: str = "default"` |
| QueryEngine 存储 self._workspace_id | `src/saw/engines/query/engine.py:87` | `self._workspace_id = workspace_id` |
| QueryEngine propagate workspace to sub-services via set_workspace_id | `src/saw/engines/query/engine.py:92-95` | `for _sub in (self._tree_mode, self._compiler, self._graph): _setter(workspace_id)` |
| create_app_from_config 创建 QueryEngine 不传 workspace_id（用默认） | `src/saw/drivers/web/app.py`（`create_app_from_config` 函数，`query_engine = QueryEngine(search=search, ...)`） | workspace_id 未传，engine.py:59 default "default" 生效 |
| observability middleware 已有 contextvars 先例 | `src/saw/drivers/web/middleware/observability.py:18,30` | `import contextvars` + `request_id_var: contextvars.ContextVar[str]` |
| 无 workspace_id contextvar 存在 | `src/saw/drivers/web/` grep workspace_id | 零匹配（仅 observability.py 有 contextvars） |
| collaborate REST 读 DB 无 per-request workspace 过滤 | `src/saw/api/routes/collaborate.py` list_workflows | SQL 无 `WHERE workspace_id = ?`（workflow_executions 表无 ws 列） |
| QueryEngine cache key 已含 workspace_id | `src/saw/engines/query/engine.py:234` | `"workspace_id": self._workspace_id` in cache params |
| embedding_store query 按 workspace_id 过滤 | `src/saw/engines/query/engine.py:528-529` | `WHERE workspace_id = ?` |
| v1.17.0 tag @e391611 = reconcile commit | `git log --oneline v1.17.0` | `e391611 chore(csp): v1.17.0 reconcile planning artifacts` |
| release commit 1cca7dc 在 tag 之后 | `git log --oneline -10` | `1cca7dc release: v1.17.0` 在 e391611 之后 |
| RequestContextMiddleware dispatch 模式 | `src/saw/drivers/web/middleware/observability.py:48-55` | `token = request_id_var.set(rid); try: response = await call_next(request); finally: request_id_var.reset(token)` |
| collaborate ThreadPoolExecutor(max_workers=1) | `src/saw/api/routes/collaborate.py:35` | `_query_executor = ThreadPoolExecutor(max_workers=1)` — contextvar 在线程池中传播需关注 |
| create_app middleware 注册顺序 | `src/saw/drivers/web/app.py`（create_app 函数） | CORSMiddleware → errors → SecurityHeaders → RequestContextMiddleware → AuditLog → InputSanitizer → RateLimit — workspace middleware 需在 RequestContextMiddleware 之后注册 |

## 决策

### 决策一：contextvar 注入方式——选择候选 ① FastAPI middleware additive（不改 QueryEngine 公开构造签名）

- **新增 `workspace_id_var: ContextVar[str]`**（default `"default"`），放在 `src/saw/drivers/web/middleware/workspace.py`（新文件），复用 `observability.py` contextvars 先例。
- **新增 `WorkspaceContextMiddleware`**（FastAPI BaseHTTPMiddleware）：
  - 每请求从 `X-Workspace-Id` header（首选）/ query param `workspace_id`（次选）提取 workspace_id。
  - 校验：`re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', workspace_id)` — 非法则 400 `{"error": "Invalid workspace_id"}`。
  - `token = workspace_id_var.set(workspace_id)`；`finally: workspace_id_var.reset(token)`。
  - 若请求未提供 workspace_id，不设 contextvar（保持 default `"default"`）——向后兼容。
- **QueryEngine 内部改为 contextvar fallback 读取**：
  - 新增 helper 函数 `_effective_workspace_id(self) -> str`：先读 `workspace_id_var.get()`，fallback 到 `self._workspace_id`。
  - 所有读 `self._workspace_id` 的位置改为 `self._effective_workspace_id()`（`engine.py:234` cache key / `engine.py:295` claims_repo.get_by_id / `engine.py:528` embedding_store query / 其他）。
  - **关键约束：QueryEngine 公开构造签名不变**——`workspace_id` 参数保留，语义不变（作为 fallback default）。contextvar 注入是 additive 行为叠加，不改 API 契约。
- **子服务（TreeModeSearch/ContextCompiler/GraphTraverse）同样改为 contextvar fallback**：
  - 每个子服务新增 `_effective_workspace_id()` helper，先读 contextvar fallback 到构造值。
  - 保留 `set_workspace_id()` setter（既有 API，不删）。
- **CLI 路径不受影响**：CLI 不走 web middleware，contextvar 保持 default `"default"`，行为与 v1.17.0 一致。
- **ThreadPoolExecutor 传播**：collaborate.py 的 `_query_executor = ThreadPoolExecutor(max_workers=1)` 中 contextvar 默认不传播。解决方案：`loop.run_in_executor` 改为 `asyncio.to_thread`（Python 3.9+ 自动复制 contextvars），或在 executor.submit 时显式 `copy_context().run(fn)`。推荐 `asyncio.to_thread`（标准库原生支持 contextvars 传播）。

### 决策二：O4 tag 流程修复——选择候选 ① 约定文档化（release-manager.md 更新 + 06 执行时验证）

- **release-manager.md 约定更新**：在 S8 发布交付节明确 tag 顺序——reconcile commit → release commit（ship artifacts + milestone archive + ROADMAP/lifecycle/manifest update）→ **`git tag -a vX.Y.Z` on release commit**。
- **v1.18.0 06 执行时验证**：发布时 `git log --oneline v1.18.0 -1` 确认 tag 指向 release commit（含 ship artifacts + archive）。
- **scripts/RELEASE-FLOW.md**（新增）：文档化完整 release 流程（reconcile → release → tag → push → GitHub Release），供 release-manager 和未来 CI 参考。
- **不做 tag 签名**（GPG 签名 tag 为后续优化项）。

## 备选方案

### 决策一对比：contextvar 注入方式

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① FastAPI middleware + QueryEngine contextvar fallback（additive）（选） | **QueryEngine 公开构造签名不变**（additive，符合 roadmap §1.1 MINOR）；复用 observability.py contextvars 先例（request_id_var），模式一致；CLI 路径零影响（contextvar 保持 default）；向后兼容（无 header 时 fallback default）；Python stdlib contextvars 原生支持（< 1μs per request，O(1)） | QueryEngine 内部读取路径需改动（self._workspace_id → _effective_workspace_id()）；子服务（TreeModeSearch/ContextCompiler/GraphTraverse）同样需改；ThreadPoolExecutor 传播需处理（asyncio.to_thread 或 copy_context） | 选：additive MINOR，符合 PMS "不改 QueryEngine 公开构造签名" 约束 |
| ② 修改 QueryEngine 构造签名（添加 workspace_id_resolver 回调参数） | 更显式的依赖注入（构造函数传递 resolver） | **破坏性变更**——所有 QueryEngine 调用方需修改（create_app_from_config + CLI + 测试 fixture）；不符合 PMS "构造签名不变" 约束；MAJOR 版本 bump（非 MINOR） | 排除：破坏性变更，违反 PMS 约束 |
| ③ Starlette scope（asgi scope 注入 workspace_id，engine 从 request scope 读取） | 标准 ASGI 机制 | QueryEngine 不接触 request 对象（engine 层在 route handler 之后，无 request 参数）；需改所有 route handler 传 request 到 engine——大面积改动 | 排除：engine 层不接触 request，改造面过大 |

### 决策二对比：O4 tag 流程

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① 约定文档化（release-manager.md 更新 + scripts/RELEASE-FLOW.md）（选） | 最简实现——仅文档更新，无新脚本/工具链；release-manager 消费约定即可（06 执行时验证）；与既有流程兼容（不改 06 脚本结构） | 依赖 release-manager 正确执行约定（人工/agent 纪律）；无自动校验 | 选：最简实现，release-manager agent 可消费约定 |
| ② 脚本化 tag step（scripts/tag-release.sh 自动在 release commit 上打 tag） | 自动化——减少人工出错；可 CI 集成 | 引入新脚本需维护；当前 06 流程由 release-manager agent 执行（非 CI），脚本化价值有限；过度工程（仅 tag 一个动作） | 排除：当前 06 流程 agent 执行，约定即可，无需脚本 |

## 理由

1. **PRD 对齐**：PRD §3.1 规则 4 明确"QueryEngine 公开构造签名不变"，候选 ① 是唯一的 additive 方案（不改构造签名）。PRD §3.2 规则 1 明确"tag 在 release commit 之后执行"，候选 ① 约定文档化最简。
2. **PMS 约束**：PMS-per-request-ws 明确"不改 QueryEngine 公开构造签名（additive MINOR，非 MAJOR）"。候选 ① 满足。候选 ② 破坏构造签名 → MAJOR bump，违反 PMS。
3. **CMS 先例**：`observability.py:18,30` 已有 contextvars 先例（`request_id_var`），模式成熟。workspace_id_var 复用同一模式（ContextVar + middleware set/reset），代码风格一致。
4. **CLI 零影响**：CLI 路径不走 web middleware，contextvar 保持 default `"default"`，行为与 v1.17.0 一致。无需修改 CLI 代码。
5. **向后兼容**：无 header 时 contextvar 保持 default，行为与 v1.17.0 一致。既有 API 调用方无需修改。
6. **v2.0 MAJOR 判断对齐**：PRD §1.1 明确"contextvar additive → MINOR（v1.18.0），非 MAJOR"。候选 ① additive（不改构造签名）→ MINOR bump 正确。
7. **ThreadPoolExecutor 传播**：Python 3.9+ 的 `asyncio.to_thread` 自动复制 contextvars（`contextvars.copy_context()` 在底层调用），无需额外处理。collaborate.py 的 `_query_executor` 可改为 `asyncio.to_thread`，或保持 executor 但用 `copy_context().run` 包裹。

## 后果

### 正面
- 多租户 web 部署请求级 workspace 隔离——跨 workspace 泄漏率 0%。
- QueryEngine 构造签名不变——既有调用方（CLI / create_app_from_config / 测试 fixture）无需修改。
- CLI 路径行为不变——contextvar 保持 default `"default"`。
- contextvar 开销可忽略（< 1μs per request，O(1)）。
- JSON 日志 payload 新增 `workspace_id` 字段（结构化日志可观测）。
- O4 tag 流程修复——`git checkout v1.18.0` 检出完整发布态。

### 负面
- QueryEngine 内部读取路径需改动（self._workspace_id → _effective_workspace_id()）——改造面涉及 engine.py + 3 子服务。
- ThreadPoolExecutor 传播需处理（asyncio.to_thread 替代或 copy_context 包裹）——collaborate.py 需改动。
- 约定文档化依赖 release-manager agent 正确执行——无自动校验脚本。

### 风险
- contextvar 在 ThreadPoolExecutor 中不自动传播——缓解：asyncio.to_thread 替代（Python 3.9+ 原生支持 contextvars 传播）或 copy_context() 包裹。
- 子服务改造范围广（TreeModeSearch/ContextCompiler/GraphTraverse）——缓解：系统测试覆盖跨 workspace 隔离（TMS-DELTA-v1.18.0）。

## 关联 Feature

- F-W-1（per-request workspace 注入——本 ADR 决策一：FastAPI middleware contextvar 注入 + QueryEngine fallback 读取，构造签名不变）
- F-W-2（O4 tag 流程修复——本 ADR 决策二：约定文档化 + 06 执行时验证）

## 关联 ADR

- ADR-007（workspace 三闭环，Accepted）——v1.5.0/v1.6.0/v1.7.0 workspace 原语，本 ADR 在 web 路径上扩展 per-request 隔离。
- ADR-003（可观测 自建 JSON log + trace_id middleware，Accepted）——observability.py contextvars 先例（request_id_var），本 ADR 复用同一模式。

## [TBD] 留尾

- sub-service contextvar fallback 实现细节（TreeModeSearch/ContextCompiler/GraphTraverse 各自的 `_effective_workspace_id()` helper）——05 实施时落定。
- asyncio.to_thread vs copy_context 选择（collaborate.py ThreadPoolExecutor 替代方案）——05 实施时验证后落定。
