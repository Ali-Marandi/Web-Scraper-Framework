# CSS Mind Map Rendering Engine

> **⚠️ Before writing any code, read [`_rules.md`](references/_rules.md) — three non-negotiable rules on overlap, hierarchy, and color.**

**Core principle: Content-driven, not template-driven. First analyze the content structure, then decide on the layout, and finally render.**

---

## Step 1: Content Analysis

After receiving a mind map requirement, **don't write any HTML/CSS yet**. First parse the content into a tree structure, then calculate key metrics.

### 1.1 Build Tree JSON

```
Input: "How to work efficiently from home", branches include "Environment Setup", "Time Management", "Tool Selection"...
    ↓
Output:
{
  "root": "在家如何高效办公",
  "branches": [
    {
      "label": "环境准备",
      "children": ["独立工作区", "降噪耳机", "人体工学椅"]
    },
    {
      "label": "时间管理",
      "children": [
        { "label": "番茄工作法", "children": ["25分钟专注", "5分钟休息"] },
        "日程规划",
        "避免多任务"
      ]
    },
    ...
  ]
}
```

### 1.2 Key Metrics

| Metric | Calculation Method | What It Affects |
|------|---------|---------|
| `branchCount` | Number of first-level branches | Choose single-sided/dual-sided expansion |
| `maxDepth` | Maximum nesting depth | Canvas width, whether sub-branch is needed |
| `maxChildren` | Maximum children per node | Vertical height of that branch |
| `totalNodes` | Total number of all nodes | Overall canvas size |
| `maxTextLen` | Longest text character count | Node width, whether line breaks are needed |
| `branchWeights[]` | Total descendants per first-level branch | Left-right balance allocation |

### 1.3 Example Analysis

```
Content: "产品经理核心技能", 6 L1 branches, max depth 3, total 35 nodes, max text length 12 chars
→ branchCount=6, maxDepth=3, totalNodes=35, maxTextLen=12
→ branchWeights=[8, 5, 7, 4, 6, 5]
```

---

## Step 2: Layout Decision

Based on the metrics from Step 1, choose a layout scheme. The following are reference suggestions, not hard rules—adjust flexibly according to actual content.

### 2.1 Layout Selection Guide

**Core principle: Use simple layouts for less content, dual-sided layouts for more content, avoid one side becoming too long.**

```
Few branches (roughly ≤4), simple content?
  → Style A: Right-expanding tree (single-sided, compact)

Many branches (roughly ≥5), or single side would be too long?
  → Style B: Left-right expanding tree (dual-sided balanced, most common)

User explicitly requests a specific form?
  → "cards"/"modules" → Style C: Card grid
  → "fishbone"/"root cause analysis" → Style D: Fishbone diagram
```

**Why not use radial layout?** Radial layout (spreading from center outward) almost inevitably causes node overlap when there are more than 3-4 branches, and is extremely difficult to debug. Not recommended.

### 2.2 Canvas Size Calculation

Don't use fixed sizes. Calculate based on content:

```python
def calc_canvas(branch_count, max_depth, total_nodes, max_text_len, layout):
    # Width: depends on depth and text length
    node_width = max(120, max_text_len * 14)  # ~14px per CJK char (including padding)
    if layout == 'left-right':
        width = node_width * max_depth * 2 + 200  # Dual-sided, 200px in center for root node
    else:
        width = node_width * max_depth + 200  # Single-sided

    # Height: depends on max branch vertical expansion
    if layout == 'left-right':
        max_side_nodes = total_nodes // 2 + 2  # rough estimate of single-side nodes
    else:
        max_side_nodes = total_nodes
    height = max_side_nodes * 32 + 200  # ~32px per leaf (including gap)

    # Lower bounds
    width = max(width, 1200)
    height = max(height, 600)
    
    return width, height
```

### 2.3 Left-Right Branch Allocation (Style B)

Goal: Achieve similar visual weight on both sides.

```python
def balance_branches(branch_weights):
    """Greedy bin-packing: sort by weight descending, alternate left/right"""
    indexed = sorted(enumerate(branch_weights), key=lambda x: -x[1])
    left, right = [], []
    left_sum, right_sum = 0, 0
    for idx, weight in indexed:
        if left_sum <= right_sum:
            left.append(idx)
            left_sum += weight
        else:
            right.append(idx)
            right_sum += weight
    return left, right
    # e.g.: weights=[8,5,7,4,6,5] → left=[0,3,5] right=[2,4,1] → 17 vs 18
```

### 2.4 Node Styling Decision

