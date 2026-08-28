#!/usr/bin/env python3
"""
AMiner Open Platform API Client
Optional convenience client for AMiner Open Platform.
The skills in this repository can be used directly with curl; this script is kept
as an optional local wrapper for users who prefer Python-based composition.

Usage:
    python aminer_client.py --token <TOKEN> --action <ACTION> [options]

Workflows:
    scholar_profile   Scholar profile analysis (search → details + portrait + papers + patents + projects)
    paper_deep_dive   Paper deep dive (search → details + citation chain)
    org_analysis      Institution research capability analysis (disambiguation → details + scholars + papers + patents)
    venue_papers      Journal paper monitoring (search → details + papers by year)
    paper_qa          Academic Q&A (AI-driven keyword search)
    patent_search     Patent search and details
    scholar_patents   Retrieve all patent details for a scholar by name

Direct single API call:
    raw               Call any API directly; requires --api and --params

Console (Generate Token): https://open.aminer.cn/open/board?tab=control
Docs: https://open.aminer.cn/open/docs
"""

import argparse
import json
import os
import sys
import time
import random
import threading
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

BASE_URL = "https://publicapi.chatglm.cn/chatglm_public/skill/aminer"

REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRYABLE_HTTP_STATUS = {408, 429, 500, 502, 503, 504}

API_PRICE: dict[str, float] = {
    "paper_search": 0, "paper_info": 0, "person_search": 0,
    "org_search": 0, "venue_search": 0, "patent_search": 0, "patent_info": 0,
    "paper_search_pro": 0.01, "paper_detail": 0.01, "patent_detail": 0.01,
    "org_detail": 0.01, "org_disambiguate": 0.01,
    "paper_qa_search": 0.05, "paper_qa_search_pro": 0.70, "org_disambiguate_pro": 0.05,
    "paper_relation": 0.10, "org_paper_relation": 0.10,
    "org_patent_relation": 0.10, "venue_paper_relation": 0.10,
    "paper_list_by_keywords": 0.10,
    "venue_detail": 0.20, "paper_detail_by_condition": 0.20,
    "person_figure": 0.50, "org_person_relation": 0.50,
    "person_detail": 1.00,
    "person_paper_relation": 1.50, "person_patent_relation": 1.50,
    "person_project": 1.50,
}

_cost_log: list[tuple[str, float]] = []
_cost_lock = threading.Lock()


def _track_cost(api_name: str) -> None:
    price = API_PRICE.get(api_name, 0)
    with _cost_lock:
        _cost_log.append((api_name, price))


def get_cost_summary() -> dict:
    with _cost_lock:
        total = sum(p for _, p in _cost_log)
        breakdown = {}
        for name, price in _cost_log:
            breakdown[name] = breakdown.get(name, 0) + price
        return {"total": round(total, 2), "breakdown": breakdown, "calls": len(_cost_log)}


def reset_cost() -> None:
    with _cost_lock:
        _cost_log.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Core HTTP Utilities
# ──────────────────────────────────────────────────────────────────────────────

def _request(token: str, method: str, path: str,
             params: Optional[dict] = None,
             body: Optional[dict] = None) -> Any:
    """Send an HTTP request and return the parsed JSON data (with retries)."""
    url = BASE_URL + path
    headers = {
        "Authorization": token,
        "X-Platform": "openclaw",
        "Content-Type": "application/json;charset=utf-8",
    }

    if method.upper() == "GET" and params:
        query = urllib.parse.urlencode(
            {k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
             for k, v in params.items() if v is not None}
        )
        url = f"{url}?{query}"

    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

    last_error_result = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body_bytes = e.read()
            try:
                err = json.loads(body_bytes)
            except Exception:
                err = body_bytes.decode("utf-8", errors="replace")
            retryable = e.code in RETRYABLE_HTTP_STATUS
            print(f"[HTTP {e.code}] {e.reason}: {err}", file=sys.stderr)
            last_error_result = {
                "code": e.code, "success": False,
                "msg": str(e.reason), "error": err, "retryable": retryable,
            }
            if not retryable:
                return last_error_result
        except urllib.error.URLError as e:
            reason = str(getattr(e, "reason", e))
            print(f"[Request failed] {reason}", file=sys.stderr)
            last_error_result = {
                "code": -1, "success": False,
                "msg": "network_error", "error": reason, "retryable": True,
            }
        except TimeoutError as e:
            print(f"[Request timeout] {e}", file=sys.stderr)
            last_error_result = {
                "code": -1, "success": False,
                "msg": "timeout", "error": str(e), "retryable": True,
            }
        except Exception as e:
            print(f"[Request failed] {e}", file=sys.stderr)
            return {
                "code": -1, "success": False,
                "msg": "unknown_error", "error": str(e), "retryable": False,
            }

        if attempt < MAX_RETRIES:
            backoff = (2 ** (attempt - 1)) + random.uniform(0, 0.3)
            print(f"[Retry] attempt={attempt}/{MAX_RETRIES} wait={backoff:.2f}s", file=sys.stderr)
            time.sleep(backoff)

    return last_error_result or {
        "code": -1, "success": False,
        "msg": "request_failed", "error": "max retries exceeded", "retryable": True,
    }


