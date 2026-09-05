# PMS-embedding-api — 产品模块说明书

> **边界（一句话）**：embedding provider 从本地 sentence-transformers 重构为 litellm OpenAI 风格 API + 维度可配 + 本地 ST 可选 fallback + 测试改 API mock。

| 字段 | 值 |
|---|---|
| slug | embedding-api |
| 边界 | embedding provider 重构为 litellm API（替代本地 ST）+ 维度可配 + 重建检测 + 本地 ST 可选 fallback + 测试改 API mock + benchmark |
| 优先级 | P0 |
| 关联 PRD | PRD-embedding-api-v1.12.0 §2 |
| 关联 Spec | SPEC-F-Q-1, SPEC-F-Q-2, SPEC-F-Q-3, SPEC-F-Q-4 |
| 关联 ADR | ADR-012 (embedding provider API + ST fallback) |
| 关联 TMS | TMS-DELTA-v1.12.0 |
| 状态 | ready |
| file | PMS-embedding-api.md |

## 模块范围

- **provider 重构**：`embeddings.py::embed_texts()` provider 从本地 `SentenceTransformer` 重构为 litellm OpenAI 风格 embedding API（`litellm.embedding`/`aembedding`）。base_url/api_key/model 走 config（复用 `LLMSettings` 范式）。`embeddings_available()` 检测逻辑改为检测 API 配置可用。
- **维度可配 + 重建检测**：API 模型 dim（如 1536）≠ 本地 384；`embedding_store` 已有 `dim`+`model` 列；`rebuild_embeddings` 维度变更检测范式沿用；`EmbeddingSink.write()` model 列从硬编码改为动态。
- **本地 ST 可选 fallback**：`[learn]` extra 装了可走本地 ST（优先级低于 API）；不装走 API（默认）。provider 优先级：API > 本地 ST > 降级 BM25。
- **测试改 API mock**：7 个 importorskip 测试改 API mock（不 skip、CI 可跑）；4 个降级测试扩展 mock 目标；新增 benchmark（semantic vs BM25 召回 + P99）。

## 不包含

- litellm embedding API 具体调用参数/模型名选型（03 技术方案 ADR）。
- 向量数据库选型/部署（沿用 v1.10.0 本地 SQLite BLOB + numpy cosine，不变）。
- per-request workspace 注入（N3/K2，续留 v2.0 候选）。
- realtime 仪表盘 / desktop（defer）。
- agent "最近活动"聚合（M2，续留）。
- 链接自动 apply（L2，续留）。

## 降级策略

- API 配置可用 → 走 litellm API（默认路径，无需本地 ST）。
- API 不可用但 `[learn]` 已装（本地 ST 可 import）→ 走本地 ST fallback。
- 两者都不可用 → `embed_texts()` 返回 None，语义检索降级到 BM25（`semantic_fallback: true`），不报错不中断。
- `detect_tier()` FULL 条件：API 配置可用 OR 本地 ST 可 import。

## 关联

- PRD: `docs/prd/PRD-embedding-api-v1.12.0.md`
- 前身 PRD: `docs/prd/PRD-embedding-v1.10.0.md`（v1.10.0 本地 ST，已 Released）
- 前身 PMS: `.csp/product-spec/PMS-embedding.md`（v1.10.0 模块边界，仍有效）
- 复盘: `.csp/artifacts/retrospective-v1.10.0.md`（findings N1/N4）+ `.csp/artifacts/retrospective-v1.11.0.md`（N1/N4 续留确认）
- ROADMAP: `docs/strategy/ROADMAP.md#v1.12.0`
