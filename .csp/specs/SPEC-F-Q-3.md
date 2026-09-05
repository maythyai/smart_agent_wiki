---
id: SPEC-F-Q-3
title: 本地 ST 可选 fallback（detect_tier 感知 API 配置为主、ST 为辅）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-embedding-api-v1.12.0.md
pms_ref: .csp/product-spec/PMS-embedding-api.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-Q-3
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
adr_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
ac_coverage: 2/2
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.12.0.md#T-F-Q-3
---

# SPEC-F-Q-3: 本地 ST 可选 fallback

## 实现 delta（ground 自源码）

> F-Q-1 provider 重构建立 API 主路径。本 Spec 扩展 fallback 路由：API 不可用但本地 ST 可用时走本地 ST（向后兼容 v1.10.0）。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `src/saw/adapters/embeddings.py:19-29` | `embeddings_available()` 仅检测 ST | `importlib.import_module("sentence_transformers")` | API 配置可用 OR 本地 ST 可 import（OR 逻辑，F-Q-1 建 API 检测，本 Spec 补 OR） |
| `src/saw/adapters/embeddings.py:41-57` | `embed_texts()` 仅走 ST | `SentenceTransformer("all-MiniLM-L6-v2").encode()` | provider 三级路由：API → ST → None（F-Q-1 建 API 路径，本 Spec 补 ST fallback 分支） |
| `src/saw/config/settings.py:116-120` | `_embeddings_available()` 仅检测 ST | `importlib.import_module("sentence_transformers")` | API 配置可用 OR 本地 ST 可 import（OR 逻辑） |

### 不改动

- `detect_tier()` 逻辑不变（:92-93 调 `_embeddings_available()`），仅改 `_embeddings_available()` 内部检测逻辑。
- `[learn]` extra 定义不变（`pyproject.toml:64` `learn = ["fsrs>=4.0", "sentence-transformers>=2.2"]`）。
- `_get_model()` / `_MODEL` 本地 ST 加载路径保留（作为 fallback）。
- `cluster_by_embedding()` 调 `embed_texts` 自动受益。
- `[learn]` extra 的其他用途（fsrs/trends/distiller 的 importorskip 先例不变）。

## 后端架构

### Provider 三级路由（`src/saw/adapters/embeddings.py`）

F-Q-1 建立了 `_api_embedding_available()` + `_embed_via_api()` + `_st_available()` + `_embed_via_st()` 的分层。本 Spec 确认 `embed_texts()` 的完整三级路由：

```python
def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts (L2-normalised).

    Provider priority: API (litellm.embedding) > local ST > None.
    Returns None if all providers fail — caller falls back to non-semantic.
    """
    if not texts:
        return None

    # 1. Try API (primary path, default for v1.12.0)
    if _api_embedding_available():
        vecs = _embed_via_api(texts)
        if vecs is not None:
            return vecs
        logger.warning("API embedding failed, trying local ST fallback")

    # 2. Try local ST fallback (v1.10.0 path, preserved for backward compat)
    if _st_available():
        logger.info("API unavailable, falling back to local ST")
        vecs = _embed_via_st(texts)
        if vecs is not None:
            return vecs

    # 3. All providers failed
    return None
```

**_st_available() 保留既有逻辑**（`embeddings.py:19-29` 改名后保留）：

```python
_ST_available: bool | None = None

def _st_available() -> bool:
    """True if sentence-transformers is importable (local ST fallback)."""
    global _ST_available
    if _ST_available is None:
        try:
            import sentence_transformers  # noqa: F401
            _ST_available = True
        except ImportError:
            _ST_available = False
    return _ST_available
```

**_embed_via_st() 保留既有逻辑**（`embeddings.py:41-57` 改名后保留）：

```python
_MODEL: Any = None

def _get_model():
    """Lazy-load + cache a small sentence-transformers model (fallback)."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL

def _embed_via_st(texts: list[str]) -> list[list[float]] | None:
    """Embed via local SentenceTransformer (fallback path)."""
    if not _st_available() or not texts:
        return None
    try:
        model = _get_model()
        vecs = model.encode(texts, normalize_embeddings=True)
        return [list(v) for v in vecs]
    except Exception as e:
        logger.warning("Local ST embedding failed: %s", e)
        return None
```

