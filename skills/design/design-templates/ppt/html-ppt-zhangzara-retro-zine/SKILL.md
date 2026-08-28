---
name: html-ppt-zhangzara-retro-zine
description: Retro Zine — 米色纸 + 绿色 accent + Bebas Neue + Caveat：HTML 形式的 riso 印刷 zine。任何应该感觉印刷 / lo-fi / 手作的 deck：独立 zine 与刊物 / 音乐艺术品牌 / 创作者作品集 / 小批量手作发布 / 社区 deck。
visibility: public
mode: template
carrier: deck
scenario: marketing
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个 riso 风 PPT"
  - "做个独立刊物 deck"
  - "做个 zine 风演讲稿"
  - "retro-zine"
  - "zhangzara-retro-zine"
  - "Retro Zine"
  - "crafted"
  - "lo-fi"
  - "indie zine / publication"
  - "music or arts brand"
  - "html deck"
  - "html slides"
  - "zhangzara"
od:
  upstream: "https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/retro-zine"
  upstream_license: MIT
  preview:
    type: html
    entry: pattern.html
  design_system:
    requires: false
  speaker_notes: false
  animations: false
---

# Retro Zine

> Beige paper with green accent and Bebas Neue + Caveat: a riso-printed zine in HTML form.

A single self-contained HTML deck — typography, palette, decorative system,
and slide vocabulary are all tuned together. Mixing layouts across templates
breaks the system; stay inside this one.

## At a glance

- **Scheme:** light
- **Formality:** medium-low
- **Density:** medium
- **Slides in demo:** 10

## Best for

Anything that should feel printed, lo-fi, and crafted: indie zines and publications, music / arts brands, creator portfolios, small-batch craft launches, community decks. Also a great underdog choice for tech, research, or business decks that want a riso-print warmth instead of digital polish.

## Avoid for

Contexts that demand digital-native polish or fast modern-tech energy — the layered zine aesthetic intentionally feels handmade.

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
<artifact identifier="zhangzara-retro-zine" type="text/html" title="Deck Title">
<!doctype html>
<html>...</html>
</artifact>
```

## Source & license

Vendored from upstream MIT-licensed
[`zarazhangrui/beautiful-html-templates`](https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/retro-zine).

The full upstream MIT license text — including the original copyright notice — ships in this skill at
[`LICENSE`](./LICENSE) and must be redistributed alongside any copy of `pattern.html`,
`template.json`, or any vendored `assets/` runtime. See `template.json` for the upstream metadata snapshot.
