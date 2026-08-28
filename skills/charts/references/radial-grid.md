# CSS Radial Grid Layout (Center-Outward Diagrams)

> **⚠️ Before writing any code, read [`_rules.md`](references/_rules.md) — three non-negotiable rules on overlap, hierarchy, and color.**

**For: SWOT analysis, Balanced Scorecard (BSC), Porter's Five Forces, PEST analysis, and any "center + 4-6 surrounding dimensions" diagram.**

**Core principle: Use flex rows to lock positions — model never calculates coordinates. Connectors are drawn by script reading bounding boxes.**

---

## When to Use This Template

| Diagram Type | Dimensions | Use This? |
|-------------|-----------|-----------|
| SWOT (Strengths/Weaknesses/Opportunities/Threats) | 4 quadrants | ✅ Layout B (2×2 Grid) |
| Balanced Scorecard (Financial/Customer/Internal/Learning) | 4 dimensions | ✅ Layout A (Cross) |
| Porter's Five Forces | 5 forces | ✅ Layout A (Cross + extra row) |
| PEST (Political/Economic/Social/Technological) | 4 dimensions | ✅ Layout B (2×2 Grid) |
| Competency wheel / capability map | 5-8 dimensions | ✅ Layout A with extra rows |
| Anything with center + surrounding elements | 3-8 | ✅ |

---

## Layout A: Cross Layout (4-6 Dimensions)

Best for: BSC, Porter's Five Forces, any "center with surrounding dimensions" structure.

### 🚫 FORBIDDEN: 3×3 CSS Grid Cross

**Do NOT use `grid-template-columns: Xpx Ypx Xpx` to place cards in a cross pattern.** The top/bottom cards in the center column will overflow into the side columns and overlap with left/right cards when content is longer than expected.

### ✅ REQUIRED: Three-Row Flex Layout

**Each row is an independent flex container. Rows cannot overlap each other — physically impossible.**

```
Row 1 (top):     [top dimension card]    ← independent flex row, centered
Row 2 (middle):  [left card] [center] [right card] ← independent flex row, horizontal
Row 3 (bottom):  [bottom dimension card] ← independent flex row, centered
```

### HTML + CSS

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'SimHei', sans-serif;
  background: #FFFFFF;
}

#root { width: fit-content; min-width: 900px; padding: 48px 60px; }

.diagram-title {
  font-size: 22px; font-weight: 700; color: #1F2937;
  text-align: center; margin-bottom: 6px;
}
.diagram-subtitle {
  font-size: 14px; color: #6B7280;
  text-align: center; margin-bottom: 40px;
}

/* === Three-row flex layout: rows CANNOT overlap === */
.cross-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  position: relative;
}

/* Middle row: left card + center + right card */
.middle-row {
  display: flex;
  align-items: center;
  gap: 40px;
}

