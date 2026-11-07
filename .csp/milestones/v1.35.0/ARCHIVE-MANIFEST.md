---
id: ARCHIVE-MANIFEST-v1.35.0
milestone: v1.35.0
release_type: MINOR (feat)
tag: v1.35.0
commit: 3c24e08c
released: 2026-11-07
---

# Archive Manifest — v1.35.0 (Structured Context API v1 ★品类定位)

## Release
- tag: `v1.35.0` (pushed origin)
- Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.35.0
- assets: wheel + sdist (1.35.0)

## Added (F1+F3+F5 partial)
- `saw_context` 统一 MCP (query.py): mode=semantic|graph|drift|hybrid, unified bundle.
- `POST /api/v1/context` REST (query_ingest_learn.py).
- state 层: confidence_min + freshness_min (last_accessed age heuristic v1).
- workspace_id via contextvar (permission partial).
- MCP 工具 39→40.

## Gate
- pytest 2441/0 fail (+4 TestStructuredContextRoute); cov 68.51% (gate 68); ruff 0; tsc clean
- 双闸门 exit 0 (vi=0, fc=0)

## Deferred → v1.35.1
- F2 ontology 层 + F4 自适应路由
- v1.34.1 deferred (coverage 70% + god-files) 续留