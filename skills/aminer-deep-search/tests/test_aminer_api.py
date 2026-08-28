from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_DIR / "scripts" / "aminer_api.py"
SPEC = importlib.util.spec_from_file_location("aminer_deep_search_api", MODULE_PATH)
assert SPEC and SPEC.loader
api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = api
SPEC.loader.exec_module(api)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def run_main(argv, urlopen):
    """Run the CLI with a fake transport; return (exit_code, stdout, stderr)."""
    stdout, stderr = io.StringIO(), io.StringIO()
    env = {"AMINER_API_KEY": "test-token"}
    api._call_counts.clear()
    with mock.patch.dict(os.environ, env, clear=True), \
            mock.patch.object(api.urllib.request, "urlopen", urlopen), \
            contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = api.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def paper_info_response(request):
    body = json.loads(request.data.decode("utf-8"))
    return FakeResponse({
        "code": 200, "success": True,
        "data": [
            {"id": pid, "title": f"Title {pid}",
             "year": (2000 + int(pid)) if pid.isdigit() else 2015,
             "venue": {"raw": "Venue X"}, "abstract_slice": "abs " * 200}
            for pid in body["ids"]
        ],
    })


class SearchTests(unittest.TestCase):
    def test_search_paginates_filters_year_and_enriches(self):
        search_pages = {
            0: [{"id": "1", "title": "P1"}, {"id": "2", "title": "P2"}] +
               [{"id": str(i), "title": f"P{i}"} for i in range(3, 21)],
            1: [{"id": "21", "title": "P21"}],
        }
        calls = {"search": [], "info": 0}

        def fake_urlopen(request, timeout):
            url = request.full_url
            if "/api/paper/search/pro" in url:
                self.assertIn("keyword=graph", url)
                self.assertIn("order=n_citation", url)
                page = int(url.split("page=")[1].split("&")[0])
                calls["search"].append(page)
                return FakeResponse({"code": 200, "success": True,
                                     "data": search_pages.get(page, [])})
            if "/api/paper/info" in url:
                calls["info"] += 1
                return paper_info_response(request)
            raise AssertionError(f"unexpected url: {url}")

        code, out, err = run_main(
            ["search", "--query", "graph", "--size", "30",
             "--year", "2010", "--order", "n_citation", "--max-pages", "3"],
            fake_urlopen,
        )
        self.assertEqual(code, 0)
        papers = json.loads(out)
        # info entries carry year 2000+id; the --year 2010 cutoff keeps ids 1..10 and none from page 1 (id 21)
        self.assertEqual([p["id"] for p in papers], [str(i) for i in range(1, 11)])
        self.assertEqual(papers[0]["venue"], "Venue X")
        self.assertLessEqual(len(papers[0]["abstract_slice"]), api.ABSTRACT_SLICE_LIMIT)
        self.assertEqual(calls["search"], [0, 1])  # stops after exhausting pages
        self.assertIn("[cost]", err)
        self.assertNotIn("[cost]", out)  # stdout stays pure JSON

    def test_missing_key_returns_structured_error(self):
        stdout = io.StringIO()
        api._call_counts.clear()
        with mock.patch.dict(os.environ, {}, clear=True), \
                contextlib.redirect_stdout(stdout):
            code = api.main(["search", "--query", "x"])
        self.assertEqual(code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"], "missing_aminer_api_key")
        self.assertNotIn("test-token", stdout.getvalue())


class InfoTests(unittest.TestCase):
    def test_info_batches_at_most_100_ids(self):
        batch_sizes = []

        def fake_urlopen(request, timeout):
            self.assertIn("/api/paper/info", request.full_url)
            body = json.loads(request.data.decode("utf-8"))
            batch_sizes.append(len(body["ids"]))
            return FakeResponse({"code": 200, "success": True,
                                 "data": [{"id": pid, "title": f"T{pid}"} for pid in body["ids"]]})

        ids = [str(i) for i in range(150)]
        code, out, _ = run_main(["info", "--ids", *ids], fake_urlopen)
        self.assertEqual(code, 0)
        self.assertEqual(batch_sizes, [100, 50])
        self.assertEqual(len(json.loads(out)), 150)


class ReferencesTests(unittest.TestCase):
    def test_references_extracts_cited_excludes_seeds_and_tracks_sources(self):
        def fake_urlopen(request, timeout):
            url = request.full_url
            if "/api/paper/relation" in url:
                seed = url.split("id=")[1]
                cited = {
                    "s1": [{"_id": "a"}, {"_id": "b"}, {"_id": "s2"}],
                    "s2": [{"_id": "b"}, {"_id": "c"}],
                }[seed]
                return FakeResponse({"code": 200, "success": True,
                                     "data": [{"_id": seed, "cited": cited}]})
            if "/api/paper/info" in url:
                return paper_info_response(request)
            raise AssertionError(f"unexpected url: {url}")

        code, out, _ = run_main(["references", "--ids", "s1", "s2"], fake_urlopen)
        self.assertEqual(code, 0)
        papers = {p["id"]: p for p in json.loads(out)}
        self.assertEqual(set(papers), {"a", "b", "c"})  # seed s2 excluded
        self.assertEqual(papers["a"]["source_paper_ids"], ["s1"])
        self.assertEqual(papers["b"]["source_paper_ids"], ["s1", "s2"])

    def test_per_seed_limit(self):
        def fake_urlopen(request, timeout):
            url = request.full_url
            if "/api/paper/relation" in url:
                cited = [{"_id": f"r{i}"} for i in range(30)]
                return FakeResponse({"code": 200, "success": True,
                                     "data": [{"_id": "s1", "cited": cited}]})
            if "/api/paper/info" in url:
                return paper_info_response(request)
            raise AssertionError(f"unexpected url: {url}")

        code, out, _ = run_main(["references", "--ids", "s1", "--per-seed", "5"], fake_urlopen)
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(out)), 5)