**Principle: The deeper the level, the lighter the visual weight.** This way readers can distinguish main branches from details at a glance.

```
Root node → most prominent: dark solid background, large font (~20px)
L1 branches → next prominent: light fill + colored border, medium font (~15px)
L2 nodes → lighter still: paler fill + thin border, medium-small font (~13px)
Leaf nodes → lightest: capsule frame or plain text, small font (~12-13px)
```

**Key: Leaves should not have the same visual weight as first-level branches.** Leaves' padding, gap, and border thickness should all be significantly smaller than their parent. Otherwise the chart will be vertically too long and lack hierarchy.

---

## Step 3: Rendering

Based on the decisions from Step 2, generate HTML + CSS + JS.

### 3.1 Playwright Screenshot (Universal)

```python
import asyncio
from playwright.async_api import async_playwright

async def mindmap_to_png(html_path, png_path, width=1600):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': width, 'height': 1200}, device_scale_factor=2)
        await page.goto(f'file://{html_path}', wait_until='networkidle')
        await page.wait_for_timeout(500)
        
        el = page.locator('#mindmap')
        bbox = await el.bounding_box()
        # First expansion: ensure content is not clipped
        expand_w = max(width, int(bbox['width'] + 100))
        expand_h = int(bbox['height'] + 100)
        await page.set_viewport_size({'width': expand_w, 'height': expand_h})
        await page.wait_for_timeout(200)
        
        # Call connector script
        await page.evaluate('if(typeof drawAllLines==="function") drawAllLines()')
        await page.wait_for_timeout(200)
        
        # Second contraction: measure actual content right edge, trim right-side blank space
        trim = await page.evaluate('''() => {
            const map = document.getElementById('mindmap');
            const nodes = map.querySelectorAll('.root-node,.branch-node,.sub-node,.leaf,.deep-node');
            const mapRect = map.getBoundingClientRect();
            let maxR = 0, maxB = 0;
            nodes.forEach(n => {
                const r = n.getBoundingClientRect();
                maxR = Math.max(maxR, r.right - mapRect.left);
                maxB = Math.max(maxB, r.bottom - mapRect.top);
            });
            return { contentW: Math.ceil(maxR) + 80, contentH: Math.ceil(maxB) + 80 };
        }''')
        await page.set_viewport_size({'width': trim['contentW'], 'height': trim['contentH']})
        await page.wait_for_timeout(200)
        # Redraw connectors (viewport changed so coordinates change)
        await page.evaluate('if(typeof drawAllLines==="function") drawAllLines()')
        await page.wait_for_timeout(200)
        
        await el.screenshot(path=png_path)
        await browser.close()
        
        import os
        print(f'✅ {png_path} ({os.path.getsize(png_path)/1024:.0f}KB)')
```

### 3.2 Universal Recursive Connector Script v4-fix (All Styles)

This script automatically handles tree connectors of **any depth** (3, 4, 5 levels... all work). HTML for styles A and B should include this script at the end.

**⚠️ DOM Structure Convention (connector script depends on this structure):**

```
#mindmap
  .tree-layout                      ← flex container (for left-right tree)
    .left-side                      ← left branch area
      .branch.c-{color}            ← L1 branch (must have color class)
        .branch-node               ← L1 node
        .children                  ← L2 container
          div                      ← child wrapper
            .sub-node              ← L2 node
            .leaf-group            ← L3 container
              div / .leaf          ← leaf or wrapper with deeper levels
                .leaf              ← L3 leaf
                .deep-group        ← L4 container (recursive, same as above)
                  .deep-node       ← L4/L5 node
    .center-root
      .root-node                   ← root node
    .right-side                    ← right branches (same structure as .left-side)
```

**Also supports legacy structure (.branches/.right-branches/.left-branches), backward compatible.**

**⚠️ CSS Indentation Rules (connectors depend on child nodes having offset relative to parent, no indentation = broken connectors):**
```css
/* .tree-layout structure (new version) must include these paddings */
.left-side .children, .left-side .leaf-group, .left-side .deep-group {
  align-items: flex-end; padding-right: 16px;
}
.right-side .children, .right-side .leaf-group, .right-side .deep-group {
  align-items: flex-start; padding-left: 16px;
}
```

