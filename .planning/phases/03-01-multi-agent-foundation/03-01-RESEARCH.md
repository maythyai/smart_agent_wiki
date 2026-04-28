# Phase 03-01: Multi-Agent Foundation - Research

**Researched:** 2026-04-28
**Status:** Research complete
**Source:** Existing research docs + design doc + PITFALLS.md

## Summary

本阶段实现 Smart Agent Wiki 的多代理协作基础。核心技术挑战：
1. cedar-python 0.1.4 实验性 → 需 PolicyEngine 协议抽象 + CLI fallback
2. YAML 工作流死锁风险 → 需要 max_retries + fallback_action + timeout
3. A2A 协议版本漂移 → 版本协商 + 拒绝不兼容连接
4. Agent 资源死锁 → 锁顺序规范 + 超时检测

## Technical Findings

### 1. Agent Role Design (COLL-01)

**来源**: 设计文档 Section 2.1 引擎五、附录 A.17

**Agent 角色表**:

| 角色 | 职责 | 模型 | 成本 |
|------|------|------|------|
| Librarian | 索引维护、分类、搜索优化 | Haiku | 低 |
| Writer | 页面创作、摘要生成 | Sonnet | 中 |
| Critic | 矛盾检测、质量审核 | Sonnet | 中 |
| Linker | 交叉链接发现、图谱维护 | Haiku | 低 |
| Scholar | 深度推理、综述生成 | Opus | 高 |
| Guardian | 安全检查、权限控制 | 规则引擎 | 零 |

**设计要点**:
- Guardian 为纯规则引擎，不调用 LLM（零成本安全检查）
- 6 个 Agent 角色定义包含：system_prompt、default_model、tools_allowed、constraints
- 支持运行时降级：Opus → Sonnet → Haiku

### 2. Model Routing (COLL-02)

**来源**: PITFALLS.md Pitfall 2

**关键发现**:
- LiteLLM `allowed_fails=0` 默认值过于激进
- 单一 API Key 共享所有模型组的 rate limit 会级联阻塞
- 建议使用 `allowed_fails=3` 最小值
- 不同模型层使用独立 API Key

**路由规则**:
```
任务复杂度 → 模型选择
─────────────────────────
简单任务（高频）→ Haiku
中等任务（质量）→ Sonnet  
复杂推理（深度）→ Opus
```

**降级策略**:
- 当 Opus 不可用时自动降级到 Sonnet
- 设置 fallback 顺序：Opus → Sonnet → Haiku

### 3. YAML Workflow Orchestration (COLL-03)

**来源**: 设计文档 A.17 + PITFALLS.md Pitfall 10/17

**工作流示例**:
```yaml
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

**关键风险 (Pitfall 10/17)**:
1. Gate 不满足时无限循环
2. Agent 资源锁死锁
3. A2A 消息队列溢出
4. 无 fallback 动作

**规避策略**:
1. 每个 step 必须有 `max_retries`（默认 3）和 `fallback_action`
2. 工作流级别 timeout：N 分钟未完成则 abort
3. 锁顺序规范：Vault → Claims → Wiki → Graph → Index
4. Gate 支持 `accept_with_flag`：无法满足时接受并标记

### 4. Cedar Policy Engine (COLL-04)

**来源**: 设计文档 A.15 + PITFALLS.md Pitfall 12/13

**关键风险 (Pitfall 13)**:
- cedar-python 0.1.4 标记为实验性
- 与官方 Rust/JS 实现功能不完全对等
- Python binding 更新节奏可能滞后

**规避策略**:
```python
class PolicyEngine(Protocol):
    def evaluate(self, agent: str, action: str, context: dict) -> bool:
        ...

class CedarPythonAdapter(PolicyEngine):
    """优先使用 cedar-python"""
    def evaluate(self, agent, action, context):
        import cedar
        return cedar.is_authorized(agent, action, context)

