# 复盘 — v1.33.0 saw web 挂 SPA + proxy + 404（2026-10-15）

> 07 闭环校验。feat MINOR (P1)。解 E2E-BLOCKED-01。前置：06-ship done（v1.33.0 tagged @32198570, pushed, Release）。

## 闭环校验：✅ 通过
| 链路 | 状态 | 证据 |
|---|---|---|
| 四读前置 | ✅ | conventions via prompts/ + findings 折入 AUDIT-F-05/06/08 + E2E-BLOCKED-01 + lifecycle 对账无漂移 |
| PRD→Spec | ✅ | PRD-saw-web-spa-v1.33.0 Approved (GWT 4) + SPEC-F-SAW-WEB-SPA (接口契约+测试+风险+file:line) |
| Spec→Task | ✅ | app.py SPA mount + vite.config.ts env + NotFound noindex + Playwright e2e + 4 unit tests |
| S6 动态门控 | ✅ ran exit 0 | pytest 2425/0 fail, cov 68.43%, ruff 0, tsc/vite/tauri build ✓, Playwright e2e 86.69s |
| 7.6 对账 | ✅ | findings_closure exit 0 (4 closed 带验证) + version_integrity exit 0 (T3/T4 ✓) |
| commit→tag→push→Release | ✅ | v1.33.0 @32198570, pushed origin, GitHub Release 含 wheel+sdist |

## 度量
- 4 feat done (SPA mount + proxy env + noindex + Playwright e2e)
- pytest 2425 passed (+5)
- 4 findings closed (AUDIT-F-05/06/08 + E2E-BLOCKED-01)
- feat MINOR (additive)

## Lessons（并入下一版 01 入口）
- saw web 启动索引 wiki 页耗时 ~80s（wiki 根=cwd 扫描数百 .md 含 .csp/specs/.claude/.cursor）——AUDIT-F-03 fix 使坏页 skip 不阻断，但索引量大慢。→ **v1.34 性能硬化**应含"wiki 根改 wiki/ 非 cwd"（性能 finding，新）。
- vite.config.ts 用 process.env 需 `declare const process`（tsc -b 无 @types/node types field）——TypeScript config 文件用 Node API 须显式 declare 或加 types。
- Playwright e2e 须 120s 超时（saw web wiki 索引慢），_wait_up 轮询 /api/auth/mode。

## 下游衔接 → v1.34.0
- v1.34.0 (feat MINOR): ANN ≥5000 实证 + coverage 70 + god-files 拆分 (AUDIT-F-01/04) + stale-freshness contamination (v1.31.1 deferred) + wiki 根性能优化 (本版 lesson)。