class QaSearchTests(unittest.TestCase):
    def test_qa_search_always_uses_topic_mode(self):
        captured = {}

        def fake_urlopen(request, timeout):
            url = request.full_url
            if "/api/paper/qa/search" in url:
                captured["body"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse({"code": 200, "success": True,
                                     "data": [{"id": "1", "title": "P1"}]})
            if "/api/paper/info" in url:
                return paper_info_response(request)
            raise AssertionError(f"unexpected url: {url}")

        code, out, _ = run_main(
            ["qa-search", "--query", "GNN scalability",
             "--topic-high", '[["graph neural network"]]', "--size", "5"],
            fake_urlopen,
        )
        self.assertEqual(code, 0)
        # with use_topic=false the backend ignores `query` (only reads `title`),
        # yielding empty terms and envelope 403 — so the script must always send true
        self.assertIs(captured["body"]["use_topic"], True)
        self.assertEqual(captured["body"]["query"], "GNN scalability")
        self.assertEqual(captured["body"]["topic_high"], '[["graph neural network"]]')
        self.assertEqual(json.loads(out)[0]["id"], "1")

    def test_qa_search_requires_query_or_topic(self):
        code, out, _ = run_main(["qa-search"], lambda *a, **k: None)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["error"], "invalid_request")


class TransportTests(unittest.TestCase):
    def test_http_200_with_error_code_in_envelope_is_reported(self):
        def fake_urlopen(request, timeout):
            return FakeResponse({"code": 403, "success": True, "msg": "no data", "data": None})

        code, out, _ = run_main(
            ["qa-search", "--query", "scalable GNN approaches"], fake_urlopen,
        )
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload["error"], "api_error")
        self.assertEqual(payload["code"], 403)


    def test_non_retryable_http_error_fails_fast(self):
        attempts = []

        def fake_urlopen(request, timeout):
            attempts.append(1)
            raise api.urllib.error.HTTPError(
                request.full_url, 401, "Unauthorized", {},
                io.BytesIO(b'{"msg":"bad token"}'),
            )

        code, out, _ = run_main(["info", "--ids", "x"], fake_urlopen)
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload["status"], 401)
        self.assertEqual(len(attempts), 1)


if __name__ == "__main__":
    unittest.main()
