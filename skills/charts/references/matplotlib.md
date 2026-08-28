# matplotlib Template Library

> **⚠️ Before writing any code, read [`_rules.md`](references/_rules.md) — three non-negotiable rules on overlap, hierarchy, and color.**


## Environment Initialization (Must Execute Before Each Plot)

```python
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ═══ Chinese Font Setup ═══
# SimHei is the default; other fonts available:
#   SimSun.ttf (Songti, formal docs), SimKai.ttf (Kaiti, artistic),
#   SarasaMonoSC-*.ttf (monospace CJK, code scenes)
# Run `fc-list :lang=zh` for system fonts (PingFang SC, Heiti TC, etc.)
# Font path: adjust for your system. Common locations:
#   macOS: '/System/Library/Fonts/Supplemental/SimHei.ttf'
#   Linux: '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
#   Custom: './fonts/SimHei.ttf'
import os
SIMHEI_PATH = os.environ.get('SIMHEI_FONT', '/System/Library/Fonts/Supplemental/SimHei.ttf')
matplotlib.font_manager.fontManager.addfont(SIMHEI_PATH)

# ═══ Global Style ═══
plt.rcParams.update({
    # Font
    'font.sans-serif': ['SimHei'],
    'axes.unicode_minus': False,
    # Background
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    # Border: only keep left and bottom
    'axes.edgecolor': '#E5E7EB',
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    # Grid: off by default
    'axes.grid': False,
    # Ticks: hide tick marks
    'xtick.major.size': 0,
    'ytick.major.size': 0,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    # Title
    'axes.labelsize': 10,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.titlepad': 16,
    # Legend: no frame
    'legend.frameon': False,
    'legend.fontsize': 9,
    # Export
    'figure.dpi': 200,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
    'savefig.facecolor': '#FFFFFF',
    'savefig.pad_inches': 0.3,
})
```

## Color Constants

```python
# ─── Cool Colors (Business/Tech) ───
C_BLUE   = '#3B82F6'
C_CYAN   = '#06B6D4'
C_PURPLE = '#8B5CF6'
C_AMBER  = '#F59E0B'
C_RED    = '#EF4444'
C_GREEN  = '#10B981'
COOL = [C_BLUE, C_CYAN, C_PURPLE, C_AMBER, C_RED, C_GREEN]

# ─── Warm Colors (Warmth/Creative) ───
WARM = ['#F59E0B', '#EF4444', '#8B5CF6', '#3B82F6', '#10B981', '#EC4899']

# ─── Academic Grayscale ───
ACADEMIC = ['#111827', '#6B7280', '#9CA3AF', '#D1D5DB', '#E5E7EB', '#F3F4F6']

# ─── Colorblind-Safe (Paper Preferred) ───
CB_SAFE = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']

# ─── Grayscale ───
G900, G700, G500, G400, G300, G200, G100, G50 = \
    '#111827', '#374151', '#6B7280', '#9CA3AF', '#D1D5DB', '#E5E7EB', '#F3F4F6', '#F9FAFB'

# ─── Gain/Loss ───
POS = '#22C55E'
NEG = '#EF4444'
```

## Helper Functions

```python
def clean_axis(ax, grid=True):
    """Clean axis: remove top and right borders, add faint grid"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if grid:
        ax.yaxis.grid(True, alpha=0.08, color=G300)
        ax.set_axisbelow(True)

def add_value_labels(ax, bars, values, highlight_idx=None, fmt='{:,.0f}',
                     offset_ratio=0.02):
    """Add value labels on top of bars, highlight bar in bold.
    ⚠️ Automatically extends Y-axis upper limit to ensure labels don't overflow chart area."""
    max_val = max(values)
    for i, (bar, val) in enumerate(zip(bars, values)):
        is_hl = (i == highlight_idx) if highlight_idx is not None else False
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + max_val * offset_ratio,
                fmt.format(val), ha='center', va='bottom',
                fontsize=10 if is_hl else 9,
                color=G900 if is_hl else G400,
                fontweight='bold' if is_hl else 'normal')

    # ⚠️ Critical: extend Y-axis upper limit to leave enough space for labels (at least 15%)
    ax.set_ylim(0, max_val * 1.18)

def save(fig, path, dpi=200):
    """Unified save — prefer constrained_layout, fallback to tight_layout"""
    if not fig.get_constrained_layout():
        try:
            fig.tight_layout()
        except Exception:
            pass
    fig.savefig(path, dpi=dpi, facecolor='white', bbox_inches='tight')
    plt.close(fig)
    import os
    size_kb = os.path.getsize(path) / 1024
    print(f'✅ {path} ({size_kb:.0f}KB)')
```

