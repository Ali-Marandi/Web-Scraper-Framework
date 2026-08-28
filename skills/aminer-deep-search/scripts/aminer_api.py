#!/usr/bin/env python3
"""AMiner Open Platform tool CLI for aminer-deep-search.

Pure-stdlib tool commands driven by the host model. Every subcommand prints a
single JSON document to stdout (the tool result); diagnostics and the cost
summary go to stderr. No relevance scoring or loop control happens here — the
host model decides what to search, what to keep, and when to stop.

Endpoints (base: https://publicapi.chatglm.cn/chatglm_public/skill/aminer):
  GET  /api/paper/search/pro   keyword search, ¥0.01/page   (subcommand: search)
  POST /api/paper/qa/search    natural-language search, ¥0.05/call (qa-search)
  POST /api/paper/info         batch metadata, free, <=100 ids     (info, and enrichment)
  GET  /api/paper/relation     backward references, ¥0.10/seed     (references)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://publicapi.chatglm.cn/chatglm_public/skill/aminer"
CONSOLE_URL = "https://open.aminer.cn/open/board?tab=control"
TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
PAPER_INFO_BATCH_LIMIT = 100
SEARCH_PRO_PAGE_SIZE = 20
ABSTRACT_SLICE_LIMIT = 300

PRICE_CNY = {
    "search_pro": 0.01,
    "qa_search": 0.05,
    "paper_info": 0.0,
    "relation": 0.10,
}

_call_counts: dict[str, int] = {}


class ToolError(Exception):
    """Fatal error carrying a structured JSON payload for stdout."""

    def __init__(self, payload: dict[str, Any], exit_code: int = 1) -> None:
        super().__init__(payload.get("message", "tool error"))
        self.payload = payload
        self.exit_code = exit_code


def _get_token() -> str:
    token = (os.getenv("AMINER_API_KEY") or "").strip()
    if not token:
        raise ToolError(
            {
                "ok": False,
                "error": "missing_aminer_api_key",
                "message": "Set the AMINER_API_KEY environment variable before calling AMiner APIs.",
                "console": CONSOLE_URL,
            },
            exit_code=2,
        )
    return token


def _redact(value: Any, token: str) -> Any:
    if isinstance(value, str):
        return value.replace(token, "[REDACTED]") if token else value
    if isinstance(value, list):
        return [_redact(item, token) for item in value]
    if isinstance(value, dict):
        return {key: _redact(item, token) for key, item in value.items()}
    return value


def _request(api_name: str, method: str, path: str,
             params: dict[str, Any] | None = None,
             body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call one endpoint with retries; return the parsed JSON envelope."""
    token = _get_token()
    url = BASE_URL + path
    if method == "GET" and params:
        query = urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}
        )
        url = f"{url}?{query}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Authorization": token, "X-Platform": "openclaw"}
    if data is not None:
        headers["Content-Type"] = "application/json;charset=utf-8"

    _call_counts[api_name] = _call_counts.get(api_name, 0) + 1

    last_error: dict[str, Any] | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read().decode("utf-8", errors="replace")
                envelope = json.loads(raw)
                if not isinstance(envelope, dict):
                    return {"data": envelope}
                # AMiner can wrap errors in an HTTP-200 response, e.g. code 403
                # for insufficient balance/permission. Surface those instead of
                # letting them look like an empty result set.
                code = envelope.get("code")
                if isinstance(code, int) and code not in (0, 200):
                    raise ToolError({
                        "ok": False,
                        "error": "api_error",
                        "api": api_name,
                        "code": code,
                        "message": _redact(str(envelope.get("msg") or ""), token)[:300],
                    })
                return envelope
        except urllib.error.HTTPError as exc:
            detail = _redact(exc.read().decode("utf-8", errors="replace")[:500], token)
            last_error = {
                "ok": False,
                "error": "http_error",
                "api": api_name,
                "status": exc.code,
                "detail": detail,
            }
            if exc.code not in RETRYABLE_STATUS:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = {
                "ok": False,
                "error": "network_error",
                "api": api_name,
                "detail": _redact(str(getattr(exc, "reason", exc)), token)[:500],
            }
        except json.JSONDecodeError as exc:
            last_error = {
                "ok": False,
                "error": "invalid_response",
                "api": api_name,
                "detail": str(exc)[:200],
            }
            break
        if attempt < MAX_RETRIES:
            backoff = (2 ** (attempt - 1)) + random.uniform(0, 0.3)
            print(f"[retry] {api_name} attempt={attempt}/{MAX_RETRIES} wait={backoff:.1f}s",
                  file=sys.stderr)
            time.sleep(backoff)

    raise ToolError(last_error or {"ok": False, "error": "request_failed", "api": api_name})