class CedarCLIAdapter(PolicyEngine):
    """CLI subprocess fallback - 权威但较慢"""
    def evaluate(self, agent, action, context):
        result = subprocess.run(['cedar', 'authorize', ...])
        return result.returncode == 0
```

**策略示例**:
```
permit(Librarian, saw_ingest) when confidence >= 2;
forbid(Writer, saw_verify);  // Writer 不能自行验证
```

**Pitfall 12 - Guardian 规则复杂性螺旋**:
- 规则集上限：200 条
- 自动生成规则 TTL：30 天
- 每次操作日志包含 rule_id
- `saw_lint --rules` 检查冲突/冗余规则

### 5. A2A Protocol (COLL-05)

**来源**: 设计文档 + PITFALLS.md Pitfall 15

**消息格式**:
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
  "trace_id": "trace-abc-123",
  "signature": "ed25519:..."  // 复用 Phase 02 审计层
}
```

**Pitfall 15 - A2A 版本漂移**:
- 协议版本嵌入 Agent Card
- 版本协商：拒绝不兼容版本连接
- 记录所有未知消息类型
- 设计可插拔适配器：`A2AAdapterV1`, `A2AAdapterV2`

**关键决策**:
- A2A 默认异步模式（消息队列），非同步 RPC
- 支持同步调用和异步回调两种模式
- 任务移交包含完整上下文

## Validation Architecture

### Test Coverage Requirements

| 组件 | 测试类型 | 覆盖目标 |
|------|---------|---------|
| Agent 定义 | 单元测试 | 6 个 Agent 角色验证 |
| 模型路由 | 集成测试 | 路由规则 + 降级 |
| YAML 解析器 | 单元测试 | 有效/无效 YAML |
| Workflow 执行器 | 集成测试 | step 顺序 + gate |
| Cedar 集成 | 集成测试 | permit/forbid 场景 |
| CLI fallback | 集成测试 | cedar-python 失败时 |
| A2A 消息 | 单元测试 | 消息格式验证 |
| A2A 队列 | 压力测试 | 消息积压处理 |

### Critical Success Factors

1. **PolicyEngine 协议正确抽象** — 确保 cedar-python 和 CLI 可互换
2. **YAML 工作流解析器健壮** — 处理无效输入，不崩溃
3. **Gate 条件可评估** — 支持变量引用和比较操作
4. **A2A 消息可溯源** — 每个 trace_id 可追踪完整链路
5. **锁顺序正确** — 避免死锁

## Dependencies

### Phase 02 Assets (复用)

- **LLM Router**: LiteLLM 集成，fallback/retry 逻辑
- **Audit Layer**: Ed25519 签名、收据链验证
- **Write Queue**: Outbox 模式、多 Sink 分发
- **Governance Engine**: Confidence 系统、Freshness 追踪
- **MCP Server**: FastMCP 集成、tool 注册模式

### New Dependencies

- `cedar` (Python binding) 或 `cedar` CLI
- `pyyaml` — YAML 解析
- `jinja2` — 模板变量替换
- `asyncio.Queue` — A2A 消息队列

## Open Questions

### Claude's Discretion (设计决策)

1. **Agent system_prompt 具体内容** — 每个角色的 prompt 工程
2. **路由复杂度阈值** — 什么任务算"简单/中等/复杂"
3. **Gate 条件语法** — 支持哪些操作符和函数
4. **A2A 超时策略** — 消息过期时间和重试次数
5. **Workflow 持久化** — 中断后如何恢复

## Risk Register

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| cedar-python API 变更 | 高 | 中 | PolicyEngine 协议抽象 |
| YAML 工作流死锁 | 中 | 高 | max_retries + timeout |
| A2A 消息丢失 | 低 | 高 | Write Queue 持久化 |
| Agent 资源争用 | 中 | 中 | 锁顺序规范 |
| 规则集膨胀 | 高 | 中 | TTL + 上限 |

---

*Phase: 03-01-multi-agent-foundation*
*Research complete: 2026-04-28*
