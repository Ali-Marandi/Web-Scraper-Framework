---
name: html-ppt-xhs-post
description: 小红书 (XHS) 3:4 vertical cover template — two voices: spring/lifestyle soft watercolor cover with Songti + ink-green accents, and bold editorial typography cover with cobalt-blue bands + folded-paper interior. Despite the "ppt" prefix in the path, these are fixed-image XHS covers, not slide decks.
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: xhs-cover-spring.html, xhs-cover-typography.html
source_priority: skill-first
triggers:
  - "做个小红书竖封面"
  - "xhs 3:4 封面"
  - "春日水彩封面"
  - "钴蓝编辑感封面"
  - "宋体 + 水墨封面"
---

# XHS Cover Template

Use this template for **小红书 / RED 信息流封面图** at the standard 3:4 (1242×1660) portrait canvas. This is a fixed-image surface delivered as HTML-to-image, not a slide deck and not a WeChat cover.

This template ships two voices. Pick before building.

## Variants

### `xhs-cover-spring.html` — Soft seasonal lifestyle

- Voice: meditative, slow-living, watercolor-paper, bilingual.
- Use for: 春日 / 慢生活 / 治愈 / 旅行 / 食物 / 居家 / 冥想 / 节气 content.
- Distinctive moves: mint→cream vertical gradient, Songti SC Chinese headline + Times New Roman italic English lead, ink-green (#2d4a3e) accents, hand-drawn SVG clouds / grass tufts, soft-glow photography.

### `xhs-cover-typography.html` — Bold editorial design

- Voice: design-led, hashtag-as-mark, magazine-issue energy.
- Use for: 设计 / 排版 / 创作工具 / 课程预告 / 沙龙活动 / 设计周刊 content.
- Distinctive moves: cobalt-blue (#1652f0) top/bottom bands, cream "folded paper" interior with shadow fold, # prefix + chunky PingFang headline + Helvetica Neue Black numerics, rotated issue tag, angled photo strip.

## Use When

- The artifact is an **XHS cover** at 3:4 portrait, optimized for the feed thumbnail context.
- The user explicitly says 小红书 / XHS / RED / 封面.
- The headline carries the card — photography supports, not dominates.

## Avoid When

- The platform is WeChat 公众号 → use `wechat-cover-pair/` (different aspect, different reading distance).
- The platform is Xiaohongshu but the content is a method / KPI / comparison card → use `social-card-swiss/`.
- The content needs to be a reflective long-quote literary card → use `social-card-editorial/`.
- The output is a deck or scrolling article — wrong carrier entirely.

## Required Reading

Read this `SKILL.md` first. Do **not** read either `pattern.html` by default.

Read the chosen variant only when you need exact title-breaking, decorative-element placement, or the folded-paper / soft-cloud SVG geometry. Extract patterns; do not copy DOM, placeholder copy, Pexels photo URLs, or class names wholesale.

## Design Strategy

Pick the variant from voice:

- Slow + warm + bilingual lyrical → **spring**
- Loud + editorial + design-savvy → **typography**

Then write the headline first. XHS covers live or die by how readable the headline is at thumbnail scale. Compose it to break in 2–3 lines with intentional line-break points.

## Layout Bias

Prefer:

- one dominant headline, one supporting sub or keyword chain
- a single visual anchor (photo, mark, or geometric block) — not three
- credible photo credit if a stock image is used
- breathing room at top and bottom safe areas (XHS UI overlay)
- bilingual stacking (English lead + Chinese headline) only when both have meaning

Avoid:

- 塑料 stickers, emoji-pile decorations, 3D plastic badges (AI-slop)
- 黑金 "premium" gradients (forbidden — see design aesthetic memory)
- crowding the canvas with 4+ decorative elements
- shrinking the headline to fit a long sentence — rewrite the sentence

## Platform / Size

Fixed 3:4 portrait. Use `canvas-and-device.md` for current XHS dimensions and safe areas. Do not hard-code other ratios; if the user wants 1:1 or 16:9 they want a different template.