def _envelope_items(envelope: dict[str, Any]) -> list[dict[str, Any]]:
    data = envelope.get("data")
    if isinstance(data, dict):
        data = data.get("data") or data.get("items") or []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = str(item or "").strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def _paper_id(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("_id") or "").strip()


# ──────────────────────────────────────────────────────────────────────────────
# paper/info enrichment (free)
# ──────────────────────────────────────────────────────────────────────────────

def _fetch_paper_info(ids: list[str]) -> dict[str, dict[str, Any]]:
    """Batch-fetch lightweight cards; returns a map of id -> raw info entry."""
    info_by_id: dict[str, dict[str, Any]] = {}
    unique_ids = _dedupe(ids)
    for start in range(0, len(unique_ids), PAPER_INFO_BATCH_LIMIT):
        chunk = unique_ids[start:start + PAPER_INFO_BATCH_LIMIT]
        envelope = _request("paper_info", "POST", "/api/paper/info", body={"ids": chunk})
        for entry in _envelope_items(envelope):
            entry_id = _paper_id(entry)
            if entry_id:
                info_by_id[entry_id] = entry
    return info_by_id


def _venue_text(entry: dict[str, Any]) -> str:
    venue = entry.get("venue")
    if isinstance(venue, dict):
        return str(venue.get("raw") or venue.get("name") or "")
    return str(venue or entry.get("raw") or entry.get("venue_name") or "")


