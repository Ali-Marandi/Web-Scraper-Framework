#!/usr/bin/env python3
"""Cross-round paper-set state file for aminer-deep-search (no network access).

Hundreds of collected papers do not fit in the host model's context, so this
CLI keeps them in a JSON state file and deduplicates by AMiner paper ID.

Subcommands (stdout is always a single JSON document):
  add     merge papers from stdin (JSON array) or --ids into the state file
  stats   totals, expanded seeds, and year distribution
  export  write the final [{"id","title"}] list and report path + count
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_STATE_FILE = "outputs/paper_set.json"


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"papers": {}, "expanded_seeds": []}
    with path.open("r", encoding="utf-8") as file:
        state = json.load(file)
    state.setdefault("papers", {})
    state.setdefault("expanded_seeds", [])
    return state


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def _normalize_items(raw_items: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise ValueError("input must be a JSON array of papers")
    items: list[dict[str, Any]] = []
    for raw in raw_items:
        if isinstance(raw, str):
            items.append({"id": raw.strip()})
        elif isinstance(raw, dict):
            items.append(raw)
    return items


def cmd_add(args: argparse.Namespace) -> dict[str, Any]:
    if args.ids:
        items = [{"id": paper_id} for paper_id in args.ids]
    else:
        stdin_text = sys.stdin.read().strip()
        if not stdin_text:
            raise ValueError("no input: pipe a JSON array to stdin or pass --ids")
        items = _normalize_items(json.loads(stdin_text))

    state_path = Path(args.file)
    state = _load_state(state_path)
    papers: dict[str, dict[str, Any]] = state["papers"]
    expanded: set[str] = set(state["expanded_seeds"])

    added = 0
    duplicates = 0
    for item in items:
        paper_id = str(item.get("id") or item.get("_id") or "").strip()
        if not paper_id:
            continue
        # source_paper_ids on an item means those seeds have been expanded
        for seed_id in item.get("source_paper_ids") or []:
            expanded.add(str(seed_id))
        if paper_id in papers:
            duplicates += 1
            existing = papers[paper_id]
            for key, value in item.items():
                if key != "source_paper_ids" and value not in (None, "", []):
                    existing.setdefault(key, value)
        else:
            added += 1
            papers[paper_id] = {
                key: value for key, value in item.items()
                if key != "source_paper_ids" and value not in (None, "", [])
            }

    state["expanded_seeds"] = sorted(expanded)
    _save_state(state_path, state)
    return {"added": added, "duplicates": duplicates, "total": len(papers)}


def cmd_mark_expanded(args: argparse.Namespace) -> dict[str, Any]:
    state_path = Path(args.file)
    state = _load_state(state_path)
    expanded = set(state["expanded_seeds"])
    expanded.update(str(paper_id).strip() for paper_id in args.ids if str(paper_id).strip())
    state["expanded_seeds"] = sorted(expanded)
    _save_state(state_path, state)
    return {"expanded_seeds": state["expanded_seeds"]}


def cmd_stats(args: argparse.Namespace) -> dict[str, Any]:
    state = _load_state(Path(args.file))
    papers = state["papers"]
    by_year: dict[str, int] = {}
    missing_title = 0
    for paper in papers.values():
        year = paper.get("year")
        key = str(year) if year else "unknown"
        by_year[key] = by_year.get(key, 0) + 1
        if not paper.get("title"):
            missing_title += 1
    return {
        "total": len(papers),
        "expanded_seeds": state["expanded_seeds"],
        "missing_title": missing_title,
        "by_year": dict(sorted(by_year.items(), reverse=True)),
    }


def cmd_export(args: argparse.Namespace) -> dict[str, Any]:
    state = _load_state(Path(args.file))
    final = [
        {"id": paper_id, "title": paper.get("title", "")}
        for paper_id, paper in state["papers"].items()
        if paper.get("title")
    ]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as file:
        json.dump(final, file, ensure_ascii=False, indent=2)
    return {"count": len(final), "path": str(out_path)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deduplicated paper-set state file (stdout: JSON only, no network)."
    )
    parser.add_argument("--file", default=DEFAULT_STATE_FILE,
                        help=f"State file path (default {DEFAULT_STATE_FILE}).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Merge papers from stdin JSON array or --ids.")
    p_add.add_argument("--ids", nargs="*", default=None,
                       help="Add bare paper IDs instead of reading stdin.")
    p_add.set_defaults(func=cmd_add)

    p_mark = sub.add_parser("mark-expanded", help="Record seed IDs whose references were expanded.")
    p_mark.add_argument("--ids", nargs="+", required=True)
    p_mark.set_defaults(func=cmd_mark_expanded)

    p_stats = sub.add_parser("stats", help="Show totals, expanded seeds, and year distribution.")
    p_stats.set_defaults(func=cmd_stats)

    p_export = sub.add_parser("export", help="Write the final [{id,title}] list.")
    p_export.add_argument("-o", "--output", default="outputs/final_papers.json")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": "invalid_input", "message": str(exc)},
                         ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
