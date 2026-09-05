---
id: SPEC-F-Q-1
title: embed_texts provider 重构为 litellm OpenAI 风格 API
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-embedding-api-v1.12.0.md
pms_ref: .csp/product-spec/PMS-embedding-api.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-Q-1
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
adr_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
ac_coverage: 2/2
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.12.0.md#T-F-Q-1
---

# SPEC-F-Q-1: embed_texts provider 重构为 litellm API

## 实现 delta（ground 自源码）

> ADR-012 候选 ①：litellm.embedding API 为主 + 本地 ST 可选 fallback（F-Q-3 扩展 fallback 分支）。本 Spec 聚焦 provider 重构本身。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `src/saw/adapters/embeddings.py:19-29` | `embeddings_available()` 检测 `sentence_transformers` | `importlib.import_module("sentence_transformers")` | 检测 embedding API 配置可用（有 model + 有 api_key 或 api_base）OR 本地 ST 可 import（F-Q-3 扩展 OR 逻辑） |
| `src/saw/adapters/embeddings.py:41-57` | `embed_texts()` 调 `_get_model().encode()` | `SentenceTransformer("all-MiniLM-L6-v2").encode(texts, normalize_embeddings=True)` | 调 `litellm.embedding(model=cfg.model, input=texts, api_base=cfg.api_base, api_key=cfg.api_key)`；API 不可用 + ST 可用时走 `_get_model().encode()` fallback |
| `src/saw/config/settings.py:19-26` | `LLMSettings` 有 `api_base`/`api_key`/`model` | 无 embedding 配置项 | 新增 `EmbeddingSettings`（`model`/`api_key`/`api_base`/`timeout`），复用 `LLMSettings` 范式 |
| `src/saw/config/settings.py:79,92-93,116-120` | `detect_tier()` FULL 检测本地 ST | `_embeddings_available()` 用 `importlib.import_module("sentence_transformers")` | `_embeddings_available()` 改为检测 API 配置可用 OR 本地 ST 可 import |

### 不改动

- `embed_texts(texts) -> list[list[float]] | None` 签名不变（下游 `_semantic_search`/`EmbeddingSink.write`/`compute_related_pages` 无需改动）。
- `cosine_similarity()` 不变。
- `cluster_by_embedding()` 调 `embed_texts` 自动受益。
- `embedding_store` 表结构不变（已有 `dim` + `model` 列）。
- `EmbeddingSink.write()` 硬编码 model 名改动态化归 F-Q-2。

## 后端架构

### EmbeddingSettings（`src/saw/config/settings.py`，新增）

复用 `LLMSettings` 范式（`settings.py:19-26`），新增 embedding 专用配置：

```python
class EmbeddingSettings(BaseModel):
    """Embedding configuration (OpenAI-style API via litellm).

    Reuses the same env-var / config pattern as LLMSettings:
    - model: embedding model name (e.g. "text-embedding-3-small")
    - api_key: API key (or env var EMBEDDING_API_KEY / OPENAI_API_KEY)
    - api_base: custom endpoint (Ollama/vLLM/etc.)
    - timeout: per-call timeout in seconds
    """
    model: str = ""
    api_key: str = ""
    api_base: str = ""
    timeout: int = 60
```

**config.yaml 示例**（复用既有 LLM config 范式）：
```yaml
llm:
  extraction_model: "gpt-4o-mini"
  api_key: "..."
  api_base: ""
embedding:
  model: "text-embedding-3-small"
  api_key: ""          # 空时 fallback 到 OPENAI_API_KEY env
  api_base: ""         # 空时用 litellm 默认 endpoint
  timeout: 60
```

**env var 范式**（复用 `router.py:133` `_MODEL_ENV_KEYS`）：
- `OPENAI_API_KEY` → gpt/openai prefix 模型
- `EMBEDDING_API_KEY` → embedding 专用 key（可选，优先于 OPENAI_API_KEY）
- `api_base` 配置时跳过 env var 检测（同 `router.py:191-194` `_endpoint_kwargs` 范式）

### embed_texts() 重构（`src/saw/adapters/embeddings.py`）

```python
import litellm

_embedding_settings: "EmbeddingSettings | None" = None

def _get_embedding_settings() -> "EmbeddingSettings | None":
    """Lazy-load embedding settings from config."""
    global _embedding_settings
    if _embedding_settings is None:
        try:
            from saw.config.settings import EmbeddingSettings
            # Try loading from config file or env
            # ... (same pattern as LLMRouter.__init__)
        except Exception:
            return None
    return _embedding_settings

def _api_embedding_available() -> bool:
    """True if embedding API is configured (model + api_key or api_base)."""
    cfg = _get_embedding_settings()
    if cfg is None:
        return False
    if not cfg.model:
        return False
    # api_base configured → assume reachable (same as router.py _check_available)
    if cfg.api_base:
        return True
    # Check env var (reuse _MODEL_ENV_KEYS pattern)
    if cfg.api_key:
        return True
    # Fallback to env var
    import os
    env_var = _required_embedding_env_var(cfg.model)
    if env_var and os.environ.get(env_var):
        return True
    return False

def _embed_via_api(texts: list[str]) -> list[list[float]] | None:
    """Embed texts via litellm.embedding API."""
    cfg = _get_embedding_settings()
    if cfg is None:
        return None
    try:
        kwargs: dict = {
            "model": cfg.model,
            "input": texts,
            "timeout": cfg.timeout,
        }
        if cfg.api_base:
            kwargs["api_base"] = cfg.api_base
        if cfg.api_key:
            kwargs["api_key"] = cfg.api_key
        response = litellm.embedding(**kwargs)
        # litellm embedding response: response.data[i].embedding
        vecs = [item["embedding"] for item in response.data]
        # L2-normalize (same as SentenceTransformer normalize_embeddings=True)
        return [_normalize(v) for v in vecs]
    except Exception as e:
        logger.warning("API embedding failed, falling back: %s", e)
        return None

def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts (L2-normalised).

    Provider priority: API (litellm.embedding) > local ST > None.
    Returns None if all providers fail — caller falls back to non-semantic.
    """
    if not texts:
        return None
    # 1. Try API
    if _api_embedding_available():
        vecs = _embed_via_api(texts)
        if vecs is not None:
            return vecs
        logger.warning("API embedding failed, trying local ST fallback")
    # 2. Try local ST fallback (F-Q-3)
    if _st_available():
        vecs = _embed_via_st(texts)
        if vecs is not None:
            return vecs
    # 3. All providers failed
    return None
```

