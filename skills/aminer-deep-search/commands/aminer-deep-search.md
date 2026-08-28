---
description: AMiner deep multi-round paper collection for survey references
argument-hint: "[research topic | topic: ... target-size: 400 max-rounds: 12]"
allowed-tools: Read, Bash, Glob, Grep
---

# /aminer-deep-search - AMiner Deep Search

User invoked the AMiner deep paper collection skill with the following arguments:

```text
$ARGUMENTS
```

## Your task

Follow `${CLAUDE_PLUGIN_ROOT}/SKILL.md`. You are the controller: run the tool scripts, read their JSON output, judge relevance yourself, and iterate. There is no external LLM mode and nothing to configure beyond `AMINER_API_KEY`.

Use this command only for deep survey-style paper collection, not for simple paper lookup or lightweight recommendations.

### 1. Parse `$ARGUMENTS`

- `topic`: required research topic. Preserve the user's wording. If absent or too vague, ask for a concrete topic.
- `target-size`: optional final paper target, default 400.
- `max-rounds`: optional round budget, default 12.

### 2. Pre-flight

```bash
[ -z "${AMINER_API_KEY:-}" ] && echo "AMINER_API_KEY missing" || echo "AMINER_API_KEY exists"
```

If missing, stop and tell the user to set `AMINER_API_KEY`. Never print the key. The scripts are pure stdlib — no dependency installation is needed.

### 3. Run the round protocol

Execute the Round Protocol from `${CLAUDE_PLUGIN_ROOT}/SKILL.md`:

- Round 0: derive 4–8 seed queries, estimate cost; confirm with the user if the estimate is ≥¥5.
- Each round (max `max-rounds`): search via
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/aminer_api.py" search --query "..." --order n_citation`,
  filter results for relevance yourself, add the kept items via
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/paper_set.py" add`,
  snowball with `references --ids ...` on ≤5 strong unexpanded seeds, and check `stats`.
- Stop when `target-size` is reached, results are exhausted, or 2 consecutive rounds add <5 papers.

Keep the state file and exports under the current working directory (`outputs/`).

### 4. Present the result

Run `export` and report the final paper count, the total cost (sum of `[cost]` stderr lines), and the output path. If the run fails due to missing configuration or API errors, show the actionable error without exposing secrets. Never fabricate papers.