**Common causes of missing connectors/layout errors:**
- **⚠️ `.sub-branch` missing `display: flex`** (most critical! Without flex, `flex-direction: row-reverse` doesn't work, left-side leaves won't expand left, instead all pile up on the right)
- **⚠️ Child node containers missing padding-left/padding-right** (without indentation, child nodes align with parent, midX is outside child nodes, connectors break)
- **⚠️ `.lr-tree` / `.tree` should not have `z-index`** (creates stacking context, covers SVG connectors)
- **⚠️ Leaf nodes must NOT stretch to equal width** — each leaf should size to its own text content (`white-space: nowrap` or `width: fit-content`). Never add `width: 100%`, `flex-grow: 1`, or `align-items: stretch` to leaf containers. Leaves with shorter text should be narrower than leaves with longer text.
- Leaf container not named `.leaf-group` (using `.child-list`, `.sub-items`, etc.)
- Deep-level container not named `.deep-group`
- `#mindmap` missing `position: relative`

**Key improvements (v4-fix vs v2):**
- **No transparency**—use solid color blend for fading (`color + '80'` is almost invisible on white background)
- **Recursively process `.children`, `.leaf-group`, `.deep-group`**—no longer limited to 3 levels
- **Vertical line draws complete range**—one line from `min(Y)` to `max(Y)`, instead of drawing per child node

