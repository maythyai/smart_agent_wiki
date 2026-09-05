# ADR-012: Embedding Provider 选型 — litellm API 为主 + 本地 ST 可选 fallback

## 状态：Accepted

## 上下文

v1.10.0 引入 embedding 语义搜索，provider 走本地 `sentence-transformers`（`SentenceTransformer("all-MiniLM-L6-v2").encode()`，`embeddings.py:41-57`）。存在三个问题：

1. **重 SDK 打死 runner**：torch + transformers ~800MB 重依赖，CI/runner OOM/模型下载超时，7 个 importorskip 测试全 skip（retrospective-v1.10.0.md N1 High/P1）。
2. **非生产形态**：本地 torch CPU 前向推理非生产合理形态；项目 LLM 调用已用 litellm 做 OpenAI 风格 API（`router.py:16` `import litellm`，`router.py:98-110` `_completion_with_retry` 调 `litellm.completion`），embedding 走本地 ST 是范式不一致。
3. **E2E 未验证**：7 条 importorskip AC 在 CI 全 skip，真实语义检索路径未运行验证。

v1.12.0 用户决策 pivot：embedding 改用 OpenAI 风格 API（litellm），闭合 N1 + N4。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| `embed_texts()` 走本地 `SentenceTransformer("all-MiniLM-L6-v2").encode()` | `src/saw/adapters/embeddings.py:41,53,57` | `_get_model()` 加载 ST 模型（:41）；`embed_texts()` 调 `model.encode(texts, normalize_embeddings=True)`（:57）；返回 L2-normalized 向量或 None（:50） |
| litellm 已在核心依赖且已用于 LLM 调用 | `pyproject.toml:13` + `src/saw/adapters/llm/router.py:16,98,110` | `litellm>=1.83.13` 核心 dep；`router.py:16` `import litellm`；`router.py:98-110` `_completion_with_retry` 调 `litellm.completion(**kwargs)`。`litellm.embedding`/`aembedding` 同包可用 |
| `LLMSettings` 已有 `api_base`/`api_key`/`model` 配置范式 | `src/saw/config/settings.py:19-26` | `LLMSettings` 有 `extraction_model`/`query_model`/`api_key`/`api_base`/`timeout`/`enable_thinking`。embedding 配置可复用此范式 |
| `detect_tier()` FULL 检测本地 ST | `src/saw/config/settings.py:79,92-93,116-120` | `detect_tier()` 调 `_embeddings_available()`（:92-93）；`_embeddings_available()` 用 `importlib.import_module("sentence_transformers")`（:117-120）。须改：检测 API embedding 配置 |
| `_endpoint_kwargs` 范式处理 api_base/api_key 路由 | `src/saw/adapters/llm/router.py:187-194` | `_is_ollama_model()`（:187）+ `_endpoint_kwargs()`（:191-194）处理 `api_base`/`api_key` 路由。embedding API 调用可复用此范式 |
| `_MODEL_ENV_KEYS` 映射 model prefix → env var | `src/saw/adapters/llm/router.py:133` | `{"gpt":"OPENAI_API_KEY", ...}`。embedding model 同样可走 env var 范式 |
| `embeddings_available()` 检测 `sentence_transformers` | `src/saw/adapters/embeddings.py:19-29` | 全局缓存 `_ST_available`；`importlib.import_module("sentence_transformers")` |
| `embedding_store` 表已有 `dim` + `model` 列 | `src/saw/db/migrations.py:337-358` | v10 migration：`dim INTEGER NOT NULL`、`model TEXT NOT NULL`，PK (doc_id, workspace_id) |
| `rebuild_embeddings` 已有维度变更检测范式 | `src/saw/drivers/cli/commands/search_cmd.py:217-227` | `SELECT DISTINCT dim` 比对 `current_dim`，不匹配则 `DELETE FROM embedding_store` |
| `EmbeddingSink.write()` 硬编码 model 名 | `src/saw/write_queue/sinks/embedding_sink.py:73` | INSERT 时 `model` 列硬编码 `"all-MiniLM-L6-v2"` |
| `_semantic_search` 调 `embed_texts` + `embeddings_available` | `src/saw/engines/query/engine.py:461,474-477,498,505,520` | provider 换了接口不变 |
| `compute_related_pages` 有 embedding 信号（权重 2.5） | `src/saw/engines/query/related_pages.py:25,61-66,70,75,110-129,165-166` | provider 重构在 embed_texts 层，自动受益 |
| 7 个测试用 `importorskip("sentence_transformers")` | `tests/unit/test_embedding_index.py:6` / `tests/unit/test_semantic_search.py:6` / `tests/unit/test_related_pages_embedding.py:6` | 三文件首行 importorskip，CI 全 skip |
| `[learn]` extra 定义 `sentence-transformers>=2.2` | `pyproject.toml:64` | `learn = ["fsrs>=4.0", "sentence-transformers>=2.2"]` |

## 决策

选择候选 ①：**litellm.embedding API 为主 provider + 本地 ST 可选 fallback**。

- **主路径**：`embed_texts()` 调 `litellm.embedding(model=cfg.model, input=texts, api_base=cfg.api_base, api_key=cfg.api_key)` 获取向量。base_url/api_key/model 走 config，复用 `LLMSettings` 同套 env 范式（新增 `EmbeddingSettings` 专用配置项）。
- **Fallback**：`[learn]` extra 装了 ST 且 API 未配置时，走本地 `SentenceTransformer("all-MiniLM-L6-v2").encode()`（保留 v1.10.0 路径）。
- **降级**：两者都不可用 → `embed_texts()` 返回 None，调用方降级 BM25。
- **接口不变**：`embed_texts(texts) -> list[list[float]] | None` 签名保持，下游 `_semantic_search`/`EmbeddingSink.write`/`compute_related_pages` 无需改动。
- **模型选型 [TBD]**：默认 `text-embedding-3-small`（OpenAI，1536 维）或 config 驱动（用户可配任意 OpenAI 风格 embedding model）。

