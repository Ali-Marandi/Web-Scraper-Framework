---
name: waitlist-page
description: Premium pre-launch waitlist page template — dark charcoal canvas with subtle vignette, drifting portrait video-thumbnail cards, fade-up cascades, glass nav, live-updating join counter, single email form with success/error states. Built for creative-tool / AI / niche-SaaS invite-only launches with hushed exclusive tone, not loud growth-marketing.
visibility: public
mode: template
carrier: web-page
scenario: pre-launch
pattern_source: 层云-waitlist.html
source_priority: skill-first
triggers:
  - "做个 waitlist 预发布"
  - "高端候补名单页"
  - "邀请制邮件登记"
  - "pre-launch 暗色页"
  - "层云风预登记"
---

# Waitlist Page Template

Use this template when the artifact is a **pre-launch / private-beta / early-access waitlist** for a product that wants to feel measured and exclusive — not a growth-hack countdown page.

## Use When

- The product is **not yet shipping** — primary CTA is "join the waitlist", not "sign up free".
- Audience is niche / creative / pro — visual creators, AI tinkerers, indie founders, design-tool users.
- The vibe should be calm, curated, "few slots" — not "10,000 people are on the list, hurry".
- The page can carry one email form well, plus a slim feature triplet, and ends there.

## Avoid When

- The product is shipping and ready for trial — use `saas-landing/` (full marketing) or `pricing-page/`.
- The brand is loud, neon, consumer-mass-market — wrong mood.
- The page needs to do conversion-optimization with multiple CTAs, A/B variants, urgency timers — this template's hushed tone is the opposite of that.
- The audience is enterprise — use a contact-sales pattern, not a public waitlist.

## Required Reading

Read this `SKILL.md` first. Do **not** read `层云-waitlist.html` by default.

Read `层云-waitlist.html` only when you need: the floating-card drift loop (8 cards, 14–19s with staggered entrance), the fade-up cascade timing, the live-counter bump-on-submit animation, the glass-nav backdrop blur, or the form success / error states. Extract patterns; do not copy the placeholder brand voice, the 820+ counter starting value, or class names wholesale.

## Design Strategy

A waitlist page does **one** job. Decide the singular hook before adding anything:

- "Your creative system. Finally arrived." (product-thesis hook)
- "Built for [audience], not everyone." (exclusion hook)
- "We're opening 100 seats this month." (scarcity hook — use sparingly)

Then keep the spine short:

1. Fixed nav (logo + secondary link + small CTA)
2. Hero teaser with drifting visual cards
3. One-line headline + one-line subline
4. Email form with live joiner count
5. 3-feature article triptych (optional)
6. Mid-page CTA echo
7. Minimal footer

Resist adding pricing, testimonials, FAQ — those belong on the post-launch landing.

## Layout Bias

Prefer:

- deep charcoal background with subtle radial vignette
- one accent color (the template uses success-green) for the joiner pill and form success
- thin weights for body, medium-bold for headline, no display-poster type
- soft floating animations (14–19s loops) — never bouncy, never fast
- form succeeds in place — no redirect to a generic "thanks" page
- live counter that bumps up by one on submit

Avoid:

- countdown timers, urgency banners, scarcity badges
- testimonials from people who haven't used the product
- 3D plastic mockup hero images
- 黑金 / neon-cyber palettes
- emoji in the counter or features

## Platform / Size

Desktop and mobile both first-class — waitlists get shared on Twitter / 微信 and most clicks are mobile. Keep the hero readable at 360px width; the floating cards should reduce to 4 (not 8) on mobile.