def _print(data: Any) -> None:
    """Pretty-print JSON result."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────────────────────────────────────────
# Paper APIs
# ──────────────────────────────────────────────────────────────────────────────

def paper_search(token: str, title: str, page: int = 1, size: int = 10) -> Any:
    """Paper Search (Free): search by title; returns ID/title/DOI."""
    _track_cost("paper_search")
    return _request(token, "GET", "/api/paper/search",
                    params={"title": title, "page": page, "size": size})


def paper_search_pro(token: str, title: str = None, keyword: str = None,
                     abstract: str = None, author: str = None,
                     org: str = None, venue: str = None,
                     order: str = None, page: int = 0, size: int = 10) -> Any:
    """Paper Search Pro (¥0.01/call): multi-condition search."""
    _track_cost("paper_search_pro")
    params = {"page": page, "size": size}
    for k, v in [("title", title), ("keyword", keyword), ("abstract", abstract),
                 ("author", author), ("org", org), ("venue", venue), ("order", order)]:
        if v is not None:
            params[k] = v
    return _request(token, "GET", "/api/paper/search/pro", params=params)


def paper_qa_search(token: str, query: str = None,
                    use_topic: bool = True,
                    topic_high: str = None, topic_middle: str = None, topic_low: str = None,
                    title: list = None, doi: str = None, year: list = None,
                    sci_flag: bool = False, n_citation_flag: bool = False,
                    force_citation_sort: bool = False, force_year_sort: bool = False,
                    author_terms: list = None, org_terms: list = None,
                    author_id: list = None, org_id: list = None, venue_ids: list = None,
                    size: int = 10, offset: int = 0) -> Any:
    """Legacy Paper QA Search (¥0.05/call). Prefer paper_qa_search_pro; use this only for topic_* OR/AND."""
    _track_cost("paper_qa_search")
    body: dict = {"use_topic": use_topic, "size": size, "offset": offset}
    optional = {
        "query": query, "topic_high": topic_high, "topic_middle": topic_middle,
        "topic_low": topic_low, "title": title, "doi": doi, "year": year,
        "author_terms": author_terms, "org_terms": org_terms,
        "author_id": author_id, "org_id": org_id, "venue_ids": venue_ids,
    }
    body.update({k: v for k, v in optional.items() if v})
    if sci_flag:
        body["sci_flag"] = True
    if n_citation_flag:
        body["n_citation_flag"] = True
    if force_citation_sort:
        body["force_citation_sort"] = True
    if force_year_sort:
        body["force_year_sort"] = True
    return _request(token, "POST", "/api/paper/qa/search", body=body)


def paper_qa_search_pro(
    token: str,
    query: str = None,
    query_type: str = "auto",
    cursor: str = None,
    authors: list = None,
    author_ids: list = None,
    organizations: list = None,
    organization_ids: list = None,
    venues: list = None,
    venue_ids: list = None,
    year_values: list = None,
    year_from: int = None,
    year_to: int = None,
    languages: list = None,
    language_preference: str = None,
    has_chinese_title: bool = None,
    has_abstract: bool = None,
    min_citations: int = None,
    max_citations: int = None,
    all_terms: list = None,
    any_terms: list = None,
    exclude_terms: list = None,
    search_in: str = None,
    paper_ids: list = None,
    exclude_paper_ids: list = None,
    dois: list = None,
    sort: str = None,
) -> Any:
    """Paper QA Search Pro (¥0.70/call): NL + filters; fixed 10/page; cursor pagination."""
    _track_cost("paper_qa_search_pro")
    if cursor:
        return _request(
            token, "POST", "/api/v3/paper/qa/searchPro", body={"cursor": cursor}
        )
    body: dict = {}
    if query is not None:
        body["query"] = query
    if query_type is not None:
        body["query_type"] = query_type
    optional = {
        "authors": authors,
        "author_ids": author_ids,
        "organizations": organizations,
        "organization_ids": organization_ids,
        "venues": venues,
        "venue_ids": venue_ids,
        "year_values": year_values,
        "year_from": year_from,
        "year_to": year_to,
        "languages": languages,
        "language_preference": language_preference,
        "has_chinese_title": has_chinese_title,
        "has_abstract": has_abstract,
        "min_citations": min_citations,
        "max_citations": max_citations,
        "all_terms": all_terms,
        "any_terms": any_terms,
        "exclude_terms": exclude_terms,
        "search_in": search_in,
        "paper_ids": paper_ids,
        "exclude_paper_ids": exclude_paper_ids,
        "dois": dois,
        "sort": sort,
    }
    for key, value in optional.items():
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        body[key] = value
    return _request(token, "POST", "/api/v3/paper/qa/searchPro", body=body)


def paper_info(token: str, ids: list) -> Any:
    """Paper Info (Free): batch-retrieve basic information by ID."""
    _track_cost("paper_info")
    return _request(token, "POST", "/api/paper/info", body={"ids": ids})


def paper_detail(token: str, paper_id: str) -> Any:
    """Paper Details (¥0.01/call): retrieve complete paper information."""
    _track_cost("paper_detail")
    return _request(token, "GET", "/api/paper/detail", params={"id": paper_id})


def paper_relation(token: str, paper_id: str) -> Any:
    """Paper Citations (¥0.10/call): retrieve papers cited by this paper."""
    _track_cost("paper_relation")
    return _request(token, "GET", "/api/paper/relation", params={"id": paper_id})


def paper_list_by_keywords(token: str, keywords: list, page: int = 0, size: int = 10) -> Any:
    """Paper Batch Query (¥0.10/call): retrieve paper abstracts and info via multiple keywords."""
    _track_cost("paper_list_by_keywords")
    params = {"page": page, "size": size, "keywords": json.dumps(keywords, ensure_ascii=False)}
    return _request(token, "GET", "/api/paper/list/citation/by/keywords", params=params)


def paper_detail_by_condition(token: str, year: int, venue_id: str = None) -> Any:
    """Paper Details by Year and Venue (¥0.20/call): year and venue_id must both be provided; providing only year returns null."""
    _track_cost("paper_detail_by_condition")
    params: dict = {"year": year}
    if venue_id:
        params["venue_id"] = venue_id
    return _request(token, "GET",
                    "/api/paper/platform/allpubs/more/detail/by/ts/org/venue",
                    params=params)


# ──────────────────────────────────────────────────────────────────────────────
# Scholar APIs
# ──────────────────────────────────────────────────────────────────────────────

def person_search(token: str, name: str = None, org: str = None,
                  org_id: list = None, offset: int = 0, size: int = 5) -> Any:
    """Scholar Search (Free): search for scholars by name/institution."""
    _track_cost("person_search")
    body: dict = {"offset": offset, "size": size}
    if name:
        body["name"] = name
    if org:
        body["org"] = org
    if org_id:
        body["org_id"] = org_id
    return _request(token, "POST", "/api/person/search", body=body)


def person_detail(token: str, person_id: str) -> Any:
    """Scholar Details (¥1.00/call): retrieve complete personal information."""
    _track_cost("person_detail")
    return _request(token, "GET", "/api/person/detail", params={"id": person_id})


def person_figure(token: str, person_id: str) -> Any:
    """Scholar Portrait (¥0.50/call): retrieve research interests, domains, and structured history."""
    _track_cost("person_figure")
    return _request(token, "GET", "/api/person/figure", params={"id": person_id})


def person_paper_relation(token: str, person_id: str) -> Any:
    """Scholar Papers (¥1.50/call): retrieve list of papers published by a scholar."""
    _track_cost("person_paper_relation")
    return _request(token, "GET", "/api/person/paper/relation", params={"id": person_id})


def person_patent_relation(token: str, person_id: str) -> Any:
    """Scholar Patents (¥1.50/call): retrieve a scholar's patent list."""
    _track_cost("person_patent_relation")
    return _request(token, "GET", "/api/person/patent/relation", params={"id": person_id})


