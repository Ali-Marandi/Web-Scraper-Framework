#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

from scripts.constants import AMINER_PAPER_URL_TEMPLATE, DEFAULT_REC5_URL

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_RETRY_ATTEMPTS = 2
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def resolve_token(config: dict[str, Any] | None = None) -> str:
    config = config or {}
    aminer_config = config.get("aminer") if isinstance(config.get("aminer"), dict) else {}
    return _clean_text(os.getenv("AMINER_API_KEY") or aminer_config.get("token"))


def resolve_rec5_url(config: dict[str, Any] | None = None) -> str:
    config = config or {}
    aminer_config = config.get("aminer") if isinstance(config.get("aminer"), dict) else {}
    return _clean_text(aminer_config.get("rec5_url") or os.getenv("AMINER_REC5_URL")) or DEFAULT_REC5_URL


def build_api_request(
    *,
    aminer_author_id: str = "",
    author_name: str = "",
    author_org: str = "",
    topics: list[str] | None = None,
    size: int = 5,
    offset: int = 0,
    start_year: int | None = None,
    end_year: int | None = None,
    language_sort: str = "",
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if _clean_text(aminer_author_id):
        params["aminer_author_id"] = _clean_text(aminer_author_id)
    if _clean_text(author_name):
        params["author_name"] = _clean_text(author_name)
    if _clean_text(author_org):
        params["author_org"] = _clean_text(author_org)
    cleaned_topics = [_clean_text(t) for t in (topics or []) if _clean_text(t)]
    if cleaned_topics:
        params["topics"] = cleaned_topics
    params["size"] = max(1, min(int(size), 20))
    params["offset"] = max(0, min(int(offset), 100))
    if start_year is not None:
        params["start_year"] = int(start_year)
    if end_year is not None:
        params["end_year"] = int(end_year)
    if _clean_text(language_sort) in {"zh", "en"}:
        params["language_sort"] = _clean_text(language_sort)
    return params


def normalize_rec5_paper(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw rec5 paper dict to the in-skill record shape (Markdown display / JSON 输出)."""
    paper_id = _clean_text(raw.get("paper_id") or raw.get("id"))
    links = raw.get("links") if isinstance(raw.get("links"), dict) else {}
    aminer_url = (
        _clean_text(links.get("aminer"))
        or _clean_text(raw.get("paper_url"))
        or (AMINER_PAPER_URL_TEMPLATE.format(paper_id=paper_id) if paper_id else "")
    )
    arxiv_url = _clean_text(links.get("arxiv") or raw.get("arxiv_url") or "")
    pdf_url = _clean_text(links.get("pdf") or raw.get("pdf_url") or "")
    arxiv_id = _clean_text(raw.get("arxiv_id") or "")

    raw_ss = raw.get("structured_summary")
    if isinstance(raw_ss, dict):
        structured_summary: dict[str, str] = {k: _clean_text(v) for k, v in raw_ss.items() if _clean_text(v)}
    else:
        structured_summary = {}

    raw_fa = raw.get("famous_authors")
    famous_authors: list[Any] = []
    if isinstance(raw_fa, list):
        for item in raw_fa:
            if isinstance(item, dict):
                name = _clean_text(item.get("name"))
                if not name:
                    continue
                famous_authors.append(
                    {
                        "name": name,
                        "description": _clean_text(item.get("description") or item.get("bio") or ""),
                        "profile_url": _clean_text(item.get("profile_url") or ""),
                    }
                )
            elif isinstance(item, str) and _clean_text(item):
                famous_authors.append(_clean_text(item))

    raw_profiles = raw.get("aminer_author_profiles")
    aminer_author_profiles: list[dict[str, Any]] = (
        [p for p in raw_profiles if isinstance(p, dict)] if isinstance(raw_profiles, list) else []
    )

    raw_entries = raw.get("author_entries")
    author_entries: list[dict[str, Any]] = (
        [e for e in raw_entries if isinstance(e, dict)] if isinstance(raw_entries, list) else []
    )

    year = raw.get("year")
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

    return {
        "paper_id": paper_id,
        "arxiv_id": arxiv_id,
        "aminer_paper_id": paper_id,
        "aminer_paper_url": aminer_url,
        "abs_url": arxiv_url,
        "pdf_url": pdf_url,
        "title": _clean_text(raw.get("title")),
        "year": year,
        "authors": [_clean_text(a) for a in list(raw.get("authors") or []) if _clean_text(a)],
        "keywords": [_clean_text(k) for k in list(raw.get("keywords") or []) if _clean_text(k)],
        "summary": _clean_text(raw.get("summary") or ""),
        "structured_summary": structured_summary,
        "famous_authors": famous_authors,
        "aminer_author_profiles": aminer_author_profiles,
        "author_entries": author_entries,
        "source": _clean_text(raw.get("source") or "rec5"),
        "recommendation_reason": _clean_text(raw.get("recommendation_reason") or ""),
    }


def call_rec5_api(
    params: dict[str, Any],
    *,
    token: str,
    url: str = DEFAULT_REC5_URL,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
) -> dict[str, Any]:
    if not _clean_text(token):
        raise RuntimeError("missing_aminer_api_key")

    body = json.dumps(params, ensure_ascii=False).encode("utf-8")
    ssl_context = ssl.create_default_context()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl_context),
    )

    last_error: Exception | None = None
    for attempt in range(1, retry_attempts + 2):
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json;charset=utf-8",
                "Authorization": token,
                "User-Agent": "aminer-rec/1.0",
                "X-Platform": "openclaw",
            },
            method="POST",
        )
        try:
            with opener.open(request, timeout=timeout_seconds) as response:  # nosec B310
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in RETRYABLE_HTTP_CODES and attempt <= retry_attempts:
                last_error = exc
                time.sleep(0.5 * attempt)
                continue
            raise RuntimeError(f"rec5_api_http_{exc.code}") from exc
        except Exception as exc:
            if attempt <= retry_attempts:
                last_error = exc
                time.sleep(0.5 * attempt)
                continue
            raise RuntimeError(f"rec5_api_error:{exc.__class__.__name__}") from exc

        if not payload.get("success"):
            msg = _clean_text(payload.get("msg") or str(payload.get("code") or "api_error"))
            raise RuntimeError(f"rec5_api_failed:{msg}")

        data = payload.get("data")
        if isinstance(data, list) and data:
            papers = list(data[0].get("papers") or [])
            data_obj = data[0] if isinstance(data[0], dict) else {}
        elif isinstance(data, dict):
            papers = list(data.get("papers") or [])
            data_obj = data
        else:
            papers = []
            data_obj = {}
        analyzed_topics = list(data_obj.get("analyzed_topics") or []) if isinstance(data_obj, dict) else []
        return {
            "papers": [p for p in papers if isinstance(p, dict)],
            "analyzed_topics": [str(t).strip() for t in analyzed_topics if str(t).strip()],
        }

    raise RuntimeError(f"rec5_api_unreachable:{_clean_text(str(last_error))}") from last_error
