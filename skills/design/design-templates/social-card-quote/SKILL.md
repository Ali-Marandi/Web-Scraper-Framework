---
name: social-card-quote
description: 一句话主导的社交卡 — 论点 / 引言 / 原则 / 关键问句 / 一句话洞察占满版心，配 source / 章节标签 / 边注 / 三个锚点。必须按语义断行（不靠自动 wrap），至少一个锚点防止 floating。触发："做个引言卡 / 论点卡 / 金句卡 / 原则卡 / hero 问句卡"。NOT 长段落伪装成引言，NOT 空洞鸡汤口号，NOT 居中文字无任何锚点结构。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个引言卡"
  - "论点卡"
  - "金句卡"
  - "原则卡"
  - "hero 问句卡"
  - "一句话卡"
  - "书摘卡"
related_patterns: social-card-editorial
---

# Social Card Quote / Thesis Template

Use when the page should carry one strong sentence, question, principle, or conclusion.

## Core Rule

The quote is the page. Do not bury it under decorations or explainers.

## Structure Options

- thesis sentence + source/context row
- hero question + short prompt
- quote + marginal note
- one-line principle + 3 tiny anchors
- section divider with large title

## Must Do

- Break lines semantically, not by random wrapping.
- Provide at least one anchor: date, section label, source, note, or footer marker.
- Keep whitespace intentional.
- Use `reference/title-and-breaking.md` for Chinese line breaks.

## Avoid

- Long paragraphs disguised as quotes.
- Empty motivational slogans.
- Centered text with no anchoring structure.
- Overusing quote marks when the sentence is not a quote.

## Related Pattern

Use `social-card-editorial` as the closest pattern if a visual reference is needed.

## Pattern Source Rule

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only when you need concrete layout rhythm, spatial relationships, or interaction/annotation behavior that this markdown cannot fully specify. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or styling wholesale.
