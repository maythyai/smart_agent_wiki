---
id: ARCHIVE-MANIFEST-v1.31.0
milestone: v1.31.0
release_type: MINOR (feat)
tag: v1.31.0
commit: 532b3f4
released: 2026-09-18
canonical_version: 1.31.0
---

# Archive Manifest — v1.31.0 (Provenance API + Activity 持久化)

## Release
- tag: `v1.31.0` (annotated, pushed origin)
- commit: `532b3f4 release: v1.31.0 — Provenance Verification API + Activity 持久化 (feat MINOR)`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.31.0
- assets: `smart_agent_wiki-1.31.0-py3-none-any.whl` + `smart_agent_wiki-1.31.0.tar.gz`

## Added (3)
- AUDIT-F-05 闭合（Activity 持久化）: v12 migration `agent_activity` 表 + AgentActivityTracker write-through + load/attach_conn.
- `GET /api/v1/provenance/{claim_id}` REST: trace source chain (depth cap 10 + cycle guard).
- `saw_verify` MCP 增强: source_claim_uuid + receipt_id.

## Gate
- pytest 2406 pass / 7 skip / 0 fail (+6: 2 activity persistence + 4 provenance REST)
- coverage 68.43% (gate 67 ✓); ruff 0; tsc clean
- bump: 1.30.2 → 1.31.0 (MINOR, additive, 无 breaking)

## Deferred → v1.31.1（附解除条件，已满足）
- contamination scan（检测衍生自过期/被取代源的 claim）→ v1.31.1 MINOR。解除条件: v1.31.0 released ✓。

## 续留（折入后续版本）
- AUDIT-F-01/04 (god-files + coverage 70) → v1.34.0
- AUDIT-F-05/06 (saw web SPA + proxy) + AUDIT-F-08 (404→200) → v1.33.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- E2E-BLOCKED-01 → v1.33 saw web 挂 SPA 解除
