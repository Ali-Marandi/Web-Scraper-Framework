# ECharts Template Library

> **⚠️ Before writing any code, read [`_rules.md`](references/_rules.md) — three non-negotiable rules on overlap, hierarchy, and color.**


ECharts strengths: interactivity (tooltip/zoom/linking), big data (Canvas renders millions of points smoothly), strong Chinese community.
Output as HTML files — open directly in browser or export PNG via Playwright screenshot.

## HTML Universal Shell

Wrap all ECharts charts with this shell:

```html
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>{{TITLE}}</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: {{BG_COLOR}}; }
  #chart { width: {{WIDTH}}px; height: {{HEIGHT}}px; margin: 40px auto; }
</style>
</head>
<body>
<div id="chart"></div>
<script>
const chart = echarts.init(document.getElementById('chart'));
const option = { /* see templates below */ };
chart.setOption(option);
window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>
```

Default dimensions: `width=900, height=520`, white background `#FFFFFF`.

---

## Theme Configuration

### Light Theme (Default)

```javascript
const THEME = {
  bg: '#FFFFFF',
  text: '#111827',
  textSub: '#6B7280',
  textMuted: '#9CA3AF',
  axis: '#E5E7EB',
  grid: '#F3F4F6',
  tooltip: { bg: '#1E293B', border: '#334155', text: '#F1F5F9' },
  colors: ['#3B82F6', '#06B6D4', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981'],
};
```

### Dark Theme (Finance / Tech Dashboard)

```javascript
const DARK = {
  bg: '#0F172A',
  text: '#F1F5F9',
  textSub: '#94A3B8',
  textMuted: '#64748B',
  axis: '#334155',
  grid: '#1E293B',
  tooltip: { bg: '#1E293B', border: '#475569', text: '#F1F5F9' },
  colors: ['#3B82F6', '#06B6D4', '#8B5CF6', '#F59E0B', '#22C55E', '#EC4899'],
};
```

### Base Option Configuration

```javascript
function baseOption(theme, title, subtitle) {
  return {
    backgroundColor: theme.bg,
    textStyle: { fontFamily: 'system-ui, SimHei, sans-serif', color: theme.text },
    title: {
      text: title, subtext: subtitle || '',
      left: 24, top: 16,
      textStyle: { fontSize: 16, fontWeight: 'bold', color: theme.text },
      subtextStyle: { fontSize: 12, color: theme.textSub },
    },
    grid: { left: 60, right: 40, top: 80, bottom: 50, containLabel: true },
    color: theme.colors,
    tooltip: {
      trigger: 'axis',
      backgroundColor: theme.tooltip.bg,
      borderColor: theme.tooltip.border,
      borderWidth: 1,
      textStyle: { color: theme.tooltip.text, fontSize: 12 },
    },
    animationDuration: 600,
    animationEasing: 'cubicOut',
  };
}

function cleanAxis(theme) {
  return {
    axisLine: { lineStyle: { color: theme.axis, width: 0.8 } },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: theme.grid, width: 0.5 } },
    axisLabel: { color: theme.textSub, fontSize: 10 },
  };
}
```

---

## Template 1: Insight Bar Chart

```javascript
const option = {
  ...baseOption(THEME, 'Q3 收入环比增长 47%', '各季度收入对比（万元）'),
  xAxis: { type: 'category', data: ['Q1','Q2','Q3','Q4'], ...cleanAxis(THEME) },
  yAxis: { type: 'value', ...cleanAxis(THEME) },
  series: [{
    type: 'bar', barWidth: '50%',
    itemStyle: { borderRadius: [4, 4, 0, 0] },
    data: [
      { value: 120, itemStyle: { color: '#E5E7EB' } },
      { value: 145, itemStyle: { color: '#E5E7EB' } },
      { value: 213, itemStyle: { color: '#3B82F6' } },
      { value: 180, itemStyle: { color: '#E5E7EB' } },
    ],
    label: {
      show: true, position: 'top', fontSize: 11, color: '#6B7280',
      formatter: (p) => p.dataIndex === 2
        ? '{hl|' + p.value + '}'
        : p.value,
      rich: { hl: { fontWeight: 'bold', fontSize: 13, color: '#111827' } },
    },
  }],
};
```

---

## Template 2: Multi-Line Trend

