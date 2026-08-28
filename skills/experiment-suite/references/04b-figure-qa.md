# Figure QA For Experiment Packages

Use this before delivery or before passing figures to `paper-writer`.

## Export bundle

The ideal bundle per figure is:

- `<basename>.pdf` for paper reuse
- `<basename>.svg` for editable vector text
- `<basename>.tiff` for journal upload when needed
- `make_<basename>.py` as the source of truth

If the environment cannot produce all three, keep PDF mandatory and note the limitation.

## Editable-text rules

For matplotlib-based figures:

```python
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42
```

This keeps SVG text editable and PDF text embedded.

## Minimum QA checklist

- Figure title / axes / legend readable at final size
- No legend overlapping the data
- No default matplotlib color cycle
- Panel labels consistent across figures
- Simulated watermark present iff the run is simulated
- Figure caption can stand alone in the report
- Statistics in the caption or surrounding prose define mean/std/CI and seed count

## For image-based experiment figures

If the figure contains microscopy, pathology, blots, or spatial overlays, also record:

- raw image source
- crop
- brightness/contrast handling
- scale-bar presence
- whether pseudo-coloring was applied

## Anti-patterns

- 3-D bars
- pie charts for quantitative comparison
- saturated rainbow heatmaps without justification
- repeated legends in every panel
- simulated figures without visible disclosure
