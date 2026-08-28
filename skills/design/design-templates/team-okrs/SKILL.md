---
name: team-okrs
description: Team operations dashboard template — Linear/Asana-clean hybrid with sprint status hero, 4-segment progress bar, workstream cards, chronological activity stream with colored event badges, right-rail with today's schedule + team-presence + upcoming milestones. For team status snapshots, OKR reviews, "team this week" all-hands views.
visibility: public
mode: template
carrier: web-page
scenario: internal-tool
pattern_source: activity-stream.html
source_priority: skill-first
triggers:
  - "做个团队 OKR 看板"
  - "sprint 状态页"
  - "团队周会 dashboard"
  - "活动流看板"
  - "team this week 页"
  - "里程碑追踪页"
---

# Team OKRs Template

Use this template when the artifact is a **team-facing status / OKR / sprint console** — not a personal todo, not a public marketing page, not a deck.

## Use When

- The audience is a team, lead, or stakeholder reviewing **collective progress** — quarterly OKR review, sprint status, "this week" all-hands view.
- Surfaces needed: sprint hero with progress segments, workstream cards with owners, chronological activity feed with event types (shipped / blocked / reviewed / commented / uploaded), today's schedule, team presence, upcoming milestones.
- Look should feel like a polished internal tool (Linear / Asana / Notion-flavored), neutral and calm.

## Avoid When

- The artifact is a personal todo / planner — too team-centric.
- The artifact is meant to be presented as slides (use a `ppt/` deck template).
- The page is public marketing — wrong audience, wrong density.
- The data is purely analytical (charts, BI metrics) — use `dashboard/` (more chart-oriented) instead.
- The content is a periodic narrative digest with prose — use `Project Brief/` (notebook weekly digest).

## Required Reading

Read this `SKILL.md` first. Do **not** read `activity-stream.html` by default.

Read `activity-stream.html` only when you need: the 4-segment sprint progress bar geometry, the event-badge taxonomy (green check / red alert / purple comment / amber up-arrow / dark review), the workstream-card layout, the schedule current-time indicator, or the team-presence dot pattern. Extract patterns; do not copy placeholder names, project titles, or class names wholesale.

## Design Strategy

Decide the page's **answer** before placing components:

- "Are we on track this sprint?" → hero progress + status stats dominate
- "What did the team do this week?" → activity stream is the spine, hero shrinks
- "What's next?" → workstream cards + milestones dominate
- "Who's around right now?" → presence + schedule dominate

A single page can blend these but pick the lead question.

## Design Structure / Visual Weight

The page is a **composition of zones with deliberately different visual weight** — not a stack of equal rows. Before placing any component, sketch the weight tiers:

- **Hero (≈ 30–40% of first screen)** — sprint title + 4-segment progress bar + 3–4 status stats. Dominant; answers the lead question immediately.
- **Primary (main column body)** — workstream cards (medium, varied internal hierarchy) and activity stream (chronological, badge-led). Cards must NOT all be the same height.
- **Right rail (≈ 25–30% of width)** — today's schedule, presence dots, upcoming milestones. Smaller type, tighter spacing, clearly secondary.
- **Tertiary** — filter chips, footers, legends. Quiet, low contrast.

Different roles get different **shapes**: hero is a wide banner with a progress geometry; workstream cards are rectangles with owner stacks; activity is a column of badge-led rows grouped by day; presence is a dot grid; schedule is a vertical time-axis. A reader should be able to tell role from silhouette alone, before reading any label.

### Counter-example — do NOT ship this

A `max-width: 1120px` centered single column with a small masthead and N identical `border-bottom: 1px solid` rows (each row: number / title / one-line meta / tag chips / link). No hero geometry, no right rail, no weight variation — every line has the same height and density. That is a **CSV with CSS**: it satisfies "show all the data" but fails as a team/OKR surface, because the eye has nowhere to land first and no signal about what matters more.

If your draft reduces to "for each item, render a row" and no zone above the list is doing more visual work, **stop and restart the layout** — add a hero that answers the lead question, push at least one block into a right rail, and let card/row heights vary.

## Layout Bias

Prefer:

- Inter with OpenType features enabled (ss01, cv11) + PingFang SC for CJK
- soft pastel status backgrounds with high-contrast colored dots, never tinting whole cards
- overlapping owner-avatar stacks for shared work
- chronological grouping in the activity feed (by day), with sub-grouped events under the day header
- right-rail used for time-bounded info (today, this week) — main column for status

Avoid:

- emoji as status indicators
- bouncy animations or playful illustrations
- dark gradients or "executive premium" overlays
- treating the activity feed as a social wall with likes / shares / reactions
- a wall of charts when status pills + progress segments would answer faster

## Platform / Size

Desktop-first internal tool. Designed for ~ 1440px wide; sidebar / right-rail collapse below ~ 1100px. Not mobile-native.
