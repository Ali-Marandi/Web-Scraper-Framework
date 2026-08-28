from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_DIR / "scripts" / "paper_set.py"
SPEC = importlib.util.spec_from_file_location("aminer_deep_search_paper_set", MODULE_PATH)
assert SPEC and SPEC.loader
paper_set = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = paper_set
SPEC.loader.exec_module(paper_set)


def run_main(argv, stdin_text=None):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        if stdin_text is not None:
            with mock.patch.object(sys, "stdin", io.StringIO(stdin_text)):
                code = paper_set.main(argv)
        else:
            code = paper_set.main(argv)
    return code, stdout.getvalue()


class PaperSetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = str(Path(self.tmp.name) / "paper_set.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_from_stdin_dedupes_and_counts(self):
        items = [
            {"id": "a", "title": "Paper A", "year": 2020},
            {"id": "b", "title": "Paper B"},
        ]
        code, out = run_main(["--file", self.state, "add"], json.dumps(items))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"added": 2, "duplicates": 0, "total": 2})

        again = [{"id": "a", "title": "Paper A"}, {"id": "c", "title": "Paper C"}]
        code, out = run_main(["--file", self.state, "add"], json.dumps(again))
        self.assertEqual(json.loads(out), {"added": 1, "duplicates": 1, "total": 3})

    def test_add_bare_ids(self):
        code, out = run_main(["--file", self.state, "add", "--ids", "x", "y", "x"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"added": 2, "duplicates": 1, "total": 2})

    def test_source_paper_ids_mark_seeds_expanded(self):
        items = [{"id": "a", "title": "A", "source_paper_ids": ["seed1", "seed2"]}]
        run_main(["--file", self.state, "add"], json.dumps(items))
        code, out = run_main(["--file", self.state, "stats"])
        stats = json.loads(out)
        self.assertEqual(stats["expanded_seeds"], ["seed1", "seed2"])
        # source_paper_ids must not be persisted onto the paper entry
        state = json.loads(Path(self.state).read_text(encoding="utf-8"))
        self.assertNotIn("source_paper_ids", state["papers"]["a"])

    def test_mark_expanded(self):
        run_main(["--file", self.state, "mark-expanded", "--ids", "s1"])
        code, out = run_main(["--file", self.state, "stats"])
        self.assertEqual(json.loads(out)["expanded_seeds"], ["s1"])

    def test_stats_by_year(self):
        items = [
            {"id": "a", "title": "A", "year": 2021},
            {"id": "b", "title": "B", "year": 2021},
            {"id": "c", "title": "C"},
        ]
        run_main(["--file", self.state, "add"], json.dumps(items))
        _, out = run_main(["--file", self.state, "stats"])
        stats = json.loads(out)
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_year"]["2021"], 2)
        self.assertEqual(stats["by_year"]["unknown"], 1)

    def test_export_shape_and_file(self):
        items = [
            {"id": "a", "title": "Paper A", "year": 2020, "venue": "V"},
            {"id": "no-title"},
        ]
        run_main(["--file", self.state, "add"], json.dumps(items))
        out_path = str(Path(self.tmp.name) / "final.json")
        code, out = run_main(["--file", self.state, "export", "-o", out_path])
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result, {"count": 1, "path": out_path})
        exported = json.loads(Path(out_path).read_text(encoding="utf-8"))
        self.assertEqual(exported, [{"id": "a", "title": "Paper A"}])

    def test_empty_stdin_is_a_structured_error(self):
        code, out = run_main(["--file", self.state, "add"], "")
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out)["error"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
