"""Generate fig_03_method_x_dataset_heatmap.pdf — MSE heatmap across methods × datasets."""
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from style_kit import add_panel_label, add_simulated_watermark, apply_publication_style, save_publication_bundle

apply_publication_style()

datasets = ["ETTh1", "ETTh2", "ETTm1", "ETTm2", "ECL", "Traffic", "Weather"]
methods = ["DLinear", "Informer", "Autoformer", "FEDformer",
           "PatchTST", "iTrans.", "TimeMixer", "Ours"]

mse = np.array([
    [0.394, 0.495, 0.439, 0.411, 0.371, 0.364, 0.358, 0.355],
    [0.310, 0.452, 0.388, 0.358, 0.301, 0.294, 0.290, 0.287],
    [0.382, 0.512, 0.421, 0.401, 0.366, 0.359, 0.357, 0.354],
    [0.279, 0.401, 0.336, 0.318, 0.262, 0.258, 0.254, 0.252],
    [0.166, 0.219, 0.187, 0.179, 0.158, 0.151, 0.150, 0.149],
    [0.434, 0.608, 0.545, 0.508, 0.412, 0.406, 0.405, 0.402],
    [0.241, 0.318, 0.281, 0.265, 0.227, 0.224, 0.223, 0.220],
])

fig, ax = plt.subplots(figsize=(6.4, 3.4))
sns.heatmap(
    mse, annot=True, fmt=".3f",
    xticklabels=methods, yticklabels=datasets,
    cmap="RdYlGn_r",
    cbar_kws={"label": "MSE", "shrink": 0.7, "pad": 0.02},
    annot_kws={"size": 7.5},
    linewidths=0.4, linecolor="white",
    ax=ax,
)
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
add_panel_label(ax, "(b)")
add_simulated_watermark(ax, y=-0.16)

plt.tight_layout(pad=0.4)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_03_method_x_dataset_heatmap")
save_publication_bundle(fig, out)
plt.close(fig)
print(f"Wrote {out}.pdf/.svg/.tiff")