```javascript
/**
 * Universal recursive connector script v4-fix
 * - Supports any nesting depth (recursively processes .children + .leaf-group + .deep-group)
 * - Unified gray-tone connectors (#64748B → #94A3B8 → #A8B4C2), visually clean
 * - Direction logic:
 *   dir='left': startX=parent.left → midX(left-biased) → endX=child.right
 *   dir='right': startX=parent.right → midX(right-biased) → endX=child.left
 */
function drawAllLines() {
  const map = document.getElementById('mindmap');
  if (!map) { console.error('❌ #mindmap not found'); return; }
  const cRect = map.getBoundingClientRect();

  const old = map.querySelector('svg.lines');
  if (old) old.remove();

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.classList.add('lines');
  svg.setAttribute('width', cRect.width);
  svg.setAttribute('height', cRect.height);
  svg.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;z-index:1;';
  let lineCount = 0;

  function rel(el) {
    const r = el.getBoundingClientRect();
    return {
      cx: r.left - cRect.left + r.width/2,
      cy: r.top - cRect.top + r.height/2,
      left: r.left - cRect.left,
      right: r.right - cRect.left,
    };
  }

  function drawLine(x1, y1, x2, y2, color, width) {
    const l = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    // Round to nearest pixel to prevent sub-pixel misalignment (visual kinks)
    l.setAttribute('x1', Math.round(x1)); l.setAttribute('y1', Math.round(y1));
    l.setAttribute('x2', Math.round(x2)); l.setAttribute('y2', Math.round(y2));
    l.setAttribute('stroke', color); l.setAttribute('stroke-width', width);
    l.setAttribute('stroke-linecap', 'round');
    svg.appendChild(l);
    lineCount++;
  }

  // ─── Unified gray connectors (decreasing by depth, visually clean) ───
  const lineStyles = [
    { color: '#64748B', width: 2.5 },  // root → L1
    { color: '#94A3B8', width: 2 },    // L1 → L2
    { color: '#A8B4C2', width: 1.5 },  // L2 → L3
    { color: '#B8C2CC', width: 1.2 },  // L3 → L4
    { color: '#CBD5E1', width: 1 },    // L4 → L5
  ];
  function getLineStyle(branchColor, depth) {
    const s = lineStyles[Math.min(depth, lineStyles.length - 1)];
    return { color: s.color, width: s.width };
  }

  // ─── Connector direction ───
  // dir='left': parent.left → midX → child.right (each child gets its own polyline)
  // dir='right': parent.right → midX → child.left
  //
  // [Principle] midX is the X coordinate of the vertical line; it must be in the gap between parent and children.
  // Use a fraction of the parent-to-nearest-child distance as offset, so:
  //   - Large node spacing → large offset, lines spread out
  //   - Small node spacing → small offset, lines compact without crossing text
  // All children in the same connect() call share one midX, ensuring vertical line alignment.
  function connect(parentEl, childEls, color, width, dir) {
    if (!childEls.length) return;
    const p = rel(parentEl);
    const startX = dir === 'left' ? p.left : p.right;
    const startY = p.cy;

    // Special case: single child — draw one straight horizontal line, no vertical spine
    if (childEls.length === 1) {
      const c = rel(childEls[0]);
      const endX = dir === 'left' ? c.right : c.left;
      const midY = Math.round((startY + c.cy) / 2);
      drawLine(startX, midY, endX, midY, color, width);
      return;
    }

    // Find the closest child edge to calculate available space
    let closestEdge;
    if (dir === 'left') {
      closestEdge = Math.max(...childEls.map(ch => rel(ch).right));
    } else {
      closestEdge = Math.min(...childEls.map(ch => rel(ch).left));
    }
    // Place midX at the midpoint between parent edge and closest child edge,
    // but guarantee at least 16px clearance from child nodes
    const childClearance = 16;
    const midpoint = startX + (closestEdge - startX) / 2;
    const midFromChild = dir === 'left' ? closestEdge + childClearance : closestEdge - childClearance;
    // Use the position that's further from children (safer)
    const midX = dir === 'left'
      ? Math.min(midpoint, midFromChild)
      : Math.max(midpoint, midFromChild);

    drawLine(startX, startY, midX, startY, color, width);

    // Draw ONE continuous vertical line spanning from parent to the last child
    const allCYs = childEls.map(ch => rel(ch).cy);
    const minY = Math.min(startY, ...allCYs);
    const maxY = Math.max(startY, ...allCYs);
    drawLine(midX, minY, midX, maxY, color, width);

    // Then draw horizontal lines from the vertical spine to each child
    childEls.forEach(ch => {
      const c = rel(ch);
      const endX = dir === 'left' ? c.right : c.left;
      const endY = c.cy;
      drawLine(midX, endY, endX, endY, color, width);
    });
  }

  // ─── Recursively process subtree (supports .children + .leaf-group + .deep-group) ───
  const NODE_SEL = '.branch-node, .sub-node, .leaf, .deep-node';
  const CONTAINER_SEL = ':scope > .children, :scope > .leaf-group, :scope > .deep-group';

  function processChildren(parentNodeEl, containerEl, branchColor, depth, dir) {
    if (!containerEl) return;
    const childNodeEls = [];
    for (const wrapper of containerEl.children) {
      const nodeEl = wrapper.matches?.(NODE_SEL) ? wrapper : wrapper.querySelector(NODE_SEL);
      if (nodeEl) childNodeEls.push(nodeEl);
    }
    if (!childNodeEls.length) return;
    const style = getLineStyle(branchColor, depth);
    connect(parentNodeEl, childNodeEls, style.color, style.width, dir);

    for (const wrapper of containerEl.children) {
      const nodeEl = wrapper.matches?.(NODE_SEL) ? wrapper : wrapper.querySelector(NODE_SEL);
      if (!nodeEl) continue;
      wrapper.querySelectorAll(CONTAINER_SEL).forEach(nc =>
        processChildren(nodeEl, nc, branchColor, depth + 1, dir)
      );
    }
  }

  // ─── Main flow ───
  const rootNode = map.querySelector('.root-node');
  if (!rootNode) { console.error('❌ .root-node not found'); return; }
  const rp = rel(rootNode);

  // Left side: collect all L1 branch-nodes, draw polylines with connect() (with vertical spine)
  const leftSel = '.left-side > .branch, .left-branches > .left-branch, .left-branches > div';
  const leftBranches = map.querySelectorAll(leftSel);
  const leftBranchNodes = [];
  leftBranches.forEach(branch => {
    const bNode = branch.querySelector('.branch-node');
    if (bNode) leftBranchNodes.push(bNode);
  });
  if (leftBranchNodes.length) {
    connect(rootNode, leftBranchNodes, lineStyles[0].color, lineStyles[0].width, 'left');
  }
  leftBranches.forEach(branch => {
    const bNode = branch.querySelector('.branch-node');
    if (!bNode) return;
    processChildren(bNode, branch.querySelector(':scope > .children'), null, 1, 'left');
  });

  // Right side: same as above
  const rightSel = '.right-side > .branch, .branches > .branch, .right-branches > .right-branch';
  const rightBranches = map.querySelectorAll(rightSel);
  const rightBranchNodes = [];
  rightBranches.forEach(branch => {
    const bNode = branch.querySelector('.branch-node');
    if (bNode) rightBranchNodes.push(bNode);
  });
  if (rightBranchNodes.length) {
    connect(rootNode, rightBranchNodes, lineStyles[0].color, lineStyles[0].width, 'right');
  }
  rightBranches.forEach(branch => {
    const bNode = branch.querySelector('.branch-node');
    if (!bNode) return;
    processChildren(bNode, branch.querySelector(':scope > .children'), null, 1, 'right');
  });

  map.insertBefore(svg, map.firstChild);
  console.log(`✅ Drew ${lineCount} lines`);
}
```

**How to call (at end of HTML):**
```html
<script>
  /* ← paste the drawAllLines function above */
  window.addEventListener('load', () => setTimeout(drawAllLines, 300));
</script>
```

