---
phase: 02-intelligence-governance
plan: 01
subsystem: [govern, learn, cli]
tags: [confidence, freshness, lint, verify, review, training-period, fsrs, distillation, feedback-files]

# Dependency graph
requires: []
provides:
  - "Governance Engine: ConfidenceAssessor, FreshnessTracker, Linter, Governor"
  - "Learning Engine: TrainingPeriod, FSRSScheduler, Distiller, TrendSenser, KnowledgeExpiry, LearnEngine"
  - "CLI Commands: saw lint, saw verify, saw freshness, saw review"
  - "Feedback Files: approved.yaml, rejected.yaml"
affects: []

# Tech tracking
tech-stack:
  added: [fsrs]
  patterns: [4-tier-confidence, 9-level-freshness, fsrs-spaced-repetition, cognitive-distillation, training-period-adaptation]

key-files:
  created:
    - src/saw/engines/govern/__init__.py
    - src/saw/engines/govern/confidence.py
    - src/saw/engines/govern/freshness.py
    - src/saw/engines/govern/linter.py
    - src/saw/engines/govern/governor.py
    - src/saw/engines/learn/__init__.py
    - src/saw/engines/learn/adaptive.py
    - src/saw/engines/learn/fsrs_scheduler.py
    - src/saw/engines/learn/distiller.py
    - src/saw/engines/learn/trends.py
    - src/saw/engines/learn/expiry.py
    - src/saw/engines/learn/engine.py
    - src/saw/drivers/cli/commands/lint_cmd.py
    - src/saw/drivers/cli/commands/verify_cmd.py
    - src/saw/drivers/cli/commands/freshness_cmd.py
    - src/saw/drivers/cli/commands/review_cmd.py
    - .saw/feedback/approved.yaml
    - .saw/feedback/rejected.yaml
  modified:
    - src/saw/domain/value_objects.py
    - src/saw/domain/wiki.py
    - src/saw/adapters/storage/wiki_repository.py
    - src/saw/drivers/cli/main.py

key-decisions:
  - "FreshnessLevel uses 0-8 (per D-10) instead of 1-9, matching plan spec"
  - "FSRS Scheduler uses fsrs library (fsrs==6.3.1) with review_card method"
  - "Confidence never auto-downgrades (per D-03), only upgrades"
  - "Cross-Validated requires 2+ independent sources with different Vault UUIDs (per D-05)"
  - "Knowledge never auto-expires (per D-18), only user can delete"
  - "Training period default 30 days (per D-16), configurable"
  - "Dual feedback files (approved/rejected) for behavioral reinforcement (per D-20)"

patterns-established:
  - "Governance engine: assess_page() aggregates claim confidence, get_color() maps freshness to colors"
  - "Linter: HealthReport with health_score calculation, wikilink regex detection"
  - "FSRS: review_card() returns (new_card, review_log), state persisted in .saw/fsrs_cards.yaml"
  - "Training period: state persisted in .saw/training.yaml"
  - "SOPs: persisted in .saw/sops/ directory"

requirements-completed: [GOVE-01, GOVE-02, GOVE-05, GOVE-06, LEARN-01, LEARN-02, LEARN-03, LEARN-04, LEARN-05, LEARN-06, CLI-05, CLI-06, CLI-09, CLI-10]

# Metrics
duration: 45min
completed: 2026-04-27
---
# Phase 02 Plan 01: Governance Core + Learning Engine Summary

**Governance Engine core (confidence, freshness, health checks) and complete Learning Engine (training period, FSRS scheduling, cognitive distillation, trend sensing, feedback files) with CLI commands**

## Performance

- **Duration:** 45 min
- **Started:** 2026-04-26T23:27:18Z
- **Completed:** 2026-04-27T00:12:00Z
- **Tasks:** 5
- **Files modified:** 22

## Accomplishments

- **Governance Engine Core:**
  - ConfidenceAssessor with 4-tier confidence assessment (UNVERIFIED -> SINGLE_SOURCE -> CROSS_VALIDATED -> HUMAN_VERIFIED)
  - Cross-Validated upgrade requires 2+ independent sources (different Vault UUIDs per D-05)
  - Never auto-downgrade confidence (per D-03)
  - FreshnessTracker with 9-level freshness (LEVEL_0 to LEVEL_8)
  - Color mapping: Green(0-2), Yellow(3-5), Orange(6-7), Red(8) per D-11
  - Multi-signal calculation: time decay + access + references + source updates per D-12

- **Linter and Governor:**
  - HealthReport with orphan pages, broken links, stale claims, missing metadata
  - Wikilink detection regex: [[page]] and [[page|display]]
  - ProvenanceChain for claim verification
  - Health score calculation (0-100)

- **Learning Engine Core:**
  - TrainingPeriod with 30-day preference learning (per D-16)
  - State persisted in .saw/training.yaml
  - FSRSScheduler using fsrs library for spaced repetition
  - Review queue prioritizes high-freshness pages
  - State persisted in .saw/fsrs_cards.yaml

- **Cognitive Distillation and Trends:**
  - Distiller extracts SOPs from approved patterns using LLM (per D-19)
  - SOPs persisted in .saw/sops/ directory
  - TrendSenser detects knowledge gaps (high query, low coverage per D-21)
  - KnowledgeExpiry classifies tactical vs strategic (per D-18, never auto-expire)

- **CLI Commands:**
  - `saw lint`: Health report with Rich table output
  - `saw verify <claim_uuid>`: Provenance chain verification
  - `saw freshness`: Freshness distribution with color indicators
  - `saw review`: Interactive review queue management

