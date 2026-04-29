# Smart Agent Wiki — 系统设计优化方案

> 基于 181 项目审计 + 三维并行研究（前端选型、模块架构、开发计划）的综合优化建议
>
> 日期：2026-04-25

---

## 一、优化总览

### 对原文档的评价

现有设计方案 (`smart_agent_wiki_design.md`) 在**功能完整性**方面已经是 181 个项目中最全面的，但在以下维度存在可优化空间：

| 维度 | 现状 | 优化方向 | 产出文档 |
|------|------|---------|---------|
| 前端选型 | 列出了 React + Cytoscape.js + Milkdown，但未深入论证 | 完成对比论证，调整为更优方案 | `frontend_tech_research.md` |
| 模块衔接 | 五大引擎独立描述，缺少引擎间数据流和接口定义 | 补充完整的接口协议和事件流 | 本文档 §三 |
| 开发计划 | 14 周（6+4+4），范围过大 | 修正为 21 周，更务实的分阶段交付 | 本文档 §四 |
| 技术架构 | 描述了选型但未给出目录结构和架构模式 | 推荐 Hexagonal Architecture + 完整目录结构 | 本文档 §三 |
| MVP 定义 | 功能清单式，缺少最小可行产品定义 | 明确 MVP 核心循环和 Aha Moment | 本文档 §四 |
| 数据模型 | Claims 数据库概念描述，无具体 schema | 完整 SQLite DDL + 查询 + 迁移策略 | `claims_schema.sql` 等 3 文件 |
| API 合约 | 无，仅列出 MCP 工具 | 27 个 HTTP 端点 + WebSocket + MCP 映射 | `api_contract.md` |
| LLM 策略 | 提到 LiteLLM 但无具体 prompt 设计 | 10 个 Prompt 模板 + Token 预算 + 成本管理 | `llm_prompt_strategy.md` |

---

## 二、前端技术栈优化

### 2.1 修正后的选型

| 层次 | 原方案 | 优化方案 | 调整理由 |
|------|--------|---------|---------|
| **图谱库** | Cytoscape.js | **@antv/G6 v5** | Canvas 瓶颈，1000+ 节点卡顿；G6 有 GPU+Rust 布局、React 官方适配器、中文文档 |
| **编辑器** | Milkdown | **Tiptap** | Milkdown 月下载 200K vs Tiptap 12.8M；ProseMirror 100+ 扩展覆盖更全；自定义"知识主张"节点类型更容易 |
| **UI 库** | 未明确 | **shadcn/ui + Tailwind CSS v4** | 源码级控制，无依赖锁定；知识管理工具需要高度定制UI |
| **状态管理** | 未明确 | **Zustand** | 1.1KB 极简，多 Store 模式匹配模块化架构，内置 persist 中间件适合桌面端 |

**保持不变**：React 19 + TypeScript（图谱/编辑器/UI 生态最优）、Tauri v2（桌面端）

### 2.2 新增前端依赖

```
React 19 + TypeScript
  ├── @antv/G6 v5          # 图谱可视化（替代 Cytoscape.js）
  ├── Tiptap               # Markdown 编辑器（替代 Milkdown）
  ├── shadcn/ui            # UI 组件库（新增）
  ├── Tailwind CSS v4      # 样式（新增）
  ├── Zustand              # 状态管理（新增）
  ├── React Router v7      # 路由
  ├── TanStack Query       # 数据请求
  ├── TanStack Table       # 虚拟滚动表格
  └── cmdk                 # 命令面板
```

### 2.3 关键架构决策

1. **封装 GraphRenderer 抽象层** — 隔离 G6 API 变更，允许未来在大规模场景下切换 sigma.js (WebGL)
2. **Tiptap 自定义扩展** — 创建 `claim.ts`（知识主张节点）、`confidence.ts`（置信度标注）、`source-ref.ts`（来源溯源链接）三个核心扩展
3. **WebSocket 实时通信** — 前端通过 FastMCP WebSocket 客户端接收知识主张更新、Agent 操作进度
4. **多 Store 模式** — auth/graph/search/editor 四个独立 Zustand Store，通过 `persist` 中间件持久化到本地

---

## 三、模块架构优化

### 3.1 架构模式：Hexagonal Architecture

**推荐六边形架构**而非 Clean Architecture，原因：

