---
id: SPEC-F-Q-2
title: 维度可配 + embedding_store dim 列驱动 + 索引重建检测维度变更
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-embedding-api-v1.12.0.md
pms_ref: .csp/product-spec/PMS-embedding-api.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-Q-2
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
adr_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
ac_coverage: 2/2
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.12.0.md#T-F-Q-2
---

# SPEC-F-Q-2: 维度可配 + dim 驱动 + 重建检测

## 实现 delta（ground 自源码）

> F-Q-1 provider 重构后，API embedding 模型 dim（如 1536）≠ 本地 ST 的 384。本 Spec 聚焦 dim 驱动 + 重建检测 + model 列动态化。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `src/saw/write_queue/sinks/embedding_sink.py:73` | `model` 列硬编码 `"all-MiniLM-L6-v2"` | INSERT 时 `model` 列值 = 当前配置的 embedding model 名（动态） | 从 `EmbeddingSettings.model` 或 `_get_model()` 获取当前 model 名 |
| `src/saw/drivers/cli/commands/search_cmd.py:217-227` | `rebuild_embeddings` 维度变更检测 probe dim | `embed_texts(["dimension probe"])` 获取 dim（已有范式） | 适配 API provider——probe dim 调 `embed_texts` 自动走 API/ST，返回向量长度即为 dim |
| `src/saw/drivers/cli/commands/search_cmd.py:249` | `_upsert_embedding` 硬编码 model 名 | `INSERT ... VALUES (?, ?, 'all-MiniLM-L6-v2', ...)` | `INSERT ... VALUES (?, ?, ?, ...)` model 列动态传参 |

### 不改动

- `embedding_store` 表结构不变（已有 `dim` + `model` 列，`migrations.py:337-358` v10 migration，无需新 migration）。
- `rebuild_embeddings` 维度变更检测逻辑不变（`SELECT DISTINCT dim` 比对 `current_dim`，不匹配则 `DELETE FROM embedding_store`，`search_cmd.py:217-227` 既有范式沿用）。
- `struct.pack`/`struct.unpack` 序列化范式不变（`<{dim}f` float32 数组）。

## 数据库 Schema（DDL 级）

> `embedding_store` 表结构不变（v10 migration，`migrations.py:337-358`）。

```sql
-- 既有表（不变）
CREATE TABLE IF NOT EXISTS embedding_store (
    doc_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    model TEXT NOT NULL,           -- 改为动态值（当前配置的 API model 名）
    vector BLOB NOT NULL,
    dim INTEGER NOT NULL,          -- 改为 API model dim（如 1536）
    workspace_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (doc_id, workspace_id)
);
```

**dim 驱动说明**：
- v1.10.0：`dim=384`（`all-MiniLM-L6-v2`）。
- v1.12.0 API：`dim=1536`（`text-embedding-3-small`，[TBD]——取决于配置的 model）。
- `dim` 列值由 `embed_texts()` 返回的向量长度决定——`len(vec)` 即为 dim，`EmbeddingSink.write()` 和 `_upsert_embedding` 既有范式 `dim = len(vec)` 不变。

## 后端架构

### EmbeddingSink.write() model 列动态化（`src/saw/write_queue/sinks/embedding_sink.py:73`）

```python
# 既有（:73）：
#   (doc_id, entity_type, "all-MiniLM-L6-v2", blob, dim, workspace_id)
# 改为：
from saw.adapters.embeddings import _get_embedding_settings

def _current_model_name() -> str:
    """Get current embedding model name for model column."""
    cfg = _get_embedding_settings()
    if cfg is not None and cfg.model:
        return cfg.model
    # Local ST fallback
    return "all-MiniLM-L6-v2"

# In write():
model_name = _current_model_name()
self._conn.execute(
    """INSERT INTO embedding_store
       (doc_id, entity_type, model, vector, dim, workspace_id)
       VALUES (?, ?, ?, ?, ?, ?)""",
    (doc_id, entity_type, model_name, blob, dim, workspace_id),
)
```

### rebuild_embeddings 维度检测适配（`src/saw/drivers/cli/commands/search_cmd.py:217-227`）

既有范式沿用，provider 重构后 `embed_texts(["dimension probe"])` 自动走 API/ST：

