# Forward Matrix — PRD → Feature → Spec

> 正向追溯：PRD 模块/AC → decomposition Feature → Spec。PRD `product-hardening-v1`。

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 e2e-usability | AC-E2E-1 | F-A-1, F-A-6 | SPEC-F-A-1, SPEC-F-A-6 |
| §3.1 | AC-E2E-2 | F-A-5 | SPEC-F-A-5 |
| §3.1 | (链路) | F-A-2, F-A-3, F-A-4 | SPEC-F-A-2/3/4 |
| §3.2 claim-alignment | AC-ALIGN-1 | F-B-1 | SPEC-F-B-1 |
| §3.2 | AC-ALIGN-2 | F-B-2, F-B-3 | SPEC-F-B-2/3 |
| §3.3 security | AC-SEC-1 | F-C-1 | SPEC-F-C-1 |
| §3.3 | AC-SEC-2 | F-C-2 | SPEC-F-C-2 |
| §3.3 | AC-SEC-3 | F-C-3 | SPEC-F-C-3 |
| §3.3 | (守卫/token) | F-C-4, F-C-5 | SPEC-F-C-4/5 |
| §3.4 observability | AC-OBS-1 | F-D-1, F-D-2 | SPEC-F-D-1/2 |
| §3.4 | AC-OBS-2 | F-D-3 | SPEC-F-D-3 |
| §3.5 test-gate | AC-TEST-1 | F-E-2 | SPEC-F-E-2 |
| §3.5 | AC-TEST-2 | F-A-6, F-E-3 | SPEC-F-A-6, SPEC-F-E-3 |
| §3.5 | (基线) | F-E-1 | SPEC-F-E-1 |

## 粒度
PRD feature_count=5（模块）→ decomposition 5 域 → 20 原子 Feature → 20 Spec（1:1）。模块↔域 1:1，域↔Feature 1:N，Feature↔Spec 1:1。

## Task 追溯（Feature → Task）
| Feature | Spec | Task | Wave |
|---|---|---|---|
| F-A-1 | SPEC-F-A-1 | T-F-A-1-1 | 1 |
| F-A-2 | SPEC-F-A-2 | T-F-A-2-1 | 2 |
| F-A-3 | SPEC-F-A-3 | T-F-A-3-1 | 2 |
| F-A-4 | SPEC-F-A-4 | T-F-A-4-1 | 2 |
| F-A-5 | SPEC-F-A-5 | T-F-A-5-1 | 3 |
| F-A-6 | SPEC-F-A-6 | T-F-A-6-1 | 3 |
| F-B-1 | SPEC-F-B-1 | T-F-B-1-1 | 1 |
| F-B-2 | SPEC-F-B-2 | T-F-B-2-1 | 2 |
| F-B-3 | SPEC-F-B-3 | T-F-B-3-1 | 2 |
| F-C-1 | SPEC-F-C-1 | T-F-C-1-1 | 1 |
| F-C-2 | SPEC-F-C-2 | T-F-C-2-1 | 1 |
| F-C-3 | SPEC-F-C-3 | T-F-C-3-1 | 1 |
| F-C-4 | SPEC-F-C-4 | T-F-C-4-1 | 1 |
| F-C-5 | SPEC-F-C-5 | T-F-C-5-1 | 1 |
| F-D-1 | SPEC-F-D-1 | T-F-D-1-1 | 1 |
| F-D-2 | SPEC-F-D-2 | T-F-D-2-1 | 2 |
| F-D-3 | SPEC-F-D-3 | T-F-D-3-1 | 1 |
| F-E-1 | SPEC-F-E-1 | T-F-E-1-1 | 1 |
| F-E-2 | SPEC-F-E-2 | T-F-E-2-1 | 2 |
| F-E-3 | SPEC-F-E-3 | T-F-E-3-1 | 3 |

链：PRD AC → Feature → Spec → Task，全 20 闭环。
