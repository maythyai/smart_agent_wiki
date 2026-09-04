# Backward Matrix — Spec → Feature → PRD

> 反向追溯：Spec → Feature → PRD 模块/AC。便于变更影响分析（改某 Spec → 找上游 PRD/Feature）。

| Spec | Feature | PRD 模块 | AC | PMS | CMS ref |
|---|---|---|---|---|---|
| SPEC-F-A-1 | F-A-1 | §3.1 | AC-E2E-1 | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-2 | F-A-2 | §3.1 | (链路) | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-3 | F-A-3 | §3.1 | (链路) | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-4 | F-A-4 | §3.1 | (链路) | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-5 | F-A-5 | §3.1 | AC-E2E-2 | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-6 | F-A-6 | §3.1 | AC-E2E-1, AC-TEST-2 | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-B-1 | F-B-1 | §3.2 | AC-ALIGN-1 | claim-alignment | entry-points.jsonl |
| SPEC-F-B-2 | F-B-2 | §3.2 | AC-ALIGN-2 | claim-alignment | entry-points.jsonl |
| SPEC-F-B-3 | F-B-3 | §3.2 | (历史标注) | claim-alignment | CODE-MODULE-SPEC |
| SPEC-F-C-1 | F-C-1 | §3.3 | AC-SEC-1 | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-2 | F-C-2 | §3.3 | AC-SEC-2 | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-3 | F-C-3 | §3.3 | AC-SEC-3 | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-4 | F-C-4 | §3.3 | (守卫) | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-5 | F-C-5 | §3.3 | (token) | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-D-1 | F-D-1 | §3.4 | AC-OBS-1 | observability | CODE-MODULE-SPEC |
| SPEC-F-D-2 | F-D-2 | §3.4 | AC-OBS-1 | observability | CODE-MODULE-SPEC |
| SPEC-F-D-3 | F-D-3 | §3.4 | AC-OBS-2 | observability | CODE-MODULE-SPEC |
| SPEC-F-E-1 | F-E-1 | §3.5 | (基线) | test-gate | [无] |
| SPEC-F-E-2 | F-E-2 | §3.5 | AC-TEST-1 | test-gate | [无] |
| SPEC-F-E-3 | F-E-3 | §3.5 | AC-TEST-2 | test-gate | [无] |

## v1.10.0 delta（embedding 语义搜索）

| Spec | Feature | PRD 模块 | AC | PMS | CMS ref | Commit |
|---|---|---|---|---|---|---|
| SPEC-F-N-1 | F-N-1 | §3.1 | AC-EMB-1/2/3 | embedding | CODE-MODULE-SPEC | ecbdb75 |
| SPEC-F-N-2 | F-N-2 | §3.2 | AC-SEM-1/2/3 | embedding | CODE-MODULE-SPEC | 9660ecc |
| SPEC-F-N-3 | F-N-3 | §3.3 | AC-LINK-1/2/3 | embedding | CODE-MODULE-SPEC | 3b2039e |
| SPEC-F-N-4 | F-N-4 | §3.4 | AC-TEST-1/2/3 | embedding | [无] | e7fb6c6 |
