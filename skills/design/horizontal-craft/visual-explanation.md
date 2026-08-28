---
name: Visual Explanation Craft
description: Design rules for diagrams, charts, visual explanations, explorable models, and information graphics. Choose representation from information shape; interaction must improve understanding.
mode: reference
platform: any
scenario: visual-explanation
preview:
  type: none
default_for:
  - diagram
  - chart
  - data visualization
  - visual explanation
  - explorable model
  - interactive report
  - flowchart
  - architecture diagram
  - system map
  - process map
  - user journey map
  - data flow diagram
  - timeline
  - comparison graphic
  - information graphic
  - 可视化解释
  - 信息图
  - 交互式解释
  - 流程图
  - 架构图
  - 系统关系图
  - 业务流程图
  - 用户旅程图
  - 数据流图
  - 时间线
fidelity: system
---

# Visual Explanation Craft

Use this file when an artifact contains a **diagram, chart, visual explanation, interactive explanation, timeline, map, relationship graph, comparison matrix, explorable model, or data/information graphic**.

This is not a style preset and not a chart-library guide. It decides **what visual form the information deserves**. Use `horizontal-craft/technique-library.md` only after the representation choice requires a specific implementation technique.

## Core Principle

Pick the representation from the information shape, not from visual habit.

Every visual explanation must answer one of these:

```text
What is the structure?
What changed over time?
What causes what?
What is larger / smaller / better / worse?
Where is it?
How does the process move?
What happens if I change this input?
What should the reader compare or decide?
```

If a chart, diagram, animation, or interaction does not change what the user can understand, decide, or do, remove it.

---

## Information Shape → Representation

| Information shape | Preferred representation | Avoid |
|---|---|---|
| Hierarchy / taxonomy | tree, nested cards, layered outline, collapsible hierarchy | force-fitting into a timeline |
| Process / workflow | flowchart, stepper, pipeline, state machine | disconnected numbered cards |
| Time / evolution | timeline, sequence strip, trend chart | unordered bullet grid |
| Comparison / trade-off | matrix, side-by-side, before/after, toggle compare | decorative radar charts with unclear axes |
| Quantity / metric | chart, KPI group, ranking, distribution, small multiples | chart without units, labels, or conclusion |
| Relationship / network | node-link, adjacency list, map of dependencies | dense spaghetti graph |
| System inventory / architecture | layered architecture map, responsibility map, component relationship diagram | pretending architecture is a time sequence |
| Geography / spatial relation | map, route, region block, schematic geography | fake map when real geography matters |
| Argument / evidence chain | claim → evidence → implication layout | pile of quotes or stats without logic |
| Explorable model | input controls that update output or explanation | sliders that only animate decoration |
| Collection / resource set | filterable grid/list, facets, search, detail drawer | endless undifferentiated cards |

Use the simplest representation that makes the information clearer.

---

## Interaction Must Earn Its Place

Use interaction only when it creates one of these values:

```text
reveal detail on demand
filter to a relevant subset
compare alternatives
advance through a sequence
change an input and see the result
highlight a relationship
reduce cognitive load by progressive disclosure
```

Interaction fails if:

```text
it only creates motion;
it hides essential information;
it makes the user click just to read basics;
it has no visible output change;
it has fake controls or placeholder handlers;
it is worse than a static chart or table.
```

Every interactive control must have visible state, keyboard access, and a clear result.

---

## Chart and Data Explanation Rules

For charts, use `horizontal-craft/data-integrity.md` together with this file.

A chart must have:

```text
clear title that states the insight or question;
visible units and labels;
honest scale and axis treatment;
legend only when needed;
source/provenance or visible demo-data label;
one main reading path.
```

Do not use:

```text
3D charts for normal data;
decorative charts with unreadable labels;
truncated axes that exaggerate difference without disclosure;
precise-looking fake data;
multiple chart types when one table would be clearer.
```

For small charts in cards, decks, or mobile surfaces, prefer fewer data points and larger labels over visual completeness.

---

## Standalone Diagram Mode

Use this mode when the user's final request is a flowchart, architecture diagram, system map, business process diagram, user journey map, dependency diagram, or data-flow diagram.

A standalone diagram may be static. Do not add filters, hover states, or animations just to make it feel interactive. Interaction is only useful when it reveals detail, switches layers, compares variants, or reduces clutter.

Before drawing, choose one diagram story:

```text
execution flow      → what happens first, next, last
system inventory    → what parts exist and how they relate
responsibility map  → who/what owns each step or component
data flow           → where data enters, transforms, and exits
dependency map      → what depends on what
journey map         → what the user/actor experiences over time
```