- **多种传输入口**（CLI/MCP/Web/Obsidian/16+ Agent）天然适配 Driving Adapter
- **多种存储后端**（SQLite/PostgreSQL/FTS5/可选向量）天然适配 Driven Adapter
- **可选组件多**（向量搜索、图数据库、云 LLM）— 与 Adapter 概念完美契合
- **插件系统** — 通过 Hexagonal 的端口-适配器模式实现

### 3.2 引擎间数据流

```
                        Collaborate Engine（编排层）
                        WorkflowParser → StepScheduler → GateEvaluator
                    ┌──────┬──────────┬──────────┬──────────┐
                    │      │          │          │          │
                 Ingest  Query     Govern      Learn      Agent
                    │      │          │          │          │
    ═══════════════╪══════╪══════════╪══════════╪══════════╪═══
    EVENT BUS      │      │          │          │          │
    (asyncio.Queue)│      │          │          │          │
    ═══════════════╪══════╪══════════╪══════════╪══════════╪═══
                    │      │          │          │          │
                 Write Queue (Outbox Pattern)
                 ┌──▼──┐┌──▼──┐┌───▼──┐┌──▼───┐┌──▼───┐
                 │Vault││Claim││Wiki  ││FTS5  ││Vector│
                 │(Git)││(SQL)││(MD)  ││Index ││(opt) │
                 └─────┘└─────┘└──────┘└──────┘└──────┘
```

### 3.3 通信模式：60% 直接调用 + 40% 事件驱动

**直接调用（需要同步返回值）**：
- Collaborate → Ingest/Query/Govern（编排需要结果）
- Query → Learn（编译需要热缓存数据）
- Ingest → Govern（验证需要置信度评估结果）
- Agent → Governor（策略检查 + 签名：同步判定）
- Agent → WriteQueue（推入 outbox）

**事件驱动（解耦，最终一致性）**：
- Ingest ──`ClaimsReady`──→ Govern（触发置信度评估）
- Govern ──`ContradictionFound`──→ Learn（触发 FSRS/强化更新）
- Govern ──`FreshnessExpired`──→ Learn（加入复习队列）
- Query ──`QueryCompleted`──→ Learn（更新热缓存和查询模式）
- Query ──`CoverageMiss`──→ Ingest（Research-on-Miss）
- Learn ──`SOPDistilled`──→ Collaborate（注入 Agent 上下文）
- WriteQueue ──`WriteFailed`──→ Govern（审计日志）

### 3.4 关键接口定义（Python Protocol 级别）

核心协议已定义在模块架构研究中，以下是关键摘要：

```python
# 五大引擎核心协议
class IngestPipeline(Protocol):   # classify → extract → fuse → validate → enqueue
class QueryEngine(Protocol):      # search / graph_traverse / compile_context / query / compare
class Governor(Protocol):         # assess_confidence / detect_contradictions / lint / blast_radius
class LearnEngine(Protocol):      # get_hot_cache / record_feedback / distill_sops / expire_knowledge
class Agent(Protocol):            # execute（检查 Cedar 策略 → 执行 → 签名收据 → 推入 WriteQueue）

# 存储协议
class Sink(Protocol):             # write / flush / is_healthy（幂等，op_id 去重）
class WriteQueue(Protocol):       # enqueue / enqueue_atomic / dispatch / retry_failed
class WorkflowEngine(Protocol):   # load_workflow / execute_workflow
```

### 3.5 Write Queue 最终一致性保证

| 保证 | 机制 |
|------|------|
| 持久性 | 写入 SQLite outbox，进程崩溃不丢失 |
| 原子性 | `enqueue_atomic` 使用 SQLite 事务，同一 session_id 的写入要么全部入队要么全部不入队 |
| 幂等性 | Sink 通过 `op_id` 去重，重复分发不产生副作用 |
| 最终一致性 | Sink 失败后指数退避重试（2^n 秒，最大 300s），超过 max_retries 进死信队列 |
| 事务边界 | 无跨 Sink 分布式事务，每个 Sink 独立处理，失败不影响其他 Sink |

### 3.6 目录结构

