---
name: Landing Page Skill
description: Design single-subject product landing pages, SaaS homepages, pre-launch waitlists, service pages, agency/studio pages, pricing pages, and conversion-oriented product marketing pages as self-contained HTML artifacts.
mode: artifact
platform: responsive-web
scenario: landing-page
preview:
  type: html
default_for:
  - landing page
  - product landing page
  - product homepage
  - SaaS homepage
  - SaaS landing
  - product website
  - marketing page
  - pre-launch waitlist
  - waitlist page
  - service page
  - agency homepage
  - studio homepage
  - pricing page
  - 产品落地页
  - 产品官网
  - SaaS 主页
  - 官网
  - waitlist 页
  - 定价页
fidelity: high
---

# Landing Page Skill

Design a landing page for **one product, service, offer, or subject** that makes a visitor answer three questions quickly:

1. **What is this?**
2. **Why should I care?**
3. **What should I do next?**

This file gives landing-page judgment, not a full rulebook. It plugs into the main `SKILL.md` flow — it does not replace it.

## Route elsewhere if

person / body-of-work showcase → `portfolio.md` · product UI / dashboard / app flow / clickable demo / “做一个 XX 的 demo” → `prototype.md` · single-task calculator/generator/checker → `web-tool.md` · linear reading / newsletter / editorial → `content-page.md` · information exploration / data story → `info-interactive.md` · social image / product brief image / report summary image / poster / cover / long-image → `social-card.md` · slides / pitch deck → `deck.md`

Studio/agency sites can be both portfolio and landing page — lead with the dominant intent: selling a service (clear offer, pricing/contact CTA, capability framing) → landing page; showing work and personality (case-led grid, project depth, distinctive voice) → `portfolio.md`.

## The Two Non-Negotiables

Everything else is flexible, but these two must be true:

1. **One audience, one action.** The page serves one primary audience and drives one primary CTA. Every section either moves the visitor toward that action or earns trust for it. If two CTAs compete at equal weight, the page has already failed.

2. **Concrete value in the first screen.** The hero must say what the product actually is and does — in product terms, not positioning language. "AI-powered platform to supercharge your workflow" is a failure; "turn a CSV of orders into a tax-ready report in 30 seconds" is a hero. If the visitor can't restate the offer after one screen, rewrite the hero before styling anything.

## Choose a Structure

Pick **one** structure from the page's conversion job. Do not blend several into mush.

### A. Classic Narrative Scroll
Hero → problem/value → product proof → how it works → objections → CTA. Each scroll section answers the visitor's next unspoken question, in order.
**Best for:** products that need explanation before purchase; most SaaS and B2B pages.
**The move:** section order = objection order. Map the skeptic's questions ("does it work with my stack?", "how long to set up?", "what does it cost?") and let the sections answer them in sequence. A section that answers no objection gets cut.

### B. Product Showcase
The product UI is the hero — shown big, real, and annotated. Copy supports the image, not the reverse.
**Best for:** visually strong products: design tools, dashboards, dev tools with a UI worth seeing.
**The move:** real interface at full scale with callout annotations on actual features. Never a floating laptop mockup at 30° with a glow — that adds three layers of distance and signals stock template.

### C. Sales / Pricing Page
Built around the buying decision: plans, comparison, objection handling, guarantee.
**Best for:** visitors who already know the product and are deciding whether and which tier.
**The move:** answer objections at the point of doubt — FAQ adjacent to the pricing table, refund/cancel terms next to the buy button, plan-comparison rows that map to real usage situations ("you need this tier when…"), not feature-name checkmark soup.

### D. Waitlist / Launch Page
Deliberately scarce: one promise, one visual, one field. Tension comes from restraint.
**Best for:** pre-launch products collecting signups before there is a full story to tell.
**The move:** make signup value explicit — what the subscriber gets (early access? founding price? build updates?) and roughly when. "Join the waitlist" with no stated payoff converts nobody. A confirmation state must exist (inline success message at minimum).

