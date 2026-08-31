"""HTTP API hardening helpers.

Keep transport policy separate from business/quant logic so the existing API
can migrate incrementally without a risky rewrite.
"""
from __future__ import annotations

from functools import wraps
from hmac import compare_digest
import os
from typing import Any, Callable, TypeVar

from flask import jsonify, request

F = TypeVar("F", bound=Callable[..., Any])


def configured_api_token() -> str | None:
    """Read the optional API token from the process environment."""
    value = os.getenv("WEBSCRAPER_API_TOKEN", "").strip()
    return value or None


def token_authorized() -> bool:
    """Return whether the current request carries the configured bearer token."""
    expected = configured_api_token()
    if not expected:
        return request.remote_addr in {"127.0.0.1", "::1"}
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    return scheme.lower() == "bearer" and bool(token) and compare_digest(token, expected)


def require_api_auth(view: F) -> F:
    """Protect a Flask endpoint while retaining loopback-only local mode."""
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if not token_authorized():
            return jsonify({"error": "authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def install_security_headers(app: Any) -> None:
    """Install defensive response headers without changing application payloads."""
    @app.after_request
    def _security_headers(response: Any) -> Any:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        return response


def validate_json_object(payload: Any) -> dict[str, Any]:
    """Validate that an API JSON payload is an object, not a list/string/null."""
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload
