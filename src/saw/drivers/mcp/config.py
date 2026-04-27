"""MCP server configuration.

Per PITFALLS.md: Default to localhost only for security.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """MCP server configuration settings.

    Per PITFALLS.md: Default host is 127.0.0.1 (localhost only).
    """

    server_name: str = "smart-agent-wiki"
    server_version: str = "1.0.0"
    host: str = "127.0.0.1"  # Per PITFALLS.md: default localhost only
    port: int = 8000
    log_level: str = "INFO"
    transport: str = "stdio"  # "stdio" or "sse"