## 备选方案

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① litellm.embedding API 为主 + 本地 ST 可选 fallback（选） | 复用 LLM 同套 config/api_key 范式（`LLMSettings` + `_MODEL_ENV_KEYS` + `_endpoint_kwargs`）；无重 SDK（litellm 已核心依赖）；生产形态合理（API 弹性、可观测、无本地模型下载）；向后兼容 v1.10.0 用户（装了 ST 可用）；CI 用 API mock 测试不再 skip | API 调用有延迟（须 benchmark P99）；API key 配置门槛（复用 LLM env 范式可降低） | 生产部署 + CI 测试 + 向后兼容 ✓ |
| ② 纯本地 ST（v1.10.0 现状） | 零 API 延迟；离线可用；已实现 | 重 SDK（torch ~800MB）打死 runner；CI 7 测试 skip（E2E 未验证）；非生产形态；范式不一致（LLM 走 API 但 embedding 走本地） | 离线/内网-only 场景，但 v1.12.0 明确 pivot away |
| ③ 纯 API 无 fallback | 最简实现（无 ST 路径）；无重 SDK；生产形态 | 无离线 fallback（API 不可用时无 embedding）；v1.10.0 用户升级后装了 ST 也不可用（breaking） | 纯云原生、无离线需求场景 |

## 理由

1. **范式一致**（决策因子 40% 需求匹配）：项目 LLM 调用已用 litellm（`router.py:16` import litellm，`router.py:98-110` `litellm.completion`），embedding 走 `litellm.embedding` 是同包同范式，复用 `LLMSettings`/`_MODEL_ENV_KEYS`/`_endpoint_kwargs` 配置路由模式。
2. **轻量优于重量**（选型六原则②）：litellm 已在核心依赖（`pyproject.toml:13`），不引入新框架；去掉 torch 重 SDK 依赖（runner 稳定），CI 用 API mock 测试不再 importorskip skip。
3. **生产形态合理**：API 调用是生产 embedding 的合理形态——弹性、可观测、无本地模型下载/OOM 风险。
4. **向后兼容**：候选 ① 保留本地 ST fallback，v1.10.0 用户装了 `[learn]` extra 且无 API 配置时行为不变（走本地 ST），是 additive MINOR 而非 breaking。
5. **CI E2E 验证闭合**：7 个 importorskip 测试改 API mock 后全 pass（不再 skip），闭合 N1（High/P1）。
6. **候选 ② 淘汰理由**：重 SDK 打死 runner + 非生产形态 + CI 测试 skip（E2E 未验证）——v1.10.0 复盘 N1 明确标 High/P1。
7. **候选 ③ 淘汰理由**：无 fallback 对离线/内网场景不友好，且对已装 ST 的 v1.10.0 用户是 breaking（升级后 ST 不可用）。

## 后果

### 正面
- embedding 从"本地重 SDK、未验证"到"API 轻接入、E2E 实测通过"——去掉 torch 重依赖，CI 用 API mock 跑通全部 embedding 测试。
- 复用 LLM 同套 config/env 范式，用户已有 LLM 配置时零额外配置。
- 向后兼容 v1.10.0 用户（本地 ST fallback）。
- 生产部署不依赖本地 torch/模型下载。
- 闭合 N1（High/P1）+ N4（Medium/P2）。

### 负面
- API 调用有延迟（P99 [TBD]，须 benchmark）。
- API dim（如 1536）> 本地 384 → 存储开销增加 [TBD]（须磁盘测量）。
- API key 配置门槛（复用 LLM env 范式降低，用户已有 LLM 配置时零额外配置）。

### 风险
- API 限流/延迟影响检索体验 → 降级策略兜底（API 失败 → BM25），P99 benchmark 后定 baseline。
- 测试 mock 与真实 API 行为偏差 → mock 验证逻辑路径；真实 API key 可选 E2E benchmark 补充。
- 维度切换数据迁移 → `rebuild_embeddings` 已有 dim 变更检测 + wipe 重建范式（`search_cmd.py:217-227`），沿用。
- `embeddings_available()` 检测逻辑变更影响 `detect_tier` → 须确保 tier 判断与既有 LIGHTWEIGHT/FULL 语义一致（API 配置可用 OR 本地 ST 可 import → FULL）。

## 模型选型 [TBD]

- 默认 `text-embedding-3-small`（OpenAI，1536 维）或 config 驱动（用户可配任意 OpenAI 风格 embedding model）。
- dim 通过 `embed_texts(["dimension probe"])` 动态探测（返回向量长度即为 dim），`rebuild_embeddings` 既有范式沿用。
- 具体模型名/价格/限流策略归 05 实施后 benchmark 定 baseline [TBD]。

## 关联 Feature

F-Q-1（provider 重构）、F-Q-2（维度可配+重建检测）、F-Q-3（本地 ST fallback）、F-Q-4（测试改 API mock+benchmark）

## 关联 ADR

- ADR-010（embedding_store BLOB + numpy cosine 存储/检索策略，仍 Accepted，不变）——本 ADR 仅聚焦 provider 层，存储/检索策略不变。
- ADR-010 标 [TBD] 的缓存优化已由 v1.11.0 ADR-011（semantic search cache）解决，本 ADR-012 不重复。
