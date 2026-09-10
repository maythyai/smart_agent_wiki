---
name: saw-tools
description: Smart Agent Wiki (SAW) MCP tool guide for coding agents. Use BEFORE modifying code (saw_code_context / saw_impact / saw_blast_radius to scope blast radius), to check staleness (saw_freshness / saw_status), and AFTER changes (saw_verify / saw_lint / saw_audit). Triggers on saw_*, code change planning, impact analysis, knowledge staleness, wiki compilation.
---

# SAW Tools — Agent Guidance (when to call which)

Smart Agent Wiki (SAW) exposes 60+ MCP tools (`saw_*`). This skill tells a coding agent **when** to call which — so you plan changes from real project context, not guessing. Always prefer the narrowest tool that answers the question.

## 1. BEFORE modifying code — scope the blast radius

Changing a function/module? First find everything it touches so you don't break callers.

- **`saw_impact`** / **`saw_blast_radius`** — "what does changing X affect?" Returns dependents/blast radius. Call this whenever you're about to edit a non-trivial symbol. High `risk_count` or depth > 1 → write a test for the affected callers too.
- **`saw_code_context`** — pull the surrounding context (definition + immediate usage) for a symbol you're editing. Use instead of grep when you need the *call sites with types*, not just string matches.
- **`saw_code_query`** / **`saw_code_search`** — semantic/graph lookup when you don't know the exact name (e.g. "where do claims get their confidence set?").
- **`saw_navigate`** — walk the code graph (callers → callees) to trace an execution path before refactoring it.

**Workflow**: `saw_impact` (what breaks) → `saw_code_context` (what the symbol is now) → edit → §3 verify.

## 2. Check staleness — is the cached knowledge still valid?

SAW's claims/wiki can go stale. Before trusting retrieved context:

- **`saw_freshness`** — freshness distribution (0–8 levels). If a claim you're about to cite is at level 6+ (aging) or 8 (stale), re-ingest the source first.
- **`saw_status`** — overall engine/DB health before a heavy operation.
- **`saw_conflicts`** — are there known contradictions on the claims you're relying on? Don't build on a contradicted premise.

## 3. AFTER changes — verify and publish

- **`saw_verify`** — provenance chain for a claim (trace to Vault source). Cite this when the change touches claims.
- **`saw_lint`** / **`saw_wiki_lint`** — lint the wiki (orphan/broken links) after editing wiki pages.
- **`saw_audit`** — full audit (orphans + broken links + coverage gaps) for a release-gate pass.
- **`saw_compile`** / **`saw_wiki_compile`** — recompile the wiki from claims after structural changes.
- **`saw_ingest`** — ingest new/updated source docs so the knowledge base reflects the change.

## 4. Quick decision table

| You want to… | Call |
|---|---|
| Know what breaks if I change X | `saw_impact` (then `saw_code_context`) |
| Find where a concept lives in code | `saw_code_query` / `saw_code_search` |
| Check if my cited claim is stale | `saw_freshness` + `saw_conflicts` |
| Verify a claim traces to source | `saw_verify` |
| Lint wiki after edits | `saw_lint` / `saw_audit` |
| Recompile wiki from claims | `saw_wiki_compile` |
| Ingest a new doc | `saw_ingest` |
| Browse the code graph | `saw_graph_overview` / `saw_navigate` |

## 5. Anti-patterns

- ❌ Editing a symbol without `saw_impact` first → silent breakage of depth>1 callers.
- ❌ Trusting a retrieved claim without `saw_freshness` → acting on stale knowledge.
- ❌ Using `saw_search` (keyword) when you need *callers with types* → use `saw_code_context`/`saw_impact` instead.
- ❌ Skipping `saw_lint`/`saw_audit` after wiki edits → leaving broken `[[links]]`.
