---
phase: 01-core-data-cycle
plan: 02
subsystem: [ingest, llm, parsers, cli]
tags: [litellm, trafilatura, docling, pymupdf, ast, git-session-branch, typer]

# Dependency graph
requires:
  - phase: 01-core-data-cycle
    plan: 01
    provides: "Foundation layer - Write Queue, Claims DB, FTS5, CLI scaffold"
provides:
  - "LLM Router: LiteLLM unified interface with configurable extraction/query models"
  - "Prompt templates: YAML-based extraction and query prompts"
  - "Parsers: Markdown (frontmatter+headings), PDF (3-tier fallback), HTML (trafilatura)"
  - "Format Classifier: PDF/Markdown/URL/Code/JSON/Table routing"
  - "Extractors: Markdown, PDF, URL, CodeAST (zero LLM), LLM-based"
  - "Fuser: content_hash deduplication and contradiction flagging"
  - "Validator: field-level validation for claims, entities, relations"
  - "Ingest Pipeline: classify -> extract -> fuse -> validate -> enqueue"
  - "CLI ingest: saw ingest with --no-llm offline mode"
  - "Git session branches: create/merge/abort with --no-ff"
affects: [03-core-data-cycle, query-engine]

# Tech tracking
tech-stack:
  added: [litellm, trafilatura, docling, PyMuPDF, python-frontmatter, markdown-it-py]
  patterns: [llm-router, three-tier-pdf-fallback, zero-llm-ast, session-branch-provenance]

key-files:
  created:
    - src/saw/adapters/llm/__init__.py
    - src/saw/adapters/llm/router.py
    - src/saw/adapters/llm/prompts/__init__.py
    - src/saw/adapters/llm/prompts/extraction.yaml
    - src/saw/adapters/llm/prompts/query_default.yaml
    - src/saw/adapters/parsers/__init__.py
    - src/saw/adapters/parsers/markdown_parser.py
    - src/saw/adapters/parsers/pdf_parser.py
    - src/saw/adapters/parsers/html_parser.py
    - src/saw/engines/__init__.py
    - src/saw/engines/ingest/__init__.py
    - src/saw/engines/ingest/classifier.py
    - src/saw/engines/ingest/extractors/__init__.py
    - src/saw/engines/ingest/extractors/llm_extract.py
    - src/saw/engines/ingest/extractors/markdown.py
    - src/saw/engines/ingest/extractors/pdf.py
    - src/saw/engines/ingest/extractors/url.py
    - src/saw/engines/ingest/extractors/code_ast.py
    - src/saw/engines/ingest/fuser.py
    - src/saw/engines/ingest/validator.py
    - src/saw/engines/ingest/pipeline.py
    - src/saw/drivers/cli/commands/ingest_cmd.py
    - tests/unit/engines/ingest/__init__.py
    - tests/unit/engines/ingest/test_classifier.py
    - tests/unit/engines/ingest/test_extractors.py
    - tests/integration/test_ingest_flow.py
  modified:
    - src/saw/adapters/storage/vault_repository.py
    - src/saw/config/settings.py
    - src/saw/drivers/cli/main.py
    - src/saw/adapters/parsers/markdown_parser.py

key-decisions:
  - "CodeASTExtractor uses ast.parse for Python and regex for other languages - zero LLM"
  - "PDF parsing uses 3-tier fallback: Docling (intelligent) -> PyMuPDF (lightweight)"
  - "MarkdownParser uses markdown-it-py for heading hierarchy extraction"
  - "Session branches use subprocess git commands (pygit2 deferred for stability)"
  - "LLM extraction uses temperature=0.1 for stable output"

patterns-established:
  - "Three-tier degradation: LLM available -> LLM extraction, no LLM -> offline (headings/paragraphs)"
  - "Zero-LLM for structured data: code files extracted via AST only"
  - "content_hash deduplication in Fuser"
  - "Git session branch: session/{timestamp}-{sanitized_source_name}"

requirements-completed: [INGE-01, INGE-02, INGE-03, INGE-04, INGE-06, INGE-07, CLI-02, XCUT-01, XCUT-02, MCP-03]

# Metrics
duration: 22min
completed: 2026-04-26
---

# Phase 1 Plan 02: Ingestion Engine Summary

**LLM Router, parsers (PDF/Markdown/HTML), extractors, and CLI ingest command with Git session branch provenance**

## Performance

- **Duration:** 22 min
- **Started:** 2026-04-26T08:15:19Z
- **Completed:** 2026-04-26T08:37:xxZ
- **Tasks:** 3
- **Files modified:** 32

## Accomplishments

- LLM Router with LiteLLM integration, single-LLM mode (multi-LLM deferred to Phase 2)
- PDF parser with 3-tier fallback (Docling -> PyMuPDF) and quality validation
- Markdown parser with YAML frontmatter and heading hierarchy extraction
- HTML parser with trafilatura content extraction from URLs
- Format classifier routing all supported document types
- CodeASTExtractor for zero-LLM AST extraction from code files
- Fuser with content_hash deduplication
- Validator with field-level checks for claims, entities, relations
- IngestPipeline orchestrating classify -> extract -> fuse -> validate -> enqueue
- saw ingest CLI command with --no-llm offline mode
- Git session branch provenance with create/merge/abort
- 75 tests passing (29 new + 46 from Plan 01)

