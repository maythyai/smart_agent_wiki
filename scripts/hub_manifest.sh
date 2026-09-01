#!/usr/bin/env bash
# hub_manifest.sh — CSP knowledge-hub manifest CLI. Pure git+grep+awk, zero runtime deps.
# Manifest (.csp/manifest.json) is the唯一 sync baseline. sources.tsv is the editable input registry.
#
# Usage:
#   hub_manifest.sh gen              # compile sources.tsv -> manifest.json (merges build_status from old)
#   hub_manifest.sh status           # hub health: items / built / pending / failed
#   hub_manifest.sh locate <query>   # locate items by source_id|title|raw_path|output_path
#   hub_manifest.sh diff              # added/changed/removed vs manifest content_hash (git blob)
#   hub_manifest.sh list --type <t>   # list items by source_type (pms|cms|tms|wiki|doc|...)
#   hub_manifest.sh doctor            # self-check: AGENTS/manifest/lifecycle present + frontmatter no sidecar

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CSP="$ROOT/.csp"
MANIFEST="$CSP/manifest.json"
SOURCES="$CSP/sources.tsv"
LIFECYCLE="$CSP/lifecycle-state.json"

die() { printf 'hub: %s\n' "$*" >&2; exit 1; }

# --- minimal JSON field extractor (no jq): get value of a scalar field for a given source_id ---
# Reads manifest.json (one item per source_id). Returns first match.
get_field() { # <source_id> <field>
  local sid="$1" field="$2"
  [ -f "$MANIFEST" ] || return 0
  awk -v sid="\"$sid\"" -v f="\"$field\":" '
    $0 ~ "\"source_id\":" && $0 ~ sid { inblk=1 }
    inblk && $0 ~ f {
      # extract value after f
      line=$0; sub(".*"f, "", line); gsub(/^[ \t"]+/,"",line);
      # strip trailing comma/quote/brace
      sub(/".*/,"",line); gsub(/[ \t,]+$/,"",line);
      print line; inblk=0
    }
  ' "$MANIFEST" 2>/dev/null
}

cmd_gen() {
  [ -f "$SOURCES" ] || die "missing $SOURCES"
  mkdir -p "$CSP"
  local repo_url; repo_url="$(git -C "$ROOT" remote get-url origin 2>/dev/null || echo "")"
  local stamp; stamp="$(git -C "$ROOT" log -1 --format=%cI 2>/dev/null || echo unknown)"

  # start emit
  {
    printf '{\n'
    printf '  "manifest_id": "smart-agent-wiki-hub",\n'
    printf '  "schemaVersion": 1,\n'
    printf '  "version": 1,\n'
    printf '  "generated_at": "%s",\n' "$stamp"
    printf '  "repo_url": "%s",\n' "$repo_url"
    printf '  "items": [\n'
    local first=1
    while IFS=$'\t' read -r sid raw_path title domain kind; do
      # skip comments / blanks
      case "$sid" in ''|\#*) continue;; esac
      [ -n "$raw_path" ] || continue
      local hash updated build out_path wiki status stype
      if [ -f "$ROOT/$raw_path" ]; then
        hash="$(git -C "$ROOT" hash-object "$ROOT/$raw_path")"
        updated="$(git -C "$ROOT" log -1 --format=%cI -- "$raw_path" 2>/dev/null || echo unknown)"
        # preserve downstream writeback fields if source_id already in old manifest
        build="$(get_field "$sid" build_status)"; [ -n "$build" ] || build="pending"
        out_path="$(get_field "$sid" output_path)"; [ -n "$out_path" ] || out_path=""
        wiki="$(get_field "$sid" wiki_pages)"; [ -n "$wiki" ] || wiki="[]"
        status="$(get_field "$sid" status)"; [ -n "$status" ] || status="ready"
      else
        hash="" updated="" build="failed" out_path="" wiki="[]" status="blocked"
      fi
      # classify source_type from source_id prefix
      case "$sid" in
        pms:*) stype="pms";; cms:*) stype="cms";; tms:*) stype="tms";;
        wiki:*) stype="wiki";; codewiki:*) stype="codewiki";;
        memory:*) stype="memory";; doc:*) stype="doc";; *) stype="doc";;
      esac
      # CMS/PMS items are produced canonical artifacts (self-referential): default built + output=raw
      if [ "$stype" = "cms" ] || [ "$stype" = "pms" ]; then
        if [ "$build" = "pending" ]; then build="built"; fi
        if [ -z "$out_path" ]; then out_path="$raw_path"; fi
      fi
      [ "$first" = 1 ] || printf ',\n'
      first=0
      printf '    {\n'
      printf '      "source_id": "%s",\n' "$sid"
      printf '      "source_type": "%s",\n' "$stype"
      printf '      "kind": "%s",\n' "$kind"
      printf '      "domain": "%s",\n' "$domain"
      printf '      "title": "%s",\n' "$title"
      printf '      "raw_path": "%s",\n' "$raw_path"
      printf '      "output_path": "%s",\n' "$out_path"
      printf '      "original_ref": "%s",\n' "${raw_path}"
      printf '      "content_hash": "%s",\n' "$hash"
      printf '      "source_updated_at": "%s",\n' "$updated"
      printf '      "build_status": "%s",\n' "$build"
      printf '      "wiki_pages": %s,\n' "$wiki"
      printf '      "status": "%s"\n' "$status"
      printf '    }'
    done < "$SOURCES"
    printf '\n  ]\n}\n'
  } > "$MANIFEST.tmp"
  mv "$MANIFEST.tmp" "$MANIFEST"
  local n; n="$(grep -c '"source_id"' "$MANIFEST")"
  printf 'hub: generated %s — %s items\n' "$MANIFEST" "$n"
}

