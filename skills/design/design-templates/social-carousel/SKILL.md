---
name: social-carousel
description: 小红书选辑 / anthology 横滚社交模板 — 8 张竖卡连续 auto-scroll snap loop，每张几何裁切 mask（拱 / 椭 / 半穹顶 / 斜）+ 宋体标题 + 一个 SVG 装饰符号 + 角部期号元数据。用于摄影系列 / 艺术指导 / mood reel / 品牌瞬间集 (6-10 帧)。触发："做个 anthology 选辑 / 横滚画廊 / mood reel / 摄影系列展 / 第 0X 辑封面集"。NOT 教程类（用 digital-eguide），NOT < 4 张系列，NOT 文字密集卡（横滚速度藏文字）。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: scroll-gallery.html
source_priority: skill-first
triggers:
  - "做个 anthology 选辑"
  - "横滚画廊"
  - "mood reel"
  - "摄影系列展"
  - "第 0X 辑封面集"
  - "auto-scroll 卡集"
related_patterns: social-card-image-led, digital-eguide
---

# Social Carousel Template

Use this template when the artifact is a **curated multi-card anthology** — 6–10 images that share an editorial identity and want to be experienced in rhythm, not as a list.

Distinct from `digital-eguide/social-carousel.html` (12-frame field-notes guide with 50/50 photo + metadata). This one is **gallery-paced**, no per-card metadata table, sculptural geometric masks.

## Use When

- The user wants to publish a **series / anthology / 选辑 / collection** — photography, art direction, branding moments, mood reel.
- Each card carries one image + a short serif title + a volume number (第 0X 辑).
- The viewing context is browsing / pause / browse — not step-by-step instruction.
- The output is a fixed-image set (HTML-to-image) or an embedded auto-scrolling strip.

## Avoid When

- The content is a tutorial or numbered steps — use `digital-eguide/social-carousel.html` (it has progress + per-step metadata) or `social-card-swiss/`.
- The series is < 4 entries — make individual cards instead.
- The content is text-heavy (quotes, body copy) — gallery rhythm hides text.
- The platform expects discrete swipeable posts (XHS multi-image post) — this is one scrolling strip, not 9 separate posts.

## Required Reading

Read this `SKILL.md` first. Do **not** read `scroll-gallery.html` by default.

Read `scroll-gallery.html` only when you need: the geometric-mask shapes (arch / oval / half-dome / diagonal), the auto-scroll easing values, the seamless-loop double-render trick, or the hover-slowdown behavior. Extract patterns; do not copy the placeholder Songti titles, photo URLs, or class names wholesale.

## Design Strategy

Commit to the anthology spine before designing cards:

- one cover frame role per card (full-bleed, arched, oval, diagonal, masked half-dome)
- a single rotating ornamental SVG mark style (don't mix flower + grid + arrow)
- consistent corner metadata (volume + tag + year, picked once)
- one title font (Songti SC), one meta font (PingFang SC), no third voice

If the cards don't share a visual system, the auto-scroll exposes the inconsistency.

## Layout Bias

Prefer:

- 2:3 or 7:9 portrait per card; mix sparingly, never randomly
- restrained warm palette (creams / terracottas / sage) over white or near-black
- one geometric mask per card, rotated through the set
- ornamental marks small and consistent, in a single accent ink
- continuous slow auto-scroll, pause on hover, infinite loop

Avoid:

- emoji or 3D plastic stickers in corner metadata
- mixing portrait + landscape card aspects randomly
- adding step numbers (this is not a tutorial)
- decorative gradients behind images — the mask is the decoration
- 黑金 / neon palettes — the template's identity is editorial / warm

## Platform / Size

A horizontal strip of vertical cards (~ 360×540 each). Designed for embedding on a long page or capturing as a wide image. If the user wants discrete XHS posts, export each card individually.