def person_project(token: str, person_id: str) -> Any:
    """Scholar Projects (¥1.50/call): retrieve research projects (funding amount/dates/source)."""
    _track_cost("person_project")
    return _request(token, "GET", "/api/project/person/v3/open", params={"id": person_id})


# ──────────────────────────────────────────────────────────────────────────────
# Institution APIs
# ──────────────────────────────────────────────────────────────────────────────

def org_search(token: str, orgs: list) -> Any:
    """Org Search (Free): search for institutions by name keyword."""
    _track_cost("org_search")
    return _request(token, "POST", "/api/organization/search", body={"orgs": orgs})


def org_detail(token: str, ids: list) -> Any:
    """Org Details (¥0.01/call): retrieve institution details by ID."""
    _track_cost("org_detail")
    return _request(token, "POST", "/api/organization/detail", body={"ids": ids})


def org_person_relation(token: str, org_id: str, offset: int = 0) -> Any:
    """Org Scholars (¥0.50/call): retrieve affiliated scholars (10 per call)."""
    _track_cost("org_person_relation")
    return _request(token, "GET", "/api/organization/person/relation",
                    params={"org_id": org_id, "offset": offset})


def org_paper_relation(token: str, org_id: str, offset: int = 0) -> Any:
    """Org Papers (¥0.10/call): retrieve papers published by institution scholars (10 per call)."""
    _track_cost("org_paper_relation")
    return _request(token, "GET", "/api/organization/paper/relation",
                    params={"org_id": org_id, "offset": offset})


def org_patent_relation(token: str, org_id: str,
                        page: int = 1, page_size: int = 100) -> Any:
    """Org Patents (¥0.10/call): retrieve institution patent list with pagination (max page_size 10,000)."""
    _track_cost("org_patent_relation")
    return _request(token, "GET", "/api/organization/patent/relation",
                    params={"id": org_id, "page": page, "page_size": page_size})


def org_disambiguate(token: str, org: str) -> Any:
    """Org Disambiguation (¥0.01/call): retrieve the normalized institution name."""
    _track_cost("org_disambiguate")
    return _request(token, "POST", "/api/organization/na", body={"org": org})


def org_disambiguate_pro(token: str, org: str) -> Any:
    """Org Disambiguation Pro (¥0.05/call): extract primary and secondary institution IDs."""
    _track_cost("org_disambiguate_pro")
    return _request(token, "POST", "/api/organization/na/pro", body={"org": org})


# ──────────────────────────────────────────────────────────────────────────────
# Journal APIs
# ──────────────────────────────────────────────────────────────────────────────

def venue_search(token: str, name: str) -> Any:
    """Venue Search (Free): search for journal ID and standard name by name."""
    _track_cost("venue_search")
    return _request(token, "POST", "/api/venue/search", body={"name": name})


def venue_detail(token: str, venue_id: str) -> Any:
    """Venue Details (¥0.20/call): retrieve ISSN, abbreviation, type, etc."""
    _track_cost("venue_detail")
    return _request(token, "POST", "/api/venue/detail", body={"id": venue_id})