### 3.3 Universal CSS Base (Shared by All Styles)

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #FFFFFF;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'SimHei', sans-serif;
}
#mindmap { padding: 60px; display: inline-block; min-width: 100%; position: relative; }
#mindmap > svg.lines {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 0;
}

/* ─── Root Node ─── */
/* ─── Topic Intent Color System ─── */
/* Model picks ONE intent based on content semantics. Add data-intent="xxx" to #mindmap.
   DO NOT manually write hex colors for root node — use intent system only. */

/* Intent → Root Node + Branch Palette mapping */
#mindmap[data-intent="professional"] .root-node { background: linear-gradient(135deg, #1E3A5F, #2D4A6F); box-shadow: 0 4px 12px rgba(30,58,95,0.25); }
#mindmap[data-intent="technical"]    .root-node { background: linear-gradient(135deg, #334155, #475569); box-shadow: 0 4px 12px rgba(51,65,85,0.25); }
#mindmap[data-intent="medical"]      .root-node { background: linear-gradient(135deg, #0F766E, #0D9488); box-shadow: 0 4px 12px rgba(15,118,110,0.25); }
#mindmap[data-intent="education"]    .root-node { background: linear-gradient(135deg, #9A3412, #B45309); box-shadow: 0 4px 12px rgba(154,52,18,0.25); }
#mindmap[data-intent="creative"]     .root-node { background: linear-gradient(135deg, #7C3AED, #8B5CF6); box-shadow: 0 4px 12px rgba(124,58,237,0.25); }
#mindmap[data-intent="finance"]      .root-node { background: linear-gradient(135deg, #1E3A5F, #1E40AF); box-shadow: 0 4px 12px rgba(30,58,95,0.25); }
#mindmap[data-intent="nature"]       .root-node { background: linear-gradient(135deg, #166534, #15803D); box-shadow: 0 4px 12px rgba(22,101,52,0.25); }
#mindmap[data-intent="warning"]      .root-node { background: linear-gradient(135deg, #991B1B, #B91C1C); box-shadow: 0 4px 12px rgba(153,27,27,0.25); }
#mindmap[data-intent="neutral"]      .root-node { background: linear-gradient(135deg, #334155, #475569); box-shadow: 0 4px 12px rgba(51,65,85,0.25); }

/*
Intent Selection Guide (for model):
  professional → corporate reports, strategy, management, business plans
  technical    → software, engineering, architecture, systems, AI/ML
  medical      → healthcare, clinical, pharmaceutical, nursing, anatomy
  education    → teaching, learning, curriculum, training, academic
  creative     → design, art, marketing, branding, media
  finance      → banking, investment, accounting, economics, trading
  nature       → environment, ecology, agriculture, biology, geography
  warning      → risk analysis, safety, incident review, compliance, audit
  neutral      → general topics, mixed content, unclear domain

Recommended branch color combos per intent:
  professional → [blue, teal, cyan]
  technical    → [blue, purple, cyan]
  medical      → [teal, green, blue]
  education    → [amber, green, blue]
  creative     → [purple, amber, cyan]
  finance      → [blue, green, cyan]
  nature       → [green, teal, amber]
  warning      → [red, amber, cyan]
  neutral      → [blue, green, purple]
*/

.root-node {
  color: white; font-size: 20px; font-weight: 700;
  padding: 18px 28px; border-radius: 12px;
  white-space: nowrap; flex-shrink: 0; align-self: center;
}
/* Fallback if no intent specified — defaults to professional blue */
#mindmap:not([data-intent]) .root-node {
  background: linear-gradient(135deg, #1E3A5F, #2D4A6F);
  box-shadow: 0 4px 12px rgba(30,58,95,0.25);
}

/* ─── Container Layout ─── */
.tree { display: flex; align-items: flex-start; gap: 0; position: relative; }
.branches { display: flex; flex-direction: column; gap: 16px; margin-left: 60px; }
.branch, .sub-branch { display: flex; align-items: flex-start; gap: 0; }

