---
id: SPEC-F-W-1
title: per-request workspace 注入（FastAPI middleware contextvar 注入 + QueryEngine fallback 读取）
version: 1.0
status: Approved
author: tech-designer
date: "2026-09-07"
prd_ref: docs/prd/PRD-per-request-ws-v1.18.0.md
pms_ref: .csp/product-spec/PMS-per-request-ws.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-W-1
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-018-contextvar-per-request-workspace.md
adr_ref: .csp/tech-decisions/ADR/ADR-018-contextvar-per-request-workspace.md
ac_coverage: 5/5
related_tasks: [.csp/tasks/TASKS-DELTA-v1.18.0.md]
---

# SPEC-F-W-1: per-request workspace 注入

> ADR-018 决策一：FastAPI middleware + QueryEngine contextvar fallback 读取（additive，不改 QueryEngine 公开构造签名）。
> 复杂度 M → 标准 8 维度。ground 自 CMS + 源码。

## 维度 1：UI/UX 规格

无前端变更。本 Feature 为后端 middleware + engine 内部读取改造。

## 维度 2：数据库 Schema

无 schema 变更。workspace_id 已在 claims/graph/embedding_store 表中存在（ADR-007, migration v8/v9）。contextvar 注入不引入新表/列。

## 维度 3：API 契约

### 端点变更

无新端点。现有 REST routes 自动按 contextvar 中 workspace_id 隔离（middleware 层透明注入）。

### Header 规范

| Header | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| `X-Workspace-Id` | string | 否 | `^[a-zA-Z0-9_-]{1,64}$` | 请求级 workspace scope。未提供时 fallback default `"default"` |

### Query Parameter（备选）

| 参数 | 类型 | 必填 | 校验规则 | 说明 |
|---|---|---|---|---|
| `workspace_id` | string | 否 | `^[a-zA-Z0-9_-]{1,64}$` | 同 header，优先级低于 header |

### 错误响应

| 状态码 | 场景 | 响应体 |
|---|---|---|
| 400 | workspace_id 校验失败（非法字符/超长） | `{"error": {"code": "INVALID_WORKSPACE_ID", "message": "workspace_id must be alphanumeric, hyphen or underscore, max 64 chars"}}` |

### 向后兼容

- 未提供 workspace_id 时 contextvar 保持 default `"default"`——行为与 v1.17.0 一致。
- 现有 API 调用方无需修改。

## 维度 4：后端架构

### 新增模块

```
src/saw/drivers/web/middleware/
└── workspace.py    # 新增：workspace_id_var + WorkspaceContextMiddleware
```

### workspace.py 实现规格

```python
"""Per-request workspace contextvar injection (ADR-018)."""
from __future__ import annotations

import contextvars
import logging
import re
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Per-request workspace scope, inheritable by asyncio tasks and threads
# spawned via asyncio.to_thread (Python 3.9+).
workspace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "saw_workspace_id", default="default"
)

# Validation: alphanumeric + hyphen + underscore, 1-64 chars.
_WORKSPACE_RE = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')


class WorkspaceContextMiddleware(BaseHTTPMiddleware):
    """Extract workspace_id from request, set contextvar, reset on exit."""

    HEADER = "X-Workspace-Id"
    PARAM = "workspace_id"

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Extract: header > query param > default
        ws_id = request.headers.get(self.HEADER)
        if ws_id is None:
            ws_id = request.query_params.get(self.PARAM)
        if ws_id is None:
            # No workspace specified — keep default, no contextvar set
            return await call_next(request)

        # Validate
        if not _WORKSPACE_RE.match(ws_id):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "INVALID_WORKSPACE_ID",
                        "message": "workspace_id must be alphanumeric, hyphen or underscore, max 64 chars",
                    }
                },
            )

        # Set contextvar for request duration
        token = workspace_id_var.set(ws_id)
        try:
            response = await call_next(request)
        finally:
            workspace_id_var.reset(token)

        # Echo workspace_id on response (observability)
        response.headers[self.HEADER] = ws_id
        return response
```

### QueryEngine 改造（engine.py）

