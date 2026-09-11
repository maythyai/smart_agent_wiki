---
id: PMS-agent-tools
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-09
status: built
roadmap_ref: ROADMAP
target_version: v1.22.0
prd_ref: docs/prd/PRD-agent-tools-v1.22.0.md
---

# PMS: agent-native tools — saw_resolve + saw_record (C1/C2, v1.22.0)

## 模块边界
两个 agent-native MCP 原语：改前任务级上下文召回（resolve）+ 持久学习/决策（record）。强化 SAW 作 agent 可信知识后端的定位。

## 对外接口
- `saw_resolve(task, limit=8) -> dict`：聚合 claims（confidence+score）+ code_symbols + freshness_warning
- `saw_record(summary, kind="decision", confidence="verified") -> dict`：经 Write Queue enqueue claim WriteOp；返回 recorded+op_id+claim_uuid
- `init_agent_tools(query_engine, code_graph_engine, write_queue)`

## 内部接口
- agent_tools.py（新模块），注册于 tools/__init__.py
- C1 用 `_query_engine._search` + `_claims_repo.get_by_id` + `handle_code_search`
- C2 用 `_write_queue.enqueue([WriteOp(sink_name="claims")])` + `Claim.compute_hash`

## 依赖
- saw.drivers.mcp.server.mcp（@mcp.tool）
- saw.write_queue.queue.WriteOp + sinks.claims_sink
- saw.domain.claims.Claim

## 状态
- built（v1.22.0）：2 工具 + 6 测试，gate 绿。
- 待补位：saw_resolve 语义检索升级；receipt 直签 wiring（经 dispatcher 自动 receipt）。
