---
name: project-brief
description: Notebook-collage weekly digest template — spiral-bound reporter's notebook aesthetic with cobalt tape, mint folder tab, binder clip, receipt block, ruled baseline grid; built for AI-product / team / design weekly digests delivered as a downloadable high-res page.
visibility: public
mode: template
carrier: long-form-article
scenario: weekly-digest
pattern_source: 清言周报-VOL18-notebook.html
source_priority: skill-first
triggers:
  - "做个 notebook 周报"
  - "AI 团队周报"
  - "胶带便签风周报"
  - "笔记本拼贴报告"
  - "活页夹周报"
---

# Project Brief Template

Use this template for **weekly / periodic digests** that should feel like a hand-assembled reporter's notebook — issue-numbered, taped, clipped, ruled, with a clear physical metaphor.

## Use When

- The artifact is a **recurring digest** (周报 / VOL.NN / Issue N) with multiple grouped entries.
- Sections include: new features, optimizations, bug fixes, links, notes — i.e. a changelog-shaped narrative.
- The voice is product-team or editorial-team-internal, not corporate.
- The deliverable will be exported / shared as a high-res image or PDF, not just a scrolling page.

## Avoid When

- The content is a one-off announcement (use a social card or blog-post).
- The audience expects a corporate formal report — this is intentionally crafty and warm.
- The user wants a presentation / deck (use `ppt/`).
- The content is a marketing landing — wrong carrier entirely.

## Required Reading

Read this `SKILL.md` first. Do **not** read `清言周报-VOL18-notebook.html` by default.

Read the pattern only when you need concrete geometry — spiral hole spacing, tape angle and deckle, binder-clip placement, receipt-grid pattern, the 31px ruled baseline. Extract patterns; do not copy placeholder issue numbers, dates, feature names, or class names wholesale.

## Design Strategy

Lock the issue's spine before placing decoration:

1. **Masthead** — logo + date strip + 1-paragraph intro.
2. **Issue mark** — cobalt tape with VOL.NN + binder clip.
3. **Table of contents** — three-column grid pointing to numbered sections.
4. **Sections** — each with a kicker (uppercase Spanish / English label) + Chinese title + indexed entries.
5. **One "physical" highlight block** — receipt for optimizations, taped Polaroid for a feature, mint folder tab for an announcement.
6. **Closing lockup + colophon** — QR / ticket / page-number metadata.

Each issue should follow the same spine — that's how a weekly builds identity over time.

## Layout Bias

Prefer:

- mixed serif (FlyFlowerSong / Noto Serif SC) + sans (Noto Sans SC) + mono (JetBrains Mono) — each carries a role
- ruled baseline grid for body copy; entries align to it
- dashed dividers between entries, not solid rules
- one or two "physical" elements per page (tape / clip / receipt / folder tab) — not all of them at once
- index numbers (01 / 02 / 03) on entries; uppercase Latin kickers above CJK section titles

Avoid:

- emoji icons (the physical metaphor already does the warmth work)
- glossy gradients, drop shadows on every element, plastic stickers
- forcing every entry into the same card shape — the charm is in varied physical props
- copying the cobalt blue / mint green palette verbatim if the brand has its own colors — keep the metaphor, retheme the palette

## Platform / Size

A4-portrait-leaning long page, designed to render as a single tall artifact (image / PDF). Not optimized for mobile feeds; if the user wants a mobile-shareable version, export sections as separate social cards.
