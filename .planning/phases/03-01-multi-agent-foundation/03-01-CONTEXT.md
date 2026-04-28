# Phase 03-01: Multi-Agent Foundation - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning
**Source:** Auto-generated from ROADMAP + REQUIREMENTS + Design Document

<domain>
## Phase Boundary

实现 Smart Agent Wiki 的多代理协作基础：6 个专业化 Agent、模型路由、YAML 工作流编排、Cedar 策略引擎、A2A 协议。用户可以定义 YAML 工作流，调度不同 Agent 协作完成任务，并通过 Cedar 策略控制 Agent 权限。

此阶段不涉及 Web UI 实现（属于 03-02/03-03），但需要定义 Agent 接口以便 Web API 调用。

</domain>

<decisions>
## Implementation Decisions

### Agent 定义 (COLL-01)
- **D-01:** 6 个专业化 Agent：Librarian（索引维护）、Writer（页面创作）、Critic（质量审核）、Linker（交叉链接）、Scholar（深度推理）、Guardian（安全检查）
- **D-02:** Agent 角色定义包含：system_prompt、default_model、tools_allowed、constraints
- **D-03:** Guardian Agent 为纯规则引擎，不调用 LLM（零成本安全检查）

### 模型路由 (COLL-02)
- **D-04:** 三层模型路由：Haiku（高频低成本）→ Sonnet（质量平衡）→ Opus（深度推理）
- **D-05:** 路由规则基于任务复杂度而非固定分配：简单任务 Haiku，中等任务 Sonnet，复杂推理 Opus
- **D-06:** 支持运行时降级：当 Opus 不可用时自动降级到 Sonnet

### YAML 工作流编排 (COLL-03)
- **D-07:** YAML 工作流定义包含：name、steps、gates、fallback
- **D-08:** 每个 step 指定：agent、action、input、output、gates（可选）
- **D-09:** Gate 条件支持：confidence 级别、contradiction_count、freshness 阈值
- **D-10:** Fallback 动作：重试、降级模型、通知用户、终止工作流

### Cedar 策略引擎 (COLL-04)
- **D-11:** cedar-python 0.1.4 为实验性，需要 PolicyEngine 协议抽象
- **D-12:** 支持两种后端：cedar-python（优先）→ CLI subprocess fallback
- **D-13:** 策略定义粒度：permit/forbid 按 Agent × Tool 组合
- **D-14:** 默认拒绝策略：未明确 permit 的操作一律 forbid

### A2A 协议 (COLL-05)
- **D-15:** A2A 消息格式：sender、receiver、action、payload、context、trace_id
- **D-16:** 支持同步调用和异步回调两种模式
- **D-17:** 任务移交（handoff）包含完整上下文，接收 Agent 可继续工作
- **D-18:** 每个 A2A 消息生成 Ed25519 签名收据（复用 Phase 02 审计层）

### Claude's Discretion
- Agent system_prompt 的具体内容设计
- 路由复杂度的具体阈值定义
- YAML 工作流解析器的错误处理细节
- Cedar CLI subprocess 的具体命令格式
- A2A 消息超时和重试策略

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Document
- `docs/smart_agent_wiki_design.md` — 协作引擎设计、Agent 角色表、YAML 工作流示例、Cedar 策略示例（Section 2.1 引擎五、Section 4.3 MCP 工具清单、附录 A.15/A.17）

### Phase 02 Context (Foundation)
- `.planning/phases/02-intelligence-governance/02-CONTEXT.md` — Phase 02 的设计决策，包括审计层和治理引擎
- `.planning/phases/02-intelligence-governance/02-03-SUMMARY.md` — MCP Server 实现、Research-on-Miss 模式

### Research Documents
- `.planning/research/ARCHITECTURE.md` — Hexagonal architecture、Write Queue 模式
- `.planning/research/PITFALLS.md` — cedar-python 实验性警告、Agent 协调陷阱

### Project Context
- `.planning/PROJECT.md` — Vision、core value、constraints
- `.planning/REQUIREMENTS.md` — COLL-01~05 需求定义
- `.planning/ROADMAP.md` — Phase 03 定义、Success Criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets from Phase 01/02
- **Domain Layer**: Claims DB、Wiki pages、Graph、Index
- **Write Queue**: Outbox pattern for durable mutations
- **LLM Router**: LiteLLM integration with fallback/retry
- **Audit Layer**: Ed25519 signing、receipt chain verification
- **MCP Server**: 23 tools implemented、FastMCP integration
- **CLI Framework**: Typer + Rich formatting

### Integration Points
- **Agent Dispatch**: 复用 LLM Router 的模型选择逻辑
- **Policy Engine**: 作为 MCP tool 调用前的权限检查
- **A2A Messages**: 通过 Write Queue 持久化，生成审计收据
- **Workflow Engine**: 解析 YAML、调度 Agent、执行 gates

### Established Patterns
- Hexagonal architecture with ports/adapters
- Protocol-based abstraction（如 PolicyEngine）
- Async queue pattern
- SQLite WAL mode for concurrent read/write

</code_context>

<specifics>
## Specific Ideas

### Agent 角色设计（来自设计文档）

| 角色 | 职责 | 模型建议 | 典型任务 |
|------|------|---------|---------|
| **Librarian** | 索引维护、分类、搜索优化 | Haiku | 元数据提取、页面分类 |
| **Writer** | 页面创作、摘要生成 | Sonnet | Wiki 页面撰写、摘要 |
| **Critic** | 矛盾检测、质量审核 | Sonnet | 草稿审核、置信度评估 |
| **Linker** | 交叉链接发现、图谱维护 | Haiku | Wikilink 发现、关系抽取 |
| **Scholar** | 深度推理、综述生成 | Opus | 复杂查询、综述页面 |
| **Guardian** | 安全检查、权限控制 | 规则引擎 | 策略验证、敏感数据检测 |

### YAML 工作流示例（来自设计文档 A.17）

```yaml
# workflows/literature_review.yaml
name: 文献综述生成
steps:
  - agent: Librarian
    action: search
    input: "{{ query }}"
    output: related_pages

  - agent: Scholar
    action: synthesize
    input: related_pages
    output: draft_synthesis

  - agent: Critic
    action: review
    input: draft_synthesis
    gates:
      - confidence >= 3
      - contradiction_count == 0

  - agent: Writer
    action: publish
    input: reviewed_synthesis
    output: wiki_page
```

### Cedar 策略示例（来自设计文档 A.15）

```
permit(Librarian, saw_ingest) when confidence >= 2;
forbid(Writer, saw_verify);  // Writer 不能自行验证
```

### A2A 消息格式

```json
{
  "sender": "librarian-001",
  "receiver": "writer-002",
  "action": "handoff",
  "payload": {
    "task": "create_wiki_page",
    "entity": "transformer",
    "sources": ["claim:uuid-1", "claim:uuid-2"]
  },
  "context": {
    "workflow_id": "wf-123",
    "step": 2
  },
  "trace_id": "trace-abc-123"
}
```

</specifics>

<deferred>
## Deferred Ideas

None — all Phase 03-01 requirements are in scope.

</deferred>

---

*Phase: 03-01-multi-agent-foundation*
*Context gathered: 2026-04-28 via auto-generation*
