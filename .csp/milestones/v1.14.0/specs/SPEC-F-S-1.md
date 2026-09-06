---
id: SPEC-F-S-1
title: semantic cache 阈值可配（env 驱动启用/禁用 + 触发阈值）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-semantic-perf-v1.14.0.md
pms_ref: .csp/product-spec/PMS-semantic-perf.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-S-1
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
adr_ref: .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
ac_coverage: 5/5
related_tasks: [".csp/tasks/TASKS-DELTA-v1.14.0.md (T-F-S-1)"]
---

# SPEC-F-S-1: semantic cache 阈值可配

## 实现 delta（ground 自源码）

> ADR-014 决策"不实现 localhost 自适应"：cache 行为由 env 显式控制，不隐式推断。
> ADR-011（Accepted）semantic cache 范式不变：`get_cache()` 单例 + `mode="semantic"` key 隔离 + TTL 300s。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `src/saw/engines/query/engine.py` `_semantic_search` 方法 | `_cache.get(question, _cache_params)` / `_cache.set(question, _cache_params, _qr)` 无条件执行——无 env 判断 | cache.get/set 路径增加 `SAW_SEMANTIC_CACHE_ENABLED` 条件分支：`false` → 跳过 cache.get/set，直接 embedding + cosine/ANN；`true`（默认）→ 走既有 cache 路径 |
| `src/saw/engines/query/engine.py` `_semantic_search` 方法 | cache.set 无条件执行 | 增加 `SAW_SEMANTIC_CACHE_THRESHOLD_MS` 条件：API 响应延迟 < 阈值时跳过 cache.set（cache.get 仍可命中已有缓存） |
| `src/saw/config/settings.py` `EmbeddingSettings` | 无 cache 配置项 | 新增 `semantic_cache_enabled` / `semantic_cache_threshold_ms` 配置项读取（env 驱动，复用 `os.environ.get` 范式） |

### 不改动

- `src/saw/engines/query/cache.py`——纯 LRU+TTL cache，配置控制在调用方（engine.py），cache.py 不改动。
- `_keyword_search` 的 cache 路径（`mode="search"`）——两个 cache 路径独立控制，keyword cache 不受 `SAW_SEMANTIC_CACHE_*` 影响。
- `QueryResult` 返回值结构——cache 行为变更仅影响内部 cache 命中/写入路径，返回值不变。
- `cache.stats()` 接口——既有 `{"hits", "misses", "size", "max_size", "hit_rate_percent"}` 不变。

## 后端架构

### 配置项（`src/saw/config/settings.py`）

```python
def _semantic_cache_enabled() -> bool:
    """True if semantic cache is enabled (default: true).

    Reads SAW_SEMANTIC_CACHE_ENABLED env var.
    - "false" → False (disable cache)
    - "true"/unset/invalid → True (enable cache, default)
    """
    import os
    val = os.environ.get("SAW_SEMANTIC_CACHE_ENABLED", "true").lower()
    if val == "false":
        return False
    if val not in ("true", ""):
        logger.warning(
            "Invalid SAW_SEMANTIC_CACHE_ENABLED=%r, defaulting to true", val
        )
    return True


def _semantic_cache_threshold_ms() -> int:
    """Cache write threshold in milliseconds (default: 0 = no threshold).

    Reads SAW_SEMANTIC_CACHE_THRESHOLD_MS env var.
    When > 0, cache.set is skipped if embedding API response latency
    is below this threshold (cache.get still executes).
    """
    import os
    try:
        return int(os.environ.get("SAW_SEMANTIC_CACHE_THRESHOLD_MS", "0"))
    except ValueError:
        logger.warning(
            "Invalid SAW_SEMANTIC_CACHE_THRESHOLD_MS, defaulting to 0"
        )
        return 0
```

### cache 路径条件分支（`engine.py` `_semantic_search`）

