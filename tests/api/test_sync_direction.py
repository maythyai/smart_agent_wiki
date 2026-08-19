"""Regression tests for _get_sync_direction derivation.

Direction is derived from the connector's ``supports_push`` capability
rather than a hardcoded {notion, logseq} allowlist, so newly push-capable
connectors (Slack/Discord/Feishu/WeCom) are recognised as bidirectional
automatically.
"""
from unittest.mock import MagicMock, patch

from saw.api.integrations import _get_sync_direction


def test_bidirectional_when_connector_supports_push():
    with patch("saw.api.integrations.ConnectorRegistry") as registry:
        registry.return_value.get.return_value = MagicMock(supports_push=True)
        assert _get_sync_direction("slack") == "bidirectional"


def test_pull_when_connector_does_not_support_push():
    with patch("saw.api.integrations.ConnectorRegistry") as registry:
        registry.return_value.get.return_value = MagicMock(supports_push=False)
        assert _get_sync_direction("feed") == "pull"


def test_pull_when_connector_cannot_be_resolved():
    # E.g. the platform's optional SDK is not installed.
    with patch("saw.api.integrations.ConnectorRegistry") as registry:
        registry.return_value.get.side_effect = Exception("no SDK")
        assert _get_sync_direction("unknown") == "pull"


def test_pull_when_registry_returns_none():
    with patch("saw.api.integrations.ConnectorRegistry") as registry:
        registry.return_value.get.return_value = None
        assert _get_sync_direction("nope") == "pull"
