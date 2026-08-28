---
name: social-card-editorial
description: 杂志感 / 电子墨水风社交卡 — 纸感留白、张力标题、克制装饰；卡角色含封面 / 期号封面 / 引言 / 编辑型短文分栏 / field note 照片 / 证据特写 / 结语 / 章节分隔 / hero 问句。用于观点 / 书摘 / 旅行 / 生活方式 / 文化 / 品牌故事 / 深度解释。触发："做个杂志感卡 / 公众号封面 / 留白卡 / 编辑型卡 / 引言卡"。NOT 强运营 KPI 卡，NOT cyber/工业科技调，NOT 商业大字海报。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个杂志感卡"
  - "公众号封面"
  - "留白卡"
  - "编辑型卡"
  - "引言卡"
  - "电子墨水风卡"
  - "纸感卡"
related_patterns: social-card-quote, social-card-image-led
---

# Social Card Editorial Template

Use this template for social cards that should feel editorial, literary, reflective, premium, or magazine-like.

## Use When

- 小红书 / 公众号 / 社媒封面需要杂志感、纸感、留白、标题张力。
- 内容是观点、书摘、旅行、生活方式、文化、品牌故事、深度解释。
- 图片、引用、标题、短段落需要共同构成一张“可保存”的卡片。
- The artifact is fixed-canvas and will be delivered as HTML-to-image.

## Avoid When

- The card is highly operational, KPI-heavy, or dashboard-like.
- The content needs dense tables, multiple metrics, or system UI explanation.
- The user asks for a loud commercial poster or cyber/industrial tech look.

## Required Reading

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only if you need to inspect visual rhythm or layout relationships. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or WebGL behavior wholesale.

## Design Strategy

This template offers an editorial stance, not a fixed layout. Start from the current brief and choose one card role:

- cover / issue cover
- pull quote / thesis
- editorial essay split
- field note photo
- evidence feature
- closing note
- section divider
- hero question

Then adapt the card around the chosen role.

## Layout Bias

Prefer:

- large title blocks with intentional line breaks
- paper-like background or quiet monochrome surfaces
- hairline rules, issue strips, captions, marginal notes
- one strong image crop or one dominant quote
- restrained accent marks rather than decorative stickers

Avoid:

- generic rounded card grids
- under-filled portrait canvases
- treating photos as small decorative thumbnails
- adding ornamental Chinese motifs without content reason

## Platform / Size

Use `canvas-and-device.md` to select the exact output size. For Xiaohongshu/RED, WeChat covers, or other platform-specific surfaces, do not hard-code sizes in this template.
