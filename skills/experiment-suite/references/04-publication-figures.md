# Publication-Grade Figures

## Why this exists

The simulator emits one default chart (`fig_01_comparison_<metric>.pdf`) with default matplotlib styling — useful for a status check, far too crude for a real experiment package. This reference defines what to bring it up to.

**Hard targets:**
- ≥ 3 figures total (more if the experiment supports them)
- All vector PDF, fonts embedded, publication-grade rcParams
- Each figure has a question it answers; that question becomes the caption

Before plotting, open `references/04a-figure-contract.md` and define the figure contract. The chart serves the claim, not the other way around.

## File layout

All figures live under `output/experiment-suite/<slug>/figures/` with a `make_fig_NN_<slug>.py` script alongside the rendered `.pdf`. The script is the source of truth — re-running the script reproduces the figure. Update `manifest.json` when adding figures.

Naming: `fig_<NN>_<slug>.pdf` and `make_fig_<NN>_<slug>.py`.

## Publication rcParams

Apply at the top of every figure script:

```python
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "axes.linewidth": 0.6,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.4,
    "lines.linewidth": 1.4,
    "lines.markersize": 4.5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})
```

`pdf.fonttype = 42` embeds fonts as TrueType — required for journal submission.

If you have many related methods on one page, prefer a restrained family palette instead of maximal hue separation.

## Color palette

```python
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
```

Never use the default matplotlib cycle (perceptually uneven on screen; clashes in print).

Alternative unified palette for method families:

```python
PALETTE_NMI_PASTEL = [
    "#484878", "#7884B4", "#B4C0E4", "#E4E4F0", "#E4CCD8", "#F0C0CC"
]
```

## Required figure families

### Family 1 — Method comparison (bar or line)

If one panel is the main paper claim, make it the hero panel. Supporting panels should not get equal visual weight by default.

Bar chart for a single metric across methods:

```python
methods = ["DLinear", "PatchTST", "iTransformer", "Ours"]
mse =     [0.382,    0.366,      0.359,         0.354]
err =     [0.012,    0.009,      0.008,         0.007]

fig, ax = plt.subplots(figsize=(3.6, 2.6))
x = np.arange(len(methods))
ax.bar(x, mse, yerr=err, capsize=3, color=COLORS[:len(methods)],
       edgecolor="black", linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(methods, rotation=15, ha="right")
ax.set_ylabel("MSE on ETTm1 (lower is better)")
ax.set_ylim(0.34, 0.40)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

Or a horizon-sweep line plot if the experiment has a horizon axis.

### Family 2 — Ablation breakdown

Either a panel-of-bars per ablation row, or a small-multiples plot per dataset showing full-vs-ablated:

```python
fig, axes = plt.subplots(1, len(DATASETS), figsize=(7.0, 2.4), sharey=True)
for ax, dataset in zip(axes, DATASETS):
    ax.bar([0, 1], [full[dataset], no_patch[dataset]],
           color=[COLORS[0], COLORS[3]], width=0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Full", r"$-$patching"], fontsize=8)
    ax.set_title(dataset, fontsize=9)
    if dataset == DATASETS[0]:
        ax.set_ylabel("MSE")
```

### Family 3 — Optional: training curves / heatmap / scaling

Use only when the data supports it:

- **Training curves** (line plot, train+val per method) — useful when the experiment varies optimisation strategy.
- **Heatmap** (method × dataset MSE) — useful when there are 6+ methods and 4+ datasets.
- **Scaling plot** (metric vs model size / data size) — useful for a foundation-model story.

If the data doesn't support a meaningful version of these, skip — empty heatmaps with 4 cells are not figures.

## Panel labels

Add lowercase panel labels for multi-panel figures:

```python
ax.text(-0.12, 1.03, "(a)", transform=ax.transAxes,
        fontsize=10, fontweight="bold", ha="left", va="bottom")
```

Keep the position consistent across panels in the same figure family.

## Captions

Every caption stands alone (a reader who only sees the figure should understand it). Aim for 1–3 sentences naming axes, what the panels show, and what the takeaway is.

For simulated results, the caption ends with `Numbers are simulated.` For measured results, the caption may name the seed count and hardware briefly.

Prefer direct labels over a detached legend when one or two curves dominate the interpretation and the labels can be placed without ambiguity.

## Watermarks for simulated mode

If `results.json` provenance is `"simulated"`, add a discreet watermark to each figure:

```python
ax.text(0.99, 0.02, "simulated",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7, color="gray", alpha=0.7, style="italic")
```

This is a redundancy with the caption, on purpose — readers who skim only figures (more common than you'd think) need a visible flag.

## Export policy

Primary export remains vector PDF because `paper-writer` reuses it directly. When possible, also export:

- `.svg` for editable text
- `.tiff` at 600 dpi for journal upload

Do not store absolute paths in `manifest.json`; only basenames.

## Anti-patterns

- **3-D bars, drop shadows, gradient fills** — none belong in a research figure.
- **Pie / donut charts** — almost never the right choice; never for experimental data.
- **Default matplotlib colors** — perceptually uneven; use the palette above.
- **Legend overlapping data** — move it or shrink data range.
- **Captions that say only "Comparison results"** — say what's being compared and what we learn.
- **Watermark missing** in simulated mode — caption without watermark is not enough.
- **Raster (.png) instead of vector (.pdf)** — pixelates in print.

Before final delivery, run the checklist in `references/04b-figure-qa.md`.

## Manifest update

After adding a figure, append an entry to `figures/manifest.json` so downstream `paper-writer` consumers see it:

```json
[
  {
    "id": "fig_02_method_comparison",
    "path_pdf": "fig_02_method_comparison.pdf",
    "path_png": "fig_02_method_comparison.png",
    "caption": "MSE comparison across methods on ETTm1 (three-seed mean ± std).",
    "section": "results"
  }
]
```

## Quick checklist

- [ ] ≥ 3 figures (4–6 ideal)
- [ ] All publication rcParams applied (font, size, dpi, embedded fonts)
- [ ] All figures vector PDF + sibling PNG for preview
- [ ] Each figure has a `make_fig_NN_*.py` script alongside
- [ ] Each figure referenced by the report and / or paper
- [ ] Each caption stands alone
- [ ] Simulated figures carry watermark + caption disclaimer
- [ ] `manifest.json` lists every figure
