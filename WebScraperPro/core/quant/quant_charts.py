"""
quant_charts.py — Matplotlib chart generation for quantitative finance.

Every public function returns a ``matplotlib.figure.Figure`` that can be saved,
embedded, or displayed.  All charts share a consistent dark-theme style.
"""

from __future__ import annotations

import base64
import io
from typing import Dict, List, Optional, Sequence, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.figure import Figure

# ── Dark theme defaults ──────────────────────────────────────────────────────
_BG = "#1e1e2e"
_FG = "#cdd6f4"
_GRID = "#45475a"
_ACCENT = "#89b4fa"
_ACCENT2 = "#a6e3a1"
_ACCENT3 = "#f38ba8"
_ACCENT4 = "#fab387"
_ACCENT5 = "#cba6f7"
_ACCENT6 = "#94e2d5"

_PALETTE = [
    _ACCENT, _ACCENT2, _ACCENT3, _ACCENT4,
    _ACCENT5, _ACCENT6, "#f9e2af", "#eba0ac",
    "#b4befe", "#74c7ec", "#f2cdcd", "#89dceb",
]

# ── Font: try NotoSansSC, fall back gracefully ────────────────────────────────
def _init_style() -> None:
    """Apply dark theme and attempt to load NotoSansSC font."""
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": _BG,
        "axes.facecolor": _BG,
        "axes.edgecolor": _FG,
        "axes.labelcolor": _FG,
        "text.color": _FG,
        "xtick.color": _FG,
        "ytick.color": _FG,
        "grid.color": _GRID,
        "grid.alpha": 0.6,
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.facecolor": "#313244",
        "legend.edgecolor": _GRID,
        "legend.fontsize": 9,
        "figure.constrained_layout.use": True,
    })
    font_path = "/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf"
    try:
        from matplotlib.font_manager import FontProperties
        _fp = FontProperties(fname=font_path)
        plt.rcParams["font.family"] = _fp.get_name()
    except Exception:
        pass  # use default


_init_style()


def _new_fig(figsize: Tuple[float, float] = (10, 6), nrows=1, ncols=1) -> Figure:
    """Create a fresh dark-themed figure."""
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    if nrows == 1 and ncols == 1:
        ax = axes
        ax.grid(True)
    elif nrows == 1 or ncols == 1:
        for ax in axes:
            ax.grid(True)
    else:
        for row in axes:
            for ax in row:
                ax.grid(True)
    return fig


def _to_arr(data) -> np.ndarray:
    """Coerce list/tuple/series into a 1-D float64 numpy array."""
    if hasattr(data, "values"):
        data = data.values
    return np.asarray(data, dtype=np.float64).ravel()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Forecast
