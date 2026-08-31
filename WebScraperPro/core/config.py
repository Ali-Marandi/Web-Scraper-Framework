"""Typed runtime configuration with environment-based overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside the allowed range")
    return value


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application-wide operational limits and API binding policy."""

    api_host: str = "127.0.0.1"
    api_port: int = 8765
    request_timeout_seconds: float = 30.0
    max_concurrency: int = 8
    max_response_bytes: int = 10 * 1024 * 1024
    max_crawl_depth: int = 3

    @classmethod
    def from_env(cls) -> "AppConfig":
        timeout_raw = os.getenv("WEBSCRAPER_REQUEST_TIMEOUT", "30")
        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise ValueError("WEBSCRAPER_REQUEST_TIMEOUT must be numeric") from exc
        if not 1 <= timeout <= 300:
            raise ValueError("WEBSCRAPER_REQUEST_TIMEOUT must be between 1 and 300 seconds")

        return cls(
            api_host=os.getenv("WEBSCRAPER_API_HOST", "127.0.0.1"),
            api_port=_env_int("WEBSCRAPER_API_PORT", 8765, minimum=1024, maximum=65535),
            request_timeout_seconds=timeout,
            max_concurrency=_env_int("WEBSCRAPER_MAX_CONCURRENCY", 8, minimum=1, maximum=64),
            max_response_bytes=_env_int("WEBSCRAPER_MAX_RESPONSE_BYTES", 10 * 1024 * 1024, minimum=1024, maximum=200 * 1024 * 1024),
            max_crawl_depth=_env_int("WEBSCRAPER_MAX_CRAWL_DEPTH", 3, minimum=0, maximum=20),
        )
