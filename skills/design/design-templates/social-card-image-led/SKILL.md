---
name: social-card-image-led
description: 图片主导的社交卡 — 图是证据 / 氛围 / 产品 / 物件 / 地点 / 钩子，文字让位。骨架：全出血 + 安全标题块 / 大图井 + 编辑标题 / 图片裁切 + caption 账本 / 产品物件照 + 三个证据点 / 旅行地点 + 地图或位置元数据。必须保护人脸 / 产品 / UI / 关键细节不被文字盖住。触发："做个图片卡 / 照片封面 / 产品图卡 / 旅行卡 / 物件卡 / 证据图卡"。NOT 没图片只能补 stock 装饰，NOT 用蒙版强行救烂图。
visibility: public
mode: template
carrier: fixed-image
scenario: social-content
pattern_source: pattern.html
source_priority: skill-first
triggers:
  - "做个图片卡"
  - "照片封面"
  - "产品图卡"
  - "旅行卡"
  - "物件卡"
  - "证据图卡"
  - "全出血图卡"
related_patterns: social-card-editorial
---

# Social Card Image-Led Template

Use when the image is the evidence, mood, product, object, place, or hook.

## Core Rule

The image must do real work. If it is only decoration, choose another template.

## Structure Options

- full-bleed image + safe title block
- large image well + editorial title
- image crop + caption ledger
- product/object photo + three evidence points
- travel/place image + map or location metadata

## Must Do

- Protect faces, products, UI, and important image details from text overlay.
- Use overlays only when contrast is genuinely needed.
- Keep title and image in a clear relationship.
- If image quality is poor, crop less aggressively or switch to a text-led recipe.

## Avoid

- Text covering faces or key product areas.
- Dark overlay as a lazy fix for all images.
- Decorative stock image with no content relation.
- Tiny image thumbnails on a portrait canvas.

## Related Pattern

Use `social-card-editorial` as the closest pattern if a visual reference is needed.

## Pattern Source Rule

Read this `SKILL.md` first. Do **not** read `pattern.html` by default.

Read `pattern.html` only when you need concrete layout rhythm, spatial relationships, or interaction/annotation behavior that this markdown cannot fully specify. When read, extract patterns only; do not copy DOM, CSS classes, exact spacing, placeholder copy, or styling wholesale.
