---
name: dashboard
description: Chinese-first internal-tool / ops dashboard template — light-mode Linear-grade layout with serif headlines, tabular Inter numerals, KPI hero, pulse bars, progress rings, team-presence grid, activity timeline, and CJK-aware typography.
visibility: public
mode: template
carrier: web-page
scenario: internal-tool
pattern_source: stack-dashboard-zh.html
source_priority: skill-first
triggers:
  - "做个运营仪表盘"
  - "内部工具看板"
  - "中文 ops dashboard"
  - "KPI hero 看板"
  - "Linear 风看板"
---

# Dashboard Template

Use this template when the artifact is a **Chinese-language internal tool / ops / project dashboard** that needs to look designed-in-Chinese, not translated.

## Use When

- The user is mocking an admin panel, operations workbench, project portfolio view, or team-status console.
- The dashboard is **CJK-primary** — Latin and numerals serve the Chinese hierarchy, not the other way around.
- The look should be light-mode, calm, editorial-leaning (Noto Serif SC headlines, Inter numerals), with restrained status color.
- Surfaces include: greeting + KPI hero, project cards with progress rings, multi-chart analytics row, activity timeline, team-presence grid, async standup blocks.

## Avoid When

- The artifact is a **marketing landing** for a SaaS product — use `saas-landing/` instead.
- The artifact is a **public-facing report** meant to be read top-to-bottom like an article — use `Project Brief/` or `blog-post/`.
- The user wants a dark observability "war-room" UI — this template is light and calm; rebuild rather than dark-mode-flip.
- The artifact is mobile-first — the layout is built around a wide desktop viewport.

## Required Reading

Read this `SKILL.md` first. Do **not** read `stack-dashboard-zh.html` by default.

Read `stack-dashboard-zh.html` only when you need concrete component geometry (ring sizes, pulse-bar segment widths, tab-grid spacing, status-dot sizing) or the Chinese font-stack ordering. Extract patterns; do not copy DOM, classnames, placeholder team names, or color tokens wholesale.

## Design Strategy

Before placing components, decide the dashboard's **job**:

- daily workbench (greeting + today's focus + KPI + team)
- project portfolio (cards with status, owners, progress)
- analytics view (charts + sparklines + bottleneck breakdown)
- activity / on-call view (timeline + heatmap + presence)

A single page can blend these, but pick a hero — the first screen should answer one primary question.

## Design Structure / Visual Weight

The page is a **composition of zones with deliberately different visual weight** — not a uniform grid of equal cards. Before placing any component, sketch the weight tiers:

- **Hero (≈ 30–35% of first screen)** — greeting + 3–4 large KPI tiles with tabular numerals and a thin trend line. Dominant; sets the headline.
- **Primary (asymmetric grid below hero)** — project cards with progress rings + a wide analytics/chart row. Mix card widths and heights (e.g. 2-up large cards + 3-up medium cards, not a uniform 4-col grid).
- **Secondary** — activity timeline (chronological column) and team-presence grid. Smaller type, tighter spacing.
- **Tertiary** — async standup blocks, footer meta, legends, filter chips. Quiet, low contrast.

Different roles get different **shapes**: KPIs are large numerals in rounded tiles, project cards have progress rings + owner stacks + status dots, charts are wide with sparklines + axis labels, presence is a dot grid, activity is a column of badge-led rows. A reader should tell role from silhouette before reading a label.

### Counter-example — do NOT ship this

A `max-width: 1120px` centered single column with a small masthead and N identical `border-bottom: 1px solid` rows (each row: number / title / one-line meta / tag chips / link). No hero, no rings, no charts, no asymmetric grid — every line has the same height and density. That is a **CSV with CSS**: it satisfies "show the data" but fails as a dashboard, because nothing has a different visual weight from anything else and the eye has nowhere to land first.

If your draft reduces to "for each item, render a row" and no zone above the list is doing more visual work (KPI hero, ring cards, chart row), **stop and restart the layout** — add a hero with real numerals, vary card geometry, and let at least one section break out of the column rhythm.

## Layout Bias

Prefer:

- serif (Noto Serif SC) for editorial headlines, sans (PingFang / MiSans) for body, Inter for numerals
- `font-variant-numeric: tabular-nums` on all metric blocks
- generous rounded corners (≈ 24–28px) with soft shadows, not flat outlines
- status conveyed by small colored dots + label, not by tinting whole cards
- one or two accent colors per page, not the full status palette in every section

Avoid:

- dark hero gradients pretending to be "premium"
- emoji icons in nav or KPIs
- forcing negative letter-spacing on CJK glyphs
- screenshot-of-screenshot composition (charts that are clearly stock images)
- treating Latin labels as primary when the audience reads Chinese

## Platform / Size

Desktop-first, ~ 1280–1440px design width. Cards should reflow gracefully to two columns at ~ 960px and stack on mobile. Do not pretend this is a mobile-native app shell.
