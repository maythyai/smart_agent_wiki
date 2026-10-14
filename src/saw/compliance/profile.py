"""Compliance profile + data-residency assertions (v1.32.1).

Loads a declarative compliance profile from ``.saw/compliance.yaml`` (or the
``compliance`` section of ``.saw/config.yaml``) and computes data-residency
assertions so a deployment can report whether it satisfies its declared
constraints (on-prem binding, audit-receipt requirement, retention policy).

Aligned with the 2026.05《智能体规范》trust baseline: compliance-relevant
metadata is introspectable via ``saw_compliance_status`` (MCP) and
``GET /api/v1/compliance`` (REST).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass
class ComplianceProfile:
    """Declarative compliance profile (loaded from YAML, else defaults)."""

    profile: str = "default"  # hipaa / sox / gdpr / default
    on_prem: bool = False  # data-residency assertion: data must stay on-prem
    region: str = ""  # e.g. "us-east-1", "eu-west-1"
    require_audit_receipts: bool = False  # every write must produce an Ed25519 receipt
    retention_days: int = 0  # 0 = no retention policy enforced


def load_compliance_profile(path: Path | str | None = None) -> ComplianceProfile:
    """Load the compliance profile from YAML.

    Looks for ``.saw/compliance.yaml`` first (or *path* if given), then falls
    back to the ``compliance`` section of ``.saw/config.yaml``. A missing or
    unparseable file yields the ``default`` profile (no constraints) —
    compliance is opt-in, never blocks startup.
    """
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    else:
        candidates.append(Path(".saw/compliance.yaml"))
        candidates.append(Path(".saw/config.yaml"))
    for cand in candidates:
        if not cand.is_file():
            continue
        try:
            import yaml

            with open(cand, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:  # pragma: no cover — best-effort, never block
            logger.warning("Failed to load compliance config %s: %s", cand, e)
            continue
        # compliance.yaml is the whole doc; config.yaml uses a `compliance` section.
        section = data.get("compliance", data) if isinstance(data, dict) else {}
        if not isinstance(section, dict) or not section:
            continue
        return ComplianceProfile(
            profile=str(section.get("profile", "default")),
            on_prem=bool(section.get("on_prem", False)),
            region=str(section.get("region", "")),
            require_audit_receipts=bool(section.get("require_audit_receipts", False)),
            retention_days=int(section.get("retention_days", 0) or 0),
        )
    return ComplianceProfile()


def compliance_status(
    profile: ComplianceProfile, host: str, networked: bool
) -> dict:
    """Compute the introspectable compliance status for a deployment.

    ``on_prem_satisfied`` is True when the deployment is *not* networked OR
    bound to a loopback host — i.e. data stays on the local machine, which is
    what an on-prem declaration requires. A declared on-prem profile that is
    served on a non-loopback networked host reports ``on_prem_satisfied=False``
    (a compliance violation surfaced, not silently ignored).
    """
    on_prem_satisfied = (not networked) or (host in _LOOPBACK_HOSTS)
    return {
        "profile": profile.profile,
        "on_prem_declared": profile.on_prem,
        "on_prem_satisfied": on_prem_satisfied,
        "region": profile.region,
        "require_audit_receipts": profile.require_audit_receipts,
        "retention_days": profile.retention_days,
        "host": host,
        "networked": networked,
    }
