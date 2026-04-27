---
phase: 02-intelligence-governance
plan: 02
subsystem: [govern, crypto, cli]
tags: [contradiction-detection, blast-radius, ed25519, audit-trail, conflicts, receipts]

# Dependency graph
requires: [02-01]
provides:
  - "Contradiction Detection: ContradictionDetector with two-phase detection"
  - "Blast Radius Analysis: BlastRadiusAnalyzer for edit impact"
  - "Audit Trail: AuditTrail with Ed25519 signed receipts"
  - "CLI Commands: saw conflicts, saw audit"
affects: []

# Tech tracking
tech-stack:
  added: [PyNaCl]
  patterns: [two-phase-contradiction-detection, blast-radius-scoring, receipt-chain, ed25519-signing]

key-files:
  created:
    - src/saw/engines/govern/contradiction.py
    - src/saw/engines/govern/blast_radius.py
    - src/saw/engines/govern/audit.py
    - src/saw/adapters/crypto/__init__.py
    - src/saw/adapters/crypto/ed25519.py
    - src/saw/drivers/cli/commands/conflicts_cmd.py
    - src/saw/drivers/cli/commands/audit_cmd.py
    - tests/unit/engines/govern/test_contradiction.py
    - tests/unit/engines/govern/test_blast_radius.py
    - tests/unit/engines/govern/test_audit.py
    - tests/unit/adapters/crypto/test_ed25519.py
    - tests/integration/test_advanced_governance_cli.py
  modified:
    - src/saw/domain/value_objects.py
    - src/saw/domain/events.py
    - src/saw/engines/govern/__init__.py
    - src/saw/drivers/cli/main.py

key-decisions:
  - "Three contradiction types: TEMPORAL (new beats old), OPINION (both preserved), FACTUAL (human review)"
  - "Resolution strategies: SUPERSEDED for TEMPORAL, DISPUTED for OPINION, HISTORICAL for FACTUAL"
  - "Two-phase detection: keyword/semantic filter -> LLM classification"
  - "Async queue for background detection (per D-06)"
  - "Blast radius score 0-100: Low (0-30), Medium (31-70), High (71-100)"
  - "Ed25519 key stored with 0600 permissions per PITFALLS.md"
  - "Receipt chain via prev_receipt_id for offline verification"

patterns-established:
  - "ContradictionDetector: detect_candidates() -> classify_contradiction() -> resolve_contradiction()"
  - "BlastRadiusAnalyzer: analyze() returns BlastRadiusReport with risk_score and recommendation"
  - "AuditTrail: record_operation() creates signed Receipt, chains to previous"
  - "ReceiptSigner: generate_keypair() -> sign_receipt() -> verify_receipt()"

requirements-completed: [GOVE-03, GOVE-04, GOVE-07, GOVE-08, CLI-08, CLI-11]

# Metrics
duration: 35min
completed: 2026-04-27
---
# Phase 02 Plan 02: Advanced Governance Summary

**Contradiction detection with 3-strategy resolution, blast radius analysis for edit impact, and Ed25519 cryptographic audit trail with signed receipts**

## Performance

- **Duration:** 35 min
- **Started:** 2026-04-27T00:00:00Z
- **Completed:** 2026-04-27T00:35:00Z
- **Tasks:** 4
- **Files modified:** 13

## Accomplishments

- **Contradiction Detection:**
  - ContradictionType enum (TEMPORAL/OPINION/FACTUAL) per D-08
  - ResolutionStrategy enum (SUPERSEDED/DISPUTED/HISTORICAL) per D-09
  - Two-phase detection: keyword filtering -> LLM classification
  - Async queue for background detection per D-06
  - SQLite storage for contradictions with blast radius tracking

- **Blast Radius Analysis:**
  - BlastRadiusAnalyzer identifies affected claims, pages, and entities
  - Risk score calculation (0-100): Low (0-30), Medium (31-70), High (71-100)
  - Recommendations: "safe to edit", "review required", "high impact"
  - Graph traversal integration for downstream entity detection

- **Ed25519 Audit Trail:**
  - ReceiptSigner with Ed25519 key generation and signing
  - Receipt dataclass with payload hash and chain linking
  - Key storage with 0600 permissions per PITFALLS.md
  - AuditTrail for receipt chain management
  - Chain verification detects tampering
  - Export for offline verification per GOVE-08

- **CLI Commands:**
  - `saw conflicts`: lists contradictions with type and resolution
  - `saw conflicts --unresolved`: filters to unresolved
  - `saw audit`: verifies receipt chain integrity
  - `saw audit --export`: exports for offline verification

- 68 new tests passing (17 contradiction + 14 blast_radius + 31 Ed25519/audit + 6 CLI)

## Task Commits

Each task was committed atomically:

1. **Task 1: Contradiction Detection and Resolution** - `bd1de16` (feat)
2. **Task 2: Blast Radius Analysis** - `d6ea2da` (feat)
3. **Task 3: Ed25519 Cryptographic Audit Trail** - `9bbcb77` (feat)
4. **Task 4: CLI Commands - conflicts and audit** - `9ade122` (feat)

## Files Created/Modified

### Contradiction Detection
- `src/saw/domain/value_objects.py` - Added ContradictionType and ResolutionStrategy enums
- `src/saw/domain/events.py` - Added ContradictionFound event
- `src/saw/engines/govern/contradiction.py` - ContradictionDetector with two-phase detection
- `tests/unit/engines/govern/test_contradiction.py` - 17 unit tests

### Blast Radius Analysis
- `src/saw/engines/govern/blast_radius.py` - BlastRadiusAnalyzer with impact scoring
- `tests/unit/engines/govern/test_blast_radius.py` - 14 unit tests

### Audit Trail
- `src/saw/adapters/crypto/__init__.py` - Module exports
- `src/saw/adapters/crypto/ed25519.py` - Ed25519 signing and verification
- `src/saw/engines/govern/audit.py` - AuditTrail and AuditSummary
- `tests/unit/adapters/crypto/test_ed25519.py` - 16 unit tests
- `tests/unit/engines/govern/test_audit.py` - 15 unit tests

### CLI Commands
- `src/saw/drivers/cli/commands/conflicts_cmd.py` - `saw conflicts` command
- `src/saw/drivers/cli/commands/audit_cmd.py` - `saw audit` command
- `src/saw/drivers/cli/main.py` - Registered conflicts and audit commands
- `tests/integration/test_advanced_governance_cli.py` - 6 integration tests

## Decisions Made

- Two-phase detection balances performance and accuracy: fast keyword filter reduces LLM calls
- Factual contradictions require human review (HISTORICAL strategy) rather than automatic resolution
- Blast radius score capped at 100 with three clear bands for user guidance
- Ed25519 chosen for signature speed and simplicity (vs RSA/ECDSA)
- Private key stored with 0600 permissions, recommend OS keychain for production

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

- Governance engine complete with confidence, freshness, lint, contradictions, blast radius, and audit
- `saw conflicts` and `saw audit` CLI commands functional
- Ed25519 receipts ready for integration with Write Queue
- Ready for Phase 02 Plan 03 (MCP Server)

## Self-Check: PASSED

- All 13 files verified present on disk
- All 4 task commits verified in git log (bd1de16, d6ea2da, 9bbcb77, 9ade122)
- All 220 tests passing (68 new + 152 existing)
- Zero warnings in pytest output

---

*Phase: 02-intelligence-governance*
*Completed: 2026-04-27*