### embeddings_available() OR 逻辑

```python
def embeddings_available() -> bool:
    """True if any embedding provider is available (API OR local ST).

    Used by detect_tier() to set FULL tier.
    - API configured (EmbeddingSettings has model + api_key or api_base) → True
    - Local ST importable ([learn] extra installed) → True
    - Neither → False (tier=LIGHTWEIGHT, semantic endpoints degrade to BM25)
    """
    return _api_embedding_available() or _st_available()
```

### detect_tier() FULL 条件（`settings.py:79,92-93,116-120`）

```python
def _embeddings_available() -> bool:
    """Check if embeddings are available (API configured OR local ST importable).

    v1.12.0: API configuration is the primary path; local ST is optional fallback.
    """
    # API: check EmbeddingSettings configured
    if _api_embedding_configured():
        return True
    # Local ST: legacy check (v1.10.0 backward compat)
    try:
        import importlib
        importlib.import_module("sentence_transformers")
        return True
    except ImportError:
        return False
```

`detect_tier()` 逻辑不变（:92-93 `if _embeddings_available(): tier = CapabilityTier.FULL`），仅 `_embeddings_available()` 内部检测逻辑改为 OR。

### Provider 路由优先级表

| API 配置 | 本地 ST | provider 选择 | tier | semantic_fallback |
|---|---|---|---|---|
| 可用 | 已装 | 走 API（默认优先） | FULL | false |
| 可用 | 未装 | 走 API | FULL | false |
| 不可用 | 已装 | 走本地 ST fallback | FULL | false |
| 不可用 | 未装 | 无 provider → None → BM25 | LIGHTWEIGHT | true |

## API 契约

无新 REST 端点（fallback 路由在 adapter 层，既有端点行为不变）。

### CLI（既有，行为不变）

```
saw search "concept" --mode semantic    # provider 路由自动选择 API/ST/降级
saw ingest                               # EmbeddingSink 调 embed_texts 自动路由
saw links suggest                        # compute_related_pages 自动路由
```

## 降级策略

| 场景 | 处理 | 用户提示 |
|---|---|---|
| API 可用 + ST 已装 | 走 API（默认优先） | 无 |
| API 不可用 + ST 已装 | 走本地 ST fallback | 日志 info "API unavailable, falling back to local ST" |
| API 可用 + ST 未装 | 走 API | 无（默认形态） |
| API 不可用 + ST 未装 | 返回 None，降级 BM25 | tier=LIGHTWEIGHT，`semantic_fallback: true` |
| API 调用失败 + ST 已装 | API try/except → 走 ST fallback | 日志 warning + info |
| API 调用失败 + ST 未装 | API try/except → None → BM25 | 日志 warning |

## 安全考量

- 本地 ST fallback 不涉及 API key，无额外安全面。
- `embeddings_available()` OR 逻辑与 `detect_tier` FULL 条件对称（API OR ST → FULL）。
- 向后兼容 v1.10.0：装了 ST 且无 API 配置时行为不变（走本地 ST，FULL tier）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-FB-1（本地 ST fallback） | `tests/unit/test_semantic_search.py`（改）：mock `embeddings_available()=True`（ST 路径）+ API 不可用 → semantic search 返回结果 + `semantic_fallback: false` + 日志提示 "API unavailable, falling back to local ST" | ST fallback 路径 + 不降级 BM25 |
| AC-FB-2（无 ST 走 API） | `tests/unit/test_semantic_search.py`（改）：mock `litellm.embedding` 返回固定向量 + `_st_available()=False` → semantic search 返回结果 + `semantic_fallback: false` + 无需本地 ST | API 路径 + 无 ST |

## 实现就绪度

- [x] provider 三级路由设计完整（API → ST → None）
- [x] `_st_available()` / `_get_model()` / `_embed_via_st()` 保留既有逻辑（`embeddings.py:19-29,41-57`）
- [x] `embeddings_available()` OR 逻辑与 `detect_tier` FULL 条件对称
- [x] 向后兼容 v1.10.0（装了 ST 且无 API 配置 → 走本地 ST，行为不变）
- [x] `[learn]` extra 其他用途不变（fsrs/trends/distiller importorskip 先例）
- [x] AC 覆盖 2/2