```
smart_agent_wiki/
├── src/saw/
│   ├── domain/                    # 核心领域模型 + Protocol 定义
│   │   ├── protocols.py           # 引擎接口协议
│   │   ├── value_objects.py       # ClaimRef, WikiPageRef, etc.
│   │   ├── events.py              # 事件定义
│   │   └── exceptions.py
│   ├── engines/                   # 五大引擎（纯业务逻辑）
│   │   ├── ingest/                # classify/extract/fuse/validate
│   │   ├── query/                 # search/graph/reason/compare/synthesize
│   │   ├── govern/                # confidence/contradiction/freshness/cedar/auditor
│   │   ├── learn/                 # adaptive/fsrs/distill/trend/expire
│   │   └── collaborate/           # agents/ + workflow_parser
│   ├── write_queue/               # Outbox Pattern 实现
│   ├── event_bus/                 # asyncio.Queue + SQLite 持久化
│   ├── adapters/                  # Driven Adapters（存储/解析/加密）
│   │   ├── storage/               # vault_sink, claims_sink, wiki_sink, fts5_sink, vector_sink, graph_sink
│   │   ├── llm/                   # LiteLLM 路由 + 嵌入模型
│   │   ├── parsers/               # pdf, markdown, code_ast, audio
│   │   └── crypto/                # Ed25519
│   ├── drivers/                   # Driving Adapters（传输入口）
│   │   ├── cli/                   # Typer CLI
│   │   ├── web/                   # FastAPI + React 静态文件
│   │   └── mcp/                   # FastMCP Server（23 工具）
│   ├── plugins/                   # 插件系统（entry_points + HookPoints）
│   └── config/                    # Pydantic Settings
├── web/                           # React 19 前端
│   ├── src/
│   │   ├── components/            # ui/graph/editor/wiki/search/dashboard
│   │   ├── stores/                # Zustand: auth/graph/search/editor
│   │   ├── hooks/
│   │   ├── lib/                   # mcp-client.ts, api.ts
│   │   └── pages/
│   └── src-tauri/                 # Tauri v2 桌面端
├── tests/                         # unit/integration/e2e
└── plugins/                       # 外部插件目录
```

---

## 四、开发计划优化

### 4.1 核心问题：原计划 14 周过于激进

参照竞品：
- **basic-memory**（最接近竞品）：v0.1 → v0.19 花了 ~8 个月，功能仅为 MCP + Markdown + SQLite + 向量
- **simonw/llm**：58 个 release，2 年多，核心只做 CLI + LLM 路由
- **Smart Agent Wiki 范围是 basic-memory 的 5-8 倍**

### 4.2 MVP 最小可行产品

**核心循环：摄入 → 提取结构化主张 → 搜索并回答（附溯源）**

Aha Moment：用户完成第三次摄入后的第一次查询，系统返回基于多源的合成回答，每条主张标注来源和页码。

**Must-Have (v1.0)**：

| 功能 | 理由 |
|------|------|
| Vault 存储（L0） | 零信息损失的根基 |
| Claims 数据库（L1, SQLite） | 结构化主张是核心数据模型 |
| 摄入引擎 — Markdown + URL + PDF | 覆盖 80%+ 输入场景 |
| BM25 + FTS5 搜索（L3） | 零依赖搜索 |
| CLI: init / ingest / query / search / lint | 完整闭环 |
| LiteLLM 集成 | 摄入提取和查询回答需要 LLM |
| Write Queue 基础版 | 保证写入到 Vault + Claims + Index |

**Nice-to-Have（延后）**：Tree Mode、Git 集成、WIP 文件、MCP Server、新鲜度、多 LLM 竞争、治理引擎、学习引擎、Web UI

### 4.3 修正后的路线图（21 周到 0.5.0-rc）

#### Phase 1A: 核心循环（4 周）

| 周 | 交付物 | 验收标准 |
|---|--------|---------|
| W1 | 项目脚手架 + 存储层 | `saw init` 创建目录+SQLite；Claims 表 schema；pytest 框架；pyproject.toml + CI |
| W2 | 摄入引擎（MD + URL） | `saw ingest notes.md` 完整流程：Vault→提取主张→Claims→FTS5；摄入报告（N条主张/耗时/费用） |
| W3 | 查询引擎 + CLI | `saw query` 返回带溯源链答案；`saw search` FTS5 匹配；LiteLLM 集成；saw.yaml 配置 |
| W4 | 集成测试 + 0.1.0-alpha | 3源摄入→查询验证；`saw lint` 基础；pip install 本地测试；README + 5分钟快速开始 |

#### Phase 1B: 基础设施补全（3 周）

| 周 | 交付物 | 验收标准 |
|---|--------|---------|
| W5 | PDF 摄入 + Git 集成 | PyMuPDF 提取；vault 自动 git commit；摄入失败回滚 |
| W6 | Write Queue + 错误恢复 | 同步写入 Vault+Claims+Index；outbox 持久化+重试；`saw status` |
| W7 | MCP Server v1 + 0.2.0-alpha | FastMCP 5 工具：ingest/query/search/lint/status；MCP与CLI共享核心逻辑；WIP基础版 |

