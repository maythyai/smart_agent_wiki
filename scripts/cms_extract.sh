#!/usr/bin/env bash
# cms_extract.sh — extract external entry points from src/saw into .csp/code-spec/saw/entry-points.jsonl.
# Pure grep+sed+awk, zero deps. Re-runnable (05 auto-align re-distills on code change).
# Each line: {"kind","id","file","line","method","route","scenario"}
set -uo pipefail
emit() { printf '%s\n' "$1" >> "$OUT"; }
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src/saw"
OUT="$ROOT/.csp/code-spec/saw/entry-points.jsonl"
mkdir -p "$(dirname "$OUT")"
: > "$OUT"

emit() { printf '%s\n' "$1" >> "$OUT"; }

# --- CLI: top-level commands registered in main.py (name -> def in commands/<name>_cmd.py) ---
emit_cli() { # <name> <deffile:line>
  local name="$1" loc="$2"
  printf '{"kind":"cli","id":"cli:%s","file":"src/saw/drivers/cli/commands/%s","line":%s,"method":"%s","scenario":"[inferred] %s CLI command"}\n' \
    "$name" "${loc%%:*}" "${loc##*:}" "$name" "$name" >> "$OUT"
}
emit_cli init        init_cmd.py:22
emit_cli status      status_cmd.py:18
emit_cli ingest      ingest_cmd.py:35
emit_cli ingest-media ingest_media_cmd.py:31
emit_cli query       query_cmd.py:31
emit_cli search      search_cmd.py:24
emit_cli lint        lint_cmd.py:12
emit_cli verify      verify_cmd.py:12
emit_cli freshness   freshness_cmd.py:12
emit_cli review      review_cmd.py:13
emit_cli conflicts   conflicts_cmd.py:18
emit_cli audit      audit_cmd.py:17
emit_cli mcp        mcp_cmd.py:16
emit_cli web        web_cmd.py:14
emit_cli tutorial   tutorial_cmd.py:230
# CLI aliases (i/q/s/w/v/l) registered in main.py — same handlers, file main.py
for pair in "i:ingest" "q:query" "s:status" "w:web" "v:verify" "l:lint"; do
  a="${pair%%:*}"; printf '{"kind":"cli","id":"cli:%s","file":"src/saw/drivers/cli/main.py","line":0,"method":"%s","scenario":"[inferred] alias of %s (line unresolved, [TBD])"}\n' "$a" "$a" "${pair##*:}" >> "$OUT"
done

# --- CLI sub-app commands (feed_cmd, plugin_cmd use @app.command("name")) ---
# feed
grep -n '@app.command' "$SRC/drivers/cli/commands/feed_cmd.py" | while IFS=: read -r ln rest; do
  name="$(printf '%s' "$rest" | sed -n 's/.*@app\.command("\([^"]*\)").*/\1/p')"
  [ -n "$name" ] && printf '{"kind":"cli","id":"cli:feed:%s","file":"src/saw/drivers/cli/commands/feed_cmd.py","line":%s,"method":"feed %s","scenario":"[inferred] RSS feed %s"}\n' "$name" "$ln" "$name" "$name" >> "$OUT"
done
grep -n '@app.command' "$SRC/drivers/cli/commands/plugin_cmd.py" | while IFS=: read -r ln rest; do
  name="$(printf '%s' "$rest" | sed -n 's/.*@app\.command("\([^"]*\)").*/\1/p')"
  [ -n "$name" ] && printf '{"kind":"cli","id":"cli:plugin:%s","file":"src/saw/drivers/cli/commands/plugin_cmd.py","line":%s,"method":"plugin %s","scenario":"[inferred] plugin %s"}\n' "$name" "$ln" "$name" "$name" >> "$OUT"
done
# dynamic sub-apps (code_graph, compile) — registered via register_*_commands(app); mark [TBD] line
printf '{"kind":"cli","id":"cli:code-graph","file":"src/saw/code_graph/cli.py","line":0,"method":"code-graph <sub>","scenario":"[TBD] sub-commands registered via register_code_graph_commands; enumerate in 05"}\n' >> "$OUT"
printf '{"kind":"cli","id":"cli:compile","file":"src/saw/drivers/cli/commands/compile_cmd.py","line":0,"method":"compile <sub>","scenario":"[TBD] wiki/archive/concept/issue/cr/code-wiki sub-apps via register_compile_commands; enumerate in 05"}\n' >> "$OUT"

# --- MCP tools: @mcp.tool + following async def name ---
for f in "$SRC"/drivers/mcp/tools/*.py; do
  [ -e "$f" ] || continue
  bn="$(basename "$f")"
  awk -v file="src/saw/drivers/mcp/tools/$bn" '
    /^@mcp\.tool/ { hit=NR; next }
    hit && /def / {
      name=$0; sub(/.*def /,"",name); sub(/\(.*/,"",name);
      printf "{\"kind\":\"mcp\",\"id\":\"mcp:%s\",\"file\":\"%s\",\"line\":%d,\"method\":\"%s\",\"scenario\":\"[inferred] MCP tool %s\"}\n", name, file, NR, name, name;
      hit=0
    }
  ' "$f" >> "$OUT"
done

# --- Web routes: @router.<method>(path) + file prefix (from APIRouter(prefix=...)) ---
emit_web() { # <fileRel> <line> <method> <route> <prefix>
  local fr="$1" ln="$2" m="$3" r="$4" pfx="$5"
  printf '{"kind":"web","id":"web:%s:%s:%s","file":"src/saw/%s","line":%s,"method":"%s","route":"%s","prefix":"%s","scenario":"[inferred] %s %s"}\n' \
    "${fr##*/}" "$ln" "$m" "$fr" "$ln" "$m" "$r" "$pfx" "$m" "$r" >> "$OUT"
}
scan_routes() { # <dirRel>
  local dir="$1"
  find "$SRC/$dir" -name '*.py' -not -path '*__pycache__*' 2>/dev/null | sort | while read -r f; do
    rel="${f#$SRC/}"
    pfx="$(grep -m1 'APIRouter(prefix=' "$f" | sed -n 's/.*prefix="\([^"]*\)".*/\1/p')"
    [ -z "$pfx" ] && pfx="(mounted at include_router)"
    grep -nE '@router\.(get|post|put|delete|patch|websocket)\(' "$f" | while IFS=: read -r ln rest; do
      m="$(printf '%s' "$rest" | sed -n 's/.*@router\.\([a-z]*\)(.*/\1/p')"
      r="$(printf '%s' "$rest" | sed -n 's/.*@router\.[a-z]*(\([^,)]*\).*/\1/p' | tr -d '"' | tr -d "'")"
      [ -z "$r" ] && r='(see source)'
      printf '{"kind":"web","id":"web:%s:%s","file":"src/saw/%s","line":%s,"method":"%s","route":"%s","prefix":"%s","scenario":"[inferred] %s %s"}\n' \
        "$rel" "$ln" "$rel" "$ln" "$m" "$r" "$pfx" "$m" "$r" >> "$OUT"
    done || true
  done
}
scan_routes api
scan_routes drivers/web/routes

# --- Webhook / WS / background already captured as web routes above; flag webhook-specific ---
# (github_webhook, webhook_inbound, oauth_callback, integrations_ws, websocket are in api/ or web/routes/)

echo "cms: wrote $OUT ($(wc -l < "$OUT") entries)"
