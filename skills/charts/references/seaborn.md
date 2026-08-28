# Seaborn Template Library

> **⚠️ Before writing any code, read [`_rules.md`](references/_rules.md) — three non-negotiable rules on overlap, hierarchy, and color.**


Seaborn is built on top of matplotlib, specializing in **statistical visualization** — distributions, regression, categorical comparisons, etc.
Its default styles are already much better looking than matplotlib, but still need tuning to reach professional standards.

## Environment Setup

```python
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# ═══ Chinese Font Setup ═══
# Font path: adjust for your system. Common locations:
#   macOS: '/System/Library/Fonts/Supplemental/SimHei.ttf'
#   Linux: '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
#   Custom: './fonts/SimHei.ttf'
import os
SIMHEI_PATH = os.environ.get('SIMHEI_FONT', '/System/Library/Fonts/Supplemental/SimHei.ttf')
matplotlib.font_manager.fontManager.addfont(SIMHEI_PATH)

# Seaborn theme + custom overrides
sns.set_theme(style='whitegrid', font='SimHei', rc={
    'axes.unicode_minus': False,
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#E5E7EB',
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'grid.color': '#F3F4F6',
    'grid.alpha': 0.5,
    'grid.linewidth': 0.5,
    'xtick.major.size': 0,
    'ytick.major.size': 0,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.titlepad': 16,
    'legend.frameon': False,
    'figure.dpi': 200,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
})

# Colors (consistent with matplotlib.md)
COOL = ['#3B82F6', '#06B6D4', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981']
CB_SAFE = ['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']
```

## Seaborn Palette Setup

```python
# Method 1: use hex list directly
sns.set_palette(COOL)

# Method 2: register custom palette
from matplotlib.colors import ListedColormap
bc_palette = ListedColormap(COOL, name='charts')
```

---

## Template 1: Distribution Plot (Histogram + KDE)

**Scenario**: View data distribution shape, detect skewness and outliers.

```python
def dist_plot(data, title, xlabel, color='#3B82F6', save_path='dist.png'):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.histplot(data, kde=True, color=color, edgecolor='white',
                 linewidth=0.5, alpha=0.7, ax=ax)
    
    # Bold the KDE line
    for line in ax.get_lines():
        line.set_linewidth(2.5)
    
    ax.set_title(title, loc='left')
    ax.set_xlabel(xlabel)
    ax.set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Template 2: Box Plot (Categorical Comparison)

**Scenario**: Compare distribution characteristics across groups (median, quartiles, outliers).

```python
def box_compare(df, x_col, y_col, title, palette=None, save_path='box.png'):
    if palette is None:
        palette = COOL
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.boxplot(data=df, x=x_col, y=y_col, palette=palette,
                width=0.5, linewidth=1.2, fliersize=4,
                boxprops=dict(edgecolor='white'),
                medianprops=dict(color='white', linewidth=2),
                ax=ax)
    
    ax.set_title(title, loc='left')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

### Box Plot + Label Avoidance (For Complex Scenarios)

When you need to annotate outliers, specific data points, or group names on a box plot, **label avoidance is required**:

```python
def box_annotated(df, x_col, y_col, title, annotations=None,
                  palette=None, save_path='box_annotated.png'):
    """
    annotations: [{'x': 0, 'y': 45, 'text': '产线A 异常'}, ...]
    """
    from adjustText import adjust_text
    
    if palette is None:
        palette = COOL
    
    fig, ax = plt.subplots(figsize=(12, 7))  # Slightly larger canvas, leave room for annotations
    
    sns.boxplot(data=df, x=x_col, y=y_col, palette=palette,
                width=0.5, linewidth=1.2, fliersize=4,
                boxprops=dict(edgecolor='white'),
                medianprops=dict(color='white', linewidth=2),
                ax=ax)
    
    # Annotation text — use adjustText for auto-avoidance
    if annotations:
        texts = []
        for ann in annotations:
            t = ax.text(ann['x'], ann['y'], ann['text'],
                       fontsize=9, color='#374151',
                       bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='#FFF7ED', edgecolor='#F59E0B',
                                alpha=0.9))
            texts.append(t)
        
        adjust_text(texts, ax=ax,
                    arrowprops=dict(arrowstyle='->', color='#9CA3AF', lw=0.8),
                    force_text=(0.8, 1.0),
                    force_points=(0.5, 0.8))
    
    ax.set_title(title, loc='left')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

### Box Plot + Colorbar (e.g., MTTR Analysis)

When a box plot needs to work with a colorbar (e.g., colored by dimension), you must leave enough space for the colorbar:

```python
def box_with_colorbar(df, x_col, y_col, color_col, title,
                      save_path='box_cbar.png'):
    import matplotlib.gridspec as gridspec
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    
    fig = plt.figure(figsize=(14, 7), constrained_layout=True)
    gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1, 0.03], wspace=0.05)
    
    ax = fig.add_subplot(gs[0, 0])
    cbar_ax = fig.add_subplot(gs[0, 1])
    
    sns.boxplot(data=df, x=x_col, y=y_col, ax=ax,
                width=0.5, linewidth=1.2)
    
    # Colorbar in its own subplot, won't obscure box plot
    norm = Normalize(vmin=df[color_col].min(), vmax=df[color_col].max())
    sm = ScalarMappable(norm=norm, cmap='Blues')
    fig.colorbar(sm, cax=cbar_ax, label=color_col)
    
    ax.set_title(title, loc='left')
    fig.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Template 3: Violin Plot

