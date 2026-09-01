#!/usr/bin/env bash
# claim_diff.sh — T-F-B-1-1: diff README/docs claims vs code reality (entry-points.jsonl).
#
# Usage: claim_diff.sh [entry_points.jsonl] [docs...]
#   default EP=.csp/code-spec/saw/entry-points.jsonl
#   default docs=README.md README_CN.md docs/*.md
#
# Outputs ACTUAL counts (from entry-points) + STALE CLAIMS (curated patterns
# known to contradict current code per PRD §1 实现度现状). Exit 0 if clean, 1 if stale.
#
# MVP: curated stale-pattern detection + actual counts. General NLP claim-vs-code
# diff is [TBD] V1.1 (F-B-2 能力清单 covers per-capability file:line verification).
set -uo pipefail
EP="${1:-.csp/code-spec/saw/entry-points.jsonl}"
shift 2>/dev/null || true
if [ "$#" -eq 0 ]; then
  set -- README.md README_CN.md docs/*.md
fi

# --- actual counts from entry-points.jsonl ---
count_kind() { # <kind>
  [ -f "$EP" ] || { printf 0; return; }
  grep -c "\"kind\":\"$1\"" "$EP" 2>/dev/null || printf 0
}
ACTUAL_MCP=$(count_kind mcp)
ACTUAL_CLI=$(count_kind cli)
ACTUAL_WEB=$(count_kind web)

printf '=== ACTUAL (from %s) ===\n' "$EP"
printf 'mcp tools:  %s\n' "$ACTUAL_MCP"
printf 'cli cmds:   %s\n' "$ACTUAL_CLI"
printf 'web routes: %s\n' "$ACTUAL_WEB"
printf '\n'

# --- curated stale-claim patterns (contradict current code per PRD §1) ---
# Each: pattern<TAB>why_stale
STALE_PATTERNS=$(cat <<'EOF'
execute() 为空实现	agents are implemented (librarian.py:46+); 6-agent execute() real
实际只有 6 个	MCP tools are 61, not 6 (deep_audit 2026-06-23 stale)
24+ MCP 工具实际	README says 56+, actual 61; "only 6" stale
2 个完全不存在	all 7 connector platforms have code (notion full)
互不通信	backend auth unified via AuthService (auth.py:13)
EOF
)

printf '=== STALE CLAIMS scan ===\n'
stale=0
while IFS=$'\t' read -r pat why; do
  [ -n "$pat" ] || continue
  hits=""
  for doc in "$@"; do
    [ -f "$doc" ] || continue
    # skip historical-snapshot-annotated lines (F-B-3 marks deep_audit as 历史快照)
    match=$(grep -nF "$pat" "$doc" 2>/dev/null | grep -v '历史快照' | grep -v '不作依据' || true)
    [ -n "$match" ] && hits="$hits$match"$'\n'
  done
  if [ -n "$hits" ]; then
    printf 'STALE  [%s] → %s\n' "$pat" "$why"
    printf '%s' "$hits"
    stale=1
  fi
done <<EOF
$STALE_PATTERNS
EOF

if [ "$stale" = "0" ]; then
  printf 'clean: no stale claims (or all marked 历史快照)\n'
  exit 0
else
  printf '\n=> %s stale claim(s) found; fix docs (F-B-3) or mark 历史快照\n' "$stale"
  exit 1
fi
