"""Connector bootstrap (HI-5).

Previously ``ConnectorRegistry.register()`` was never called in the web app,
so every connector API endpoint returned 404 ("X connector not registered").
This module provides the missing registration point: at startup, construct
each platform connector with a default ``ConnectorConfig`` + ``RateLimitManager``
and register it, best-effort — platforms whose optional SDK is not installed
or whose construction fails are skipped (debug-logged) and never block ``saw web``.

This makes the connector framework *wired* (the registry is populated, so
endpoints no longer 404). Full credential-backed operation still requires
per-platform settings stored in the ``connector_settings`` table (configured
via the connector-settings API); a registered-but-unconfigured connector loads
its credentials lazily once settings exist.
"""
from __future__ import annotations

import importlib
import logging
from typing import Any

from saw.connectors.models import ConnectorConfig
from saw.connectors.rate_limiter import RateLimitManager
from saw.connectors.registry import ConnectorRegistry

logger = logging.getLogger(__name__)

# platform -> (module, class, rate-limit-platform). Each connector class is
# imported lazily so a missing optional SDK never breaks the others.
_PLATFORMS: dict[str, tuple[str, str, str]] = {
    "github": ("saw.connectors.github.connector", "GitHubConnector", "github"),
    "notion": ("saw.connectors.notion.connector", "NotionConnector", "notion"),
    "slack": ("saw.connectors.im.slack.connector", "SlackConnector", "slack"),
    "discord": ("saw.connectors.im.discord.connector", "DiscordConnector", "discord"),
    "feishu": ("saw.connectors.im.feishu.connector", "FeishuConnector", "feishu"),
    "wecom": ("saw.connectors.im.wecom.connector", "WeComConnector", "wecom"),
    "logseq": ("saw.connectors.logseq.connector", "LogseqConnector", "logseq"),
}


def register_default_connectors(registry: ConnectorRegistry) -> list[str]:
    """Construct + register each platform connector (best-effort, HI-5).

    Returns the list of successfully registered platform names. Safe to call
    on a fresh install — missing SDKs/settings are skipped, not fatal.
    """
    registered: list[str] = []
    for platform, (module_path, class_name, rl_platform) in _PLATFORMS.items():
        try:
            mod = importlib.import_module(module_path)
            conn_cls = getattr(mod, class_name)
            config = ConnectorConfig(
                id=f"{platform}-default",
                user_id="system",
                platform=platform,
                name=platform.title(),
            )
            rate_limiter = RateLimitManager(rl_platform)
            connector: Any
            # Connectors accept (config, rate_limiter, session, ...). Pass
            # what we can; optional handlers default to None inside each
            # connector. Fall back to narrower signatures for connectors that
            # don't take the full triple.
            try:
                connector = conn_cls(config, rate_limiter, None)
            except TypeError:
                try:
                    connector = conn_cls(config, rate_limiter)
                except TypeError:
                    try:
                        connector = conn_cls(config)
                    except TypeError:
                        # Some connectors (e.g. WeCom, Logseq) take no args
                        # and initialise lazily from stored settings.
                        connector = conn_cls()
            registry.register(connector)
            registered.append(platform)
        except ImportError as e:
            logger.debug(
                "Connector %s skipped (optional SDK not installed): %s",
                platform, e,
            )
        except Exception as e:  # pragma: no cover — best-effort, never fatal
            logger.warning("Connector %s registration failed: %s", platform, e)
    if registered:
        logger.info("Registered connectors: %s", ", ".join(registered))
    return registered