```javascript
const option = {
  ...baseOption(THEME, '2024 年增长持续加速'),
  legend: { right: 40, top: 20, textStyle: { color: '#6B7280', fontSize: 10 } },
  xAxis: { type: 'category', data: months, boundaryGap: false, ...cleanAxis(THEME) },
  yAxis: { type: 'value', ...cleanAxis(THEME) },
  series: [
    {
      name: '2024', type: 'line', data: thisYear,
      lineStyle: { width: 2.5 },
      symbol: 'circle', symbolSize: 6,
      itemStyle: { color: '#3B82F6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59,130,246,0.12)' },
          { offset: 1, color: 'rgba(59,130,246,0)' },
        ]),
      },
    },
    {
      name: '2023', type: 'line', data: lastYear,
      lineStyle: { width: 1.5, type: 'dashed', color: '#D1D5DB' },
      symbol: 'none', itemStyle: { color: '#D1D5DB' },
    },
  ],
};
```

---

## Template 3: Candlestick (Finance)

```javascript
// Dark theme
const option = {
  ...baseOption(DARK, 'BTC/USDT 日K线'),
  xAxis: { type: 'category', data: dates, ...cleanAxis(DARK) },
  yAxis: { type: 'value', scale: true, ...cleanAxis(DARK) },
  dataZoom: [
    { type: 'inside', start: 70, end: 100 },
    { type: 'slider', start: 70, end: 100, height: 20, bottom: 10,
      borderColor: DARK.axis, fillerColor: 'rgba(59,130,246,0.15)',
      textStyle: { color: DARK.textSub } },
  ],
  series: [{
    type: 'candlestick',
    data: ohlcData, // [[open,close,low,high], ...]
    itemStyle: {
      color: '#22C55E',        // Bullish (close > open)
      color0: '#EF4444',       // Bearish
      borderColor: '#16A34A',
      borderColor0: '#DC2626',
    },
  }],
};
```

---

## Template 4: Dashboard (Multi-Chart Linking)

⚠️ **ECharts multi-chart dashboard anti-overlap rules** (highest priority):
1. Maximum 4 subplots per canvas; more must be split into multiple HTML files
2. Each subplot's `grid` area must not overlap; maintain ≥5% safety margin between adjacent grids
3. Pie chart `center` and `radius` must not intrude into other subplots' grid areas
4. Same applies to radar chart's `radar.center` and `radar.radius`
5. Place legend in top/bottom common area, not inside subplots

### Simple Dual Chart (Bar + Pie)

```javascript
const option = {
  ...baseOption(THEME, '产品线收入分布'),
  grid: [{ left: 60, right: '55%', top: 80, bottom: 50 }],
  xAxis: [{ type: 'value', gridIndex: 0, ...cleanAxis(THEME) }],
  yAxis: [{ type: 'category', data: products, gridIndex: 0, ...cleanAxis(THEME) }],
  series: [
    {
      type: 'bar', data: revenues,
      itemStyle: { borderRadius: [0, 4, 4, 0] },
      barWidth: '60%',
    },
    {
      type: 'pie', center: ['78%', '50%'], radius: ['35%', '55%'],
      data: products.map((name, i) => ({ name, value: revenues[i] })),
      label: { formatter: '{b}\n{d}%', fontSize: 10 },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
    },
  ],
};
```

### Four-Chart Dashboard (Safe Layout Template)

