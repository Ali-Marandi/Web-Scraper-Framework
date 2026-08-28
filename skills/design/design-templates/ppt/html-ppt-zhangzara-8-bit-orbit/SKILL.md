---
name: html-ppt-zhangzara-8-bit-orbit
description: 8-Bit Orbit — 像素艺术霓虹街机 × 深海军蓝。任何应该感觉像凌晨 2 点 CRT 屏幕的 deck：cyberpunk / gaming / web3 / indie dev tools / hackathon demo。
visibility: public
mode: template
carrier: deck
scenario: marketing
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个像素风 PPT"
  - "做个赛博朋克 deck"
  - "8-bit-orbit"
  - "zhangzara-8-bit-orbit"
  - "8-Bit Orbit"
  - "retro-tech"
  - "霓虹街机"
  - "gaming pitch"
  - "hackathon demo"
  - "html deck"
  - "html slides"
  - "zhangzara"
od:
  upstream: "https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/8-bit-orbit"
  upstream_license: MIT
  preview:
    type: html
    entry: pattern.html
  design_system:
    requires: false
  speaker_notes: false
  animations: false
---

# 8-Bit Orbit

> Pixel-art neon arcade aesthetic on a deep navy void.

A single self-contained HTML deck — typography, palette, decorative system,
and slide vocabulary are all tuned together. Mixing layouts across templates
breaks the system; stay inside this one.

## At a glance

- **Scheme:** dark
- **Formality:** low
- **Density:** medium
- **Slides in demo:** 10

## Best for

Anything that should feel like a CRT screen at 2am: cyberpunk, gaming, web3, indie dev tools, hackathon demos. Just as good for a tech talk that wants to lean into nostalgic-digital craft, a synthwave brand deck, or a creative review that wants to feel like a console.

## Avoid for

Contexts where the dark neon palette would actively work against the message — quiet institutional finance disclosures, healthcare patient-facing materials, traditional luxury.

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
<artifact identifier="zhangzara-8-bit-orbit" type="text/html" title="Deck Title">
<!doctype html>
<html>...</html>
</artifact>
```

## Source & license

Vendored from upstream MIT-licensed
[`zarazhangrui/beautiful-html-templates`](https://github.com/zarazhangrui/beautiful-html-templates/tree/main/templates/8-bit-orbit).

The full upstream MIT license text — including the original copyright notice — ships in this skill at
[`LICENSE`](./LICENSE) and must be redistributed alongside any copy of `pattern.html`,
`template.json`, or any vendored `assets/` runtime. See `template.json` for the upstream metadata snapshot.
