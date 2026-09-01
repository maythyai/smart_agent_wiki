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