### Label Text Avoidance (adjustText)

When charts have multiple label annotations (e.g., scatter plot labels, box plot annotations), **must use adjustText library** to prevent text overlap:

```python
# pip install adjustText
from adjustText import adjust_text

# Call after adding all annotations
texts = []
for i, (x, y, label) in enumerate(zip(x_data, y_data, labels)):
    texts.append(ax.text(x, y, label, fontsize=9, color='#374151'))

# Auto-avoidance — pass all text objects, adjustText will move them to avoid overlap
adjust_text(texts, ax=ax,
            arrowprops=dict(arrowstyle='->', color='#9CA3AF', lw=0.8),
            force_text=(0.5, 0.8),   # Force to push text away
            force_points=(0.3, 0.5), # Repulsion from data points
            expand=(1.2, 1.4))       # Expansion factor for text bbox
```

---

## Template 1: Insight Bar Chart

**Scenario**: Emphasize outstanding performance of one data item. Gray out others, highlight the focus.

```python
def insight_bar(labels, values, highlight_idx, title, 
                highlight_color=C_BLUE, save_path='insight_bar.png'):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = [G200] * len(labels)
    colors[highlight_idx] = highlight_color
    
    bars = ax.bar(labels, values, color=colors, width=0.6,
                  zorder=3, edgecolor='white', linewidth=0.5)
    add_value_labels(ax, bars, values, highlight_idx)
    
    ax.set_title(title, loc='left')
    # ⚠️ add_value_labels already sets ylim automatically, no need to repeat here
    clean_axis(ax)
    save(fig, save_path)
```

---

## Template 2: Trend Comparison Line Chart

**Scenario**: This year vs last year, actual vs target. Main line in colored solid, comparison line in gray dashed.

```python
def trend_compare(x, y_main, y_ref, label_main, label_ref, title,
                  color=C_BLUE, save_path='trend_compare.png'):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Comparison line (gray dashed, at bottom layer)
    ax.plot(x, y_ref, color=G300, linewidth=1.5, linestyle='--', zorder=2)
    ax.text(len(x)-0.5, y_ref[-1], label_ref, color=G400, fontsize=9, va='center')

    # Main line (colored solid + white-center dots)
    ax.plot(x, y_main, color=color, linewidth=2.5, marker='o', markersize=5,
            markerfacecolor='white', markeredgewidth=2, markeredgecolor=color, zorder=3)
    ax.text(len(x)-0.5, y_main[-1], f'{label_main}  {y_main[-1]:,.0f}',
            color=color, fontsize=10, fontweight='bold', va='center')

    # Difference area
    ax.fill_between(range(len(x)), y_ref, y_main, alpha=0.06, color=color)

    ax.set_title(title, loc='left')
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x)
    clean_axis(ax)
    save(fig, save_path)
```

---

## Template 3: Grouped Bar Chart

**Scenario**: Comparison of multiple categories across multiple dimensions.

```python
def grouped_bar(labels, datasets, series_names, title,
                colors=None, save_path='grouped_bar.png'):
    if colors is None:
        colors = COOL[:len(datasets)]

    fig, ax = plt.subplots(figsize=(12, 6))
    n = len(datasets)
    width = 0.7 / n
    x = np.arange(len(labels))

    for i, (data, name, color) in enumerate(zip(datasets, series_names, colors)):
        offset = (i - n/2 + 0.5) * width
        ax.bar(x + offset, data, width=width*0.85, color=color,
               label=name, zorder=3, edgecolor='white', linewidth=0.3)

    ax.set_title(title, loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(max(d) for d in datasets) * 1.20)  # Leave 20% space for labels
    ax.legend(loc='upper right', ncol=n)
    clean_axis(ax)
    save(fig, save_path)
```

