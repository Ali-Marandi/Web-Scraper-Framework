"""Shared publication-style helpers for experiment-suite figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral_light": "#CFCECE",
    "neutral_mid": "#767676",
    "neutral_dark": "#4D4D4D",
    "neutral_black": "#272727",
    "teal": "#42949E",
    "violet": "#9A4D8E",
}

DEFAULT_COLORS = [
    PALETTE["blue_main"],
    PALETTE["green_3"],
    PALETTE["red_strong"],
    PALETTE["teal"],
    PALETTE["violet"],
    PALETTE["neutral_mid"],
]

PALETTE_NMI_PASTEL = [
    "#484878",
    "#7884B4",
    "#B4C0E4",
    "#E4E4F0",
    "#E4CCD8",
    "#F0C0CC",
]


def apply_publication_style(font_size: int = 9, axes_linewidth: float = 0.6) -> None:
    """Apply a shared journal-style matplotlib configuration."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
        "font.size": font_size,
        "axes.labelsize": font_size,
        "axes.titlesize": font_size + 1,
        "xtick.labelsize": max(font_size - 1, 6),
        "ytick.labelsize": max(font_size - 1, 6),
        "legend.fontsize": max(font_size - 1, 6),
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": axes_linewidth,
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


def add_panel_label(ax, label: str, x: float = -0.12, y: float = 1.03) -> None:
    ax.text(
        x, y, label,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def add_simulated_watermark(ax, x: float = 0.99, y: float = 0.02) -> None:
    ax.text(
        x, y, "simulated",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color="gray",
        alpha=0.7,
        style="italic",
    )


def save_publication_bundle(fig, out_base: str, dpi: int = 600) -> None:
    """Save PDF/SVG/TIFF together when possible."""
    out_path = Path(out_base)
    fig.savefig(out_path.with_suffix(".pdf"))
    fig.savefig(out_path.with_suffix(".svg"))
    fig.savefig(out_path.with_suffix(".tiff"), dpi=dpi)