### E. Service / Agency Page
Capability framing + named process + proof of work + contact path.
**Best for:** consultancies, studios, freelancers selling expertise rather than a product.
**The move:** a named, numbered process ("Week 1: audit → Week 2–3: prototype → Week 4: ship") is the strongest trust signal a service page has — it proves the work is systematized, not improvised. Vague "we collaborate closely" paragraphs prove nothing.

### F. Editorial Launch
Manifesto-style, type-led. The copy IS the design; imagery is minimal or absent.
**Best for:** opinionated products, brand-led launches, developer tools with a strong point of view.
**The move:** oversized statement typography (clamp() up to ~10–14vw for the thesis line), long-form conviction copy with real paragraph rhythm, one accent color. Works only if the writing is genuinely sharp — weak copy at display scale is just louder weakness.

### G. Interactive-Canvas Hero
The product is usable inside the hero — a live demo, playground, or generated output.
**Best for:** tools and APIs whose value is provable in under 10 seconds of interaction.
**The move:** the visitor uses the product before reading about it. The demo must actually work with real logic (`web-tool.md` rigor applies to that component); a fake demo is worse than no demo.

**Anti-pattern: the Interchangeable SaaS Page.**
Soft gradient hero → vague headline → three equal feature cards → grayscale logo wall → testimonial carousel → CTA banner. Cover the product name and it could be any competitor. This is a template wearing a product's clothes — if a draft converges here, return to structure choice.

**Trust-sensitive / enterprise pages** (fintech, security, healthcare, infrastructure): distinctiveness comes from hierarchy, proof density, product clarity, and restraint — not loud visual moves. Structure A or C with a disciplined system beats an expressive concept here.

## Proof Strategy

Decide what proves the value claim, then design that proof as a first-class section — not a logo strip afterthought.

- **The product itself is the best proof.** Real UI, real workflow, real input→output example. Prefer it over any testimonial.
- **Pick proof the product can actually offer:** product UI / workflow walkthrough / customer quote / metric / case / benchmark / press / live demo data. One strong form beats four weak ones.
- **Never invent proof.** No fake logos, testimonials, usage numbers, awards, market data, or quotes. Placeholder proof must be visibly marked as placeholder. Detailed rules: `horizontal-craft/link-and-proof.md`, `horizontal-craft/data-integrity.md`.

## Landing-Page-Specific Moves

### Visual-weight tiers, never CSV-with-CSS
Every information-dense section needs at least four visible weight tiers: hero moment / primary modules / secondary modules / tertiary detail. A page of equal-height cards in a single column is a spreadsheet with padding. Give the strongest claim 2–3× the space of supporting points; let minor features compress into a compact grid or single line each.

### Density rhythm
Alternate full-bleed statement moments with denser informational sections. One dominant moment per page (the hero or one mid-page section), everything else supports it. A page where every section shouts at the same volume reads as noise; a page of uniform medium density reads as a document.

### The repeated CTA, with restraint
Primary CTA at the hero, then again at each natural commitment moment (after the proof section, after pricing, at page end). Identical wording and style each time — the repetition builds familiarity. Secondary actions ("read docs", "watch video") get visually subordinate treatment everywhere: text link or ghost button, never a second filled button beside the primary.

### Asymmetric hero, not centered safety
Default to off-balance hero composition — copy column against product visual at `1fr 1.2fr`, headline hanging into the margin, product image bleeding off one edge. Centered headline + centered subline + centered button is the single strongest template signal. Center only when structure D's scarcity or F's manifesto genuinely calls for it.

### Objection ladder for pricing
Wherever a price appears, the three purchase anxieties must be answered within one viewport: what exactly do I get, what if it doesn't work out (cancel/refund/trial terms), and which option is for me (a highlighted recommended tier with a reason, not just a "POPULAR" badge).

### Numbers as design material
Real metrics (latency, accuracy, time saved, counts) set at display scale with small labels are both proof and visual texture. Only real or clearly-labeled-demo numbers — and respect `horizontal-craft/data-integrity.md`.

## Completeness Checklist

A landing page is finished when:

- [ ] The hero answers what / why / next-action within one screen, in concrete product terms
- [ ] One structure (A–G) is recognizable; the page is not a blend
- [ ] Every information-dense section shows four visual-weight tiers — no equal-card walls
- [ ] Primary CTA appears at hero and recurs at natural commitment moments; secondary actions never compete
- [ ] Every CTA resolves to a real next step — working form with success state, pricing anchor, mailto, or confirmation view; never `href="#"`
- [ ] All proof is real or visibly marked placeholder
- [ ] Sections that serve no objection or goal are removed, not filled
- [ ] Pricing/sales pages answer the three purchase anxieties; waitlist pages state the signup payoff
- [ ] The page works on mobile — structure adapts, not just shrinks
- [ ] Distinctiveness test passes: cover the product name — the page would not work unchanged for an arbitrary competitor

## How this fits the Design Skill flow

- **Scene type.** A landing page is an **expressive** scene by default (per `SKILL.md`): design from this file's structure choices + Creative Context + horizontal craft. Don't push it into a generic UI kit. Exception: trust-sensitive/enterprise briefs may deliberately go restrained — that's a judgment, not a fallback.
- **Templates.** If `design-templates/TEMPLATE-ROUTER.md` + `INDEX.md` has a matching pattern (SaaS landing, pricing, waitlist, launch, service), it may seed the skeleton — but structure choice and the signature moment still drive the result; never ship a template's layout unchanged.

## Creative Context (from SKILL.md)

For open-ended requests, silently complete before generating:

- `creative_positioning` — what the product is really about beyond the feature list (one line; this becomes the hero's angle).
- `first_impression` — what the visitor should feel in the first 3 seconds (tie it to the structure choice and hero treatment).
- `anti_default` — which generic reflex to avoid (usually the Interchangeable SaaS Page anti-pattern; name the specific cliché this product is most at risk of).

The artifact must visibly reflect this. Don't print the context unless asked.

## References — load only when triggered

Don't read these by default. A first draft usually needs this file + a selected template/design-system reference if any + only 1–3 triggered craft files.

- `horizontal-craft/chinese-typography.md` — substantial Chinese text. **If the page has Chinese, its font rules are mandatory**: named fonts must actually load, `font-family` must contain a CJK font name, and webfonts load non-blockingly (preload + fetchpriority / print-onload / unicode-range subset / system fallback) — no FOIT on slow networks.
- `horizontal-craft/color.md` — no design system is provided, or color direction is vague.
- `horizontal-craft/icon-system.md` — feature icons, pictograms, nav icons. No emoji as icons.
- `horizontal-craft/link-and-proof.md` — logos, testimonials, claims, awards, press, citations, CTA links, or proof modules.
- `horizontal-craft/data-integrity.md` — metrics, ROI, market size, benchmarks, charts, or tables.
- `horizontal-craft/animation-discipline.md` — scroll reveal, parallax, hero motion, micro-interactions. For an expressive landing page a fully static page is usually under-delivered; take paste-ready entrance CSS from here.
- `horizontal-craft/technique-library.md` — advanced effects beyond plain CSS that genuinely serve comprehension or the product story (notably structure G).
- `design-system-reference.md` — a brand guide, style reference, template, or `DESIGN.md` is provided or referenced.
- `canvas-and-device.md` — special viewport, device frame, export size, or breakpoint constraints.

## Final Gate

Run `quality-gate.md` as the blocking final checklist before delivery. It owns the global checks (accessibility, dead links, fake proof, placeholder logic, anti-AI-slop, Design Compliance comments) — don't duplicate them here.

Landing-page-specific gate, on top of the Completeness Checklist above:

- the hero explains the actual offer, not positioning vapor;
- the chosen structure's "move" is present, not just its section order;
- pricing/sales pages answer buying objections at the point of doubt;
- waitlist/launch pages make the signup payoff explicit and confirm success;
- the visual direction traces back to the product and audience — every major choice (palette, hero composition, type, motion, module order) has a product-side reason;
- high polish is not hiding weak structure: strip the styling mentally — the section logic must still hold.

## Handoff

Use the standard Design Skill delivery, export, and version-management flow (`export.md`). Landing pages have no separate handoff process unless the user requests export/package/asset handoff.
