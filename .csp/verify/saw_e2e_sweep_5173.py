#!/usr/bin/env python3
"""SAW E2E route-sweep audit (Step 2). Evidence-first: route status / button inventory / console errors / network 4xx-5xx / screenshots + frontend-called API vs openapi diff."""
import json, os, time, re, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = "/Users/cs/projects/smart_agent_wiki/.csp/verify/ui-sweep"
os.makedirs(OUT, exist_ok=True)

ROUTES = ["/", "/search", "/graph", "/pages", "/dashboard",
          "/integrations", "/import", "/templates", "/timeline",
          "/login", "/onboarding", "/definitely-not-a-route-xyz"]

def slug(r): return re.sub(r'[^a-z0-9]+', '-', r.strip('/')).strip('-') or 'root'
def norm(path): return re.sub(r'/\d+', '/{id}', re.sub(r'/[^/]{20,}', '/{x}', path))

try:
    op = json.load(urllib.request.urlopen(BASE + "/openapi.json", timeout=5))
    openapi_paths = set(op.get("paths", {}).keys())
except Exception:
    openapi_paths = set()

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1366, "height": 900})
    results = []
    all_api_calls = set()
    for route in ROUTES:
        page = ctx.new_page()
        ce, ne, calls = [], [], []
        page.on("console", lambda m: ce.append(f"{m.type}:{m.text}") if m.type in ("error","warning") else None)
        page.on("response", lambda r: (ne.append(f"{r.status} {r.url.replace(BASE,'')}") if r.status >= 400 else None, calls.append(r.url.replace(BASE,"")) if "/api/" in r.url else None))
        rec = {"route": route, "errors": []}
        try:
            resp = page.goto(BASE + route, wait_until="networkidle", timeout=15000)
            time.sleep(1.2)
            rec["http_status"] = resp.status if resp else None
            rec["final_url"] = page.url
            rec["title"] = page.title()
            rec["h1_count"] = page.locator("h1").count()
            rec["has_main_content"] = bool(page.locator("main").count() and page.locator("main").inner_text().strip())
            rec["main_preview"] = (page.locator("main").inner_text()[:160].replace("\n"," ")) if page.locator("main").count() else ""
            btns = page.locator("button:visible").all()
            bi = []
            for b in btns[:20]:
                try: bi.append({"text": (b.inner_text() or "").strip()[:40], "disabled": b.is_disabled()})
                except Exception: bi.append({"text": "<stale>", "disabled": None})
            rec["button_count"] = len(btns)
            rec["buttons_sample"] = bi
            rec["empty_text_buttons"] = [b for b in bi if b["text"] == "" and not b["disabled"]]
            rec["console_errors"] = ce[:8]
            rec["net_4xx_5xx"] = ne[:12]
            rec["api_calls"] = sorted(set(calls))[:20]
            all_api_calls.update(calls)
            page.screenshot(path=f"{OUT}/{slug(route)}.png", full_page=False)
        except Exception as e:
            rec["errors"].append(f"NAV_FATAL: {e}")
        finally:
            page.close()
        results.append(rec)
    browser.close()

called = {u.split("?")[0] for u in all_api_calls}
called_norm = {norm(c) for c in called}
hidden = sorted([p for p in openapi_paths if norm(p) not in called_norm and p != "/openapi.json"])
report = {"base": BASE, "openapi_path_count": len(openapi_paths), "routes_audited": len(results),
          "frontend_api_called_count": len(called), "hidden_backend_api_uncalled": hidden, "route_results": results}
with open("/Users/cs/projects/smart_agent_wiki/.csp/verify/ui-test-report-5173.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(json.dumps({"routes": len(results), "openapi_paths": len(openapi_paths),
    "frontend_called": len(called), "hidden_backend_candidates": len(hidden),
    "routes_with_errors": [r["route"] for r in results if r.get("net_4xx_5xx") or r.get("console_errors") or r.get("errors")],
    "empty_main_routes": [r["route"] for r in results if not r.get("has_main_content")]}, indent=2))
