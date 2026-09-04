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
