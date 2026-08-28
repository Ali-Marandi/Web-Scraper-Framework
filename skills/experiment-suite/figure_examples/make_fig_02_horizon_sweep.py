"""Generate fig_02_horizon_sweep.pdf — MSE vs forecast horizon (publication style)."""
import os
import matplotlib.pyplot as plt
import numpy as np
from style_kit import (
    DEFAULT_COLORS,
    add_panel_label,
    add_simulated_watermark,
    apply_publication_style,
    save_publication_bundle,
)

apply_publication_style()
MARKERS = ["o", "s", "^", "D"]

horizons = np.array([96, 192, 336, 720])
methods = {
    "DLinear":      np.array([0.345, 0.380, 0.420, 0.498]),
    "PatchTST":     np.array([0.330, 0.358, 0.395, 0.469]),
    "iTransformer": np.array([0.328, 0.354, 0.392, 0.466]),
    "Ours":         np.array([0.319, 0.346, 0.385, 0.460]),
}

fig, ax = plt.subplots(figsize=(5.0, 3.2))
for (name, vals), color, marker in zip(methods.items(), DEFAULT_COLORS, MARKERS):
    ax.plot(horizons, vals, marker=marker, color=color, label=name)

ax.set_xlabel(r"Forecast horizon $H$")
ax.set_ylabel("MSE on ETTm1 (lower is better)")
ax.set_xscale("log", base=2)
ax.set_xticks(horizons)
ax.set_xticklabels([str(h) for h in horizons])
ax.legend(frameon=False, loc="upper left")
add_panel_label(ax, "(a)")
add_simulated_watermark(ax)

plt.tight_layout(pad=0.4)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_02_horizon_sweep")
save_publication_bundle(fig, out)
plt.close(fig)
print(f"Wrote {out}.pdf/.svg/.tiff")
