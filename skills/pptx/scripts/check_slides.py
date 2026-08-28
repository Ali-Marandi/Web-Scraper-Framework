#!/usr/bin/env python3
"""CLI for slide dimension / overflow / blank-region / overlap checks.

Renders each HTML slide in headless Chromium (via Playwright) at 1280x720 and
reports vertical overflow, large blank regions, and text-vs-text overlaps.
Standalone — does not import from any sibling agent package.

Usage:
  # Check specific files (preferred — matches whatever naming the brief uses):
  python check_slides.py /work/slides/slide_01.html /work/slides/slide_02.html

  # Check every *.html in a directory (sorted by filename):
  python check_slides.py --dir /work/slides

  # Restrict to a few positions when --dir is used (matches files whose stem
  # ends in those numbers, e.g. `1.html`, `slide_01.html`):
  python check_slides.py --dir /work/slides --positions 1 3 5

  # JSON output for downstream tooling:
  python check_slides.py --dir /work/slides --json --output /work/check.json

Stdout is a compact text report by default; pass --json for the raw measurement
dict per file. Exit code is 0 when every checked slide fits the viewport
vertically with no large blank / text overlap, otherwise 1.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import traceback
from pathlib import Path

_VIEWPORT_W = 1280
_VIEWPORT_H = 720
_MAX_CONCURRENCY = 81
_PROXY = {"server": "http://httpproxy.glm.ai:8888"}


_TEXT_OVERLAP_JS = r"""
(opts) => {
    const minOverlapPx = opts.minOverlapPx || 3;
    const maxPairs = opts.maxPairs || 50;
    // Relative overlap threshold: the intersection must consume at least
    // `relMin` of the smaller element's corresponding side on BOTH axes.
    // Suppresses line-height bleed where vertically-stacked siblings share
    // 3-5px of line-box overhang without true visual collision.
    const relMin = opts.relMin != null ? opts.relMin : 0.10;
    // Decorative-text thresholds (mirrors genspark html2pptx checkTextOverlaps):
    // - opacity ≤ 0.2 → watermark / ghost layer
    // - font-size ≥ 150px → giant ghost numeral / chapter mark
    const decorOpacity = opts.decorOpacity != null ? opts.decorOpacity : 0.2;
    const decorFontPx = opts.decorFontPx || 150;

    function ownText(el) {
        let t = '';
        for (const n of el.childNodes) {
            if (n.nodeType === Node.TEXT_NODE) t += n.textContent;
        }
        return t.trim();
    }
    // Effective opacity = product of opacity along ancestor chain (CSS-correct).
    // Returns 0 if any ancestor is display:none / visibility:hidden.
    function effectiveOpacity(el) {
        let op = 1;
        let cur = el;
        while (cur && cur !== document.body) {
            const s = getComputedStyle(cur);
            if (s.display === 'none' || s.visibility === 'hidden') return 0;
            const o = parseFloat(s.opacity);
            if (!isNaN(o)) op *= o;
            cur = cur.parentElement;
        }
        return op;
    }
    // First ancestor (incl. self) that establishes a stacking context with a
    // numeric z-index. Returns 0 if none — matches "auto" → 0 for sibling
    // comparison purposes. We don't try to fully simulate the stacking algorithm;
    // this is a heuristic to skip *intentional* layered decorations.
    function effectiveZ(el) {
        let cur = el;
        while (cur && cur !== document.body) {
            const s = getComputedStyle(cur);
            if (s.position && s.position !== 'static') {
                const z = parseInt(s.zIndex, 10);
                if (!isNaN(z)) return z;
            }
            cur = cur.parentElement;
        }
        return 0;
    }
    // Restrict reporting to text inside the slide canvas — body padding / preview
    // gaps / off-canvas overflow shouldn't surface as overlap noise.
    const canvas = document.querySelector('.slide, .slide-canvas');
    const canvasRect = canvas ? canvas.getBoundingClientRect() : null;
    function insideCanvas(r) {
        if (!canvasRect) return true;
        // Require ≥50% of the rect's area to lie inside the canvas.
        const x = Math.max(r.x, canvasRect.left);
        const y = Math.max(r.y, canvasRect.top);
        const w = Math.min(r.x + r.w, canvasRect.right) - x;
        const h = Math.min(r.y + r.h, canvasRect.bottom) - y;
        if (w <= 0 || h <= 0) return false;
        return (w * h) >= 0.5 * (r.w * r.h);
    }

    const items = [];
    const walker = document.querySelectorAll('body *');
    for (const el of walker) {
        const text = ownText(el);
        if (!text) continue;
        const op = effectiveOpacity(el);
        if (op === 0) continue;
        const cs = getComputedStyle(el);
        const fontPx = parseFloat(cs.fontSize) || 0;
        const decorative = op <= decorOpacity || fontPx >= decorFontPx;
        const z = effectiveZ(el);
        const rects = el.getClientRects();
        if (!rects.length) continue;
        for (const r of rects) {
            if (r.width < 2 || r.height < 2) continue;
            const rect = {x: r.x, y: r.y, w: r.width, h: r.height};
            if (!insideCanvas(rect)) continue;
            items.push({
                el, text, decorative, z, fontPx,
                tag: el.tagName.toLowerCase(),
                rect,
            });
        }
    }

    function rel(a, b) { return a.contains(b) || b.contains(a); }
    function inter(r1, r2) {
        const x = Math.max(r1.x, r2.x);
        const y = Math.max(r1.y, r2.y);
        const w = Math.min(r1.x + r1.w, r2.x + r2.w) - x;
        const h = Math.min(r1.y + r1.h, r2.y + r2.h) - y;
        if (w < minOverlapPx || h < minOverlapPx) return null;
        // Relative gate: overlap must occupy ≥ relMin of the smaller side.
        if (w < relMin * Math.min(r1.w, r2.w)) return null;
        if (h < relMin * Math.min(r1.h, r2.h)) return null;
        return {x, y, w, h};
    }
    function trunc(s, n) { return s.length > n ? s.slice(0, n) + '…' : s; }
    function fmtRect(r) {
        return {
            x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.w), h: Math.round(r.h),
        };
    }

    // Dedupe by element pair: a 4-line <p> overlapping another 4-line <p> via
    // getClientRects() would otherwise produce up to 16 entries. Keep the
    // largest overlap rect per (elA, elB) pair.
    const seen = new Map();  // key → {a, b, overlap}
    for (let i = 0; i < items.length; i++) {
        for (let j = i + 1; j < items.length; j++) {
            const A = items[i], B = items[j];
            if (A.el === B.el) continue;
            if (rel(A.el, B.el)) continue;
            // Skip intentional layered decorations (genspark parity).
            if (A.decorative || B.decorative) continue;
            if (A.z !== B.z) continue;
            const ov = inter(A.rect, B.rect);
            if (!ov) continue;
            // Stable pair key: use DOM position to order.
            const order = A.el.compareDocumentPosition(B.el) & Node.DOCUMENT_POSITION_FOLLOWING;
            const first = order ? A : B;
            const second = order ? B : A;
            const key = first.tag + ' ' + first.text + ' '
                      + second.tag + ' ' + second.text;
            const area = ov.w * ov.h;
            const prev = seen.get(key);
            if (!prev || area > prev._area) {
                seen.set(key, {
                    a: {tag: first.tag, text: trunc(first.text, 80), rect: fmtRect(first.rect)},
                    b: {tag: second.tag, text: trunc(second.text, 80), rect: fmtRect(second.rect)},
                    overlap: fmtRect(ov),
                    _area: area,
                });
            }
        }
    }
    const overlaps = [];
    for (const v of seen.values()) {
        delete v._area;
        overlaps.push(v);
        if (overlaps.length >= maxPairs) break;
    }
    return overlaps;
}
"""


def _detect_largest_blank(screenshot_bytes: bytes,
                          color_tolerance: int = 15,
                          downsample: int = 4,
                          decor_rects: list[dict] | None = None) -> dict | None:
    """Find the largest contiguous background-colored rectangle in a screenshot.

    Background color is sampled from the four corners (median). A pixel is
    "non-background" if its max channel diff from the sample exceeds
    `color_tolerance`. The image is downsampled by `downsample`× for the
    rectangle search (1280x720 → 320x180 by default), then results are scaled
    back to original pixels. Returns None on failure (e.g. PIL/numpy missing).

    `decor_rects` (list of {x, y, w, h} in screenshot pixels) marks regions
    occupied by decorative elements — those rects are forced to "non-
    background" in the mask so faint / ghost decoration that blends with the
    bg color does not register as a false blank patch.
    """
    try:
        import io
        import numpy as np
        from PIL import Image
    except Exception:
        return None
    try:
        img = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        H, W, _ = arr.shape
        if H < 8 or W < 8:
            return None
        corner = max(4, min(W, H) // 64)
        samples = np.concatenate([
            arr[:corner, :corner].reshape(-1, 3),
            arr[:corner, -corner:].reshape(-1, 3),
            arr[-corner:, :corner].reshape(-1, 3),
            arr[-corner:, -corner:].reshape(-1, 3),
        ], axis=0).astype(np.int32)
        bg = np.median(samples, axis=0)
        diff = np.abs(arr.astype(np.int32) - bg).max(axis=2)
        nonbg = (diff > color_tolerance).astype(np.uint8)

        # Mask out decorative element rects: their visual area is intentional
        # design, not blank. Without this, a low-opacity ghost numeral or
        # gradient blob whose pixels blend into bg would show up as one big
        # contiguous blank region.
        if decor_rects:
            for r in decor_rects:
                x0 = max(0, int(round(r.get("x", 0))))
                y0 = max(0, int(round(r.get("y", 0))))
                x1 = min(W, int(round(r.get("x", 0) + r.get("w", 0))))
                y1 = min(H, int(round(r.get("y", 0) + r.get("h", 0))))
                if x1 > x0 and y1 > y0:
                    nonbg[y0:y1, x0:x1] = 1

        s = max(1, downsample)
        Hd, Wd = H // s, W // s
        if Hd < 2 or Wd < 2:
            return None
        # Pool: cell is "blocked" if any underlying pixel is non-background.
        nonbg_d = nonbg[:Hd * s, :Wd * s].reshape(Hd, s, Wd, s).max(axis=(1, 3))

        heights = [0] * Wd
        best_area = 0
        best = (0, 0, 0, 0)  # x, y, w, h in downsampled units
        for r in range(Hd):
            row = nonbg_d[r]
            for c in range(Wd):
                heights[c] = 0 if row[c] else heights[c] + 1
            stack = []  # (start_index, height)
            for c in range(Wd + 1):
                cur = heights[c] if c < Wd else 0
                start = c
                while stack and stack[-1][1] > cur:
                    idx, h = stack.pop()
                    w = c - idx
                    area = w * h
                    if area > best_area:
                        best_area = area
                        best = (idx, r - h + 1, w, h)
                    start = idx
                stack.append((start, cur))

        x_d, y_d, w_d, h_d = best
        x, y, w, h = x_d * s, y_d * s, w_d * s, h_d * s
        return {
            "x": int(x), "y": int(y), "w": int(w), "h": int(h),
            "area_ratio": round((w * h) / float(W * H), 3),
            "bg_rgb": [int(c) for c in bg],
        }
    except Exception:
        return None


async def measure_slide_dimensions(html_content, viewport_width=1280, viewport_height=720, proxy=None,
                             detect_overlaps=True, detect_blank=True,
                             blank_min_area_ratio=0.25, blank_min_side=180,
                             overflow_tolerance_ratio=0.005, overflow_tolerance_px=3,
                             file_path: str | None = None):
    """Render HTML at the given viewport and report ACTUAL content width + height.

    Returns a dict with success bool, plus on success: width, height,
    viewport_width, viewport_height, overflow_x (px past viewport, 0 if fits),
    overflow_y (px past viewport, 0 if fits), `details` subdict with raw
    browser measurements, `overlaps` (when detect_overlaps): a list of
    text-vs-text overlapping pairs each shaped {a: {tag, text, rect}, b:
    {tag, text, rect}, overlap: {x,y,w,h}}, and `blank` (when detect_blank):
    {x, y, w, h, area_ratio, bg_rgb, flagged: bool} for the largest contiguous
    background-colored region. `flagged` is True only when area_ratio ≥
    blank_min_area_ratio AND min(w, h) ≥ blank_min_side.

    Notes:
        - Width and height are both measured (not assumed = viewport_*) and
          reported. Horizontal AND vertical overflow are flagged when content
          extends past the viewport beyond the tolerance buffer.
        - If the slide root uses `overflow:hidden` the inner content is clipped
          for the user — we measure content-bearing children to surface the
          underlying content size when possible. Elements clipped by any
          ancestor with `overflow:hidden|clip` have their rect intersected
          with the clipping box before contributing to overflow, so bleed
          decoration that's invisible to the user is not flagged.
        - Decorative elements are excluded from overflow measurement when
          ANY of these hold: (a) the element (or an ancestor) carries
          `data-decor` or `aria-hidden="true"`, (b) effective opacity along
          the ancestor chain is ≤ 0.2 (ghost / watermark layer). Authors
          should tag intentional background blobs, oversized ghost numerals,
          and bleed shapes with `data-decor` to silence false-positive
          overflow flags.
        - Overlap detection only flags pairs of visible text-bearing elements
          that are NOT in an ancestor/descendant relationship and whose
          bounding rects intersect by ≥3px on both axes (suppresses border
          touches) AND by ≥20% of the smaller element's corresponding side
          (suppresses line-height bleed in vertically-stacked siblings).
          Capped at 50 pairs per slide. Filters that mirror the
          genspark html2pptx checker:
            * effective opacity ≤ 0.2 → decorative watermark, skipped
            * font-size ≥ 150px → ghost numeral / chapter mark, skipped
            * different effective z-index → intentional layering, skipped
            * rect mostly outside `.slide` canvas (preview chrome / cropped
              overflow) → skipped
          Multi-line text pairs are deduped to one entry per element pair
          (largest overlap rect wins).
        - Blank detection samples background color from the four corners and
          finds the largest rectangle whose pixels are all within
          `color_tolerance` (15) of that color. Operates on a 4×-downsampled
          screenshot for speed. Decorative element rects (same opt-out as
          the overflow check: `data-decor` / `aria-hidden="true"`, plus
          elements whose effective opacity is ≤ 0.2) are forced to "non-
          background" in the mask, so faint ghost decoration that blends
          with the bg color is not flagged as a large blank region.
    """
    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, proxy=proxy)
            page = await browser.new_page()
            await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
            # When a real file path is supplied, navigate to it via file://
            # so relative resources (global.css, images/, fonts) resolve.
            # set_content has no base URL and would render the slide
            # unstyled — which collapses layouts and hides real overflow.
            if file_path:
                await page.goto(f"file://{file_path}")
            else:
                await page.set_content(html_content)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)
            dims = await page.evaluate("""() => {
                // Canvas = the .slide element. With overflow:hidden|clip, decorative
                // absolute children (background blobs, bleed shapes) extend past the
                // box but are visually clipped — using scrollWidth/Height would count
                // them as overflow. Instead: use the declared box as canvas, then
                // measure overflow from CONTENT-BEARING elements (text + media) only.
                const slides = document.querySelectorAll('.slide, .slide-canvas');
                const ContentTags = new Set(['IMG','SVG','VIDEO','CANVAS','PICTURE','IFRAME']);
                function ownText(el){
                    let t='';
                    for (const n of el.childNodes){
                        if (n.nodeType === Node.TEXT_NODE) t += n.textContent;
                    }
                    return t.trim();
                }
                function isContent(el){
                    if (ContentTags.has(el.tagName)) return true;
                    return ownText(el).length > 0;
                }
                // Effective opacity along the ancestor chain. Returns 0 if any
                // ancestor is display:none / visibility:hidden — collapses the
                // old isVisible check into the same signal.
                function effectiveOpacity(el){
                    let op = 1;
                    let cur = el;
                    while (cur && cur !== document.body){
                        const s = getComputedStyle(cur);
                        if (s.display === 'none' || s.visibility === 'hidden') return 0;
                        const o = parseFloat(s.opacity);
                        if (!isNaN(o)) op *= o;
                        cur = cur.parentElement;
                    }
                    return op;
                }
                // Three signals that an element is decorative and should not
                // contribute to overflow:
                //  1. Author opt-out via data-decor / aria-hidden="true".
                //  2. Effective opacity ≤ 0.2 (mirrors the text-overlap
                //     checker's ghost / watermark threshold).
                function isDecorative(el){
                    if (el.closest('[data-decor], [aria-hidden="true"]')) return true;
                    if (effectiveOpacity(el) <= 0.2) return true;
                    return false;
                }
                // Walk ancestors UP TO (but not including) the slide root;
                // if any inner ancestor clips overflow, intersect the rect
                // with the clipping box. Decoration that bleeds past an
                // inner card / panel and is hidden by overflow:hidden|clip
                // is invisible to the user and must not be flagged. We
                // intentionally do NOT clip by the .slide canvas itself —
                // even when .slide has overflow:hidden (it almost always
                // does), content that wants to extend past 1280x720 is
                // still bad layout and must surface as overflow.
                function visibleRect(el, slide){
                    let r = el.getBoundingClientRect();
                    let left = r.left, top = r.top, right = r.right, bottom = r.bottom;
                    let cur = el.parentElement;
                    while (cur && cur !== slide && cur !== document.body){
                        const s = getComputedStyle(cur);
                        const clipped = (
                            s.overflow === 'hidden' || s.overflow === 'clip' ||
                            s.overflowX === 'hidden' || s.overflowX === 'clip' ||
                            s.overflowY === 'hidden' || s.overflowY === 'clip'
                        );
                        if (clipped){
                            const cr = cur.getBoundingClientRect();
                            left = Math.max(left, cr.left);
                            top = Math.max(top, cr.top);
                            right = Math.min(right, cr.right);
                            bottom = Math.min(bottom, cr.bottom);
                            if (right <= left || bottom <= top) return null;
                        }
                        cur = cur.parentElement;
                    }
                    return {left, top, right, bottom,
                            width: right - left, height: bottom - top};
                }
                function maxOverflow(slide){
                    const cr = slide.getBoundingClientRect();
                    let ox = 0, oy = 0;
                    for (const el of slide.querySelectorAll('*')){
                        if (!isContent(el)) continue;
                        if (isDecorative(el)) continue;
                        const r = visibleRect(el, slide);
                        if (!r || r.width < 1 || r.height < 1) continue;
                        ox = Math.max(ox, r.right - cr.right, cr.left - r.left);
                        oy = Math.max(oy, r.bottom - cr.bottom, cr.top - r.top);
                    }
                    return {ox: Math.max(0, ox), oy: Math.max(0, oy),
                            cw: slide.offsetWidth, ch: slide.offsetHeight};
                }
                if (slides.length){
                    let cw=0, ch=0, ox=0, oy=0;
                    for (const s of slides){
                        const m = maxOverflow(s);
                        cw = Math.max(cw, m.cw);
                        ch = Math.max(ch, m.ch);
                        ox = Math.max(ox, m.ox);
                        oy = Math.max(oy, m.oy);
                    }
                    return {scrollWidth: cw + ox, scrollHeight: ch + oy,
                            clientWidth: cw, clientHeight: ch};
                }
                const body = document.body;
                const html = document.documentElement;
                return {
                    scrollWidth: Math.max(body.scrollWidth, html.scrollWidth, body.offsetWidth, html.offsetWidth),
                    scrollHeight: Math.max(body.scrollHeight, html.scrollHeight, body.offsetHeight, html.offsetHeight),
                    clientWidth: html.clientWidth,
                    clientHeight: html.clientHeight,
                };
            }""")
            overlaps = []
            if detect_overlaps:
                overlaps = await page.evaluate(_TEXT_OVERLAP_JS, {"minOverlapPx": 3, "maxPairs": 50})
            screenshot_bytes = None
            decor_rects = []
            if detect_blank:
                # Bounding rects of decorative elements, in viewport pixel
                # coordinates that match the screenshot clip. Used by the
                # blank detector to avoid flagging intentional decoration as
                # a blank patch.
                decor_rects = await page.evaluate(r"""() => {
                    const out = [];
                    function pushRects(el){
                        const rs = el.getClientRects();
                        for (const r of rs){
                            if (r.width >= 1 && r.height >= 1){
                                out.push({x: r.x, y: r.y, w: r.width, h: r.height});
                            }
                        }
                    }
                    // Explicit author opt-out.
                    for (const el of document.querySelectorAll('[data-decor], [aria-hidden="true"]')){
                        pushRects(el);
                    }
                    // Effective-opacity heuristic: ghost / watermark layer.
                    function effOpacity(el){
                        let op = 1;
                        let cur = el;
                        while (cur && cur !== document.body){
                            const s = getComputedStyle(cur);
                            if (s.display === 'none' || s.visibility === 'hidden') return 0;
                            const o = parseFloat(s.opacity);
                            if (!isNaN(o)) op *= o;
                            cur = cur.parentElement;
                        }
                        return op;
                    }
                    for (const el of document.querySelectorAll('body *')){
                        if (el.closest('[data-decor], [aria-hidden="true"]')) continue;
                        const op = effOpacity(el);
                        if (op > 0 && op <= 0.2) pushRects(el);
                    }
                    return out;
                }""")
                screenshot_bytes = await page.screenshot(
                    clip={"x": 0, "y": 0, "width": viewport_width, "height": viewport_height},
                    type="png",
                )
            await browser.close()
        width = int(dims["scrollWidth"])
        height = int(dims["scrollHeight"])
        # Tolerance is ratio + fixed buffer (default 2% + 5px → ~19px at 720 /
        # ~30px at 1280) to absorb sub-pixel rendering noise and line-box
        # bleed. Both axes use the same ratio + buffer formula, scaled to the
        # axis's viewport length.
        tol_y = int(viewport_height * overflow_tolerance_ratio) + overflow_tolerance_px
        tol_x = int(viewport_width * overflow_tolerance_ratio) + overflow_tolerance_px
        result = {
            "success": True,
            "width": width,
            "height": height,
            "viewport_width": viewport_width,
            "viewport_height": viewport_height,
            "overflow_x": max(0, width - viewport_width - tol_x),
            "overflow_y": max(0, height - viewport_height - tol_y),
            "details": dims,
            "overlaps": overlaps,
        }
        if detect_blank and screenshot_bytes is not None:
            blank = _detect_largest_blank(screenshot_bytes, decor_rects=decor_rects)
            if blank is not None:
                blank["flagged"] = (
                    blank["area_ratio"] >= blank_min_area_ratio
                    and min(blank["w"], blank["h"]) >= blank_min_side
                )
                result["blank"] = blank
        return result
    except Exception:
        return {"success": False, "error": traceback.format_exc()}


def _trailing_int(stem: str) -> int | None:
    m = re.search(r"(\d+)$", stem)
    return int(m.group(1)) if m else None


def _collect_targets(args) -> list[Path]:
    if args.files:
        return [Path(f).resolve() for f in args.files]

    base = Path(args.dir).resolve()
    if not base.is_dir():
        raise SystemExit(f"check_slides: --dir {base} is not a directory")

    files = sorted(base.glob("*.html"), key=lambda p: (_trailing_int(p.stem) or 0, p.name))
    if args.positions:
        wanted = set(args.positions)
        files = [p for p in files if (_trailing_int(p.stem) in wanted)]
    return files


async def _measure_one(path: Path, sem: asyncio.Semaphore) -> tuple[Path, dict]:
    try:
        html = path.read_text(encoding="utf-8")
    except Exception as exc:
        return path, {"success": False, "error": f"read failed: {exc}"}
    async with sem:
        result = await measure_slide_dimensions(
            html,
            viewport_width=_VIEWPORT_W,
            viewport_height=_VIEWPORT_H,
            proxy=_PROXY,
            detect_overlaps=True,
            detect_blank=True,
            file_path=str(path),
        )
    return path, result


async def _measure_all(targets: list[Path]) -> list[tuple[Path, dict]]:
    # One event loop drives every slide concurrently; the semaphore caps how
    # many headless browsers run at once so a large deck can't exhaust memory.
    sem = asyncio.Semaphore(min(_MAX_CONCURRENCY, len(targets)))
    return await asyncio.gather(*(_measure_one(p, sem) for p in targets))


def _format_report(results: list[tuple[Path, dict]]) -> tuple[str, bool]:
    lines = [
        f"Checked {len(results)} slide(s) at viewport {_VIEWPORT_W}x{_VIEWPORT_H} "
        f"(actual rendered width × height; '✗' marks overflow, overlap, or large blank):"
    ]
    overflow_count = blank_count = overlap_count = fail_count = ok_count = 0
    for path, r in results:
        label = path.name
        if not r.get("success"):
            err = (r.get("error") or "unknown")
            err = err.strip().splitlines()[-1][:140] if err else "unknown"
            lines.append(f"- {label}: render FAILED — {err}")
            fail_count += 1
            continue
        w, h = r["width"], r["height"]
        ox = r.get("overflow_x", 0)
        oy = r.get("overflow_y", 0)
        blank = r.get("blank") or {}
        overlaps = r.get("overlaps") or []
        flags = []
        if ox > 0:
            flags.append(f"horizontal overflow +{ox}px")
        if oy > 0:
            flags.append(f"vertical overflow +{oy}px")
        if blank.get("flagged"):
            flags.append(
                f"large blank region {blank['w']}x{blank['h']}px "
                f"@ ({blank['x']},{blank['y']}) ≈ {int(blank['area_ratio'] * 100)}% of canvas"
            )
        if overlaps:
            flags.append(f"{len(overlaps)} text overlap(s)")
        if flags:
            if ox > 0 or oy > 0:
                overflow_count += 1
            if blank.get("flagged"):
                blank_count += 1
            if overlaps:
                overlap_count += 1
            lines.append(f"- {label}: {w}x{h} ✗ {', '.join(flags)}")
            for o in overlaps[:5]:
                a, b, ov = o["a"], o["b"], o["overlap"]
                ta = (a["text"][:36] + "…") if len(a["text"]) > 37 else a["text"]
                tb = (b["text"][:36] + "…") if len(b["text"]) > 37 else b["text"]
                lines.append(
                    f"    · <{a['tag']}>'{ta}' ⨯ <{b['tag']}>'{tb}' "
                    f"(overlap {ov['w']}x{ov['h']}px @ ({ov['x']},{ov['y']}))"
                )
            if len(overlaps) > 5:
                lines.append(f"    · … +{len(overlaps) - 5} more overlap pair(s)")
        else:
            ok_count += 1
            lines.append(f"- {label}: {w}x{h} ✓")

    all_clean = (overflow_count == blank_count == overlap_count == fail_count == 0)
    if all_clean:
        lines.append(f"Summary: all {len(results)} slides fit the {_VIEWPORT_W}x{_VIEWPORT_H} canvas with no overlaps or large blank regions.")
    else:
        lines.append(
            f"Summary: {overflow_count} overflowing, "
            f"{overlap_count} with text overlaps, "
            f"{blank_count} with large blank, {fail_count} failed, {ok_count} OK. "
            "Use the Read tool to inspect each flagged file, then Edit for surgical fixes."
        )
    return "\n".join(lines), all_clean


def main() -> int:
    p = argparse.ArgumentParser(description="Check rendered slide dimensions / overflow / blank / overlaps.")
    p.add_argument("files", nargs="*", help="Slide HTML files to check (paths).")
    p.add_argument("--dir", help="Directory of slide HTMLs (used when no positional files are given).")
    p.add_argument("--positions", type=int, nargs="*",
                   help="When --dir is used, restrict to files whose name ends with these integers.")
    p.add_argument("--json", action="store_true", help="Emit raw per-file measurements as JSON.")
    p.add_argument("--output", type=Path, default=None, help="Write output here instead of stdout.")
    args = p.parse_args()

    if not args.files and not args.dir:
        p.error("provide one or more file paths, or --dir <slides_dir>")

    targets = _collect_targets(args)
    if not targets:
        msg = "check_slides: no slide files found."
        if args.output:
            args.output.write_text(msg + "\n", encoding="utf-8")
        else:
            sys.stdout.write(msg + "\n")
        return 1

    results = asyncio.run(_measure_all(targets))

    if args.json:
        payload = json.dumps(
            {str(path): r for path, r in results},
            ensure_ascii=False,
            indent=2,
        )
        all_clean = all(r.get("success") and r.get("overflow_x", 0) == 0
                        and r.get("overflow_y", 0) == 0
                        and not (r.get("blank") or {}).get("flagged") and not (r.get("overlaps") or [])
                        for _, r in results)
    else:
        payload, all_clean = _format_report(results)

    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        sys.stdout.write(payload + "\n")

    return 0 if all_clean else 1


if __name__ == "__main__":
    sys.exit(main())
