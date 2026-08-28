# Playwright + CSS Rendering Engine

> **⚠️ Before writing any code, read [`_rules.md`](references/_rules.md) — three non-negotiable rules on overlap, hierarchy, and color.**

**Core principle: Content-driven, not template-driven. Analyze content structure first, then decide layout, then render.**

Applicable to: flowcharts, infographics, KPI cards, data posters — any visualization requiring full CSS power (gradients, shadows, rounded corners, Grid/Flexbox layout).

---

## Step 1: Content Analysis

When you receive a flowchart/infographic requirement, **don't write HTML/CSS first**. Analyze the content structure.

### 1.1 Flowchart Content Analysis

```
Input: "Honey production process", 8 steps, linear without branches
    ↓
{
  "type": "flowchart",
  "nodes": [
    { "id": "1", "label": "花粉采集", "desc": "蜜蜂从花朵采集花蜜" },
    { "id": "2", "label": "酿造", "desc": "蜜蜂在蜂巢中反复吞吐" },
    ...
  ],
  "edges": [["1","2"], ["2","3"], ...],
  "nodeTypes": { "start": ["1"], "end": ["8"], "decision": [], "normal": ["2","3","4","5","6","7"] }
}
```

### 1.2 Key Metrics

| Metric | Calculation | Affects |
|------|---------|---------|
| `nodeCount` | Total node count | Mermaid vs CSS flowchart |
| `maxTextLen` | Longest text char count | Node width |
| `hasDecision` | Has decision branches | Layout complexity |
| `hasBranch` | Has parallel/branches | Column count |
| `parallelCount` | Max parallel branches | Column count |
| `phaseCount` | Phase/group count | Need for phased containers |
| `hasRoles` | Has roles/swimlanes | Need for dual-panel |
| `isLinear` | Linear without branches | Can use snake layout |

### 1.3 Infographic Content Analysis

Infographics (KPI cards, data posters) are simpler to analyze:
- How many data metrics? → Determines grid columns
- Any trend data? → Need for sparklines
- Title area? → Need for hero header
- Comparison data? → Need for bar chart

---

## Step 2: Layout Decision

### 2.1 Flowchart Layout Decision Tree

```
⚠️ DEFAULT RULE: When user asks "generate/create XXX 流程图" without specifying format,
   DEFAULT to Layout C (Phased Vertical). Almost all real-world processes have phases.

User specified Mermaid/markdown?
  └─ Yes → Follow user choice (Format Constraint Rule)
  └─ No →
      nodeCount ≤ 6 AND no phases AND maxTextLen ≤ 8 (CJK)?
        └─ Yes → Mermaid (minimal flowchart)
        └─ No →
            phaseCount > 0 OR nodeCount ≥ 5?
              └─ Yes → ⭐ Layout C: CSS Phased Vertical flowchart (DEFAULT)
              └─ No →
                  hasRoles?
                    └─ Yes → Layout D: CSS Dual-panel/Swimlane flowchart
                    └─ No → Layout C: CSS Phased Vertical flowchart (fallback also uses C)
```

**⚠️ Layout A (Grid) and Layout B (Snake) are only for very special scenarios (e.g., flat comparison, unordered parallel items). Flowcharts default to Layout C.**

### 🚫 Flowchart Anti-Patterns (FORBIDDEN)

| ❌ Bad Pattern | ✅ Correct Pattern |
|---|---|
| Phase titles (一、二、三...) as isolated left-side text labels | Phase titles as colored title bars, wrapped inside group cards |
| All nodes flat-laid in Grid without group containers | Each phase wrapped in a `.phase-group` card containing its steps |
| Role labels scattered above nodes | Role info displayed uniformly at the top of the flowchart, or as phase card labels |
| Nodes connected with loose diverging lines | Phases connected with arrows (↓), steps within phases use numbering |
| Inconsistent node sizes, uneven spacing, misaligned | Same-phase nodes share uniform style, overall alignment consistent |
| Using Layout A Grid for a phased flowchart | Has phases → must use Layout C |

### 2.2 Canvas Size Calculation

