# ADR-015: agent 角色注册表 + 活动聚合机制

## 状态：Accepted

## 上下文

v1.15.0 agent/link 能力轮（PRD-agent-link-v1.15.0），补齐三项续留 finding：

1. **自定义 agent 角色注册**（v1.5.0 留 v2.0 候选 → v1.15.0）：`build_default_agents()`（`src/saw/engines/collaborate/agents/__init__.py:35`）硬编码 6 角色（Librarian/Writer/Critic/Linker/Scholar/Guardian），无外部注册入口。用户无法注册领域自定义角色（如 MedicalExpert / LegalAnalyst）。

2. **M2 agent 活动聚合**（v1.9.0 M2 续留）：`GET /api/v1/agents`（`src/saw/api/routes/collaborate.py:426` `list_agents()`）返回静态 roster，调用 `build_default_agents(llm_router=None)` 返回 name/model_tier/tools_allowed/rule，无活动数据（calls/failures/last_action/last_active_at）。

PRD 要求：
- 自定义角色通过配置文件注册，不修改 `build_default_agents()` 签名/返回结构（additive 合并）。
- 活动聚合通过 event bus 订阅 `WorkflowStep` 事件，内存态聚合，不持久化，不阻塞 workflow 执行。
- 不引入新依赖，复用既有 `InMemoryEventBus.add_subscriber` / `BaseAgent.__init__` / `WikiRepository.write` / `compute_related_pages`。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| `build_default_agents()` 硬编码 6 角色 | `src/saw/engines/collaborate/agents/__init__.py:35` | 构造 Librarian/Writer/Critic/Linker/Scholar/Guardian 6 个实例返回 dict，无外部注册入口 |
| `BaseAgent.__init__` 接受 name/model_tier/system_prompt/tools_allowed/constraints | `src/saw/engines/collaborate/agents/base.py:23` | 构造函数签名 `name: str, model_tier: Literal["haiku","sonnet","opus","rule"], system_prompt: str, tools_allowed: list[str], constraints: dict \| None = None`，可被自定义角色复用 |
| `list_agents()` REST 端点返回静态 roster | `src/saw/api/routes/collaborate.py:426` | 调用 `build_default_agents(llm_router=None)` 返回 name/model_tier/tools_allowed/rule，无活动数据 |
| `InMemoryEventBus.add_subscriber` 支持按事件类型订阅 | `src/saw/plugins/event_bus.py:71` | `add_subscriber(event_type: str \| None, handler: Callable[[Any], None])` 注册回调，匹配 `event_type` 或 None（全部）；handler 在 publisher 线程同步执行 |
| `WorkflowExecutor._execute_step` 发布 WorkflowStep 事件 | `src/saw/engines/collaborate/workflow_executor.py:389` | 事件 dict `{"type":"WorkflowStep","workflow_id":workflow_id,"step":f"{step.agent}.{step.action}","status":"completed","output_key":step.output_key}`，含 agent name |
| `_dispatch` fan-out handler 有 try/except 不传播 | `src/saw/plugins/event_bus.py:63`（`_dispatch` 方法） | `handler(event)` 包裹在 `try/except Exception` 中，`logger.warning("Event handler raised for '%s'", name, exc_info=True)`——handler 抛异常不传播 |
| `workflow_executions` 表存 workflow 级状态不存 per-agent 活动 | `src/saw/db/migrations.py:189`（v4 migration） | `CREATE TABLE workflow_executions(workflow_id, definition_name, status, steps_completed, steps_total, errors_json, updated_at, finished_at)`，无 agent_name 列 |
| `links suggest` 只打印不写回 | `src/saw/drivers/cli/commands/links_cmd.py:51` | suggest 命令调用 `compute_related_pages` 打印表格，不调用 `WikiRepository.write` |
| `WikiRepository.write()` 写回 Markdown+YAML frontmatter | `src/saw/adapters/storage/wiki_repository.py:42` | 接受 `WikiPage` 对象，`yaml.dump(fm)` + `page_path.write_text(content)` 写入磁盘 |

## 决策

### 决策一：agent 角色注册表 → 候选 ① YAML 配置文件 + build_default_agents 合并

选择候选 ①：**YAML 配置文件 + build_default_agents 合并**。

- 用户在 `.saw/agents/*.yaml` 放置角色定义文件（name/model_tier/system_prompt/tools_allowed）。
- 新增 `load_custom_agents()` 函数：启动时扫描 `.saw/agents/*.yaml`，用 `yaml.safe_load` 解析，校验 name 唯一性 + model_tier 合法性 + system_prompt 非空 + tools_allowed 格式，构造 `BaseAgent` 实例列表。
- 新增 `build_agent_roster()` 函数：调用 `build_default_agents(llm_router, feedback_engine)` 获取内置 6 角色 dict，再调用 `load_custom_agents()` 获取自定义角色，`dict.update()` 合并（自定义角色 additive 加入，不修改 `build_default_agents` 源码/签名/返回结构）。
- CLI `saw agents` 和 REST `GET /api/v1/agents` 改为调用 `build_agent_roster()` 替代直接调用 `build_default_agents()`。
- `WorkflowParser.validate()` 校验 `step.agent` 时，`available_agents` 集合含自定义角色名。