def venue_paper_relation(token: str, venue_id: str, offset: int = 0,
                         limit: int = 20, year: Optional[int] = None) -> Any:
    """Venue Papers (¥0.10/call): retrieve journal paper list (supports year filtering)."""
    _track_cost("venue_paper_relation")
    body: dict = {"id": venue_id, "offset": offset, "limit": limit}
    if year is not None:
        body["year"] = year
    return _request(token, "POST", "/api/venue/paper/relation", body=body)


# ──────────────────────────────────────────────────────────────────────────────
# Patent APIs
# ──────────────────────────────────────────────────────────────────────────────

def patent_search(token: str, query: str, page: int = 0, size: int = 10) -> Any:
    """Patent Search (Free): search patents by name/keyword."""
    _track_cost("patent_search")
    return _request(token, "POST", "/api/patent/search",
                    body={"query": query, "page": page, "size": size})


def patent_info(token: str, patent_id: str) -> Any:
    """Patent Info (Free): retrieve basic patent information (title/patent number/inventor)."""
    _track_cost("patent_info")
    return _request(token, "GET", "/api/patent/info", params={"id": patent_id})


def patent_detail(token: str, patent_id: str) -> Any:
    """Patent Details (¥0.01/call): retrieve complete patent information (abstract/filing date/IPC, etc.)."""
    _track_cost("patent_detail")
    return _request(token, "GET", "/api/patent/detail", params={"id": patent_id})


# ──────────────────────────────────────────────────────────────────────────────
# Combined Workflows
# ──────────────────────────────────────────────────────────────────────────────

def workflow_scholar_profile(token: str, name: str) -> dict:
    """
    Workflow 1: Scholar Profile
    Search scholar → details + portrait + papers + patents + projects
    """
    print(f"[1/6] Searching scholar: {name}", file=sys.stderr)
    search_result = person_search(token, name=name, size=5)
    if not search_result or not search_result.get("data"):
        return {"error": f"Scholar not found: {name}"}

    candidates = search_result["data"]
    scholar = candidates[0]
    person_id = scholar.get("id") or scholar.get("_id")
    print(f"      Found: {scholar.get('name')} ({scholar.get('org')}), ID={person_id}", file=sys.stderr)

    result = {
        "source_api_chain": [
            "person_search",
            "person_detail",
            "person_figure",
            "person_paper_relation",
            "person_patent_relation",
            "person_project",
        ],
        "search_candidates": candidates[:3],
        "selected": {
            "id": person_id,
            "name": scholar.get("name"),
            "name_zh": scholar.get("name_zh"),
            "org": scholar.get("org"),
            "interests": scholar.get("interests"),
            "n_citation": scholar.get("n_citation"),
        }
    }

    print("[2/6] Fetching scholar details (parallel)...", file=sys.stderr)
    tasks = {
        "detail": lambda: person_detail(token, person_id),
        "figure": lambda: person_figure(token, person_id),
        "papers": lambda: person_paper_relation(token, person_id),
        "patents": lambda: person_patent_relation(token, person_id),
        "projects": lambda: person_project(token, person_id),
    }
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fn): key for key, fn in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                resp = future.result()
            except Exception as e:
                print(f"  [{key}] failed: {e}", file=sys.stderr)
                continue
            data = resp.get("data") if resp else None
            if not data:
                continue
            if key == "detail":
                result["detail"] = data
            elif key == "figure":
                result["figure"] = data
            elif key == "papers":
                result["papers"] = data[:20]
                result["papers_total"] = resp.get("total", len(data))
            elif key == "patents":
                result["patents"] = data[:10]
            elif key == "projects":
                result["projects"] = data[:10]

    return result


def workflow_paper_deep_dive(token: str, title: str = None, keyword: str = None,
                              author: str = None, order: str = "n_citation") -> dict:
    """
    Workflow 2: Paper Deep Dive
    Search paper → details + citation chain + basic info of cited papers
    """
    print(f"[1/4] Searching paper: title={title}, keyword={keyword}", file=sys.stderr)
    if keyword or author:
        search_result = paper_search_pro(token, title=title, keyword=keyword,
                                         author=author, order=order, size=5)
        search_api = "paper_search_pro"
    else:
        search_result = paper_search(token, title=title or keyword, size=5)
        search_api = "paper_search"
        if not search_result or not search_result.get("data"):
            # Fall back to pro search when title search yields no results to improve recall
            print("      Title search returned no results; falling back to paper_search_pro...", file=sys.stderr)
            search_result = paper_search_pro(token, title=title, keyword=title,
                                             author=author, order=order, size=5)
            search_api = "paper_search_pro(fallback)"

    if not search_result or not search_result.get("data"):
        return {"error": "No relevant papers found"}

    papers = search_result["data"]
    top_paper = papers[0]
    paper_id = top_paper.get("id") or top_paper.get("_id")
    print(f"      Found: {top_paper.get('title')[:60]}, ID={paper_id}", file=sys.stderr)

    result = {
        "source_api_chain": [
            search_api,
            "paper_detail",
            "paper_relation",
            "paper_info",
        ],
        "search_candidates": papers[:5],
        "selected_id": paper_id,
        "selected_title": top_paper.get("title"),
    }

    print("[2/4] Fetching paper details...", file=sys.stderr)
    detail = paper_detail(token, paper_id)
    if detail and detail.get("data"):
        result["detail"] = detail["data"]

    print("[3/4] Fetching citation relationships...", file=sys.stderr)
    relation = paper_relation(token, paper_id)
    if relation and relation.get("data"):
        # data structure: [{"_id": "<paper_id>", "cited": [{...}, ...]}]
        # the outer array wraps each paper; the actual citation list is in the cited field
        all_cited = []
        for item in relation["data"]:
            all_cited.extend(item.get("cited") or [])
        result["citations_count"] = len(all_cited)
        result["citations_preview"] = all_cited[:10]

        cited_ids = [c.get("_id") or c.get("id") for c in all_cited[:20]
                     if c.get("_id") or c.get("id")]
        if cited_ids:
            print(f"[4/4] Batch-fetching basic info for {len(cited_ids)} cited papers...", file=sys.stderr)
            info = paper_info(token, cited_ids)
            if info and info.get("data"):
                result["cited_papers_info"] = info["data"]
        else:
            print("[4/4] Skipping (no cited IDs)", file=sys.stderr)
    else:
        print("[4/4] Skipping (no citation data)", file=sys.stderr)

    return result


