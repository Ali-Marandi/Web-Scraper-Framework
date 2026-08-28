---
name: experiment-suite
description: Use when the user has a research question and needs a complete experiment package — design document, runnable code, results (measured or simulated with honest provenance), publication-grade figures, structured report. Single-stage, no Python runtime.
---

# Experiment Suite

## Overview

End-to-end experiment package builder. **Single stage, full quality from the start.** The agent (Claude Code / Cursor / Aider / Codex / …) writes everything directly using its own tools (Write, Bash, WebFetch, …). This skill contains procedure + reference playbooks + figure-example scripts — no Python runtime, no LLM SDK.

The substantive work is decomposed into reference playbooks under `references/`:

| Reference | Topic |
|---|---|
| `references/00-incremental-execution.md` | how to do this without losing work: batches, persistence, resume — **read first** |
| `references/01-design-depth.md` | what a real experiment design contains (motivation → hypothesis → datasets → baselines → metrics → ablations → budget) |
| `references/01a-data-contract.md` | runtime dataset binding: source, access route, version, split, and reuse boundary |
| `references/02-code-quality.md` | code-skeleton standards — runnable `model.py`, `data.py`, `train.py`, `evaluate.py` |
| `references/03-results-protocol.md` | `results.json` schema; `measured` / `simulated` / `illustrative` provenance |
| `references/04-publication-figures.md` | publication-grade charts, multi-panel layouts, taste rules |
| `references/04a-figure-contract.md` | figure logic before plotting: conclusion, panel map, reviewer risk |
| `references/04b-figure-qa.md` | export bundle, editable text, statistics and image-integrity QA |
| `references/05-report-structure.md` | structured `experiment_report.md` (problem → design → method → results → analysis → limitations) |
| `references/06-quality-gate.md` | self-check before delivery |

Also: `figure_examples/` — publication-style matplotlib scripts plus a shared style kit the agent can use as starting points.

**Read the relevant reference _before_ writing, not after.** The full pass does not fit in a single turn — `references/00-incremental-execution.md` is the only execution mode that completes.

## When to Use

- User wants to "design an experiment" for a research question.
- User needs runnable code for a specific task (classification / forecasting / detection / …).
- User wants to compare methods and have a structured report at the end.
- User needs publication-quality figures of experimental results.

## When NOT to Use

- User only wants a quick code snippet (write code directly).
- User wants a full paper → `paper-writer`.
- User wants a literature survey → `literature-survey`.

## Workflow

### Step 1 — Understand the question and operating mode

Confirm with the user:

- **Research question** — what we are trying to answer.
- **Task type** — classification / regression / forecasting / detection / generation / …
- **Mode**
  - **measured** — user has real data or will run code themselves; provide a path to a measured `results.json` or run `train.py` against real data later.
  - **simulated** (default) — agent generates a plausible-shaped, deterministic `results.json` as a placeholder. Every figure/table caption must say "simulated".
- **Framework preference** — PyTorch (default), JAX, TensorFlow, or sklearn.
- **Compute budget** — hours / GPUs available; constrains the code skeleton and hyperparameter plan.

If the user has data and time, push toward measured mode. If not, simulated is acceptable **provided** disclosures are honest in every artefact.

### Step 2 — Set up the run directory

```bash
QUESTION="<research_question>"
SLUG=$(python3 -c "import re,hashlib,sys; t=sys.argv[1]; n=re.sub(r'[\\s_]+','-',re.sub(r'[^\\w\\s-]','',t.lower().strip())).strip('-')[:40].rstrip('-'); h=hashlib.sha1(t.encode()).hexdigest()[:8]; print(f'{n}-{h}')" "$QUESTION")
TS=$(date +%Y-%m-%d_%H%M%S)
RUN=output/experiment-suite/$SLUG/$TS

mkdir -p "$RUN/experiment" "$RUN/figures"
ln -sfn "$TS" "output/experiment-suite/$SLUG/latest"
```

In commands below `$RUN` = `output/experiment-suite/<slug>/latest`.

The agent will create five top-level files inside `$RUN/`:

- `experiment_design.md`
- `data_contract.md`
- `experiment/{model.py,data.py,train.py,evaluate.py,config.yaml,requirements.txt,README.md}`
- `results.json`
- `figures/*.pdf` plus their `make_*.py` source and a `manifest.json`
- `experiment_report.md`

### Step 3 — Build the package (REQUIRED — this is the whole job)

Open `references/00-incremental-execution.md` first. Then carry out the six tracks below across many turns, persisting state to `$RUN/` after every batch.

#### 3.1 Design — full justification document

**Open:** `references/01-design-depth.md` and `references/01a-data-contract.md`. First write `$RUN/data_contract.md` as the dataset contract for this run. It must say whether the data are user-supplied, agent-discovered, reused public, controlled, or synthetic fallback. Then write `$RUN/experiment_design.md` as a real design (≥ 700 words): motivation → hypothesis → datasets → baselines → metrics → ablations → compute budget. Justify every choice.

#### 3.2 Code — actually runnable

**Open:** `references/02-code-quality.md`. Fill `$RUN/experiment/` with code that an engineer could launch with `python train.py --config config.yaml`. Real (if minimal) model class, real data loader, real train loop, real eval. The generated `data.py` and `config.yaml` are runtime products of this run and should bind to `$RUN/data_contract.md`, not to a repository-wide hard-coded benchmark. Add a `README.md` with run instructions.

#### 3.2.5 Execute (if execution environment is available)

**Priority order for execution:**

