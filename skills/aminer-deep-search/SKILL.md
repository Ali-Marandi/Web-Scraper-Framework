---
name: aminer-deep-search
version: 2.0.0
author: AMiner
contact: report@aminer.cn
description: >
  Activate this skill when the user wants deep, multi-round academic paper collection for a survey or literature review.
  The host model (the model running this skill) drives the loop itself: it expands queries, judges relevance, snowballs backward references, and decides when to stop.
  The bundled scripts are pure tool commands that call documented AMiner Open Platform endpoints and print JSON tool results only — no extra LLM configuration is needed.
  Use this skill for broad topic exploration, survey bibliography construction, and collecting hundreds of candidate papers with AMiner IDs and titles.
  Not intended for single-paper lookup or lightweight recommendations; use aminer-free-academic or aminer-daily-paper for those.
metadata:
  {
    "openclaw":
      {
        "requires": {
          "bins": ["python3"],
          "env": ["AMINER_API_KEY"]
        },
        "primaryEnv": "AMINER_API_KEY"
      }
  }
---

# AMiner Deep Search

Host-model-driven survey paper collection. You (the model reading this) are the controller: run the tool scripts, read their JSON output, judge relevance yourself, and iterate until the collection target is met.

## Scope

- Use for: survey bibliography collection (hundreds of papers), keyword expansion, backward-citation snowballing.
- Do not use for: single-paper lookup or Q&A (route to `aminer-free-academic`), personalized recommendations (route to `aminer-daily-paper`).

## Pre-flight

1. Check the key without printing it:

```bash
[ -z "${AMINER_API_KEY:-}" ] && echo "AMINER_API_KEY missing" || echo "AMINER_API_KEY exists"
```

If missing, stop and ask the user to set `AMINER_API_KEY` (console: https://open.aminer.cn/open/board?tab=control). Never print the key.

2. Confirm the `topic` and the `target-size` (default 400). If your round plan is estimated to cost ¥5 or more, tell the user the estimate and get confirmation before starting.

## Tools

Both scripts live in `scripts/` under this skill directory. They print exactly one JSON document to stdout (the tool result); diagnostics and a `[cost]` line go to stderr. They never score relevance — that is your job.

### `scripts/aminer_api.py` — AMiner API calls

| Subcommand | Endpoint | Price |
|---|---|---|
| `search --query Q [--size 20] [--year YYYY] [--order n_citation\|year] [--max-pages 3]` | GET `/api/paper/search/pro` + free `paper/info` enrichment | ¥0.01/page |
| `qa-search [--query "natural language question"] [--topic-high '[["termA","termB"],["termC"]]'] [--size 20] [--year-from Y] [--year-to Y] [--citation-sort]` | POST `/api/paper/qa/search` (always `use_topic=true`; the backend ignores `query` when `use_topic=false`) + free enrichment | ¥0.05/call |
| `info --ids id1 id2 ...` | POST `/api/paper/info` (batched ≤100 ids) | Free |
| `references --ids id1 id2 ... [--per-seed 20]` | GET `/api/paper/relation` per seed + free enrichment | ¥0.10/seed |

Output shape: `search`/`qa-search`/`info` print `[{id, title, year?, venue?, abstract_slice?}]`; `references` additionally includes `source_paper_ids` (which seeds cited the paper). Seeds themselves are excluded from `references` output.

### `scripts/paper_set.py` — cross-round state file (no network)

State file defaults to `outputs/paper_set.json` relative to the working directory.

```bash
# Merge kept results (pipe the filtered JSON array in), dedupe by id
python3 scripts/aminer_api.py search --query "..." | python3 scripts/paper_set.py add
# → {"added": N, "duplicates": M, "total": T}

python3 scripts/paper_set.py stats     # totals, expanded_seeds, by_year
python3 scripts/paper_set.py mark-expanded --ids id1 id2   # record snowballed seeds
python3 scripts/paper_set.py export -o outputs/final_papers.json
```

`add` also accepts `--ids id1 id2 ...` for bare IDs. Items carrying `source_paper_ids` (from `references`) automatically mark those seeds as expanded.

If you want to filter before adding, read the search output first, then pipe only the kept items:

```bash
printf '%s' '[{"id":"...","title":"..."}]' | python3 scripts/paper_set.py add
```

## Round Protocol (core)

### Round 0 — plan

- Derive 4–8 seed queries from the topic: synonyms, subfields, method names, datasets/benchmarks, common English abbreviations.
- Estimate rounds and cost (searches ≈ ¥0.01–0.05 each, references ≈ ¥0.10/seed). If the estimate is ≥¥5, confirm with the user first.

### Each round (default budget: 12 rounds), five fixed steps

1. **Search**: run 1–4 `search` / `qa-search` calls from the pending query queue. Prefer `search` (cheaper); use `qa-search` when the query is a natural-language question.
2. **Filter & add**: read the stdout results, judge relevance to the topic yourself, and pipe only the kept items into `paper_set.py add`. Never add papers you consider off-topic.
3. **Check**: run `stats` to see the total and this round's increment.
4. **Snowball**: from this round's relevant additions pick ≤5 strong seeds (highly relevant, ranked high under `--order n_citation`, not in `expanded_seeds`) and run `references --ids ...`. Filter the output for relevance, then add it. Run `mark-expanded` for seeds that yielded nothing addable.
5. **Decide**: choose the next move —
   - a search returned <5 results or poor quality → replace it with a reformulated query (max 2 variants per direction, then switch to snowballing);
   - references are yielding many relevant papers → keep snowballing from fresh seeds;
   - reached `target-size`, or results are exhausted, or 2 consecutive rounds added <5 papers → terminate.

### Wrap-up

Run `export`, then report: final paper count, total cost (sum the `[cost]` stderr lines), and the output path.

## Rules

1. Never fabricate paper IDs or titles; only cite data actually returned by the tools.
2. Free first: metadata always comes from the free `paper/info` (the scripts already do this); never call the paid `paper/detail` for bulk metadata.
3. Keep the raw tool output out of your final answer; report counts and the exported file path instead.
4. Never print or log `AMINER_API_KEY`.
5. If AMiner returns fewer papers than the target, report the real count instead of inventing papers.