```javascript
// ⚠️ Key: grid areas precisely defined, no overlap, maintain safety margins
const option = {
  ...baseOption(THEME, '数据全景仪表盘'),
  grid: [
    // Top-left: bar chart
    { left: '5%', right: '55%', top: '12%', bottom: '55%' },
    // Top-right: line chart
    { left: '55%', right: '5%', top: '12%', bottom: '55%' },
    // Bottom-left: scatter plot
    { left: '5%', right: '55%', top: '55%', bottom: '5%' },
    // Bottom-right area reserved for pie chart (pie uses center + radius, not grid)
  ],
  xAxis: [
    { type: 'category', gridIndex: 0, data: categories1, ...cleanAxis(THEME) },
    { type: 'category', gridIndex: 1, data: categories2, ...cleanAxis(THEME), boundaryGap: false },
    { type: 'value', gridIndex: 2, ...cleanAxis(THEME) },
  ],
  yAxis: [
    { type: 'value', gridIndex: 0, ...cleanAxis(THEME) },
    { type: 'value', gridIndex: 1, ...cleanAxis(THEME) },
    { type: 'value', gridIndex: 2, ...cleanAxis(THEME) },
  ],
  series: [
    // Top-left: bar chart
    {
      type: 'bar', xAxisIndex: 0, yAxisIndex: 0,
      data: barData,
      itemStyle: { borderRadius: [4, 4, 0, 0] },
    },
    // Top-right: line chart
    {
      type: 'line', xAxisIndex: 1, yAxisIndex: 1,
      data: lineData,
      smooth: true,
      areaStyle: { opacity: 0.08 },
    },
    // Bottom-left: scatter plot
    {
      type: 'scatter', xAxisIndex: 2, yAxisIndex: 2,
      data: scatterData,
      symbolSize: 8,
    },
    // Bottom-right: pie chart (positioned via center in bottom-right quadrant)
    {
      type: 'pie',
      center: ['77%', '72%'],    // Positioned at bottom-right area center
      radius: ['15%', '25%'],    // Radius stays within bottom-right quadrant
      data: pieData,
      label: { formatter: '{b}\n{d}%', fontSize: 10 },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
    },
  ],
};
```

### Grid Safety Margin Quick Reference

| Layout | Grid Config | Safety Margin |
|------|----------|---------|
| Left-right dual | Left `right:'55%'` Right `left:'55%'` | 10% center gap |
| Top-bottom dual | Top `bottom:'55%'` Bottom `top:'55%'` | 10% center gap |
| 2x2 quad | Each quadrant 45%, 10% center gap | 5% margin on all sides |
| With pie/radar | Pie center+radius must not intrude grid | Pie radius ≤ 40% of available area |

### What If More Than 4 Subplots?

```javascript
// ❌ Wrong: 8 charts crammed into one canvas — all labels will inevitably overlap
// ✅ Correct: split into 2 HTML files

// dashboard_overview.html — 4 overview charts
// dashboard_detail.html  — 4 detailed analysis charts

// Or use tab switching (ECharts toolbox doesn't support this, need custom HTML tabs)
```

---

## Template 5: Radar Chart

```javascript
const option = {
  ...baseOption(THEME, '团队能力评估'),
  radar: {
    indicator: dims.map(d => ({ name: d, max: 100 })),
    axisName: { color: '#6B7280', fontSize: 10 },
    splitArea: { areaStyle: { color: ['#FAFAFA', '#F5F5F5'] } },
    splitLine: { lineStyle: { color: '#E5E7EB' } },
    axisLine: { lineStyle: { color: '#E5E7EB' } },
  },
  series: [{
    type: 'radar',
    data: teams.map((t, i) => ({
      name: t.name, value: t.scores,
      lineStyle: { width: 2 },
      areaStyle: { opacity: 0.08 },
      itemStyle: { color: THEME.colors[i] },
    })),
  }],
  legend: { bottom: 10, textStyle: { color: '#6B7280' } },
};
```

---

## Export to PNG (Playwright)

```python
import asyncio
from playwright.async_api import async_playwright

async def echarts_to_png(html_path, png_path, width=900, height=520):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': width, 'height': height})
        await page.goto(f'file://{html_path}', wait_until='networkidle')
        await page.wait_for_timeout(800)  # Wait for animation to complete
        await page.locator('#chart').screenshot(path=png_path)
        await browser.close()
        print(f'✅ {png_path}')

# asyncio.run(echarts_to_png('./output/chart.html', './output/chart.png'))
```

---

## Template 5: Tree (Interactive Only)

**⚠️ For static PNG export, use Playwright+CSS (see `mindmap-css.md`). ECharts tree connector length and node spacing cannot be finely controlled — static output is not aesthetically satisfying.**

**ECharts tree is suitable for interactive scenarios** (click expand/collapse, hover tooltip, zoom/drag). For PNG/PDF static output, the CSS approach looks better.

### Basic Usage