### 决策二：活动聚合机制 → 候选 ① event_bus subscriber 写内存计数器

选择候选 ①：**event_bus subscriber 写内存计数器**。

- 新增 `AgentActivityTracker` 类：初始化时调用 `event_bus.add_subscriber("WorkflowStep", handler)` 订阅 WorkflowStep 事件。
- `handler(event)` 解析 `event["step"]`（格式 `"{agent}.{action}"`，split(".") 取 agent name）+ `event["status"]`（completed/failed），按 agent name 分组更新内存计数器：`calls`（completed++）/`failures`（failed++）/`last_action`/`last_active_at`（ISO timestamp）。
- 计数器用 `dict[str, dict[str, Any]]` 存储（agent_name → {calls, failures, last_action, last_active_at}），无锁（handler 在 publisher 线程同步执行，单线程无竞争；`_dispatch` 串行调用 handler）。
- `GET /api/v1/agents/{name}/activity`：先查 roster 确认 agent 存在，再从 tracker 返回活动聚合。
- `GET /api/v1/agents`：roster 中每个 agent 附带 `activity_summary`（{calls, last_active_at}），无活动时为 `null`。
- 活动聚合为内存态（进程重启后丢失），不持久化。

## 备选方案

### 决策一备选（agent 角色注册表）

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① YAML 配置文件 + build_default_agents 合并（选） | 用户友好（YAML 声明式，不需写代码）；启动时扫描加载，运行时无开销；additive 合并不改 `build_default_agents()` 签名/返回；复用 `BaseAgent.__init__` 构造函数；`.saw/agents/` 目录约定与 `.saw/workflows/` 一致（既有范式）；YAML 格式错误跳过该文件不阻断启动 | 启动时全量加载，无动态热加载（PRD 明确不做）；YAML schema 须严格校验 | 自定义角色声明式注册 ✓ |
| ② DB 表存自定义角色 | 持久化存储；支持 CRUD API 动态增删角色；查询灵活 | 引入 DB schema 变更（migration + new table）；过度设计——角色定义是静态配置非动态数据；PRD 明确"不修改 `build_default_agents()` 签名"且"启动时扫描加载"，DB 方案偏离 PRD 意图；YAML 文件更符合 local-first 范式 | 排除：过度设计，偏离 PRD "配置文件注册"意图 |
| ③ Python API 动态注册（`register_agent(name, ...)`） | 灵活，可编程注册 | 用户须写 Python 代码，门槛高；PRD 明确"配置文件（YAML 或 Python API）"，YAML 为主路径；运行时注册增加并发复杂度 | 可选补充（非主路径），本轮不做 |

### 决策二备选（活动聚合机制）

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① event_bus subscriber 写内存计数器（选） | 复用既有 `InMemoryEventBus.add_subscriber` 机制（`event_bus.py:71`）；handler 轻量（仅计数器更新，O(1)）；不阻塞 workflow 执行（`_dispatch` 有 try/except 不传播异常）；内存态无 DB 开销；进程重启自动清零（PRD 明确不持久化）；实时聚合（事件发生即更新） | 内存态进程重启丢失（PRD 明确不做持久化）；handler 在 publisher 线程同步执行，须轻量（仅 dict 更新，满足约束） | 实时活动聚合 ✓ |
| ② DB 聚合查询 workflow_executions 表 | 持久化；重启不丢失；SQL 聚合灵活 | `workflow_executions` 表无 `agent_name` 列（ground claim 8 TRUE），须加列 + migration；每次查询全表扫描（无 agent 索引）；DB 开销大（每次 GET activity 跑 SQL）；PRD 明确"内存态不持久化"；过度设计 | 排除：PRD 明确不持久化 + 表无 agent 列 |
| ③ workflow_executor 直接调 tracker 方法 | 最直接，不走 event bus | 耦合 workflow_executor 与 tracker（违反关注分离）；event bus 已有 fan-out 机制，重复实现不 DRY；无法扩展到其他事件源 | 排除：违反关注分离 + 不 DRY |

## 理由

### 决策一理由（YAML 配置文件 + build_default_agents 合并）

1. **PRD 对齐**：PRD §3.1 业务规则 1 明确"自定义角色通过配置文件（YAML 或 Python API）注册"；交互流程步骤 1 明确 `.saw/agents/` 目录约定。YAML 配置文件是 PRD 指定的主路径。
2. **additive 合并安全**：不修改 `build_default_agents()` 源码/签名/返回结构（PMS 明确约束）。新增 `build_agent_roster()` 包装函数，先调 `build_default_agents()` 再 `load_custom_agents()` 合并——内置 6 角色行为不变。
3. **复用 BaseAgent 构造函数**：`BaseAgent.__init__(name, model_tier, system_prompt, tools_allowed, constraints)` 签名完全匹配自定义角色需求（ground claim 2 TRUE）。自定义角色直接 `BaseAgent(name, model_tier, system_prompt, tools_allowed)` 构造，无需新 class。
4. **local-first 范式**：`.saw/agents/*.yaml` 与既有 `.saw/workflows/*.yaml` 目录约定一致（config 文件驱动），符合项目 local-first 原则。
5. **候选 ② 淘汰理由**：DB 表方案引入 schema 变更（migration + new table）+ 过度设计（角色定义是静态配置非动态数据）+ 偏离 PRD "配置文件注册"意图。
6. **候选 ③ 不选主路径理由**：Python API 动态注册可作为后续扩展，但 PRD 主路径是 YAML 声明式（门槛低，用户友好）。