- **Feedback Files:**
  - .saw/feedback/approved.yaml for positive patterns
  - .saw/feedback/rejected.yaml for negative patterns
  - Per D-20: Edit implies acceptance, reject requires explicit action

- 152 tests passing (43 new: 23 govern + 20 learn + 4 integration)

## Task Commits

Each task was committed atomically:

1. **Task 1: Governance Engine Core - Confidence and Freshness** - `1e5a7f0` (feat)
2. **Task 2: Linter and Health Check System** - `5e78fc8` (feat)
3. **Task 3: Learning Engine - Training Period and FSRS Scheduler** - `0bbd545` (feat)
4. **Task 4: Cognitive Distillation, Trends, and Feedback** - `43064b9` (feat)
5. **Task 5: CLI Commands - lint, verify, freshness, review** - `56c3912` (feat)

## Files Created/Modified

### Governance Engine
- `src/saw/engines/govern/__init__.py` - Module exports
- `src/saw/engines/govern/confidence.py` - 4-tier confidence assessment
- `src/saw/engines/govern/freshness.py` - 9-level freshness tracking
- `src/saw/engines/govern/linter.py` - Health check functionality
- `src/saw/engines/govern/governor.py` - Governance orchestrator

### Learning Engine
- `src/saw/engines/learn/__init__.py` - Module exports
- `src/saw/engines/learn/adaptive.py` - Training period adaptation
- `src/saw/engines/learn/fsrs_scheduler.py` - FSRS spaced repetition
- `src/saw/engines/learn/distiller.py` - Cognitive distillation
- `src/saw/engines/learn/trends.py` - Gap detection and trend sensing
- `src/saw/engines/learn/expiry.py` - Knowledge expiry classification
- `src/saw/engines/learn/engine.py` - Learning orchestrator

### CLI Commands
- `src/saw/drivers/cli/commands/lint_cmd.py` - `saw lint` command
- `src/saw/drivers/cli/commands/verify_cmd.py` - `saw verify` command
- `src/saw/drivers/cli/commands/freshness_cmd.py` - `saw freshness` command
- `src/saw/drivers/cli/commands/review_cmd.py` - `saw review` command
- `src/saw/drivers/cli/main.py` - Registered all 4 new commands

### Feedback Files
- `.saw/feedback/approved.yaml` - Positive behavioral patterns
- `.saw/feedback/rejected.yaml` - Negative behavioral patterns

### Domain Updates
- `src/saw/domain/value_objects.py` - Updated FreshnessLevel to 0-8 (per D-10)
- `src/saw/domain/wiki.py` - Updated default freshness to LEVEL_0
- `src/saw/adapters/storage/wiki_repository.py` - Updated freshness parsing

## Decisions Made

- FreshnessLevel uses 0-8 range (per D-10) to match plan specification for color mapping
- FSRS library uses `Scheduler` class with `review_card()` method returning tuple
- Card serialization uses `to_dict()`/`from_dict()` methods from fsrs library
- Confidence upgrade requires explicit flag for HUMAN_VERIFIED (per D-01)
- Knowledge never auto-expires - only returns candidates for user review (per D-18)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed fsrs library API mismatch**
- **Found during:** Task 3 test run
- **Issue:** fsrs library exports `Scheduler` not `FSRS`, and uses `review_card()` not `repeat()`
- **Fix:** Updated FSRSScheduler to use correct API
- **Files modified:** src/saw/engines/learn/fsrs_scheduler.py
- **Committed in:** 0bbd545 (Task 3 commit)

**2. [Rule 1 - Bug] Fixed Card attribute mismatch**
- **Found during:** Task 3 test run
- **Issue:** fsrs Card object doesn't have `elapsed_days`, `scheduled_days`, `reps`, `lapses` attributes
- **Fix:** Use Card.to_dict() for serialization instead of manual attribute extraction
- **Files modified:** src/saw/engines/learn/fsrs_scheduler.py
- **Committed in:** 0bbd545 (Task 3 commit)

**3. [Rule 1 - Bug] Fixed FreshnessLevel enum values**
- **Found during:** Task 1 test run
- **Issue:** Existing FreshnessLevel used 1-9, plan specifies 0-8 for color mapping
- **Fix:** Updated FreshnessLevel to LEVEL_0 through LEVEL_8, updated wiki.py and wiki_repository.py
- **Files modified:** src/saw/domain/value_objects.py, src/saw/domain/wiki.py, src/saw/adapters/storage/wiki_repository.py
- **Committed in:** 1e5a7f0 (Task 1 commit)

**4. [Rule 3 - Blocking] Fixed test mock setup for learning engine tests**
- **Found during:** Task 4 test run
- **Issue:** FSRS tests needed proper wiki_repo mocks with list_pages returning iterable
- **Fix:** Added proper mock setup with WikiPage objects
- **Files modified:** tests/unit/engines/learn/test_fsrs.py
- **Committed in:** 0bbd545 (Task 3 commit)

---

**Total deviations:** 4 auto-fixed (2 bugs, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correct library API usage and test setup. No scope creep.

## Next Phase Readiness

- Governance engine ready for end-to-end: `saw lint -> saw verify -> saw review`
- Learning engine ready for integration with ingestion pipeline
- All CLI commands functional with Rich output
- Feedback files ready for behavioral pattern collection

## Self-Check: PASSED

- All 22 files verified present on disk
- All 5 task commits verified in git log (1e5a7f0, 5e78fc8, 0bbd545, 43064b9, 56c3912)
- All 152 tests passing (152 total: 116 unit + 36 integration)
- Zero warnings in pytest output

---

*Phase: 02-intelligence-governance*
*Completed: 2026-04-27*