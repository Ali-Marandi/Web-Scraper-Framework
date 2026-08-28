---
name: video-shortform
description: Pro-camera HUD mockup template — full-viewport black canvas wrapping a real video with monospace overlays (corner brackets, top status bar, side AF/exposure columns, bottom timecode + aperture/shutter/ISO row, vertical 8-filter wheel, animated reticle). For cinematographer portfolios, camera-app demos, LUT pack previews, filter-look auditions. NOT a TikTok/Reels mockup, NOT a storyboard, NOT a shot list, NOT a script document. The chrome wraps real footage — never a div placeholder.
visibility: public
mode: template
carrier: web-page
scenario: video-showcase
pattern_source: video-shortform.html
source_priority: skill-first
triggers:
  - "做个相机 HUD mockup"
  - "包视频的相机取景框"
  - "LUT 预览页"
  - "cinematographer 作品包装"
  - "滤镜审片页"
---

# Video Shortform Template

Camera-HUD mockup that **wraps a real piece of footage** with pro-camera (RED / ARRI / Blackmagic / Sony Cine-flavored) viewfinder chrome and lets the user audition 8 film-emulation looks against it.

This template is **not** a TikTok / Reels / 视频号 / 抖音 social mockup, **not** a storyboard, **not** a shot list, **not** a 分镜 / 脚本 document, **not** a vertical-video ad poster.

---

## ⚠️ Three Pre-flight Gates — clear all three BEFORE writing code

### Gate 1 — Is this actually a HUD job, or a script/storyboard job?

Trigger words that mean **this skill is wrong** and you should refuse:

| User says | What they actually want | Correct response |
|---|---|---|
| 短视频脚本 / 视频脚本 / script doc | shot-by-shot text with VO / timing | refuse, suggest a doc template or `wireframe-sketch` |
| 分镜 / storyboard / shot list | frame-by-frame thumbnails + descriptions | refuse, suggest a storyboard layout |
| 短视频封面 / 视频封面 / video cover | static image / social card | refuse, suggest `social-card-*` skills |
| 视频号/抖音/小红书视频卡 | feed-style mockup with profile/likes/comments | refuse, suggest a social card |
| 视频海报 / video poster | static print-style poster | refuse, suggest `social-card-image-led` |
| 调色 demo / LUT 预览 / 滤镜对比 / cinematographer portfolio / camera-app demo / 拍摄取景器 / viewfinder | ✅ this is the right skill | proceed |

If the user's words straddle "脚本 / 拍摄 HUD" ambiguity, **stop and ask**:
> "你要的是 (a) 拍摄取景器 HUD wrap 一段真视频做调色/镜头展示,还是 (b) 视频脚本/分镜的文档?这个 skill 只做 (a),(b) 我会换别的 skill 来做。"

Don't guess. Wrong skill = full rewrite.

### Gate 2 — Where is the video coming from?

**The chrome wraps a real `<video>`. A `<div>` with `[视频画面]` text inside is not acceptable** — that's what B48 did and the whole point of this template was lost.

Decision tree:

1. **User gave a video file / URL** → use it directly in `<video src="...">`
2. **User gave nothing but is OK with sample footage** → pick ONE from the Hotlink List below, paste the URL into `<video src>`, add a one-liner "示例素材:Big Buck Bunny / 公共测试视频,替换为自己的素材后效果一致"
3. **User wants offline / self-contained** → `curl -L -o sample.mp4 <hotlink>` into the case folder, then `<video src="sample.mp4">`
4. **Unclear** → stop and ask which of 1/2/3 they want

#### Hotlink List (public sample footage, verified 200 OK as of 2026-06)

Pick in this priority order. The historical "Google Cloud gtv-videos-bucket" URLs are **dead** (anonymous access revoked) — don't use them even though they're widely cited online.

```
# Mozilla MDN — most reliable, CORS-friendly, h264
https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4   # ~30s, 16:9, CC0 flower close-up

# test-videos.co.uk — purpose-built test files, multiple sizes
https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4   # 10s, 720p, ~1MB
https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4   # 10s, 360p, ~1MB tiny fallback

# w3.org — cinematic trailers, longer playback
https://media.w3.org/2010/05/sintel/trailer.mp4                            # Sintel trailer, ~52s, cinematic 16:9

# W3Schools — well-known, oldest standby
https://www.w3schools.com/html/mov_bbb.mp4                                 # ~10s BBB clip, h264
https://www.w3schools.com/html/movie.mp4                                   # generic test clip
```

If you need to verify before using: `curl -sIL -o /dev/null -w "%{http_code} %{content_type}\n" <url>` — expect `200 video/mp4`. If a URL returns 403 / 404 / 000, fall to the next in the list. Don't ship a dead URL.

