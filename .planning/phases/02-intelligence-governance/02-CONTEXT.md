# Phase 2: Intelligence & Governance - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

为知识库添加智能治理层——置信度评分、矛盾检测与解决、新鲜度追踪、学习引擎、MCP Server（23个工具）、审计层（Ed25519签名收据）。用户可以信任知识库的质量，通过 `saw lint`、`saw conflicts`、`saw freshness`、`saw audit` 等 CLI 命令监控和治理知识库健康状态。

</domain>

<decisions>
## Implementation Decisions

### 置信度计算
- **D-01:** 混合升级策略——Cross-Validated 以下自动升级，Human Verified 需要人工审核确认
- **D-02:** 三等级来源标记正交设计——extracted（直接提取）/ inferred（推理得出）/ ambiguous（不确定），与页面置信度正交组合
- **D-03:** 永不自动降级——置信度只升不降，只有人工操作可以降级
- **D-04:** Cross-Validated 升级阈值——最少 2 个独立来源确认即升级
- **D-05:** 独立来源定义——必须来自不同 Vault 文档（UUID 不同），同一文档不同页面/段落不算独立

### 矛盾检测算法
- **D-06:** 异步队列检测——后台队列异步检测，平衡实时性和性能，不影响摄入速度
- **D-07:** 两阶段检测算法——先基于关键词和语义相似度筛选候选对，再用 LLM 精确判断是否矛盾
- **D-08:** LLM 自动分类矛盾类型——由 LLM 判断矛盾属于时间矛盾/观点矛盾/事实矛盾
- **D-09:** 全部自动解决——三类矛盾都根据规则自动应用解决策略（Superseded/Disputed/Historical）

### 新鲜度追踪
- **D-10:** 保持 9 级新鲜度系统——级别 0-8，0=最新鲜，8=最过期
- **D-11:** 颜色均等分割映射——Green(0-2)、Yellow(3-5)、Orange(6-7)、Red(8)
- **D-12:** 多信号综合计算——时间衰减 + 用户访问 + 引用频率 + 来源更新
- **D-13:** 访问自动刷新——当用户查询或访问页面时自动重置新鲜度

### 学习引擎集成
- **D-14:** 按依赖顺序实现——训练期 → 过期修剪 → FSRS → 反馈文件 → 认知蒸馏 → 趋势感知
- **D-15:** 训练期实时调整——训练期内也实时调整推荐和展示，而非纯观察模式
- **D-16:** 训练期默认 30 天，用户可配置——在 `.saw/config.yaml` 中可自定义长度
- **D-17:** FSRS 页面级复习——FSRS 调度 Wiki 页面的复习时间，用户被提醒复核重要页面
- **D-18:** 知识永不过期——所有知识都永不过期，除非用户手动删除
- **D-19:** 认知蒸馏 SOP 提取——从用户反馈中自动提取标准操作流程（SOP），形成可复用的最佳实践
- **D-20:** 反馈混合收集模式——编辑隐式接受，拒绝需要显式操作
- **D-21:** 趋势感知缺口检测——监控知识库增长模式，识别知识缺口，建议合成页面

### Claude's Discretion
- 矛盾检测候选筛选的语义相似度阈值具体数值
- FSRS 参数调优（默认使用 py-fsrs 库推荐值）
- 新鲜度各信号权重具体数值
- 训练期学习结果应用的具体算法
- SOP 提取的触发条件和格式
- 缺口检测的启发式规则

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Document
- `docs/smart_agent_wiki_design.md` — Full architecture, 5 engines, 4-layer storage, 23 appendix design decisions (A.1-A.23)

### Research
- `.planning/research/STACK.md` — Technology stack recommendations with versions and rationale
- `.planning/research/FEATURES.md` — Feature landscape, table stakes, differentiators, dependency chains
- `.planning/research/ARCHITECTURE.md` — Hexagonal architecture, Write Queue design, engine decomposition
- `.planning/research/PITFALLS.md` — 12 domain-specific pitfalls with warning signs, prevention, phase mapping

### Project Context
- `.planning/PROJECT.md` — Vision, core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — 65 v1 requirements with traceability (GOVE-01~08, LEARN-01~06, CLI-05~11, MCP-01~02, XCUT-05~08 for Phase 2)
- `.planning/ROADMAP.md` — Phase 2 definition, requirements mapping, success criteria
- `.planning/STATE.md` — Current state, blockers/concerns (cedar-python, FSRS mapping)
- `.planning/phases/01-core-data-cycle/01-CONTEXT.md` — Prior phase decisions that Phase 2 builds on

### Ecosystem Analysis
- `docs/llm_wiki_ecosystem_analysis.md` — 181-project categorization
- `docs/remote_project_audit_findings.md` — Deep audit of reference projects with relevant patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 1 已实现：Domain layer、Write Queue、Storage adapters、CLI framework、FTS5 search、LLM Router
- Claims DB schema 已支持 `confidence` 和 `source_type` 字段（Phase 1 设计时预埋）
- Wiki YAML frontmatter 已包含 `confidence` 和 `freshness` 字段

### Established Patterns
- Hexagonal architecture with ports/adapters
- Write Queue (Outbox) pattern for durable mutations
- SQLite WAL mode for concurrent read/write
- Typer CLI with Rich formatting
- Async queue pattern（可复用于矛盾检测）

### Integration Points
- Claims DB 扩展：添加 `cross_validated_at`、`validated_by` 字段
- Wiki frontmatter 扩展：添加 `last_reviewed`、`review_count` 字段
- CLI 新命令：`lint`、`conflicts`、`freshness`、`audit`、`review`
- MCP Server：新增 23 个工具（Phase 2 主要交付）

### Concerns (from STATE.md)
- cedar-python 0.1.4 是实验性的 — Guardian agent 需要抽象为 PolicyEngine 协议，支持 CLI subprocess fallback
- FSRS-to-wiki 页面映射已通过讨论决定：页面级复习

</code_context>

<specifics>
## Specific Ideas

- `saw lint` 应输出结构化健康报告：矛盾数、孤儿页数、断链数、缺失元数据、过期声称
- `saw conflicts` 应展示冲突详情、解决策略建议、影响范围（blast radius）
- 矛盾检测的"独立来源"必须严格定义为不同文档，避免同一文档内部的冗余被误判为交叉验证
- 训练期学习应该"边学边用"，而不是纯观察 30 天后才应用
- 反馈收集应该是"无感知"的——编辑即接受，但拒绝需要显式操作

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-intelligence-governance*
*Context gathered: 2026-04-26*
