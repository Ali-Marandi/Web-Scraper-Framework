---
name: social-card-screenshot-explainer
description: 截图 / UI / 工具流解释类社交卡 — 必须给截图一个"舞台"：可读裁切 + 标注层级 + 出现的理由。骨架：封面 + 大截图 + 3 个标注 / 截图裁切 + 放大细节 + 结论 / before-after 截图对 / 产品 UI 框 + 编号 callout / 3 步工作流。截图要大到手机能看清，箭头节制，加一个 takeaway 标题。触发："做个工具教程卡 / AI 工作流卡 / UI 解释卡 / 截图说明卡 / before-after 卡"。NOT 原图直接丢上画布，NOT 装饰性无关截图。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个工具教程卡"
  - "AI 工作流卡"
  - "UI 解释卡"
  - "截图说明卡"
  - "before-after 卡"
  - "产品功能拆解卡"
related_patterns: social-card-swiss
---

# Social Card Screenshot Explainer

Use for tool walkthroughs, product UI explanations, app feature breakdowns, AI workflow screenshots, or before/after UI captures.

## Core Rule

Never drop a raw screenshot onto the canvas and call it designed. A screenshot needs a stage, readable crop, annotation hierarchy, and a reason to be there.

## Structure Options

- cover + large screenshot + 3 annotations
- screenshot crop + zoomed detail + conclusion
- before / after screenshot pair
- product UI frame + numbered callouts
- 3-step workflow with one screenshot per step

## Must Do

- Keep the screenshot large enough to inspect on phone.
- Crop irrelevant browser chrome unless it helps context.
- Use device/browser frames only when they clarify the source.
- Use arrows/callouts sparingly; labels must not cover key UI.
- Add one takeaway title so the card is not just a screenshot.

## Avoid

- Tiny unreadable UI captures.
- Too many callout bubbles.
- Fake product screenshots.
- Decorative screenshots unrelated to the point.

## Related Pattern

Use `social-card-swiss` as the closest pattern if a visual reference is needed.

## Pattern Source Rule

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only when you need concrete layout rhythm, spatial relationships, or interaction/annotation behavior that this markdown cannot fully specify. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or styling wholesale.