**Scenario**: Enhanced version of box plot, showing distribution density simultaneously.

```python
def violin_plot(df, x_col, y_col, title, palette=None, save_path='violin.png'):
    if palette is None:
        palette = COOL
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.violinplot(data=df, x=x_col, y=y_col, palette=palette,
                   inner='box', linewidth=1, ax=ax)
    
    ax.set_title(title, loc='left')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Template 4: Regression Scatter Plot

**Scenario**: Two-variable relationship + linear regression + confidence interval.

```python
def reg_plot(df, x_col, y_col, title, color='#3B82F6', save_path='reg.png'):
    fig, ax = plt.subplots(figsize=(10, 7))
    
    sns.regplot(data=df, x=x_col, y=y_col, color=color,
                scatter_kws={'s': 50, 'alpha': 0.6, 'edgecolor': 'white', 'linewidth': 1},
                line_kws={'linewidth': 2},
                ax=ax)
    
    ax.set_title(title, loc='left')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Template 5: Correlation Heatmap

**Scenario**: Correlation coefficient matrix among multiple variables.

```python
def corr_heatmap(df, title, cmap='RdBu_r', save_path='corr.png'):
    corr = df.corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Show only lower triangle
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(corr, mask=mask, cmap=cmap, center=0,
                vmin=-1, vmax=1, annot=True, fmt='.2f',
                square=True, linewidths=1, linecolor='white',
                cbar_kws={'shrink': 0.8, 'label': 'Correlation'},
                annot_kws={'size': 9},
                ax=ax)
    
    ax.set_title(title, loc='left', pad=16)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Template 6: Pair Plot

**Scenario**: Overview of pairwise relationships among multiple variables (distribution on diagonal, scatter plots elsewhere).

```python
def pair_plot(df, hue_col=None, palette=None, save_path='pair.png'):
    if palette is None:
        palette = COOL
    
    g = sns.pairplot(df, hue=hue_col, palette=palette,
                     diag_kind='kde', plot_kws={'alpha': 0.6, 's': 30},
                     height=2.5, aspect=1)
    
    g.figure.suptitle('Pairwise Variable Relationships', y=1.02, fontsize=16, fontweight='bold')
    
    g.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Template 7: Facet Grid (FacetGrid)

**Scenario**: Split into multiple subplots by categorical variable for comparison.

```python
def facet_hist(df, col_var, value_col, title, color='#3B82F6', save_path='facet.png'):
    g = sns.FacetGrid(df, col=col_var, col_wrap=3, height=3.5, aspect=1.3)
    g.map(sns.histplot, value_col, color=color, edgecolor='white',
          linewidth=0.5, alpha=0.7, kde=True)
    
    g.set_titles('{col_name}', fontsize=12, fontweight='bold')
    g.figure.suptitle(title, y=1.02, fontsize=16, fontweight='bold')
    
    g.savefig(save_path, dpi=200, facecolor='white', bbox_inches='tight')
    plt.close()
```

---

## Seaborn vs matplotlib Selection Guide

| What to Plot | Use Seaborn | Use matplotlib |
|---------|-----------|--------------|
| Histogram/KDE distribution | ✅ `histplot` / `kdeplot` | Works, but more code |
| Box plot/Violin plot | ✅ One-liner | Works, but rougher style |
| Regression scatter + confidence interval | ✅ `regplot` auto-calculates | Manual fitting + plotting |
| Correlation heatmap | ✅ `heatmap` + mask | Manual `imshow` tedious |
| Pairwise relationship matrix | ✅ `pairplot` unique | No equivalent |
| Facet grid | ✅ `FacetGrid` | `plt.subplots` manual loop |
| Regular bar chart | Less flexible than matplotlib | ✅ More control |
| Line trend chart | Less than matplotlib | ✅ More control |
| Custom annotations/arrows | Not suitable | ✅ `ax.annotate` |

**Principle: Use Seaborn for statistical charts, matplotlib for customized charts.**
