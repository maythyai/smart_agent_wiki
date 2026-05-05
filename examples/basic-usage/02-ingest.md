# Example 02: Ingest Documents

Learn how to add documents to your Smart Agent Wiki.

## Basic Ingestion

```bash
# Single file
saw ingest document.pdf

# Markdown file
saw ingest notes.md

# URL (extracts content automatically)
saw ingest https://example.com/blog/article

# Directory (all supported files)
saw ingest ./documents/

# Recursive directory
saw ingest ./library/ --recursive
```

## Supported Formats

| Format | Extension | Processing Method |
|--------|-----------|-------------------|
| Markdown | `.md` | LLM extraction (entities, claims) |
| PDF | `.pdf` | Docling → PyMuPDF parsing |
| URL | — | Trafilatura extraction |
| Python | `.py` | AST parsing (zero LLM) |
| JavaScript | `.js` | AST parsing (zero LLM) |
| TypeScript | `.ts` | AST parsing (zero LLM) |
| JSON | `.json` | Schema parsing |
| YAML | `.yaml` | Schema parsing |

## Output

```
Ingesting ./documents/...

[1/5] Processing meeting-notes.md
  → 12 claims extracted
  → 3 entities identified
  → Confidence: 0.85 (cross-validated)

[2/5] Processing project-plan.pdf
  → 28 claims extracted
  → 5 entities identified
  → Confidence: 0.72 (single-source)

[3/5] Processing https://example.com/article
  → Content extracted (2,450 words)
  → 15 claims extracted
  → Confidence: 0.68 (unverified)

[4/5] Processing utils.py
  → AST analysis (zero LLM)
  → 8 function signatures
  → 4 class definitions
  → Confidence: 0.95 (structure)

[5/5] Processing config.yaml
  → Schema parsed
  → 12 configuration items
  → Confidence: 0.95 (structure)

Summary:
  Documents: 5
  Claims: 63
  Entities: 8
  Time: 2.3s
```

## Ingest Options

```bash
# Offline mode (no LLM calls)
saw ingest document.pdf --no-llm
# Only structure extraction

# Force re-ingest
saw ingest document.pdf --force

# Batch with progress
saw ingest ./large-library/ --batch-size 100

# Specific processor
saw ingest document.pdf --processor pymupdf

# Set confidence manually
saw ingest notes.md --confidence 0.9 --source "verified"
```

## Confidence Levels

| Level | Label | Requirements |
|-------|-------|--------------|
| 4 | Human Verified | Manual review completed |
| 3 | Cross-Validated | Multiple sources confirm |
| 2 | Single Source | One document claims |
| 1 | Unverified | No source confirmation |

## Verifying Ingestion

```bash
saw status
```

```
Documents: 15
Claims: 142
  - Verified: 23 (16%)
  - Cross-validated: 45 (32%)
  - Single-source: 62 (43%)
  - Unverified: 12 (8%)

Wiki Pages: 23
Last Ingest: 2026-05-05 17:30
```

## Querying Ingested Documents

```bash
# Check what was extracted
saw query "meeting" --mode direct --limit 5
```

```
Results for "meeting":

[1] Weekly Sync Meeting Notes (confidence: 0.85)
    Source: meeting-notes.md
    Claims: 12 extracted
    → "Decision: Adopt microservices architecture"
    → "Action: Deploy to staging by Friday"

[2] Project Kickoff (confidence: 0.72)
    Source: project-plan.pdf
    Claims: 5 related
    → "Budget approved for Q2"
...
```

---

*Next: [03-query.md](./03-query.md) — Searching knowledge*