### 决策二理由（event_bus subscriber 写内存计数器）

1. **PRD 对齐**：PRD §3.3 业务规则 1 明确"活动聚合器通过 `InMemoryEventBus.add_subscriber("WorkflowStep", handler)` 订阅 WorkflowStep 事件"；业务规则 6 明确"活动聚合为内存态（进程重启后丢失），不持久化"。
2. **复用既有机制**：`InMemoryEventBus.add_subscriber(event_type, handler)` 已实现（`event_bus.py:71`），handler 在 publisher 线程同步执行，`_dispatch` 有 try/except 不传播异常（`event_bus.py:63`）——零改动复用。
3. **handler 轻量**：handler 仅做 `dict[agent_name]["calls"] += 1` + 更新 last_action/last_active_at——O(1) 内存操作，不阻塞 workflow 执行。
4. **无锁安全**：handler 在 publisher 线程同步执行（`_dispatch` 串行调用所有 handler），单线程无竞争——`dict` 更新无需锁。PRD §3.3 业务规则 7 明确"handler 在 publisher 线程同步执行，须轻量"。
5. **候选 ② 淘汰理由**：`workflow_executions` 表无 `agent_name` 列（ground claim 8 TRUE），须加列 + migration；PRD 明确"不持久化"；每次查询全表扫描开销大。
6. **候选 ③ 淘汰理由**：直接调 tracker 方法耦合 workflow_executor 与 tracker（违反关注分离），event bus 已有 fan-out 机制不 DRY。

## 后果

### 正面
- 用户可通过 `.saw/agents/*.yaml` 注册领域自定义 agent 角色，被 workflow YAML 引用执行。
- `GET /api/v1/agents/{name}/activity` 返回 agent 活动聚合（calls/failures/last_action/last_active_at），OPS 可观测 agent 运行态。
- `GET /api/v1/agents` roster 含 `activity_summary` 字段，一站式查看 agent 活跃度。
- 自定义角色 additive 合并，不修改 `build_default_agents()` 签名/返回，内置 6 角色行为不变。
- 活动聚合器复用 event bus 机制，handler 轻量不阻塞 workflow，异常不传播。

### 负面
- 新增 `load_custom_agents()` + `build_agent_roster()` 函数（`agents/__init__.py` 扩展，不改 `build_default_agents` 源码）。
- 新增 `AgentActivityTracker` 类（新文件或 collaborate 模块扩展）。
- `collaborate.py` REST `list_agents()` 改调 `build_agent_roster()` + 附带 `activity_summary`。
- `collaborate.py` REST 新增 `GET /api/v1/agents/{name}/activity` 端点。
- `links_cmd.py` 新增 `apply` 子命令。
- 活动聚合内存态，进程重启丢失（PRD 明确不做持久化，v2.0 候选）。

### 风险
- 自定义角色 YAML schema 格式多样 → 严格校验 + 跳过无效定义不阻断启动（PRD §3.1 异常处理）。
- event bus handler 阻塞 workflow → handler 轻量（仅计数器更新），`_dispatch` 有 try/except 不传播（PRD §8 风险 Low/Medium）。
- F-T-1 与 F-T-3 均触及 `collaborate.py` REST 但不同端点（F-T-1 = GET /agents 扩展 custom 标记；F-T-3 = GET /agents/{name}/activity 新增 + activity_summary 扩展），03 技术方案协调：F-T-1 先改 `list_agents()` 用 `build_agent_roster()`，F-T-3 再在 `list_agents()` 加 `activity_summary` + 新增 activity 端点，无冲突。

## 关联 Feature

- F-T-1（自定义 agent 角色注册——本 ADR 决策一：YAML 配置文件 + build_default_agents 合并）
- F-T-2（L2 links auto-apply——无新选型，复用 WikiRepository.write + compute_related_pages，本 ADR 不直接涉及但同属 v1.15.0）
- F-T-3（M2 agent 活动聚合——本 ADR 决策二：event_bus subscriber 写内存计数器）

## 关联 ADR

- ADR-001（Python 3.11 + Typer + FastAPI，Accepted）——CLI/REST 复用既有框架。
- ADR-002（SQLite + FTS5 + Write Queue，Accepted）——WikiRepository.write 复用既有 write 机制。

## [TBD] 留尾

- 自定义角色数量上界 [TBD]（PRD 未声明，预期有限）。
- 活动聚合持久化属 v2.0 候选（PRD 明确不做）。
- Python API 动态注册角色（候选 ③）作为后续扩展，本轮不做。
