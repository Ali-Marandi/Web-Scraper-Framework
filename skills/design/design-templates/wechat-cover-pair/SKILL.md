---
name: wechat-cover-pair
description: 微信公众号封面对模板 — 主图（headline + subline + 视觉锚点）+ 次图/分享图（短标题 + logo / 账号标签）+ 长图头（文章标题 + 章节预览）。比小红书封面要求更强的标题腿粗、更明确的安全区、更克制的阅读节奏。必须按当前微信尺寸读 canvas-and-device.md。触发："做个公众号封面 / 微信首图次图对 / 视频号封面 / 公众号分享图 / 长图头"。NOT XHS 3:4 尺寸，NOT XHS 贴纸密集风。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个公众号封面"
  - "微信首图次图对"
  - "视频号封面"
  - "公众号分享图"
  - "长图头封面"
  - "微信生态封面"
related_patterns: social-card-editorial
---

# WeChat Cover Pair Template

Use for 微信公众号首图、封面图、分享图、视频号/微信生态封面等 fixed-image surfaces.

## Core Rule

WeChat covers are not Xiaohongshu covers. They need stronger headline legibility, clearer safe areas, and a calmer reading rhythm.

## Structure Options

- main cover: headline + subline + visual anchor
- secondary cover: shorter title + logo/account label
- long image header: article title + section preview
- cover pair: large main cover + smaller share-safe variant

## Must Do

- Read `canvas-and-device.md` for current WeChat dimensions and safe areas.
- Keep title readable in thumbnail contexts.
- Avoid placing important text too close to edges.
- Do not assume XHS 3:4 dimensions.

## Avoid

- XHS-style crowded sticker layouts.
- Long headline squeezed into one line.
- Tiny subtitle that disappears in feed preview.

## Pattern Source Rule

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only when you need concrete layout rhythm, spatial relationships, or interaction/annotation behavior that this markdown cannot fully specify. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or styling wholesale.
