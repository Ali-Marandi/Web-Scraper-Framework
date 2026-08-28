---
name: social-card-data-kpi
description: 数据驱动的小红书 / 公众号社交卡 — 一个 hero 数字 + 解释、KPI 塔（3-5 指标堆叠）、前后对比、横向迷你条形图、排行榜带高亮行、ROI 卡。必须标单位 / 时间窗 / 数据来源，必须一个数字视觉主导。触发："做个 KPI 卡 / 数据卡 / 排行榜卡 / 增长卡 / 复盘数字卡"。NOT 表情绪 / 引言 / 图主导的卡，NOT chartjunk。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个 KPI 卡"
  - "数据卡"
  - "排行榜卡"
  - "增长卡"
  - "复盘数字卡"
  - "前后对比卡"
  - "ROI 卡"
related_patterns: social-card-swiss
---

# Social Card Data / KPI Template

Use when the card is driven by numbers, rankings, growth, score, ROI, benchmark, funnel, or result summary.

## Core Rule

A data card must have one clear claim. Do not show numbers without explaining what decision or insight they support.

## Structure Options

- one hero number + explanation
- KPI tower: 3-5 stacked metrics
- before / after metric comparison
- horizontal bar mini-chart
- ranking table with one highlighted row
- ROI/result card with assumptions

## Must Do

- Label units, time windows, and data source / placeholder status.
- Make one number visually primary.
- Use consistent alignment and numeric tabular spacing where possible.
- If numbers are invented placeholders, mark them as sample/demo.

## Avoid

- Fake market size, fake growth rate, fake client proof.
- Chartjunk.
- Tiny chart labels.
- More than 5 competing metrics on one social card.

## Pattern Source Rule

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only when you need concrete layout rhythm, spatial relationships, or interaction/annotation behavior that this markdown cannot fully specify. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or styling wholesale.
