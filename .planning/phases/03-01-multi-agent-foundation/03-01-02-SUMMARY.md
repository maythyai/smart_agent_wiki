---
phase: 03-01
plan: 02
subsystem: collaborate
tags:
  - cedar-policy
  - workflow-orchestration
  - multi-agent
  - yaml-parser
  - policy-engine
requires:
  - 03-01-01 (Multi-Agent Foundation - Agent definitions, Dispatcher, A2A)
provides:
  - Cedar policy engine with Python binding and CLI fallback
  - YAML workflow parser with validation and defaults
  - Workflow executor with gates, retries, and fallback actions
  - CollaborateEngine orchestrator as unified entry point
affects:
  - Phase 03-02 (Web API will expose workflow execution)
  - Phase 03-03 (React Frontend will trigger workflows)
tech_stack:
  added:
    - Cedar policy engine integration (cedar-python or CLI)
    - YAML parsing with PyYAML
    - Jinja2 template rendering
    - asyncio.timeout for workflow execution
  patterns:
    - Protocol-based abstraction (PolicyEngine)
    - Fallback pattern (Python binding -> CLI subprocess)
    - Default deny policy (fail-secure)
key_files:
  created:
    - src/saw/adapters/crypto/cedar_policy.py
    - src/saw/engines/collaborate/workflow_parser.py
    - src/saw/engines/collaborate/workflow_executor.py
    - src/saw/engines/collaborate/orchestrator.py
    - workflows/example_literature_review.yaml
    - tests/test_cedar_policy.py
    - tests/test_workflow_parser.py
    - tests/test_workflow_executor.py
    - tests/test_collaborate_orchestrator.py
  modified:
    - src/saw/adapters/crypto/__init__.py
    - src/saw/engines/collaborate/__init__.py
decisions:
  - D-11: cedar-python 0.1.4 为实验性，需要 PolicyEngine 协议抽象
  - D-12: 支持两种后端：cedar-python（优先）→ CLI subprocess fallback
  - D-13: 策略定义粒度：permit/forbid 按 Agent × Tool 组合
  - D-14: 默认拒绝策略：未明确 permit 的操作一律 forbid
  - D-07: YAML 工作流定义包含 name、steps、gates、fallback
  - D-08: 每个 step 指定 agent、action、input、output、gates
  - D-09: Gate 条件支持 confidence、contradiction_count、freshness
  - D-10: Fallback 动作：重试、降级模型、通知用户、终止工作流
metrics:
  duration: ~15 minutes
  test_count: 60 new tests
  files_created: 9
  files_modified: 2
---

# Phase 03-01 Plan 02: YAML Workflow Orchestration + Cedar Policy Summary

## One-Liner

实现了 Cedar 策略引擎（支持 cedar-python 和 CLI fallback）和 YAML 工作流编排系统，通过 CollaborateEngine 统一入口整合所有多 Agent 协作功能。

## Key Outputs

### Cedar Policy Engine

- **PolicyEngine 协议**：统一接口，支持多种后端实现
- **CedarPythonAdapter**：优先使用 cedar-python 绑定
- **CedarCLIAdapter**：CLI subprocess fallback，权威但较慢
- **CedarPolicyEngine**：自动选择可用后端，失败时默认拒绝
- **默认拒绝策略 (D-14)**：任何评估失败都返回 `allowed=False`

### YAML Workflow Parser

- **WorkflowParser**：解析 YAML 工作流定义
- **WorkflowDefinition** 和 **WorkflowStep** 数据类
- **必需字段验证**：name, steps, agent, action
- **Gate 条件语法验证**：支持 `>=`, `<=`, `==`, `!=`, `>`, `<` 操作符
- **默认值**：`max_retries=3` (PITFALLS.md Pitfall 17), `timeout=300`
- **Jinja2 模板支持**：`{{ query }}` 变量替换

### Workflow Executor

- **WorkflowExecutor**：异步执行工作流
- **Gate 条件评估**：支持 confidence, contradiction_count, freshness
- **重试逻辑**：max_retries 默认 3，超过后执行 fallback
- **Fallback 动作**：`abort`, `accept_with_flag`, `escalate_to_human`
- **超时控制**：asyncio.timeout 防止无限执行
- **事件发布**：工作流开始/完成/步骤完成事件

### CollaborateEngine Orchestrator

- **统一入口**：整合 Dispatcher、A2A、Workflow、Policy
- **dispatch_agent**：带策略检查的 Agent 调度
- **execute_workflow**：从 YAML 路径执行工作流
- **check_policy**：策略权限检查
- **handoff**：A2A 任务移交

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written.

## Key Design Decisions

1. **PolicyEngine 协议抽象**：确保 cedar-python 和 CLI 可互换，应对实验性绑定风险
2. **默认拒绝策略**：安全优先，任何未明确允许的操作都被拒绝
3. **Gate 条件语法**：简单的比较操作符，避免复杂的表达式解析风险
4. **max_retries=3 默认值**：按 PITFALLS.md Pitfall 17 防止无限循环
5. **Fallback 动作三级**：abort（终止）、accept_with_flag（接受并标记）、escalate_to_human（人工审核）

## Test Coverage

| 测试文件 | 测试数 | 覆盖内容 |
|---------|-------|---------|
| test_cedar_policy.py | 15 | PolicyDecision、适配器、引擎、fallback |
| test_workflow_parser.py | 16 | 解析、验证、gate 语法、Jinja2 |
| test_workflow_executor.py | 19 | 执行、gate 评估、fallback、超时 |
| test_collaborate_orchestrator.py | 10 | 统一入口、策略检查、集成 |
| **Total** | **60** | |

## Integration Points

- **From Plan 01**：
  - `AgentDispatcher.dispatch()` - Agent 调度
  - `A2AAdapter.handoff()` - Agent 间通信
  - `AgentTask`, `AgentContext`, `AgentResult` - Agent 类型

- **To Future Plans**：
  - Phase 03-02: Web API 将通过 `CollaborateEngine` 执行工作流
  - Phase 03-03: React 前端将触发工作流执行

## Self-Check: PASSED

- [x] All files exist at expected paths
- [x] All commits exist in git history
- [x] 430 tests pass (including 60 new tests)

---

*Completed: 2026-04-28*
*Duration: ~15 minutes*