---

## Template 4: Horizontal Ranking Chart

**Scenario**: Rankings / Top N. Progressive highlight for top items.

```python
def ranking_bar(labels, values, title, top_n=3,
                color=C_BLUE, save_path='ranking.png'):
    from matplotlib.colors import to_rgba
    
    sorted_pairs = sorted(zip(labels, values), key=lambda x: x[1])
    labels_s, values_s = zip(*sorted_pairs)
    
    fig, ax = plt.subplots(figsize=(10, max(6, len(labels)*0.45)))
    
    bar_colors = [G200] * len(labels_s)
    for i in range(len(labels_s) - top_n, len(labels_s)):
        progress = (i - (len(labels_s) - top_n)) / max(top_n - 1, 1)
        bar_colors[i] = to_rgba(color, 0.35 + 0.65 * progress)
    
    bars = ax.barh(range(len(labels_s)), values_s, color=bar_colors,
                   height=0.6, zorder=3, edgecolor='white', linewidth=0.3)
    
    for i, (bar, val) in enumerate(zip(bars, values_s)):
        is_top = i >= len(labels_s) - top_n
        ax.text(bar.get_width() + max(values_s)*0.01,
                bar.get_y() + bar.get_height()/2,
                f'{val:,.0f}', va='center', fontsize=9,
                color=G900 if is_top else G400)
    
    ax.set_yticks(range(len(labels_s)))
    ax.set_yticklabels(labels_s)
    ax.set_title(title, loc='left')
    ax.spines['bottom'].set_visible(False)
    ax.xaxis.set_visible(False)
    save(fig, save_path)
```

---

## Template 5: Donut Chart

**Scenario**: Proportion distribution (max 5 slices, avoid if possible — bar charts are usually better).

```python
def donut(labels, values, title, center_text=None,
          colors=None, save_path='donut.png'):
    if colors is None:
        colors = COOL[:len(labels)]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, _, autotexts = ax.pie(
        values, labels=None, colors=colors, autopct='%1.0f%%',
        startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))
    
    for t in autotexts:
        t.set_fontsize(10)
        t.set_fontweight('bold')
    
    if center_text:
        ax.text(0, 0.06, str(center_text), ha='center', va='center',
                fontsize=28, fontweight='bold', color=G900)
        ax.text(0, -0.1, '总计', ha='center', va='center', fontsize=11, color=G500)
    
    ax.legend(wedges, labels, loc='center left',
              bbox_to_anchor=(1, 0.5), fontsize=10)
    ax.set_title(title, loc='center', pad=20)
    save(fig, save_path)
```

---

## Template 6: Scatter Plot + Trend Line

**Scenario**: Two-variable correlation analysis.

```python
def scatter_trend(x, y, title, xlabel, ylabel,
                  color=C_BLUE, save_path='scatter.png'):
    fig, ax = plt.subplots(figsize=(10, 7))
    
    ax.scatter(x, y, c=color, s=50, alpha=0.6,
               edgecolors='white', linewidth=1, zorder=3)
    
    # Trend line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(x), max(x), 100)
    ax.plot(x_line, p(x_line), color=G400, linewidth=1.5,
            linestyle='--', zorder=2, alpha=0.7)
    
    ax.set_title(title, loc='left')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    clean_axis(ax, grid=True)
    ax.xaxis.grid(True, alpha=0.08, color=G300)
    save(fig, save_path)
```

---

## Template 7: Heatmap

**Scenario**: Matrix data, correlations, time × category.

```python
def heatmap(data, row_labels, col_labels, title,
            cmap_color=C_BLUE, save_path='heatmap.png'):
    from matplotlib.colors import LinearSegmentedColormap
    
    cmap = LinearSegmentedColormap.from_list('bc', ['#FFFFFF', cmap_color])
    fig, ax = plt.subplots(
        figsize=(max(8, len(col_labels)*1.2), max(6, len(row_labels)*0.6)))
    
    arr = np.array(data)
    im = ax.imshow(arr, cmap=cmap, aspect='auto')
    
    vmax = arr.max()
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            val = arr[i][j]
            color = 'white' if val > vmax * 0.6 else G700
            ax.text(j, i, f'{val:.1f}', ha='center', va='center',
                    fontsize=9, color=color)
    
    ax.set_xticks(range(len(col_labels)))
    ax.set_yticks(range(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    ax.set_title(title, loc='left', pad=16)
    
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.08, shrink=0.8)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(labelsize=8)  # colorbar ticks should not be too large
    
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(G200)
    save(fig, save_path)
```