1. **Sandbox MCP** (`sandbox_execute`) — preferred for formal experiments.
   - Generates measured `results.json` with real execution output.
   - Smart timeout (auto-calculated from code complexity), auto-retry on missing packages.
   - Call: `sandbox_execute(code=<entire_script>, timeout=300, requirements=["torch","scikit-learn"])`

2. **Jupyter MCP** — preferred for interactive exploration and debugging.
   - Write code as notebook cells, execute via `jupyter_execute_cell`.
   - Good for data loading verification and quick smoke tests.

3. **Agent Bash** — fallback for simple scripts.
   - `python experiment/train.py` directly.

If **NO** execution environment is available, fall back to "simulated" mode (current behavior).

**When execution succeeds:**

- Set `provenance.mode = "measured"` in `results.json`
- Include `execution_time` from sandbox/Jupyter output
- Run `execution-guard` gate **BEFORE** execution
- Run `correctness` gate **AFTER** execution

**Auto-measured results protocol:**

When the sandbox runs the code successfully, parse the stdout into a structured `results.json`:

```json
{
  "provenance": {
    "mode": "measured",
    "source": "sandbox_execute via SANDBOX_API_BASE",
    "execution_time": 15.3,
    "timestamp": "2026-07-08T14:30:00Z"
  }
}
```

If execution partially succeeds (some metrics computed, others failed), use `"mode": "mixed"` with `by_method` provenance (see `references/03-results-protocol.md`).

#### 3.3 Results — honest provenance

**Open:** `references/03-results-protocol.md`. Produce `$RUN/results.json` with a well-formed schema: per-seed entries, per-method per-metric mean & std, ablation block, and a `provenance` field that names the source.

- **measured mode** — the user runs `experiment/train.py` (or supplies a results JSON) and the agent loads it into `$RUN/results.json`, setting `"simulated": false` and `"provenance": "loaded from <path>"`.
- **measured mode, agent-discovered data** — the agent may search for and bind an open dataset itself, but the chosen source, split, and access route must first be written into `$RUN/data_contract.md`; `results.json` provenance must point back to that binding.
- **simulated mode** — the agent writes a deterministic seeded JSON of plausible shape, setting `"simulated": true`.

#### 3.4 Figures — 3–6 publication-grade

**Open:** `references/04-publication-figures.md`, `references/04a-figure-contract.md`, `references/04b-figure-qa.md`, and `figure_examples/`. Before writing plotting code, define the figure contract in a small working note under `$RUN/figures/figure_contract.md`:

- one-sentence conclusion,
- figure archetype,
- panel map,
- evidence hierarchy,
- statistics needed,
- reviewer risk.

Then plan and generate at minimum:

- 1 method-comparison chart (bar or line).
- 1 ablation breakdown.
- Optionally training curves, scaling plot, heatmap.

Save each figure into `$RUN/figures/<basename>.pdf` with its `make_*.py` source alongside. Prefer saving an editable `.svg` and print-grade `.tiff` alongside the PDF when the environment supports it. Append entries to `$RUN/figures/manifest.json` storing **basenames only** (never absolute paths) so paper-writer can copy them in directly. Apply the shared publication style (embedded fonts, explicit palette, panel labels, simulated watermark when applicable).

If simulated, watermark the figures or always note "simulated" in their captions in the report.

#### 3.5 Report — structured

**Open:** `references/05-report-structure.md`. Write `$RUN/experiment_report.md` with sections: problem statement → design rationale → method → setup → results → analysis → limitations. Reference figures by filename. This report is the primary deliverable for users who want only the experiment package (no paper-writer follow-up).

#### 3.6 Quality gate

**Open:** `references/06-quality-gate.md`. Targets: design ≥ 700 words, code imports cleanly (`python -c "import experiment.model"` from inside `$RUN`), `results.json` passes schema check, ≥ 3 figures, report ≥ 6 sections.

### Step 4 — Deliver

Report:

1. `output/experiment-suite/<slug>/latest/experiment_design.md`
2. `output/experiment-suite/<slug>/latest/experiment/` — runnable code package.
3. `output/experiment-suite/<slug>/latest/results.json` — with provenance.
4. `output/experiment-suite/<slug>/latest/figures/` — publication-grade charts + `manifest.json`.
5. `output/experiment-suite/<slug>/latest/experiment_report.md` — structured report.
6. Stats per the report format in `references/06-quality-gate.md`.

## Cross-skill data flow (path convention)

The `paper-writer` skill computing the same slug for the same topic will look here:

- `output/experiment-suite/<slug>/latest/results.json` — source of the numbers and the `"simulated"` flag (drives the disclosure clause in the paper).
- `output/experiment-suite/<slug>/latest/figures/*.pdf` (+ `manifest.json`) — figures to reuse rather than redraw.

Always store **basenames** in `manifest.json`. Absolute paths in the manifest break paper-writer's `\includegraphics{figures/<basename>}`.

## Important rules

- **No LLM SDK in this skill.** No `import anthropic` / `import openai`. The skill is SKILL.md + references + figure examples only.
- **Simulated results must always remain visibly labelled** — in `results.json` (`"simulated": true`), in figure captions, in the report's top-of-page disclosure, and in any downstream paper's `\thanks` footnote.
- **Never present simulated results as measured.** When in doubt, treat as simulated and disclose.
- The runnable code is a starting point, not a SOTA reproduction. Be honest about its scope in `experiment/README.md`.
- A real experiment package would normally take days of compute for real numbers; the simulated path lets the workflow proceed when that's not possible, with honest disclosure throughout.
