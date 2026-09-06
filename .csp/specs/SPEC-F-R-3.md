---
id: SPEC-F-R-3
title: REST /workflows 字段别名 + CHANGELOG.md
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-e2e-tail-v1.13.0.md
pms_ref: .csp/product-spec/PMS-e2e-tail.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-R-3
complexity: S
tdd_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
ac_coverage: 3/3
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.13.0.md#T-F-R-3
---

# SPEC-F-R-3: REST /workflows 字段别名 + CHANGELOG.md

## 实现 delta（ground 自源码）

> ADR-013 关联：O3 闭合——v1.11.0 REST 行为变更无 CHANGELOG + 无兼容别名。本 Spec 加别名 + 建 CHANGELOG。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `src/saw/api/routes/collaborate.py:373` | durable item dict：`"definition_name": name` | 加 `"name": name`（别名，同值）+ `"workflow": name`（别名，兼容 POST） |
| `src/saw/api/routes/collaborate.py:401` | live item dict：`"definition_name": wf.get("workflow", "unknown")` | 加 `"name": ...` + `"workflow": ...`（同值别名） |
| `CHANGELOG.md`（项目根） | 不存在 | 新建，Keep a Changelog 约定，回溯 v1.10.0–v1.13.0 关键行为变更 |

### 不改动

- `list_workflows()` 既有逻辑不变（读 `workflow_executions` 表 merge `_workflows` in-memory，`collaborate.py:328-411`）。
- 既有字段（`definition_name`/`status`/`steps_completed`/`steps_total`/`updated_at`/`finished_at`）值不变。
- `definition_name` 仍是主字段（别名是镜像值，未来 deprecated 时再移除）。
- DB schema 不变（`workflow_executions` 表，`definition_name` 列不变）。
- POST `/workflows` 响应不变。

## 后端架构

### list_workflows 响应加别名（`src/saw/api/routes/collaborate.py`）

durable item（`:373`）：
```python
items.append({
    "workflow_id": wid,
    "definition_name": name,
    "name": name,            # alias (compat, = definition_name)
    "workflow": name,        # alias (compat with POST response field)
    "status": st,
    "steps_completed": sc,
    "steps_total": tot,
    "updated_at": updated,
    "finished_at": finished,
})
```

live item（`:401`）：
```python
items.append({
    "workflow_id": wid,
    "definition_name": wf.get("workflow", "unknown"),
    "name": wf.get("workflow", "unknown"),      # alias
    "workflow": wf.get("workflow", "unknown"),  # alias
    "status": "running",
    "steps_completed": wf.get("current_step", 0),
    "steps_total": wf.get("steps_total", 0),
    "updated_at": wf.get("started_at"),
    "finished_at": None,
})
```

**别名语义**：`name`/`workflow` 均等于 `definition_name`（同值镜像）。`name` 兼容老消费者（v1.10.0 前 `name` 字段）；`workflow` 兼容 POST `/workflows` 响应字段名。

### CHANGELOG.md（项目根，新建）

遵循 Keep a Changelog 约定（语义化版本 + 日期 + 变更类型 Added/Changed/Fixed/Deprecated）。回溯 v1.10.0–v1.13.0 关键行为变更：

```markdown
# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] / v1.13.0] - 2026-09-06
### Fixed
- `saw ingest <dir>` now recursively ingests all supported files in a
  directory instead of erroring with "Is a directory" (Bug A).
### Added
- `scripts/benchmark_semantic.py`: real vLLM embedding benchmark
  (semantic vs BM25 recall + P99 + cache hit rate).
- REST `GET /api/v1/workflows` response items now include `name` and
  `workflow` alias fields (= `definition_name`) for backward compatibility.
### Changed
- Coverage gate `fail_under` raised from 65 to 67.

## [v1.12.0] - 2026-09-05
### Changed
- Embedding provider pivoted from local sentence-transformers to OpenAI-style
  API (litellm.embedding via httpx direct to vLLM). Local ST is now optional
  fallback only. Provider is API-only by default (commit 84e1776 removed ST
  fallback path).
### Added
- `EmbeddingSettings` (model/api_key/api_base/timeout) reusing LLMSettings
  env-var pattern.
### Fixed
- Embedding tests no longer `importorskip` sentence-transformers — all run
  via mock litellm.embedding (7 tests moved from skip to pass).

## [v1.11.0] - 2026-09-04
### Changed
- REST `GET /api/v1/workflows` now reads durable `workflow_executions` table
  and merges live in-memory workflows (previously in-memory only).
- Response field renamed from `name` to `definition_name` (aligns with DB
  column). `name` alias added for backward compatibility (see v1.13.0).
### Added
- Semantic search query cache (mode="semantic" key isolation, TTL 300s).
- `compile/compiler.py` deep coverage (20 test cases, 30+ functions).

## [v1.10.0] - 2026-09-03
### Added
- Embedding semantic search (embedding_store table + numpy cosine, parallel
  `--mode semantic` not fused with BM25).
- Smart linking suggest (3-signal + embedding similarity).
```

## API 契约

### GET /api/v1/workflows（响应加别名）

响应体每个 item 新增 `name` + `workflow` 别名字段（= `definition_name` 镜像值），既有字段不变：

```json
{
  "workflows": [
    {
      "workflow_id": "uuid",
      "definition_name": "knowledge_review",
      "name": "knowledge_review",
      "workflow": "knowledge_review",
      "status": "completed",
      "steps_completed": 4,
      "steps_total": 4,
      "updated_at": "2026-09-06T...",
      "finished_at": "2026-09-06T..."
    }
  ],
  "total": 1
}
```

## 安全考量

- 别名不暴露额外数据（= `definition_name` 同值镜像，不引入新字段语义）。
- CHANGELOG 不含敏感信息（API key/内部路径）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-C-1（别名兼容） | `tests/unit/test_workflow_rest_db.py`（扩）：`GET /workflows` 返回非空 → 每个 item 含 `name` 且 == `definition_name` + 含 `workflow` 且 == `definition_name` | `item["name"] == item["definition_name"]` + `item["workflow"] == item["definition_name"]` |
| AC-C-2（CHANGELOG 存在） | `tests/unit/test_changelog.py`（新建）：读项目根 `CHANGELOG.md` → 文件存在 + 含 v1.11.0 `/workflows` 行为变更条目 | 文件存在 + "v1.11.0" + "workflows" + "definition_name" |
| AC-C-3（CHANGELOG 回溯） | `tests/unit/test_changelog.py`（扩）：读 `CHANGELOG.md` → 含 v1.12.0 embedding pivot 条目 + v1.13.0 本轮条目 | 含 "v1.12.0" + "embedding" + "v1.13.0" + "ingest" |

## 实现就绪度

- [x] 改动点明确（collaborate.py:373,401 加别名 + CHANGELOG.md 新建）
- [x] 别名语义明确（= definition_name 镜像，主字段不变）
- [x] CHANGELOG 回溯范围定（v1.10.0–v1.13.0，至少 v1.11.0 + v1.12.0 + v1.13.0）
- [x] 既有字段值不变（definition_name/status/steps_*/updated_at/finished_at）
- [x] AC 覆盖 3/3
