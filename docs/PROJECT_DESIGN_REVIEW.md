# Smart Agent Wiki — 项目设计深度审查报告

> 审查日期：2026-08-11
> 审查范围：全栈（后端 70,830 LOC / 376 Python 文件 + React 19 前端 + Tauri 2 桌面端）
> 审查方法：架构文档对照实现、跨子系统源码精读、五路并行深度审计

---

## 目录

1. [审查总览与评分卡](#一审查总览与评分卡)
2. [架构设计评价](#二架构设计评价)
3. [核心子系统实现真相](#三核心子系统实现真相)
4. [关键问题清单（按严重度排序）](#四关键问题清单按严重度排序)
5. [文档与实现的偏差](#五文档与实现的偏差)
6. [安全评估](#六安全评估)
7. [改进建议与优先级路线图](#七改进建议与优先级路线图)
8. [结论](#八结论)

---

## 一、审查总览与评分卡

### 1.1 总体评价

Smart Agent Wiki **不是空壳项目（vaporware）**——其核心算法、管线、连接器、前端均有真实且相当成熟的实现。但在"工程化交付"维度存在**系统性偏差**：文档描述的目标架构与代码现状之间存在三重分裂，关键治理/安全承诺在代码层并未落实。

**一句话定性**：一个**设计远见优秀、核心实现扎实、但治理边界与文档真实性失守**的项目。

### 1.2 子系统评分卡

| 子系统 | 实现度 | LOC/规模 | 核心结论 |
|--------|--------|----------|----------|
| **Code Graph（代码图谱）** | 🟢 90% | 5,067 LOC | 六阶段生命周期真实编排；Python AST 生产级，TS 仅正则启发式 |
| **存储 / Write Queue / Adapters** | 🟡 65% | ~6,977 LOC | Outbox 设计精良但**非唯一写入网关**；无迁移框架 |
| **连接器（Connectors）** | 🟢 85% | ~170KB | Notion/GitHub 真实 OAuth；IM 连接器只读；GitHub Discussions 桩 |
| **前端（Web）** | 🟢 95% | 50+ 组件 | React19+Cytoscape+Milkdown+Zustand 全栈真实可用 |
| **桌面端（Tauri）** | 🟢 90% | Rust | 原生菜单/托盘/快捷键/文件监听完整 |
| **Ingest DAG Pipeline** | 🟢 85% | 6 阶段 | 拓扑排序+环检测真实；与旧管线并存导致重复 |
| **Govern / Reconcile / Synthesize** | 🟡 55% | ~2,600 LOC | 算法真实但**脱离持久层**（纯内存/JSON 文件） |
| **Workflows（YAML）** | 🟢 90% | 408 LOC | 解析+执行+门控+回退真实；代理实现待验证 |
| **Plugins（插件系统）** | 🔴 30% | 8.7KB | 仅骨架——**无沙箱、无事件总线、钩子永不触发** |
| **Token Optimizer** | 🟡 60% | 53.5KB | 追踪真实但"65% 节省"为硬编码估算，未接入主管线 |
| **Drivers / API / Auth** | 🔴 40% | — | **REST 仅实现 ~15-20% 合约；认证中间件从未挂载；用户存内存** |
| **LLM Gateway** | 🟡 60% | 305 LOC | LiteLLM 重试/路由真实；**无 token/成本追踪** |

---

## 二、架构设计评价

### 2.1 设计亮点（值得肯定）

1. **六边形架构真实落地**：`domain/`（纯 Python 值对象+Protocol）→ `engines/`（业务逻辑）→ `adapters/`（基础设施）→ `drivers/`（CLI/Web/MCP）的分层清晰，依赖方向基本正确。Domain 层零外部依赖。

2. **四层存储模型（Vault→Claims→Wiki→Index）概念扎实**：Vault 不可变文件存储、Claims SQLite、Wiki Markdown+frontmatter、FTS5 索引，每层职责清晰、Sink 接口统一（`name/write/can_handle`）。

3. **Write Queue（SQLite Outbox）设计精良**：`queue.py` 实现了原子入队、指数退避重试、死信队列、`PROCESSING→PENDING` 崩溃恢复（`dispatcher.py`）。这是真正可用的可靠投递模式。

4. **Code Graph 六阶段生命周期**：Parse→Build→PostProcess→Query→Review→Update 由 `engine.py` 真实编排，含增量构建（git-diff + content-hash 双模式）、WAL+FTS5、加权 BFS 影响分析（`WILL_BREAK/LIKELY_AFFECTED/MAY_NEED_TESTING` 风险分级）。

5. **代码图谱的安全卫生优秀**：`incremental.py:161-167` 对 git 子进程禁用 fsmonitor/hooks/pager/editor 并设置 `GIT_CONFIG_NOSYSTEM=1`，防止恶意仓库在 `git diff` 期间执行代码——这是少见的防御性细节。

6. **加密栈选型正确**：PyNaCl（Ed25519 审计收据，私钥 0600/目录 0700）、Fernet（连接器 token at rest）、bcrypt（密码）——密码学原语选型无瑕疵。

7. **前端工程质量高**：Zustand 切片化 store、React Query 服务端状态、WebSocket 指数退避心跳、Cytoscape 性能优化（`hideEdgesOnViewport`/`textureOnViewport`）、Command Palette、Milkdown 编辑器——均为生产级实现。

### 2.2 架构性问题（设计层）

#### P1 — 单一可变网关原则失守（D-04 原则）

`queue.py:3` 声称 "Single durable entry point"，但实际**仅 core ingest→claims→wiki→FTS 走 Write Queue**。以下子系统全部绕过 outbox 直写各自 DB：

| 绕过点 | 写入对象 | 机制 |
|--------|---------|------|
| `code_graph/store.py:197-530` | 代码图谱节点/边 | 独立 SQLite 连接+独立 schema |
| `engines/ingest/preview.py:79-357` | 预览 claims/entities | 直 `INSERT/UPDATE/DELETE` |
| `engines/query/wiki_indexer.py:77-112` | Wiki FTS 索引 | 直 `INSERT INTO fts_index` |
| `engines/govern/linter.py:230-271` | Lint 结果 | 直 `conn.execute` |
| `engines/govern/contradiction.py:329-375` | 矛盾记录 | 直 `INSERT INTO contradiction` |
| `audit/service.py:236-237` | 审计日志 | ORM `session.add()` |
| `connectors/*` 多处 | 同步游标/状态 | ORM 直写 |

**后果**：崩溃恢复、重放、审计链的保证**仅覆盖主摄入管线**，治理/代码图谱/连接器写入无 outbox 保护。这是架构承诺与实现的最严重分裂。

#### P2 — 三重 Schema 分裂

`claim` 表存在三个互不一致的版本：

| 维度 | `docs/claims_schema.sql`（参考） | `claims_repository.py`（代码） | `db/models.py`（ORM） |
|------|----|----|----|
| 列数 | 20+ | 12 | 14（含 `media_timestamp`） |
| `freshness` 0-8 | ✅ | ❌ 缺失 | ❌ |
| `temperature` 分层 | ✅ | ❌ 缺失 | ❌ |
| `lifecycle` 战略/战术 | ✅ | ❌ 缺失 | ❌ |
| `claim_source`/`claim_entity` 表 | ✅ | ❌ 缺失 | ❌ |
| `contradiction`/`audit_receipt` 表 | ✅ | ❌ 缺失 | ❌ |
| FK 触发器 / `updated_at` 触发器 | ✅ | ❌ 缺失 | ❌ |
| FTS 分词器 | `porter unicode61` | `unicode61` | N/A |
| 迁移机制 | `user_version`+`schema_migration` | 临时 `ALTER TABLE` try/except | `create_all` |

**代码实现约 30% 的参考 schema**，且文档中的新鲜度/温度/生命周期分层治理在代码层基本不存在——但 README/API 合约却把它们当作已交付能力对外宣传。

#### P3 — 无迁移框架

`docs/claims_schema.sql` 定义了 `PRAGMA user_version = 1` 和 `schema_migration` 表，但**全代码零引用**。唯一"迁移"是 `queue.py:85-89` 的临时 `ALTER TABLE ... ADD COLUMN` 包在 try/except 里。所有表用 `CREATE TABLE IF NOT EXISTS`，意味着**对已存在数据库的列变更会被静默忽略**——线上库升级会直接丢失字段。

---

## 三、核心子系统实现真相

### 3.1 Code Graph（代码图谱）— 生产级

**真实可用**：`engine.py:68-90` 编排六阶段；`store.py:112-117` 正确设置 WAL+`synchronous=NORMAL`+`busy_timeout=5000`+`foreign_keys=ON`；FTS5 用触发器自动同步（`store.py:67-77`）。

**影响分析真实**：`engine.py:131-197` 加权 BFS，`new_score = parent_score * edge.weight * DEPTH_DECAY(0.85)`，`SCORE_FLOOR=0.05` 剪枝，按深度分派风险等级（`engine.py:280-286`）。

**增量同步真实**：git 模式（`incremental.py:147-218`）解析 `--name-status` 含 R/C 重命名，hash 模式（220-243）做兜底。

**短板**：
- TS/JS 仅正则启发式（`parser.py:377-489`），**无调用图**，`end_line` 永远等于 `start_line`。README 宣称的"Tree-sitter AST 零 LLM"未落地（pyproject 无 tree-sitter 依赖）。
- `flows.py:_check_test_coverage()` 永远返回 False——无组件生成 `TESTED_BY` 边。
- `resolvers/python_resolver.py:_resolve_endpoints()` 检查 `metadata["decorators"]`，但解析器从不填充该键 → 死代码。
- `postprocess.py`/`snapshot.py` 直访 `self.store._conn` 破坏封装。

### 3.2 存储与 Write Queue — 设计好但边界失守

详见 §2.2 P1。补充：

- **FTS5 Sink 非事务**（`fts5_sink.py:42-52`）：DELETE+INSERT+commit 未包在单事务，崩溃窗口丢失索引项。
- **双 Ed25519 实现**：`adapters/crypto/ed25519.py`（PyNaCl）与 `audit/service.py:85-133`（cryptography 库）密钥格式/签名编码不兼容；审计服务无持久密钥时生成临时密钥 → **重启后签名不可验证**。
- **Fernet 密钥未持久化**（`token_encryption.py:44-48`）：未设 `SAW_ENCRYPTION_KEY` 时自动生成新密钥但**不落盘** → 加密 token 重启后不可读。
- **LLM 网关零追踪**（`adapters/llm/router.py`）：无 `response.usage` token 提取、无成本表、无客户端限流、无流式。`extract_claims()` 解析 JSON 失败即致命抛错。

### 3.3 Drivers / API / Auth — 最薄弱环节

**REST API 仅实现 ~15-20% 的 `api_contract.md`**：大量端点（`/claims/{id}`、`/blast-radius`、`/verify`、`/lint`、`/distill`、`/prune`、`/workflows`、WebSocket 等）只存在于 CLI/MCP，HTTP 侧缺失。

**认证中间件存在但从未挂载到任何端点**——全部端点无鉴权。RBAC/Cedar（`adapters/crypto/cedar_policy.py` 327 LOC，含 python binding + CLI 子进程兜底 + default-deny）写得很认真，但**没有路由真正用上它**。

**用户持久化纯内存**——每次重启重置。JWT/bcrypt/refresh token 代码齐备，但 `User` 表不被实际写入。

**MCP 工具数虚标**：实际 ~62 个 `saw_*` 函数，README 标 "30+"（低估），文档章节标 "24+"（过时）。

### 3.4 插件系统 — 装饰性骨架

- `PluginBase` ABC + `PluginContext` + `Registry` 结构正确，`discover()`/`load()`（`importlib.util.spec_from_file_location`）真实。
- **致命缺口**：
  - **无沙箱**：`__init__.py:3` docstring 写 "sandboxing"，但**零实现**。插件经 `importlib` 拥有完整解释器权限，`data_dir` 只是 Path，无文件系统隔离。
  - **无事件总线**：`PageCreated`/`ClaimCreated` 等事件是纯 dataclass，无 pub/sub。`drivers/cli/commands/plugin_cmd.py:87` 中 `publish_event = lambda x, y: None`——事件发往虚空。**无任何引擎调用 `plugin.on_event()`**。

### 3.5 Token Optimizer — 追踪真实，宣传失实

五个模块（Anatomy/Cerebrum/BugLog/SessionTracker/TokenLedger）均有持久化实现，Cerebrum 跨会话记忆真实。但：

- "65% token 节省"基于硬编码常量 `AVG_TOKENS_PER_ANATOMY_HIT_SAVED=800`、`..._REPEATED_READ_SAVED=500`（`token_ledger.py:42-45`），**无基准测试、无实测校准**。
- 模块**未接入主管线**：AnatomyIndex 不被任何引擎调用，SessionTracker 不挂文件读取，TokenLedger 不记录真实 LLM 调用。

### 3.6 连接器 — 真实但有误导

- Notion/GitHub OAuth 真实（`oauth_handler.py` 用 `secrets.token_urlsafe(32)` 做 state）。
- **GitHub OAuth 静默兜底**（`github/oauth.py:142`）：网络异常时落回 `{"access_token": "test_token"}`——生产环境安全隐患。
- IM 连接器（Slack/Discord/Feishu/WeCom）**全部只读**，`put_item` 抛 `NotImplementedError`，但 README 暗示双向。
- GitHub Discussions（`connector.py:278`）返回 `[]` 桩。
- 生产代码中混入 ~100 行 Mock 类（`github/connector.py:434-530`、`notion/connector.py:380-413`）。

### 3.7 Reconcile / Synthesize — 脱离持久层

矛盾检测（Jaccard 相似度、否定/时序/置信度）、解决策略（freshness-wins/confidence-wins/source-diversity）、合成（TF-IDF 挖掘+聚类+AI 生成）算法真实，但**全程内存/JSON 文件**，不读不写 Claims DB。与主数据流脱节。

---

## 四、关键问题清单（按严重度排序）

### 🔴 Critical（阻断生产可用）

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| C1 | 认证中间件从未挂载，全部端点无鉴权 | `api/routes/*` | 安全裸奔 |
| C2 | 用户持久化纯内存 | `auth/` | 重启即重置，团队部署不可用 |
| C3 | Write Queue 非唯一写入网关 | 多处见 §2.2 P1 | outbox 保证仅覆盖主摄入，治理/图谱无可靠投递 |
| C4 | 无迁移框架，列变更静默丢失 | `queue.py:85-89` 唯一"迁移" | 线上库升级丢字段 |
| C5 | Fernet 密钥未持久化 | `token_encryption.py:44-48` | 加密 token 重启后不可读 |

### 🟡 High（架构债务）

| # | 问题 | 影响 |
|---|------|------|
| H1 | REST API 仅实现 ~15-20% 合约 | 团队/API 不可用，MCP 与 HTTP 非对称 |
| H2 | 三重 Schema 分裂（docs/code/ORM） | 文档失真，治理字段（freshness/temperature/lifecycle）代码缺失 |
| H3 | 双不兼容 Ed25519 实现 | 审计收据跨实现不可验，重启后不可验 |
| H4 | 插件无沙箱+无事件总线 | 插件系统仅装饰，不可安全扩展 |
| H5 | Token Optimizer 未接入主管线 + "65%"未实测 | 核心卖点失实 |
| H6 | Reconcile/Synthesize 脱离持久层 | 矛盾治理/合成结果不入库 |
| H7 | LLM 网关无 token/成本追踪 | 无法兑现 api_contract 中的 `cost_usd`/`tokens_used` |

### 🟢 Medium/Low（代码质量）

| # | 问题 | 位置 |
|---|------|------|
| M1 | `flows._check_test_coverage` 永远 False（死代码） | `flows.py:224` |
| M2 | `python_resolver._resolve_endpoints` 检查永不存在的键 | `resolvers/python_resolver.py` |
| M3 | TS 解析无调用图、无 `end_line` | `parser.py:377-489` |
| M4 | `communities._find_hubs` N+1 查询 | `communities.py:237-258` |
| M5 | 死信队列无监控/告警/重试 UI | `queue.py:260-278` |
| M6 | FTS5 Sink DELETE+INSERT 非事务 | `fts5_sink.py:42-52` |
| M7 | 生产代码混入 Mock 类 | `github/connector.py:434-530` |
| M8 | GitHub OAuth 静默兜底假 token | `github/oauth.py:142` |
| M9 | `postprocess`/`snapshot` 直访 `store._conn` | 破坏封装 |
| M10 | 旧/新 Ingest 管线并存 | `pipeline_v2.py` vs `ingest/pipeline/` |

---

## 五、文档与实现的偏差

### 5.1 `ARCHITECTURE.md` 严重过时

- 文件名/实体模型与实际不符（如 `evidence.py` 实际已并入 Claim，文档仍单列）。
- 置信度范围、新鲜度范围、管线阶段、存储层数均与代码不一致。
- 文档描述"五引擎"，实际有六个（多了 **Compile** 引擎，~18 个 MCP 工具，未在架构图体现）。

### 5.2 README 宣传失实项

| 宣传 | 实际 |
|------|------|
| "6 Specialized Agents — Librarian/Writer/Critic/Linker/Scholar/Guardian" | `domain/agent.py` 仅定义 DTO（AgentTask/Context/Result），**无具名代理实现类**，仅工作流按字符串派发 |
| "30+ MCP tools" / "24+" | 实际 ~62 个，badge 低估、章节过时 |
| "Sandbox Isolation — Each plugin gets its own data_dir" | **无任何沙箱实现** |
| "Reduce LLM token consumption by 65%+" | 硬编码常量估算，未实测、未接入主管线 |
| Roadmap "Web UI Impact visualization (D3.js)" | 未交付，前端用 Cytoscape 非 D3 |
| Roadmap "Tree-sitter AST zero LLM parsing" | 未交付，pyproject 无 tree-sitter |
| Roadmap "LadybugDB / KuzuDB graph database" | 未交付，仍用 SQLite |
| Roadmap "Agent Skills Layer" | 未交付 |

### 5.3 `api_contract.md` 高保真但代码低兑现

合约本身设计优秀（RFC 7807 错误、cursor 分页、`op_id` 幂等、WebSocket 主题订阅、MCP↔HTTP 映射表），但**代码兑现率低**——合约是"待实现蓝图"而非"已交付规格"。

---

## 六、安全评估

| 维度 | 状态 | 说明 |
|------|------|------|
| 认证 | 🔴 未生效 | JWT/bcrypt 代码齐备但中间件未挂载 |
| 授权 (RBAC/Cedar) | 🟡 未接线 | Cedar 引擎 default-deny 写得好，但无路由调用 |
| SQL 注入 | 🟢 低风险 | 全参数化 `?` 占位，仅静态 DDL 用 `executescript` |
| 路径穿越 | 🟢 已防护 | `parser.py:_resolve_relative_import`、`context_tool.py`、`logseq connector` 均有 `is_relative_to` 校验 |
| Git 子进程 | 🟢 优秀 | 禁用 hooks/fsmonitor/pager + `GIT_CONFIG_NOSYSTEM=1` |
| 文件大小防护 | 🟢 2MB 上限 | parser + context_tool |
| FTS 查询转义 | 🟢 有 | `store.py:search_nodes_fts` 双引号包裹 + LIKE 兜底 |
| 加密 at rest | 🟡 部分 | Fernet 选型正确但密钥未持久化 |
| 审计收据 | 🟡 部分 | Ed25519 正确但双实现+临时密钥致跨重启不可验 |
| OAuth | 🟡 部分 | state 用 `secrets.token_urlsafe(32)` 良好，但 GitHub 静默兜底假 token |
| 速率限制 | 🔴 未接线 | 文档称 Redis 滑窗，代码未见挂载 |
| 安全头 (CSP/HSTS) | 🔴 未生效 | 中间件未挂载 |
| 输入清洗 | ❓ 待核 | SQLi/XSS 模式检测代码存在，需确认是否在中间件生效 |

**总结**：密码学原语与防御性细节（路径/git/FTS）质量高；但**认证授权体系整体未接线**，是部署到团队环境的最大风险。

---

## 七、改进建议与优先级路线图

### 阶段 0 — 真实性对齐（1-2 周，立即）

1. **修正 README/ARCHITECTURE**：把"6 agents"改为"6 agent 角色（DTO 已定义，实现待补）"；删除/标注 "Sandbox Isolation"；"65%" 改为"理论估算，待基准"；更新 MCP 工具数；Roadmap 标注实际状态。
2. **统一 Schema 真相源**：选定 `claims_repository.py` 代码为准，把 `docs/claims_schema.sql` 改为"目标 schema（部分未实现）"，或反向补齐代码到文档。消除三重分裂。

### 阶段 1 — 安全接线（2-3 周，阻断团队部署）

1. **挂载认证中间件**到所有 `/api/v1/*` 写端点（C1）。
2. **用户持久化落 DB**（C2）——`User` 表已有 ORM，只需接线。
3. **持久化 Fernet 密钥**（C5）到 `.saw/config.yaml`，缺失时生成并写盘。
4. **统一 Ed25519**（H3）——以 PyNaCl 实现为唯一，删除 audit/service 的 cryptography 实现，密钥持久化。
5. **GitHub OAuth 删除假 token 兜底**（M8）——失败即报错。

### 阶段 2 — 治理边界（3-4 周）

1. **Write Queue 收口**（C3）：让 govern/contradiction/linter/code_graph 的写入经 outbox，或明确文档化"哪些子系统属 outbox 范围"。
2. **迁移框架**（C4）：引入 Alembic 或最小化 `user_version` 迁移器，废弃 try/except `ALTER TABLE`。
3. **REST API 兑现合约**（H1）：按 `api_contract.md` 优先补齐 `/claims/{id}`、`/blast-radius`、`/verify`、`/lint`、`/workflows`、WebSocket。
4. **Reconcile/Synthesize 入库**（H6）：把矛盾/合成结果写回 Claims DB 而非 JSON 文件。

### 阶段 3 — 兑现宣传（4-6 周）

1. **插件事件总线**（H4）：实现 in-process pub/sub，引擎在 `ClaimCreated`/`PageUpdated` 等点 `publish`，registry 分发到 `plugin.on_event()`；沙箱可用 RestrictedPython 或子进程隔离（先做事件总线，沙箱分期）。
2. **LLM token/成本追踪**（H7）：在 `router.py` 提取 `response.usage`，建模型价格表，回填 `api_contract` 的 `cost_usd`/`tokens_used`。
3. **Token Optimizer 接入主管线 + 实测校准**（H5）：把 AnatomyIndex 接入 query 编译、SessionTracker 接入文件读取；跑基准测试校准常量后再对外给数。
6 个具名代理实现类（补齐 `domain/agent.py` 之外的 `engines/collaborate` 实现）。
4. **清理死代码**（M1/M2）、生产 Mock 移出（M7）、TS 调用图（M3，或明确标注 TS 为只读结构图）。

---

## 八、结论

Smart Agent Wiki 展现了**少见的系统设计野心**——四层存储、六引擎、六代理、代码图谱六阶段生命周期、outbox 治理、加密审计链、插件沙箱、token 优化。**核心算法与前端实现是真实的、扎实的、可用的**，尤其是 Code Graph 子系统与 React 前端已达生产级。

然而项目正处在**"宣传跑在实现前面"**的典型阶段：架构文档与代码三重分裂，安全/治理承诺（认证、RBAC、Write Queue 统一、插件沙箱、token 追踪）在代码层大面积未兑现或未接线，README 的若干卖点（6 agents、沙箱、65%、Roadmap）与实际不符。

**判定**：
- 作为**个人/本地知识工具**（CLI + MCP + 单机 Web）→ **可用且优秀**。
- 作为**团队/多用户生产平台**（HTTP API + RBAC + 团队部署）→ **尚未就绪**，需完成阶段 1-2 的安全接线与 API 兑现。
- 作为**对外发布开源项目**→ **需先做阶段 0 真实性对齐**，否则文档失真会损害信誉与采用者信任。

最高优先级的两件事：**(1) 把认证中间件真正挂上去并持久化用户/密钥；(2) 修正文档使其与代码一致**。前者决定能否上生产，后者决定能否被信任。

---

*本报告基于 2026-08-11 代码快照的源码精读生成，所有结论附 file:line 可追溯。*