```python
# 既有（:217-227），无需改逻辑，provider 换了 embed_texts 自动走新路径：
old_dim_row = conn.execute(
    "SELECT DISTINCT dim FROM embedding_store LIMIT 1"
).fetchone()
probe = embed_texts(["dimension probe"])
current_dim = len(probe[0]) if probe else 384  # fallback dim
if old_dim_row is not None and old_dim_row[0] != current_dim:
    console.print(
        f"[yellow]Dimension changed ({old_dim_row[0]} → {current_dim}), "
        "wiping old vectors.[/yellow]"
    )
    conn.execute("DELETE FROM embedding_store")
    conn.commit()
```

### _upsert_embedding model 列动态化（`search_cmd.py:249`）

```python
# 既有（:249）：
#   (doc_id, entity_type, "all-MiniLM-L6-v2", blob, dim, workspace_id)
# 改为：
from saw.adapters.embeddings import _get_embedding_settings

def _current_model_name() -> str:
    """Get current embedding model name."""
    cfg = _get_embedding_settings()
    if cfg is not None and cfg.model:
        return cfg.model
    return "all-MiniLM-L6-v2"

def _upsert_embedding(conn, doc_id, entity_type, vec, workspace_id):
    dim = len(vec)
    blob = struct.pack(f"<{dim}f", *vec)
    model_name = _current_model_name()
    conn.execute(
        "DELETE FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
        (doc_id, workspace_id),
    )
    conn.execute(
        """INSERT INTO embedding_store
           (doc_id, entity_type, model, vector, dim, workspace_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (doc_id, entity_type, model_name, blob, dim, workspace_id),
    )
```

## API 契约

无新 REST 端点。

### CLI（既有，行为不变）

```
saw rebuild-embeddings --path DIR    # 维度检测 + 全量重建，provider 换了自动走 API
saw ingest                           # EmbeddingSink.write model 列动态化
```

## 降级策略

| 条件 | 行为 | 用户提示 |
|---|---|---|
| dim 变更（384 → 1536） | `SELECT DISTINCT dim` 不匹配 → `DELETE FROM embedding_store` → 全量重建 | "Dimension changed (384 → 1536), wiping old vectors." |
| rebuild 时 API 调用失败（chunk 级） | 跳过该 chunk，继续其他 chunk | "Embedding failed for a chunk, skipping." |
| rebuild 时 API 完全不可用 | 提示配置 API，exit 0 | "Embeddings unavailable. Configure embedding API in config." |
| ingest 时 EmbeddingSink.write API 失败 | `embed_texts()` 返回 None → skip 该 doc，warning 日志，不中断 ingest | 日志 warning |

## 安全考量

- `embedding_store` PK (doc_id, workspace_id) 既有，workspace 隔离不变。
- `rebuild_embeddings` `WHERE deleted_at IS NULL` 过滤已删除 claim，不变。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-DIM-1（维度变更触发重建） | `tests/unit/test_embedding_index.py`（改）：mock `litellm.embedding` 返回 1536 维向量 → seed 旧 dim=384 向量 → rebuild → 检测 dim 不匹配 → wipe 旧向量 → 新向量 dim=1536 + model=mock model 名 | dim 变更检测 + wipe + 重建 + model 列动态 |
| AC-DIM-2（ingest 写入正确 model） | `tests/unit/test_embedding_index.py`（改）：mock `litellm.embedding` → EmbeddingSink.write → `SELECT model FROM embedding_store` = mock model 名（非 `all-MiniLM-L6-v2`） | model 列动态值 |

## 实现就绪度

- [x] `embedding_store` 表已有 `dim` + `model` 列（`migrations.py:337-358` v10，无需新 migration）
- [x] `rebuild_embeddings` 维度变更检测范式已有（`search_cmd.py:217-227`），provider 换了自动走新路径
- [x] `_upsert_embedding` model 列动态化改动点明确（`search_cmd.py:249`）
- [x] `EmbeddingSink.write` model 列动态化改动点明确（`embedding_sink.py:73`）
- [x] AC 覆盖 2/2
- [ ] 全量重建延迟 [TBD]（取决于 claim/wiki 总量 × API embedding 单次延迟）
- [ ] 向量索引存储开销 [TBD]（API dim 如 1536 > 本地 384，须磁盘测量）
