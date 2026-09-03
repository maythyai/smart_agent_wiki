"""Production deploy compose — F-P-2 (AC-DEPLOY-1, AC-DEPLOY-2).

Validates docker/docker-compose.prod.yml is a self-contained production
stack with the v1.2.0 healthcheck and env-injected secrets (no values baked
into the file or committed).
"""

from __future__ import annotations

from pathlib import Path

import yaml

_COMPOSE = Path(__file__).resolve().parents[2] / "docker" / "docker-compose.prod.yml"


def _compose() -> dict:
    return yaml.safe_load(_COMPOSE.read_text())


def test_prod_compose_self_contained() -> None:
    """AC-DEPLOY-1: the prod compose is self-contained (no missing service refs)."""
    services = _compose()["services"]
    # saw app + redis defined (not referencing an external base).
    assert "saw" in services, "no saw service"
    assert "redis" in services, "no redis service"
    # No stale postgres (project is SQLite-based).
    assert "db" not in services, "stale postgres db service (project is SQLite)"


def test_prod_compose_healthcheck() -> None:
    """AC-DEPLOY-1: the saw service healthchecks the real /health/ready."""
    saw = _compose()["services"]["saw"]
    hc = saw["healthcheck"]["test"]
    assert any("/health/ready" in str(part) for part in hc), (
        "healthcheck does not probe /health/ready"
    )
    assert saw["restart"] == "always"
    # persistent volume for SQLite + receipts
    assert saw["volumes"], "no persistent volumes"


def test_prod_compose_secrets_env_injected() -> None:
    """AC-DEPLOY-2: secrets are env-injected (no values committed)."""
    env = _compose()["services"]["saw"]["environment"]
    # The secret key must use the ${VAR:?...} required-env form, not a literal.
    secret_entry = [e for e in env if e.startswith("SAW_AUTH_SECRET_KEY=")]
    assert secret_entry, "SAW_AUTH_SECRET_KEY not wired"
    val = secret_entry[0].split("=", 1)[1]
    assert val.startswith("${") and ":?" in val, (
        f"SAW_AUTH_SECRET_KEY must be ${VAR:?...} required-env, got: {val}"
    )
    # No literal-looking secret values (long hex/base64) committed in the file.
    text = _COMPOSE.read_text()
    # Heuristic: no line assigns a 32+ char literal to a *_SECRET/*_KEY env.
    import re

    bad = [
        ln for ln in text.splitlines()
        if re.search(r"(SECRET|PASSWORD|KEY)=\${0,1}[A-Za-z0-9]{32,}", ln)
        and "${" not in ln
    ]
    assert not bad, f"literal secret values committed: {bad}"