def _compact_paper(base: dict[str, Any], info: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = dict(info or {})
    item: dict[str, Any] = {
        "id": _paper_id(base) or _paper_id(merged),
        "title": str(base.get("title") or merged.get("title")
                     or base.get("title_zh") or merged.get("title_zh") or "").strip(),
    }
    year = merged.get("year") or base.get("year")
    if year:
        item["year"] = year
    venue = _venue_text(merged) or _venue_text(base)
    if venue:
        item["venue"] = venue
    abstract = str(merged.get("abstract_slice") or merged.get("abstract") or "").strip()
    if abstract:
        item["abstract_slice"] = abstract[:ABSTRACT_SLICE_LIMIT]
    return item


def _enrich(base_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach year/venue/abstract_slice from the free paper/info endpoint."""
    ids = [_paper_id(item) for item in base_items if _paper_id(item)]
    info_by_id = _fetch_paper_info(ids) if ids else {}
    papers: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in base_items:
        paper_id = _paper_id(item)
        if not paper_id or paper_id in seen:
            continue
        seen.add(paper_id)
        compact = _compact_paper(item, info_by_id.get(paper_id))
        if compact["id"] and compact["title"]:
            papers.append(compact)
    return papers


# ──────────────────────────────────────────────────────────────────────────────
# Subcommands
# ──────────────────────────────────────────────────────────────────────────────

def cmd_search(args: argparse.Namespace) -> list[dict[str, Any]]:
    target = max(1, args.size)
    max_year = args.year
    collected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(max(1, args.max_pages)):
        params: dict[str, Any] = {
            "keyword": args.query,
            "page": page,
            "size": SEARCH_PRO_PAGE_SIZE,
        }
        if args.order:
            params["order"] = args.order
        envelope = _request("search_pro", "GET", "/api/paper/search/pro", params=params)
        page_items = _envelope_items(envelope)
        if not page_items:
            break
        enriched = _enrich(page_items)
        for paper in enriched:
            if paper["id"] in seen:
                continue
            if max_year and paper.get("year") and int(paper["year"]) > max_year:
                continue
            seen.add(paper["id"])
            collected.append(paper)
        if len(collected) >= target or len(page_items) < SEARCH_PRO_PAGE_SIZE:
            break
    return collected[:target]


def cmd_qa_search(args: argparse.Namespace) -> list[dict[str, Any]]:
    # The backend only uses the `query` keyword-extraction result when
    # use_topic=true; with use_topic=false it reads `title` only, so a
    # query-only request ends up with empty terms and returns envelope 403.
    # Therefore always send use_topic=true.
    body: dict[str, Any] = {
        "use_topic": True,
        "size": max(1, args.size),
    }
    if args.query:
        body["query"] = args.query
    if args.topic_high:
        body["topic_high"] = args.topic_high
    if not args.query and not args.topic_high:
        raise ToolError({
            "ok": False,
            "error": "invalid_request",
            "message": "qa-search requires --query and/or --topic-high",
        }, exit_code=2)
    if args.year_from or args.year_to:
        year_from = args.year_from or 1900
        year_to = args.year_to or time.gmtime().tm_year
        body["year"] = list(range(year_from, year_to + 1))
    if args.citation_sort:
        body["force_citation_sort"] = True
    envelope = _request("qa_search", "POST", "/api/paper/qa/search", body=body)
    return _enrich(_envelope_items(envelope))


def cmd_info(args: argparse.Namespace) -> list[dict[str, Any]]:
    info_by_id = _fetch_paper_info(args.ids)
    return [_compact_paper(entry, None) for entry in info_by_id.values()]


def cmd_references(args: argparse.Namespace) -> list[dict[str, Any]]:
    seed_ids = _dedupe(args.ids)
    per_seed = max(1, args.per_seed)
    sources_by_id: dict[str, list[str]] = {}
    ordered_ids: list[str] = []
    seed_set = set(seed_ids)
    for seed_id in seed_ids:
        envelope = _request("relation", "GET", "/api/paper/relation",
                            params={"id": seed_id})
        cited_ids: list[str] = []
        for item in _envelope_items(envelope):
            cited = item.get("cited") or []
            if not isinstance(cited, list):
                continue
            for cited_item in cited:
                cited_id = _paper_id(cited_item) if isinstance(cited_item, dict) else str(cited_item or "").strip()
                if cited_id:
                    cited_ids.append(cited_id)
        for cited_id in _dedupe(cited_ids)[:per_seed]:
            if cited_id in seed_set:
                continue
            if cited_id not in sources_by_id:
                sources_by_id[cited_id] = []
                ordered_ids.append(cited_id)
            sources_by_id[cited_id].append(seed_id)

    papers = _enrich([{"id": paper_id} for paper_id in ordered_ids])
    for paper in papers:
        paper["source_paper_ids"] = sources_by_id.get(paper["id"], [])
    return papers


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AMiner Open Platform tool commands (stdout: JSON only; diagnostics: stderr)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Keyword search via paper/search/pro (¥0.01/page).")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--size", type=int, default=20, help="Papers to return (default 20).")
    p_search.add_argument("--year", type=int, default=None,
                          help="Inclusive publication end year (client-side filter).")
    p_search.add_argument("--order", choices=["n_citation", "year"], default=None)
    p_search.add_argument("--max-pages", type=int, default=3,
                          help="Max result pages to fetch (default 3).")
    p_search.set_defaults(func=cmd_search)

    p_qa = sub.add_parser("qa-search", help="Natural-language search via paper/qa/search (¥0.05/call).")
    p_qa.add_argument("--query", default=None, help="Natural-language question.")
    p_qa.add_argument("--topic-high", default=None,
                      help='Structured keywords, JSON string like [["termA","termB"],["termC"]] '
                           "(outer AND, inner OR).")
    p_qa.add_argument("--size", type=int, default=20)
    p_qa.add_argument("--year-from", type=int, default=None)
    p_qa.add_argument("--year-to", type=int, default=None)
    p_qa.add_argument("--citation-sort", action="store_true",
                      help="Sort entirely by citation count.")
    p_qa.set_defaults(func=cmd_qa_search)

    p_info = sub.add_parser("info", help="Batch metadata via paper/info (free, <=100 ids/batch).")
    p_info.add_argument("--ids", nargs="+", required=True)
    p_info.set_defaults(func=cmd_info)

    p_refs = sub.add_parser("references",
                            help="Backward-reference expansion via paper/relation (¥0.10/seed).")
    p_refs.add_argument("--ids", nargs="+", required=True, help="Seed AMiner paper IDs.")
    p_refs.add_argument("--per-seed", type=int, default=20,
                        help="Max references kept per seed (default 20).")
    p_refs.set_defaults(func=cmd_references)

    return parser


def _print_cost_summary() -> None:
    if not _call_counts:
        return
    total = sum(PRICE_CNY.get(name, 0.0) * count for name, count in _call_counts.items())
    parts = " + ".join(f"{name} x{count}" for name, count in sorted(_call_counts.items()))
    print(f"[cost] {parts} = ¥{total:.2f}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except ToolError as exc:
        print(json.dumps(exc.payload, ensure_ascii=False), file=sys.stdout)
        _print_cost_summary()
        return exc.exit_code
    print(json.dumps(result, ensure_ascii=False, indent=2))
    _print_cost_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
