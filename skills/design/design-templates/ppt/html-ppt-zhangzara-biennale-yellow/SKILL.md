---
name: html-ppt-zhangzara-biennale-yellow
description: Biennale Yellow — 暖羊皮纸上的太阳黄 + 靛蓝衬线 + 阳光晕染渐变。任何应该感觉像艺术双年展海报或美术馆年度方案的 deck：展览 deck / 艺术机构公告 / 设计大会手册 / 策展提案 / 文学出版物 / 工作室回顾。
visibility: public
mode: template
carrier: deck
scenario: marketing
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个双年展 deck"
  - "做个艺术机构方案"
  - "做个策展提案"
  - "biennale-yellow"
  - "zhangzara-biennale-yellow"
  - "Biennale Yellow"
  - "editorial"
  - "atmospheric"
  - "literary"
  - "exhibition or biennale"
  - "html deck"
  - "html slides"
  - "zhangzara"
od:
  upstream: "https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/biennale-yellow"
  upstream_license: MIT
  preview:
    type: html
    entry: pattern.html
  design_system:
    requires: false
  speaker_notes: false
  animations: false
---

# Biennale Yellow

> Solar yellow on warm parchment with deep indigo serif and atmospheric sun-glow gradients.

A single self-contained HTML deck — typography, palette, decorative system,
and slide vocabulary are all tuned together. Mixing layouts across templates
breaks the system; stay inside this one.

## At a glance

- **Scheme:** light
- **Formality:** high
- **Density:** medium
- **Slides in demo:** 8

## Best for

Anything that should feel like an art-biennale poster or a museum's annual programme: exhibition decks, arts-institution announcements, design conference brochures, curatorial pitches, literary publications, studio retrospectives. Equally good for any deck wanting Dutch-editorial atmosphere with an unmistakable single-color signature.

## Avoid for

Decks that need visual punch or saturated multi-color energy — the warm-paper canvas and one-yellow palette are intentionally quiet and atmospheric.

## Workflow

1. **Use `pattern.html` only as a secondary pattern reference.** Do not clone it wholesale; extract section rhythm, layout pattern, and interaction behavior, then rebuild for the current brief.
2. **Replace placeholder content** with the user's real headlines, body copy,
   numbers, names, dates, and section labels. Match existing dimensions when
   swapping image placeholders.
3. **Preserve the design system.** Never substitute fonts, recolor the palette,
   restructure the layout grid, or strip decorative elements (corner brackets,
   paper grain, geometric shapes, illustrated SVGs). They are part of the
   identity.
4. **Adjust deck length by duplicating layouts.** If the user has more content
   than the demo holds, duplicate an existing slide of the most appropriate
   layout. If less, drop slides from the bottom. Update page-number labels.
5. **Designing missing layouts:** if a slide needs a layout the template
   doesn't have, design it from scratch using the same fonts, palette,
   decorative vocabulary, spacing rhythm, and component grammar — never bail
   to a different template.
6. **Keep the navigation runtime as shipped.** If the deck ships an
   `assets/deck-stage.js` or inline keyboard handler, leave it intact.

## Output contract

Emit between `<artifact>` tags:

```
<artifact identifier="zhangzara-biennale-yellow" type="text/html" title="Deck Title">
<!doctype html>
<html>...</html>
</artifact>
```

## Source & license

Vendored from upstream MIT-licensed
[`zarazhangrui/beautiful-html-templates`](https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/biennale-yellow).

The full upstream MIT license text — including the original copyright notice — ships in this skill at
[`LICENSE`](./LICENSE) and must be redistributed alongside any copy of `pattern.html`,
`template.json`, or any vendored `assets/` runtime. See `template.json` for the upstream metadata snapshot.
