"""Compliance profile loader + status tests (v1.32.1)."""
from __future__ import annotations

from pathlib import Path

from saw.compliance.profile import (
    ComplianceProfile,
    compliance_status,
    load_compliance_profile,
)


def test_default_profile_when_no_file(tmp_path, monkeypatch):
    """Missing compliance.yaml → default profile (no constraints)."""
    monkeypatch.chdir(tmp_path)
    p = load_compliance_profile()
    assert p.profile == "default"
    assert p.on_prem is False
    assert p.require_audit_receipts is False
    assert p.retention_days == 0


def test_load_compliance_yaml(tmp_path):
    """A .saw/compliance.yaml loads the declared profile."""
    cfg = tmp_path / ".saw"
    cfg.mkdir()
    (cfg / "compliance.yaml").write_text(
        "profile: hipaa\non_prem: true\nregion: us-east-1\n"
        "require_audit_receipts: true\nretention_days: 365\n",
        encoding="utf-8",
    )
    p = load_compliance_profile(path=cfg / "compliance.yaml")
    assert p.profile == "hipaa"
    assert p.on_prem is True
    assert p.region == "us-east-1"
    assert p.require_audit_receipts is True
    assert p.retention_days == 365


def test_compliance_status_loopback_satisfies_on_prem():
    """on_prem declared + loopback host → on_prem_satisfied=True."""
    p = ComplianceProfile(profile="hipaa", on_prem=True)
    s = compliance_status(p, host="127.0.0.1", networked=False)
    assert s["on_prem_declared"] is True
    assert s["on_prem_satisfied"] is True
    assert s["profile"] == "hipaa"


def test_compliance_status_networked_violates_on_prem():
    """on_prem declared + networked non-loopback host → on_prem_satisfied=False."""
    p = ComplianceProfile(profile="hipaa", on_prem=True)
    s = compliance_status(p, host="0.0.0.0", networked=True)
    assert s["on_prem_satisfied"] is False  # compliance violation surfaced


def test_compliance_status_not_networked_satisfies_even_if_not_loopback():
    """A non-networked bind (e.g. unix socket / no network) satisfies on-prem."""
    p = ComplianceProfile(profile="default")
    s = compliance_status(p, host="0.0.0.0", networked=False)
    assert s["on_prem_satisfied"] is True
