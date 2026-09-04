# PMS-embedding — 产品模块说明书

> **边界（一句话）**：embedding 语义索引与检索 + smart-linking 语义增强。

| 字段 | 值 |
|---|---|
| slug | embedding |
| 边界 | embedding 语义索引与检索 + smart-linking 语义增强 |
| 优先级 | P0 |
| 关联 PRD | PRD-embedding-v1.10.0 §2 |
| 关联 Spec | .csp/specs/SPEC-F-N-1.md, SPEC-F-N-2.md, SPEC-F-N-3.md, SPEC-F-N-4.md |
| 关联 ADR | .csp/tech-decisions/ADR/ADR-010-embedding-storage-retrieval.md |
| 关联 TMS | .csp/test-spec/TMS-DELTA-v1.10.0.md |
| 状态 | ready |
| file | PMS-embedding.md |

## 模块范围

- **embedding 索引**：claim/wiki 页面向量入库（复用 `embeddings.py::embed_texts()`），通过 Write Queue sink 范式（参照 `fts5_sink.py`）。
- **语义检索**：Query 引擎增 semantic 模式（`QueryEngine.query()` mode=semantic），与 BM25 并行/融合。CLI `saw search --mode semantic` + REST `GET /api/v1/search?mode=semantic`。
- **smart-linking 语义增强**：`compute_related_pages` 增 embedding 相似度信号（tier=FULL 时），解 L1 启发式噪声。
- **heavy-SDK 测试**：`pytest.importorskip("sentence_transformers")` 沿用 distiller/fsrs 先例。

## 不包含

- 向量数据库选型/部署（03 技术方案 ADR）。
- 实时仪表盘/desktop（defer）。
- K1/K2 债务（续留）。

## 降级策略

- 无 `[learn]` extra（tier=LIGHTWEIGHT/OFFLINE）时：embedding 索引不建、语义检索降级到 BM25、smart-linking 保持 3-signal 启发式。不报错不中断。

## 关联

- PRD: `docs/prd/PRD-embedding-v1.10.0.md`
- Spec: `.csp/specs/SPEC-F-N-1.md` (embedding 索引) / `SPEC-F-N-2.md` (语义检索) / `SPEC-F-N-3.md` (smart-linking) / `SPEC-F-N-4.md` (importorskip 测试)
- ADR: `.csp/tech-decisions/ADR/ADR-010-embedding-storage-retrieval.md`
- TMS: `.csp/test-spec/TMS-DELTA-v1.10.0.md`
- 复盘: `.csp/artifacts/retrospective-v1.9.0.md`（findings M1 + L1）