/* ─── First-Level Branch Node ─── */
.branch-node {
  font-size: 15px; font-weight: 600;
  padding: 10px 20px; border-radius: 8px;
  white-space: nowrap; flex-shrink: 0; border: 2px solid;
}
/* ─── Second-Level Sub-Node (when has children) ─── */
.sub-node {
  font-size: 13px; font-weight: 500;
  padding: 7px 14px; border-radius: 6px;
  white-space: nowrap; flex-shrink: 0; border: 1.5px solid;
  background: #F8FAFC;
}
/* ─── Leaf Node ─── */
/* Default: lightweight capsule frame */
.leaf {
  font-size: 13px; font-weight: 400; color: #475569;
  padding: 4px 10px; background: #FAFAFA;
  border-radius: 12px; border: 1px solid #E5E7EB;
  white-space: nowrap; line-height: 1.5;
}
/* Text-only mode (more compact, add class="leaf text-only") */
.leaf.text-only {
  background: none; border: none; padding: 2px 0; border-radius: 0;
}
/* Leaf supplementary description */
.leaf-desc {
  font-size: 12px; color: #94A3B8; font-weight: 400; margin-left: 8px;
}
.leaf-desc::before { content: '— '; color: #CBD5E1; }

/* ─── Child Node Container ─── */
/* Principle: The deeper the level, the smaller the gap, but not so small that connectors and text overlap */
.children { display: flex; flex-direction: column; gap: 6px; margin-left: 48px; align-items: flex-start; }
.children:has(.sub-branch) { gap: 10px; }  /* sub-branch is larger than leaf, needs more spacing */
.sub-branch .children { gap: 5px; margin-left: 40px; align-items: flex-start; }
.sub-branch .sub-branch .children { gap: 4px; margin-left: 36px; align-items: flex-start; }
/* Tip: If leaf text and connectors overlap, prioritize increasing gap */

/* ─── Color System (for distinguishing different branches) ─── */
.c-blue { background: #EFF6FF; border-color: #3B82F6; color: #1E40AF; }
.c-green { background: #F0FDF4; border-color: #10B981; color: #065F46; }
.c-amber { background: #FFF7ED; border-color: #F59E0B; color: #92400E; }
.c-purple { background: #F5F3FF; border-color: #8B5CF6; color: #5B21B6; }
.c-red { background: #FEF2F2; border-color: #EF4444; color: #991B1B; }
.c-cyan { background: #ECFEFF; border-color: #06B6D4; color: #155E75; }
.c-teal { background: #F0FDFA; border-color: #14B8A6; color: #134E4A; }

/* Second-level sub-node inherits branch color scheme (lighter) */
.c-blue .sub-node { background: #F0F7FF; border-color: #93C5FD; color: #1E40AF; }
.c-green .sub-node { background: #F2FDF6; border-color: #6EE7B7; color: #065F46; }
.c-amber .sub-node { background: #FFF9F0; border-color: #FCD34D; color: #92400E; }
.c-purple .sub-node { background: #F8F6FF; border-color: #C4B5FD; color: #5B21B6; }
.c-red .sub-node { background: #FFF5F5; border-color: #FCA5A5; color: #991B1B; }
.c-cyan .sub-node { background: #F0FEFF; border-color: #67E8F9; color: #155E75; }
.c-teal .sub-node { background: #F2FDFA; border-color: #5EEAD4; color: #134E4A; }
```

---

## Style A: Right-Expanding Tree (Simple scenarios with branchCount ≤ 4 or maxDepth ≤ 2)

### HTML Structure

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
  /* ← paste the "Universal CSS Base" above */
</style>
</head>
<body>
<div id="mindmap" data-intent="professional">
  <div class="tree">
    <div class="root-node">中心主题</div>
    <div class="branches">

      <div class="branch">
        <div class="branch-node c-blue">一级分支A</div>
        <div class="children">
          <div class="leaf">叶子1</div>
          <div class="leaf">叶子2</div>
        </div>
      </div>

      <div class="branch">
        <div class="branch-node c-green">一级分支B</div>
        <div class="children">
          <div class="sub-branch">
            <div class="sub-node c-green">二级有下级</div>
            <div class="children">
              <div class="leaf">三级叶子1</div>
              <div class="leaf">三级叶子2</div>
            </div>
          </div>
          <div class="leaf">二级叶子</div>
        </div>
      </div>

    </div>
  </div>
</div>
<script>
  /* ← paste the "Universal Recursive Connector Script" */
  drawAllLines();
</script>
</body>
</html>
```

---

## Style B: Left-Right Expanding Tree (Standard scenario with branchCount ≥ 5, most common)

### Additional CSS (append after universal base)

```css
/* ─── Left-Right Expanding Layout ─── */
.lr-tree { display: flex; align-items: center; gap: 0; position: relative; }
.lr-tree .root-node {
  padding: 20px 32px; border-radius: 14px;
  margin: 0 60px; text-align: center;
}

/* ⚠️ sub-branch must be flex, otherwise flex-direction: row-reverse won't work, leaves won't expand left */
.sub-branch { display: flex; align-items: flex-start; gap: 0; }

.left-branches { display: flex; flex-direction: column; gap: 16px; }
.left-branch { display: flex; align-items: flex-start; flex-direction: row-reverse; gap: 0; }
.left-branch .children {
  display: flex; flex-direction: column; gap: 6px;
  margin-right: 48px; align-items: flex-end;
}
.left-branch .children:has(.sub-branch) { gap: 10px; }
.left-branch .sub-branch .children { gap: 5px; margin-right: 40px; margin-left: 0; align-items: flex-end; }
.left-branch .sub-branch { flex-direction: row-reverse; }

.right-branches { display: flex; flex-direction: column; gap: 16px; }
.right-branch { display: flex; align-items: flex-start; gap: 0; }
.right-branch .children {
  display: flex; flex-direction: column; gap: 6px; margin-left: 48px; align-items: flex-start;
}
.right-branch .children:has(.sub-branch) { gap: 10px; }
.right-branch .sub-branch .children { gap: 5px; margin-left: 40px; align-items: flex-start; }
```

### HTML Structure

```html
<div id="mindmap" data-intent="professional">
  <div class="lr-tree">

    <!-- Left branches (allocated by balance_branches) -->
    <div class="left-branches">
      <div class="left-branch">
        <div class="branch-node c-purple">分支D（放左边）</div>
        <div class="children">
          <div class="leaf">叶子1</div>
          <div class="leaf">叶子2</div>
        </div>
      </div>
      <!-- More left branches... -->
    </div>

    <div class="root-node">中心主题</div>

    <!-- Right branches -->
    <div class="right-branches">
      <div class="right-branch">
        <div class="branch-node c-blue">分支A（放右边）</div>
        <div class="children">
          <div class="leaf">叶子1</div>
          <div class="leaf">叶子2</div>
        </div>
      </div>
      <!-- More right branches... -->
    </div>

  </div>
</div>
<script>
  /* ← paste the "Universal Recursive Connector Script" */
  drawAllLines();  // v4: auto-handles both left and right sides
</script>
```

---

## Style C: Card Grid (when user explicitly requests "cards" / "modules")

> ⚠️ This is not a mind map — it's a modular display. No connectors; use cards + color coding to show relationships.

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'SimHei', sans-serif;
  }
  #mindmap { padding: 48px 64px; }
  .map-title {
    font-size: 24px; font-weight: 700; color: #1E293B; text-align: center;
    margin-bottom: 8px;
  }
  .map-subtitle {
    font-size: 14px; color: #64748B; text-align: center;
    margin-bottom: 36px;
  }
  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px; max-width: 1000px; margin: 0 auto;
  }
  .card {
    background: #FFFFFF; border-radius: 12px;
    padding: 20px; border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 2px solid; }
  .card-title { font-size: 15px; font-weight: 600; }
  .card-icon {
    width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
    font-size: 16px; border-radius: 50%; flex-shrink: 0;
  }
  .card-items { list-style: none; display: flex; flex-direction: column; gap: 6px; }
  .card-items li {
    font-size: 13px; color: #475569; padding-left: 16px; position: relative;
  }
  .card-items li::before {
    content: ''; position: absolute; left: 0; top: 8px;
    width: 6px; height: 6px; border-radius: 50%;
  }

  /* Color variants */
  .card.blue .card-header { border-color: #3B82F6; }
  .card.blue .card-icon { background: #EFF6FF; }
  .card.blue .card-title { color: #1E40AF; }
  .card.blue li::before { background: #3B82F6; }

  .card.green .card-header { border-color: #10B981; }
  .card.green .card-icon { background: #F0FDF4; }
  .card.green .card-title { color: #065F46; }
  .card.green li::before { background: #10B981; }

  .card.amber .card-header { border-color: #F59E0B; }
  .card.amber .card-icon { background: #FFF7ED; }
  .card.amber .card-title { color: #92400E; }
  .card.amber li::before { background: #F59E0B; }

  .card.purple .card-header { border-color: #8B5CF6; }
  .card.purple .card-icon { background: #F5F3FF; }
  .card.purple .card-title { color: #5B21B6; }
  .card.purple li::before { background: #8B5CF6; }
</style>
</head>
<body>
<div id="mindmap" data-intent="professional">
  <div class="map-title">标题</div>
  <div class="map-subtitle">副标题</div>
  <div class="card-grid">
    <div class="card blue">
      <div class="card-header">
        <div class="card-icon">📋</div>
        <div class="card-title">模块A</div>
      </div>
      <ul class="card-items">
        <li>条目1</li>
        <li>条目2</li>
      </ul>
    </div>
    <!-- More cards... -->
  </div>
</div>
</body>
</html>
```

---

## Style D: Fishbone Diagram (Problem Analysis / Root Cause)

Best for problem analysis, root cause tracing, quality management (Ishikawa diagram).

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'SimHei', sans-serif;
  }
  #mindmap { padding: 48px 64px; }
  .fishbone { position: relative; }
  .spine { display: flex; align-items: center; gap: 0; }
  .spine-line { flex: 1; height: 3px; background: #1E293B; }
  .spine-head {
    width: 0; height: 0;
    border-left: 16px solid #1E293B;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
  }
  .result-node {
    background: #1E293B; color: white;
    font-size: 16px; font-weight: 700;
    padding: 12px 24px; border-radius: 8px;
    white-space: nowrap; margin-left: 4px;
  }
  .bone-branches {
    position: absolute; left: 80px; right: 200px; top: 50%;
    display: flex; justify-content: space-around;
  }
  .bone { display: flex; flex-direction: column; align-items: center; gap: 8px; }
  .bone.up { transform: translateY(calc(-100% - 20px)); }
  .bone.down { transform: translateY(20px); }
  .bone-title {
    font-size: 14px; font-weight: 600;
    padding: 8px 16px; border-radius: 8px; white-space: nowrap;
  }
  .bone-items { display: flex; flex-direction: column; gap: 4px; align-items: center; }
  .bone-item {
    font-size: 12px; color: #64748B;
    padding: 3px 10px; background: #F8FAFC;
    border-radius: 4px; border: 1px solid #E2E8F0; white-space: nowrap;
  }
  .bone-line { width: 2px; height: 24px; background: #CBD5E1; }
</style>
</head>
<body>
<div id="mindmap" data-intent="professional">
  <div class="fishbone">
    <div class="spine">
      <div class="spine-line"></div>
      <div class="spine-head"></div>
      <div class="result-node">问题/结果</div>
    </div>
    <!-- Upper causes -->
    <div class="bone-branches" style="transform: translateY(calc(-50% - 20px));">
      <div class="bone">
        <div class="bone-items">
          <div class="bone-item">子原因1</div>
          <div class="bone-item">子原因2</div>
        </div>
        <div class="bone-line"></div>
        <div class="bone-title" style="background:#EFF6FF;color:#1E40AF;border:1.5px solid #3B82F6;">原因类别A</div>
      </div>
    </div>
    <!-- Lower causes -->
    <div class="bone-branches" style="transform: translateY(calc(-50% + 20px));">
      <div class="bone">
        <div class="bone-title" style="background:#F0FDF4;color:#065F46;border:1.5px solid #10B981;">原因类别B</div>
        <div class="bone-line"></div>
        <div class="bone-items">
          <div class="bone-item">子原因1</div>
          <div class="bone-item">子原因2</div>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
```

---

## Quality Checklist

After rendering, verify against this checklist:

1. **Content complete** — Every node from the original requirement is in the map, nothing missing
2. **Clear hierarchy** — L1 branches and leaves are instantly distinguishable (different bg/border/font-weight)
3. **No overlap** — No boxes covering boxes, no lines through text
4. **Connectors visible** — Every parent-child pair has a connector, no orphan leaves. Connector color ≥ `#94A3B8` (too light = invisible)
5. **Connector direction correct** — Left-side leaves extend left, right-side extends right
6. **Proportions reasonable** — Map is not extremely narrow/tall (target aspect ratio 1:1 to 3:1), visually comfortable
7. **Text readable** — At final output size, smallest text is legible. Reference: root 18px+, L1 15px+, L2 13px+, leaves 12px+
8. **Roughly balanced** (Style B) — Visual weight approximately equal on both sides, doesn't need to be symmetric. Target ≤30% difference
9. **Canvas large enough** — No nodes clipped, sufficient padding on all sides (reference 60px+)
10. **No large blank areas on right** — Screenshot trimmed to content edge

---

## ⛔ Radial Layout Warning

**Radial layout is strongly discouraged.** Using `position: absolute` for fixed branch positions leads to overlap when branches increase, and deep levels cannot be handled.

If content is very simple (reference: ≤3 branches, ≤3 children per branch, text ≤6 chars, depth ≤2, total ≤12 nodes), it's technically possible, but tree layout is always the safer choice.

**No code template provided.** If conditions are met, manually adjust based on Style A.