```python
# 新增 helper（在 QueryEngine class 内）
def _effective_workspace_id(self) -> str:
    """Return per-request workspace_id from contextvar, fallback to self._workspace_id.

    additive (ADR-018): QueryEngine.__init__ signature unchanged.
    contextvar takes priority when set by WorkspaceContextMiddleware;
    falls back to the constructor-injected default for CLI/non-web paths.
    """
    from saw.drivers.web.middleware.workspace import workspace_id_var
    return workspace_id_var.get(self._workspace_id)
```

**改动点**（ground 自源码 engine.py）：

| 位置 | 现状 | 改为 |
|---|---|---|
| `engine.py:234`（cache key） | `"workspace_id": self._workspace_id` | `"workspace_id": self._effective_workspace_id()` |
| `engine.py:295`（claims_repo.get_by_id） | `workspace_id=self._workspace_id` | `workspace_id=self._effective_workspace_id()` |
| `engine.py:528`（embedding_store query） | `WHERE workspace_id = ?` + `(self._workspace_id,)` | `WHERE workspace_id = ?` + `(self._effective_workspace_id(),)` |
| 其他 `self._workspace_id` 读取点 | 直读 | 改为 `self._effective_workspace_id()` |

**不改**：
- `engine.py:59`：`workspace_id: str = "default"` 参数保留（构造签名不变）。
- `engine.py:87`：`self._workspace_id = workspace_id` 赋值保留（作为 fallback default）。
- `engine.py:92-95`：`for _sub in ... _setter(workspace_id)` 保留（子服务构造时注入 default）。

### 子服务改造（TreeModeSearch / ContextCompiler / GraphTraverse）

每个子服务新增相同 helper：

```python
def _effective_workspace_id(self) -> str:
    """contextvar fallback (ADR-018)."""
    from saw.drivers.web.middleware.workspace import workspace_id_var
    return workspace_id_var.get(self._workspace_id)
```

子服务内所有 `self._workspace_id` 读取改为 `self._effective_workspace_id()`。保留 `set_workspace_id()` setter（既有 API 不删）。

### Middleware 注册（app.py create_app 函数）

在 `RequestContextMiddleware` 之后注册 `WorkspaceContextMiddleware`：

```python
# ADR-018: per-request workspace contextvar injection
from saw.drivers.web.middleware.workspace import WorkspaceContextMiddleware
app.add_middleware(WorkspaceContextMiddleware)
```

注册顺序（middleware 后注册先执行，先执行 = 外层）：
1. CORSMiddleware
2. SecurityHeadersMiddleware
3. RequestContextMiddleware（设 request_id_var）
4. **WorkspaceContextMiddleware**（设 workspace_id_var，在 RequestContextMiddleware 之后注册 = 在 request_id 之后设）
5. AuditLogMiddleware
6. InputSanitizerMiddleware
7. RateLimitMiddleware

### JSON 日志增强（observability.py JsonFormatter）

在 `JsonFormatter.format` 的 payload 中新增 `workspace_id` 字段：

```python
payload = {
    "ts": ...,
    "level": ...,
    "logger": ...,
    "msg": ...,
    "request_id": getattr(record, "request_id", "-"),
    "workspace_id": workspace_id_var.get(),  # 新增
}
```

### ThreadPoolExecutor 传播（collaborate.py）

`collaborate.py:35` 的 `_query_executor = ThreadPoolExecutor(max_workers=1)` 中 contextvar 默认不传播。

**解决方案**：`loop.run_in_executor(_query_executor, lambda: query.query(...))` 改为 `asyncio.to_thread(query.query, ...)`。

Python 3.9+ `asyncio.to_thread` 内部使用 `contextvars.copy_context().run(fn)`，自动传播当前 coroutine 的 contextvars 到新线程。

若必须保持 executor 模式（如需要 max_workers=1 限制并发），则改为：

```python
import contextvars
ctx = contextvars.copy_context()
result = await loop.run_in_executor(
    _query_executor, lambda: ctx.run(query.query, question, mode="search")
)
```

## 维度 5：前端架构

无前端变更。

## 维度 6：基础设施需求

### 环境变量

无新环境变量。workspace_id 通过 HTTP header 注入，非环境变量。