Do not mix incompatible stories in one diagram. If the request combines system inventory and execution sequence, split into two diagrams or separate layers.

Default complexity:

```text
4–8 primary nodes
one dominant reading path
at most two secondary branches
one clear reading direction: left-to-right, top-to-bottom, radial, or loop
no unlabeled spaghetti connectors
```

Node types should have meaning:

```text
step · decision · data · external system · actor · component · annotation
```

Relationship types should have meaning:

```text
main pipeline · optional branch · feedback loop · async signal · dependency · ownership · data movement
```

Connector rules:

- edge labels sit near the relationship, not on top of the line;
- arrows should not cross through nodes;
- line style encodes meaning, not decoration;
- avoid unnecessary connector colors;
- if labels or arrows need long explanation, simplify the diagram.

Fail a standalone diagram if it requires long prose to understand, if nodes are too small to read, if every connector looks equally important, or if system structure and execution timing are confused.

---

## Diagram Rules

### Flowcharts and Process Diagrams

- One node = one step, state, decision, actor, component, or data object — but do not mix these meanings without visual distinction.
- Keep primary flow visually dominant.
- Branches must be labeled by trigger or condition.
- Do not let arrows cross casually; if arrows cross, simplify the graph.
- For user journeys, label the user action between states.
- For system diagrams, label data/object movement between nodes.
- For architecture diagrams, separate layers or groups before drawing arrows; boxes alone are not architecture.

### Timelines

- Use time only when order or duration matters.
- Make scale explicit: chronological, phase-based, or milestone-based.
- Do not mix exact dates and vague phases without visual distinction.
- Long timelines need grouping or zoom/filter.

### Hierarchies

- Use indentation, nesting, or containment consistently.
- Parent/child relations must be obvious without reading all text.
- Avoid more than 3 visible hierarchy levels on a small canvas unless expandable.

### Comparisons

- Compare like with like.
- Keep dimensions aligned across columns or rows.
- If one side has extra criteria, explain why.
- Difference must be visible before decorative styling.

### Maps and Spatial Views

- Use a real map when geography matters.
- Use a schematic map when only relationship, route, or grouping matters.
- Do not use live map widgets for exported images unless the final export captures a stable state.

---

## Carrier-Native Behavior

The visual explanation must feel native to its final carrier.

```text
info-interactive → explorable page or standalone visual explanation, not a product demo
web-tool → controls update the result, not just decoration
prototype → diagram explains product flow, not a marketing infographic
social-card → readable image, not a shrunk webpage
standalone diagram → clear SVG/HTML diagram, not a full report page
landing-page → visual proof supports conversion, not a full report
slide/deck → one idea per slide, not a dense dashboard screenshot
```

If the carrier is fixed image, prioritize readability at export scale. If the carrier is interactive HTML, prioritize progressive exploration and accessible state changes.

---

## Implementation Guidance

Choose implementation after choosing representation.

```text
simple static chart / diagram → inline SVG or semantic HTML/CSS
simple interaction → vanilla JS + SVG/HTML state updates
complex custom data viz → D3 or canvas only when needed
standard charts → chart library only when supported and appropriate
3D / shader / WebGL → almost never for explanation; use only when spatial/physical meaning matters
```

Default to stable HTML/SVG. Do not escalate to advanced libraries for novelty.

---

## Accessibility and Resilience

- Provide text alternatives or visible summaries for charts/diagrams.
- Do not rely on color alone; use labels, shapes, patterns, or position.
- Ensure controls are keyboard reachable.
- Preserve focus-visible styling.
- Support reduced motion when animation exists.
- Keep labels readable at the target viewport/export size.
- If data is missing, say so; do not invent a complete visualization.

---

## Failure Cases

Fail the visual explanation if:

```text
[ ] representation does not match the information shape
[ ] interaction does not change understanding, decision, or task outcome
[ ] chart lacks labels, units, scale, or conclusion
[ ] diagram arrows/nodes are visually confusing
[ ] standalone diagram mixes incompatible stories such as architecture inventory and execution sequence
[ ] connectors lack semantic meaning or labels
[ ] visual form looks impressive but explains less than text would
[ ] controls are fake, hidden, or inaccessible
[ ] data/proof is invented or not marked as demo/sample
[ ] labels are too small for the final carrier
[ ] carrier mismatch: image behaves like a webpage, deck behaves like a report, tool behaves like an infographic
```

Fix by simplifying the representation before adding more decoration.
