---
phase: 03-01
plan: 01
subsystem: collaborate
tags: [agents, routing, a2a, protocol]
dependency_graph:
  requires: [Phase 02 LLM Router, Phase 02 Audit Layer]
  provides: [AgentProtocol, BaseAgent, AgentDispatcher, A2AAdapter]
  affects: [collaborate engine, future workflow orchestration]
tech_stack:
  added:
    - dataclasses for AgentTask, AgentContext, AgentResult
    - Protocol for AgentProtocol
    - Enum for ModelTier, MessageType
    - asyncio.Queue for A2A message handling
  patterns:
    - Protocol-based agent abstraction
    - Strategy pattern for model routing
    - Observer pattern for A2A broadcast
key_files:
  created:
    - src/saw/domain/agent.py
    - src/saw/engines/collaborate/agents/base.py
    - src/saw/engines/collaborate/agents/librarian.py
    - src/saw/engines/collaborate/agents/writer.py
    - src/saw/engines/collaborate/agents/critic.py
    - src/saw/engines/collaborate/agents/linker.py
    - src/saw/engines/collaborate/agents/scholar.py
    - src/saw/engines/collaborate/agents/guardian.py
    - src/saw/engines/collaborate/dispatcher.py
    - src/saw/engines/collaborate/a2a_protocol.py
  modified:
    - src/saw/domain/protocols.py
decisions:
  - D-01: 6 specialized agents with role-specific behavior
  - D-02: Agent role definition includes system_prompt, model_tier, tools_allowed
  - D-03: Guardian is pure rule engine, no LLM calls (zero cost)
  - D-04: Three-tier model routing (Haiku/Sonnet/Opus)
  - D-05: Routing based on task complexity
  - D-06: Runtime fallback when higher tiers unavailable
  - D-14: Guardian max 200 rules, default deny policy
  - D-15: A2A message format with trace_id and correlation_id
  - D-17: Handoff includes full context transfer
  - D-18: All A2A messages generate Ed25519 signature receipts
metrics:
  duration_minutes: 13
  test_count: 83
  test_pass_rate: 100
  files_created: 10
  files_modified: 1
  lines_added: 2164
  completed_date: "2026-04-28"
---

# Phase 03-01 Plan 01: Multi-Agent Foundation Summary

实现 Smart Agent Wiki 的多代理基础架构：Agent 协议、6 个专业化 Agent、模型路由器、A2A 协议。

## One-liner

实现了完整的 Agent 基础架构，包括 Protocol 定义、BaseAgent 基类、6 个专业化 Agent（Librarian/Writer/Critic/Linker/Scholar/Guardian）、AgentDispatcher 模型路由、A2A 协议消息传递，全部通过 83 个测试用例验证。

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | 定义 Agent 协议和基础类 | d24768e | protocols.py, agent.py, base.py, test_agent_definitions.py |
| 2 | 实现 6 个专业化 Agent | a433c05 | librarian.py, writer.py, critic.py, linker.py, scholar.py, guardian.py |
| 3 | 实现模型路由器 AgentDispatcher | b1dc32c | dispatcher.py, test_model_routing.py |
| 4 | 实现 A2A 协议 | 4fc1b09 | a2a_protocol.py, test_a2a_protocol.py |

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written.

## Key Implementation Details

### Agent Architecture

- **AgentProtocol**: Protocol 定义了 `name`, `model_tier`, `execute()` 三个核心接口
- **BaseAgent**: 提供 `_build_messages()` 构建消息列表，子类继承并实现 `execute()`
- **6 个专业化 Agent**:
  - Librarian (Haiku): 索引维护、元数据提取
  - Writer (Sonnet): Wiki 页面创作
  - Critic (Sonnet): 质量审核、置信度评估
  - Linker (Haiku): 交叉链接发现
  - Scholar (Opus): 深度推理、综述生成
  - Guardian (Rule): 零 LLM 安全检查

### Model Routing

- **ModelTier enum**: HAIKU, SONNET, OPUS, RULE
- **FALLBACK_ORDER**: Opus → Sonnet → Haiku
- **DispatcherConfig**: `allowed_fails=3` (per PITFALLS.md), `cooldown_time=120s`, `timeout=60s`

### A2A Protocol

- **MessageType**: REQUEST, RESPONSE, BROADCAST, QUERY, RESULT, HANDOFF
- **A2AMessage**: sender, receiver, action, payload, context, trace_id, correlation_id
- **A2AAdapter**: 支持 `send()`, `broadcast()`, `handoff()` 方法
- **版本协商**: 主版本号匹配才接受

## Threat Model Compliance

| Threat | Component | Status |
|--------|-----------|--------|
| T-03-01-01 | A2A messages | Ed25519 签名验证已实现 |
| T-03-01-02 | Agent context | AgentContext 使用 dataclass |
| T-03-01-03 | Agent actions | 审计收据在 A2AAdapter 中生成 |
| T-03-01-05 | Rate limits | allowed_fails=3 + cooldown_time=120s |
| T-03-01-06 | Agent tools | Guardian 在 execute 前检查 tools_allowed |

## Test Coverage

- **test_agent_definitions.py**: 44 tests (Protocol + Agent classes + BaseAgent)
- **test_model_routing.py**: 15 tests (ModelTier + AgentDispatcher + integration)
- **test_a2a_protocol.py**: 24 tests (MessageType + A2AMessage + A2AAdapter)

Total: **83 tests passing**

## Commits

```
4fc1b09 feat(03-01-01): implement A2A protocol for agent communication
b1dc32c feat(03-01-01): implement AgentDispatcher with model routing
a433c05 feat(03-01-01): implement 6 specialized agents
d24768e test(03-01-01): add failing tests for agent protocol and base types
```

## Duration

- Start: 2026-04-28T12:35:49Z
- End: 2026-04-28T12:48:39Z
- Duration: ~13 minutes
