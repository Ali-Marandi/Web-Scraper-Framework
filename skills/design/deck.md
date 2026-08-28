---
name: Deck Skill
description: Design HTML-based slide decks, presentation decks, pitch decks, report decks, and narrative visual presentations.
mode: deck
platform: presentation
scenario: deck
preview:
  type: html
default_for:
  - deck
  - presentation
  - slide deck
  - pitch deck
  - product deck
  - report deck
  - strategy deck
  - workshop deck
  - 演示文稿
  - 路演材料
speaker_notes: optional
animations: optional
fidelity: high
---

# Deck Skill

Design a paged, one-screen-at-a-time presentation that carries a narrative — each slide makes
one point, and the sequence builds an argument.

Judgment, not a rulebook. Use taste. Techniques: `horizontal-craft/technique-library.md`; delivery
check: `skills/design/quality-gate.md`. For a base runtime/template, see
`skills/design/prototype-templates/` (html-ppt seed) and the Preset Template Rule in SKILL.md.

## Route elsewhere if

- it's a scrollable web page (not paged) → `landing-page.md` / `content-page.md`
- it's an interactive product → `prototype.md`

## What makes a deck succeed: one idea per slide, a story across slides

The failure mode is text-dumped slides with no narrative spine — bullet walls that should have
been a doc. So:

- **One idea per slide.** Each slide has a single takeaway, stated clearly. If a slide needs two
  points, it's two slides.
- **A narrative arc.** The deck has a beginning (problem/context), middle (argument/evidence),
  and end (ask/conclusion). Order the slides to build, not just enumerate.
- **Show, don't dump.** Visualize relationships and data; a sentence + a strong visual beats a
  paragraph. Speaker notes carry the detail, not the slide.

## The few decisions that matter

- **Deck type & tone** — pitch (persuasive, bold), report (clear, sober), strategy (structured),
  workshop (interactive). This sets density, color, and pacing.
- **Narrative spine** — the sequence of takeaways before any visuals. Get the story right first.
- **Slide rhythm** — vary slide types (statement, data, comparison, quote, section break);
  don't repeat the same layout 20 times. Use full-bleed moments for emphasis.
- **Data honesty** — charts with correct axes/units/scales; the title states the insight; never
  invent numbers.

## Non-negotiables

- One idea per slide; speaker-facing detail goes in notes, not on the slide.
- Never invent data, quotes, or metrics; charts faithful to real numbers.
- Consistent system (type scale, color, spacing) across all slides.
- No decorative emoji as icons (use SVG); no Lorem ipsum.

## Avoiding AI slop (one principle)

Catalog in `quality-gate.md`. Principle: each slide's layout serves its specific point, not a
repeated template. A title + three bullets on every slide, a generic gradient title slide,
identical icon-feature rows — reflexes. Vary with intent; when a slide feels like filler, cut it.

## Workflow

1. Define the deck type, audience, and the single ask/conclusion.
2. Write the narrative spine (the ordered takeaways) before designing slides.
3. Design slides — one idea each, varied rhythm, visuals over text; detail to speaker notes.
4. Techniques/animations from `horizontal-craft/technique-library.md` only when they aid the point; reduced-motion.
5. Quality gate before delivery; verify data honesty and one-idea-per-slide.

## References (load only when relevant)

- `horizontal-craft/chinese-typography.md` — substantial Chinese text (Mandatory Runtime Baseline).
- `horizontal-craft/icon-system.md` — when icons are used.
- `canvas-and-device.md` — slide dimensions / export sizes.
- `design-system-reference.md` — when a brand/style/template reference is given (see SKILL.md Style Routing).
- `horizontal-craft/technique-library.md` — restrained transitions only when they aid the narrative.

## Creative Context

For open-ended requests, complete `SKILL.md` Creative Context (creative_positioning,
first_impression, anti_default) before generating.

## Mandatory Final Gate

Run `quality-gate.md` as a blocking check. Must satisfy: one idea per slide; honest data/charts;
consistent system across slides; no invented numbers/quotes; no emoji-as-icons / Lorem ipsum;
visible focus and reduced-motion where interactive; non-visible Design Compliance block matching
the code. Apply `horizontal-craft/chinese-typography.md` if substantial Chinese text.

## Handoff

May continue to: `design-system-reference.md`, `design-system-generation.md`, `export.md`,
`skills/version-management/SKILL.md`, built-in selected-region edits, and local parameter handling.
