# Release Notes — v1.10.0: embedding 语义搜索

**Tag**: v1.10.0
**Date**: 2026-09-04
**Internal milestone**: v4.0
**Commits**: ecbdb75, 9660ecc, 3b2039e, e7fb6c6, fef4deb, 15bb5fe
**Bump type**: MINOR (additive — no breaking API changes)

## Summary

引入 embedding 语义搜索，从 BM25 词面匹配扩到语义匹配。直接提升 trustworthy-claim coverage 北极星，并解掉 L1（smart-linking suggest 启发式噪声）。

## Added

- **F-N-1: embedding 索引** — claim/wiki 页面向量入库，复用 `[learn]` extra 的 sentence-transformers。EmbeddingSink（BLOB storage + numpy cosine），migration v10，`saw embedding rebuild` CLI。
- **F-N-2: 语义检索** — query engine 增 `--mode semantic` 并行模式，`saw query --mode semantic` CLI，`GET /api/v1/search?mode=semantic` REST 端点。
- **F-N-3: smart-linking embedding signal** — `saw links suggest` 接 embedding 相似度，替代/增强 3-signal 启发式，解 L1 噪声。
- **F-N-4: 测试** — importorskip 模式（3 文件 skip when sentence_transformers 未装）+ degradation mock 测试（4 测试无条件 pass）。

## Changed

- ADR-010: embedding_store BLOB + numpy cosine；`--mode` 并行不融合；all-MiniLM-L6-v2 384 维。
- ROADMAP 版本-主题表 v1.10.0 行 status → released。

## Notes

- embedding E2E 测试（AC-EMB-1/AC-SEM-1/AC-LINK-1）须 `pip install -e ".[learn]"`（sentence_transformers），CI 环境 skip。
- degradation 测试（AC-EMB-2/AC-SEM-2/AC-LINK-2）通过 mock 无条件 pass。
- 6 skipped = 3 原有 + 3 embedding importorskip。

## Quality Gates

| Gate | Result |
|---|---|
| pytest | 1993 passed, 6 skipped, 0 failed |
| ruff check src/ tests/ | 0 errors |
| saw smoke | 6/6 passed |
| wheel build | smart_agent_wiki-1.10.0-py3-none-any.whl |

## 07 回流

- M1（embedding defer 解除）✓
- L1（smart-linking 噪声）✓ — embedding signal 替代启发式
- K1（coverage 65）/K2（per-request ws）续留
