---
name: charts
metadata:
  author: Z.AI
  version: "1.0"
description: >
  Professional chart and diagram creation skill. Covers all types of visual data
  representation and structural diagrams:
  - **Data charts**: bar charts, line charts, pie charts, scatter plots, heatmaps,
    radar charts, candlestick charts, boxplots, histograms, area charts, waterfall charts,
    regression plots, distribution plots, and statistical visualizations.
  - **Structural diagrams**: flowcharts, mind maps, tree diagrams, org charts,
    architecture diagrams, network/relationship graphs, ER diagrams, class diagrams,
    Gantt charts, swimlane diagrams, and sequence diagrams.
  - **Dashboards**: data dashboards, KPI panels, multi-chart compositions,
    and interactive visualizations.
  - **Design quality**: professional color systems, anti-overlap rules, layout optimization,
    scene-based framework routing (matplotlib, seaborn, ECharts, D3.js, Mermaid, Playwright+CSS),
    and publication-ready output.
  Applies when the user wants to create, generate, draw, plot, visualize, or improve
  any chart, graph, diagram, or dashboard. Also applies when the user asks for something
  more polished, cleaner, or publication-ready.
  NOT for: PDF document layout (use pdf skill), slide decks (use slides skill),
  spreadsheets with embedded charts (use xlsx skill), AI image generation (use image_gen),
  posters / infographics / creative cards (use pdf skill Creative pipeline).
  FORBIDDEN: Using matplotlib/seaborn to draw mind maps, tree diagrams, org charts,
  flowcharts, or any structural diagram. These MUST use Playwright+CSS.
license: Proprietary. LICENSE.txt has complete terms
---

# Beautiful Charts

## Quick Setup

```bash
bash "$SKILL_DIR/setup.sh"    # Interactive environment check + install
```

Make every chart and diagram look professionally designed, not AI-generated.

## Architecture

| Module | File | When to Load |
|--------|------|-------------|
| **Routing + Core Rules** | This file | Always read first |
| **Framework Templates** | `references/` by framework | After choosing framework, read the corresponding file |

**Loading order: Read this file → choose framework → read template file → start coding.**

Each template file contains its own framework-specific rules (spacing, connectors, color details). This file contains only routing decisions and universal rules that apply to ALL charts.

---

# Part 1: Routing

## ⚠️ Format Constraint Rule (HIGHEST PRIORITY)

**When the user specifies an output format/tool, you MUST comply. Never substitute.**

| User Says | You Must Do | Forbidden |
|-----------|------------|-----------|
| "use mermaid code" / "用Mermaid格式输出" / "转化为mermaid" / "mermaid流程" | ① Output Mermaid code block (```mermaid ... ```) ② Also provide a rendered image preview | ❌ Cannot only give image without code; ❌ Cannot screenshot raw code text as image |
| "use markdown code" | Output markdown-formatted hierarchy | ❌ Cannot switch to HTML/CSS |
| "via mermaid or markdown code" | Choose one of the two, output code text | ❌ Cannot switch to any non-specified format |
| "flowchart" / "mind map" (no format specified) | Free to choose the best approach | - |
| "use echarts/d3" | Must use the specified framework | ❌ Cannot switch |

