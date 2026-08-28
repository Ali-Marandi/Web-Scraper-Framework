# Design Skill Index

This file is a directory map for the design skill package. It should not contain runtime routing rules. Runtime behavior lives in `SKILL.md`; template selection lives in `design-templates/TEMPLATE-ROUTER.md`.

## Runtime Entry

### `SKILL.md`

Main design router. It decides the primary artifact skill, output target, design-system/reference usage, template usage, horizontal craft triggers, quality gate, export, and version-management handoff.

## Active Artifact Skills

| File | Output target | Use for |
|---|---|---|
| `landing-page.md` | `responsive-html` | Product landing pages, SaaS homepages, marketing pages, waitlists, service pages. |
| `portfolio.md` | `responsive-html` | Personal sites, portfolios, creator profiles, resumes, project showcases. |
| `prototype.md` | `responsive-html` / `mobile-html` | Product prototypes, app flows, dashboards, admin panels, wireframes, UI mockups. |
| `content-page.md` | `responsive-html` | Articles, editorial pages, newsletters, public-account layouts, long-form reading pages. |
| `info-interactive.md` | `responsive-html` | Interactive reports, data stories, explorable explainers, filterable information. |
| `web-tool.md` | `responsive-html` / `mobile-html` | Single-task web tools: calculators, generators, converters, checkers, pickers, quizzes/tests, decision tools, H5/mobile tools. |
| `social-card.md` | `fixed-image` | Social cards, Xiaohongshu/RED cards, WeChat/Douyin covers, screenshot cards, KPI cards, quote cards, image-led covers, long-image card sequences. |
| `deck.md` | `html-slide-deck` | Slide decks, pitch decks, report decks, strategy decks, teaching decks, presentation-style HTML. |

Legacy note: old references to `xiaohongshu-card.md` should route to `social-card.md`; old `tool-h5.md` references should route to `web-tool.md`.

## System / Reference Skills

| File | Purpose |
|---|---|
| `design-system-reference.md` | Select and apply existing style skills, brand inspiration, open-source design systems, uploaded DESIGN.md, screenshots, or user-owned references. |
| `design-system-generation.md` | Import, extract, normalize, or persist reusable `DESIGN.md`. |
| `canvas-and-device.md` | Viewport presets, device frames, deck canvases, social-card sizes, long-image/export surfaces, fixed aspect ratios. |
| `quality-gate.md` | Final blocking delivery gate for generated or major-edited design artifacts. |
| `export.md` | Package, convert, or hand off the current artifact. |
| `skills/version-management/SKILL.md` | Parallel version-management skill for editable web entry files (`.html`, `.jsx`, `.tsx`, `.vue`); not a design reference. |

## Template Library

| File | Purpose |
|---|---|
| `design-templates/INDEX.md` | Human/model-readable template directory: what exists and where. |
| `design-templates/TEMPLATE-ROUTER.md` | Template selection rules: carrier gate, conflict handling, and when to select templates. |
| `design-templates/TEMPLATE-INDEX.json` | Machine-readable template metadata for tooling or automated retrieval. |

Template rule: choose the artifact skill first, then use `TEMPLATE-ROUTER.md` to decide whether a template applies.

## Design Systems

### `design-systems/`

Style skills and brand inspiration references. Use `design-systems/index.json` for candidate selection, then read only the matched `DESIGN.md` or style skill.

The index may contain:

- `style_skills`
- `brand_inspiration`
- selection tags such as `industry`, `product_type`, `mood`, `formality`, `density`, `scheme`, `era`, `best_for`, and `avoid_for`

Keep detailed vocabulary and selection logic inside the design-system reference files, not here.

## Horizontal Craft

Read only when the task trigger is present. `SKILL.md` contains the runtime trigger matrix.

| File | Use when |
|---|---|
| `horizontal-craft/chinese-typography.md` | Substantial Chinese text or Chinese reading comfort matters. |
| `horizontal-craft/reference/title-and-breaking.md` | Titles, covers, slides, social-card headings, or line-break-sensitive Chinese. |
| `horizontal-craft/reference/punctuation.md` | Punctuation-heavy Chinese long text. |
| `horizontal-craft/reference/text-detail.md` | Font size, line height, paragraph rhythm, dense reading surfaces. |
| `horizontal-craft/reference/fonts.md` | Font selection materially affects visual direction. |
| `horizontal-craft/reference/grid-system.md` | Reports, long images, publication-like or dense grid layouts. |
| `horizontal-craft/reference/directions.md` | Vertical text, classical Chinese, regional typography differences, or traditional layouts. |
| `horizontal-craft/color.md` | No design system or color direction is underspecified. |
| `horizontal-craft/icon-system.md` | UI/feature/nav/status icons or icon-like marks appear. |
| `horizontal-craft/accessibility.md` | Interactive or publish-ready artifacts; also part of final checks. |
| `horizontal-craft/animation-discipline.md` | Motion, transitions, scroll effects, animated storytelling. |
| `horizontal-craft/form-validation.md` | Forms, inputs, validation, signup, checkout, submission, settings. |
| `horizontal-craft/laws-of-ux.md` | Pricing, onboarding, dashboards, H5 tools, conversion or interaction-heavy flows. |
| `horizontal-craft/state-coverage.md` | Product, dashboard, form, tool, H5, data, and prototype states. |
| `horizontal-craft/data-integrity.md` | Metrics, charts, tables, rankings, percentages, or claims. |
| `horizontal-craft/link-and-proof.md` | Links, CTAs, citations, client logos, testimonials, proof claims. |
| `horizontal-craft/technique-library.md` | Advanced motion, 3D, shaders, data-viz, or effects beyond plain CSS. |
| `horizontal-craft/anti-ai-slop.md` | Final anti-default/anti-template-quality check; light generation reminder, heavier delivery check. |

## Deprecated / Removed

- `chinese-copy.md` — removed from core craft. Lightweight AI-flavored copy checks belong in `anti-ai-slop.md` when they affect design quality.
- `execution-checklists.md` — removed. Canonical checks live in `SKILL.md` and `quality-gate.md`.
- `xiaohongshu-card.md` — replaced by `social-card.md`; keep only as a temporary alias if needed.
- `tool-h5.md` — replaced by `web-tool.md`; keep only as a temporary alias if needed.
- `METADATA.md` — not required unless a separate tool explicitly consumes it. Prefer `SKILL.md` frontmatter plus this index.