def workflow_org_analysis(token: str, org: str) -> dict:
    """
    Workflow 3: Org Analysis
    Org disambiguation pro → details + scholars + papers + patents
    """
    print(f"[1/5] Disambiguating org: {org}", file=sys.stderr)
    disamb = org_disambiguate_pro(token, org)
    org_id = None

    if disamb and disamb.get("data"):
        data = disamb["data"]
        if isinstance(data, list) and data:
            first = data[0]
            org_id = first.get("一级ID") or first.get("二级ID")
        elif isinstance(data, dict):
            org_id = data.get("一级ID") or data.get("二级ID")

    if not org_id:
        print("      Disambiguation pro returned no ID; trying org search...", file=sys.stderr)
        search_r = org_search(token, [org])
        if search_r and search_r.get("data"):
            orgs = search_r["data"]
            org_id = orgs[0].get("org_id") if orgs else None

    if not org_id:
        return {"error": f"Could not find org ID: {org}"}

    print(f"      Org ID: {org_id}", file=sys.stderr)
    result = {
        "source_api_chain": [
            "org_disambiguate_pro",
            "org_detail",
            "org_person_relation",
            "org_paper_relation",
            "org_patent_relation",
        ],
        "org_query": org,
        "org_id": org_id,
        "disambiguate": disamb,
    }

    print("[2/5] Fetching org data (parallel)...", file=sys.stderr)
    tasks = {
        "detail": lambda: org_detail(token, [org_id]),
        "scholars": lambda: org_person_relation(token, org_id, offset=0),
        "papers": lambda: org_paper_relation(token, org_id, offset=0),
        "patents": lambda: org_patent_relation(token, org_id, page=1, page_size=100),
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn): key for key, fn in tasks.items()}
        for future in as_completed(futures):
            key = futures[future]
            try:
                resp = future.result()
            except Exception as e:
                print(f"  [{key}] failed: {e}", file=sys.stderr)
                continue
            data = resp.get("data") if resp else None
            if not data:
                continue
            if key == "detail":
                result["detail"] = data
            elif key == "scholars":
                result["scholars"] = data
                result["scholars_total"] = resp.get("total", len(data))
            elif key == "papers":
                result["papers"] = data
                result["papers_total"] = resp.get("total", len(data))
            elif key == "patents":
                result["patents"] = data
                result["patents_total"] = resp.get("total", len(data))

    return result


def workflow_venue_papers(token: str, venue: str, year: Optional[int] = None,
                           limit: int = 20) -> dict:
    """
    Workflow 4: Venue Papers
    Venue search → venue details + papers by year
    """
    print(f"[1/3] Searching venue: {venue}", file=sys.stderr)
    search_result = venue_search(token, venue)
    if not search_result or not search_result.get("data"):
        return {"error": f"Venue not found: {venue}"}

    venues = search_result["data"]
    top_venue = venues[0]
    venue_id = top_venue.get("id")
    print(f"      Found: {top_venue.get('name_en')}, ID={venue_id}", file=sys.stderr)
    result = {
        "source_api_chain": [
            "venue_search",
            "venue_detail",
            "venue_paper_relation",
        ],
        "search_candidates": venues[:3],
        "venue_id": venue_id,
    }

    print("[2/3] Fetching venue details...", file=sys.stderr)
    detail = venue_detail(token, venue_id)
    if detail and detail.get("data"):
        result["venue_detail"] = detail["data"]

    print(f"[3/3] Fetching venue papers (year={year}, limit={limit})...", file=sys.stderr)
    papers = venue_paper_relation(token, venue_id, year=year, limit=limit)
    if papers and papers.get("data"):
        result["papers"] = papers["data"]
        result["papers_total"] = papers.get("total", len(papers["data"]))

    return result


