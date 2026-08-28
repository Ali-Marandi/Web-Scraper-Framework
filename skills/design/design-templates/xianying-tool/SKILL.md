---
name: xianying-tool
description: Chinese-first AI image-generation tool landing template — TwelveMei-style centered hero with floating icon-island nav, FlyFlowerSong serif display headline, textured pill CTAs, glass canvas mockup of the tool itself, monochrome ink palette. Built for Chinese creative-tool / generative-image / AI-工具 product pages aimed at designers and editors, not loud growth-marketing.
visibility: public
mode: template
carrier: web-page
scenario: product-tool-landing
pattern_source: index.standalone.html
source_priority: skill-first
triggers:
  - "做个 AI 工具落地页"
  - "生成图像工具 landing"
  - "TwelveMei 风工具页"
  - "玻璃画布 mockup"
  - "中文 AI-工具产品页"
  - "宋体 hero 工具页"
---

# Xianying Tool Template

Use this template when the artifact is a **Chinese-language AI / generative-image creative-tool product page** that needs to feel like a quiet editorial workshop, not a SaaS pitch.

## Use When

- The product is a creative tool (生图 / 设计 / 编辑 / AI 工具) whose audience is Chinese designers, illustrators, or editors.
- The hero needs to **show the tool itself** — a glass canvas mockup with case-tabs, presets, prompt card, seed/style chips — rather than a metaphor or stock illustration.
- Navigation should be a **floating central icon-island** (首页 / 案例廊 / 模型 / 定价 / 文档), with brand mark on the left and one textured pill CTA on the right.
- Look should be monochrome ink — paper background, deep ink type, one restrained accent — with FlyFlowerSong (or another high-contrast modern serif) for the display headline and MiSans for UI text.
- The page is single-screen-led: hero + glass canvas + a short lookbook strip + footer. Long-scroll feature reels are out of scope.

## Avoid When

- The product is a **B2B SaaS** with tiered pricing as the primary surface — use `pricing-page/` or `saas-landing/` instead.
- The page is a **pre-launch waitlist** (no working canvas, just an email form) — use `waitlist-page/`.
- The brand wants loud growth-marketing — bright gradients, hero video, social proof walls. This template is hushed and editorial.
- The audience is English-primary — the type stack and rhythm are tuned for CJK display + Latin support, not the other way around.
- The artifact is a dashboard, deck, social card, or PDF report — pick the matching template.

## Required Reading

Read this `SKILL.md` first. Do **not** read `index.standalone.html` by default — it is ~11MB with inlined base64 webfonts and will flood context.

Read `index.standalone.html` only when you need: the icon-island nav geometry, the glass canvas mockup composition (canvas-frame / canvas-glass / canvas-row / case-tabs / preset chips), the textured pill CTA treatment, the brand-mark lockup (`显影` + `XIANYING®`), or the footer column structure. Extract patterns; do not copy preset names (灵境 / 幻翼 / 缓光 / 霞照 / 触发显影), model labels (GEN-3 / GEN-2 / 线稿模型), or the ICP filing wholesale.

## Design Strategy

Before placing components, decide what the hero is **selling**:

- the **tool** (canvas + presets dominate, headline is a one-liner about the audience)
- the **aesthetic** (one large generated frame dominates, controls are hinted)
- the **model lineup** (case-tabs / model-card row dominates, canvas is secondary)
- the **lookbook** (gallery strip rises into view, hero compresses)

Pick one. Mixing all four flattens the page into a feature list.

The headline pattern here is `显影 是一个面向[受众]的生图工具。` — a single sentence that names the audience inline. Keep that rhythm: one declarative sentence, audience in serif emphasis, period at the end. Don't replace it with a marketing slogan.

## Layout Bias

Prefer:

- FlyFlowerSong (or a comparable modern Song with high stroke contrast) for the display headline; MiSans Heavy / Bold / Semibold for UI weights; Inter for numerals and Latin tags.
- paper-tone background (#F7F4EE / 米白) with deep ink type (#1A1A1A), one warm-grey or single-hue accent — never two accents on the same screen.
- textured pill buttons (subtle noise / paper grain), not flat solid fills.
- floating icon-island nav with tooltip chips on hover; brand mark on the left, single CTA pill on the right.
- glass canvas mockup with a thin hairline frame, light inner shadow, and visible canvas-row of preset chips at the bottom — show the tool working, don't fake it with a screenshot.
- footer in four short columns (产品 / 公司 / 资源 / 条款) plus a 备案信息 line — Chinese internet compliance, not decorative.

Avoid:

- 黑金 / dark gradients / "executive premium" overlays — this template is monochrome ink on paper.
- monospace fonts anywhere (the direction note explicitly says no mono).
- dot-separators between nav items (`首页 · 案例廊 · 模型`) — the icon-island replaces them.
- emoji in nav, CTAs, or preset chips.
- 3D plastic stickers, glossy reflections, or AI-generated hero illustrations of the canvas.
- forcing negative letter-spacing on CJK display type — FlyFlowerSong needs its native rhythm.

## Platform / Size

Desktop-first, ~ 1280–1440px design width. The icon-island nav and glass canvas mockup are the load-bearing elements — they need horizontal room. On tablet (~ 900px) the canvas collapses to a stacked preview; on mobile the icon-island becomes a top tab strip and the canvas drops to a single-frame card. Do not pretend this is a mobile-native app.