# ═══════════════════════════════════════════════════════════════════════════════
def plot_forecast(
    values,
    forecast,
    conf_lower: Optional[Sequence] = None,
    conf_upper: Optional[Sequence] = None,
    title: str = "Forecast",
) -> Figure:
    """Line chart with historical values, dashed forecast, and optional
    shaded confidence band.

    Parameters
    ----------
    values : array-like
        Historical observations.
    forecast : array-like
        Forecasted future values (appended after *values* on the x-axis).
    conf_lower, conf_upper : array-like, optional
        Lower / upper confidence bounds (same length as *forecast*).
    title : str
        Chart title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    vals = _to_arr(values)
    fc = _to_arr(forecast)
    n_hist = len(vals)
    n_fc = len(fc)
    x_hist = np.arange(n_hist)
    x_fc = np.arange(n_hist, n_hist + n_fc)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(True)

    ax.plot(x_hist, vals, color=_ACCENT, linewidth=1.6, label="Historical")
    ax.plot(x_fc, fc, color=_ACCENT3, linewidth=1.6, linestyle="--", label="Forecast")

    if conf_lower is not None and conf_upper is not None:
        cl = _to_arr(conf_lower)
        cu = _to_arr(conf_upper)
        if len(cl) == n_fc and len(cu) == n_fc:
            ax.fill_between(x_fc, cl, cu, color=_ACCENT3, alpha=0.18, label="Confidence band")

    ax.axvline(n_hist - 1, color=_FG, linewidth=0.8, linestyle=":", alpha=0.5)
    ax.set_title(title)
    ax.set_xlabel("Period")
    ax.set_ylabel("Value")
    ax.legend(loc="best")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Volatility (two-panel)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_volatility(
    values,
    vol_forecast,
    title: str = "Volatility",
) -> Figure:
    """Two-panel chart: prices on top, volatility forecast on bottom.

    Parameters
    ----------
    values : array-like
        Price series.
    vol_forecast : array-like
        Volatility series (can be same length or forecast-only).
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    vals = _to_arr(values)
    vol = _to_arr(vol_forecast)
    n = len(vals)
    nv = len(vol)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax1.grid(True)
    ax2.grid(True)

    x_vals = np.arange(n)
    ax1.plot(x_vals, vals, color=_ACCENT, linewidth=1.4)
    ax1.set_title(title)
    ax1.set_ylabel("Price")

    if nv == n:
        x_vol = x_vals
    else:
        x_vol = np.arange(n, n + nv)
    ax2.plot(x_vol, vol, color=_ACCENT4, linewidth=1.4)
    ax2.fill_between(x_vol, 0, vol, color=_ACCENT4, alpha=0.15)
    ax2.set_xlabel("Period")
    ax2.set_ylabel("Volatility")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Efficient Frontier
