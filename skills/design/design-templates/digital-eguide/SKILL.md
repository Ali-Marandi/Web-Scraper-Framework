---
name: digital-eguide
description: Premium "digital e-guide" template family — two patterns sharing a metadata-rich, editorial-archive identity: an infinite 3D-canvas portfolio (case/) for designer 作品集, and a 12-slide horizontal field-notes carousel (social-carousel.html) for long-form knowledge series.
visibility: public
mode: template
carrier: web-page
scenario: portfolio-and-guide
pattern_source: case（无限画布：作品集）/case/index.html, social-carousel.html
source_priority: skill-first
triggers:
  - "做个 e-guide 电子手册"
  - "3D 画布作品集"
  - "field notes 横滚"
  - "知识系列横滚"
  - "高端作品集"
  - "无限画布作品集"
---

# Digital E-Guide Template

Use this template family for **premium, metadata-rich, exploratory digital artifacts** — designer portfolios, archival photo series, knowledge guides — that reward slow browsing instead of fast scrolling.

This template ships two variants. Pick before building.

## Variants

### `case/` — Infinite-canvas portfolio (作品集)

> On-disk path: `case（无限画布：作品集）/case/index.html`

- A Miro-like 3D-cylindrical canvas of 18 tiles you drag, zoom, and click to open case detail pages.
- Use for: designer 作品集, studio portfolio, photographer archive, case-study lobby.
- Distinctive moves: Three.js-style cylindrical projection, drag inertia, gold/dark glass UI, hash-routed detail pages, "Works / About / Resume" nav.
- Companion generator: see top-level `../vr-canvas/` template (modern frontmatter version).

### `social-carousel.html` — 12-frame field-notes carousel

- A 50/50 photo + metadata carousel with 12 horizontal slides, progress bar, slide counter, scaling-on-focus serif title.
- Use for: digital ebook chapter navigation, photography series, "12 lessons from the field"-style guides, museum/archive viewer.
- Distinctive moves: Fraunces italic display that scales on active slide, Inter metadata, film-frame photo marks, 50/50 desktop split that stacks on mobile.

## Use When

- The user wants a **considered, curatorial** browsing experience — not a marketing site, not a social card.
- Every item carries metadata (year, location, technique, brand, tags) and that metadata is part of the design.
- The audience is designers, creators, or curious readers who will spend minutes, not seconds.

## Avoid When

- The artifact is a fast-conversion marketing page (use `saas-landing/`).
- The content has no per-item metadata to display (the template will feel empty).
- The user actually wants a flat blog index, dashboard, or social-card pack.
- Mobile is the dominant channel and rich interaction would degrade — both variants are desktop-leaning.

## Required Reading

Read this `SKILL.md` first. Do **not** read `case/index.html` or `social-carousel.html` by default.

Read the chosen variant only when you need concrete interaction geometry — drag inertia easing, cylinder radius, slide-scale-on-focus curve, breakpoint behavior. Extract patterns; do not lift Three.js code, placeholder project names, or photo URLs wholesale.

## Design Strategy

Pick the variant from the **interaction contract**, not the topic:

- "Let me wander a room of work" → **case/**
- "Walk me through 8–14 numbered entries" → **social-carousel.html**

Then commit to the metadata schema up front (year / category / location / brand …). The template only sings when every entry carries the same set of labels.

## Layout Bias

Prefer:

- one dominant image per entry, full-bleed inside its frame
- metadata in mono / small-caps / Latin to contrast the serif display
- a single warm accent (gold, rust) over a dark or paper ground
- smooth eased motion (cubic-bezier), no bouncy springs
- generous negative space — the artifact's premium feel comes from restraint

Avoid:

- stacking multiple thumbnails per slide / tile (kills the curatorial feel)
- bright neon accents, gradient meshes, sticker decorations
- pop-in animations on every element — choose one motion idiom and hold it
- treating metadata as a footnote — surface it equally with the image