def workflow_paper_qa(token: str, query: str = None,
                      topic_high: str = None, topic_middle: str = None,
                      sci_flag: bool = False, sort_citation: bool = False, sort_year: bool = False,
                      author_id: list = None, org_id: list = None, venue_ids: list = None,
                      size: int = 10,
                      year_from: int = None, year_to: int = None,
                      min_citations: int = None, cursor: str = None) -> dict:
    """
    Workflow: Paper QA Search — prefer Pro, use legacy sparingly.
    - Default: natural language / filters → paper_qa_search_pro (¥0.70, fixed 10/page)
    - Rare: only topic_high/topic_middle → legacy paper_qa_search (¥0.05)
    """
    # Structured topic_* exists only on the legacy endpoint; avoid unless required.
    if topic_high or topic_middle:
        print(f"[1/1] Legacy topic QA search: topic_high={bool(topic_high)}", file=sys.stderr)
        qa_result = paper_qa_search(
            token, query=query, use_topic=True,
            topic_high=topic_high, topic_middle=topic_middle,
            sci_flag=sci_flag, force_citation_sort=sort_citation,
            force_year_sort=sort_year,
            author_id=author_id, org_id=org_id, venue_ids=venue_ids,
            size=size,
        )
        if isinstance(qa_result, dict):
            qa_result["source_api_chain"] = ["paper_qa_search"]
            qa_result["route"] = "paper_qa_search"
        return qa_result

    sort = None
    if sort_citation:
        sort = "citation"
    elif sort_year:
        sort = "recent"

    print(f"[1/1] Paper QA Search Pro: query={query}, sort={sort}", file=sys.stderr)
    qa_result = paper_qa_search_pro(
        token,
        query=query,
        query_type="auto",
        cursor=cursor,
        author_ids=author_id,
        organization_ids=org_id,
        venue_ids=venue_ids,
        year_from=year_from,
        year_to=year_to,
        min_citations=min_citations,
        sort=sort,
    )
    data = (qa_result or {}).get("data") or {}
    items = data.get("items") if isinstance(data, dict) else None
    if qa_result and qa_result.get("code") == 200 and items:
        qa_result["source_api_chain"] = ["paper_qa_search_pro"]
        qa_result["route"] = "paper_qa_search_pro"
        return qa_result

    if query and not cursor:
        print("      paper_qa_search_pro returned no results; falling back to paper_search_pro...", file=sys.stderr)
        order = "n_citation" if sort_citation or not sort_year else "year"
        fallback = paper_search_pro(token, keyword=query, order=order, size=min(size, 10))
        fb_data = (fallback or {}).get("data") or []
        return {
            "code": 200 if fb_data else (qa_result or {}).get("code", -1),
            "success": bool(fb_data),
            "msg": "" if fb_data else "no data",
            "data": fb_data,
            "total": (fallback or {}).get("total", len(fb_data)),
            "route": "paper_qa_search_pro -> paper_search_pro",
            "source_api_chain": ["paper_qa_search_pro", "paper_search_pro"],
            "primary_result": qa_result,
        }

    if isinstance(qa_result, dict):
        qa_result["source_api_chain"] = ["paper_qa_search_pro"]
        qa_result["route"] = "paper_qa_search_pro"
    return qa_result


def workflow_patent_search(token: str, query: str, page: int = 0, size: int = 10) -> dict:
    """
    Workflow 6: Patent Search and Details
    Patent search → retrieve details for each patent
    """
    print(f"[1/2] Searching patents: {query}", file=sys.stderr)
    search_result = patent_search(token, query, page=page, size=size)
    if not search_result or not search_result.get("data"):
        return {"error": f"No patents found: {query}"}

    patents = search_result["data"]
    result = {
        "source_api_chain": ["patent_search", "patent_detail"],
        "search_results": patents,
        "total": len(patents),
    }

    top_patents = [p for p in patents[:3] if p.get("id")]
    print(f"[2/2] Fetching details for {len(top_patents)} patents (parallel)...", file=sys.stderr)
    details = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(patent_detail, token, p["id"]): p["id"] for p in top_patents}
        for fut in as_completed(futs):
            try:
                d = fut.result()
                if d and d.get("data"):
                    details.append(d["data"])
            except Exception as e:
                print(f"  [patent_detail] failed: {e}", file=sys.stderr)
    result["details"] = details
    return result


def workflow_scholar_patents(token: str, name: str) -> dict:
    """
    Retrieve patent list + individual patent details for a scholar by name
    """
    print(f"[1/3] Searching scholar: {name}", file=sys.stderr)
    search_result = person_search(token, name=name, size=3)
    if not search_result or not search_result.get("data"):
        return {"error": f"Scholar not found: {name}"}

    scholar = search_result["data"][0]
    person_id = scholar.get("id")
    print(f"      Found: {scholar.get('name')}, ID={person_id}", file=sys.stderr)
    result = {"scholar": scholar}

    print("[2/3] Fetching scholar patent list...", file=sys.stderr)
    patents = person_patent_relation(token, person_id)
    if not patents or not patents.get("data"):
        return {**result, "patents": [], "error": "No patent data for this scholar"}
    patent_list = patents["data"]
    result["patents_list"] = patent_list

    top_patents = [p for p in patent_list[:3] if p.get("patent_id")]
    print(f"[3/3] Fetching details for {len(top_patents)} patents (parallel)...", file=sys.stderr)
    details = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(patent_detail, token, p["patent_id"]): p["patent_id"]
                for p in top_patents}
        for fut in as_completed(futs):
            try:
                d = fut.result()
                if d and d.get("data"):
                    details.append(d["data"])
            except Exception as e:
                print(f"  [patent_detail] failed: {e}", file=sys.stderr)
    result["patent_details"] = details
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Command-Line Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="AMiner Open Platform Academic Data Query Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scholar profile analysis
  python aminer_client.py --token <TOKEN> --action scholar_profile --name "Andrew Ng"

  # Paper deep dive
  python aminer_client.py --token <TOKEN> --action paper_deep_dive --title "BERT"
  python aminer_client.py --token <TOKEN> --action paper_deep_dive --keyword "large language model" --author "Hinton"

  # Institution research capability analysis
  python aminer_client.py --token <TOKEN> --action org_analysis --org "Tsinghua University"

  # Journal paper monitoring
  python aminer_client.py --token <TOKEN> --action venue_papers --venue "NeurIPS" --year 2023

  # Academic Q&A (default: paper_qa_search_pro)
  python aminer_client.py --token <TOKEN> --action paper_qa --query "deep learning for protein structure"
  python aminer_client.py --token <TOKEN> --action paper_qa \\
    --query "graph neural network" --sort_citation --year_from 2020 --min_citations 50
  python aminer_client.py --token <TOKEN> --action paper_qa \\
    --topic_high '[["transformer","self-attention"],["protein folding"]]' \\
    --sci_flag --sort_citation

  # Patent search
  python aminer_client.py --token <TOKEN> --action patent_search --query "quantum computing chip"

  # Scholar patents
  python aminer_client.py --token <TOKEN> --action scholar_patents --name "Shou-Cheng Zhang"

  # Direct single API call
  python aminer_client.py --token <TOKEN> --action raw \\
    --api paper_search --params '{"title":"BERT","page":0,"size":5}'