```javascript
const option = {
  tooltip: { trigger: 'item', triggerOn: 'mousemove' },
  series: [{
    type: 'tree',
    data: [treeData],      // Tree-structured JSON data
    layout: 'orthogonal',  // Orthogonal layout (right-angle connectors)
    orient: 'LR',          // Direction: LR(left→right) / RL / TB(top→bottom) / BT
    
    // Node spacing control (key params to prevent crowding)
    initialTreeDepth: -1,  // -1=expand all, positive=initial expand depth
    
    // Label style
    label: {
      position: 'left',         // Leaf node label position
      verticalAlign: 'middle',
      fontSize: 13,
      fontFamily: 'PingFang SC, SimHei, sans-serif',
    },
    leaves: {
      label: { position: 'right' }  // Leaf labels on right
    },
    
    // Connector style
    lineStyle: {
      color: '#94A3B8',
      width: 1.5,
      curveness: 0.5,    // Curvature, 0=straight, 0.5=natural curve
    },
    
    // Node style
    itemStyle: {
      borderWidth: 1.5,
    },
    
    // Animation
    animationDuration: 550,
    animationDurationUpdate: 750,
  }]
};
```

### Tree Data Format

```javascript
const treeData = {
  name: '中心主题',
  children: [
    {
      name: '分支A',
      children: [
        { name: '叶子1' },
        { name: '叶子2' },
        { name: '叶子3', children: [{ name: '更深叶子' }] }
      ]
    },
    {
      name: '分支B',
      children: [
        { name: '叶子4' },
        { name: '叶子5' }
      ]
    }
  ]
};
```

### Node Style Customization (by Level)

```javascript
// Root node highlight
function styleTreeData(node, depth) {
  const styles = [
    { // Root node
      itemStyle: { color: '#3B82F6', borderColor: '#2563EB', borderWidth: 2 },
      label: { fontSize: 18, fontWeight: 'bold', color: '#fff',
               backgroundColor: '#3B82F6', borderRadius: 6, padding: [8, 16] }
    },
    { // Level 1 branches
      itemStyle: { color: '#60A5FA', borderColor: '#3B82F6' },
      label: { fontSize: 15, fontWeight: 600, color: '#1E40AF',
               backgroundColor: '#EFF6FF', borderColor: '#3B82F6',
               borderWidth: 1.5, borderRadius: 6, padding: [6, 14] }
    },
    { // Level 2
      itemStyle: { color: '#93C5FD', borderColor: '#60A5FA' },
      label: { fontSize: 13, color: '#1E40AF',
               backgroundColor: '#F0F7FF', borderColor: '#93C5FD',
               borderWidth: 1, borderRadius: 4, padding: [4, 10] }
    },
    { // Level 3+ leaves
      itemStyle: { color: '#BFDBFE', borderColor: '#93C5FD' },
      label: { fontSize: 12, color: '#475569', padding: [3, 8] }
    }
  ];
  
  const style = styles[Math.min(depth, styles.length - 1)];
  Object.assign(node, style);
  
  if (node.children) {
    node.children.forEach(child => styleTreeData(child, depth + 1));
  }
}

styleTreeData(treeData, 0);
```

### Left-Right Distribution (Large Tree Mode)

When branches ≥ 5, use two trees for left-right expansion:

```javascript
function splitTree(data) {
  const children = data.children || [];
  // Alternate assignment by subtree size
  const sorted = children.map((c, i) => ({ c, w: countNodes(c), i }))
    .sort((a, b) => b.w - a.w);
  const left = [], right = [];
  let lw = 0, rw = 0;
  sorted.forEach(({ c }) => {
    if (lw <= rw) { left.push(c); lw += countNodes(c); }
    else { right.push(c); rw += countNodes(c); }
  });
  return {
    left: { name: data.name, children: left },
    right: { name: data.name, children: right }
  };
}

function countNodes(node) {
  if (!node.children) return 1;
  return 1 + node.children.reduce((s, c) => s + countNodes(c), 0);
}

// Dual tree series
const { left, right } = splitTree(treeData);
const option = {
  series: [
    { type: 'tree', data: [right], orient: 'LR', left: '50%', width: '45%', /* ... */ },
    { type: 'tree', data: [left], orient: 'RL', right: '50%', width: '45%', /* ... */ },
  ]
};
```

### Recommended Canvas Size

| Node Count | Width | Height |
|--------|------|------|
| ≤ 15 | 900px | 500px |
| 16-30 | 1200px | 600px |
| 31-60 | 1600px | 800px |
| 60+ | 2000px | 1000px |

