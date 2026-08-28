---
name: parchment
description: Warm editorial, print-leaning document design system — parchment background, single ink-blue accent, serif-led hierarchy (LXGW WenKai for Chinese, Charter for English). For résumés, reports, white papers, letters, and editorial reading pages that should feel authored and published. Not a product-UI / component system.
license: MIT
metadata:
  author: adapted from Kami (tw93), OFL/MIT sources
---

# Parchment Design System Skill (Document / Editorial)

## Mission
You are a design-system guideline author for **Parchment**, a warm editorial system for formal and long-form documents. Produce guidance that makes a document read as authored and published, not generated.

## Brand
Parchment is a print-leaning editorial system: a calm parchment ground, one restrained ink-blue accent, and a serif-led hierarchy. It suits résumés, one-pagers, reports, white papers, letters, and editorial reading pages — documents meant to be read and printed (A4 / PDF), not dense interactive product UI.

## Style Foundations
- Visual style: editorial, formal, print-leaning, warm, content-first
- Typography scale: 12/14/16/18/22/26/36 | Fonts: primary=LXGW WenKai Screen (CN), display=Charter (EN), mono=JetBrains Mono | weights=400, 500
- Color palette: parchment surface #f5f4ed / ivory #faf9f5, ink tiers near-black #141413 / olive #504e49 / stone #6b6a64, single accent ink-blue #1B365D
- Spacing scale: 6/12/16/24/32/48
- Page: A4, ~14mm/16mm margins, real pagination, print-color-adjust: exact

## Writing Tone
calm, precise, editorial, professional, low-jargon

## Rules: Do
- keep a warm parchment ground; never pure white
- lead with serif hierarchy (size / weight 500 / space), not boxes and cards
- use the single ink-blue accent for rules, headers, emphasis — and nothing else
- hold a controlled text measure; let margins and whitespace pace the reading
- paginate for print (A4), with deliberate page breaks
- give figures/tables captions and real or clearly-marked sample data
- load the Chinese serif online via the @import in DESIGN.md

## Rules: Don't
- avoid a second accent color competing with the ink-blue
- avoid web-y card grids, bento layouts, gradient meshes, neon, glows
- avoid emoji as icons
- avoid invented data, fake metrics, fake citations
- avoid full-page-width body lines and edge-to-edge cramming
- avoid synthetic bold; use weight 500 for emphasis

## Expected Behavior
- This is a document/editorial system: optimize for reading and print, not for interaction states.
- When uncertain, prioritize legibility, hierarchy, and whitespace over decoration.
- Keep one serif per page; one accent; warm ground.
- It pairs naturally with the content-page scenario: content-page handles structure and reading rhythm, Parchment supplies the visual character.

## Best For
- résumés, one-pagers, formal letters
- reports, white papers, long-form documents, equity/research reports
- editorial reading pages, public-account long reads that want a printed, literary feel

## Not For
- product UI, dashboards, admin panels, data-dense interfaces (use a UI-oriented style)
- marketing landing pages, loud commercial launches
- anything where interaction/animation is the point

## Quality Gates
- parchment ground present; no pure-white page
- exactly one accent (ink-blue); no competing color
- serif hierarchy reads without relying on boxes
- text measure controlled; whitespace deliberate
- Chinese serif actually loaded (@import), with system-serif fallback
- data is real or clearly marked sample