Console (Generate Token): https://open.aminer.cn/open/board?tab=control
Docs: https://open.aminer.cn/open/docs
        """
    )
    p.add_argument(
        "--token",
        default=None,
        help=(
            "AMiner API Token. If not provided, reads from the environment variable AMINER_API_KEY by default; "
            "or go to https://open.aminer.cn/open/board?tab=control to generate one."
        ),
    )
    p.add_argument("--action", required=True,
                   choices=["scholar_profile", "paper_deep_dive", "org_analysis",
                            "venue_papers", "paper_qa", "patent_search",
                            "scholar_patents", "raw"],
                   help="Action to perform")

    # General parameters
    p.add_argument("--name", help="Scholar name")
    p.add_argument("--title", help="Paper title")
    p.add_argument("--keyword", help="Keyword")
    p.add_argument("--author", help="Author name")
    p.add_argument("--org", help="Institution name")
    p.add_argument("--venue", help="Journal name")
    p.add_argument("--query", help="Query string (natural language Q&A or patent search)")
    p.add_argument("--year", type=int, help="Year filter")
    p.add_argument("--size", type=int, default=10, help="Number of results to return")
    p.add_argument("--page", type=int, default=0, help="Page number")
    p.add_argument("--page_size", type=int, default=100,
                   help="Org patent pagination size (max 10,000)")
    p.add_argument("--order", default="n_citation",
                   choices=["n_citation", "year"], help="Sort order")

    # Paper QA specific
    p.add_argument("--topic_high", help="Required keyword array (JSON string; outer AND, inner OR)")
    p.add_argument("--topic_middle", help="Strongly boosted keywords (same format as topic_high)")
    p.add_argument("--sci_flag", action="store_true", help="Return SCI papers only")
    p.add_argument("--sort_citation", action="store_true", help="Sort by citation count")
    p.add_argument("--sort_year", action="store_true", help="Sort by year (most recent first)")
    p.add_argument("--author_id", help="Author ID filter; accepts single ID or JSON array string")
    p.add_argument("--org_id", help="Institution ID filter; accepts single ID or JSON array string")
    p.add_argument("--venue_ids", help="Conference/journal ID filter; accepts JSON array string")
    p.add_argument("--year_from", type=int, help="[paper_qa pro] start year (inclusive)")
    p.add_argument("--year_to", type=int, help="[paper_qa pro] end year (inclusive)")
    p.add_argument("--min_citations", type=int, help="[paper_qa pro] minimum citation count")
    p.add_argument("--cursor", help="[paper_qa pro] pagination cursor from previous next_cursor")

    # Raw mode
    p.add_argument("--api", help="[raw mode] API function name, e.g. paper_search")
    p.add_argument("--params", help="[raw mode] Parameter dictionary in JSON format")

    # Dry run
    p.add_argument("--dry-run", action="store_true", dest="dry_run",
                   help="Preview the API call chain and estimated cost without sending requests")

    return p


WORKFLOW_DRY_RUN_INFO = {
    "scholar_profile": [
        ("person_search", 0), ("person_detail", 1.00), ("person_figure", 0.50),
        ("person_paper_relation", 1.50), ("person_patent_relation", 1.50), ("person_project", 1.50),
    ],
    "paper_deep_dive": [
        ("paper_search", 0), ("paper_detail", 0.01), ("paper_relation", 0.10), ("paper_info", 0),
    ],
    "org_analysis": [
        ("org_disambiguate_pro", 0.05), ("org_detail", 0.01),
        ("org_person_relation", 0.50), ("org_paper_relation", 0.10), ("org_patent_relation", 0.10),
    ],
    "venue_papers": [
        ("venue_search", 0), ("venue_detail", 0.20), ("venue_paper_relation", 0.10),
    ],
    "paper_qa": [("paper_qa_search_pro", 0.70)],
    "patent_search": [("patent_search", 0), ("patent_detail", 0.01)],
    "scholar_patents": [
        ("person_search", 0), ("person_patent_relation", 1.50), ("patent_detail", 0.01),
    ],
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    token = (args.token or os.getenv("AMINER_API_KEY") or "").strip()

    if args.dry_run:
        info = WORKFLOW_DRY_RUN_INFO.get(args.action, [])
        if not info:
            print(f"[Dry Run] No preview available for action '{args.action}'.")
        else:
            total = sum(p for _, p in info)
            print(f"[Dry Run] Action: {args.action}")
            for i, (api, price) in enumerate(info, 1):
                label = "Free" if price == 0 else f"¥{price:.2f}"
                print(f"  {i}. {api} ({label})")
            print(f"  Estimated total: ¥{total:.2f}")
        return

    if not token or not token.strip():
        parser.error(
            "Missing --token; cannot call AMiner API. Please go to "
            "https://open.aminer.cn/open/board?tab=control to generate a token first."
        )

    def _parse_id_filter(value: Optional[str]) -> Optional[list]:
        if not value:
            return None
        # Accepts a single ID string or a JSON array string
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, str) and parsed.strip():
                return [parsed.strip()]
        except Exception:
            pass
        return [value.strip()] if value.strip() else None

    if args.action == "scholar_profile":
        if not args.name:
            parser.error("--action scholar_profile requires --name")
        result = workflow_scholar_profile(token, args.name)

    elif args.action == "paper_deep_dive":
        if not args.title and not args.keyword:
            parser.error("--action paper_deep_dive requires --title or --keyword")
        result = workflow_paper_deep_dive(
            token, title=args.title, keyword=args.keyword,
            author=args.author, order=args.order
        )

    elif args.action == "org_analysis":
        if not args.org:
            parser.error("--action org_analysis requires --org")
        result = workflow_org_analysis(token, args.org)

    elif args.action == "venue_papers":
        if not args.venue:
            parser.error("--action venue_papers requires --venue")
        result = workflow_venue_papers(token, args.venue, year=args.year, limit=args.size)

    elif args.action == "paper_qa":
        if not args.query and not args.topic_high:
            parser.error("--action paper_qa requires --query or --topic_high")
        if args.sort_citation and args.sort_year:
            parser.error("--sort_citation and --sort_year cannot both be enabled")
        author_id_filter = _parse_id_filter(args.author_id)
        org_id_filter = _parse_id_filter(args.org_id)
        venue_ids_filter = _parse_id_filter(args.venue_ids)
        result = workflow_paper_qa(
            token, query=args.query,
            topic_high=args.topic_high, topic_middle=args.topic_middle,
            sci_flag=args.sci_flag, sort_citation=args.sort_citation, sort_year=args.sort_year,
            author_id=author_id_filter, org_id=org_id_filter, venue_ids=venue_ids_filter,
            size=args.size,
            year_from=args.year_from, year_to=args.year_to,
            min_citations=args.min_citations, cursor=args.cursor,
        )

    elif args.action == "patent_search":
        if not args.query:
            parser.error("--action patent_search requires --query")
        result = workflow_patent_search(token, args.query, page=args.page, size=args.size)

    elif args.action == "scholar_patents":
        if not args.name:
            parser.error("--action scholar_patents requires --name")
        result = workflow_scholar_patents(token, args.name)

    elif args.action == "raw":
        if not args.api:
            parser.error("--action raw requires --api (API function name)")
        RAW_API_ALLOWLIST = {
            "paper_search": paper_search,
            "paper_search_pro": paper_search_pro,
            "paper_qa_search": paper_qa_search,
            "paper_qa_search_pro": paper_qa_search_pro,
            "paper_info": paper_info,
            "paper_detail": paper_detail,
            "paper_relation": paper_relation,
            "paper_list_by_keywords": paper_list_by_keywords,
            "paper_detail_by_condition": paper_detail_by_condition,
            "person_search": person_search,
            "person_detail": person_detail,
            "person_figure": person_figure,
            "person_paper_relation": person_paper_relation,
            "person_patent_relation": person_patent_relation,
            "person_project": person_project,
            "org_search": org_search,
            "org_detail": org_detail,
            "org_person_relation": org_person_relation,
            "org_paper_relation": org_paper_relation,
            "org_patent_relation": org_patent_relation,
            "org_disambiguate": org_disambiguate,
            "org_disambiguate_pro": org_disambiguate_pro,
            "venue_search": venue_search,
            "venue_detail": venue_detail,
            "venue_paper_relation": venue_paper_relation,
            "patent_search": patent_search,
            "patent_info": patent_info,
            "patent_detail": patent_detail,
        }
        fn = RAW_API_ALLOWLIST.get(args.api)
        if fn is None:
            allowed = ", ".join(sorted(RAW_API_ALLOWLIST.keys()))
            parser.error(f"API function not found: {args.api}. Available APIs: {allowed}")
        kwargs = json.loads(args.params) if args.params else {}
        result = fn(token, **kwargs)

    else:
        parser.print_help()
        sys.exit(1)

    _print(result)

    cost = get_cost_summary()
    if cost["calls"] > 0:
        parts = [f"{k}: ¥{v:.2f}" if v > 0 else f"{k}: Free"
                 for k, v in sorted(cost["breakdown"].items())]
        print(f"\n[Cost] ¥{cost['total']:.2f} total, {cost['calls']} API calls "
              f"({', '.join(parts)})", file=sys.stderr)


if __name__ == "__main__":
    main()
