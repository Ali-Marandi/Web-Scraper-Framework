---
name: link-and-proof
description: Link, CTA destination, placeholder, proof provenance, source-labeling, and fake-claim prevention rules.
mode: reference
platform: web
scenario: horizontal-craft
preview:
  type: none
default_for:
  - proof provenance
  - links
  - dead links
  - placeholder links
  - fake proof
  - CTA destinations
fidelity: system
---

# Link and Proof

Use this file whenever an artifact contains links, CTAs, proof-like claims, metrics, logos, testimonials, awards, press mentions, or case studies.

---

## Dead link protocol

Never use:

```html
<a href="#">...</a>
<a href="javascript:void(0)">...</a>
<button onclick="">...</button>
<button onclick="alert('todo')">...</button>
<button onclick="console.log('clicked')">...</button>
```

Use one of:

```html
<a href="#contact">Contact</a>
<button type="button" data-action="open-demo">Open demo</button>
<a aria-disabled="true" data-placeholder-link>Link pending</a>
```

Rules:

- navigation uses `<a href="...">`
- actions use `<button type="button">`
- if the CTA destination is unknown, use a real section anchor, disabled placeholder, or ask if it materially matters
- no fake external links
- no placeholder JavaScript logic

---

## Proof-like content

Proof-like content includes:

- percentages
- money
- revenue
- market size
- user counts
- customer counts
- testimonials
- awards
- pricing
- logos
- case studies
- benchmarks
- “trusted by” claims
- press mentions
- rankings
- dates that imply launch or traction

Allowed provenance states:

```text
user-provided
sourced
demo
placeholder
```

Recommended attribute:

```html
<span data-proof="user-provided">¥128/月</span>
<span data-proof="sourced">92%</span>
<span data-proof="demo">92% demo</span>
<span data-proof="placeholder">[填写真实满意度]</span>
```

---

## Rules

- If the user provided the number, keep it and mark it when practical.
- If a source is included in the artifact, mark it as sourced and include a source label.
- If the number is illustrative, mark it visibly as demo.
- If the number is unknown, use a placeholder.
- Do not create fake customer logos, fake testimonials, fake press quotes, fake awards, fake market reports, fake rankings, or fake growth charts.
- Decks and reports may use demo data only when clearly labeled as demo.

---

## Placeholder content

Forbidden:

```text
TODO
FIXME
待实现
lorem ipsum
placeholder text
feature one / two / three
```

Allowed when clearly labeled:

```text
[填写真实客户 Logo]
[替换为用户提供的案例]
示例数据，仅用于版式预览
Demo data — replace before publishing
```

---

## CTA destination rules

Every CTA must answer:

1. What will happen?
2. Is it navigation or an action?
3. Is the destination real, in-page, disabled, or pending?

Bad:

```html
<a href="#" class="button">立即体验</a>
```

Better:

```html
<a href="#demo" class="button">预约演示</a>
<button type="button" class="button" data-action="generate-report">生成报告</button>
<a aria-disabled="true" data-placeholder-link class="button">等待接入报名链接</a>
```

---

## Quality checks

```text
[ ] No href="#" or javascript:void(0) exists.
[ ] Every CTA has a real behavior or visible pending state.
[ ] Proof-like claims have provenance.
[ ] Demo data is visibly labeled.
[ ] No fake logos, quotes, awards, press, rankings, or case outcomes exist.
[ ] Placeholder content is bracketed or labeled, not disguised as final copy.
```