---

## Template 8: KPI Metric Cards

**Scenario**: Dashboard top key number display.

```python
def kpi_cards(metrics, save_path='kpi.png'):
    """
    metrics: [{'label': '总收入', 'value': '12.8M', 
               'change': '+23%', 'positive': True}, ...]
    """
    from matplotlib.patches import FancyBboxPatch
    
    n = len(metrics)
    fig, axes = plt.subplots(1, n, figsize=(3.8*n, 2.8))
    if n == 1: axes = [axes]
    
    for ax, m in zip(axes, metrics):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
        
        bg = FancyBboxPatch((0.05, 0.05), 0.9, 0.9,
            boxstyle='round,pad=0.05', facecolor=G50, edgecolor=G200, linewidth=0.8)
        ax.add_patch(bg)
        
        ax.text(0.5, 0.75, m['label'], ha='center', va='center',
                fontsize=10, color=G500)
        ax.text(0.5, 0.45, m['value'], ha='center', va='center',
                fontsize=24, fontweight='bold', color=G900)
        
        if 'change' in m:
            is_pos = m.get('positive', True)
            ax.text(0.5, 0.18,
                    f'{"↑" if is_pos else "↓"} {m["change"]}',
                    ha='center', va='center', fontsize=11,
                    color=POS if is_pos else NEG, fontweight='bold')
    
    save(fig, save_path)
```

---

## Template 9: Radar Chart

**Scenario**: Multi-dimensional capability comparison (max 8 dimensions, max 3 groups).

```python
def radar(categories, datasets, series_names, title,
          colors=None, save_path='radar.png'):
    if colors is None:
        colors = COOL[:len(datasets)]
    
    N = len(categories)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # Close the polygon
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.yaxis.set_visible(False)
    
    # Grid beautification
    ax.spines['polar'].set_color(G200)
    ax.grid(color=G200, linewidth=0.5, alpha=0.5)
    
    for data, name, color in zip(datasets, series_names, colors):
        vals = data + data[:1]  # Close the polygon
        ax.plot(angles, vals, color=color, linewidth=2, label=name)
        ax.fill(angles, vals, color=color, alpha=0.08)
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.set_title(title, pad=30, fontsize=16, fontweight='bold')
    save(fig, save_path)
```

---

## Template 10: Waterfall Chart

**Scenario**: Show incremental changes from start to end value.

```python
def waterfall(labels, values, title, save_path='waterfall.png'):
    """labels and values correspond, positive=increase negative=decrease, last item auto-treated as total"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    cumulative = [0]
    for v in values[:-1]:
        cumulative.append(cumulative[-1] + v)
    
    bar_colors = []
    for i, v in enumerate(values):
        if i == len(values) - 1:
            bar_colors.append(C_BLUE)      # Total
        elif v >= 0:
            bar_colors.append(POS)          # Increase
        else:
            bar_colors.append(NEG)          # Decrease
    
    bottoms = []
    for i, v in enumerate(values):
        if i == len(values) - 1:
            bottoms.append(0)               # Total starts from 0
        elif v >= 0:
            bottoms.append(cumulative[i])
        else:
            bottoms.append(cumulative[i] + v)
    
    bars = ax.bar(labels, [abs(v) for v in values], bottom=bottoms,
                  color=bar_colors, width=0.6, edgecolor='white', linewidth=0.5, zorder=3)
    
    # Connecting lines
    for i in range(len(values) - 2):
        y = cumulative[i+1]
        ax.plot([i+0.3, i+0.7], [y, y], color=G300, linewidth=0.8, zorder=2)
    
    # Value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        y_pos = bar.get_y() + bar.get_height() + max(abs(v) for v in values)*0.01
        prefix = '+' if val > 0 and i < len(values)-1 else ''
        ax.text(bar.get_x()+bar.get_width()/2, y_pos,
                f'{prefix}{val:,.0f}', ha='center', va='bottom',
                fontsize=9, color=G700)
    
    ax.set_title(title, loc='left')
    clean_axis(ax)
    save(fig, save_path)
```

