# Figure Examples

Reference matplotlib / seaborn scripts producing publication-grade figures
for AI4S research papers. Reproduce with:

```bash
pip install matplotlib seaborn
cd <where-you-want-the-pdf>
python make_fig_02_horizon_sweep.py
python make_fig_03_heatmap.py
python make_fig_04_ablation.py
```

These are illustrative templates — copy and adapt for your data. They were
extracted from a successful enrichment run of the `paper-writer` skill on
the topic *Transformer-based time-series forecasting* (May 2026); the data
embedded inline are simulated and meant only to illustrate the formatting.

Start by filling `FIGURE_CONTRACT_TEMPLATE.md` for the figure you are about to make.
Then reuse `style_kit.py` so exports, palette, panel labels, and simulated
watermarks stay consistent across the experiment package.

## Style summary
- Shared `style_kit.py` with editable SVG text and PDF font embedding
- Explicit color palette (no default cycle)
- Removed top/right spines
- `axes.grid` on at low alpha
- Figure sizes targeted at column-width (3.4-5.0 inches wide)
- "simulated" watermark in italic gray for runs from the simulator path
- Save PDF + SVG + TIFF together when the environment allows it

See the `paper-writer` skill's `references/02-figures-publication-grade.md`
for the full taste guide.
