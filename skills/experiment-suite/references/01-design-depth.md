# Experiment Design Depth

## Why this exists

The pipeline emits a 5-line design stub like:
```
**Task:** Transformer-based time series forecasting
**Dataset:** Synthetic dataset
**Methods:** Baseline A, Baseline B
**Metrics:** Accuracy, F1-Score, Runtime
```

That's not a design — it's a placeholder. A real experiment design tells someone else why your decisions are the right ones. This reference defines what a real design contains.

**Hard target:** `experiment_design.md` ≥ 700 words, structured into the seven sections below. Every choice (dataset, baseline, metric, ablation) carries a justification, not just a name.

## Required structure

### 1. Research question and hypothesis

State the question precisely (one paragraph) and convert it into a falsifiable hypothesis. The hypothesis should name the expected effect direction and a rough magnitude.

> *We test whether channel-independent patched attention reduces long-horizon MSE by ≥ 5% on ETT benchmarks compared to point-wise attention, while not increasing compute by more than 1.3×.*

If the question doesn't compress into a falsifiable form, weaken it until it does. Vague questions ("how does X work?") produce vague experiments.

### 2. Datasets

For each dataset:
- **Name** and **citation**
- **Source route** — user-supplied, agent-discovered, reused public, controlled, or synthetic fallback
- **Repository / accession / DOI / stable URL** when available
- **Why this dataset** — what makes it appropriate for the question (size, domain, structure)
- **Splits** — train / val / test sizes, how they were obtained
- **Pre-processing** — normalisation, windowing, encoding
- **Access / licence condition** — public, controlled, licensed, or local-only
- **Known limitations** — biases, age, label-noise issues

If the experiment uses 1 dataset, justify why one is enough. If 5+, justify why so many.

The dataset section must agree with `$RUN/data_contract.md`. Do not let the design and the runtime
binding drift apart.

### 3. Baselines

A real comparison needs the right baselines. Group them by family:

- **Lower-bound baselines**: dumb baselines (mean, last-value, linear regression). If your method doesn't beat these, something is wrong.
- **Same-paradigm baselines**: other methods solving the same problem with the same paradigm.
- **Adjacent-paradigm baselines**: rival paradigms (e.g., for a Transformer paper: linear, MLP, state-space).
- **Optional zero-shot reference**: foundation models / pretrained baselines.

For each baseline cite a primary source, name the implementation used (released code or our re-implementation), and note the hyperparameter budget allocated.

### 4. Metrics

Three failure modes here:

- Reporting too few metrics (one number per method) hides regressions.
- Reporting too many metrics (10+) spreads the signal thin.

Aim for **3–6 metrics** of distinct types: at least one accuracy-like, one cost-like (compute / latency / memory), and one robustness-like (worst-case / variance / OOD).

For each metric: name, units, direction (lower / higher better), why it matters for the research question, what value range is meaningful.

### 5. Protocol

- **Seeds**: minimum 3, ideally 5. Report mean ± std, not single-run numbers.
- **Hyperparameter search**: same budget per method (e.g., 30 trials). Document the search space, including ranges and distributions.
- **Hardware**: name the accelerator(s) and approximate wall-clock per configuration.
- **Implementation**: framework, key library versions, deterministic flags.
- **Cross-validation**: forecasting is autoregressive — use rolling-origin / time-series CV per~\cite{bergmeir2018cv} (or its equivalent for your task), not random k-fold.

### 6. Ablations

A method usually has 3–6 components. The ablation plan removes them one at a time on a representative dataset / horizon. List the planned ablations explicitly:

| Ablation | What it removes | Expected effect direction | Why it tests our hypothesis |
|---|---|---|---|

Without an ablation plan, the headline number cannot be attributed to any component.

### 7. Risk and limitations

Be explicit about what the experiment **can't** test:

- Datasets / domains the experiment does not cover
- Failure modes the metrics don't measure
- Confounds (e.g., compute differences, data-leakage risks)
- Negative results we'd accept as the hypothesis being wrong

A design without limitations is a design that doesn't know its weaknesses.

## Compute / time budget

End with a small budget table:

| Item | Per-config cost | Total |
|---|---|---|
| Method × seeds × hyperparameter trials | 30 min × 3 × 30 = 45 hrs | one-time |
| Ablation re-runs | 30 min × 3 × 6 = 9 hrs | re-used datasets |
| Total | ≈ 54 hrs on 1 A100 | ~ 2.5 days |

This calibrates the user on the cost of running the experiment for real and supports the simulated-vs-measured choice in `references/03-results-protocol.md`.

## Anti-patterns

- **No hypothesis, just a question** — "how does X compare to Y?" is not a hypothesis. State the expected direction.
- **Cherry-picked baselines** — picking only the baselines you'll beat. Include baselines that might beat you.
- **Single seed** — never trust a single-seed number.
- **No ablation plan** — the headline number with no component attribution is not a finding.
- **Real-data brag with synthetic data** — if the dataset is synthetic, say so up front in §2.

## Quick checklist

- [ ] Hypothesis is falsifiable, with direction + rough magnitude
- [ ] Each dataset has its rationale, splits, pre-processing, limitations
- [ ] Baselines grouped by family; each has a primary citation and budget
- [ ] 3–6 metrics covering accuracy + cost + robustness, each with rationale
- [ ] Protocol explicit: seeds, hyperparameter budget, hardware, framework
- [ ] Ablation plan with expected effect direction per ablation
- [ ] Limitations and risks named
- [ ] Compute budget concrete (hours, not "TBD")
- [ ] Total length ≥ 700 words