## Task Commits

Each task was committed atomically:

1. **Task 1: LLM Router + Parsers + Format Classifier** - `0b6705e` (feat)
2. **Task 2: Extractors + Fuser + Validator + Ingest Pipeline** - `e57ea3c` (feat)
3. **Task 3: CLI ingest command + Git session branches + Integration tests** - `eb943ef` (feat)

## Files Created/Modified

- `src/saw/adapters/llm/router.py` - LLMRouter with LiteLLM, extraction and query methods
- `src/saw/adapters/llm/prompts/extraction.yaml` - Claim extraction prompt template
- `src/saw/adapters/llm/prompts/query_default.yaml` - Query prompt template (placeholder)
- `src/saw/adapters/parsers/markdown_parser.py` - MarkdownParser with frontmatter + headings
- `src/saw/adapters/parsers/pdf_parser.py` - PDFParser with 3-tier fallback
- `src/saw/adapters/parsers/html_parser.py` - HTMLParser with trafilatura
- `src/saw/engines/ingest/classifier.py` - DocumentFormat enum and classify function
- `src/saw/engines/ingest/extractors/code_ast.py` - CodeASTExtractor (zero LLM)
- `src/saw/engines/ingest/extractors/markdown.py` - MarkdownExtractor
- `src/saw/engines/ingest/extractors/pdf.py` - PDFExtractor
- `src/saw/engines/ingest/extractors/url.py` - URLExtractor
- `src/saw/engines/ingest/extractors/llm_extract.py` - LLMExtractor
- `src/saw/engines/ingest/fuser.py` - Fuser with content_hash dedup
- `src/saw/engines/ingest/validator.py` - Validator
- `src/saw/engines/ingest/pipeline.py` - IngestPipeline orchestrator
- `src/saw/adapters/storage/vault_repository.py` - Added session branch methods
- `src/saw/config/settings.py` - Added SUPPORTED_EXTENSIONS and scan_directory
- `src/saw/drivers/cli/commands/ingest_cmd.py` - saw ingest command
- `src/saw/drivers/cli/main.py` - Registered ingest command

## Decisions Made

- CodeASTExtractor uses Python ast.parse for .py files and regex patterns for other languages (JS/TS/Rust/Go/Java)
- PDF parsing uses Docling for intelligent layout analysis, PyMuPDF as lightweight fallback
- Session branches use subprocess git commands instead of pygit2 for stability and simpler error handling
- LLM extraction temperature=0.1 for stable, reproducible outputs
- Offline mode creates claims from headings and paragraphs without LLM

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed MarkdownParser heading extraction**
- **Found during:** Task 2 test run
- **Issue:** Heading extraction logic was incorrect - checking wrong token sequence
- **Fix:** Changed from checking `tokens[i+1].type == "heading_close"` to correctly finding inline token after heading_open
- **Files modified:** src/saw/adapters/parsers/markdown_parser.py
- **Verification:** test_extract_without_llm_offline_mode passes
- **Committed in:** e57ea3c (Task 2 commit)

**2. [Rule 1 - Bug] Fixed validator.py syntax error**
- **Found during:** Task 2 file write
- **Issue:** `from __future__ from annotations` typo (should be `import`)
- **Fix:** Corrected to `from __future__ import annotations`
- **Files modified:** src/saw/engines/ingest/validator.py
- **Committed in:** e57ea3c (Task 2 commit)

**3. [Rule 3 - Blocking] Fixed integration test fixture**
- **Found during:** Task 3 test run
- **Issue:** Test fixture created simplified DB schema that conflicted with ClaimsRepository schema init
- **Fix:** Let ClaimsRepository and WriteQueue initialize their own schemas, removed manual schema creation from fixture
- **Files modified:** tests/integration/test_ingest_flow.py
- **Verification:** All 4 integration tests pass
- **Committed in:** eb943ef (Task 3 commit)

**4. [Rule 3 - Blocking] Fixed FTS5 sink injection in tests**
- **Found during:** Task 3 test run
- **Issue:** FTS5Sink was passed ClaimsRepository instead of Connection
- **Fix:** Changed to pass Connection directly to FTS5Sink
- **Files modified:** tests/integration/test_ingest_flow.py
- **Committed in:** eb943ef (Task 3 commit)

---

**Total deviations:** 4 auto-fixed (2 bugs, 2 blocking)
**Impact on plan:** All auto-fixes necessary for test correctness. No scope creep.

## User Setup Required

- LLM API key (optional): Set OPENAI_API_KEY or ANTHROPIC_API_KEY for LLM extraction
- Git (optional): For session branch provenance

## Next Phase Readiness

- Ingestion engine ready for Plan 03 (Query Engine) to consume claims
- Claims DB populated with extracted claims from various document formats
- FTS5 index updated for search operations
- Entity and relation graph populated
- CLI scaffold ready for query and search commands

---

*Phase: 01-core-data-cycle*
*Completed: 2026-04-26*

## Self-Check: PASSED

- All 32 files verified present on disk
- All 3 task commits verified in git log (0b6705e, e57ea3c, eb943ef)
- All 75 tests passing with zero warnings