**Required `<video>` attributes** (or autoplay won't fire on most browsers):

```html
<video src="<hotlink-or-local>"
       autoplay muted loop playsinline
       preload="auto"
       style="width:100%;height:100%;object-fit:cover">
</video>
```

`muted` is mandatory for autoplay on Chrome/Safari/Mobile. `playsinline` is mandatory for iOS not to take the video fullscreen.

### Gate 3 — What's in the filter wheel?

8 filters is the canonical count (reference uses 8). For each, declare:
- Display name (3–6 chars, e.g. `KODAK 2383`, `FUJI 3510`, `LOG`, `REC 709`)
- CSS filter recipe to apply to the video: `filter: contrast(1.1) saturate(.85) sepia(.15) hue-rotate(-5deg) ...`
- Optionally: corresponding camera-setting deltas (F-stop / shutter / ISO / EV) that update in the HUD when the filter is active

If user didn't specify, default to these 8 (covers the common LUT palette space):

```
01 LOG         filter: contrast(.85) saturate(.7) brightness(1.05);
02 REC 709     filter: none;                       /* baseline */
03 KODAK 2383  filter: contrast(1.1) saturate(.9) sepia(.08) hue-rotate(-4deg);
04 FUJI 3510   filter: contrast(1.05) saturate(1.1) hue-rotate(8deg);
05 ARRI K1S1   filter: contrast(1.15) saturate(.85) brightness(.95);
06 TEAL ORANGE filter: contrast(1.2) saturate(1.2) hue-rotate(-12deg);
07 B&W         filter: grayscale(1) contrast(1.15);
08 BLEACH BP   filter: saturate(.3) contrast(1.25) brightness(1.05);
```

---

## Must-Have HUD Interactions — none of these are optional

If any is missing, the artifact is incomplete. **B48 was missing all 6**.

1. **Real `<video>` element** (Gate 2 enforces). Not a div, not a poster image, not a bg image.
2. **Filter wheel switching** — scroll wheel + ArrowUp/ArrowDown + click each dot cycles through the 8 filters; active filter highlighted in record-red.
3. **Timecode running at 24/25 fps** — `HH:MM:SS:FF` format, `requestAnimationFrame`-driven, tabular-nums, restarts with the video loop.
4. **Reticle pulse** — slow scale + opacity loop, accent stroke (record-red **not green**), animation paused under `prefers-reduced-motion`.
5. **Filter-switch brightness flash** — 80–120 ms white flash over the video on filter change (simulates exposure re-meter); skip if `prefers-reduced-motion`.
6. **Battery drain** — top-right battery readout decreases 1% every 8–12s, stops at 5%, turns red ≤ 20%.

Optional but encouraged: REC pulse (red dot blinks at 1Hz when "recording"), focus-confirm beep when filter changes, histogram glyph in a corner.

---

## Must-Lock Visual Rules — no substitutions

| Lock | Value | Why |
|---|---|---|
| Background | pure `#000` | Not `#0a0a0a`, not a dark gray. Black canvas is the viewfinder. |
| Foreground type | `#e0e0e0` / `#fff` | One light tone only. |
| Single accent | **record-red `#ff3b30`** | Used for REC pill, active filter, reticle, warning states. **Not green, not blue, not teal** — record-red is the entire visual signature of this template. |
| Type stack | mono only (`SF Mono` / `JetBrains Mono` / `Menlo` / `IBM Plex Mono`) | No sans for HUD numerics. CJK script-overlay is the only sans use, and that overlay is itself rare. |
| HUD opacity | secondary readouts ≈ 45% | Video stays protagonist. |
| Border style | 4 corner brackets, never solid border | Solid border = monitor frame, not viewfinder. |
| Filter wheel | vertical, ~8 dots, right side | Horizontal carousel = social UI, wrong register. |

---

## Anti-patterns (self-check against B48's failure modes)

- [ ] `<video>` is missing or replaced with `<div>` + text → reject, go back to Gate 2
- [ ] Accent color is anything other than `#ff3b30` (e.g. green, teal, blue) → revert
- [ ] HUD numerics are static strings (timecode, ISO, battery) → make them live
- [ ] Filter wheel has no interaction (no scroll/arrow/click handler) → wire it up
- [ ] Script / 镜头 / VO / 旁白 text block layered on top → wrong skill, refuse the job at Gate 1
- [ ] Social UI (profile, likes, captions, music attribution) → wrong skill, refuse
- [ ] Centered Play/Pause button → this is a viewfinder, kill it
- [ ] More than one accent color → revert to record-red only
- [ ] Glassmorphism / gradient / glow shadow on HUD elements → camera chrome is flat, kill it
- [ ] Sans-serif on HUD readouts → switch to mono
- [ ] Yellow / amber / cyan HUD tint to "look futuristic" → flat white/gray + record-red only
- [ ] No `muted playsinline autoplay loop` on `<video>` → won't autoplay, add them

---

## Required Reading

Read this `SKILL.md` first, end to end. Then read `video-shortform.html` for the actual implementation patterns: corner-bracket geometry, the timecode HH:MM:SS:FF ticker logic, the 8-filter wheel scroll/keyboard handlers, the reticle pulse keyframes, the battery drain interval, and the filter-switch brightness flash.

Do not copy:
- the fallback video URLs from the reference (use the Hotlink List above)
- the placeholder filter metadata (use Gate 3's defaults or the user's spec)
- class names wholesale (rename for the project)

---

## Design Strategy

Lock the experience contract before writing:

1. **Source video** (Gate 2) — what footage, what aspect ratio, how long?
2. **Filter set** (Gate 3) — names + CSS filter recipes for all 8
3. **HUD honesty** — which numbers react to filter change, which are decorative?
4. **Aspect** — 16:9 desktop default; if vertical 9:16, the side columns crowd, switch to top/bottom-only HUD strips

---

## Layout Bias

Prefer:
- pure black canvas; mono only; record-red accent
- 4 corner brackets at 24–32 px from video edges
- secondary HUD at ~45% opacity so footage dominates
- vertical 8-filter wheel right side, ~20 px dots
- subtle film-grain `::after` overlay (5–8% opacity max, multiply blend)
- timecode bottom-center, tabular-nums, bigger than other HUD elements

Avoid: everything in the Must-Lock and Anti-patterns tables above.

---

## Platform / Size

Full-viewport, responsive to window aspect. Best on desktop with a 16:9 source. Portrait video works but side columns crowd — move HUD strips to top/bottom. Mobile renders but keyboard cycling is lost — add touch swipe up/down on the filter wheel.