#### Phase 2A: 治理引擎（4 周）

| 周 | 交付物 | 验收标准 |
|---|--------|---------|
| W8 | 置信度体系 + 来源标记 | 4 层置信度 + 三级来源标记(extracted/inferred/ambiguous)；页面级聚合计算 |
| W9 | 矛盾检测 + 冲突处理 | 自动对比新主张；三种策略(Superseded/Disputed/Historical)；`saw conflicts` |
| W10 | 新鲜度 + Schema 治理 | 9 级新鲜度；Schema infer/validate/diff |
| W11 | 治理集成 + 0.3.0-beta | `saw verify`；矛盾检出率 > 80%（测试集）|

#### Phase 2B: 学习引擎 + MCP 完整版（4 周）

| 周 | 交付物 | 验收标准 |
|---|--------|---------|
| W12 | 训练期自适应 | 前 30 天训练期；修正操作→规则；preferences.yaml |
| W13 | 认知蒸馏 + 反馈强化 | approved/rejected 双反馈；Echo 蒸馏→SOP；知识过期基础 |
| W14 | MCP 23 工具 + 多 LLM | 23 工具全部实现；Haiku/Sonnet/Opus 按任务路由；三层降级测试 |
| W15 | 集成 + 0.4.0-beta | Ed25519 基础版；Cedar 策略基础版；`saw audit` |

#### Phase 3: 协作 + 可视化（6 周）

| 周 | 交付物 | 验收标准 |
|---|--------|---------|
| W16 | 多 Agent 框架 | 6 角色+调度器；单用户模式 Guardian+Librarian+Writer |
| W17 | YAML 工作流引擎 | 解析器+执行引擎；3 个内置模板 |
| W18 | Web UI 基础版 | React+Vite；页面浏览+搜索+摄入；MVP 前端只做展示 |
| W19 | 图谱可视化 + 编辑器 | @antv/G6 知识图谱；Tiptap 编辑器；图谱浏览+页面编辑 |
| W20 | 向量搜索 + Chrome 扩展 | LanceDB 可选；all-MiniLM-L6-v2；混合搜索；Chrome 剪藏基础版 |
| W21 | FSRS + 集成 + 0.5.0-rc | 间隔重复复习；Research-on-Miss 基础版；全功能集成测试 |

### 4.4 发布策略

| 版本 | 时间 | 包含 | 通过标准 |
|------|------|------|---------|
| 0.1.0-alpha | W5 | CLI + MD/URL 摄入 + BM25 | init→ingest→query < 5 分钟 |
| 0.2.0-alpha | W8 | +PDF + Write Queue + MCP(5) | Write Queue 零丢失 |
| 0.3.0-beta | W12 | +治理引擎 | 矛盾检出率 > 80% |
| 0.4.0-beta | W16 | +学习引擎 + MCP(23) | 3 外部用户 7 天留存 > 40% |
| 0.5.0-rc | W22 | +多 Agent + Web UI | 工作流端到端跑通 |
| 1.0.0-stable | W24+ | 全引擎 + 文档 + Demo | 所有成功指标达标 |

---

## 五、关键决策变更总结

| 决策 | 原方案 | 优化方案 | 理由 |
|------|--------|---------|------|
| Phase 1 时长 | 6 周 | 7 周（4+3） | 原计划 8 个子系统过载 |
| 总时长 | 14 周 | 21 周（到 0.5.0-rc） | 参照竞品节奏 |
| 图谱库 | Cytoscape.js | @antv/G6 v5 | GPU+Rust 布局、React 官方适配、中文文档 |
| 编辑器 | Milkdown | Tiptap | 12.8M 月下载、100+ 扩展、ProseMirror 定制能力 |
| MCP 引入时机 | Phase 2 | Phase 1B（5 工具） | 早期 MCP 是增长杠杆 |
| 架构模式 | 未明确 | Hexagonal Architecture | 多传输入口+多存储后端+插件友好 |
| Web UI 时机 | Phase 3 | 保持 Phase 3 | CLI 先行验证后端逻辑 |
| PDF 支持 | Phase 1 | Phase 1A 用 PyMuPDF, Phase 1B 增强 | 渐进式实现 |
| 测试策略 | 2368 总量目标 | 按阶段递增 | 自然增长：150→250→450→600→900+ |

---