cmd_status() {
  [ -f "$MANIFEST" ] || die "no manifest; run gen first"
  local total built pending failed ready degraded blocked
  total="$(grep -c '"source_id"' "$MANIFEST")"
  built="$(grep -c '"build_status": "built"' "$MANIFEST" || true)"
  pending="$(grep -c '"build_status": "pending"' "$MANIFEST" || true)"
  failed="$(grep -c '"build_status": "failed"' "$MANIFEST" || true)"
  ready="$(grep -c '"status": "ready"' "$MANIFEST" || true)"
  degraded="$(grep -c '"status": "degraded"' "$MANIFEST" || true)"
  blocked="$(grep -c '"status": "blocked"' "$MANIFEST" || true)"
  printf '=== hub status ===\n'
  printf 'items:     %s\n' "$total"
  printf 'built:     %s\n' "$built"
  printf 'pending:   %s\n' "$pending"
  printf 'failed:    %s\n' "$failed"
  printf 'ready:     %s\n' "$ready"
  printf 'degraded:  %s\n' "$degraded"
  printf 'blocked:   %s\n' "$blocked"
}

cmd_locate() {
  [ -n "${1:-}" ] || die "usage: locate <query>"
  [ -f "$MANIFEST" ] || die "no manifest"
  local q="$1"
  awk -v q="$q" '
    /"source_id":/ {
      sid=$0; sub(/.*"source_id": "/,"",sid); sub(/".*/,"",sid)
      blk=""
      capturing=1
    }
    capturing { blk = blk $0 "\n" }
    capturing && /\}/ {
      if (blk ~ q) {
        printf "--- %s ---\n", sid
        print blk
      }
      capturing=0; blk=""
    }
  ' "$MANIFEST"
}

