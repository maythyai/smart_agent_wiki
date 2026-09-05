# Release Notes — v1.12.0: embedding 改用 OpenAI 风格 API + E2E 验证

**Tag**: v1.12.0
**Date**: 2026-09-05
**Internal milestone**: v4.2
**Commits**: f4f4869, f4e9f04, 4818926, 65f036f, 6c07c89, 50fc8e8
**Bump type**: MINOR (additive — provider refactor + E2E mock + benchmark, no breaking API changes)

## Summary

把 embedding provider 从本地 `SentenceTransformer` 重构为 litellm OpenAI 风格 embedding API（`litellm.embedding`），去掉本地 torch 重依赖。E2E 用 API mock 验证（不再 importorskip、不再打死 runner）。闭合 v1.10.0 N1（embedding E2E 未验证）+ N4（benchmark）。

## Changed

- **F-Q-1: provider 重构** — `embeddings.py::embed_texts()` 从本地 `SentenceTransformer` 改为 `litellm.embedding()` API（base_url/api_key/model 走 config，复用 LLM 同套 env 范式）。本地 ST 降级为可选 fallback（`[learn]` extra 仍可装，但默认走 API）。
- **F-Q-2: 维度可配** — embedding 维度可配置（API 模型 dim 如 1536 ≠ 本地 384），`EmbeddingSettings` 加入 settings.py，`embedding_store` dim 列驱动，索引重建检测维度变更。
- **F-Q-3: ST fallback** — `detect_tier()._embeddings_available()` 检查 API config OR 本地 ST；`EmbeddingSink.write()` + `_upsert_embedding()` 使用动态 model name（`_current_model_name()`）。
- **F-Q-4: 测试改 API mock** — 3 个测试文件移除 `importorskip("sentence_transformers")`，改 mock litellm.embedding。新增 `test_embedding_benchmark.py`（semantic vs BM25 recall + P99 latency）。`tests/conftest.py` 设 `LITELLM_LOCAL_MODEL_COST_MAP=True`（跳过远程 fetch）。

## ADR

- ADR-012: embedding provider litellm API 为主 + 本地 ST 可选 fallback，复用 LLMSettings/_MODEL_ENV_KEYS/_endpoint_kwargs 范式，3 候选对比。

## Quality Gates

| Gate | Result |
|---|---|
| pytest | 2076 passed, 3 skipped, 0 failed (108.92s) |
| ruff check src/ tests/ | 0 errors |
| coverage | 66% (TOTAL 29284 10092, ≥65 ✓) |
| saw smoke | 6/6 passed |
| wheel build | smart_agent_wiki-1.12.0-py3-none-any.whl |

## Notes

- 3 skipped = 1 fsrs importorskip [learn] extra + 2 pre-existing。Zero embedding importorskip skips — all embedding tests now run via mock litellm.embedding。
- **无本地 torch 加载**（runner 稳定）。embedding 测试全 pass（API mock，不 skip）。
- 不要求本地 sentence-transformers（API 为默认路径）。
- pyproject.toml version 1.11.0 → 1.12.0。

## 07 回流

- N1（embedding E2E）✓ — 改用 API mock，CI 可跑
- N4（benchmark）✓ — `test_embedding_benchmark.py` 新增
- 续留：N3（per-request ws）/ M2（agent 活动聚合）/ L2（链接自动 apply）/ O1-O4
