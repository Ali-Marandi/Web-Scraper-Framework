---
name: technique-library
description: Advanced front-end technique selection reference for motion, 3D, shaders, data visualization, and high-cost visual effects. This is a horizontal craft reference, not a routing target.
mode: reference
type: horizontal-craft
applies_to:
  - landing-page
  - prototype
  - portfolio
  - info-interactive
  - deck
  - web-tool
avoid_for:
  - static export cards unless explicitly animated
  - text-heavy editorial reading experiences
---

# Technique Library

A reference of advanced techniques that can make a web artifact more effective, and **when**
each is worth using. Artifact skills consult this when an effect would genuinely improve the
result. It is not a scenario and not a routing target — a user asks for "a landing page with
rich scroll storytelling", not "a GSAP". The artifact skill (e.g. `landing-page.md`) decides
the form and intent, then reaches here for the implementation technique.

## How to use this

- Only reach for a technique when it serves comprehension, emotion, or the product goal.
  Default to simple CSS; escalate to a library only when the effect earns its weight.
- Never add a technique for novelty. Motion/3D that doesn't help the message is noise — and a
  cost in load, accessibility, and maintenance.
- Always pair an advanced technique with `prefers-reduced-motion` handling and a sensible
  no-JS / fallback state.
- Prefer CDN includes consistent with the artifact environment; keep dependencies minimal.

### Not every scenario should use this — match technique to intent

| Scenario | What it should pull (if anything) |
|----------|-----------------------------------|
| landing-page | full range — motion/3D/shader serve conviction and impact |
| prototype | motion/transitions for realistic interaction; 3D/device mockups when relevant |
| portfolio | optional motion/3D when craft is the message; restrained for résumé/text-led profiles |
| info-interactive | **interactive data-visualization is the point** — use diagram/chart interaction that aids comprehension (linked highlighting, filter/recompare, draggable/zoomable graphs, slider-driven models); avoid only *decorative* motion/3D that doesn't explain |
| content-page | none — reading wants calm; at most subtle CSS reveals |
| social-card | none — static export graphics |
| web-tool | none beyond simple CSS — single-task utility, keep it light |
| deck | none beyond restrained CSS — decks favor clarity over spectacle |

The rule of thumb: the more a scenario is about *impact/craft* (landing, creative portfolio),
the more these techniques help; the more it is about *reading or understanding* (content-page,
info-interactive), the more decorative effects hurt — there, only data viz qualifies.

---

## Motion & scroll

### CSS transitions / animations (default)
First choice for hovers, state changes, simple reveals, micro-interactions. No library needed.
Reach further only when CSS genuinely can't express the effect.

### GSAP (GreenSock)
For complex, sequenced, or scroll-driven motion that CSS handles poorly.
- **GSAP core + Timeline** — choreographed multi-step sequences, precise easing, coordinated
  animations.
- **ScrollTrigger** — scroll-linked storytelling: pin sections, scrub animations to scroll,
  reveal-on-enter, parallax. The main reason to choose GSAP for landing pages and explainers.
- Use when: a landing page needs narrative scroll, a product reveal, or staged emphasis.
- Avoid when: a simple fade/slide on scroll (use CSS + IntersectionObserver instead).

### Lottie
For designer-authored vector animations (exported from After Effects) — mascots, rich loaders,
illustrative loops. Use when you have/need polished illustrative motion; avoid for simple UI motion.

---

## 3D & shaders

### Three.js
For real 3D: product showcases in 3D, spatial scenes, interactive 3D objects.
- Use when: a hero needs a rotatable 3D product, a spatial concept, or depth that 2D can't convey.
- Avoid when: a flat illustration or a CSS 3D transform would do. 3D is heavy — justify it.
- Note: in constrained runtimes some Three.js addons/geometries may be unavailable; prefer core
  geometries and verify availability.

### Shaders (GLSL / WebGL)
For custom visual effects: generative backgrounds, fluid/gradient fields, particle systems.
- Use when: a distinctive atmospheric background or effect is core to the design direction.
- Avoid when: a CSS gradient or static image achieves the same impression. High cost, niche payoff.

---

## Data visualization

For quantitative, relational, or temporal information. **This overlaps with
`info-interactive.md`** — when the deliverable's *purpose* is expressing information (report,
data story, explainer), route to `info-interactive.md` and use these techniques inside it. Use
them here when a scenario (e.g. landing page, dashboard) needs a chart as a supporting element.

### Inline SVG (default for simple charts)
Hand-built bar/line/donut charts as inline SVG. First choice for a few simple, static charts —
no dependency, full control, crisp export.

### D3.js
For complex, custom, or data-driven visualizations: custom scales, force/network graphs,
hierarchical layouts, bespoke interactive charts that off-the-shelf libraries can't express.
- **Use when:** the visualization is interactive or custom beyond standard chart types — this is
  the right tool for the force/relationship graphs, zoomable hierarchies, and bespoke explorable
  charts in the Interactive diagrams section below. Don't shy away from it when the diagram genuinely
  needs force layout, hierarchical layout, or custom scales.
- **Avoid when:** a standard bar/line/pie suffices (inline SVG or a chart library is lighter), or
  when hand-written SVG + vanilla JS already covers the interaction (see skeletons below — many
  linked-highlight / slider-model diagrams don't need D3 at all).

### Chart libraries (Chart.js / Recharts, when supported)
For standard chart types quickly. Use when standard charts are enough and a library is available
in the environment; otherwise fall back to inline SVG.

Visualization integrity (always): correct axes/units/scales; no misleading truncation; readable
labels; the title states the insight; never invent data.

### Interactive diagrams — go past "expand / click-to-show"

For info-interactive (and any explainer), "click to expand" is the *lowest* tier of interaction.
When the information is relational, comparative, sequential, or model-like, reach for a real
interactive diagram. The point is comprehension, not spectacle — but a static list with a toggle
is usually under-delivering for these shapes. Tiers:

```text
L1 (baseline)  expand / collapse / click-to-reveal      ← don't stop here for explore-class info
L2             linked highlighting, filter-and-recompose, hover-to-trace
L3             draggable / zoomable / slider-driven models that recompute live
```

Match shape → interaction (and grab a skeleton below):

| Information shape | Interactive move |
|---|---|
| relationship / network | hover a node → highlight its neighbours + dim the rest; click → detail |
| architecture / dependency | click a layer/component → trace and highlight its dependency path |
| sequence / process | scrub or step through; the active step explains itself |
| comparison | toggle a dimension → matrix/chart re-sorts or re-weights live |
| model / sensitivity | slider/input → numbers, chart, and the written takeaway update together |
| time / evolution | brush/zoom a range → detail and summary update for that window |

Paste-ready skeletons (vanilla JS + SVG/HTML; reduced-motion safe; escalate to D3 only when the
layout maths genuinely needs it):

**1. Linked-highlight relationship graph** (hover highlights neighbours)
```html
<svg id="graph" viewBox="0 0 400 300" role="img" aria-label="Relationship graph"></svg>
<script>
const nodes=[{id:'a',x:80,y:80,label:'Auth'},{id:'b',x:220,y:60,label:'API'},
  {id:'c',x:300,y:180,label:'DB'},{id:'d',x:120,y:210,label:'Cache'}];
const edges=[['a','b'],['b','c'],['b','d']];
const svg=document.getElementById('graph'), adj={};
edges.forEach(([s,t])=>{(adj[s]=adj[s]||[]).push(t);(adj[t]=adj[t]||[]).push(s);});
edges.forEach(([s,t])=>{const a=nodes.find(n=>n.id===s),b=nodes.find(n=>n.id===t);
  const l=document.createElementNS(svg.namespaceURI,'line');
  l.setAttribute('x1',a.x);l.setAttribute('y1',a.y);l.setAttribute('x2',b.x);l.setAttribute('y2',b.y);
  l.setAttribute('stroke','#bbb');l.dataset.edge=s+'-'+t;svg.appendChild(l);});
nodes.forEach(n=>{const g=document.createElementNS(svg.namespaceURI,'g');g.tabIndex=0;
  g.innerHTML=`<circle cx="${n.x}" cy="${n.y}" r="20" fill="#3b82f6"/>
    <text x="${n.x}" y="${n.y+4}" text-anchor="middle" font-size="10" fill="#fff">${n.label}</text>`;
  const focus=()=>{const near=new Set([n.id,...(adj[n.id]||[])]);
    svg.querySelectorAll('circle').forEach((c,i)=>c.style.opacity=near.has(nodes[i].id)?1:.25);
    svg.querySelectorAll('line').forEach(l=>{const[s,t]=l.dataset.edge.split('-');
      l.setAttribute('stroke',s===n.id||t===n.id?'#3b82f6':'#eee');});};
  const reset=()=>{svg.querySelectorAll('circle').forEach(c=>c.style.opacity=1);
    svg.querySelectorAll('line').forEach(l=>l.setAttribute('stroke','#bbb'));};
  g.addEventListener('mouseenter',focus);g.addEventListener('focus',focus);
  g.addEventListener('mouseleave',reset);g.addEventListener('blur',reset);svg.appendChild(g);});
</script>
```

**2. Slider-driven explorable model** (input → chart + takeaway recompute)
```html
<label>Monthly users <input id="u" type="range" min="100" max="10000" value="2000" step="100"></label>
<p id="out"></p><svg id="bars" viewBox="0 0 320 120"></svg>
<script>
const u=document.getElementById('u'),out=document.getElementById('out'),bars=document.getElementById('bars');
function render(){const users=+u.value, revenue=users*12, cost=2000+users*3, profit=revenue-cost;
  out.textContent=`At ${users.toLocaleString()} users: revenue ¥${revenue.toLocaleString()}, `
    +`profit ¥${profit.toLocaleString()} — ${profit>0?'profitable':'below break-even'}.`;
  const data=[['Revenue',revenue],['Cost',cost],['Profit',Math.max(profit,0)]],max=Math.max(...data.map(d=>d[1]),1);
  bars.innerHTML=data.map((d,i)=>{const h=d[1]/max*80;return `
    <rect x="${20+i*100}" y="${100-h}" width="60" height="${h}" fill="${['#3b82f6','#ef4444','#22c55e'][i]}"/>
    <text x="${50+i*100}" y="115" text-anchor="middle" font-size="9">${d[0]}</text>`;}).join('');}
u.addEventListener('input',render);render();
</script>
```

**3. Step-through process** (active step explains itself) and **4. Toggle-recompose comparison**
follow the same pattern: state in a variable, one `render()` that redraws SVG/HTML from state, and
controls that mutate state then call `render()`. Keep state in the DOM (classes/attributes) so it
stays editable and inspectable.

Rules for all of the above: every control has a visible output change and keyboard access; provide
a static-readable fallback (the default render must already make sense); honor `prefers-reduced-motion`;
never fake a control. Use D3 only when force layout, hierarchical layout, or custom scales exceed
what hand-written SVG can manage.

---

## Selection summary

| Need | Default | Escalate to |
|------|---------|-------------|
| hover / state / simple reveal | CSS | — |
| scroll-driven storytelling | CSS + IntersectionObserver | GSAP ScrollTrigger |
| choreographed multi-step motion | CSS | GSAP Timeline |
| illustrative vector animation | — | Lottie |
| real 3D / spatial | CSS 3D transforms | Three.js |
| custom atmospheric effect | CSS gradient/image | Shaders (WebGL) |
| a few simple charts | inline SVG | — |
| standard charts, fast | inline SVG | Chart.js / Recharts |
| custom / interactive data viz | inline SVG | D3.js |

Every escalation must (1) serve the goal, (2) ship reduced-motion handling, (3) justify its weight.
