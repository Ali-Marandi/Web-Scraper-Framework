---
name: pricing-page
description: Chinese-market SaaS pricing page template — soft sky-blue glass-morphism, 4-tier card grid with one elevated "recommended" tier, monthly/annual toggle, FAQ accordion, ¥ pricing with Inter numerals, careful CJK linebreaking, ICP filing footer.
visibility: public
mode: template
carrier: web-page
scenario: pricing
pattern_source: pricing-cn.html
source_priority: skill-first
triggers:
  - "做个 SaaS 定价页"
  - "中文付费页"
  - "月年套餐切换"
  - "4 档卡片定价"
  - "¥ 价格表"
  - "定价 + FAQ"
---

# Pricing Page Template

Use this template when the artifact is a **Chinese-market SaaS / product pricing page** that needs to feel premium, calm, and design-led — not a generic 3-tier feature-checklist grid.

## Use When

- The product is sold to a Chinese audience (¥, 元/月, ICP filing, 微信/支付宝 implied).
- The pricing model fits tier cards (3–4 tiers, optional monthly/annual toggle).
- One tier should be visibly elevated (early-bird, most-popular, recommended).
- The brand can carry soft sky-blue glassmorphism — or you intend to retheme the palette while keeping the structure.

## Avoid When

- The product is global / EN-primary — re-theme heavily or use a different template.
- Pricing is purely per-seat / usage-metered with no tiers — a tier grid is the wrong shape.
- The page needs a deep feature-comparison matrix as the primary surface — start from a comparison-table-first template instead.
- It's an OSS / free / waitlist product — use `waitlist-page/` or `saas-landing/`.

## Required Reading

Read this `SKILL.md` first. Do **not** read `pricing-cn.html` by default.

Read `pricing-cn.html` only when you need concrete tier-card geometry, the elevated-tier transform values, the monthly/annual toggle behavior, or the FAQ single-open pattern. Extract patterns; do not copy DOM, classnames, brand copy, or placeholder prices wholesale.

## Design Strategy

Decide before building:

1. **Tier count** — 3 (standard) or 4 (with an Observer / Free tier).
2. **Recommended tier** — which one lifts and inverts (white CTA on dark) ?
3. **Toggle model** — monthly / annual with discount %, or batch / cohort labels (第 N 批) for early-access.
4. **Tier naming** — generic (Basic / Pro / Business) or atmospheric (Observer / Early Bird / Founder / Patron). The template's voice favors atmospheric.

## Layout Bias

Prefer:

- one elevated tier (3D lift + image-backed scrim + inverted CTA), the rest flat glass cards
- ¥ + Inter tabular numerals for the price; PingFang / MiSans for surrounding copy
- short feature lists (≤ 6 per tier), each prefixed by a single hairline check
- a "value strip" below the cards (4 short callouts) rather than a giant comparison table
- FAQ as single-open accordion, not all-expanded by default
- ICP filing in the footer (real or placeholder)

Avoid:

- multiple "推荐" badges across tiers — pick one
- 黑金 gradients or neon accents (forbidden aesthetic)
- generic emoji or 3D-icon feature bullets
- forcing English tier names when the audience reads Chinese
- pretending to be Stripe / Linear with a near-identical clone of their pricing page

## Platform / Size

Desktop-first responsive web page. Cards reflow to 2 + 2 at tablet width and stack on mobile. Keep the elevated tier prominent at every breakpoint.
