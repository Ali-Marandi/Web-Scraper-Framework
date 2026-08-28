---
name: Canvas and Device Constraints
description: Shared sizing, viewport, device-ratio, and export-surface rules for design artifacts.
mode: reference
platform: any
scenario: canvas-device-constraints
preview:
  type: none
default_for:
  - device size
  - viewport
  - canvas
  - resolution
  - aspect ratio
  - phone frame
  - desktop frame
  - export size
  - 尺寸
  - 分辨率
  - 画布
  - 手机比例
  - 导出尺寸
fidelity: system
---

# Canvas and Device Constraints

Use this shared reference whenever a design artifact includes device previews, fixed export sizes, phone frames, dashboard canvases, deck canvases, social cards, long images, or image-export surfaces.

Core rule:

```text
Artifact canvas ≠ device screen canvas ≠ export surface
```

A flow diagram may use a wide canvas. A phone preview inside it must still preserve a real phone ratio. A social card may use a fixed image export ratio. A dashboard may use a desktop viewport. Do not stretch everything into generic cards.

---

## Extensible size registry

This file is the canonical place for platform size presets. Do not delete it when simplifying routing. Add new platform presets here instead of scattering dimensions across artifact skills.

Use this registry for:

- Xiaohongshu / RED covers, notes, long images, and share cards
- WeChat article covers, article images, and long images
- Posters, flyers, social cards, and story images
- Mobile app, mobile web, and H5 viewports
- Desktop web, dashboard, and deck canvases

When a platform has multiple valid sizes, record them as named presets. Artifact skills should reference these presets instead of hard-coding dimensions.

Recommended preset marker format:

```html
<section data-platform="xhs" data-preset="cover-3x4" data-export-ratio="3:4">
<section data-platform="xhs" data-preset="portrait-4x5" data-export-ratio="4:5">
<section data-platform="xhs" data-preset="square" data-export-size="1080x1080">
<section data-platform="wechat" data-preset="article-cover">
<section data-platform="poster" data-preset="a4-portrait">
```

### Current social/export presets

```text
Social square:         1080 × 1080
Social portrait:       1080 × 1350
Story / vertical:      1080 × 1920
Xiaohongshu cover:     3:4 or 4:5
Xiaohongshu square:    1:1, usually 1080 × 1080
Xiaohongshu long image: width 1080, height content-driven
WeChat long image:     width 750 or 1080, height content-driven
Poster portrait:       ratio-driven, preset required
```

If a user provides a platform-specific size, use the user-provided size and add it to this registry if it is likely to be reused.

### User-provided Chinese social media presets

These presets are collected from the user's provided social-media size reference image. Treat them as practical production presets, not as immutable official platform specifications. If a platform updates its recommended sizes, update this section.

#### Xiaohongshu / RED

| Preset | Size | Ratio | Use |
|---|---:|---:|---|
| `xhs-avatar` | 400 × 400 | 1:1 | 头像 |
| `xhs-profile-background` | 1000 × 800 | 5:4 | 个人背景图 |
| `xhs-note-cover-portrait` | 1242 × 1660 | ~3:4 | 图文封面，竖版 |
| `xhs-note-cover-square` | 1080 × 1080 | 1:1 | 图文封面，方版 |
| `xhs-note-cover-landscape` | 2560 × 1440 | 16:9 | 图文封面，横版 |
| `xhs-video-cover-portrait` | 1080 × 1440 | 3:4 | 视频封面，竖版 |
| `xhs-video-cover-landscape-4x3` | 1440 × 1080 | 4:3 | 视频封面，横版；source image labels it as 3:4, but the pixel ratio is 4:3 |
| `xhs-video-cover-landscape-16x9` | 1920 × 1080 | 16:9 | 视频封面，横版 / widescreen |

Recommended markers:

```html
<section data-platform="xhs" data-preset="xhs-note-cover-portrait" data-export-size="1242x1660" data-export-ratio="3:4">
<section data-platform="xhs" data-preset="xhs-note-cover-square" data-export-size="1080x1080" data-export-ratio="1:1">
<section data-platform="xhs" data-preset="xhs-note-cover-landscape" data-export-size="2560x1440" data-export-ratio="16:9">
<section data-platform="xhs" data-preset="xhs-video-cover-portrait" data-export-size="1080x1440" data-export-ratio="3:4">
```

#### Douyin / TikTok China

| Preset | Size | Ratio | Use |
|---|---:|---:|---|
| `douyin-avatar` | 400 × 400 | 1:1 | 头像 |
| `douyin-profile-background` | 1125 × 633 | ~16:9 | 个人背景图 |
| `douyin-cover-portrait-3x4` | 1242 × 1660 | ~3:4 | 封面，竖版 |
| `douyin-cover-portrait-9x16` | 1080 × 1920 | 9:16 | 封面，竖版 |
| `douyin-cover-landscape-16x9` | 1080 × 608 | ~16:9 | 封面，横版 |

Recommended markers:

```html
<section data-platform="douyin" data-preset="douyin-cover-portrait-9x16" data-export-size="1080x1920" data-export-ratio="9:16">
<section data-platform="douyin" data-preset="douyin-cover-landscape-16x9" data-export-size="1080x608" data-export-ratio="16:9">
```

#### WeChat ecosystem

| Preset | Size | Ratio | Use |
|---|---:|---:|---|
| `wechat-official-account-avatar` | 240 × 240 | 1:1 | 公众号头像 |
| `wechat-official-account-cover` | 900 × 383 | ~2.35:1 | 公众号封面 |
| `wechat-official-account-thumbnail` | 200 × 200 | 1:1 | 公众号小图 |
| `wechat-official-account-qrcode-card` | 600 × 600 | 1:1 | 公众号二维码名片 |
| `wechat-official-account-guide-image` | 1080 × 300 | 18:5 | 公众号内容引导图 |
| `wechat-channels-cover-portrait` | 1080 × 1260 | 6:7 | 视频号封面，竖版 |
| `wechat-channels-cover-landscape` | 1080 × 608 | ~16:9 | 视频号封面，横版 |
| `wechat-miniprogram-cover` | 520 × 416 | 5:4 | 小程序封面 |
| `wechat-moments-cover` | 1280 × 1184 | ~1.08:1 | 朋友圈封面 |

Recommended markers:

```html
<section data-platform="wechat" data-preset="wechat-official-account-cover" data-export-size="900x383">
<section data-platform="wechat" data-preset="wechat-official-account-guide-image" data-export-size="1080x300">
<section data-platform="wechat-channels" data-preset="wechat-channels-cover-portrait" data-export-size="1080x1260" data-export-ratio="6:7">
<section data-platform="wechat-moments" data-preset="wechat-moments-cover" data-export-size="1280x1184">
```

---

## Default viewport presets

```text
iOS default:       390 × 844
iOS large:         430 × 932
iOS small:         375 × 812

Android default:   360 × 800
Android large:     412 × 915

Mobile web / H5:   390 × 844
Tablet:            768 × 1024
Desktop web:       1440 × 900
Dashboard:         1440 × 1024
Deck:              1600 × 900
Deck HD:           1920 × 1080

Social square:     1080 × 1080
Social portrait:   1080 × 1350
Story / vertical:  1080 × 1920
Xiaohongshu cover: 1242 × 1660, 1080 × 1080, 2560 × 1440
Douyin cover:      1242 × 1660, 1080 × 1920, 1080 × 608
WeChat OA cover:   900 × 383
WeChat guide:      1080 × 300
WeChat Channels:   1080 × 1260 or 1080 × 608
Long image:        width 1080, height content-driven
```

---

## Scenario defaults

### Prototype

- Mobile app and mobile web previews default to `390 × 844`.
- Android-specific previews default to `360 × 800`.
- Desktop web previews default to `1440 × 900`.
- Dashboard previews default to `1440 × 1024`.
- Flow diagrams may use a wide canvas.
- Screen previews inside flow diagrams must keep device aspect ratio.

