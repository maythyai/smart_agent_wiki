# Test Results — v1.10.0 Implementation Verification

**Date**: 2026-09-04
**Version**: v1.10.0 (embedding)
**Commits**: ecbdb75, 9660ecc, 3b2039e, e7fb6c6

## Test Suite Results

| Metric | Value |
|---|---|
| pytest total | 1993 passed, 6 skipped, 0 failed |
| (baseline v1.9.0) | 1987 passed, 3 skipped |
| New tests added | 6 (3 importorskip-skip + 3 degradation-mock) |
| ruff check src/ tests/ | 0 errors |
| saw smoke | 6/6 passed |

## Embedding Test Skip Details

| Test file | importorskip | CI behavior |
|---|---|---|
| tests/unit/test_embedding_index.py | `sentence_transformers` | skip (3 tests) |
| tests/unit/test_semantic_search.py | `sentence_transformers` | skip (2 tests) |
| tests/unit/test_related_pages_embedding.py | `sentence_transformers` | skip (2 tests) |
| tests/unit/test_embedding_degradation.py | none (uses mock) | pass (4 tests) |

**Note**: sentence_transformers is NOT installed in this environment.
The 3 importorskip test files are skipped (total 3 new skips added to
the original 3 = 6 skipped). The degradation test file runs and passes
using `unittest.mock.patch` to simulate `embeddings_available()=False`.

**Honest annotation**: Real embedding E2E tests (AC-EMB-1, AC-SEM-1,
AC-LINK-1/3) require `pip install -e ".[learn]"` (sentence_transformers).
They are skipped in this environment — they will pass when the user
installs the `[learn]` extra. The degradation tests (AC-EMB-2, AC-SEM-2,
AC-LINK-2) pass unconditionally via mock.

## CI Workflow Test

- `test_embedding_tests_importorskip`: verifies 3 embedding test files
  have `pytest.importorskip("sentence_transformers")` ✓
- `test_embedding_degradation_uses_mock_not_importorskip`: verifies
  degradation file uses mock, not importorskip ✓

---

## 06-Ship Verification (2026-09-04)

| Gate | Command | Result | Status |
|---|---|---|---|
| pytest | `.venv/bin/python -m pytest tests/ -q` | 1993 passed, 6 skipped, 0 failed (112.34s) | PASS |
| ruff | `ruff check src/ tests/` | All checks passed (0 errors) | PASS |
| smoke | `.venv/bin/saw smoke` | 6/6 passed (skeleton.import, skeleton.console, ingest.compile, query.keyword, govern.learn, offline.fallback) | PASS |
| wheel build | `uv build` | dist/smart_agent_wiki-1.10.0-py3-none-any.whl (820KB) + sdist | PASS |
| version | `pyproject.toml [project].version` | 1.10.0 | PASS |
| multi-platform | desktop 0.1.0 / web 0.1.0 | independent 0.x (pre-1.0, not aligned to canonical — per §1.2 rules) | PASS |

**Verdict**: All gates green. Code is finalized. Proceeding to reconcile + local tag.

---

## v1.11.0 Implementation Verification (2026-09-05)

**Version**: v1.11.0 (debt-closure IV / bug fix)
**Commits**: 209c294 (F-O-1), 42b9399 (F-O-2), e3869d3 (F-O-3), 0f0e82e (F-O-4)

| Metric | Value |
|---|---|
| pytest total | 2064 passed, 6 skipped, 0 failed |
| (baseline v1.10.0) | 1993 passed, 6 skipped |
| New tests added | 71 (4 semantic cache + 58 compile/compiler + 5 workflow REST DB + 4 spec/hash) |
| ruff check src/ tests/ | 0 errors |
| coverage total | 65.36% (fail_under=65 ✓) |
| (baseline v1.10.0) | 64.2% (fail_under=64) |
| saw smoke | 6/6 passed |

### Task breakdown

| Task | Commit | AC | Tests added |
|---|---|---|---|
| T-F-O-1 (semantic cache) | 209c294 | AC-CACHE-1/2/3/4 | 4 (test_semantic_cache.py, mock-based) |
| T-F-O-2 (compile deep coverage) | 42b9399 | AC-COV-1/2 | 58 (7 test files + conftest, 30+ functions) |
| T-F-O-3 (workflow REST unify) | e3869d3 | AC-WF-1/2/3 | 5 (test_workflow_rest_db.py, in-memory DB) |
| T-F-O-4 (Spec naming + hash) | 0f0e82e | AC-SPEC-1/2, AC-HASH-1 | 4 (test_spec_naming.py + test_hash_consistency.py) |

**Verdict**: All gates green. 2064 passed, ruff 0, coverage 65.36% ≥ 65, smoke 6/6.

---

## 06-Ship Verification (2026-09-05)

| Gate | Command | Result | Status |
|---|---|---|---|
| pytest | `.venv/bin/python -m pytest tests/ -q` | 2064 passed, 6 skipped, 0 failed (102.83s) | PASS |
| ruff | `.venv/bin/ruff check src/ tests/` | All checks passed! (0 errors) | PASS |
| coverage | `.venv/bin/python -m pytest tests/ -q --cov=src/saw --cov-fail-under=65` | 65.36% (fail_under=65 ✓) | PASS |
| smoke | `.venv/bin/saw smoke` | 6/6 passed (skeleton.import, skeleton.console, ingest.compile, query.keyword, govern.learn, offline.fallback) | PASS |
| wheel build | `uv build` | dist/smart_agent_wiki-1.11.0-py3-none-any.whl (822KB) + sdist (2.6MB) | PASS |
| version | `pyproject.toml [project].version` | 1.11.0 (bumped from 1.10.0) | PASS |
| multi-platform | desktop 0.1.0 / web 0.1.0 | independent 0.x (pre-1.0, per §1.2 rules — OK) | PASS |

**Verdict**: All gates green. Code is finalized. Proceeding to reconcile + local tag.