/* Center node */
.center-node {
  background: linear-gradient(135deg, #1E293B, #334155);
  color: white; font-size: 18px; font-weight: 700;
  padding: 24px 32px; border-radius: 14px;
  text-align: center; z-index: 2;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  flex-shrink: 0;
}
.center-sub {
  font-size: 12px; font-weight: 400; color: #94A3B8;
  margin-top: 4px;
}

/* Dimension cards */
.dim-card {
  background: #FFFFFF; border-radius: 12px;
  padding: 20px; border: 2px solid;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  z-index: 2;
  width: 260px;
  flex-shrink: 0;
}
.dim-card .dim-title {
  font-size: 15px; font-weight: 700; margin-bottom: 10px;
  padding-bottom: 8px; border-bottom: 2px solid;
  display: flex; align-items: center; gap: 8px;
}
.dim-card .dim-icon {
  width: 26px; height: 26px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.dim-card .dim-items { list-style: none; }
.dim-card .dim-items li {
  font-size: 13px; color: #475569; padding: 4px 0 4px 18px;
  position: relative; line-height: 1.5;
}
.dim-card .dim-items li::before {
  content: ''; position: absolute; left: 0; top: 10px;
  width: 6px; height: 6px; border-radius: 50%;
}

/* Color variants — border + title border + bullet */
.dim-blue { border-color: #3B82F6; }
.dim-blue .dim-title { color: #1E40AF; border-color: #3B82F6; }
.dim-blue .dim-icon { background: #DBEAFE; color: #1E40AF; }
.dim-blue li::before { background: #3B82F6; }

.dim-green { border-color: #10B981; }
.dim-green .dim-title { color: #065F46; border-color: #10B981; }
.dim-green .dim-icon { background: #D1FAE5; color: #065F46; }
.dim-green li::before { background: #10B981; }

.dim-amber { border-color: #F59E0B; }
.dim-amber .dim-title { color: #92400E; border-color: #F59E0B; }
.dim-amber .dim-icon { background: #FEF3C7; color: #92400E; }
.dim-amber li::before { background: #F59E0B; }

.dim-purple { border-color: #8B5CF6; }
.dim-purple .dim-title { color: #5B21B6; border-color: #8B5CF6; }
.dim-purple .dim-icon { background: #EDE9FE; color: #5B21B6; }
.dim-purple li::before { background: #8B5CF6; }

.dim-red { border-color: #EF4444; }
.dim-red .dim-title { color: #991B1B; border-color: #EF4444; }
.dim-red .dim-icon { background: #FEE2E2; color: #991B1B; }
.dim-red li::before { background: #EF4444; }

.dim-cyan { border-color: #06B6D4; }
.dim-cyan .dim-title { color: #155E75; border-color: #06B6D4; }
.dim-cyan .dim-icon { background: #CFFAFE; color: #155E75; }
.dim-cyan li::before { background: #06B6D4; }

/* SVG connector layer */
.cross-connectors {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 1;
}
</style>
</head>
<body>
<div id="root">
  <div class="diagram-title">平衡计分卡四维评价体系</div>
  <div class="diagram-subtitle">基于战略目标的绩效管理框架</div>
  
  <div class="cross-layout" id="crossLayout">
    <!-- SVG connectors drawn by script -->
    <svg class="cross-connectors" id="connSvg"></svg>
    
    <!-- Row 1: top dimension -->
    <div class="dim-card dim-blue" data-pos="top">
      <div class="dim-title"><div class="dim-icon">F</div> 财务维度</div>
      <ul class="dim-items">
        <li>营收增长率</li>
        <li>利润率</li>
        <li>ROI</li>
      </ul>
    </div>
    
    <!-- Row 2: left + center + right -->
    <div class="middle-row">
      <div class="dim-card dim-green" data-pos="left">
        <div class="dim-title"><div class="dim-icon">I</div> 内部流程</div>
        <ul class="dim-items">
          <li>流程效率</li>
          <li>质量管控</li>
          <li>创新能力</li>
        </ul>
      </div>
      
      <div class="center-node">战略目标</div>
      
      <div class="dim-card dim-amber" data-pos="right">
        <div class="dim-title"><div class="dim-icon">C</div> 客户维度</div>
        <ul class="dim-items">
          <li>客户满意度</li>
          <li>市场份额</li>
          <li>客户留存率</li>
        </ul>
      </div>
    </div>
    
    <!-- Row 3: bottom dimension -->
    <div class="dim-card dim-purple" data-pos="bottom">
      <div class="dim-title"><div class="dim-icon">L</div> 学习与成长</div>
      <ul class="dim-items">
        <li>员工能力提升</li>
        <li>信息系统建设</li>
        <li>组织文化</li>
      </ul>
    </div>
  </div>
</div>

<script>
function drawCrossConnectors() {
  const layout = document.getElementById('crossLayout');
  const svg = document.getElementById('connSvg');
  const gRect = layout.getBoundingClientRect();
  
  svg.setAttribute('width', gRect.width);
  svg.setAttribute('height', gRect.height);
  svg.setAttribute('viewBox', `0 0 ${gRect.width} ${gRect.height}`);
  svg.innerHTML = '';
  
  // Bidirectional arrow markers — eliminates direction ambiguity
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <marker id="arrowEnd" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#94A3B8" />
    </marker>
    <marker id="arrowStart" markerWidth="8" markerHeight="6" refX="1" refY="3" orient="auto">
      <polygon points="8 0, 0 3, 8 6" fill="#94A3B8" />
    </marker>
  `;
  svg.appendChild(defs);
  
  const center = layout.querySelector('.center-node');
  const cR = center.getBoundingClientRect();
  const cx = cR.left - gRect.left + cR.width / 2;
  const cy = cR.top - gRect.top + cR.height / 2;
  
  // Draw connector from center edge to each card edge
  const cards = layout.querySelectorAll('.dim-card');
  cards.forEach(card => {
    const pos = card.dataset.pos;
    const r = card.getBoundingClientRect();
    const cardCx = r.left - gRect.left + r.width / 2;
    const cardCy = r.top - gRect.top + r.height / 2;
    
    let x1, y1, x2, y2;
    switch (pos) {
      case 'top':
        x1 = cx; y1 = cR.top - gRect.top;       // center top edge midpoint
        x2 = cardCx; y2 = r.bottom - gRect.top;   // card bottom edge midpoint
        break;
      case 'bottom':
        x1 = cx; y1 = cR.bottom - gRect.top;      // center bottom edge midpoint
        x2 = cardCx; y2 = r.top - gRect.top;       // card top edge midpoint
        break;
      case 'left':
        x1 = cR.left - gRect.left; y1 = cy;       // center left edge midpoint
        x2 = r.right - gRect.left; y2 = cardCy;    // card right edge midpoint
        break;
      case 'right':
        x1 = cR.right - gRect.left; y1 = cy;      // center right edge midpoint
        x2 = r.left - gRect.left; y2 = cardCy;     // card left edge midpoint
        break;
      // --- 5+ dimension: bottom row with two cards side by side ---
      case 'bottom-left':
        x1 = cx; y1 = cR.bottom - gRect.top;       // center BOTTOM MIDPOINT (not corner!)
        x2 = cardCx; y2 = r.top - gRect.top;        // card TOP MIDPOINT
        break;
      case 'bottom-right':
        x1 = cx; y1 = cR.bottom - gRect.top;       // center BOTTOM MIDPOINT (not corner!)
        x2 = cardCx; y2 = r.top - gRect.top;        // card TOP MIDPOINT
        break;
    }
    
    // 🚫 FORBIDDEN: drawing lines from center CORNERS (e.g. cR.left + cR.bottom)
    // All lines MUST originate from center EDGE MIDPOINTS (cx or cy)
    
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1);
    line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.setAttribute('stroke', '#94A3B8');
    line.setAttribute('stroke-width', '2');
    line.setAttribute('stroke-dasharray', '6,4');
    line.setAttribute('marker-start', 'url(#arrowStart)');
    line.setAttribute('marker-end', 'url(#arrowEnd)');
    svg.appendChild(line);
  });
}

window.addEventListener('load', () => setTimeout(drawCrossConnectors, 300));
</script>
</body>
</html>
```

**Key design decisions:**
- **Three-row flex** instead of 3×3 Grid — rows physically cannot overlap
- **Fixed card width (260px)** — prevents content-driven overflow
- **`gap: 24px`** between rows, **`gap: 40px`** within middle row — generous spacing
- **Center node uses `flex-shrink: 0`** — never collapses under pressure

### Adapting for 5+ Dimensions

For Porter's Five Forces (5 dimensions) or more:

```html
<!-- Row 1: top -->
<div class="dim-card dim-blue" data-pos="top">...</div>

<!-- Row 2: left + center + right -->
<div class="middle-row">
  <div class="dim-card dim-green" data-pos="left">...</div>
  <div class="center-node">...</div>
  <div class="dim-card dim-amber" data-pos="right">...</div>
</div>

<!-- Row 3: bottom-left + bottom-right (two cards side by side) -->
<div class="middle-row" style="gap: 40px;">
  <div class="dim-card dim-purple" data-pos="bottom-left">...</div>
  <div class="dim-card dim-red" data-pos="bottom-right">...</div>
</div>
```

For the connector script, add cases for `bottom-left` and `bottom-right`:
```javascript
// 🚫 FORBIDDEN: using cR.left/cR.right as x1 — that draws from center CORNER, angle is ugly
// ✅ CORRECT: always use cx (center bottom midpoint) as x1
case 'bottom-left':
  x1 = cx; y1 = cR.bottom - gRect.top;        // center BOTTOM MIDPOINT
  x2 = cardCx; y2 = r.top - gRect.top;         // card TOP MIDPOINT
  break;
case 'bottom-right':
  x1 = cx; y1 = cR.bottom - gRect.top;        // center BOTTOM MIDPOINT
  x2 = cardCx; y2 = r.top - gRect.top;         // card TOP MIDPOINT
  break;
```

### Adapting for 3 Dimensions

Simply remove one side card from the middle row:

```html
<!-- Row 1: top -->
<div class="dim-card dim-blue" data-pos="top">...</div>

<!-- Row 2: center + right only -->
<div class="middle-row">
  <div class="center-node">...</div>
  <div class="dim-card dim-amber" data-pos="right">...</div>
</div>

<!-- Row 3: bottom -->
<div class="dim-card dim-purple" data-pos="bottom">...</div>
```

---

## Layout B: 2×2 Quadrant Grid (SWOT / PEST)

Best for: exactly 4 dimensions arranged as equal quadrants (no center node needed).

**This layout has NO center node — the four quadrants themselves tell the story.**

### HTML + CSS

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'SimHei', sans-serif;
  background: #FFFFFF;
}

#root { width: fit-content; min-width: 900px; padding: 48px 60px; }

.diagram-title {
  font-size: 22px; font-weight: 700; color: #1F2937;
  text-align: center; margin-bottom: 12px;
}
.diagram-subtitle {
  font-size: 14px; color: #6B7280;
  text-align: center; margin-bottom: 36px;
}

.quadrant-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.quadrant {
  border-radius: 12px; padding: 24px;
  border: 1.5px solid;
  min-height: 200px;
}
.quadrant .q-title {
  font-size: 16px; font-weight: 700; margin-bottom: 14px;
  display: flex; align-items: center; gap: 8px;
}
.quadrant .q-icon {
  width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700;
}
.quadrant .q-items { list-style: none; }
.quadrant .q-items li {
  font-size: 13px; padding: 5px 0 5px 18px;
  position: relative; line-height: 1.5;
}
.quadrant .q-items li::before {
  content: ''; position: absolute; left: 0; top: 11px;
  width: 6px; height: 6px; border-radius: 50%;
}

/* SWOT colors — low-sat backgrounds, sat borders */
.q-strengths { background: #F0FDF4; border-color: #86EFAC; }
.q-strengths .q-title { color: #065F46; }
.q-strengths .q-icon { background: #D1FAE5; color: #065F46; }
.q-strengths li { color: #1F2937; }
.q-strengths li::before { background: #10B981; }

.q-weaknesses { background: #FEF2F2; border-color: #FECACA; }
.q-weaknesses .q-title { color: #991B1B; }
.q-weaknesses .q-icon { background: #FEE2E2; color: #991B1B; }
.q-weaknesses li { color: #1F2937; }
.q-weaknesses li::before { background: #EF4444; }

.q-opportunities { background: #EFF6FF; border-color: #93C5FD; }
.q-opportunities .q-title { color: #1E40AF; }
.q-opportunities .q-icon { background: #DBEAFE; color: #1E40AF; }
.q-opportunities li { color: #1F2937; }
.q-opportunities li::before { background: #3B82F6; }

.q-threats { background: #FFF7ED; border-color: #FDE68A; }
.q-threats .q-title { color: #92400E; }
.q-threats .q-icon { background: #FEF3C7; color: #92400E; }
.q-threats li { color: #1F2937; }
.q-threats li::before { background: #F59E0B; }
</style>
</head>
<body>
<div id="root">
  <div class="diagram-title">SWOT 分析</div>
  <div class="diagram-subtitle">企业战略定位评估</div>
  
  <div class="quadrant-grid">
    <div class="quadrant q-strengths">
      <div class="q-title"><div class="q-icon">S</div> 优势 Strengths</div>
      <ul class="q-items">
        <li>核心技术领先</li>
        <li>品牌知名度高</li>
        <li>供应链成熟</li>
      </ul>
    </div>
    
    <div class="quadrant q-weaknesses">
      <div class="q-title"><div class="q-icon">W</div> 劣势 Weaknesses</div>
      <ul class="q-items">
        <li>国际化经验不足</li>
        <li>产品线单一</li>
        <li>人才储备有限</li>
      </ul>
    </div>
    
    <div class="quadrant q-opportunities">
      <div class="q-title"><div class="q-icon">O</div> 机会 Opportunities</div>
      <ul class="q-items">
        <li>新兴市场需求增长</li>
        <li>政策利好</li>
        <li>技术融合趋势</li>
      </ul>
    </div>
    
    <div class="quadrant q-threats">
      <div class="q-title"><div class="q-icon">T</div> 威胁 Threats</div>
      <ul class="q-items">
        <li>竞争加剧</li>
        <li>原材料价格波动</li>
        <li>法规变化风险</li>
      </ul>
    </div>
  </div>
</div>
</body>
</html>
```

**No connectors needed** — the 2×2 grid itself communicates the four-quadrant relationship. Adding arrows would be visual noise.

---

## Connector Rules

1. **Connectors are ALWAYS drawn by script reading bounding boxes** — never hardcode x/y values in HTML/CSS
2. **Straight lines only** (horizontal or vertical) — no diagonal lines unless top/bottom cards are offset from center
3. **Dashed lines** (`stroke-dasharray: 6,4`) for conceptual relationships
4. **Solid lines** for causal/sequential relationships
5. **Arrow direction**: model chooses based on diagram semantics — pick ONE style per diagram, don't mix:
   - **Outward** (`marker-end` only): center influences/drives dimensions (e.g. BSC: strategy → dimensions)
   - **Inward** (`marker-start` only): dimensions report/pressure center (e.g. Porter: forces → competition)
   - **Bidirectional** (`marker-start` + `marker-end`): mutual influence (e.g. feedback loops)
6. **🚫 All lines MUST originate from center EDGE MIDPOINTS** (cx or cy) — never from center corners
7. **Line color**: `#94A3B8` (gray-blue) — never use dimension-specific colors for connectors (visual chaos)

### SVG Arrow Markers (copy-paste into defs)

```javascript
// Include both markers; use only what the diagram needs
const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
defs.innerHTML = `
  <marker id="arrowEnd" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0, 8 3, 0 6" fill="#94A3B8" />
  </marker>
  <marker id="arrowStart" markerWidth="8" markerHeight="6" refX="1" refY="3" orient="auto">
    <polygon points="8 0, 0 3, 8 6" fill="#94A3B8" />
  </marker>
`;
svg.appendChild(defs);

// Outward (center → card):
line.setAttribute('marker-end', 'url(#arrowEnd)');

// Inward (card → center):
line.setAttribute('marker-start', 'url(#arrowStart)');

// Bidirectional:
line.setAttribute('marker-start', 'url(#arrowStart)');
line.setAttribute('marker-end', 'url(#arrowEnd)');
```

---

## Content Rules

1. **Each dimension card: max 6 bullet items** — more than 6 → group into sub-categories or use a separate detail table
2. **Bullet text: max 15 Chinese characters per line** — longer text wraps naturally (word-break: break-word)
3. **Center node text: max 8 Chinese characters** — keep it a short label, not a sentence
4. **Dimension title: max 10 Chinese characters** — concise category name

---

## Font Size Rules

| Element | Size | Weight |
|---------|------|--------|
| Diagram title | 22px | 700 |
| Center node | 18px | 700 |
| Dimension title | 15-16px | 700 |
| Bullet items | 13px | 400 |
| Subtitle/footnote | 14px | 400 |

---

## Quality Checklist

1. **No overlap** — all dimension cards fully visible, none clipped or covering another
2. **Connectors point to card edges** — not to random points in space
3. **Center node visually dominant** — largest, darkest, or most contrast
4. **Dimension cards visually equal** — similar size, similar padding, no one card 3× larger
5. **Colors follow scheme** — each dimension has its own color (border + title), backgrounds stay pale (white or near-white)
6. **Layout is centered** — equal margins on all sides
7. **Canvas large enough** — min 900px wide for cross layout, min 800px for 2×2 quadrant
