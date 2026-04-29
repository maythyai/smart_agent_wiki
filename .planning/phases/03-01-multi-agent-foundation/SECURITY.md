# Security Audit Report: Phase 03-01 Multi-Agent Foundation

**Audit Date:** 2026-04-28
**Auditor:** gsd-security-auditor
**ASVS Level:** L2
**Block On:** critical
**Re-audit:** Yes (after fixes for T-03-01-02, T-03-01-06)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Phase** | 03-01 - Multi-Agent Foundation |
| **Total Threats** | 10 |
| **Closed** | 10 |
| **Open** | 0 |
| **Accepted Risks** | 2 |

**Overall Status:** SECURED

---

## Threat Verification

### Closed Threats

| Threat ID | Category | Disposition | Evidence |
|-----------|----------|-------------|----------|
| T-03-01-01 | Spoofing | mitigate | src/saw/adapters/crypto/ed25519.py:177-208 - Ed25519 signature verification via `verify_receipt()`; src/saw/engines/collaborate/a2a_protocol.py:151-162 - Receipt signing on A2A messages |
| T-03-01-02 | Tampering | mitigate | src/saw/domain/agent.py:23 - `@dataclass(frozen=True)` prevents context tampering during transfer |
| T-03-01-03 | Repudiation | mitigate | src/saw/engines/govern/audit.py:70-121 - AuditTrail.record_operation() creates signed receipts; src/saw/engines/govern/audit.py:181-251 - verify_chain() provides offline verification |
| T-03-01-05 | Denial of Service | mitigate | src/saw/engines/collaborate/dispatcher.py:64-65 - `allowed_fails: int = 3`, `cooldown_time: int = 120` prevents aggressive cooldown |
| T-03-01-06 | Elevation of Privilege | mitigate | src/saw/engines/collaborate/agents/guardian.py:85-105 - Guardian checks `tools_allowed` before execution, blocks unauthorized tool access |
| T-03-01-08 | Tampering | mitigate | src/saw/engines/collaborate/workflow_parser.py:65-66, 123-145 - Validates required fields, valid fallback actions, unknown agents |
| T-03-01-09 | Denial of Service | mitigate | src/saw/engines/collaborate/workflow_executor.py:138 - `asyncio.timeout(workflow.timeout)`; src/saw/engines/collaborate/workflow_parser.py:34 - `max_retries: int = 3` default |
| T-03-01-10 | Elevation of Privilege | mitigate | src/saw/engines/collaborate/orchestrator.py:103-119 - Cedar policy `evaluate()` check before dispatch_agent; src/saw/adapters/crypto/cedar_policy.py:324-335 - Default deny on error |
| T-03-01-11 | Tampering | mitigate | src/saw/engines/collaborate/workflow_parser.py:174-191 - `_validate_gate()` uses strict regex `^(>=|<=|==|!=|>|<)\s*\d+$` for gate conditions |

### Accepted Risks

| Threat ID | Category | Rationale | Reviewed By |
|-----------|----------|-----------|-------------|
| T-03-01-04 | Information Disclosure | System prompts contain no sensitive information; user data passed via context | Plan 03-01-01 |
| T-03-01-12 | Information Disclosure | Workflow context contains only workflow state, no sensitive data | Plan 03-01-02 |

---

## Verification Details

### T-03-01-01: Ed25519 Signature Verification

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/adapters/crypto/ed25519.py`
  - Line 177-208: `verify_receipt()` method uses PyNaCl VerifyKey for Ed25519 signature verification
  - Line 156-175: `sign_receipt()` method signs receipts with Ed25519
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/a2a_protocol.py`
  - Lines 151-162: A2AAdapter generates signed receipt for messages when signer is available

### T-03-01-02: AgentContext Frozen (RE-AUDIT)

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/domain/agent.py`
  - Line 23: `@dataclass(frozen=True)` decorator now present
  - Lines 24-36: AgentContext is now immutable, preventing tampering during agent transfer

### T-03-01-03: Audit Receipts

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/govern/audit.py`
  - Lines 70-121: `record_operation()` creates signed receipt with payload hash, chains to previous receipt
  - Lines 181-251: `verify_chain()` validates all signatures and chain linkage
  - Lines 308-332: `export_for_verification()` enables offline verification

### T-03-01-05: Rate Limit Protection

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/dispatcher.py`
  - Lines 56-67: DispatcherConfig with `allowed_fails: int = 3` and `cooldown_time: int = 120`
  - Comment at line 4: References PITFALLS.md Pitfall 2 for preventing aggressive cooldown

### T-03-01-06: Guardian Tool Access Check (RE-AUDIT)

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/agents/guardian.py`
  - Lines 85-105: Guardian.execute() now checks `tools_allowed` before rule evaluation
  - Line 93-96: Extracts tool name from action and verifies against allowed_tools
  - Lines 97-105: Returns `success=False` with `tool_check_failed=True` if tool not allowed

### T-03-01-08: YAML Workflow Validation

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/workflow_parser.py`
  - Lines 65-66: `REQUIRED_STEP_FIELDS` and `VALID_FALLBACK_ACTIONS` constants
  - Lines 123-134: Validates required fields and fallback_action values
  - Lines 147-172: `validate()` method checks unknown agents and gate syntax

### T-03-01-09: Workflow Loop Prevention

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/workflow_executor.py`
  - Line 138: `async with asyncio.timeout(workflow.timeout):` enforces timeout
  - Lines 154-166: TimeoutError handling returns proper status
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/workflow_parser.py`
  - Line 34: `max_retries: int = 3` default prevents infinite retry loops

### T-03-01-10: Cedar Policy Check

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/orchestrator.py`
  - Lines 103-119: `dispatch_agent()` checks Cedar policy before dispatch when `enable_policy_check=True`
  - Lines 196-226: `check_policy()` method for explicit policy queries
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/adapters/crypto/cedar_policy.py`
  - Lines 324-335: Default deny policy - returns `allowed=False` on any error

### T-03-01-11: Gate Condition Validation

**Files Verified:**
- `/mnt/g/chensai/example_llm_wikis/smart_agent_wiki/src/saw/engines/collaborate/workflow_parser.py`
  - Lines 174-191: `_validate_gate()` method with strict regex validation
  - Line 189: Regex pattern `^(>=|<=|==|!=|>|<)\s*\d+$` only allows valid operators and integers

---

## Unregistered Flags

None. All threat flags from SUMMARY.md are mapped to existing threat IDs.

---

## Appendix: Verification Commands

```bash
# Ed25519 signing verification
grep -n "verify_receipt\|sign_receipt" src/saw/adapters/crypto/ed25519.py

# AgentContext frozen check
grep -n "frozen=True" src/saw/domain/agent.py

# Guardian tool check
grep -n "tools_allowed" src/saw/engines/collaborate/agents/guardian.py

# Rate limit configuration
grep -n "allowed_fails\|cooldown_time" src/saw/engines/collaborate/dispatcher.py

# Workflow validation
grep -n "validate\|REQUIRED_STEP_FIELDS" src/saw/engines/collaborate/workflow_parser.py

# Cedar policy integration
grep -n "evaluate\|check_policy" src/saw/engines/collaborate/orchestrator.py

# Gate condition validation
grep -n "_validate_gate\|re.match" src/saw/engines/collaborate/workflow_parser.py

# Workflow timeout
grep -n "asyncio.timeout\|max_retries" src/saw/engines/collaborate/workflow_executor.py
```