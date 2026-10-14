---
id: SPEC-F-COMPLIANCE-PROFILE
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-14
status: approved
prd_ref: PRD-compliance-profile-v1.32.1
target_version: v1.32.1
---

# SPEC — v1.32.1 数据驻留 + 合规 profile（详细）

## F-CP-1: ComplianceProfile + loader
新模块 `src/saw/compliance/profile.py`:
```python
@dataclass
class ComplianceProfile:
    profile: str = "default"          # hipaa/sox/gdpr/default
    on_prem: bool = False             # data residency assertion
    region: str = ""                  # e.g. "eu-west-1"
    require_audit_receipts: bool = False
    retention_days: int = 0           # 0 = no policy

def load_compliance_profile(path: Path | None = None) -> ComplianceProfile:
    # reads .saw/compliance.yaml (or config.yaml compliance section)
    # missing file -> ComplianceProfile() defaults
```

## F-CP-2: saw_compliance_status MCP + GET /api/v1/compliance REST
返回:
```json
{
  "profile": "hipaa",
  "on_prem_declared": true,
  "on_prem_satisfied": true,        // host ∈ loopback OR not networked
  "region": "us-east",
  "require_audit_receipts": true,
  "retention_days": 365,
  "host": "127.0.0.1",
  "networked": false
}
```
on_prem_satisfied = (not networked) or (host in loopback set). 复用 app.py `_networked` 逻辑。

## 接线
app.py create_app_from_config: load profile → app.state.compliance。REST via `_compliance(request)` helper 取 app.state.compliance + host/networked。

## AC
- 无 compliance.yaml → status.profile="default", on_prem_declared=False, on_prem_satisfied=(not networked).
- 有 compliance.yaml(profile=hipaa, on_prem=True) + host=127.0.0.1 → on_prem_satisfied=True.
- 有 compliance.yaml(on_prem=True) + host=0.0.0.0(networked) + 无 SAW_ALLOW_UNAUTH_NETWORK → on_prem_satisfied=False.

## 测试
- `tests/unit/compliance/test_profile.py`: loader (missing file / valid yaml).
- `tests/api/test_h1_routes.py::TestComplianceProfileRoute`: status default + declared.
- 全量回归 + ruff 0 + coverage 不回归。MCP 工具 38→39。
