---
id: SPEC-F-SAW-WEB-SPA
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-15
status: approved
prd_ref: PRD-saw-web-spa-v1.33.0
target_version: v1.33.0
---

# SPEC — v1.33.0 saw web 挂 SPA + proxy + 404（详细）

## 技术方案

### F-1: saw web 挂 SPA（AUDIT-F-05）
**文件**: `src/saw/drivers/web/app.py` `create_app()`（末尾，所有 `include_router` 之后，避免 shadow /api）。

挂载逻辑（graceful：web/dist 不存在则不挂，保持 API-only）：
```python
from pathlib import Path as _Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# ... after all app.include_router(...)
_dist = _Path("web/dist")
_index = _dist / "index.html"
if _dist.is_dir() and _index.is_file():
    # Built JS/CSS assets (vite outputs to web/dist/assets/)
    _assets = _dist / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="spa-assets")
    # SPA fallback: non-/api paths → index.html (client routing). /api/unknown → 404.
    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            raise HTTPException(status_code=404)
        return FileResponse(str(_index))
```
**证据 file:line**: `src/saw/drivers/web/app.py` `create_app` return 前（当前无 StaticFiles/mount——AUDIT-F-05 证据：grep 无）。

**接口契约**: `GET /` → 200 `text/html`（index.html，含 `<div id="root">`）。`GET /assets/*.js` → 200（StaticFiles）。`GET /pages` → 200 `text/html`（SPA fallback → index.html，客户端路由解析）。`GET /api/v1/compliance` → 200 JSON（路由先匹配，不被 fallback 拦截）。`GET /api/unknown` → 404（fallback 排除 api/）。

### F-2: vite proxy env-config（AUDIT-F-06）
**文件**: `web/vite.config.ts`（line 17-24 server.proxy）。
```ts
const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:8000';
proxy: {
  '/api': { target: apiTarget, changeOrigin: true },
  '/ws':  { target: apiTarget.replace('http','ws'), ws: true },
}
```
**证据**: `web/vite.config.ts:19` 硬编 `http://localhost:8000`（AUDIT-F-06）。

### F-3: NotFound noindex（AUDIT-F-08）
**文件**: `web/src/pages/NotFound.tsx`。加 `<meta name="robots" content="noindex">` via `useEffect`（document.head）或 react-helmet。无 react-helmet → useEffect 注入 meta + cleanup。
**证据**: `web/src/pages/NotFound.tsx`（AUDIT-F-08: 客户端 404→200）。

### F-4: Playwright smoke（解 E2E-BLOCKED-01）
**文件**: `tests/e2e/test_saw_web_spa.py`（新）。启动 `saw web :9133`（fixture）→ Playwright GET / → 200 + `#root` div + GET /api/auth/mode → 200 JSON `auth_mode`。
**证据**: `.csp/verify/ui-test-report.md` E2E-BLOCKED-01（vite proxy→vLLM 非 SAW；本版 saw web 服务 SPA 后直驱）。

## 测试计划
1. **单元**: `tests/unit/drivers/web/test_spa_mount.py` — create_app + web/dist fixture → GET / 200 + /api/v1/compliance 200 + /api/unknown 404（TestClient，不依赖真实 dist——用 tmp dist）。
2. **Playwright smoke**: `tests/e2e/test_saw_web_spa.py` — real saw web + chromium → / 200 + root div + /api/auth/mode 200（数据 E2E gate 证据）。
3. **回归**: pytest 全量 0 fail / ruff 0 / tsc clean / vitest pass。
4. **双闸门**: version_integrity (T3 pyproject+VERSION=v1.33.0) + findings_closure (AUDIT-F-05/06/08 closed 带验证)。

## 风险
- **R1 fallback shadow /api**: 缓解——fallback 注册在所有 include_router 之后 + `full_path.startswith("api/")` → 404（已含）。
- **R2 web/dist 未构建**: 缓解——`_dist.is_dir() and _index.is_file()` guard，不存在则不挂（API-only，不报错）。
- **R3 Playwright CI**: smoke 须能起 saw web + chromium；已在审计时装好 playwright+chromium。
- **R4 vite proxy env 默认**: 不传 env 仍 → :8000（向后兼容）。

## 测试矩阵
| AC | 测试 | 证据 |
|---|---|---|
| GWT-1 | test_spa_mount: GET / 200 + root div + /api/v1/compliance 200 + /api/unknown 404 | TestClient |
| GWT-2 | vite.config.ts 读 VITE_API_TARGET env | tsc + 手测 |
| GWT-3 | NotFound noindex meta | vitest + tsc |
| GWT-4 | Playwright smoke saw web SPA + API | e2e test ran+exit 0 |