```python
# 伪代码（改动在 _semantic_search cache.get/set 两处）

from saw.config.settings import _semantic_cache_enabled, _semantic_cache_threshold_ms

_cache_enabled = _semantic_cache_enabled()
_threshold_ms = _semantic_cache_threshold_ms()

# cache.get（条件执行）
if _cache_enabled:
    _cached = _cache.get(question, _cache_params)
    if _cached is not None:
        return _cached

# ... embedding + cosine/ANN 检索 ...

# cache.set（条件执行）
if _cache_enabled and _threshold_ms == 0:
    _cache.set(question, _cache_params, _qr)
elif _cache_enabled and _threshold_ms > 0:
    # 仅当 API 响应延迟 >= 阈值时写入
    _api_latency_ms = _measure_api_latency()  # embedding 调用耗时
    if _api_latency_ms >= _threshold_ms:
        _cache.set(question, _cache_params, _qr)
# else: cache 禁用 → 不 set
```

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| `SAW_SEMANTIC_CACHE_ENABLED` 值非法（非 true/false） | 忽略，回退默认（enabled=true） | 日志 warning |
| `SAW_SEMANTIC_CACHE_THRESHOLD_MS` 值非法（非整数） | 忽略，回退默认（0=不设阈值） | 日志 warning |
| cache 配置读取异常 | 不阻断查询，回退默认行为（enabled=true） | 日志 warning |
| cache.get/set 异常 | 不阻断查询（既有 try/except pattern） | 日志 warning |

## 数据库 Schema

无 schema 变更。cache 是内存 LRU+TTL（`QueryCache` 单例），不持久化到 DB。

## API 契约

无 API 变更。`QueryEngine._semantic_search` 是内部方法，返回 `QueryResult` 不变。

## 测试策略（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-A-1（cache 禁用） | `tests/unit/test_semantic_cache_config.py`（新建）：设 `SAW_SEMANTIC_CACHE_ENABLED=false`，连续两次相同 semantic 查询 → `cache.stats().hits` 不增加 | hits_before == hits_after |
| AC-A-2（cache 启用默认） | `test_semantic_cache_config.py`：无 env 或 `SAW_SEMANTIC_CACHE_ENABLED=true`，连续两次相同查询 → 第 2 次 `cache.stats().hits` 增加 | hits_after_2nd > hits_after_1st |
| AC-A-3（阈值跳过写入） | `test_semantic_cache_config.py`：设 `SAW_SEMANTIC_CACHE_THRESHOLD_MS=100`，mock embedding API 响应 < 100ms → cache.set 被跳过（新查询不写入），但 cache.get 仍可命中已有缓存 | 第 1 次 miss + cache 无新增 entry；已有缓存仍可命中 |
| AC-A-4（向后兼容） | `test_semantic_cache_config.py`：无任何 `SAW_SEMANTIC_CACHE_*` env → 行为与 v1.13.0 一致（cache 始终启用，cache.get/set 正常执行） | hits 正常增加，与不设 env 前一致 |
| AC-A-5（keyword cache 不受影响） | `test_semantic_cache_config.py`：设 `SAW_SEMANTIC_CACHE_ENABLED=false`，连续两次相同 keyword 查询 → keyword cache 正常命中（`mode=search` 路径不受影响） | keyword cache hits 正常增加 |

**CI 兼容**：全部用 mock embedding（不依赖 vLLM），CI 始终跑，不 skip。

## 安全考量

- 无新增安全面。env 配置复用既有 `os.environ.get` 范式（同 `EmbeddingSettings`）。
- cache 禁用不影响 workspace_id 隔离（key 仍含 `workspace_id`，禁用时仅跳过 get/set）。

## 实现就绪度

- [x] 改动点明确（engine.py cache 路径条件分支 + settings.py 新增配置项 + cache.py 不改）
- [x] 配置项语义明确（`SAW_SEMANTIC_CACHE_ENABLED` + `SAW_SEMANTIC_CACHE_THRESHOLD_MS`）
- [x] 默认行为不变（向后兼容 AC-A-4）
- [x] keyword cache 独立控制（AC-A-5）
- [x] 异常处理覆盖（非法值 + 读取异常 → 回退默认）
- [x] AC 覆盖 5/5
- [x] 不实现 localhost 自适应（ADR-014 决策）
- [ ] `SAW_SEMANTIC_CACHE_THRESHOLD_MS` 实际效果须 05 实施 benchmark 验证
