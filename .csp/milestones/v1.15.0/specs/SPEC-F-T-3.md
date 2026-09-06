---
id: SPEC-F-T-3
title: M2 agent 活动聚合（event bus 订阅 WorkflowStep + GET /api/v1/agents/{name}/activity 端点）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-agent-link-v1.15.0.md
pms_ref: .csp/product-spec/PMS-agent-link.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-T-3
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md
adr_ref: .csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md
ac_coverage: 4/4
related_tasks: [.csp/tasks/TASKS-DELTA-v1.15.0.md#T-F-T-3]
---

# SPEC-F-T-3: M2 agent 活动聚合

## 实现 delta（ground 自源码）

> ADR-015 决策二：event_bus subscriber 写内存计数器。
> 复用既有 `InMemoryEventBus.add_subscriber`（`event_bus.py:71`）+ `WorkflowExecutor._execute_step` 发布 WorkflowStep 事件（`workflow_executor.py:389`）。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `src/saw/engines/collaborate/`（新增 `activity_tracker.py`） | 无活动聚合器 | 新增 `AgentActivityTracker` 类：`add_subscriber("WorkflowStep", handler)` 订阅 + 内存计数器 |
| `src/saw/api/routes/collaborate.py` L426 `list_agents()` | 返回静态 roster（name/model_tier/tools_allowed/rule） | 扩展返回 `activity_summary` 字段（calls + last_active_at），无活动时 `null` |
| `src/saw/api/routes/collaborate.py` | 无 `GET /agents/{name}/activity` 端点 | 新增 `GET /api/v1/agents/{name}/activity` 端点 |
| `src/saw/drivers/web/app.py`（lifespan/startup） | 无 tracker 初始化 | 启动时初始化 `AgentActivityTracker` + 绑定到 `app.state.activity_tracker` |

### 不改动

- `src/saw/plugins/event_bus.py`——`InMemoryEventBus.add_subscriber` 已实现（`event_bus.py:71`），`_dispatch` 有 try/except 不传播异常（`event_bus.py:63`），零改动复用。
- `src/saw/engines/collaborate/workflow_executor.py`——`_execute_step` 已发布 WorkflowStep 事件（`workflow_executor.py:389`），含 `step`（`{agent}.{action}`）和 `status`（`completed`/`failed`），零改动复用。
- `workflow_executions` 表——无 schema 变更（PRD 明确不持久化，活动聚合为内存态）。

## 后端架构

### `AgentActivityTracker` 类（新增 `src/saw/engines/collaborate/activity_tracker.py`）

```python
"""Agent activity aggregation via event bus subscription.

ADR-015 决策二: event_bus subscriber writes in-memory counters.
Handler runs on publisher thread (sync), _dispatch has try/except —
lightweight O(1) dict update, no lock needed (single-thread).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AgentActivityTracker:
    """Aggregate agent activity by subscribing to WorkflowStep events.

    In-memory only — process restart loses all data (PRD §3.3 rule 6).
    Handler is lightweight (dict counter update), does not block workflow.
    """

    def __init__(self) -> None:
        self._activities: dict[str, dict[str, Any]] = {}

    def subscribe(self, event_bus: Any) -> None:
        """Register as subscriber for WorkflowStep events."""
        event_bus.add_subscriber("WorkflowStep", self._handle_event)

    def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle WorkflowStep event — update agent activity counters.

        Event format (from workflow_executor.py:389):
        {"type":"WorkflowStep","workflow_id":...,"step":"{agent}.{action}","status":"completed"|"failed","output_key":...}
        """
        try:
            step_str = event.get("step", "")
            if "." not in step_str:
                return
            agent_name = step_str.split(".", 1)[0]
            action = step_str.split(".", 1)[1]
            status = event.get("status", "completed")

            now = datetime.now(timezone.utc).isoformat()

            if agent_name not in self._activities:
                self._activities[agent_name] = {
                    "calls": 0,
                    "failures": 0,
                    "last_action": None,
                    "last_active_at": None,
                }

            activity = self._activities[agent_name]
            if status == "completed":
                activity["calls"] += 1
            elif status == "failed":
                activity["failures"] += 1

            activity["last_action"] = action
            activity["last_active_at"] = now
        except Exception:
            # Handler must never raise — _dispatch already has try/except,
            # but double-guard for safety.
            logger.warning("Activity tracker handler error", exc_info=True)

    def get_activity(self, agent_name: str) -> dict[str, Any]:
        """Get activity aggregation for a specific agent.

        Returns empty activity (calls=0) if agent has no activity.
        """
        if agent_name not in self._activities:
            return {
                "agent": agent_name,
                "calls": 0,
                "failures": 0,
                "last_action": None,
                "last_active_at": None,
            }
        activity = self._activities[agent_name]
        return {
            "agent": agent_name,
            "calls": activity["calls"],
            "failures": activity["failures"],
            "last_action": activity["last_action"],
            "last_active_at": activity["last_active_at"],
        }

    def get_summary(self, agent_name: str) -> dict[str, Any] | None:
        """Get compact activity summary for roster (calls + last_active_at).

        Returns None if agent has no activity.
        """
        if agent_name not in self._activities:
            return None
        activity = self._activities[agent_name]
        return {
            "calls": activity["calls"],
            "last_active_at": activity["last_active_at"],
        }
```

### REST `GET /api/v1/agents/{name}/activity`（新增端点）

```python
@router.get("/agents/{agent_name}/activity")
async def get_agent_activity(agent_name: str) -> dict[str, Any]:
    """Get agent activity aggregation (AC-C-1..3).

    Returns calls/failures/last_action/last_active_at.
    Agent not in roster → 404. No activity → 200 + empty (calls=0).
    """
    from saw.engines.collaborate.agents import build_agent_roster

    roster = build_agent_roster(llm_router=None)
    if agent_name not in roster:
        raise HTTPException(404, f"Agent '{agent_name}' not found in roster")

    # Get tracker from app state (initialized in lifespan)
    # Fallback: return empty activity if tracker not initialized
    tracker = getattr(getattr(_router, "app", None), "state", None)
    # In practice, tracker is passed via dependency injection or app.state
    from saw.drivers.web.app import get_activity_tracker
    tracker = get_activity_tracker()
    if tracker is None:
        return {
            "agent": agent_name,
            "calls": 0,
            "failures": 0,
            "last_action": None,
            "last_active_at": None,
        }

    return tracker.get_activity(agent_name)
```

### REST `list_agents()` 扩展（`collaborate.py` L426）

```python
@router.get("/agents")
async def list_agents() -> dict[str, Any]:
    """List the agent roster with activity_summary (AC-C-4)."""
    from saw.engines.collaborate.agents import build_agent_roster
    from saw.drivers.web.app import get_activity_tracker

    BUILTIN_NAMES = {"Librarian", "Writer", "Critic", "Linker", "Scholar", "Guardian"}
    roster = build_agent_roster(llm_router=None)
    tracker = get_activity_tracker()

    agents = []
    for name in sorted(roster):
        a = roster[name]
        activity_summary = None
        if tracker is not None:
            activity_summary = tracker.get_summary(name)

        agents.append({
            "name": a.name,
            "model_tier": a.model_tier,
            "tools_allowed": list(getattr(a, "_tools_allowed", []) or []),
            "rule": a.model_tier == "rule",
            "custom": name not in BUILTIN_NAMES,
            "activity_summary": activity_summary,
        })
    return {"agents": agents, "total": len(agents)}
```

### `app.py` lifespan 初始化

```python
# In lifespan/startup:
from saw.engines.collaborate.activity_tracker import AgentActivityTracker

activity_tracker = AgentActivityTracker()
event_bus = getattr(app.state, "event_bus", None)
if event_bus is not None:
    activity_tracker.subscribe(event_bus)
app.state.activity_tracker = activity_tracker

# Helper for route access:
def get_activity_tracker():
    # Module-level singleton, set in lifespan
    return _activity_tracker_instance
```

### CLI `saw agents activity`

```python
# In agents_cmd.py (CLI):
@app.command(name="activity")
def activity(
    name: str = typer.Argument(..., help="Agent name"),
    path: str = typer.Option(".", "--path", "-p", help="Wiki directory path"),
) -> None:
    """Show agent activity aggregation (AC-C-1..3)."""
    # CLI connects to REST or reads in-memory tracker
    # For local mode: tracker is initialized at startup
    console.print(f"Agent: {name}")
    console.print(f"  Calls: {activity['calls']}")
    console.print(f"  Failures: {activity['failures']}")
    console.print(f"  Last action: {activity['last_action']}")
    console.print(f"  Last active: {activity['last_active_at']}")
```

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| agent name 不存在于 roster | 返回 404 | HTTP 404 `"Agent '{name}' not found in roster"` |
| agent 存在但无活动记录 | 返回 200 + 空活动 | `{ "agent": "Guardian", "calls": 0, "failures": 0, "last_action": null, "last_active_at": null }` |
| event bus handler 抛异常 | bus 已有 try/except 不传播 | 日志 `"Event handler raised for 'WorkflowStep'"` |
| tracker 未初始化（app.state 无 tracker） | 返回空活动（calls=0） | 不报错，正常降级 |

## 数据库 Schema

无 schema 变更。活动聚合为内存态（`dict[str, dict]`），不持久化到 DB（PRD §3.3 业务规则 6 明确"活动聚合为内存态，进程重启后丢失，不持久化"）。

## API 契约

### `GET /api/v1/agents/{name}/activity`（新增端点）

**响应 200**（有活动）：
```json
{
  "agent": "Scholar",
  "calls": 3,
  "failures": 0,
  "last_action": "synthesize",
  "last_active_at": "2026-09-06T12:34:56+00:00"
}
```

**响应 200**（无活动）：
```json
{
  "agent": "Guardian",
  "calls": 0,
  "failures": 0,
  "last_action": null,
  "last_active_at": null
}
```

**响应 404**（agent 不存在）：
```json
{
  "detail": "Agent 'NonExistent' not found in roster"
}
```

### `GET /api/v1/agents`（扩展 `activity_summary`）

```json
{
  "agents": [
    {
      "name": "Librarian",
      "model_tier": "sonnet",
      "tools_allowed": ["search", "read"],
      "rule": false,
      "custom": false,
      "activity_summary": {
        "calls": 5,
        "last_active_at": "2026-09-06T12:34:56+00:00"
      }
    },
    {
      "name": "Guardian",
      "model_tier": "rule",
      "tools_allowed": [],
      "rule": true,
      "custom": false,
      "activity_summary": null
    }
  ],
  "total": 6
}
```

## 测试策略（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-C-1 | `tests/unit/test_agent_activity.py`（新建）：创建 `AgentActivityTracker` → 模拟发布 WorkflowStep 事件 `{"step":"Scholar.synthesize","status":"completed"}` → `tracker.get_activity("Scholar")` | `calls >= 1`，`last_action == "synthesize"`，`last_active_at` 非空 |
| AC-C-2 | `test_agent_activity.py`：`tracker.get_activity("Guardian")`（从未发布 Guardian 事件） | `calls == 0`，`last_active_at == None` |
| AC-C-3 | `tests/unit/test_agents_rest.py`（扩）：`GET /api/v1/agents/NonExistent/activity` | 返回 404 `"Agent not found"` |
| AC-C-4 | `test_agents_rest.py`：发布 3 次 Scholar 事件 → `GET /api/v1/agents` → Scholar 行含 `activity_summary: {calls: 3, ...}` | `activity_summary["calls"] == 3`，`last_active_at` 非空 |

**CI 兼容**：全部用 mock event（直接调用 `tracker._handle_event(event)` 或 mock event_bus），不依赖真实 workflow 执行。REST 测试用 `TestClient` + mock `get_activity_tracker()`。无 LLM 调用。

## 安全考量

- 活动数据不含 PII（仅 agent name + action + 时间戳，非用户数据）。
- agent name 来自 workflow YAML + 内置角色名，无用户输入注入风险。
- 活动聚合为内存态，进程重启自动清零（无持久化泄露风险）。
- handler 异常不传播（`_dispatch` try/except + handler 内部 try/except 双重防护）。

## 实现就绪度

- [x] `AgentActivityTracker` 类伪代码完整（subscribe + _handle_event + get_activity + get_summary）
- [x] handler 数据结构明确（dict[str, dict[str, Any]]，无锁安全）
- [x] `GET /api/v1/agents/{name}/activity` 端点定义（200/404 响应）
- [x] `GET /api/v1/agents` 扩展 `activity_summary` 字段
- [x] CLI `saw agents activity` 命令
- [x] 异常处理覆盖（agent 不存在/无活动/handler 异常/tracker 未初始化）
- [x] AC 覆盖 4/4
- [ ] 05 实施后 CI 验证 `GET /api/v1/agents/{name}/activity` 返回正确聚合
