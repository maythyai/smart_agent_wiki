# Release v1.17.0 — desktop 完成 v4.4

**Tag**: v1.17.0  
**Date**: 2026-09-07  
**Type**: additive MINOR (pyproject), desktop 0.1.0→1.0.0  
**Internal milestone**: v4.7  

## Summary

Desktop application reaches 1.0. Tauri build produces native macOS `.app` + `.dmg` bundles. Web dashboard (v1.16.0) is integrated into the desktop app. Port convergence (8080→8000) and CORS expansion (localhost:5173) enable seamless dev/prod workflows.

## What's New

### Desktop 1.0 (T-F-V-1)
- Version bumped `0.1.0 → 1.0.0` across `desktop/package.json`, `tauri.conf.json`, `Cargo.toml`, `web/package.json`
- 15-item tauri.conf.json config audit (version, frontendDist, devUrl, beforeBuildCommand, bundle targets, plugins, IPC commands, release profile)
- Desktop version now aligned to canonical pyproject versioning

### Web Dashboard Integration (T-F-V-2)
- Desktop loads `web/dist` as `frontendDist` (verified dev/prod build chain)
- `@tauri-apps/api` ^2.0.0 dependency confirmed
- Dashboard from v1.16.0 (agent roster + activity + workflow runtime + realtime updates) accessible within desktop app

### Tauri Build Verification (T-F-V-3)
- `tauri build` produces native macOS bundles:
  - `Smart Agent Wiki.app` (macOS native application)
  - `Smart Agent Wiki_1.0.0_aarch64.dmg` (~2.8 MB)
- 8 Tauri plugins (fs, dialog, shell, http, notification, window, app, os)
- 16 IPC commands exposed
- Release profile optimized for production

### Port Convergence + CORS (T-F-V-4)
- `web/vite.config.ts` proxy target `8080 → 8000` (aligns with `web_cmd.py` default port)
- CORS origins expanded to include `localhost:5173` (desktop dev port)
- Prod mode: desktop uses external saw web server (`VITE_API_BASE_URL` configurable)

## Verification

| Gate | Result |
|---|---|
| pytest | 2267 passed, 7 skipped, 0 failed |
| ruff | 0 errors |
| smoke | 16/16 passed |
| vitest | 64 passed (13 files), 0 failed |
| vite build | 1029 modules, success |
| tauri build | .app + .dmg produced |

## Downloads

- **macOS (Apple Silicon)**: `Smart Agent Wiki_1.0.0_aarch64.dmg` — unsigned (code signing deferred per ADR-017, v2.0 candidate)

## Important Notes

- **Unsigned DMG**: The `.dmg` is not code-signed. On macOS, you may need to right-click → Open, or go to System Settings → Privacy & Security → "Open Anyway" to run the app. Code signing is deferred to v2.0 per ADR-017.
- **No new dependencies**: No new Python or JS dependencies added. No torch loaded.
- **Backend changes minimal**: 4 lines total (vite.config.ts 2 + web_cmd.py 1 + app.py 1). No backend logic changes.
- **50 new pytest tests**: version consistency + tauri config + web dist/dev integration + bundle targets + port convergence + CORS expansion + prod backend + tauri build smoke.

## ADR

- **ADR-017**: Desktop embed strategy — Hybrid (dev proxy + prod external sidecar defer). Port convergence 8080→8000, CORS +5173. Sidecar execution deferred to v2.0.

## Commits

| Commit | Description |
|---|---|
| `f922a99` | feat(desktop): F-V-1 bump 0.1.0→1.0.0 + config convergence |
| `19578ef` | feat(desktop): F-V-2 web dashboard integration verify |
| `6bb6949` | build(desktop): F-V-3 tauri build produces .app/.dmg |
| `1ca63a1` | fix(web): F-V-4 port convergence 8080→8000 + CORS localhost:5173 |
| `e391611` | chore(csp): v1.17.0 reconcile planning artifacts + pyproject bump |

## Roadmap Reference

- **Track**: ecosystem-integration
- **Theme**: desktop 完成 v4.4 (Tauri→1.0 + 集成 web 仪表盘)
- **Previous**: v1.16.0 (realtime 仪表盘 v4.3)
- **Next candidates**: v2.0 per-request workspace, agent activity persistence, links apply undo, engine.py refactor, Playwright E2E