```python
def calc_flowchart_canvas(node_count, max_text_len, parallel_count, has_roles, layout):
    node_width = max(180, max_text_len * 16)  # ~16px per CJK char (including padding)
    
    if layout == 'snake':
        cols = min(4, node_count)
        rows = (node_count + cols - 1) // cols
        width = cols * (node_width + 60) + 120   # 60=gap, 120=padding
        height = rows * 120 + 200                 # 120=row height
    elif layout == 'dual-panel':
        width = max(1600, node_width * 2 + 400)   # left panel + right flow
        height = node_count * 100 + 200
    elif layout == 'phased-vertical':
        width = max(800, node_width + 200)
        height = node_count * 80 + 200
    else:  # grid
        cols = max(parallel_count, 2)
        width = cols * (node_width + 60) + 120
        rows = (node_count + cols - 1) // cols
        height = rows * 120 + 200
    
    return max(width, 800), max(height, 600)
```

### 2.3 Color Decision

**Iron rule: Node background = low-saturation light color, border = high-saturation color. Large high-saturation areas = children's drawing.**

**⚠️ Text contrast iron rule: Dark/accent background nodes must use light text (white or near-white) for title and description.**
Light background → dark text (`#1F2937`), dark background → light text (`#FFFFFF` or `#FFF7ED`).
Common mistake: Endpoint/highlight node switched to dark background, but description text remains dark gray, making it completely unreadable.

```
Node type → color:
  Start/end  → bg: #EFF6FF, border: #3B82F6 (blue), text: #1E40AF
  Normal step  → bg: #F8FAFC, border: #94A3B8 (gray-blue), text: #374151  or colored by phase
  Decision node  → bg: #FFF7ED, border: #F59E0B (amber), text: #92400E
  Success/pass → bg: #F0FDF4, border: #10B981 (green), text: #065F46
  End/failure → bg: #F5F3FF, border: #8B5CF6 (purple), text: #5B21B6
  Emphasis/endpoint (dark bg) → bg: #92400E, border: #F59E0B, text: #FFFFFF, desc: #FFF7ED

Max 3-4 background colors for nodes in the same flowchart.
Overall chart background = white #FFFFFF.
```

**Phase bar colors**: Same-hue gradient (blue-gray family), **never use different hues per phase**.

```css
/* ✅ Same-hue blue-gray progression */
.phase-1 { background: #F0F4F8; border-left: 4px solid #64748B; }
.phase-2 { background: #E8EDF2; border-left: 4px solid #5B7A99; }

/* ❌ Different hue per phase (rainbow effect) */
.phase-1 { background: #EFF6FF; border-left: 4px solid #3B82F6; }  /* blue */
.phase-2 { background: #F0FDF4; border-left: 4px solid #10B981; }  /* green */
.phase-3 { background: #FFF7ED; border-left: 4px solid #F59E0B; }  /* amber */
```

---

## Step 3: Rendering

### 3.1 Playwright Screenshot (Universal)

```python
import asyncio
from playwright.async_api import async_playwright

async def html_to_image(html_path, output_path, selector='#root',
                        width=1200, height=None, scale=2):
    """HTML → PNG/PDF
    
    scale: 2 (default crisp), 1.5 (large canvas 3000px+), 3 (print).
    Width must accommodate ALL content. After first render, auto-resize viewport to fit.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={'width': width, 'height': height or 800},
            device_scale_factor=scale
        )
        await page.goto(f'file://{html_path}', wait_until='networkidle')
        await page.wait_for_timeout(500)
        
        if output_path.endswith('.pdf'):
            await page.pdf(path=output_path, print_background=True)
        else:
            el = page.locator(selector)
            bbox = await el.bounding_box()
            if bbox:
                fit_w = max(width, int(bbox['width'] + 100))
                fit_h = int(bbox['height'] + 100)
                await page.set_viewport_size({'width': fit_w, 'height': fit_h})
                await page.wait_for_timeout(200)
            await el.screenshot(path=output_path)
        
        await browser.close()
        import os
        print(f'✅ {output_path} ({os.path.getsize(output_path)/1024:.0f}KB)')
```

### 3.2 HTML Universal Shell

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  :root {
    --text: #111827;
    --text-sub: #6B7280;
    --text-muted: #9CA3AF;
    --bg: #FFFFFF;
    --surface: #F9FAFB;
    --border: #E5E7EB;
    --blue: #3B82F6;
    --cyan: #06B6D4;
    --purple: #8B5CF6;
    --amber: #F59E0B;
    --red: #EF4444;
    --green: #10B981;
    --positive: #22C55E;
    --negative: #EF4444;
    --connector: #94A3B8;
  }
  
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'SimHei', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
  }
  
  #root { width: fit-content; min-width: 800px; margin: 0 auto; padding: 48px 40px; }