---

## Template 6: Relationship / Force-Directed Graph

**ECharts graph suits process relationships, org charts, knowledge graphs** — nodes auto-repel to avoid overlap, connectors auto-bind, supports categorical coloring.

### Basic Usage

```javascript
const option = {
  tooltip: {},
  legend: [{ data: categories.map(c => c.name) }],
  series: [{
    type: 'graph',
    layout: 'force',     // Force-directed auto layout
    
    // Force model params (controls repulsion and attraction)
    force: {
      repulsion: 300,    // Repulsion force (higher = more spread out, recommended 200-500)
      gravity: 0.1,      // Gravity (prevents nodes from flying too far)
      edgeLength: [100, 200],  // Edge length range
      layoutAnimation: true,
    },
    
    roam: true,          // Allow drag and zoom
    draggable: true,     // Allow dragging nodes
    
    // Nodes
    data: nodes,
    // Edges
    links: links,
    // Categories (for coloring)
    categories: categories,
    
    // Labels
    label: {
      show: true,
      position: 'right',
      fontSize: 12,
      fontFamily: 'PingFang SC, SimHei, sans-serif',
    },
    
    // Connector style
    lineStyle: {
      color: 'source',   // Edge color follows source node
      curveness: 0.3,    // Curvature
      width: 1.5,
    },
    
    // Highlight effect
    emphasis: {
      focus: 'adjacency',   // Highlight adjacent nodes on hover
      lineStyle: { width: 3 },
    },
  }]
};
```

### Data Format

```javascript
const categories = [
  { name: '核心系统', itemStyle: { color: '#3B82F6' } },
  { name: '数据层', itemStyle: { color: '#10B981' } },
  { name: '应用层', itemStyle: { color: '#F59E0B' } },
];

const nodes = [
  { name: 'API Gateway', category: 0, symbolSize: 40 },
  { name: 'User Service', category: 0, symbolSize: 30 },
  { name: 'MySQL', category: 1, symbolSize: 35 },
  { name: 'Redis', category: 1, symbolSize: 28 },
  { name: 'Web App', category: 2, symbolSize: 32 },
];

const links = [
  { source: 'API Gateway', target: 'User Service' },
  { source: 'User Service', target: 'MySQL' },
  { source: 'User Service', target: 'Redis' },
  { source: 'Web App', target: 'API Gateway' },
];
```

### Flowchart Mode (Fixed Layout)

When you don't want force-directed auto-layout, fix node positions:

```javascript
const option = {
  series: [{
    type: 'graph',
    layout: 'none',  // Fixed layout, positions determined by x/y
    data: [
      { name: '开始', x: 300, y: 50, symbolSize: 40, 
        itemStyle: { color: '#EFF6FF', borderColor: '#3B82F6', borderWidth: 2 } },
      { name: '处理', x: 300, y: 200, symbolSize: 35 },
      { name: '判断', x: 300, y: 350, symbolSize: 35,
        symbol: 'diamond',
        itemStyle: { color: '#FFF7ED', borderColor: '#F59E0B', borderWidth: 2 } },
      { name: '结束', x: 300, y: 500, symbolSize: 40 },
    ],
    links: [
      { source: '开始', target: '处理' },
      { source: '处理', target: '判断' },
      { source: '判断', target: '结束', label: { show: true, formatter: '通过' } },
    ],
    lineStyle: { color: '#94A3B8', width: 2, curveness: 0 },
    edgeSymbol: ['', 'arrow'],
    edgeSymbolSize: [0, 10],
  }]
};
```

---

## ECharts vs Other Frameworks

| Capability | ECharts | Plotly | Chart.js |
|------|---------|--------|----------|
| Canvas rendering (big data) | ✅ Millions | ❌ SVG-based | ✅ But limited |
| Chinese docs | ✅ Official | ❌ English | ❌ English |
| Candlestick | ✅ Built-in | ❌ Plugin needed | ❌ None |
| Maps | ✅ Built-in China map | ✅ mapbox | ❌ None |
| 3D Charts | ✅ echarts-gl | ✅ Built-in | ❌ None |
| No Node.js needed | ✅ CDN import | ❌ Needs plotly.js | ✅ CDN |
| Server-side rendering | ✅ node-echarts | ✅ orca | ✅ chartjs-node |
