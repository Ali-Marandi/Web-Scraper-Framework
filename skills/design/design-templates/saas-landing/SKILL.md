---
name: saas-landing
description: Premium calm-tech SaaS landing template — bilingual (CN/EN) literary voice over a dark forest-night palette with warm gold accent, Cormorant + Noto Serif SC, Three.js procedural forest hero, station-based scrolling narrative, custom cursor. Built for ambient-AI / creative-tool / philosophical SaaS, not loud commercial launch.
visibility: public
mode: template
carrier: web-page
scenario: marketing-landing
pattern_source: reference.html
source_priority: skill-first
triggers:
  - "做个 calm-tech SaaS 落地页"
  - "双语 SaaS landing"
  - "森林夜调 SaaS"
  - "Three.js hero 落地页"
  - "高端 SaaS 官网"
  - "氛围型 AI 工具落地页"
---

# SaaS Landing Template

Use this template when the artifact is a **premium, slow-paced, design-led SaaS landing page** that needs to feel like an artist statement, not a Stripe-clone.

## Use When

- The product is an **ambient / creative / calm-tech / philosophical** SaaS — AI companion, journaling tool, content tool, creative software, slow productivity.
- The brand voice can sustain Chinese literary prose alongside English — bilingual is a feature, not an afterthought.
- The user wants stations of scrolling narrative (manifesto → features → CTA), not a generic hero-features-pricing-FAQ stack.
- 3D / Three.js hero is welcome (or at least an atmospheric visual carrying the mood).

## Avoid When

- The product is e-commerce, transactional, or mass-market consumer — the pacing is too slow.
- The user wants a fast-conversion, A/B-tuned, growth-marketing landing — use a Linear / Vercel-clone instead.
- The brand is loud / neon / cyber — fight or rebuild rather than retheme.
- The audience is mobile-first — the template is desktop-primary; mobile works but the magic lives on a wide canvas.
- Pricing or signup is the primary surface — use `pricing-page/` or `waitlist-page/`.

## Required Reading

Read this `SKILL.md` first. Do **not** read `reference.html` by default.

Read `reference.html` only when you need: the Three.js forest scene geometry (instanced trunks, canopy, fireflies), the scroll-driven camera walk, the custom-cursor expand-to-ring behavior, or the station-scrolling pattern. Extract patterns; do not copy placeholder product copy, the bilingual nav strings, or the exact gold / forest tokens wholesale.

## Design Strategy

Decide the page's **stations** before any visual choice:

1. **Hero station** — one-line thesis. A claim, not a feature.
2. **Manifesto station** — a paragraph explaining the worldview.
3. **3 feature stations** — each a verb (Listen / Reflect / Compose), not a noun.
4. **Closing CTA** — quiet invitation, not "Start your free trial now".

Sub-pages (features / story / pricing / contact) inherit the same hush.

## Layout Bias

Prefer:

- thin weights (300–500) dominating, with display italic serifs as accent
- one warm accent color over a deep, organic background — never two
- generous vertical breathing room between stations (each station feels like its own page)
- a single atmospheric hero — 3D, video, or a single large image — not stacked
- custom cursor and easing micro-interactions, used sparingly
- bilingual nav and headlines where it adds meaning

Avoid:

- "social proof logo wall" of unrelated brand marks
- screenshot-stack feature grids (this template is not for that)
- gradient meshes, neon accents, dark-cyber overlays
- "Get started for free" CTA energy
- emoji icons in features
- fast / bouncy motion — the contract is calm

## Platform / Size

Desktop-first. Set a generous content max-width with side rails for chapter nav. Mobile should degrade to a single column with the atmospheric hero replaced by a static crop — do not try to render Three.js scenes full-quality on mobile.
