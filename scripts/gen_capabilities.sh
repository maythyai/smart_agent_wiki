#!/usr/bin/env bash
# gen_capabilities.sh — T-F-B-2 (AC-ALIGN-2)
#
# Consume .csp/code-spec/saw/entry-points.jsonl (+ knowledge-graph.json) and
# emit docs/CAPABILITIES.md, one row per capability with file:line provenance.
# Entries whose scenario is `[inferred]` (not grounded by a real call) are
# marked [unverified] — never written as "supported" without code backing.
#
# Usage: bash scripts/gen_capabilities.sh [repo-root]
set -euo pipefail

ROOT="${1:-.}"
ENTRIES="$ROOT/.csp/code-spec/saw/entry-points.jsonl"
KG="$ROOT/.csp/code-spec/saw/knowledge-graph.json"
OUT="$ROOT/docs/CAPABILITIES.md"

python3 - "$ENTRIES" "$KG" "$OUT" <<'PY'
import json, sys
from pathlib import Path

entries_path, kg_path, out_path = sys.argv[1:4]
entries = [json.loads(l) for l in Path(entries_path).read_text().splitlines() if l.strip()]

# Group by kind for readability.
by_kind: dict[str, list] = {}
for e in entries:
    by_kind.setdefault(e.get("kind", "misc"), []).append(e)

lines = [
    "# Capabilities — code-grounded inventory",
    "",
    "> Generated from `.csp/code-spec/saw/entry-points.jsonl` (CMS 00-hub distillation).",
    "> Each row traces a capability to its code entry point (file:line).",
    "> `[unverified]` = scenario inferred, not grounded by a real call path —",
    "> do not claim as supported without further verification.",
    "",
]

verified_n = 0
unverified_n = 0
for kind in sorted(by_kind):
    lines.append(f"## {kind}")
    lines.append("")
    lines.append("| capability | entry | file:line | status |")
    lines.append("|---|---|---|---|")
    for e in sorted(by_kind[kind], key=lambda x: x.get("id", "")):
        scen = e.get("scenario", "")
        unverified = scen.startswith("[inferred]") or scen == ""
        status = "[unverified]" if unverified else "verified"
        if unverified:
            unverified_n += 1
        else:
            verified_n += 1
        file_ = e.get("file", "—")
        line_ = e.get("line", "—")
        loc = f"{file_}:{line_}" if file_ != "—" else "—"
        lines.append(f"| {e.get('id','—')} | {e.get('method','—')} | {loc} | {status} |")
    lines.append("")

lines += [
    "## Summary",
    "",
    f"- verified: **{verified_n}**",
    f"- unverified: **{unverified_n}** (need call-path grounding)",
    f"- total: {verified_n + unverified_n}",
]

Path(out_path).parent.mkdir(parents=True, exist_ok=True)
Path(out_path).write_text("\n".join(lines) + "\n")
print(f"wrote {out_path}: {verified_n} verified, {unverified_n} unverified")
PY
