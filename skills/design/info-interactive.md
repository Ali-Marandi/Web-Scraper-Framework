---
name: Info-Interactive Skill
description: Design HTML artifacts that explain fixed bodies of information through interaction or visual explanation — interactive reports, data stories, explorable explainers, standalone flowcharts/architecture diagrams, knowledge browsers, comparison tools, timelines, maps, and filterable information pages. Interactivity serves comprehension, not product demonstration.
mode: artifact
platform: responsive-web
scenario: info-interactive
preview:
  type: html
default_for:
  - interactive report
  - data story
  - explorable explainer
  - interactive explainer
  - knowledge browser
  - knowledge set
  - filterable data page
  - interactive infographic
  - interactive timeline
  - comparison explorer
  - relationship map
  - visual explanation
  - standalone diagram
  - flowchart
  - architecture diagram
  - system map
  - process map
  - user journey map
  - relationship diagram
  - 独立流程图
  - 架构图
  - 系统关系图
  - 业务流程图
  - 用户旅程图
  - 交互式报告
  - 数据故事
  - 可交互讲解
  - 可视化解释
  - 可筛选资料
  - 交互式信息
  - 互动信息图
  - 交互式时间线
fidelity: high
---

# Info-Interactive Skill

Use this skill when the user has a **fixed body of information** — a report, dataset, concept, comparison, process, timeline, knowledge set, map, diagram, or argument — and wants readers to understand it through interaction or visual explanation.

This is not a product prototype. Interaction, when used, expresses information. It does not simulate product UI unless the product UI is the subject being explained. If the user asks for a standalone flowchart, architecture diagram, system map, or process diagram, treat it as a visual explanation artifact inside this skill — do not force unnecessary interaction.

## Standalone diagram & carrier attribution

The main router sends scenario types to their skills; this section only resolves where a **diagram**
or a mixed info+utility artifact belongs, since the same diagram can live in several carriers:

- flowchart / architecture diagram / system map / process map as the final artifact → this skill + `horizontal-craft/visual-explanation.md`
- flowchart inside a deck → `deck.md` + `horizontal-craft/visual-explanation.md`
- flowchart inside a social image/card → `social-card.md` + `horizontal-craft/visual-explanation.md`
- product prototype with a user-flow handoff → `prototype.md`

If the artifact mixes information exploration with a small utility, lead with this skill only when the primary value is understanding the information. If the primary value is producing a result, use `web-tool.md`.

---

## Core Principle

**This skill's job is to express information visually and structurally so the reader understands it by *seeing the structure*, instead of reading prose and rebuilding the structure in their head.** When the information has a shape — a process, a comparison, a hierarchy, a set of relationships, a trend, a distribution — represent that shape directly (flow, matrix, tree, node map, chart, timeline). Default assumption: **structured/visual presentation beats a wall of text** for this kind of content. Lead with the structure, not with paragraphs.

The one limit on this: only structure information that genuinely *has* structure. Content that is fundamentally linear narrative or argument is better written well (→ `content-page.md`) than chopped into a disconnected infographic. So: actively look for structure and visualize it — but don't manufacture fake structure just to have a diagram.

The chosen form must make the information easier to understand than plain text would. Use interactivity only when it adds comprehension value; a clear static SVG/HTML diagram is valid when interaction would add friction.

Every interactive element must do at least one of these:

```text
reveal detail on demand;
filter a set;
compare alternatives;
sequence a process;
change an input and update an explanation;
highlight a relationship;
reduce cognitive load through progressive disclosure.
```

If interaction only adds motion, novelty, or UI chrome, remove it.

**But don't under-deliver on interaction either.** For explore-class artifacts (interactive
reports, data stories, comparison tools, explorable models, relationship/architecture explorers),
"click to expand" or "click to show more" is the *lowest* tier and usually not enough. Push to
real interactive visualization — linked highlighting, filter-and-recompose, draggable/zoomable
graphs, slider-driven models that recompute live. See the interaction-complexity ladder and the
paste-ready skeletons in `horizontal-craft/technique-library.md` (Interactive diagrams), and match
the information shape to an interactive move there.

Exception — **standalone diagram requests stay allowed to be static.** When the user just wants a
flowchart / architecture diagram / system map, a clear static SVG is the goal; do not bolt on
draggable/zoom interaction it doesn't need (see Standalone Diagram Mode in `visual-explanation.md`).
The push for richer interaction is for explore-class artifacts, not for "draw me a diagram."

---

## Information Shape First

Before designing layout or interaction, identify the shape of the information.

| Information shape | Good artifact pattern |
|---|---|
| Hierarchy / taxonomy | collapsible outline, nested cards, knowledge tree |
| Collection / resource set | searchable/filterable grid, facets, detail drawer |
| Sequence / process | stepper, timeline, flow, state machine |
| Comparison / trade-off | matrix, before/after, toggle compare, side-by-side explorer |
| Quantity / metric | chart, KPI explanation, ranking, small multiples |
| Relationship / dependency | node map, dependency graph, linked cards |
| System inventory / architecture | architecture diagram, responsibility map, layered system map |
| Geography / route | map, schematic route, region comparison |
| Argument / evidence chain | claim → evidence → implication path |
| Model / sensitivity | adjustable input → updated explanation/result |

Use the smallest number of patterns that clarifies the information. One strong pattern is usually better than five weak ones.

---

## What makes an info-interactive artifact succeed

