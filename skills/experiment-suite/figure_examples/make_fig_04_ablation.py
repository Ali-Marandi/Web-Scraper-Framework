"""Generate fig_04_ablation_panels.pdf — 2x2 ablation panel figure."""
import os
import matplotlib.pyplot as plt
import numpy as np
from style_kit import PALETTE, add_simulated_watermark, apply_publication_style, save_publication_bundle

apply_publication_style()

PRIMARY = PALETTE["blue_main"]
ABLATION = PALETTE["red_strong"]
DATASETS = ["ETTm1", "Electricity", "Traffic", "Weather"]

horizons = np.array([96, 192, 336, 720])
full = {
    "ETTm1":       np.array([0.319, 0.346, 0.385, 0.460]),
    "Electricity": np.array([0.131, 0.142, 0.149, 0.171]),
    "Traffic":     np.array([0.352, 0.378, 0.402, 0.451]),
    "Weather":     np.array([0.179, 0.198, 0.220, 0.272]),
}
no_patch = {
    "ETTm1":       np.array([0.354, 0.382, 0.422, 0.499]),
    "Electricity": np.array([0.143, 0.155, 0.164, 0.186]),
    "Traffic":     np.array([0.378, 0.408, 0.434, 0.486]),
    "Weather":     np.array([0.198, 0.221, 0.247, 0.301]),
}

fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.4), sharex=True)
for ax, name in zip(axes.flat, DATASETS):
    ax.plot(horizons, full[name], marker="o", color=PRIMARY, label="Full")
    ax.plot(horizons, no_patch[name], marker="s", linestyle="--",
            color=ABLATION, label=r"$-$ patching")
    ax.set_title(name)
    ax.set_xscale("log", base=2)
    ax.set_xticks(horizons)
    ax.set_xticklabels([str(h) for h in horizons])
    ax.grid(True, alpha=0.25, linewidth=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

for ax in axes[:, 0]:
    ax.set_ylabel("MSE")
for ax in axes[-1, :]:
    ax.set_xlabel(r"Horizon $H$")

handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.02),
           ncol=2, frameon=False)

for ax, label in zip(axes.flat, "abcd"):
    ax.text(-0.15, 1.05, f"({label})", transform=ax.transAxes,
            fontweight="bold", fontsize=10)

add_simulated_watermark(fig.axes[-1], y=-0.22)

plt.tight_layout(rect=(0.0, 0.01, 1.0, 0.95))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_04_ablation_panels")
save_publication_bundle(fig, out)
plt.close(fig)
print(f"Wrote {out}.pdf/.svg/.tiff")