</style>
</head>
<body>
<div id="root">
  <!-- Content -->
</div>
</body>
</html>
```

### 3.3 CSS Variables: Node Color System

```css
:root {
  /* Node types — low-saturation background + high-saturation border */
  --node-bg: #EFF6FF;       --node-border: #3B82F6;         /* Normal step (blue) */
  --node-decision-bg: #FFF7ED; --node-decision-border: #F59E0B; /* Decision (amber) */
  --node-success-bg: #F0FDF4;  --node-success-border: #10B981;  /* Success (green) */
  --node-end-bg: #F5F3FF;     --node-end-border: #8B5CF6;      /* End (purple) */
  --group-bg: #F8FAFC;        --group-border: #E2E8F0;         /* Group container */
}
```

---

## Layout A: CSS Grid Flowchart (Universal, Most Common)

For: Flowcharts with branches/decisions, >10 nodes or long CJK text.

### Core CSS

```css
.flow-title {
  font-size: 22px; font-weight: 700; color: var(--text);
  text-align: center; margin-bottom: 40px;
}
.flow-subtitle {
  font-size: 14px; color: var(--text-sub);
  text-align: center; margin-top: 8px;
}

/* Grid container */
.flow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 220px));
  gap: 40px 60px;
  justify-content: center;
  position: relative;
}

/* Node */
.flow-node {
  background: var(--node-bg); border: 2px solid var(--node-border);
  border-radius: 10px; padding: 16px 20px;
  text-align: center; position: relative; z-index: 1;
  min-height: 56px; display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  max-width: 260px;            /* Prevent single node from being too wide and crowding parallel nodes */
  word-break: break-word;       /* Force line break for overly long text */
  white-space: normal;          /* Allow line breaks (override possible nowrap) */
}
.flow-node .node-title { font-size: 15px; font-weight: 600; line-height: 1.4; }
.flow-node .node-desc { font-size: 12px; color: var(--text-sub); margin-top: 4px; }

/* Node variants */
.flow-node.start { border-radius: 24px; }
.flow-node.decision { background: var(--node-decision-bg); border-color: var(--node-decision-border); }
.flow-node.success { background: var(--node-success-bg); border-color: var(--node-success-border); }
.flow-node.end { background: var(--node-end-bg); border-color: var(--node-end-border); }

/* Group box */
.flow-group {
  background: var(--group-bg); border: 1.5px dashed var(--group-border);
  border-radius: 12px; padding: 24px 20px 20px; position: relative;
}
.flow-group .group-label {
  position: absolute; top: -10px; left: 16px;
  background: var(--bg); padding: 0 8px;
  font-size: 12px; font-weight: 600; color: var(--text-sub);
}

/* ─── Parallel branch constraints (prevent overlap when multiple nodes in same row) ─── */
/* 
  ⚠️ Parallel branch iron rules:
  1. Gap between parallel nodes in same row ≥ 40px (guaranteed by .flow-grid gap)
  2. Each node max-width: 260px + word-break: break-word (set in .flow-node)
  3. If parallel nodes > 3 → switch to vertical branch layout (don't force-squeeze into one row)
  4. Text over 15 CJK characters → must line-break, don't expand node width
  5. When using flex instead of manual grid-column for parallel areas, add flex-wrap: wrap as fallback
*/
.parallel-group {
  display: flex; gap: 40px; justify-content: center;
  flex-wrap: wrap;  /* Fallback: auto-wrap when exceeding width */
}
.parallel-group .flow-node {
  flex: 0 1 220px;  /* Max 220px, can shrink, won't grow infinitely */
}