---

## Template 11: Multi-Subplot Dashboard (GridSpec Precision Layout)

**Scenario**: Combine multiple subplots into a dashboard. ⚠️ Max 4 subplots per canvas, split if exceeded.

**Core Principle**: Use `GridSpec` for precise control of each subplot's position and spacing, don't rely on `tight_layout()`.

```python
import matplotlib.gridspec as gridspec

def dashboard(data_dict, title, save_path='dashboard.png'):
    """
    2x2 dashboard layout example.
    data_dict contains data needed for each subplot.
    """
    # ⚠️ Use constrained_layout instead of tight_layout
    fig = plt.figure(figsize=(16, 12), constrained_layout=True)
    fig.suptitle(title, fontsize=20, fontweight='bold', y=0.98)
    
    # GridSpec: precise spacing control
    gs = gridspec.GridSpec(2, 2, figure=fig,
                           wspace=0.35,  # Column spacing (at least 0.3)
                           hspace=0.35,  # Row spacing (at least 0.3)
                           left=0.08, right=0.92,
                           top=0.92, bottom=0.08)
    
    # ─── Top-left: bar chart ───
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_title('Quarterly Revenue', loc='left', fontsize=13, fontweight='bold')
    # ... binddata ...
    clean_axis(ax1)
    
    # ─── Top-right: line chart ───
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_title('Monthly Trend', loc='left', fontsize=13, fontweight='bold')
    # ... bind data ...
    clean_axis(ax2)
    
    # ─── Bottom-left: pie chart ───
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.set_title('Category Share', loc='left', fontsize=13, fontweight='bold')
    # ... bind data ...
    
    # ─── Bottom-right: scatter plot ───
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_title('Conversion Analysis', loc='left', fontsize=13, fontweight='bold')
    # ... bind data ...
    clean_axis(ax4)
    
    fig.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close(fig)
```

### Dashboard Layout Golden Rules

| Rule | Description |
|------|-------------|
| **Max 4 subplots** | Split into multiple charts if exceeded |
| **Use `constrained_layout=True`** | Smarter than `tight_layout()`, auto-avoids labels |
| **`wspace/hspace ≥ 0.3`** | Subplot spacing too small causes overlap |
| **Independent title per subplot** | Use `ax.set_title()` instead of `fig.suptitle()` |
| **Consistent font sizes** | Subtitle 13px, axis labels 10px, data labels 9px |
| **Colorbar in separate column** | If a subplot needs colorbar, allocate `gs[0, 2]` separately |
| **Don't mix legend and direct labels** | Use either all legends or all direct labels in a dashboard |

### Safe Layout with Colorbar

```python
# When a subplot needs a colorbar, use 3-column layout, rightmost column for colorbar
gs = gridspec.GridSpec(2, 3, figure=fig,
                       width_ratios=[1, 1, 0.05],  # Third column very narrow, dedicated to colorbar
                       wspace=0.4, hspace=0.35)

ax_heat = fig.add_subplot(gs[0, 1])
im = ax_heat.imshow(data, cmap='Blues')

# Colorbar placed in its own subplot position, won't obscure any content
cbar_ax = fig.add_subplot(gs[0, 2])
fig.colorbar(im, cax=cbar_ax)
cbar_ax.set_ylabel('Value', fontsize=10)
```

### Split Strategy for More Than 4 Subplots

```python
# ❌ Wrong: 8 subplots crammed into one canvas
fig, axes = plt.subplots(2, 4, figsize=(20, 10))  # Everything becomes unreadable

# ✅ Correct: split into 2 figures, 4 subplots each
# Figure 1: overview metrics
fig1 = plt.figure(figsize=(16, 12), constrained_layout=True)
# ... 4 subplots ...
fig1.savefig('dashboard_overview.png', dpi=200)

# Figure 2: detailed analysis
fig2 = plt.figure(figsize=(16, 12), constrained_layout=True)
# ... 4 subplots ...
fig2.savefig('dashboard_detail.png', dpi=200)
```