### 🚫 FORBIDDEN: Mermaid Code Screenshot
**NEVER take a screenshot of raw Mermaid source code and deliver it as the "diagram image".** This is the worst possible outcome — the user gets neither usable code nor a visual diagram. When the user requests Mermaid format:
1. **MUST** output the Mermaid code in a fenced code block (````mermaid`)
2. **SHOULD** also render the code into a visual diagram image (via mermaid-cli or Playwright + mermaid.js)
3. If rendering fails, deliver the code block and tell the user to paste it into mermaid.live

### Format Specified vs Auto-Upgrade Conflict
When the user specifies Mermaid but content triggers auto-upgrade conditions (>8 nodes, CJK-heavy, etc.):
1. **User choice wins** — still use Mermaid, deliver code block + rendered image
2. **Proactively guide** — after delivery, suggest the user try without specifying Mermaid for better layout quality
3. **Never silently switch** to Playwright+CSS when user explicitly asked for Mermaid

When a specified tool hits rendering difficulties (e.g., mermaid CDN fails):
- ✅ Output raw mermaid code text, tell user to view at mermaid.live
- ❌ Secretly switch to another framework
- ❌ Screenshot the code text as an "image"

---

## Routing Decision Tree

### 1. Structural Diagrams

#### 🔴 Flowchart Default: Phased Vertical (HIGHEST PRIORITY)

**When the user asks to "generate/create a XXX flowchart/流程图" without specifying format, the DEFAULT layout is Phased Vertical (Layout C in `references/playwright-css.md`).**

This is because nearly all real-world processes (manufacturing, legal proceedings, project management, business operations, cooking recipes, etc.) have natural phases/stages. Layout C produces the most professional, readable result.

**Flowchart routing priority:**
1. **User specified Mermaid/markdown** → follow user choice (Format Constraint Rule)
2. **≤6 nodes AND no phases AND short text** → Mermaid (simple flowchart)
3. **Everything else** → **Playwright + CSS, Layout C (Phased Vertical)** → `references/playwright-css.md`

**Phase detection — treat as "has phases" when ANY is true:**
- Content has numbered sections (一、二、三 or 1. 2. 3. or Phase 1/Stage 1)
- Process can be grouped by time/stage/role (e.g., "preparation → execution → review")
- Total steps ≥ 5 (almost always groupable into 2+ phases)
- Process involves multiple roles/departments
- Process has clear start/end with intermediate stages

**⚠️ When in doubt, default to Layout C.** A phased layout with only 1 phase still looks professional. A Grid layout with phases looks like a mess.

#### Other Structural Diagrams
- Simple flowchart (≤6 nodes, truly flat, no phases): **Mermaid**
- Complex flowchart (>6 nodes / CJK-heavy / branches / phases): **Playwright + CSS Layout C** → `references/playwright-css.md`
- Mind map / tree / org chart: **Playwright + CSS** → `references/mindmap-css.md`
- Relationship / network diagram: **ECharts graph**
- Center-radial analysis (SWOT / BSC / Porter's Five Forces / PEST): **Playwright + CSS** → `references/radial-grid.md`

### 2. Data Charts (matplotlib / seaborn)
- Standard bar/line/scatter/heatmap/radar/pie: **matplotlib**
- Regression/distribution/boxplot: **Seaborn**

### 3. Interactive Charts / Dashboards
- Data dashboard / candlestick / real-time: **ECharts**
- Fully custom interactive: **D3.js**

### Default Strategy
**One scene, one tool — don't hesitate:**

| Scene | Tool | Template |
|-------|------|----------|
| Data chart (bar/line/scatter/pie/radar) | matplotlib | `references/matplotlib.md` |
| Statistical (regression/box/dist) | Seaborn | `references/seaborn.md` |
| Mind map / tree / org chart | Playwright + CSS | `references/mindmap-css.md` |
| Center-radial (SWOT/BSC/PEST/Five Forces) | Playwright + CSS | `references/radial-grid.md` |
| **Any flowchart (default)** | **Playwright + CSS Layout C** | **`references/playwright-css.md`** |
| Simple flowchart (≤6 nodes, truly flat) | Mermaid | `references/mermaid.md` |
| Relationship / force-directed | ECharts graph | `references/echarts.md` |
| Data dashboard | ECharts | `references/echarts.md` |
| Academic paper figures | matplotlib | `references/matplotlib.md` |

---

## Mermaid Auto-Upgrade Rules

Mermaid's dagre/elk layout estimates CJK widths incorrectly. **Auto-switch to Playwright+CSS when ANY condition is met:**

| Trigger | Action |
|---------|--------|
| Total nodes > **6** | → CSS flowchart (Layout C) |
| Any node text > **12 Chinese characters** | → CSS flowchart |
| More than **3 parallel branches** | → CSS flowchart |
| Nested subgraphs > **2 levels** | → CSS flowchart |
| Connector crossings > **2** | → CSS flowchart |
| **Side annotations / dashed note boxes** | → CSS flowchart |
| **Loop-back / cycle arrows** | → CSS flowchart |
| **Process has identifiable phases/stages** | → CSS flowchart (Layout C) |

**If staying with Mermaid**: `padding: 32`, `nodeSpacing: 80`, `rankSpacing: 80`. Node text ≤ 10 CJK chars/line, wrap with `<br>`, quote all text `A["text"]`.

---

## Large Dataset Rendering

| Data Size | Approach |
|-----------|----------|
| < 1,000 points | matplotlib / any |
| 1,000 - 10,000 | matplotlib (no markers) or ECharts |
| 10,000 - 100,000 | ECharts (Canvas mode) |
| > 100,000 | ECharts (`large: true`) or WebGL |

---

# Part 2: Universal Rules

These rules apply to ALL charts regardless of framework. Framework-specific rules live in each template file.

## 7 Core Rules

1. **Zero overlap.** No element may cover another's text. Overlap = information loss = task failure. Post-generation: verify every element has clear separation.

2. **Hierarchy over uniformity.** Primary nodes larger/bolder than secondary. Annotation nodes smaller/muted. Spacing between groups > within groups. If every box looks identical, the layout has failed.

3. **Low-saturation palette.** 70% background/neutral, 20% secondary, 10% accent (one highlight only). No high-saturation large fills. Saturated colors only on borders (2px), text, and small elements.

4. **Insight first.** Titles express conclusions, not field names. Remove non-essential elements: top/right borders, grid lines, tick marks, legend box borders. If removing it doesn't reduce understanding, it shouldn't exist.

5. **Label clarity over label method.** The goal is zero overlap — choose the method that achieves it for each chart type. Direct labels, legends, and leader lines are all valid; what matters is that nothing overlaps.

### 🚫 FORBIDDEN: Any Text Overlapping Any Other Element
**No label, legend, annotation, or title may overlap any other visual element.** This is the single most common matplotlib defect. Both direct labels AND legends can cause overlap — neither is inherently safe.

**Anti-overlap decision tree:**
1. **Check if direct labels fit** — if all labels have enough space (bar tops, line endpoints, large pie slices), label directly. No legend needed.
2. **If some labels would collide** (small pie slices, dense scatter points, clustered bars) → use legend outside plot area instead of forcing labels into tight spaces.
3. **Mixed approach** — label the major items directly, group small items into "其他" or use leader lines + legend for the small ones.

**Pie chart specific (the worst offender):**
- Slices < 5%: MUST use leader lines (`wedgeprops + texts` manual repositioning, or `matplotlib.patches.ConnectionPatch`) to pull labels outside. Do NOT rely on `autopct` alone — it places text inside/near the slice.
- Multiple small adjacent slices: use `bbox_to_anchor` legend outside, NOT direct labels
- `labeldistance=1.25` minimum to keep labels outside the pie
- When >2 slices are < 5%, consider grouping all < 3% into "其他（X项）"
- Use `adjustText` library to auto-resolve label collisions when available

**Legend placement (when legend is needed):**
- Place legend **outside** the plot area using `bbox_to_anchor`
- Suggested starting positions:
  - Bar/line/scatter: right side outside (`bbox_to_anchor=(1.02, 1), loc='upper left'`)
  - Pie: right side outside (`bbox_to_anchor=(1.1, 0.5), loc='center left'`)
  - Radar: below chart (`bbox_to_anchor=(0.5, -0.15), loc='upper center'`)
  - Heatmap: no legend needed (colorbar suffices)

**🔧 Mandatory: auto-adjust legend to prevent overlap.** Copy this snippet after placing any legend:
```python
# ── Auto-adjust legend position to prevent overlap ──
fig.canvas.draw()  # must render first to get bboxes
legend = ax.get_legend()
if legend:
    renderer = fig.canvas.get_renderer()
    # Try shifting up to 5 times to resolve overlap
    for _ in range(5):
        leg_bb = legend.get_window_extent(renderer).transformed(ax.transAxes.inverted())
        has_overlap = False
        for text in ax.texts + [ax.title] + ax.get_xticklabels() + ax.get_yticklabels():
            if not text.get_text():
                continue
            txt_bb = text.get_window_extent(renderer).transformed(ax.transAxes.inverted())
            if leg_bb.overlaps(txt_bb):
                has_overlap = True
                break
        if not has_overlap:
            break
        # Move legend further outside (direction depends on current loc)
        bbox = legend.get_bbox_to_anchor().transformed(ax.transAxes.inverted())
        x0, y0 = bbox.x0, bbox.y0
        # Heuristic: if legend is below center, move down; if right of center, move right
        if y0 < 0.5:
            legend.set_bbox_to_anchor((x0, y0 - 0.08), transform=ax.transAxes)
        else:
            legend.set_bbox_to_anchor((x0 + 0.08, y0), transform=ax.transAxes)
        fig.canvas.draw()
```
- **After placing legend**: always call `plt.tight_layout()` or `fig.subplots_adjust()` to ensure legend is not clipped

🚫 FORBIDDEN:
- `loc='best'` — matplotlib's "best" frequently overlaps data
- `loc='upper right'` / `loc='lower right'` on line/bar charts — high collision risk
- Direct labels on pie slices < 5% without leader lines
- Any text placement without verifying zero overlap

6. **Font discipline.** Max 2 fonts. Chinese: SimHei/PingFang SC. Always explicitly set fonts in code. Font size follows hierarchy (title 18-24px → body 13-15px → annotation 11-13px). Never go below 10px floor. When text overflows: condense text → enlarge canvas → last resort: shrink font (but never below floor).

7. **Whitespace is design.** Chart area 60-70% of canvas, margins 15-20%. At least 16pt between title and chart. Crowded ≠ information-rich.

---

## Color System

### Recommended Palettes

| Palette | Text | Background | Block Fill | Accent |
|---------|------|------------|------------|--------|
| Business Cool | `#243447` | `#F8FAFC` | `#E9EEF3` | `#4C6EF5` |
| Tech Cyan-Gray | `#1F2937` | `#F5F7FA` | `#E6ECF2` | `#3AAFA9` |
| Morandi Warm | `#4B4A45` | `#FAF8F4` | `#EAE4DB` | `#C6866A` |
| Invisible Precision | `#37352F` | `#FFFFFF` | `#F7F7F7` | `#2383E2` |

### 🚫 Forbidden Background Colors

| Color | Forbidden Hex Values |
|-------|---------------------|
| Pure blue | `#3B82F6`, `#2563EB`, `#1D4ED8` |
| Pure green | `#10B981`, `#059669`, `#22C55E` |
| Pure red | `#EF4444`, `#DC2626`, `#F87171` |
| Pure purple | `#8B5CF6`, `#7C3AED`, `#A855F7` |
| Pure amber | `#F59E0B`, `#D97706`, `#FB923C` |

### ✅ Allowed Background Colors

| Color | Hex Values |
|-------|------------|
| Ice blue | `#EFF6FF`, `#DBEAFE` |
| Mint green | `#F0FDF4`, `#D1FAE5` |
| Light amber | `#FFF7ED`, `#FEF3C7` |
| Lavender | `#F5F3FF`, `#EDE9FE` |
| Light gray | `#F8FAFC`, `#F1F5F9` |

### Functional Color (states only, not decoration)
- Active/Selected: brand accent or `2px` accent line
- Error: `#EF4444`
- Success: `#10B981`
- Tags: light bg + dark text, never high-sat pills

### Colorblind-Safe
Don't rely on color alone — pair with shape, line style, or direct labels.
Paul Tol palette: `['#0077BB', '#33BBEE', '#009988', '#EE7733', '#CC3311', '#EE3377']`

### Dark Theme
- Background: `#0F172A` (not pure black)
- Text: `#F1F5F9` (not pure white)
- Grid: `#1E293B`, low alpha
- Export: `savefig(facecolor='#0F172A')`

---

## Export Rules

- Static charts: minimum 200 DPI, recommended 300 DPI
- Pie/radar: **square `figsize=(8, 8)`** — non-square = elliptical
- No more than 6 colors per chart (split if more)
- Bar chart Y-axis starts at 0 (line charts may truncate)
- Never use 3D (distorts proportions)

### Playwright Screenshot
Default `device_scale_factor=2`. Large mind maps (3000px+): 1.5. PDF embed: 1-1.5. Print: 3.
After render, read `bounding_box()` and resize viewport to fit. Min viewport: 800px single-col, 1200px multi-col.

### 🚫 FORBIDDEN: `max-width` on Mermaid/SVG Containers
Mermaid's dagre engine produces SVGs with unpredictable width (especially with subgraphs, CJK text, or parallel branches). **NEVER set `max-width` on the Mermaid container element.** Use `width: fit-content; min-width: 800px;` instead.

**Root cause**: Mermaid SVGs overflow their CSS container silently. `bounding_box()` (Playwright) returns the CSS box model size, NOT the SVG's actual rendered size. So auto-resize viewport based on `bounding_box()` alone will still produce clipped screenshots.

**Fix**: Always read the **SVG element's own `getBoundingClientRect()`** via `page.evaluate()`, then use `max(css_size, svg_size) + padding` for viewport dimensions. See `references/mermaid.md` for the corrected screenshot script.

### Aspect Ratio Preservation (embedding)
**MUST read actual image dimensions and calculate height proportionally. NEVER hardcode both width and height.**

---

## matplotlib-Specific Rules

These apply when routing to matplotlib/seaborn:

### Layout & Overlap
- Prefer `constrained_layout=True` over `tight_layout()`
- Use `adjustText` library for automatic label repositioning — **this is the most reliable anti-overlap tool for matplotlib.** Install: `pip install adjustText`. Usage: `from adjustText import adjust_text; adjust_text(texts)`
- Max 4 subplots per canvas. More → split images or `figsize=(20, 16)` minimum
- Multi-subplot: `GridSpec` with `wspace/hspace` ≥ 0.3
- Colorbar: `shrink=0.8` + `pad=0.08`
- Data labels: Y-axis upper limit with 15-20% headroom (`ylim(0, max_val * 1.18)`)
- Long X labels → horizontal bar chart or show every N-th label

### Radar / Spider Charts
- **Every `fill()` MUST have `alpha=0.25`** (max 0.3). Omitting alpha = opaque = hides underlying series.
- Legend: place outside chart with `bbox_to_anchor`, start with `(0.5, -0.15), loc='upper center'`. If dimension labels are long or dimensions > 8, increase offset (e.g., `-0.25` or `-0.3`). Also FORBIDDEN: `loc='lower right'` (collides with radar dimension labels).
- Dimension label padding: `set_rlim(0, max_value * 1.2)`
- Labels with >4 CJK chars: rotate to follow angle or abbreviate
- `figsize=(8, 8)` mandatory (square)

### One Color, Gray the Rest
5 lines → color only the key one, others `#D1D5DB`. 8 bars → accent only the highlight, rest `#E5E7EB`.

---

## Connector Rules (structural diagrams)

- Attach to node edges, not through centers
- Prefer orthogonal polylines or clean curves
- Main paths avoid crossing
- Never pass through text areas
- Start/end points at same level must align (no staggering)
- Same-level connectors follow same direction
- Bend angles consistent (all right-angles or all curves, no mixing)
- Label positions uniform (all above line or all centered)

---

## Pre-Output Checklist

Before delivery, verify:

- [ ] Zero overlap (nodes, connectors, labels, legends — **especially check legend vs data, and adjacent pie/bar labels**)
- [ ] No connectors pass through text boxes
- [ ] Clear hierarchy (primary/secondary/annotation visually distinct)
- [ ] Low-saturation palette (no forbidden background colors)
- [ ] Text readable at final size (standalone: ≥12px body, ≥10px annotation; PDF embed: ≥10pt/8pt/7pt)
- [ ] Legend fully visible, not clipped, not overlapping any chart element
- [ ] Canvas wide/tall enough (check bounding box before screenshot)
- [ ] **If mind map**: each level distinct (≥3 property changes), connectors visible (≥ `#94A3B8`), left-right balanced
- [ ] **If flowchart**: phase titles distinct from steps, arrows only between phases, **using Layout C by default**
- [ ] **If flowchart**: phase colors are same-hue family (blue-gray progression), **NOT rainbow** (blue→green→amber→purple)
- [ ] **If flowchart looks scattered**: STOP — you're using the wrong layout, switch to Layout C
- [ ] **If Mermaid looked rigid**: already switched to Playwright+CSS

---

## Anti-Pattern Quick Reference

| ❌ Don't | ✅ Do This Instead |
|----------|-------------------|
| matplotlib default blue `#1f77b4` | Use this skill's palette |
| 3D bar/pie | Always 2D |
| Rainbow colormap (jet/rainbow) | Single-hue gradient or diverging |
| Thick black grid lines | `alpha=0.08` or remove |
| Different color per bar | Same series same color, highlight only key |
| 45° tilted X labels | Horizontal bar chart or shorten |
| 8+ subplots in one canvas | Split to 2-3 images, max 4 each |
| `tight_layout()` alone | `constrained_layout=True` or `GridSpec` |
| Labels overflowing chart | `ylim` with 18-25% headroom |
| Mind map: all levels same style | Root+L1 get boxes, leaves plain text |
| Mind map: image too tall | Left-right layout for ≥5 branches |
| Mind map: invisible connectors | Lines ≥ `#94A3B8`, root→L1 `#64748B` 2.5px |
| Mind map: unbalanced sides | Alternate large/small branches across sides |
| Flowchart: high-sat node fills | Low-sat bg (`#EFF6FF`) + sat border (`#3B82F6`) |
| Flowchart: dark bg + dark text | Dark bg → white text. Light bg → dark text |
| Flowchart: arrows between every step | Arrows ONLY between phases, steps use indent |
| Flowchart: cross-layer lines through nodes | Connect adjacent layers only |
| Flowchart: Grid layout for phased process | **Always use Layout C (Phased Vertical)** |
| Flowchart: phase titles as floating labels | Phase titles MUST be inside group cards |
| Flowchart: nodes scattered without grouping | Group nodes into phase cards with `.phase-group` |
| Flowchart: rainbow phase colors (blue→green→amber→purple) | Same-hue blue-gray progression for all phases |
| Multiple arrows to same entry point | Merge-then-enter pattern |
| Legend inside plot obscuring data | `bbox_to_anchor` outside plot area |
| Radar fill without alpha | `alpha=0.25` mandatory |
| Decorative icons/emoji | Let the data speak |
| Grid lines where whitespace suffices | Background contrast or spacing instead |

---

## UI Aesthetics (dashboards / card layouts)

When building UI-style outputs (dashboards, panels), apply "Invisible Precision":

- **Boundaries**: Subtle bg shifts (`#F7F7F7` on `#FFFFFF`), not border lines. Reserve `1px` dividers for absolute logical breaks only.
- **Actions**: Primary CTA in dark neutral (`#1A1A1B`). Secondary: ghost/gray. Hover: 5% darker, no size change.
- **Quiet UI**: Action buttons `opacity: 0` by default, `1` on hover. Only active elements get visual indicators.
- **Numbers**: `font-variant-numeric: tabular-nums` for strict vertical alignment.
- **Spacing**: `line-height: 1.625`, generous paragraph spacing.