### Tool H5

- Canonical surface is mobile portrait.
- Default mobile viewport: `390 × 844`.
- Desktop view should either center a realistic mobile frame or intentionally expand the experience.
- Do not leave a mobile column floating in a large empty desktop canvas.
- Result/share cards should use explicit export ratios.

### Content Page

- Long-form HTML is responsive.
- WeChat article layout is mobile-first and editor-safe.
- Generic long image uses explicit width and content-driven height when requested.
- Xiaohongshu covers, notes, and fixed-card sequences use `social-card.md`, not `content-page.md`.

### Deck

- Default deck canvas: `1600 × 900`.
- HD deck export: `1920 × 1080`.
- Deck viewport should scale to fit the browser, not reflow like a webpage.

### Landing Page

- Responsive web first.
- Validate at `375px`, `768px`, and `1280px`.
- Product screenshots or device mockups must preserve their own viewport ratios.

---

## Device frame rules

When showing mobile screens:

- preserve aspect ratio
- keep safe margins
- include status/nav bars only when useful
- keep tap targets readable
- avoid shrinking full screens until text becomes unreadable
- use simplified mini-previews when space is limited
- use exact-ratio full previews in screen inventory, prototype, or tool preview sections

Recommended markers:

```html
<section data-device="ios" data-viewport="390x844">
<section data-device="ios-large" data-viewport="430x932">
<section data-device="android" data-viewport="360x800">
<section data-platform="mobile-web" data-viewport="390x844">
<section data-platform="desktop-web" data-viewport="1440x900">
<section data-platform="dashboard" data-viewport="1440x1024">
<section data-export-size="1080x1920">
<section data-export-ratio="3:4">
```

Recommended CSS:

```css
.phone-frame {
  width: min(390px, 100%);
  aspect-ratio: 390 / 844;
}

.phone-frame[data-size="ios-large"] {
  width: min(430px, 100%);
  aspect-ratio: 430 / 932;
}

.phone-frame[data-size="ios-small"] {
  width: min(375px, 100%);
  aspect-ratio: 375 / 812;
}

.phone-frame[data-size="android"] {
  width: min(360px, 100%);
  aspect-ratio: 360 / 800;
}

.desktop-frame {
  aspect-ratio: 1440 / 900;
}

.dashboard-frame {
  aspect-ratio: 1440 / 1024;
}

.social-card[data-ratio="3:4"] {
  aspect-ratio: 3 / 4;
}

.social-card[data-ratio="4:5"] {
  aspect-ratio: 4 / 5;
}
```

---

## Flow diagram vs screen preview

For interaction flow diagrams:

- Use a wide canvas for the overall diagram.
- Use abstract nodes for minor actions and state changes.
- Use exact-ratio screen previews only for key screens.
- Do not draw every state as a full phone screen.
- Do not let phone previews become landscape cards.
- When the screen preview is too large for the flow diagram, use a compact node plus a separate exact-ratio screen inventory.

---

## Export surface rules

When the artifact is meant to be exported as an image:

- declare the export size or ratio explicitly
- keep important content inside safe margins
- test title readability at thumbnail size
- avoid tiny captions unless export resolution is high enough
- do not rely on browser viewport size for fixed social exports
- do not silently redesign during export

For long images:

- use stable card boundaries
- avoid content blocks that depend on viewport height
- keep vertical rhythm consistent
- set a clear export width, usually `1080px`

---

## Quality checklist

Before delivery, check:

- Is the artifact canvas appropriate for the scenario?
- Are device previews using realistic viewport ratios?
- Are mobile screens locked to phone proportions instead of arbitrary cards?
- Is the export surface declared when image export is expected?
- Does desktop fallback look intentional, not empty?
- Are phone previews readable at their displayed size?
- Are flow diagrams using abstract nodes when full device previews would hurt readability?
