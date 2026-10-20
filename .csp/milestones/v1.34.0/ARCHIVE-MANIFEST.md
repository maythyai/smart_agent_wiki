---
id: ARCHIVE-MANIFEST-v1.34.0
milestone: v1.34.0
release_type: MINOR (feat)
tag: v1.34.0
commit: 23adaf38
released: 2026-10-20
canonical_version: 1.34.0
---

# Archive Manifest — v1.34.0 (wiki 根性能 + coverage 推进)

## Release
- tag: `v1.34.0` (annotated, pushed origin)
- commit: `23adaf38 release: v1.34.0 — wiki 根性能 + coverage 推进`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.34.0
- assets: wheel + sdist (1.34.0)

## Added (2)
- wiki 根性能: app.py:575 Path(".") → Path("wiki"). saw web 启动 80s→15s.
- coverage: +12 ingest pipeline tests (parse 13→77%, validate 15→87%). fail_under 67→68. total 68.43→68.74%.

## Gate
- pytest 2437 pass / 7 skip / 0 fail (+12 pipeline tests)
- coverage 68.74% (gate 68 ✓); ruff 0; tsc clean
- 双闸门: version_integrity + findings_closure exit 0

## Deferred → v1.34.1
- AUDIT-F-04 70% target (差 1.3%): 需补 extract.py/feed_cmd.py/learn.py 测试。
- AUDIT-F-01 god-files 拆分 (app.py 755/engine.py 631/compiler.py 663)。
- stale-freshness contamination (需 FreshnessTracker 集成)。

## 续留
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- desktop 签名/跨平台 (V1/V2) → v1.33.1