# ═══════════════════════════════════════════════════════════════════════════════
def plot_efficient_frontier(
    frontier_points,
    tangency_point: Optional[Sequence] = None,
    title: str = "Efficient Frontier",
) -> Figure:
    """Scatter plot of mean-variance frontier with optional tangency (CML) point.

    Parameters
    ----------
    frontier_points : array-like, shape (N, 2)
        Each row is (volatility, return).
    tangency_point : array-like of length 2, optional
        (volatility, return) of the tangency portfolio.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    pts = np.asarray(frontier_points, dtype=np.float64)
    if pts.ndim == 1:
        pts = pts.reshape(-1, 2)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.grid(True)

    ax.scatter(pts[:, 0], pts[:, 1], c=_ACCENT, s=14, alpha=0.7, label="Frontier")

    if tangency_point is not None:
        tp = np.asarray(tangency_point, dtype=np.float64).ravel()
        if len(tp) >= 2:
            ax.scatter([tp[0]], [tp[1]], c=_ACCENT3, s=90, marker="*",
                       zorder=5, label="Tangency")
            # Draw CML line from (0, rf_approx) to tangency and beyond
            rf_approx = 0.0
            if tp[0] > 0:
                slope = (tp[1] - rf_approx) / tp[0]
                x_max = pts[:, 0].max() * 1.15
                x_cml = np.linspace(0, x_max, 200)
                y_cml = rf_approx + slope * x_cml
                ax.plot(x_cml, y_cml, color=_ACCENT3, linewidth=1.2,
                        linestyle="--", alpha=0.7, label="CML")

    ax.set_title(title)
    ax.set_xlabel("Volatility (σ)")
    ax.set_ylabel("Expected Return")
    ax.legend(loc="best")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Pie Weights
# ═══════════════════════════════════════════════════════════════════════════════
def plot_pie_weights(
    weights,
    names,
    title: str = "Weights",
) -> Figure:
    """Pie chart of portfolio / allocation weights.

    Parameters
    ----------
    weights : array-like
        Positive weight values (will be normalised if they don't sum to 1).
    names : list[str]
        Labels for each slice.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    w = np.asarray(weights, dtype=np.float64).ravel()
    if w.sum() == 0:
        w = np.ones_like(w)
    w = w / w.sum()
    n = len(w)
    colors = [_PALETTE[i % len(_PALETTE)] for i in range(n)]

    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        w, labels=names, autopct="%1.1f%%",
        colors=colors, startangle=140,
        textprops={"color": _FG},
        pctdistance=0.75,
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title(title, pad=18)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 5. VaR Histogram
# ═══════════════════════════════════════════════════════════════════════════════
def plot_var_histogram(
    returns,
    var_level: float,
    title: str = "VaR",
) -> Figure:
    """Histogram of returns with a vertical line at the VaR level.

    Parameters
    ----------
    returns : array-like
        Portfolio or asset returns.
    var_level : float
        Value-at-Risk threshold (e.g. -0.02 for 2 % daily loss).
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    r = _to_arr(returns)
    if len(r) == 0:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax.grid(True)
        ax.set_title(title + " (no data)")
        return fig

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.grid(True)

    n_bins = max(15, int(np.sqrt(len(r))))
    ax.hist(r, bins=n_bins, color=_ACCENT, edgecolor=_BG, alpha=0.8)
    ax.axvline(var_level, color=_ACCENT3, linewidth=2, linestyle="--",
               label=f"VaR = {var_level:.4f}")
    ax.set_title(title)
    ax.set_xlabel("Return")
    ax.set_ylabel("Frequency")
    ax.legend(loc="best")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Drawdown (area chart)
# ═══════════════════════════════════════════════════════════════════════════════
def plot_drawdown(
    returns,
    title: str = "Drawdown",
) -> Figure:
    """Area chart of cumulative drawdown from a peak.

    Parameters
    ----------
    returns : array-like
        Simple returns (prices will be cumulated internally).
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    r = _to_arr(returns)
    if len(r) == 0:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.grid(True)
        ax.set_title(title + " (no data)")
        return fig

    # Cumulative price series
    cum = np.cumprod(1 + r)
    running_max = np.maximum.accumulate(cum)
    dd = (cum - running_max) / running_max

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.grid(True)

    x = np.arange(len(dd))
    ax.fill_between(x, dd, 0, color=_ACCENT3, alpha=0.35)
    ax.plot(x, dd, color=_ACCENT3, linewidth=1.2)
    ax.set_title(title)
    ax.set_xlabel("Period")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Correlation Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
def plot_correlation_heatmap(
    corr_matrix,
    names,
    title: str = "Correlation",
) -> Figure:
    """Heatmap of a correlation matrix with annotated values and colorbar.

    Parameters
    ----------
    corr_matrix : array-like, shape (N, N)
        Square correlation matrix.
    names : list[str]
        Asset / variable names.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    cm = np.asarray(corr_matrix, dtype=np.float64)
    n = cm.shape[0]
    if names is None:
        names = [str(i) for i in range(n)]

    fig, ax = plt.subplots(figsize=(max(7, n * 0.9), max(6, n * 0.85)))

    im = ax.imshow(cm, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(names, fontsize=9)

    # Annotate cells
    for i in range(n):
        for j in range(n):
            val = cm[i, j]
            color = "white" if abs(val) > 0.55 else _FG
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color=color)

    ax.set_title(title)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 8. DSGE Impulse Response
# ═══════════════════════════════════════════════════════════════════════════════
def plot_dsge_irf(
    irf_data,
    title: str = "Impulse Response",
) -> Figure:
    """Multi-line impulse-response function chart.

    Parameters
    ----------
    irf_data : dict[str, array-like]
        Mapping from variable name to its IRF time series.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    if not irf_data:
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.grid(True)
        ax.set_title(title + " (no data)")
        return fig

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(True)

    for idx, (var_name, series) in enumerate(irf_data.items()):
        s = _to_arr(series)
        color = _PALETTE[idx % len(_PALETTE)]
        ax.plot(s, color=color, linewidth=1.4, label=var_name)

    ax.axhline(0, color=_FG, linewidth=0.7, linestyle=":", alpha=0.5)
    ax.set_title(title)
    ax.set_xlabel("Horizon")
    ax.set_ylabel("Response")
    ax.legend(loc="best")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Phillips Curve
# ═══════════════════════════════════════════════════════════════════════════════
def plot_phillips_curve(
    unemployment,
    inflation,
    fitted: Optional[Sequence] = None,
    title: str = "Phillips Curve",
) -> Figure:
    """Scatter of unemployment vs. inflation with optional fitted regression.

    Parameters
    ----------
    unemployment : array-like
        Unemployment rate series.
    inflation : array-like
        Inflation rate series.
    fitted : array-like, optional
        Fitted inflation values (same length as *unemployment*) for the
        regression line.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    u = _to_arr(unemployment)
    pi = _to_arr(inflation)
    if len(u) == 0:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.grid(True)
        ax.set_title(title + " (no data)")
        return fig

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.grid(True)

    ax.scatter(u, pi, c=_ACCENT, s=28, alpha=0.7, edgecolors="none", label="Data")

    if fitted is not None:
        f = _to_arr(fitted)
        if len(f) == len(u):
            order = np.argsort(u)
            ax.plot(u[order], f[order], color=_ACCENT3, linewidth=2,
                    label="Fitted")

    ax.set_title(title)
    ax.set_xlabel("Unemployment Rate")
    ax.set_ylabel("Inflation Rate")
    ax.legend(loc="best")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Comparison Bars
# ═══════════════════════════════════════════════════════════════════════════════
def plot_comparison_bars(
    categories,
    values,
    title: str = "Comparison",
) -> Figure:
    """Horizontal bar chart.

    Parameters
    ----------
    categories : list[str]
        Bar labels on the y-axis.
    values : array-like
        Corresponding numeric values.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    cats = list(categories)
    vals = _to_arr(values)
    n = len(cats)
    if n == 0:
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.grid(True)
        ax.set_title(title + " (no data)")
        return fig

    colors = [_PALETTE[i % len(_PALETTE)] for i in range(n)]

    fig, ax = plt.subplots(figsize=(max(8, n * 0.55), max(5, n * 0.45)))
    ax.grid(True, axis="x")

    y_pos = np.arange(n)
    ax.barh(y_pos, vals, color=colors, edgecolor=_BG, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(cats, fontsize=10)
    ax.set_title(title)
    ax.set_xlabel("Value")
    ax.invert_yaxis()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Multi-Series Line Chart
# ═══════════════════════════════════════════════════════════════════════════════
def plot_multi_series(
    series_dict,
    title: str = "Multi-Series",
) -> Figure:
    """Plot multiple named series on the same axes.

    Parameters
    ----------
    series_dict : dict[str, array-like]
        Mapping from series name to its values.
    title : str

    Returns
    -------
    matplotlib.figure.Figure
    """
    if not series_dict:
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.grid(True)
        ax.set_title(title + " (no data)")
        return fig

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(True)

    for idx, (name, series) in enumerate(series_dict.items()):
        s = _to_arr(series)
        color = _PALETTE[idx % len(_PALETTE)]
        ax.plot(s, color=color, linewidth=1.3, label=name)

    ax.set_title(title)
    ax.set_xlabel("Period")
    ax.set_ylabel("Value")
    ax.legend(loc="best")
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Tkinter Embedding Helper
# ═══════════════════════════════════════════════════════════════════════════════
def create_chart_widget(parent_frame, figure) -> "FigureCanvasTkAgg":
    """Embed a Matplotlib figure into a *tkinter* parent frame.

    Parameters
    ----------
    parent_frame : tkinter.Widget
        The parent Tk frame or widget.
    figure : matplotlib.figure.Figure
        The figure to embed.

    Returns
    -------
    FigureCanvasTkAgg
        The canvas widget (call ``.get_tk_widget().pack()`` to display).
    """
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    canvas = FigureCanvasTkAgg(figure, master=parent_frame)
    canvas.draw()
    return canvas


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Base64 Encoding Helper
# ═══════════════════════════════════════════════════════════════════════════════
def get_figure_as_base64(figure) -> str:
    """Serialize a Matplotlib figure to a PNG base-64 string.

    Parameters
    ----------
    figure : matplotlib.figure.Figure

    Returns
    -------
    str
        Base-64 encoded PNG image.
    """
    buf = io.BytesIO()
    figure.savefig(buf, format="png", facecolor=figure.get_facecolor(),
                   edgecolor="none", bbox_inches="tight")
    plt.close(figure)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
