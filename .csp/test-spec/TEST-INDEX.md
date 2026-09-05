# Test Index — TMS 索引

> 全部模块测试说明书。每条 PRD AC ≥1 用例；未映射 AC 在 COVERAGE-REPORT 显式标缺口。

| module | slug | 用例数 | AC 覆盖 | 状态 | file |
|---|---|---|---|---|---|
| e2e-usability | e2e-usability | 11 | AC-E2E-1/2, AC-TEST-2(部分) | ready | TMS-e2e-usability.md |
| claim-alignment | claim-alignment | 6 | AC-ALIGN-1/2 | ready | TMS-claim-alignment.md |
| security-hardening | security-hardening | 10 | AC-SEC-1/2/3 | ready | TMS-security-hardening.md |
| observability | observability | 6 | AC-OBS-1/2 | ready | TMS-observability.md |
| test-gate | test-gate | 6 | AC-TEST-1/2 | ready | TMS-test-gate.md |

## 汇总
- 用例总数：39
- PRD AC 覆盖：11/11（AC-E2E-1/2, AC-ALIGN-1/2, AC-SEC-1/2/3, AC-OBS-1/2, AC-TEST-1/2）
- 状态：全 ready（边界已定）；[TBD] 项见各 TMS 缺口

## TMS 红线
- 继承 PMS 边界，不发明 PMS 未声明模块。
- 变更只产 delta 增量用例，不推倒重来。

## 05 增量（2026-09-01，feat/hardening-wave1-slice）
- 新增 30 用例：e2e-usability +5（F-A-1）、claim-alignment +4（F-B-1）、security-hardening +21（F-C-3 ×6, F-C-4 ×15）。
- 用例总数：39 → 69。
- 新覆盖 AC：AC-SEC-1（URL guard track）/ AC-SEC-3（限流 429）/ AC-ALIGN-1（宣称 diff）/ AC-E2E-1（冒烟骨架 partial）。
- ruff 未跑（未装，[TBD]）；coverage 基线 deferred（T-F-E-1-1）。

## v1.10.0 delta（embedding 语义搜索）
- 模块：embedding（PMS-embedding），ADR-010 向量存储 + 检索融合。
- 新增 12 AC（AC-EMB-1/2/3, AC-SEM-1/2/3, AC-LINK-1/2/3, AC-TEST-1/2/3），全映射。
- 测试文件：test_embedding_index.py（importorskip）、test_semantic_search.py（importorskip）、test_related_pages_embedding.py（importorskip）、test_embedding_degradation.py（mock 降级）、test_ci_workflow.py（扩）。
- 用例总数：69 → 69 + 12 = 81（[TBD-impl] 实施后落定）。
- 新覆盖 AC：AC-EMB-1/2/3, AC-SEM-1/2/3, AC-LINK-1/2/3, AC-TEST-1/2/3（12 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.10.0.md`。

## v1.11.0 delta（债务收口 IV / bug fix）
- 模块：debt-closure（PMS-debt-closure），ADR-011 semantic search cache 策略。
- 新增 12 AC（AC-CACHE-1/2/3/4, AC-COV-1/2, AC-WF-1/2/3, AC-SPEC-1/2, AC-HASH-1），全映射。
- 测试文件：test_semantic_cache.py（mock，无 SDK）、tests/unit/engines/compile/（新建 7 文件 + conftest，20 用例）、test_workflow_rest_db.py（in-memory DB）、test_spec_naming.py（grep + subprocess）、test_hash_consistency.py（git rev-list）。
- 用例总数：81 → 81 + 12 = 93（[TBD-impl] 实施后落定）。
- 新覆盖 AC：AC-CACHE-1/2/3/4, AC-COV-1/2, AC-WF-1/2/3, AC-SPEC-1/2, AC-HASH-1（12 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.11.0.md`。

## v1.12.0 delta（embedding API 重构）
- 模块：embedding-api（PMS-embedding-api），ADR-012 embedding provider 选型 litellm API + 本地 ST fallback。
- 新增 9 AC（AC-EA-1/2, AC-DIM-1/2, AC-FB-1/2, AC-TEST-1/2/3），全映射。
- 测试文件：test_embedding_index.py（改 API mock，去 importorskip）、test_semantic_search.py（改 API mock，去 importorskip）、test_related_pages_embedding.py（改 API mock，去 importorskip）、test_embedding_degradation.py（扩 API 不可用场景）、test_ci_workflow.py（扩 importorskip 检测更新）、test_embedding_benchmark.py（新建 benchmark）。
- 用例总数：93 → 93 + 9 = 102（[TBD-impl] 实施后落定）。
- 新覆盖 AC：AC-EA-1/2, AC-DIM-1/2, AC-FB-1/2, AC-TEST-1/2/3（9 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.12.0.md`。
