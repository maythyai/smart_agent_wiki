# Release Notes — v1.11.0: 债务收口 IV / bug fix

**Tag**: v1.11.0
**Date**: 2026-09-05
**Internal milestone**: v4.1
**Commits**: 209c294, 42b9399, e3869d3, 0f0e82e, d943cf9, 5fca85b
**Bump type**: MINOR (additive — bug fix + coverage + behavior unify, no breaking API changes)

## Summary

收敛 v1.10.0 及累积的可修缺陷（不引入新能力、不需 SDK）。把 coverage 棘轮推进到 65，统一既有行为语义。

## Fixed

- **F-O-1: semantic search cache** — semantic search 走 query cache（复用 F-QS-07 cache 路径，query-text→embedding→results，TTL 300s + 索引变更失效）。修 v1.10.0 新引入的 perf bug（N7）。
- **F-O-2: compile/compiler deep coverage** — compile/compiler.py 17% → 深覆盖，coverage 64% → 65.36%，fail_under 65（N2/K1，拖 6 轮的 coverage 洼地填平）。
- **F-O-3: workflow REST unify** — CLI `saw workflow list` vs REST `/workflows` 语义双重统一：REST 读 DB（merge live + durable）消歧（M3）。
- **F-O-4: Spec naming + hash reconcile** — SPEC-F-N-1 命令名回更（`saw rebuild-embeddings` 实现偏离 Spec，回更 Spec）；tag hash 一致性复核（N5/N6）。

## Changed

- ADR-011: semantic cache 复用 F-QS-07 单例，mode=semantic key 隔离，TTL 300s，ingest/rebuild clear。
- ROADMAP 版本-主题表 v1.11.0 行 status → released。
- pyproject.toml version 1.10.0 → 1.11.0。

## Quality Gates

| Gate | Result |
|---|---|
| pytest | 2064 passed, 6 skipped, 0 failed |
| ruff check src/ tests/ | 0 errors |
| coverage | 65.36% (fail_under=65 ✓) |
| saw smoke | 6/6 passed |
| wheel build | smart_agent_wiki-1.11.0-py3-none-any.whl (822KB) |

## Notes

- 6 skipped = 3 原有 + 3 embedding importorskip（sentence_transformers 未装，同 v1.10.0）。
- 不需 `[learn]` extra（N1/N4 embedding E2E/benchmark 续留，须用户装 SDK）。

## 07 回流

- N7（semantic cache）✓
- N2/K1（coverage 65）✓
- M3（CLI vs REST 语义双重）✓
- N5（Spec 命名偏离）✓
- N6（tag hash 复核）✓
- 续留：N1（embedding E2E）/ N3（per-request ws）/ N4（benchmark）/ M2（agent 活动聚合）/ L2（链接自动 apply）
