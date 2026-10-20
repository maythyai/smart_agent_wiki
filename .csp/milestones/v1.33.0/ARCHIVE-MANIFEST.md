---
id: ARCHIVE-MANIFEST-v1.33.0
milestone: v1.33.0
release_type: MINOR (feat)
tag: v1.33.0
commit: 32198570
released: 2026-10-15
canonical_version: 1.33.0
---

# Archive Manifest — v1.33.0 (saw web 挂 SPA + proxy + 404)

## Release
- tag: `v1.33.0` (annotated, on release commit 32198570)
- commit: `32198570 release: v1.33.0 — saw web 挂 SPA + proxy env + 404 noindex (feat MINOR, P1)`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.33.0
- assets: wheel + sdist (1.33.0)

## Added (4, 解 E2E-BLOCKED-01 + AUDIT-F-05/06/08)
- saw web 挂 SPA: create_app() mount web/dist StaticFiles + SPA fallback. saw web 单命令服务 API+SPA.
- vite proxy env-config: VITE_API_TARGET (default :8000). web/vite.config.ts + declare process (tsc -b).
- NotFound noindex: useEffect meta robots noindex (AUDIT-F-08).
- Playwright e2e: tests/e2e/test_saw_web_spa.py (real saw web + chromium → GET / 200 + #root + /api/auth/mode 200).

## Gate
- pytest 2425 pass / 7 skip / 0 fail (+5: 4 TestSpaMountRoute + 1 Playwright e2e)
- coverage 68.43% (gate 67 ✓); ruff 0; tsc/vite/tauri build ✓
- bump: 1.32.1 → 1.33.0 (MINOR, additive)
- 双闸门: version_integrity + findings_closure (with --baseline) exit 0

## Findings closed (4, with verification)
- AUDIT-F-05 (saw web SPA) → closed, fixed_in=v1.33.0, verification=code+dynamic
- AUDIT-F-06 (vite proxy) → closed, fixed_in=v1.33.0
- AUDIT-F-08 (404 noindex) → closed, fixed_in=v1.33.0
- E2E-BLOCKED-01 (数据 E2E) → closed, fixed_in=v1.33.0

## 续留
- AUDIT-F-01/04 (god-files + coverage 70) + stale-freshness contamination → v1.34.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- desktop 签名/跨平台 (V1/V2) → v1.33.1