- **Overview first.** The reader should know what this is about before interacting.
- **Progressive depth.** Let readers drill into detail without overwhelming the first screen.
- **Representation fit.** Chart, map, flow, timeline, matrix, or filter must match the information shape.
- **Real state changes when interactive.** Controls visibly change the information, not just visual decoration.
- **Diagram clarity when static.** Nodes, arrows, grouping, and labels should explain the relationship without long prose.
- **Data honesty.** Numbers, claims, sources, and quotes are real or clearly marked demo/sample.
- **Carrier-native.** It should feel like an explorable information page, not a product dashboard, slide deck, or shrunk article.

---

## The few decisions that matter

- **Comprehension goal** — what should the reader understand or decide after using it?
- **Information shape** — hierarchy, collection, sequence, comparison, quantity, relationship, geography, argument, or model.
- **Interaction pattern** — filter, disclosure, compare, stepper, chart, map, explorable model, or relationship view.
- **Default view** — what is shown before the user touches anything?
- **Depth control** — what is summarized, what is expandable, and what is omitted?
- **Evidence treatment** — how numbers, sources, examples, and assumptions are labeled.
- **Visual explanation style** — plain analytical, editorial explainer, data-led, map-led, or diagram-led.
- **Diagram story** — for standalone diagrams, decide whether it is execution flow, system inventory, responsibility map, data flow, or dependency map before drawing.

---

## Non-negotiables

- Running JavaScript for any claimed interaction. Do not require JavaScript for a static standalone diagram.
- Every control has a comprehension purpose and a visible output change.
- No invented data, sources, statistics, quotes, rankings, or proof.
- Charts/diagrams have readable labels, units, scales, and conclusions when relevant.
- Keyboard access, visible focus, and reduced-motion fallback when motion exists.
- No placeholder handlers, fake filters, or decorative-only controls.

---

## Decision Sequence

1. Identify the information body and the reader's comprehension goal.
2. Classify the information shape.
3. Choose the minimum representation and interaction pattern from that shape. If a static diagram is clearer than interaction, choose the static diagram.
4. Define the default view, diagram story, and progressive-disclosure depth.
5. Build working interaction and faithful visual explanations.
6. Validate: does interaction make the information clearer than a static page? If not, simplify.

---

## HTML structure

Use stable markers so regions can be edited and checked.

```html
<main data-info-interactive="topic-name">
  <section data-info-section="overview">…</section>
  <section data-info-section="explorer" data-pattern="filter">…</section>
  <section data-info-section="compare" data-pattern="comparison">…</section>
  <figure data-viz="trend-chart">…</figure>
  <figure data-diagram="system-architecture" data-diagram-story="system-inventory">…</figure>
  <div data-explorable-model="cost-sensitivity">…</div>
</main>
```

Rules:

- Every `data-pattern` region must have working behavior.
- Every `data-viz` block must have labels, units, and source/demo-data handling when relevant.
- Every `data-diagram` block must have a clear diagram story, readable node labels, and meaningful connectors.
- Keep interaction state visible in DOM/classes/attributes.
- Avoid opaque generated markup that blocks selected-region edits.

---

## References, load only when triggered

- `horizontal-craft/visual-explanation.md` — standalone diagrams, flowcharts, architecture maps, process maps, charts, timelines, maps, relationship graphs, comparison visuals, explorable models, or any visual explanation component.
- `horizontal-craft/data-integrity.md` — metrics, charts, tables, rankings, market claims, benchmarks, or demo/sample data.
- `horizontal-craft/link-and-proof.md` — sources, citations, claims, proof, client logos, quotes, or external links.
- `horizontal-craft/state-coverage.md` — filters, accordions, tabs, drawers, stepper states, empty/error/loading states.
- `horizontal-craft/form-validation.md` — search boxes, inputs, filters with validation, adjustable model inputs.
- `horizontal-craft/chinese-typography.md` — substantial Chinese text or Chinese reading comfort.
- `horizontal-craft/color.md` — no design system, vague color direction, or color has to encode categories/status.
- `horizontal-craft/icon-system.md` — icons, pictograms, status symbols, category markers.
- `horizontal-craft/animation-discipline.md` — transitions, stepper motion, scroll effects, animated charts.
- `horizontal-craft/technique-library.md` — only after a representation requires advanced implementation such as D3, custom SVG, canvas, or complex interaction. Default to HTML/SVG/vanilla JS.
- `canvas-and-device.md` — fixed export surface, embedded preview, mobile-first viewport, or snapshot/social summary.
- `design-system-reference.md` — brand/style/template/DESIGN.md reference.

Do not load `export.md` or `skills/version-management/SKILL.md` as references. They are delivery/handoff flows.

---

## Final Gate

Run `quality-gate.md`. This scenario adds stricter info-interactive checks:

```text
[ ] information shape is identified and matched to representation
[ ] default view gives an understandable overview
[ ] every interaction changes what the reader can understand, compare, filter, or decide
[ ] static standalone diagrams are not forced into fake interaction
[ ] no decorative-only interaction, fake controls, or placeholder handlers
[ ] charts/diagrams follow `visual-explanation.md`
[ ] standalone diagrams have one diagram story and do not mix architecture inventory with execution sequence unless deliberately separated
[ ] data/claims are real, sourced, or clearly marked demo/sample
[ ] keyboard/focus/reduced-motion handled for interactive regions
[ ] required markers exist: data-info-section, data-pattern, data-viz, or equivalent
[ ] page still makes sense if a reader does not interact deeply
```

If these fail, simplify the interaction or representation before adding visual polish.

---

## Handoff

Use the standard Design Skill delivery, export, and version-management flow.

Add artifact-specific export targets only when the request includes:

- downloadable data / CSV / JSON;
- PDF or static report snapshot;
- embeddable chart/widget snapshot;
- standalone SVG/PNG diagram export;
- social summary image;
- source appendix or methodology notes.

If exported as an image or snapshot, keep the interactive HTML as the editable source of truth.