cmd_diff() {
  [ -f "$MANIFEST" ] || die "no manifest; run gen first"
  printf '=== diff (manifest vs working tree, git blob) ===\n'
  local added=0 changed=0 removed=0
  # changed/removed: items in manifest whose raw_path now differs or is gone
  awk -v RS='\n' '
    /"source_id":/ { sid=$0; sub(/.*"source_id": "/,"",sid); sub(/".*/,"",sid) }
    /"raw_path":/ { rp=$0; sub(/.*"raw_path": "/,"",rp); sub(/".*/,"",rp); paths[sid]=rp }
    /"content_hash":/ { h=$0; sub(/.*"content_hash": "/,"",h); sub(/".*/,"",h); hash[sid]=h }
    END { for (s in paths) print paths[s] "\t" hash[s] "\t" s }
  ' "$MANIFEST" | while IFS=$'\t' read -r rp h sid; do
    [ -n "$rp" ] || continue
    if [ -f "$ROOT/$rp" ]; then
      cur="$(git -C "$ROOT" hash-object "$ROOT/$rp" 2>/dev/null || echo MISSING)"
      if [ -z "$h" ]; then printf 'ADDED   %s  (%s)\n' "$rp" "$sid"; added=$((added+1))
      elif [ "$cur" != "$h" ]; then printf 'CHANGED %s  (%s)\n' "$rp" "$sid"; changed=$((changed+1))
      fi
    else
      printf 'REMOVED %s  (%s)\n' "$rp" "$sid"; removed=$((removed+1))
    fi
  done
  printf 'summary: changed/added/removed computed above\n'
}

cmd_list() {
  [ -f "$MANIFEST" ] || die "no manifest"
  local t="${2:-}"
  if [ -z "$t" ]; then
    awk '/"source_id":/{sid=$0;sub(/.*"source_id": "/,"",sid);sub(/".*/,"",sid)} /"raw_path":/{rp=$0;sub(/.*"raw_path": "/,"",rp);sub(/".*/,"",rp)} /"build_status":/{b=$0;sub(/.*"build_status": "/,"",b);sub(/".*/,"",b);printf "%-34s %-50s %s\n",sid,rp,b}' "$MANIFEST"
  else
    awk -v t="\"$t\"" '
      /"source_id":/{sid=$0;sub(/.*"source_id": "/,"",sid);sub(/".*/,"",sid);mtch=0}
      /"source_type":/{st=$0; if($0 ~ t) mtch=1}
      /"raw_path":/{rp=$0;sub(/.*"raw_path": "/,"",rp);sub(/".*/,"",rp)}
      /"build_status":/{b=$0;sub(/.*"build_status": "/,"",b);sub(/".*/,"",b); if(mtch) printf "%-34s %-50s %s\n",sid,rp,b}
    ' "$MANIFEST"
  fi
}

cmd_doctor() {
  local ok=1
  printf '=== hub doctor ===\n'
  [ -f "$CSP/AGENTS.md" ] && { printf 'AGENTS.md:      OK\n'; } || { printf 'AGENTS.md:      MISSING\n'; ok=0; }
  [ -f "$MANIFEST" ] && { printf 'manifest.json:  OK (%s items)\n' "$(grep -c '"source_id"' "$MANIFEST" || echo 0)"; } || { printf 'manifest.json:  MISSING\n'; ok=0; }
  [ -f "$LIFECYCLE" ] && { printf 'lifecycle:      OK\n'; } || { printf 'lifecycle:      MISSING\n'; ok=0; }
  [ -f "$SOURCES" ] && { printf 'sources.tsv:    OK\n'; } || { printf 'sources.tsv:    MISSING\n'; ok=0; }
  # no .meta.json sidecars under .csp spec dirs
  local sidecars; sidecars="$(find "$CSP" -name '.meta.json' 2>/dev/null | head -1)"
  [ -z "$sidecars" ] && printf 'sidecar audit:  OK (no .meta.json)\n' || { printf 'sidecar audit:  WARN .meta.json present\n'; ok=0; }
  [ "$ok" = 1 ] && printf '=> doctor PASS\n' || printf '=> doctor FAIL\n'
  return $(( 1 - ok ))
}

case "${1:-}" in
  gen) cmd_gen;;
  status) cmd_status;;
  locate) shift; cmd_locate "${1:-}";;
  diff) cmd_diff;;
  list) shift; cmd_list "$@";;
  doctor) cmd_doctor;;
  *) cat <<EOF
usage: hub_manifest.sh <command>
  gen            compile sources.tsv -> manifest.json
  status         hub health summary
  locate <q>     locate items by id/title/path
  diff           added/changed/removed vs content_hash
  list [--type T]  list items (optionally by source_type)
  doctor         self-check
EOF
  exit 1;;
esac
