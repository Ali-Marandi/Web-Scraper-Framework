"""Security primitives for WebScraper Pro.

The functions in this module deliberately avoid making authorization decisions
for remote sites. They provide local input validation and safe filesystem/
network boundaries for the application itself.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urljoin, urlparse

ALLOWED_SCHEMES = frozenset({"http", "https"})


def validate_url(url: str, *, base_url: str | None = None) -> str:
    """Return a normalized absolute HTTP(S) URL or raise ValueError."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")
    candidate = urljoin(base_url, url) if base_url else url.strip()
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError("Only HTTP and HTTPS URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("Embedded URL credentials are not allowed")
    return candidate


def resolve_host_addresses(hostname: str) -> set[ipaddress._BaseAddress]:
    """Resolve a hostname to IP objects for destination policy checks."""
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f"Unable to resolve hostname: {hostname}") from exc

    addresses: set[ipaddress._BaseAddress] = set()
    for info in infos:
        try:
            addresses.add(ipaddress.ip_address(info[4][0]))
        except ValueError:
            continue
    if not addresses:
        raise ValueError(f"Hostname has no usable addresses: {hostname}")
    return addresses


def assert_public_destination(hostname: str) -> None:
    """Reject loopback, link-local, private and otherwise non-public IPs.

    This is a conservative SSRF guard for features that fetch arbitrary user
    supplied URLs. Sites explicitly hosted on private networks require a
    separate, opt-in trust policy rather than bypassing this check globally.
    """
    for address in resolve_host_addresses(hostname):
        if not address.is_global:
            raise ValueError(f"Destination is not public: {hostname}")


def safe_path(root: str | os.PathLike[str], requested: str | os.PathLike[str]) -> Path:
    """Resolve *requested* under *root* and reject traversal outside root."""
    root_path = Path(root).expanduser().resolve()
    candidate = (root_path / Path(requested)).resolve()
    try:
        candidate.relative_to(root_path)
    except ValueError as exc:
        raise ValueError("Path escapes the configured root directory") from exc
    return candidate


def safe_output_path(root: str | os.PathLike[str], requested: str | os.PathLike[str]) -> Path:
    """Return a safe output path and ensure its parent directory exists."""
    candidate = safe_path(root, requested)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate
