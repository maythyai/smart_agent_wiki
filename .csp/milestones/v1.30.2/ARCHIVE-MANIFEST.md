---
id: ARCHIVE-MANIFEST-v1.30.2
milestone: v1.30.2
release_type: PATCH (fix)
tag: v1.30.2
commit: 6a7d4d3
released: 2026-09-18
canonical_version: 1.30.2
---

# Archive Manifest — v1.30.2 (AUDIT-F-03 wiki 索引韧性)

## Release
- tag: `v1.30.2` (annotated, pushed origin)
- commit: `6a7d4d3 release: v1.30.2 — AUDIT-F-03 wiki 索引 YAML 韧性 (PATCH fix)`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.30.2
- assets: `smart_agent_wiki-1.30.2-py3-none-any.whl` + `smart_agent_wiki-1.30.2.tar.gz`

## Findings closed (1)
- AUDIT-F-03 [P1 resilience] `WikiIndexer.index_all()` per-page 容错（坏 YAML skip+warn+继续）。

## Gate
- pytest 2400 pass / 7 skip / 0 fail (+1 `test_index_all_skips_unparseable_page`)
- coverage 68.43% (gate 67 ✓); ruff 0
- bump: 1.30.1 → 1.30.2 (PATCH)

## 续留（折入后续版本）
- AUDIT-F-05/06 (saw web SPA + proxy) + AUDIT-F-08 (404→200) → v1.33.0
- AUDIT-F-01/04 (god-files + coverage 70) → v1.34.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- E2E-BLOCKED-01 → v1.33 saw web 挂 SPA 解除
- v1.31.0 (feat: activity 持久化 + Provenance API) — 下一版
