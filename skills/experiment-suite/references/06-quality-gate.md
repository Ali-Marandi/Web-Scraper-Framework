# Experiment-Suite Quality Gate — Self-Check Before Delivery

## Why this exists

This checklist runs **after** drafting and assembling, **before** declaring the experiment package complete. If any gate fails, return to the relevant reference.

The gate is bright-line. Do not soften the targets to ship.

## Hard gates (must pass)

### G1 · Design depth

```bash
test -s experiment_design.md && [ $(wc -w < experiment_design.md) -ge 700 ]
test -s data_contract.md
```

Must include the seven sections from `references/01-design-depth.md`: hypothesis, datasets, baselines, metrics, protocol, ablations, limitations.

### G2 · Code skeleton runs (imports cleanly)

```bash
cd experiment
for m in model data train evaluate; do
  python -c "import importlib; m = importlib.import_module('$m'); print('$m: OK')"
done
```

All four must import without error. Then check for placeholders:

```bash
grep -rE "^\s*pass\s*$|# TODO|raise NotImplementedError" experiment/*.py | head
# Should be empty (or only inside genuinely-optional hooks).
```

### G3 · `requirements.txt` matches imports

```bash
grep -h "^import \|^from " experiment/*.py | awk '{print $2}' | cut -d. -f1 | sort -u
# Compare against requirements.txt — every third-party import should be listed.
```

### G4 · `README.md` has install + launch instructions

```bash
grep -E "pip install|python train.py|python evaluate.py" experiment/README.md
```

Must include all three lines (install, launch, evaluate) or equivalents.

### G5 · `results.json` schema valid

```python
import json
r = json.load(open("results.json"))
required = {"task", "dataset", "metrics", "seeds", "provenance", "summary"}
assert not (required - set(r.keys())), f"missing: {required - set(r.keys())}"
assert r["provenance"].get("mode") in {"simulated", "measured", "mixed"}
print("OK")
```

If mode is `measured`, the provenance should also point to `data_contract.md` directly or indirectly.

### G6 · Figures present and publication-grade

```bash
[ $(ls figures/*.pdf 2>/dev/null | wc -l) -ge 3 ]
test -f figures/manifest.json
test -f figures/figure_contract.md
```

For each figure:
- vector PDF (not raster)
- has a sibling `make_fig_*.py` script
- listed in `manifest.json` with `id`, `path_pdf`, `caption`, `section`
- should also have sibling `.svg` / `.tiff` when the environment supports them

### G7 · Report depth

```bash
test -s experiment_report.md && [ $(wc -w < experiment_report.md) -ge 800 ]
```

Must contain the seven sections from `references/05-report-structure.md`. Search for section headings:

```bash
grep -E "^## (Problem|Design|Method|Results|Analysis|Limitations|Reproduction)" experiment_report.md | wc -l
# Should be ≥ 6
```

### G8 · Provenance disclosed wherever numbers appear

If `results.json` provenance mode is `simulated`:

```bash
grep -i "simulated" experiment_report.md     # must appear in header + figure captions
grep -i "simulated" figures/manifest.json    # captions should say "Numbers are simulated."
```

If mode is `measured`:

```bash
grep -i "simulated" experiment_report.md     # should NOT appear (otherwise inconsistent)
grep -i "measured\|three-seed\|hardware" experiment_report.md   # should appear in §1 header
```

If mode is `mixed`:

```bash
grep -i "mixed\|partially\|by_method" experiment_report.md      # should explicitly explain
```

If mode is `measured` and the data were agent-discovered or reused public data:

```bash
grep -i "data contract" experiment_report.md
grep -i "repository\|accession\|doi\|source" data_contract.md
```

## Soft gates (should pass)

### S1 · No marketing prose in the report

```bash
grep -E "state-of-the-art|cutting-edge|comprehensive|extensive|novel" experiment_report.md | head
```

These phrases aren't categorically wrong but should be sparse and earned.

### S2 · No hidden numbers

```bash
# Numbers in the report must be traceable to results.json
# (Manual check; eyeball that every number in the headline table appears in results.json["summary"].)
```

### S3 · Code is callable end-to-end (smoke)

For experiments where compute permits:

```bash
cd experiment
# Run with --quick or a tiny config to verify the pipeline doesn't crash.
# This is optional but a powerful confidence check.
```

### S4 · Visuals make sense

Open each figure PDF. Check:
- Axes labelled, legend readable at print scale
- Watermark "simulated" present iff mode is simulated
- Colors from the publication palette (no default cycle)
- Hero panel / supporting panel hierarchy matches `figures/figure_contract.md`

### S5 · Multi-seed reporting

```python
import json
r = json.load(open("results.json"))
n_seeds = r.get("seeds", [])
if len(n_seeds) < 3:
    print(f"WARNING: only {len(n_seeds)} seeds — disclose in report.")
```

## Final report format

When all gates pass:

```
Experiment package ready: output/experiment-suite/<slug>/

Stats:
  Design:        912 words, 7 sections
  Code:          model.py 184 lines, data.py 96 lines, train.py 128 lines, evaluate.py 64 lines
  Results:       schema valid, mode=simulated, 3 seeds, 4 datasets × 4 horizons
  Figures:       5 (2 method comparison, 1 ablation panel, 1 heatmap, 1 training curves)
  Report:        1240 words, 8 sections
  Disclosure:    "simulated" present in report header, every figure caption, results.json provenance

Quality gate: PASSED (G1–G8 hard, S1–S5 soft).
```

If any hard gate cannot honestly be cleared:

> "Code skeleton imports cleanly but `train.py` has a `NotImplementedError` in the loss-weighting branch — leaving in place because the design called for it as an optional extension; the main loss path is functional."

That's a legitimate deviation. Padding the design to 700 words with filler is not.

## Quick checklist

- [ ] G1 design ≥ 700 words, all 7 sections present
- [ ] `data_contract.md` exists and matches the design / results provenance
- [ ] G2 all 4 modules import cleanly; no `pass`/`TODO`/`NotImplementedError` in core paths
- [ ] G3 requirements.txt matches actual imports
- [ ] G4 README has install + launch + evaluate commands
- [ ] G5 results.json schema valid with provenance
- [ ] G6 ≥ 3 figures, vector PDF, all in manifest
- [ ] Figure contract written before plotting; export bundle present when possible
- [ ] G7 report ≥ 800 words, 7 sections
- [ ] G8 provenance consistent across report / figures / results.json
- [ ] S1–S5 soft gates reviewed
- [ ] Honest report — don't pad to clear gates