## 六、风险与缓解

| 风险 | 可能性 | 影响 | 缓解 |
|------|--------|------|------|
| PDF 解析质量不稳定 | 高 | 高 | 多级降级 MinerU→Docling→PyMuPDF；MVP 先用 PyMuPDF |
| LLM API 变更/涨价 | 中 | 高 | LiteLLM 抽象 + 本地模型降级 |
| FTS5 搜索质量不足 | 中 | 中 | Tree Mode 增强 + Catalog 模式兜底 |
| 多 Agent 编排复杂度爆炸 | 高 | 中 | Phase 3 前不做多 Agent，先做单 Agent+规则引擎 |
| Write Queue 多 Sink 一致性 | 中 | 高 | MVP 先同步写入，Phase 1B 再引入异步 outbox |

---

## 七、北极星指标

**用户从 `saw init` 到第一个带溯源链的查询回答的时间 < 5 分钟**

各 Phase 通过标准：

| Phase | 核心验证 |
|-------|---------|
| 1A | init→ingest→query < 5分钟，查询返回溯源链 |
| 1B | Write Queue 零丢失，MCP 工具可用 |
| 2A | 矛盾检出率 > 80% |
| 2B | 3 个外部用户 7 天留存 > 40% |
| 3 | 多 Agent 工作流端到端跑通 |

---

## 八、数据模型设计

### 8.1 Claims 数据库（L1 层）

完整的 SQLite Schema 已设计并通过验证（`docs/claims_schema.sql`）：

**核心表（8 张）：**

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `claim` | 结构化知识主张 | content, confidence(1-4), source_mark, freshness(0-8), temperature, lifecycle |
| `claim_relation` | 主张间关系 | supports/refutes/supplements/corrects/supersedes |
| `claim_source` | 主张溯源 | vault_uuid, page_number, paragraph, surrounding_text |
| `contradiction` | 矛盾记录 | 3 类型 × 3 策略 × 3 状态 |
| `entity` | 命名实体 | 5 种类型，JSON 别名，claim_count 缓存 |
| `entity_relation` | 实体间关系 | 7 种关系类型，溯源到来源主张 |
| `claim_entity` | 多对多关联 | 带 subject/object/context 角色 |
| `audit_receipt` | Ed25519 签名收据 | 不可变（触发器阻止 UPDATE/DELETE） |

**基础设施表（2 张）：** `schema_migration`（版本迁移）、`write_outbox`（Outbox Pattern）

**FTS5 全文索引：** `claim_fts` 虚拟表，Porter 词干 + Unicode61 分词，通过触发器自动同步

**验证结果：** 16 张表 + 35 个索引 + 17 个触发器全部通过 Python sqlite3 加载测试

**配套文件：**
- `docs/claims_schema.sql` — 完整 DDL
- `docs/claims_queries.sql` — 9 类关键查询示例
- `docs/claims_migration_and_performance.sql` — 迁移策略 + 性能优化 + PostgreSQL 迁移路径

### 8.2 关键设计决策

| 决策 | 说明 |
|------|------|
| 置信度 × 来源标记正交 | confidence(1-4) 是聚合后页面可信度，source_mark 是主张级来源质量，两者正交组合 |
| 软删除 + 部分索引 | 所有活跃查询通过 `WHERE deleted_at IS NULL` 过滤，索引均为 partial index |
| FK 通过触发器实现 | SQLite FK 不支持软删除过滤，改用 BEFORE INSERT 触发器 |
| 审计不可变 | audit_receipt 通过触发器阻止 UPDATE/DELETE，保证审计链完整 |
| 缓存字段自动维护 | entity.claim_count 通过 INSERT/DELETE 触发器自动递增/递减 |
| PRAGMA 优化 | WAL 模式 + 64MB 缓存 + 64MB mmap + NORMAL 同步 + 5s 锁等待 |

---

## 九、API 合约设计

完整的 RESTful API + WebSocket 协议已设计（`docs/api_contract.md`）。

### 9.1 API 路由总览

| 引擎 | 端点数 | 核心路由 |
|------|--------|---------|
| 通用 | 2 | `/health`, `/status` |
| Ingest | 3 | `POST /ingest`, `GET /ingest/{id}/status`, `GET /ingest/history` |
| Query | 5 | `POST /query`, `POST /search`, `GET /graph/{id}`, `POST /compare`, `POST /compile` |
| Govern | 7 | `GET/PATCH /claims/{id}`, `GET /contradictions`, `POST /verify`, `POST /lint`, `POST /blast-radius` |
| Learn | 5 | `POST /feedback`, `POST /distill`, `GET /sop`, `POST /prune`, `GET /wip` |
| Collaborate | 2 | `POST /workflows`, `GET /workflows/{id}/status` |
| Wiki | 3 | `GET /pages`, `GET /pages/{id}`, `PUT /pages/{id}` |
| **合计** | **27** | |

