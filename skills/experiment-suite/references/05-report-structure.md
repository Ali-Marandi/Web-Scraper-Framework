# Experiment Report Structure

## Why this exists

The pipeline emits a 30-line `experiment_report.md`:

```markdown
# Experiment Report: <topic>

**Task:** ...
**Dataset:** ...
**Data contract:** `data_contract.md`

## Results Summary
| Method | ... |

## Charts
![Chart](...)

## Code
Runnable code skeleton in `experiment/`.
```

That's a placeholder. A real experiment report is a **standalone deliverable**: a reader who has only the report, none of the code or PDFs, should understand what was done, how, and what was found. This reference defines that.

**Hard target:** `experiment_report.md` ≥ 800 words, structured into the seven sections below, citing the figures and tables by filename.

## Required structure

### 1. Header + provenance disclosure

The first lines of the report:

```markdown
# Experiment Report: <topic>

**Authored by:** AI4S Agent (with human review strongly recommended before publication or production use)
**Mode:** Simulated (numbers from `experiment-suite/scripts/simulator.py`)  ← or "Measured" / "Mixed"
**Date:** YYYY-MM-DD
**Hardware (if measured):** 1× A100 80GB, 38h wall-clock total
**Data contract:** `data_contract.md`
```

If simulated, follow with a 2-sentence prominent disclaimer block:

```markdown
> **Notice:** numerical results in this report are simulated to demonstrate the experiment-suite workflow. Production decisions must replace these numbers with measurements from the released code; see `experiment/README.md` for how to run.
```

### 2. Problem statement

Re-state the research question and hypothesis from `experiment_design.md` in 1–2 paragraphs. The reader of the report may not have read the design doc; the report stands alone.

### 3. Design rationale

A condensed version of `experiment_design.md` §§ 2–6: which datasets, which baselines, which metrics, what the ablation plan was, what the protocol was. Aim for ~300 words; full justification stays in the design doc.

If the dataset was agent-discovered, say so explicitly and name the repository/accession or stable source route.

### 4. Method (briefly)

The model / approach being evaluated. Reference `experiment/model.py` for implementation detail. 1–2 paragraphs is enough.

### 5. Results

The substantive section. Two passes:

**5.a — Headline numbers.** A markdown table summarising the main comparison. Format:

```markdown
| Method | ETTm1 | Electricity | Traffic | Weather |
|---|---|---|---|---|
| DLinear      | 0.382 | 0.166 | 0.434 | 0.241 |
| ...          | ...   | ...   | ...   | ...   |
| **Ours**     | **0.354** | **0.149** | **0.402** | **0.220** |

*Three-seed mean. Numbers are simulated.*
```

**5.b — Figures.** Embed each figure with a markdown reference + brief surrounding prose:

```markdown
![Method comparison](figures/fig_02_method_comparison.pdf)

*Figure 2.* MSE on ETTm1 across methods, with three-seed error bars. The patched configuration (Ours) is consistently best, with a roughly 8% improvement over DLinear at horizon 720. Numbers are simulated.
```

### 6. Analysis

Beyond the table: what does the result mean? Aim for 3–5 paragraphs covering:

- **Where the method wins / loses.** Don't bury the dataset where your method underperforms.
- **What the ablation tells us.** Which component carries the gain. Reference Fig 3 / Table 2.
- **Cost vs. accuracy trade-off.** Compute / latency relative to baselines.
- **Surprises.** Anything that contradicted the design's expected effect direction.

### 7. Limitations

A real experiment package has limitations. List 3–5:

- Datasets / domains not covered
- Failure modes the metrics don't capture
- Compute / hyperparameter budget constraints
- Confounds and how they were (or weren't) controlled

### 8. Reproduction

Closing block — how to reproduce the experiment:

```markdown
## Reproduction

1. Install: `pip install -r experiment/requirements.txt`
2. Configure: edit `experiment/config.yaml` to point at your dataset
3. Run: `python experiment/train.py --config experiment/config.yaml`
4. Evaluate: `python experiment/evaluate.py --checkpoint <path>`

Expected wall-clock per configuration: ≈ 30 min on 1× A100. Configurations × seeds × ablations = 24 runs ≈ 12 hours.
```

## Length guidance

| Section | Target words |
|---|---|
| 1. Header + disclosure | 60–120 |
| 2. Problem | 100–200 |
| 3. Design rationale | 250–350 |
| 4. Method | 100–200 |
| 5. Results (5.a + 5.b) | 200–400 |
| 6. Analysis | 300–500 |
| 7. Limitations | 100–200 |
| 8. Reproduction | 80–150 |
| **Total** | **≥ 800** |

## Anti-patterns

- **Marketing prose.** "Our method achieves state-of-the-art performance across all benchmarks." No claim that's not in the table.
- **Hidden simulated mode.** If the report doesn't say "simulated" in the header and again in the figure captions, it's misleading.
- **Walls of bullet points.** A real report has paragraphs that argue. Bullets are for enumerating limitations / steps, not for saying things.
- **Missing reproduction block.** A reader can't try the experiment without knowing how.
- **Figure dump.** Embedding 8 figures with no surrounding prose doesn't help a reader.

## Quick checklist

- [ ] Header includes provenance mode (simulated / measured / mixed)
- [ ] Header includes `data_contract.md`
- [ ] Disclosure block visible in §1 if simulated
- [ ] Problem and hypothesis re-stated (report stands alone)
- [ ] Design rationale condensed (datasets / baselines / metrics)
- [ ] Method paragraph references `experiment/model.py`
- [ ] Headline table with `**Ours**` bolded; "Numbers are simulated" caption if applicable
- [ ] Each figure embedded with a brief surrounding paragraph
- [ ] Analysis names where the method loses, not just wins
- [ ] Limitations explicit (3–5 items)
- [ ] Reproduction block with concrete commands and time estimate
- [ ] Total ≥ 800 words