### 服务依赖

无新服务依赖。

### 配置

无新配置项。workspace_id 校验规则（`^[a-zA-Z0-9_-]{1,64}$`）硬编码在 middleware 中。

## 维度 7：测试策略 + TMS

### 测试用例表

| AC | 用例 | 类型 | 断言 |
|---|---|---|---|
| AC-WS-1 | `test_workspace_contextvar.py::test_middleware_sets_contextvar`（新建）：FastAPI TestClient + WorkspaceContextMiddleware + X-Workspace-Id header → 断言 QueryEngine._effective_workspace_id() == "team-a" | integration | contextvar set 生效 |
| AC-WS-2 | `test_workspace_contextvar.py::test_middleware_default_fallback`（新建）：TestClient 不带 header → 断言 QueryEngine._effective_workspace_id() == "default" | integration | fallback 默认值 |
| AC-WS-3 | `test_workspace_isolation.py::test_cross_workspace_no_leak`（新建）：2 workspace（team-a + team-b）各写入 claim → workspace A 请求搜索结果 → 断言不含 workspace B claim | integration（mock DB） | 跨 workspace 零泄漏 |
| AC-WS-4 | `test_workspace_cli_compat.py::test_cli_unchanged`（新建）：CLI 模式下 QueryEngine.query → 断言使用 default workspace（contextvar 保持 default） | unit | CLI 行为不变 |
| AC-WS-5 | `test_workspace_signature.py::test_queryengine_init_signature`（新建）：`inspect.signature(QueryEngine.__init__)` → 断言参数列表含 `workspace_id: str = "default"`（与 v1.17.0 一致） | unit（inspect） | 构造签名不变 |

### 补充测试

| 场景 | 用例 | 类型 | 断言 |
|---|---|---|---|
| workspace_id 非法字符 | `test_workspace_validation.py::test_invalid_chars_400` | unit | 400 INVALID_WORKSPACE_ID |
| workspace_id 超长 | `test_workspace_validation.py::test_too_long_400` | unit | 400 INVALID_WORKSPACE_ID |
| workspace_id 合法边界 | `test_workspace_validation.py::test_valid_64_chars` | unit | 200 + contextvar set |
| middleware reset（finally） | `test_workspace_contextvar.py::test_reset_after_request` | integration | 请求后 contextvar 回到 default |
| asyncio.to_thread 传播 | `test_workspace_thread_propagation.py::test_contextvar_in_thread` | unit | to_thread 内 contextvar.get() == 设入值 |

### CI 兼容

全部 pytest 运行，无外部依赖。CI 始终跑。

## 维度 8：安全考量

### 输入校验

- workspace_id 校验 `^[a-zA-Z0-9_-]{1,64}$`——阻止路径注入（如 `../` 或 SQL 注入字符）。
- workspace_id 在 SQL query 中作为参数化绑定（`WHERE workspace_id = ?`），非字符串拼接。

### 多租户隔离

- workspace_id contextvar per-request 隔离——请求 A 的 workspace_id 不泄漏到请求 B。
- middleware finally 块强制 reset——防止 contextvar 跨请求残留。
- cache key 含 workspace_id（engine.py:234 既有）——cache 自然按 workspace 隔离。

### 审计

- JSON 日志 payload 新增 `workspace_id` 字段——可追溯每请求的 workspace scope。
- Response header 回显 `X-Workspace-Id`——客户端可确认请求被路由到正确 workspace。

## 实现就绪度

- [x] middleware 实现规格完整（workspace.py 伪代码）
- [x] QueryEngine 改造点明确（engine.py 4+ 位置 self._workspace_id → _effective_workspace_id()）
- [x] **QueryEngine 公开构造签名不变（additive，engine.py:59 workspace_id: str = "default" 保留）**
- [x] 子服务改造点明确（3 子服务各加 _effective_workspace_id() helper）
- [x] middleware 注册顺序明确（app.py create_app 函数 RequestContextMiddleware 之后）
- [x] ThreadPoolExecutor 传播方案明确（asyncio.to_thread 或 copy_context）
- [x] AC 覆盖 5/5
- [ ] 05 实施后测试通过
