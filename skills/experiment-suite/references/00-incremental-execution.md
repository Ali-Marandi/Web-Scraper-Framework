# Incremental Execution — How an Experiment Package Actually Gets Built

## Why this exists

A high-quality experiment package has six artefacts (design / code / results / figures / report / quality-checked PDF) and each one is non-trivial. None of this fits into a single LLM tool call. Trying to "do it all in one shot" hits context limits and produces shallow content across the board. This reference defines the only execution mode that works: **incremental, file-persisted, resumable**.

## The three invariants

### Invariant 1 — Filesystem is the source of truth

Each artefact is written to its file the moment it's drafted. The data binding goes to `data_contract.md`, the design to `experiment_design.md`, code to `experiment/<file>.py`, results to `results.json`, figures to `figures/`, report to `experiment_report.md`. If the agent crashes or the user pivots, the files survive.

### Invariant 2 — Progress is observable on disk

```bash
cd output/experiment-suite/<slug>

wc -w experiment_design.md                              # design length
test -s data_contract.md && echo "data contract present"
wc -l experiment/*.py                                    # code length per module
python -c "import json; d=json.load(open('results.json')); print(d.get('provenance'), '|', list(d.keys()))"
ls figures/*.pdf | wc -l                                # figure count
wc -w experiment_report.md                              # report length
```

If any artefact looks thin, return to the relevant reference and expand.

### Invariant 3 — Each batch is small enough to succeed, atomic enough to retry

Batch granularity for this skill:

| Operation | Batch size per turn | Total batches | Persistence |
|---|---|---|---|
| Data binding | 1 contract document | 1 turn | Write `data_contract.md` |
| Design rewrite | 1 design document | 1 turn | Write `experiment_design.md` |
| Code rewrite | 1 module per turn | 4–6 turns (model, data, train, evaluate, config, README) | Write each `experiment/<file>` |
| Results curation | 1 results.json structure | 1 turn | Write `results.json` |
| Figure generation | 1 figure per turn | 3–6 turns | Save script + render + manifest entry |
| Report rewrite | 1–2 sections per turn | 4–6 turns | Edit `experiment_report.md` incrementally |

A turn that tries to write all the code in one shot truncates. A turn that tries 5 figures at once produces shallow figures. One per turn is the rhythm.

## Recovery — when a session resumes mid-task

```bash
cd output/experiment-suite/<slug>

# Design done?
wc -w experiment_design.md       # < 200 words means stub; > 600 means real

# Data binding done?
sed -n '1,120p' data_contract.md

# Code done?
for f in experiment/*.py; do echo "$(basename "$f"): $(wc -l < "$f") lines"; done

# Results well-formed?
python -c "import json; d=json.load(open('results.json')); print('OK' if 'summary' in d else 'STUB')"

# Figures present?
ls figures/*.pdf 2>/dev/null

# Report done?
wc -w experiment_report.md
```

Resume the sub-step that's incomplete. Never redo work that's already on disk.

## Checkpoint files

Maintain four small bookkeeping files in the slug dir:

- `.data_progress.txt` — one line per dataset discovery / binding decision
- `.code_progress.txt` — one line per code module written / rewritten
- `.figure_progress.txt` — one line per figure generated
- `.report_progress.txt` — one line per report section drafted

```bash
echo "dataset-bound: GEO/GSE123456" >> .data_progress.txt
echo "model.py" >> .code_progress.txt
echo "fig_02_method_comparison" >> .figure_progress.txt
echo "results-section-drafted" >> .report_progress.txt
```

## Sanity check before delivery

```bash
test -s data_contract.md
test -s experiment_design.md && [ $(wc -w < experiment_design.md) -gt 700 ]
ls experiment/{model,data,train,evaluate}.py
python -c "import json; d=json.load(open('results.json')); assert 'summary' in d, 'no summary'"
[ $(ls figures/*.pdf 2>/dev/null | wc -l) -ge 3 ]
test -s experiment_report.md && [ $(wc -w < experiment_report.md) -gt 800 ]
```

## Quick checklist

- [ ] Data contract written before code generation
- [ ] Design rewritten in 1 dedicated turn (not interleaved)
- [ ] Code rewritten **one module per turn**
- [ ] Results curated in 1 dedicated turn (schema + provenance)
- [ ] Figures generated **one per turn**, scripts saved alongside renders
- [ ] Report drafted **section by section**
- [ ] Four checkpoint files maintained
- [ ] Compile/run check after each major artefact (e.g., `python -c "import experiment.model"` after writing model.py)
- [ ] Never tried to "do it all in one turn"