**litellm.embedding 返回格式**（ground 自 `litellm` 文档 + `router.py:98-110` 同包调用范式）：
- `litellm.embedding(model=..., input=[...])` 返回 `ModelResponse`，`.data` 是 list of `{"embedding": [...], "index": i}`。
- 与 `litellm.completion` 同包同调用范式（`router.py:98-110` `_completion_with_retry` 调 `litellm.completion(**kwargs)`），embedding 照此调 `litellm.embedding(**kwargs)`。
- 异常处理同 `router.py:98-110` try/except 范式。

### embeddings_available() 重构

```python
def embeddings_available() -> bool:
    """True if any embedding provider is available (API OR local ST)."""
    return _api_embedding_available() or _st_available()
```

### detect_tier() 适配（`src/saw/config/settings.py:79,92-93,116-120`）

```python
def _embeddings_available() -> bool:
    """Check if embeddings are available (API configured OR local ST importable)."""
    # API: check EmbeddingSettings configured
    if _api_embedding_configured():
        return True
    # Local ST: legacy check
    try:
        import importlib
        importlib.import_module("sentence_transformers")
        return True
    except ImportError:
        return False
```

`detect_tier()` 逻辑不变（:92-93 调 `_embeddings_available()`），仅改 `_embeddings_available()` 内部检测逻辑。

### _normalize() 辅助

API embedding 返回的向量不保证 L2-normalized（与 `SentenceTransformer.encode(normalize_embeddings=True)` 不同），须显式 normalize：

```python
def _normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector (same as SentenceTransformer normalize_embeddings=True)."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]
```

## API 契约

无新 REST 端点（provider 重构在 adapter 层，既有端点行为不变）。

### CLI（既有，行为不变）

```
saw search "concept" --mode semantic     # provider 换，行为不变
saw ingest                                # EmbeddingSink 调 embed_texts 自动受益
saw links suggest                         # compute_related_pages 调 embed_texts 自动受益
```

## 降级策略

| 条件 | 行为 | meta |
|---|---|---|
| API 配置可用 + 调用成功 | 走 API，返回向量 | `semantic_fallback: false` |
| API 配置可用 + 调用失败（网络/限流/超时） | try/except → 走 ST fallback（如可用）→ 否则 None → BM25 | `semantic_fallback: true` |
| API 未配置 + ST 可用（[learn] 已装） | 走本地 ST fallback | `semantic_fallback: false` |
| API 未配置 + ST 未装 | `embeddings_available()` False → tier=LIGHTWEIGHT → BM25 | `semantic_fallback: true` |
| API 返回空向量/维度异常 | try/except → None → BM25 | `semantic_fallback: true` |

## 安全考量

- API key 走 config/env（复用 `LLMSettings` 同套 env 范式），不硬编码。
- `EmbeddingSettings.api_key` 从 config.yaml 或 `EMBEDDING_API_KEY`/`OPENAI_API_KEY` env 读取。
- `api_base` 配置时跳过 env var 检测（同 `router.py:191-194` `_endpoint_kwargs` 范式）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-EA-1（API 配置可用时语义检索） | `tests/unit/test_embedding_index.py`（改）：mock `litellm.embedding` 返回固定 1536 维向量 → EmbeddingSink.write → `SELECT FROM embedding_store` 有行 + dim=1536 + model=mock model 名 | 向量可查 + dim 正确 + model 列动态 |
| AC-EA-2（API 未配置时降级） | `tests/unit/test_embedding_degradation.py`（扩）：mock `embeddings_available()=False` → semantic search → `semantic_fallback: true` + BM25 回退 | 不报错 + BM25 回退 |

## 实现就绪度

- [x] `litellm.embedding` 调用范式可参照 `router.py:98-110` `_completion_with_retry`（同包同调用模式）
- [x] `EmbeddingSettings` 可参照 `LLMSettings`（`settings.py:19-26`）
- [x] `_MODEL_ENV_KEYS` env var 范式可参照 `router.py:133`
- [x] `_endpoint_kwargs` api_base/api_key 路由范式可参照 `router.py:187-194`
- [x] `embed_texts()` 签名不变，下游无需改动
- [x] 降级策略完备（API 失败 → ST fallback → None → BM25）
- [x] AC 覆盖 2/2
- [ ] API P99 延迟 [TBD]（05 实施后 benchmark）
- [ ] 具体模型名 [TBD]（默认 `text-embedding-3-small` 或 config 驱动）
