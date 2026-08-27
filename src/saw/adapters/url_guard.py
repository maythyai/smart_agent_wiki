"""SSRF guard — block fetches to internal / private / loopback targets.

HI-12: URL ingestion (trafilatura), RSS feed + entry-link fetch (httpx) and
outbound webhook delivery all accepted user-supplied URLs with no internal-IP
blocklist — allowing cloud-metadata exfiltration (``169.254.169.254``) and
internal-service probing. ``assert_safe_url`` resolves the hostname and rejects
private / loopback / link-local / reserved / cloud-metadata addresses.

Because DNS may change between resolution and the actual fetch (DNS rebinding,
a TOCTOU), callers should re-check immediately before each network call; this
guard is applied at every fetch site.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class SsrfError(ValueError):
    """Raised when a URL targets a blocked internal address."""


_BLOCKED_HOSTS = {"localhost", "ip6-localhost", "ip6-loopback"}
# Cloud metadata endpoints (AWS / GCP / Azure IMDS).
_METADATA_IPS = {"169.254.169.254", "fd00:ec2::254"}


def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        # Unresolvable / non-IP literal → block (be conservative).
        return True
    if (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_unspecified
        or addr.is_multicast
    ):
        return True
    if str(addr) in _METADATA_IPS:
        return True
    return False


def assert_safe_url(url: str) -> None:
    """Raise :class:`SsrfError` if *url* targets a private/internal host.

    Checks scheme (http/https only), hostname, and every resolved A/AAAA
    record. Resolving all records defends against DNS rebinding where one
    record is public and another is internal.
    """
    if not url or not isinstance(url, str):
        raise SsrfError("Empty URL")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SsrfError(f"Refused non-http(s) scheme: {parsed.scheme!r}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise SsrfError(f"URL has no hostname: {url!r}")
    if host in _BLOCKED_HOSTS:
        raise SsrfError(f"Refused blocked host: {host!r}")
    # Bare-IP hosts: evaluate directly without DNS.
    try:
        ipaddress.ip_address(host)
        if _is_blocked_ip(host):
            raise SsrfError(f"Refused internal target: {host}")
        return
    except ValueError:
        pass  # hostname is a DNS name — resolve below.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise SsrfError(f"Could not resolve {host!r}: {e}") from e
    for info in infos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise SsrfError(f"Refused internal target {host!r} -> {ip}")


async def assert_safe_url_async(url: str) -> None:
    """Async wrapper — runs the (blocking) DNS resolution in a threadpool."""
    import asyncio

    await asyncio.to_thread(assert_safe_url, url)