/* SVG connector layer */
.flow-connectors {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 0;
}
.flow-connectors line, .flow-connectors path {
  stroke: var(--connector); stroke-width: 2; fill: none;
  marker-end: url(#arrowhead);
}
.connector-label {
  font-size: 12px; fill: var(--text-sub); text-anchor: middle;
  font-family: -apple-system, 'PingFang SC', 'SimHei', sans-serif;
}

/* Legend — must be independent container, not inside flow-grid */
.flow-legend {
  display: flex; gap: 24px; justify-content: center;
  margin-top: 40px; padding: 16px 24px;
  background: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB;
}
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #4B5563; }
.legend-dot { width: 12px; height: 12px; border-radius: 3px; border: 2px solid; }
```

### Auto Connector Script

```javascript
// connections = [['sourceID', 'targetID', 'label'], ...]
function drawConnectors(connections) {
  const svg = document.getElementById('connectorSvg');
  const container = svg.parentElement;
  const cRect = container.getBoundingClientRect();
  
  svg.setAttribute('width', cRect.width);
  svg.setAttribute('height', cRect.height);
  svg.setAttribute('viewBox', `0 0 ${cRect.width} ${cRect.height}`);
  
  // Clear old connectors (keep defs)
  svg.querySelectorAll('line, path, text.connector-label').forEach(el => el.remove());
  
  connections.forEach(([fromId, toId, label]) => {
    const fromEl = document.querySelector(`[data-id="${fromId}"]`);
    const toEl = document.querySelector(`[data-id="${toId}"]`);
    if (!fromEl || !toEl) return;
    
    const f = fromEl.getBoundingClientRect();
    const t = toEl.getBoundingClientRect();
    const x1 = f.left + f.width/2 - cRect.left;
    const y1 = f.bottom - cRect.top;
    const x2 = t.left + t.width/2 - cRect.left;
    const y2 = t.top - cRect.top;
    
    if (Math.abs(x1 - x2) < 10) {
      // Same column → straight line
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      svg.appendChild(line);
    } else {
      // Different column → bent line
      const midY = (y1 + y2) / 2;
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`);
      svg.appendChild(path);
    }
    
    if (label) {
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', (x1 + x2) / 2);
      text.setAttribute('y', (y1 + y2) / 2 - 6);
      text.setAttribute('class', 'connector-label');
      text.textContent = label;
      svg.appendChild(text);
    }
  });
}

// SVG defs (arrow definitions)
function ensureArrowDef(svg) {
  if (svg.querySelector('#arrowhead')) return;
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#94A3B8" /></marker>';
  svg.appendChild(defs);
}
```

### HTML Structure Example

```html
<div id="root">
  <div class="flow-title">流程图标题</div>
  
  <div style="position: relative;">
    <svg class="flow-connectors" id="connectorSvg"></svg>
    <div class="flow-grid" id="flowGrid">
      <div class="flow-node start" data-id="start" style="grid-column: 2;">
        <div class="node-title">开始</div>
      </div>
      <div class="flow-node" data-id="step1" style="grid-column: 1;">
        <div class="node-title">步骤一</div>
        <div class="node-desc">详细说明</div>
      </div>
      <div class="flow-node decision" data-id="decide" style="grid-column: 2;">
        <div class="node-title">判断条件？</div>
      </div>
      <div class="flow-node end" data-id="end" style="grid-column: 2;">
        <div class="node-title">结束</div>
      </div>
    </div>
  </div>
  
  <div class="flow-legend">
    <div class="legend-item"><div class="legend-dot" style="border-color:#3B82F6;background:#EFF6FF;"></div>步骤</div>
    <div class="legend-item"><div class="legend-dot" style="border-color:#F59E0B;background:#FFF7ED;"></div>判断</div>
  </div>
</div>

<script>
  const connections = [
    ['start', 'step1', ''], ['step1', 'decide', ''],
    ['decide', 'end', '通过']
  ];
  window.addEventListener('load', () => {
    ensureArrowDef(document.getElementById('connectorSvg'));
    setTimeout(() => drawConnectors(connections), 100);
  });
</script>
```

---

## Layout B: Snake Flowchart (>4 Linear Steps)

For: Linear non-branching processes with many steps (5-20).

### Key Rules

- Max 4 nodes per row
- First row left→right, second row right→left (snake pattern)
- End-of-row to next-row turn connectors use bend lines, with ≥60px clearance at turns
- Node positions in grid are auto-calculated by JS (no manual grid-column)

### Snake Layout Generation Script

```javascript
function layoutSnake(nodeIds, cols) {
  cols = cols || 4;
  nodeIds.forEach((id, i) => {
    const row = Math.floor(i / cols);
    const colInRow = i % cols;
    const col = row % 2 === 0 ? colInRow + 1 : cols - colInRow; // Even rows L→R, odd rows R→L
    const el = document.querySelector(`[data-id="${id}"]`);
    if (el) {
      el.style.gridRow = row + 1;
      el.style.gridColumn = col;
    }
  });
}
```

---

## Layout C: Phased Vertical Flowchart (⭐ DEFAULT for all flowcharts)

**This is the DEFAULT layout for flowcharts.** When the user asks for any flowchart without specifying format, use this layout.

For: Any process with phases/stages, which is nearly ALL real-world processes (manufacturing, legal, project management, business operations, etc.). Also the safe fallback when unsure.

**Why this is the default:** Layout C produces consistently professional, readable results. Even if the process has only 2 "phases", the card-based grouping still looks clean. In contrast, Layout A (Grid) without proper grouping produces scattered, unreadable results.

### Key Design

**Phase titles vs sub-steps must have clear visual distinction**:
- Phase titles: colored background, font-size ≥ 16px, font-weight: 700
- Sub-steps: white/light gray background, font-size 14-15px, font-weight: 400-500

**No arrows between sub-steps**. Arrows only connect phase-to-phase. Sub-steps use indent + numbering for sequence.

### Phase Connector Direction Rule
Phase-to-phase connector arrows MUST match the logical flow direction. If the flow goes top → bottom, arrows point ↓. If bottom → top, arrows point ↑. If left → right, arrows point →. **Never draw arrows opposing the flow direction.**

### Additional CSS

```css
.phase-group {
  background: #F8FAFC; border-radius: 12px; padding: 20px 24px;
  margin-bottom: 24px;
}
.phase-title {
  font-size: 16px; font-weight: 700; padding: 10px 16px;
  border-radius: 8px; margin-bottom: 16px;
}
.phase-steps { display: flex; flex-direction: column; gap: 8px; padding-left: 12px; }
.phase-step {
  font-size: 14px; font-weight: 400; color: var(--text);
  padding: 8px 14px; background: white; border-radius: 6px;
  border: 1px solid var(--border);
}
.phase-step .step-num {
  display: inline-block; width: 22px; height: 22px; line-height: 22px;
  text-align: center; border-radius: 50%; font-size: 12px; font-weight: 600;
  margin-right: 8px;
}

/* Phase colors — same-hue blue-gray gradient (low saturation, easy on the eyes)
   All phases share the blue-gray color family, distinguished by brightness progression.
   🚫 FORBIDDEN: Different hue per phase (blue→green→amber→purple) — becomes rainbow with many phases.
   ✅ CORRECT: Progress within same hue family (light→dark), or pure grayscale + single-color accent.
   
   Two schemes provided below; model selects based on phase count:
   - ≤4 phases: Scheme A (blue-gray progression)
   - 5-7 phases: Scheme B (neutral gray base + blue accent progression)
   - >7 phases: all use same gray base, distinguish only by numbering
*/

/* Scheme A: Blue-gray progression (≤4 phases) */
.phase-1 .phase-title { background: #F0F4F8; color: #334155; border-left: 4px solid #64748B; }
.phase-1 .step-num { background: #E2E8F0; color: #475569; }
.phase-2 .phase-title { background: #E8EDF2; color: #1E3A5F; border-left: 4px solid #5B7A99; }
.phase-2 .step-num { background: #DBEAFE; color: #1E3A5F; }
.phase-3 .phase-title { background: #E0E7EF; color: #1E3050; border-left: 4px solid #4A6B8A; }
.phase-3 .step-num { background: #D0D9E4; color: #1E3050; }
.phase-4 .phase-title { background: #D8E0EA; color: #172540; border-left: 4px solid #3A5C7A; }
.phase-4 .step-num { background: #C7D2E0; color: #172540; }

/* Scheme B: Neutral gray base + blue accent progression (5-7 phases) */
/*
.phase-1 .phase-title { background: #F8FAFC; color: #334155; border-left: 4px solid #94A3B8; }
.phase-1 .step-num { background: #F1F5F9; color: #475569; }
.phase-2 .phase-title { background: #F1F5F9; color: #334155; border-left: 4px solid #7B8FA3; }
.phase-2 .step-num { background: #E2E8F0; color: #475569; }
.phase-3 .phase-title { background: #E8EDF3; color: #2D4156; border-left: 4px solid #6B809A; }
.phase-3 .step-num { background: #DBEAFE; color: #2D4156; }
.phase-4 .phase-title { background: #E2E8F0; color: #283C52; border-left: 4px solid #5B7590; }
.phase-4 .step-num { background: #D0D9E4; color: #283C52; }
.phase-5 .phase-title { background: #DAE1EB; color: #23364D; border-left: 4px solid #4B6A87; }
.phase-5 .step-num { background: #C7D2E0; color: #23364D; }
.phase-6 .phase-title { background: #D2DAE5; color: #1E3048; border-left: 4px solid #3B5F7D; }
.phase-6 .step-num { background: #BFC9D8; color: #1E3048; }
.phase-7 .phase-title { background: #CAD3E0; color: #192A3E; border-left: 4px solid #2B5473; }
.phase-7 .step-num { background: #B7C2D2; color: #192A3E; }
*/
```

### HTML Structure

```html
<div id="root">
  <div class="flow-title">项目流程</div>
  
  <div class="phase-group phase-1">
    <div class="phase-title">第一阶段：需求分析</div>
    <div class="phase-steps">
      <div class="phase-step"><span class="step-num">1</span>需求收集与整理</div>
      <div class="phase-step"><span class="step-num">2</span>可行性评估</div>
      <div class="phase-step"><span class="step-num">3</span>需求优先级排序</div>
    </div>
  </div>
  
  <!-- Phase-to-phase arrow (use SVG or simple centered down arrow) -->
  <div style="text-align:center; color:#94A3B8; font-size:24px; margin: 8px 0;">↓</div>
  
  <div class="phase-group phase-2">
    <div class="phase-title">第二阶段：设计开发</div>
    <div class="phase-steps">
      <div class="phase-step"><span class="step-num">4</span>UI/UX 设计</div>
      <div class="phase-step"><span class="step-num">5</span>前后端开发</div>
    </div>
  </div>
</div>
```

---

## Layout D: Dual-Panel / Swimlane Flowchart

For: Processes involving multiple roles or departments.

### Key Rules

- Canvas width ≥ 1600px
- Left panel for role/swimlane labels, right panel for flow nodes
- Role labels font-size ≥ 12px, solid background, right edge ≥ 40px from canvas
- `overflow: hidden` is forbidden

### Additional CSS

```css
.dual-layout { display: flex; gap: 40px; }
.role-panel {
  flex-shrink: 0; width: 160px;
  display: flex; flex-direction: column; gap: 12px;
}
.role-tag {
  font-size: 13px; font-weight: 600; padding: 8px 12px;
  border-radius: 6px; text-align: center;
}
.flow-panel { flex: 1; min-width: 0; }
```

---

## Infographic Templates

The following templates are for non-flowchart information visualization.

### Template: KPI Dashboard Cards

```css
.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 20px; margin-bottom: 32px;
}
.kpi-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 24px; text-align: center;
}
.kpi-label { font-size: 13px; color: var(--text-sub); margin-bottom: 8px; }
.kpi-value { font-size: 32px; font-weight: 700; }
.kpi-change { font-size: 14px; font-weight: 600; margin-top: 8px; }
.kpi-change.up { color: var(--positive); }
.kpi-change.down { color: var(--negative); }
```

### Template: CSS Bar Chart (Pure CSS, No JS)

```css
.bar-chart {
  display: flex; align-items: flex-end; gap: 16px;
  height: 300px; padding: 0 20px; border-bottom: 1px solid var(--border);
}
.bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.bar { width: 100%; max-width: 60px; border-radius: 6px 6px 0 0; background: var(--border); }
.bar.highlight { background: var(--blue); }
.bar-label { font-size: 12px; color: var(--text-sub); }
.bar-value { font-size: 11px; color: var(--text-muted); font-weight: 600; }
```

### Template: Gradient Background Infographic Header

```css
.hero-header {
  background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
  border-radius: 16px; padding: 48px; color: white; margin-bottom: 32px;
}
.hero-header h1 { font-size: 28px; font-weight: 700; margin-bottom: 12px; }
.hero-header p { font-size: 15px; color: #94A3B8; max-width: 600px; line-height: 1.6; }
.hero-badge {
  display: inline-block; background: rgba(59,130,246,0.15);
  color: #60A5FA; font-size: 12px; font-weight: 600;
  padding: 4px 12px; border-radius: 20px; margin-bottom: 16px;
}
```

### Template: Data Card + Mini Sparkline

```html
<div class="metric-card">
  <div class="metric-info">
    <div class="metric-title">月活用户</div>
    <div class="metric-value">34,521</div>
    <div class="metric-change" style="color: var(--positive)">↑ +18.2%</div>
  </div>
  <div class="metric-sparkline">
    <svg width="120" height="40" viewBox="0 0 120 40">
      <polyline fill="none" stroke="var(--blue)" stroke-width="2"
        points="0,35 15,30 30,25 45,28 60,20 75,15 90,12 105,8 120,5" />
    </svg>
  </div>
</div>
```

```css
.metric-card {
  background: white; border: 1px solid var(--border);
  border-radius: 16px; padding: 28px;
  display: flex; justify-content: space-between; align-items: center;
}
.metric-title { font-size: 13px; color: var(--text-sub); }
.metric-value { font-size: 36px; font-weight: 700; margin: 4px 0; }
.metric-change { font-size: 14px; font-weight: 600; }
```

---

## Advanced Connector Rules

### Many-to-One Convergence

When multiple lines converge into one node, use the "merge first, then enter" pattern:

```
[A] ──┐
[B] ──┤── → [目标]
[C] ──┘
```

Implementation: Source lines reach a relay x-coordinate, merge into one vertical line, then a single line enters the target.

### Cross-Layer Connector Avoidance

If other nodes block the path between two nodes, **do not draw a straight line through them**.

Priority:
1. **Redesign hierarchy** (best) — Most cross-layer lines indicate hierarchy design issues; connect adjacent layers only
2. **Detour line** — Route around middle nodes via canvas edge (offset 40px right)
3. **Thread through gap** — If middle-layer node gap ≥ 40px, route through the gap

### Connector Alignment

- Multiple lines from the same node start at a consistent position on the node border
- Use only one connector style per chart (right-angle/curved/straight), no mixing
- Connector label positions must be consistent (all above line or all centered)

---

## Font Size Rules

| Element | Recommended | Minimum |
|------|------|------|
| Flowchart main node title | 16-18px | 14px |
| Node description / subtext | 13-15px | 12px |
| Connector labels | 12-14px | 11px |
| Legend text | 13-14px | 12px |
| Footnotes / watermark | 11-13px | 10px |
| Phase titles | 16-18px | 16px |
| Role labels | 13-14px | 12px |

**Not enough space → Enlarge canvas, don't shrink fonts.**

---

## Overflow Protection

1. **`#root { width: fit-content; min-width: 800px; }`** — Expands with content automatically
2. **`overflow: hidden` / `overflow: clip` are forbidden**
3. **Auto-resize viewport before Playwright screenshot** (see 3.1 screenshot script)
4. **Canvas minimum width**:

| Layout Type | Minimum Width | Recommended |
|---------|---------|------|
| Single-column flowchart | 800px | 1000px |
| Dual-panel / swimlane | 1400px | 1600-1800px |
| Three-column / multi-panel | 1800px | 2000-2400px |

---

## Quality Checklist

1. **Layout C used by default** — If this is a flowchart, verify you're using Layout C (Phased Vertical) unless there's a specific reason not to
2. **Content complete** — Every node/step from the requirement is in the chart
3. **No overlap** — No boxes covering boxes, no lines through boxes
4. **Clear hierarchy** — Phase titles and sub-steps are instantly distinguishable
5. **Colors reasonable** — Node backgrounds low-saturation, no children's-drawing palette
6. **Connectors visible** — Connector color ≥ `#94A3B8`, arrow direction correct
7. **Font sizes meet standards** — Check against font size table, nothing below minimum
8. **Legend independent** — Not inside flow-grid, not obscured by any node
9. **No clipping** — Padding ≥ 40px on all sides, all nodes and labels fully visible
10. **Phase colors consistent** — Same hue family, no blue/brown/green/purple mix
11. **Connectors don't pass through nodes** — Cross-layer lines use detour or redesign hierarchy
12. **No scattered layout** — Phase titles MUST be inside group cards, NOT floating as isolated labels

---

## Playwright+CSS vs Other Approaches

| Capability | Playwright+CSS | matplotlib | ECharts |
|------|---------------|------------|---------|
| Gradients/shadows/rounded | ✅ Full CSS power | ❌ Limited | ⚠️ Partial |
| Responsive layout | ✅ Flexbox/Grid | ❌ Fixed size | ⚠️ resize |
| PNG/PDF export | ✅ Native | ✅ savefig | ⚠️ Needs Playwright |
| Precise data charts | ⚠️ Manual | ✅ Built-in | ✅ Built-in |

**Best practice: CSS for layout and visual design, embed ECharts/SVG for precise charts.**
