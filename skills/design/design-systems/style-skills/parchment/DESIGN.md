---
name: Parchment
colors:
  primary: "#1B365D"
  secondary: "#2D5A8A"
  success: "#16A34A"
  warning: "#D97706"
  danger: "#DC2626"
  surface: "#f5f4ed"
  text: "#141413"
  neutral: "#faf9f5"
typography:
  h1:
    fontFamily: "LXGW WenKai Screen"
    fontSize: 2.25rem
  body-md:
    fontFamily: "LXGW WenKai Screen"
    fontSize: 1rem
  label-caps:
    fontFamily: "JetBrains Mono"
    fontSize: 0.75rem
  sourceScale: "12/14/16/18/22/26/36"
  weights: "400, 500"
rounded:
  sm: 2px
  md: 4px
spacing:
  sm: 6px
  md: 12px
  sourceScale: "6/12/16/24/32/48"
---

## Overview

Warm, editorial, print-leaning document system. A calm parchment background, a single ink-blue accent, and a serif-led hierarchy give long-form and formal documents a published, authored feel — résumés, reports, white papers, letters, and editorial reading pages. Built for reading and print (A4 / PDF), not for dense product UI.

## Style Foundations

- **Visual style:** editorial, formal, print-leaning, warm, content-first
- **Typography scale:** 12/14/16/18/22/26/36
- **Typography fonts:** primary=LXGW WenKai Screen (霞鹜文楷, Chinese), display=Charter (English serif), mono=JetBrains Mono
- **Typography weights:** 400, 500 (no synthetic bold; weight 500 carries headings)
- **Color palette:** parchment surface, near-black/olive/stone ink tiers, single ink-blue accent
- **Spacing scale:** 6/12/16/24/32/48
- **Surface:** warm parchment `#f5f4ed` / ivory `#faf9f5`, never pure white
- **Page model:** A4, ~14mm/16mm margins, real pagination, `print-color-adjust: exact`
- **Body rhythm:** line-height ~1.55, controlled measure (never full-page-width lines)

## Colors

- **Primary (#1B365D):** Ink-blue accent — section rules, headers, emphasis. The only accent; never add a second.
- **Secondary (#2D5A8A):** Lighter ink-blue for links or subtle secondary emphasis.
- **Success (#16A34A):** Status only, used sparingly (e.g. changelog "added").
- **Warning (#D97706):** Status only, used sparingly.
- **Danger (#DC2626):** Status only, used sparingly.
- **Surface (#f5f4ed):** Warm parchment page background — the signature of this system.
- **Text (#141413):** Near-black body ink; secondary tier olive `#504e49`, meta tier stone `#6b6a64`.
- **Neutral (#faf9f5):** Ivory, for raised blocks / cards on the parchment ground.

## Fonts

Chinese serif loads online (no bundled font files):

```
@import url("https://cdn.jsdelivr.net/npm/cn-fontsource-lxgw-wen-kai-screen-r/font.css");
```

Stack: `"LXGW WenKai Screen", "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC", Charter, Georgia, serif`. English uses Charter first. One serif per page (`--sans: var(--serif)`); reserve JetBrains Mono for code/figures/numbers only.

When exporting to PDF, the online Chinese font may fall back to a system CJK serif; install LXGW WenKai locally if exact rendering is required, otherwise the fallback is acceptable.