### 9.2 关键接口设计

- **分页：** Cursor-based（Base64 编码的 `{created_at, uuid}`），避免 offset 性能问题
- **错误格式：** RFC 7807 Problem Details，统一 `type`/`title`/`status`/`detail`/`request_id`
- **认证：** 桌面模式用 API Key，团队模式用 JWT + RBAC
- **异步处理：** 摄入和工作流返回 202 Accepted + 轮询 URL

### 9.3 WebSocket 协议

8 种事件类型覆盖所有实时推送场景，客户端通过 `subscribe` 订阅特定 topic（ingest/query/govern/learn/collaborate）。

### 9.4 MCP 工具映射

23 个 MCP 工具到 HTTP API 的一一映射已完成，共享核心引擎层通过 Hexagonal Architecture 的 Driving Adapter 模式实现。

---

## 十、LLM Prompt 策略

完整的 Prompt 模板体系已设计（`docs/llm_prompt_strategy.md`）。

### 10.1 Prompt 模板清单

| 引擎 | 场景 | 模型 | 版本 |
|------|------|------|------|
| Ingest | 文档分类 | Haiku | v1 |
| Ingest | 主张提取 | Sonnet | v1 |
| Ingest | 多源融合 | Sonnet | v1 |
| Query | 意图识别 | Haiku | v1 |
| Query | 查询回答 | Opus | v1 |
| Query | 综述生成 | Opus | v1 |
| Govern | 矛盾检测 | Sonnet | v1 |
| Govern | 置信度评估 | Sonnet | v1 |
| Learn | 认知蒸馏 | Sonnet | v1 |
| Collaborate | 5 Agent 角色 | Haiku/Sonnet/Opus/None | v1 |

### 10.2 Token 预算与成本

| 模式 | 日摄入 | 日查询 | 月成本(USD) |
|------|--------|--------|------------|
| 经济 | 5文档 | 20查询 | ~$5 |
| 标准 | 10文档 | 30查询 | ~$15 |
| 高质量 | 20文档 | 50查询 | ~$40 |

单文档摄入成本：经济 ~$0.005，标准 ~$0.03，高质量（双LLM）~$0.04。

### 10.3 可跳过 LLM 的 15+ 操作

代码 AST 解析、JSON Schema 验证、BM25 搜索、新鲜度计算、Cedar 策略检查、Ed25519 签名、Git 操作、重复检测（content_hash）、搜索排序（BM25/TF-IDF）、Write Queue 分发等——覆盖约 60% 的日常操作。

### 10.4 三层缓存策略

L1 Exact Match（1h TTL）→ L2 Semantic（24h，余弦 >0.95）→ L3 Hot Cache（会话级，高频页面预编译）。缓存失效由 Claim 更新和新文档摄入触发。

### 10.5 Prompt 版本管理

YAML 文件 + manifest 索引，支持模型降级配置和 A/B 测试框架。

---

## 十一、文档体系总览

| 文档 | 内容 | 状态 |
|------|------|------|
| `smart_agent_wiki_design.md` | 原始设计方案（五大引擎、23 附录） | ✓ 完成 |
| `smart_agent_wiki_optimization.md` | 本文档 — 综合优化方案 | ✓ 完成 |
| `frontend_tech_research.md` | 前端技术选型深度研究报告 | ✓ 完成 |
| `claims_schema.sql` | Claims 数据库完整 DDL | ✓ 验证通过 |
| `claims_queries.sql` | 9 类关键查询示例 | ✓ 完成 |
| `claims_migration_and_performance.sql` | 迁移策略 + 性能优化 + PostgreSQL 迁移 | ✓ 完成 |
| `api_contract.md` | RESTful API + WebSocket + MCP 映射 | ✓ 完成 |
| `llm_prompt_strategy.md` | Prompt 模板 + Token 预算 + 成本管理 | ✓ 完成 |

---

*本优化方案基于六份研究文档综合生成：前端选型、模块架构、开发计划、Claims 数据模型、API 合约、LLM Prompt 策略*
*Last updated: 2026-04-25*
