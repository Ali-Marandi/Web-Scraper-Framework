/**
 * html2pptx v4 — Convert HTML slide to pptxgenjs slide with positioned elements
 *
 * v4 Changes (2026-05-07) — broader & more faithful HTML coverage:
 *   ── NEW ELEMENT SUPPORT ─────────────────────────────────────────
 *   - <table>: full table extraction with cells, header row, alignment & basic styling
 *   - <hr>:    extracted as a horizontal line shape
 *   - <svg>:   inline SVG serialized & rasterized to PNG, then placed as image
 *   - <a>:     hyperlink preserved on text runs (url + tooltip)
 *   - <sub>/<sup>: rendered with PptxGenJS subscript/superscript run option
 *   ── COLOR / FILL ────────────────────────────────────────────────
 *   - HSL / HSLA color parsing in addition to RGB / RGBA / hex / named
 *   - Linear gradients now emit real PptxGenJS gradient fill on shapes (best-effort)
 *   - background-image: url() on containers preserved as a layered image (under text)
 *   ── SHAPE / IMAGE ───────────────────────────────────────────────
 *   - border-radius: 50% on square boxes → ellipse (oval) shape
 *   - <img> object-fit: cover/contain/fill respected via sizing & cropping
 *   - <img> border-radius now produces a rounded image clip (approximation)
 *   - <img> opacity / box-shadow forwarded to the inserted picture
 *   ── TEXT ────────────────────────────────────────────────────────
 *   - text-shadow → run-level glow / shadow approximation
 *   - text-align: justify mapped to PptxGenJS 'justify'
 *   - per-run text-decoration: line-through preserved as strike
 *   ── ROBUSTNESS ──────────────────────────────────────────────────
 *   - z-index 'auto' no longer collapses to 0 incorrectly
 *   - placeholders carry z-index so chart insertions layer correctly
 *   - color parsing falls back gracefully on unknown values
 *   - non-finite numeric CSS values default safely
 *   - <iframe>, <video>, <audio>, <canvas> are silently skipped (won't error)
 *
 * v3 features carried forward:
 *   - Smart font mapping (PPT-safe pass-through, macOS/web fonts auto-mapped)
 *   - Adaptive width / height compensation for text frames
 *   - Element boundary, font size, overlap, vertical-balance validation
 *
 * USAGE:
 *   const pptx = new pptxgen();
 *   pptx.layout = 'LAYOUT_16x9';
 *   const { slide, placeholders, warnings } = await html2pptx('slide.html', pptx, { fontConfig });
 *   // warnings prefixed with 🚨 CRITICAL must be fixed before finalizing
 *   await pptx.writeFile('output.pptx');
 *
 * VALIDATION (all non-blocking — returned in warnings array):
 *   - 🚨 CRITICAL OVERFLOW: HTML content overflows slide canvas by >12pt
 *   - ⚠ BOUNDS: element extends beyond slide edges after PPT compensation
 *   - ⚠ FONT: text element below minimum font size (11pt)
 *   - ⚠ OVERLAP: two text elements overlap each other
 *   - ⚠ LAYOUT: content clustered in top portion of slide
 *
 * RETURNS:
 *   { slide, placeholders, warnings } where placeholders is an array of { id, x, y, w, h, zIndex }
 */

const { chromium } = require('playwright');
const path = require('path');
const sharp = require('sharp');
const fs = require('fs');
const http = require('http');
const https = require('https');

const PT_PER_PX = 0.75;
const PX_PER_IN = 96;
const EMU_PER_IN = 914400;

const DEFAULT_FONT_CONFIG = {
  cjk: "Microsoft YaHei",
  latin: "Carlito",
  emphasis: "Liberation Sans Narrow",
  display: "Microsoft YaHei",
  symbol: "Segoe UI Symbol"
};

// ── v3: Compensation factors ──
const COMPENSATION = {
  HEADING_WIDTH: 0.10, SINGLE_LINE_NARROW: 0.10, SINGLE_LINE_NORMAL: 0.10,
  MULTI_LINE: 0.05, SHORT_TEXT_EXTRA: 0.18, NUMERIC_TEXT_EXTRA: 0.08,
  // Very-short text (1–5 chars) — single labels like "学", "Apply", "→"
  // are the most likely to wrap when a wider PPT font substitutes the
  // browser-measured glyph. Stack this on top of SHORT_TEXT_EXTRA.
  VERY_SHORT_TEXT_EXTRA: 0.30,
  NOWRAP_EXTRA: 0.15, MAX_WIDTH_FACTOR: 0.60,
  TEXT_HEIGHT: 0.08, LIST_HEIGHT: 0.06,
  MIN_FONT_SIZE_PT: 11,
  VERTICAL_BALANCE_THRESHOLD: 0.65, OVERLAP_TOLERANCE_IN: 0.05, BOUNDS_TOLERANCE_IN: 0.02,
  AUTO_SHORT_TEXT_THRESHOLD: 22,  // chars — auto-detect short text even without explicit nowrap
};

// ── v3: Validation helpers (Node.js scope) ──
function extractTextContent(el) {
  if (typeof el.text === 'string') return el.text;
  if (Array.isArray(el.text)) return el.text.map(r => r.text || '').join('');
  if (Array.isArray(el.items)) return el.items.map(r => r.text || '').join('');
  // Tables: flatten cells across all rows
  if (Array.isArray(el.rows)) {
    return el.rows.map(row =>
      row.map(cell => typeof cell === 'string' ? cell : (cell?.text || '')).join(' ')
    ).join(' ');
  }
  return '';
}
function getElementLabel(el) {
  const t = extractTextContent(el);
  return t.substring(0, 40) + (t.length > 40 ? '...' : '') || `[${el.type}]`;
}
function getListItemCount(el) {
  const styleCount = Number(el.style?._itemCount);
  if (Number.isFinite(styleCount) && styleCount > 0) return styleCount;
  if (!Array.isArray(el.items) || el.items.length === 0) return 0;
  return 1 + el.items.filter(r => r?.options?.breakLine).length;
}
function getListSpacingHeightBonus(el) {
  if (el.type !== 'list') return 0;
  const itemCount = getListItemCount(el);
  const afterPt = Number(el.style?.paraSpaceAfter) || 0;
  if (itemCount <= 1 || afterPt <= 0) return 0;
  // The source list rect already includes the inter-item gap. PPT may still
  // reserve paragraph spacing after the final item, so keep one gap as bottom
  // headroom rather than shifting the list down.
  return afterPt / 72;
}
function clampHeightToNextTextBound(el, height) {
  const nextTop = Number(el.style?._nextTextTopBound);
  if (!Number.isFinite(nextTop) || nextTop <= el.position.y) return height;
  // Keep a visible gutter before the next normal-flow text block. This catches
  // card body -> kicker stacks where PPT text metrics make the body box taller
  // than the browser-measured gap, e.g. timeline milestone descriptions.
  const maxHeight = nextTop - el.position.y - 0.03;
  if (maxHeight < 0.08) return height;
  return Math.min(height, maxHeight);
}
function isNarrowBodyTextForPptCompensation(el) {
  const txt = extractTextContent(el).replace(/\s+/g, ' ').trim();
  if (!txt || hasExplicitTextBreaks(el)) return false;
  const fs = Number(el.style?.fontSize) || 0;
  return txt.length >= 35 && txt.length <= 160 && fs <= 14 && el.position.w < 1.7;
}
function getNarrowBodyTextClipSlack(el) {
  if (!isNarrowBodyTextForPptCompensation(el)) return 0;
  return Math.min(0.10, Math.max(0.04, el.position.w * 0.06));
}
function isMediumSingleLineLabelForPptCompensation(el) {
  const txt = extractTextContent(el).replace(/\s+/g, ' ').trim();
  if (!txt || hasExplicitTextBreaks(el)) return false;
  const compactLen = txt.replace(/\s+/g, '').length;
  if (compactLen < 23 || compactLen > 42) return false;
  const fs = Number(el.style?.fontSize) || 16;
  if (fs < 8 || fs > 18) return false;
  const lh = el.style?.lineSpacing || fs * 1.2;
  const heightSingle = el.position.h <= lh * 1.7 / 72;
  if (!heightSingle) return false;
  const boxWidthPt = Math.max(1, (el.position?.w || 0) * 72);
  return estimateTextWidthPt(txt, fs) <= boxWidthPt * 1.55;
}
function getMediumSingleLineClipSlack(el) {
  if (!isMediumSingleLineLabelForPptCompensation(el)) return 0;
  return Math.min(0.12, Math.max(0.045, el.position.w * 0.06));
}
// Compute PPT-adjusted position for text/list elements (mirrors addElements logic, pre-clamp)
function getAdjustedTextPosition(el, slideWidthIn) {
  const MAX_TEXT_WIDTH_IN = 680 / 72;
  const isRotatedText = el.style?.rotate !== undefined;
  const widthFactor = isRotatedText ? 0 : calculateWidthCompensation(el, slideWidthIn);
  const widthIncrease = el.position.w * widthFactor;
  let adjustedX = el.position.x;
  let adjustedW = el.position.w;
  const align = el.style?.align;
  if (align === 'center') { adjustedX -= widthIncrease / 2; adjustedW += widthIncrease; }
  else if (align === 'right') { adjustedX -= widthIncrease; adjustedW += widthIncrease; }
  else { adjustedW += widthIncrease; }
  if (align === 'center' && /^h[1-6]$/.test(el.type)) {
    const centerX = adjustedX + adjustedW / 2;
    const margin = 0.3;
    const maxExpand = Math.min(centerX - margin, slideWidthIn - centerX - margin);
    if (maxExpand > adjustedW / 2) { adjustedX = centerX - maxExpand; adjustedW = maxExpand * 2; }
  }
  const hComp = el.type === 'list' ? COMPENSATION.LIST_HEIGHT : COMPENSATION.TEXT_HEIGHT;
  const finalW = isRotatedText ? adjustedW : Math.min(adjustedW, MAX_TEXT_WIDTH_IN);
  let finalH = el.position.h * (1 + hComp) + getListSpacingHeightBonus(el);
  finalH = clampHeightToNextTextBound(el, finalH);
  return { x: adjustedX, y: el.position.y, w: finalW, h: finalH };
}
function getVisualCheckPosition(el, p) {
  const rot = ((el.style?.rotate || 0) % 360 + 360) % 360;
  if (rot !== 90 && rot !== 270) return p;
  const cx = p.x + p.w / 2;
  const cy = p.y + p.h / 2;
  return { x: cx - p.h / 2, y: cy - p.w / 2, w: p.h, h: p.w };
}
function checkElementBounds(slideData, sw, sh) {
  const w = []; const tol = COMPENSATION.BOUNDS_TOLERANCE_IN;
  const textTypes = new Set(['p','h1','h2','h3','h4','h5','h6','list']);
  // Heavy-watermark text (≥80% transparent OR font-size ≥150pt) is intentionally
  // bleeding off-canvas — skip bounds warnings for it to avoid noise on cover slides.
  const isDecorative = (el) => {
    const t = el.style?.transparency;
    if (typeof t === 'number' && t >= 80) return true;
    const fs_ = el.style?.fontSize || 0;
    if (fs_ >= 150) return true;
    return false;
  };
  for (const el of slideData.elements) {
    if (!el.position) continue;
    if (textTypes.has(el.type) && isDecorative(el)) continue;
    const rawP = textTypes.has(el.type) ? getAdjustedTextPosition(el, sw) : el.position;
    const p = textTypes.has(el.type) ? getVisualCheckPosition(el, rawP) : rawP;
    if (p.x < -tol) w.push(`⚠ BOUNDS: "${getElementLabel(el)}" extends ${(-p.x*72).toFixed(0)}pt beyond LEFT`);
    if (p.y < -tol) w.push(`⚠ BOUNDS: "${getElementLabel(el)}" extends ${(-p.y*72).toFixed(0)}pt beyond TOP`);
    // 已禁用：右侧溢出（beyond RIGHT）告警噪声较大，按需关闭
    // if (p.x+p.w > sw+tol) w.push(`⚠ BOUNDS: "${getElementLabel(el)}" extends ${((p.x+p.w-sw)*72).toFixed(0)}pt beyond RIGHT`);
    if (p.y+p.h > sh+tol) w.push(`⚠ BOUNDS: "${getElementLabel(el)}" extends ${((p.y+p.h-sh)*72).toFixed(0)}pt beyond BOTTOM`);
  }
  return w;
}
function checkTextOverlaps(slideData) {
  const w = [];
  const te = slideData.elements.filter(e => ['p','h1','h2','h3','h4','h5','h6','list'].includes(e.type));
  // An element is "decorative" if it is essentially invisible — heavily transparent
  // and/or very large (like a 600px watermark character). Such elements are intentionally
  // placed under foreground content and should not trigger overlap warnings.
  const isDecorative = (el) => {
    const t = el.style?.transparency;
    if (typeof t === 'number' && t >= 80) return true; // ≥80% transparent → watermark-like
    const fs_ = el.style?.fontSize || 0;
    if (fs_ >= 150) return true; // absurdly large font → watermark / ghost numeral
    return false;
  };
  for (let i = 0; i < te.length; i++) {
    for (let j = i + 1; j < te.length; j++) {
      // Skip intentional z-stacking (ghost numbers, decorative overlays, etc.)
      if (te[i].zIndex !== te[j].zIndex) continue;
      // Skip overlaps that involve a decorative (watermark-like) element on either side
      if (isDecorative(te[i]) || isDecorative(te[j])) continue;
      const a = getVisualCheckPosition(te[i], te[i].position);
      const b = getVisualCheckPosition(te[j], te[j].position);
      const tol = COMPENSATION.OVERLAP_TOLERANCE_IN;
      const ow = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
      const oh = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
      if (ow > tol && oh > tol) {
        // 已禁用：文本重叠（OVERLAP）告警噪声较大，按需关闭
        // w.push(`⚠ OVERLAP: "${getElementLabel(te[i])}" overlaps "${getElementLabel(te[j])}"`);
      }
    }
  }
  return w;
}
function hasExplicitTextBreaks(el) {
  if (typeof el.text === 'string') return el.text.includes('\n');
  if (Array.isArray(el.text)) return el.text.some(r => (r.text && r.text.includes('\n')) || r.options?.breakLine);
  return false;
}
function estimateTextWidthPt(text, fontSize) {
  let units = 0;
  for (const ch of Array.from(text || '')) {
    if (/\s/.test(ch)) units += 0.28;
    else if (/[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/.test(ch)) units += 1.0;
    else if (/[A-Z0-9]/.test(ch)) units += 0.62;
    else if (/[a-z]/.test(ch)) units += 0.52;
    else units += 0.45;
  }
  return units * (fontSize || 16);
}
function isShortAutoNoWrapText(el) {
  const txt = extractTextContent(el).replace(/\s+/g, ' ').trim();
  if (!txt || hasExplicitTextBreaks(el)) return false;
  const compactTxt = txt.replace(/\s+/g, '');
  if (compactTxt.length === 0 || compactTxt.length > COMPENSATION.AUTO_SHORT_TEXT_THRESHOLD) {
    return false;
  }
  const fs = Number(el.style?.fontSize) || 16;
  const boxWidthPt = Math.max(1, (el.position?.w || 0) * 72);
  return estimateTextWidthPt(txt, fs) <= boxWidthPt * 1.15;
}
function calculateWidthCompensation(el, slideWidthIn) {
  if (el.style?._isIcon) return 0;
  const isH = /^h[1-6]$/.test(el.type);
  const txt = extractTextContent(el);
  const lh = el.style?.lineSpacing || (el.style?.fontSize||16)*1.2;
  // Detect single-line text: either the box is narrow enough to fit only one
  // line of text, OR the source text has no explicit breaks (no '\n' from <br>
  // and no breakLine flag on any run). The height-only heuristic misses cases
  // where padding inflates the box (e.g. `<div class="px-3 py-1.5">label</div>`),
  // causing under-compensation and visible wrapping when PPT substitutes a
  // wider font (Inter→Carlito etc.).
  const heightSingle = el.position.h <= lh*1.5/72;
  const noExplicitBreaks =
    (typeof el.text === 'string' && !el.text.includes('\n')) ||
    (Array.isArray(el.text) && !el.text.some(r => (r.text && r.text.includes('\n')) || r.options?.breakLine));
  // The noExplicitBreaks signal alone is unreliable: a long paragraph with no
  // <br> still wraps naturally, but would be misclassified as single-line and
  // get the wider compensation, overflowing its parent (e.g. a card column).
  // Guard by also estimating whether the text could plausibly fit on one line
  // at the measured box width.
  const fs_est = el.style?.fontSize || 16;
  const boxWidthPt = el.position.w * 72;
  const estTextWidthPt = estimateTextWidthPt(txt, fs_est);
  const couldFitOneLine = estTextWidthPt <= boxWidthPt * 1.2;
  const single = heightSingle || (noExplicitBreaks && couldFitOneLine);

  // Width compensation is mostly limited to short labels/titles. Long
  // paragraphs usually keep their browser-measured width, except for narrow
  // card body copy where PPT font substitution can add one avoidable wrap.
  const compactTxt = txt.replace(/\s+/g, '');
  const isShortText = compactTxt.length > 0 && compactTxt.length <= COMPENSATION.AUTO_SHORT_TEXT_THRESHOLD;
  if (!isShortText || !single) {
    let f0 = 0;
    if (isNarrowBodyTextForPptCompensation(el)) f0 = Math.max(f0, 0.06);
    if (isMediumSingleLineLabelForPptCompensation(el)) f0 = Math.max(f0, 0.08);
    // Single-line headings / large titles longer than the short-text threshold
    // are still prone to a spurious extra wrap: the browser box is tight to the
    // measured glyph run, and PPT's substitute font (Inter→Carlito, etc.) is a
    // few percent wider, so the last word drops to a new line. Give these a
    // modest widen. Downstream clip/slide clamping (see getAdjustedTextPosition
    // and addElements) keeps the wider box from pushing into neighbours.
    const fsHere = el.style?.fontSize || 0;
    if (single && !el.noWrap && (isH || fsHere >= 18)) {
      f0 = Math.max(f0, isH ? COMPENSATION.HEADING_WIDTH : COMPENSATION.HEADING_WIDTH * 0.8);
    }
    // Single-line labels with pronounced letter-spacing (all-caps footers,
    // kickers, "EMPTY-NEST · DEFINITION · DATA" style captions) keep a box that
    // is tight to the browser-measured glyph run. pptxgenjs applies charSpacing
    // per glyph gap, so PPT's wider substitute font plus the tracking pushes the
    // final token onto a 2nd line. The per-char letter-spacing bonus later in
    // this function only runs for short text, so long tracked single-liners
    // would otherwise fall through and wrap. Widen proportionally to the
    // tracking ratio and run length, but only when the text plausibly already
    // fits one line (est width — which ignores tracking — is within the measured
    // box), so genuinely-wrapping paragraphs are never widened. Take the max
    // with the weaker medium-label/narrow-body factors above rather than
    // returning early, so a tracked medium label still gets enough room.
    if (single && !el.noWrap && fsHere > 0) {
      const csHere = el.style?.charSpacing || 0;
      const ratio = csHere / fsHere;
      if (ratio > 0.08) {
        const boxWidthPt = (el.position?.w || 0) * 72;
        if (boxWidthPt > 0 && estimateTextWidthPt(txt, fsHere) <= boxWidthPt * 1.3) {
          const lenBoost = Math.min(1.6, 0.6 + compactTxt.length / 40);
          f0 = Math.max(f0, Math.min(0.30, ratio * 0.9 * lenBoost));
        }
      }
    }
    return f0;
  }

  let f = isH ? COMPENSATION.HEADING_WIDTH : (el.position.w < slideWidthIn/3 && txt.length < 14 ? COMPENSATION.SINGLE_LINE_NARROW : COMPENSATION.SINGLE_LINE_NORMAL);
  if (txt.length>0 && txt.length<10) f += COMPENSATION.SHORT_TEXT_EXTRA;
  // Extra punch for 1–5 char labels — these are the worst offenders for
  // wrapping when PPT swaps to a wider font (e.g. Inter→Carlito on "Apply"
  // or YaHei→Noto on "学").
  if (txt.length > 0 && txt.length <= 5) f += COMPENSATION.VERY_SHORT_TEXT_EXTRA;
  if (/^[\d\s\.\,\-\/\+\%\$\#\@\!\?\:\;\(\)\[\]]+$/.test(txt)) f += COMPENSATION.NUMERIC_TEXT_EXTRA;
  if (el.noWrap) f += COMPENSATION.NOWRAP_EXTRA;
  // v4: Auto-detect short text that should not wrap even without explicit nowrap.
  // Threshold widened to 22 chars so labels like "No. 07 · Spring Term" (19) and
  // "Lorem ipsum dolor" (17) still get a wrap-prevention bonus.
  // Bonus is intentionally modest (0.4×) — heavier compensation here
  // over-inflates plain medium-length labels and makes them push neighbours.
  // Styled cases (italic / letter-spaced) get extra bonuses lower in the function
  // that stack on top of this baseline.
  if (!el.noWrap && single && txt.length >= 10 && txt.length < COMPENSATION.AUTO_SHORT_TEXT_THRESHOLD) {
    f += COMPENSATION.SHORT_TEXT_EXTRA * 0.4;
  }
  // v4: Auto-detect card titles (>=18pt, single line, <20 chars) — treat like heading
  const fs_ = el.style?.fontSize || 16;
  if (!isH && single && fs_ >= 18 && txt.length < 20) {
    f = Math.max(f, COMPENSATION.HEADING_WIDTH * 0.8); // At least 80% of heading compensation
  }
  // Letter-spacing widens the rendered glyph run; PPT font substitution can
  // turn that into wrapping when the browser-measured box was already snug.
  // Add a proportional bonus when letter-spacing is a noticeable fraction of
  // the font size. Apply across single/multi-line because spacing affects both.
  const cs = el.style?.charSpacing || 0;
  let hasLetterSpacing = false;
  if (cs > 0) {
    const ratio = cs / fs_;
    if (ratio > 0.02) {
      f += Math.min(ratio * 1.0, 0.22);
      hasLetterSpacing = true;
    }
  }
  // Italic widens the rendered run vs. the upright browser metric (PPT often
  // synthesises italic from the regular face). Tag for the safety guard below.
  const isItalic = el.style?.italic === true ||
    (Array.isArray(el.text) && el.text.some(r => r.options?.italic));
  if (single && isItalic) f += 0.04;
  // Already-wide single-line boxes don't usually need full width compensation —
  // their parent (card, column, etc.) is tight to the measured content, and
  // adding 10% on top can push the text past the container edge. Reduce
  // (not zero) the compensation for those cases. Skip the reduction entirely
  // when letter-spacing or italic is present — those genuinely need the
  // extra width to avoid wrapping (e.g. "No. 07 · Spring Term", italic +
  // 0.1em tracking, wraps without help).
  if (single && el.position.w > 1.5 && txt.length >= 14 && !el.noWrap &&
      !hasLetterSpacing && !isItalic) {
    f = Math.min(f, 0.05);
  }
  return Math.min(f, COMPENSATION.MAX_WIDTH_FACTOR);
}

// ── Emphasis fonts (post-extraction, Node.js scope) ──
const hasCJKCharsNode = (text = "") => /[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/.test(text);
const hasDigitCharsNode = (text = "") => /[0-9０-９]/.test(text);
const hasEmojiCharsNode = (text = "") => /[\u2600-\u27BF]|[\uD800-\uDBFF][\uDC00-\uDFFF]/.test(text);
const hasIconSymbolCharsNode = (text = "") => /[\u2190-\u21FF\u2300-\u23FF\u2900-\u297F\u2460-\u24FF\u25A0-\u27BF\u2B00-\u2BFF]|[\uD800-\uDBFF][\uDC00-\uDFFF]/.test(text);

function isIconOnlyTextNode(text = "") {
  const t = String(text).trim();
  if (!t) return false;
  const compact = t.replace(/[\s\uFE0E\uFE0F\u200D\u20E3]/g, "");
  if (!compact || Array.from(compact).length > 4) return false;
  if (hasCJKCharsNode(compact) || /[A-Za-z0-9０-９]/.test(compact)) return false;
  return hasIconSymbolCharsNode(compact);
}

function shouldUseNumericEmphasisText(text = "") {
  const t = String(text).trim();
  if (!t || hasCJKCharsNode(t) || !hasDigitCharsNode(t)) return false;
  if (t.length > 36) return false;
  const compact = t.replace(/\s+/g, "");
  const useful = compact.replace(/[^0-9０-９A-Za-z.,:;_#%+\-\/()\[\]·]/g, "");
  const ratio = useful.length / Math.max(1, compact.length);
  const labelPrefix = /^(?:lv|no|honor|resource|step|part|section|chapter|page|slide|p|q|a|item|case|fig|table)\b/i.test(compact);
  return ratio >= 0.65 || labelPrefix;
}

function applyEmphasisFont(slideData, fontConfig = DEFAULT_FONT_CONFIG) {
  const cfg = typeof fontConfig === "string" ? { ...DEFAULT_FONT_CONFIG, emphasis: fontConfig } : { ...DEFAULT_FONT_CONFIG, ...(fontConfig || {}) };
  for (const el of slideData.elements) {
    if (!["p","h1","h2","h3","h4","h5","h6"].includes(el.type)) continue;
    if (typeof el.text === "string") {
      const trimmed = el.text.trim();
      if (isIconOnlyTextNode(trimmed)) {
        el.style.fontFace = cfg.symbol;
        el.style._isIcon = true;
        el.noWrap = true;
      } else if (hasEmojiCharsNode(trimmed) && Array.from(trimmed).length <= 4) {
        el.style.fontFace = cfg.symbol;
      }
      if (shouldUseNumericEmphasisText(trimmed)) el.style.fontFace = cfg.emphasis;
    } else if (Array.isArray(el.text)) {
      const wholeText = extractTextContent(el).trim();
      if (isIconOnlyTextNode(wholeText)) {
        el.style.fontFace = cfg.symbol;
        el.style._isIcon = true;
        el.noWrap = true;
      }
      for (const run of el.text) {
        const trimmed = String(run.text || "").trim();
        if (!trimmed) continue;
        if (hasEmojiCharsNode(trimmed) && Array.from(trimmed).length <= 4) run.options.fontFace = cfg.symbol;
        if (shouldUseNumericEmphasisText(trimmed)) run.options.fontFace = cfg.emphasis;
      }
    }
  }
}

// Helper: Fix image path if file extension doesn't match actual format
function fixImageExtension(imagePath, tmpDir) {
  try {
    const fd = fs.openSync(imagePath, 'r');
    const buf = Buffer.alloc(12);
    fs.readSync(fd, buf, 0, 12, 0);
    fs.closeSync(fd);

    let actualExt = null;
    if (buf[0] === 0xFF && buf[1] === 0xD8) actualExt = '.jpg';
    else if (buf[0] === 0x89 && buf[1] === 0x50 && buf[2] === 0x4E && buf[3] === 0x47) actualExt = '.png';
    else if (buf[0] === 0x47 && buf[1] === 0x49 && buf[2] === 0x46) actualExt = '.gif';
    else if (buf[0] === 0x52 && buf[1] === 0x49 && buf[8] === 0x57 && buf[9] === 0x45) actualExt = '.webp';

    if (!actualExt) return imagePath;

    const currentExt = path.extname(imagePath).toLowerCase();
    if (currentExt === actualExt || (currentExt === '.jpeg' && actualExt === '.jpg') || (currentExt === '.jpg' && actualExt === '.jpeg')) {
      return imagePath;
    }

    // Extension mismatch: copy with correct extension
    const fixedPath = path.join(tmpDir, path.basename(imagePath, currentExt) + actualExt);
    fs.copyFileSync(imagePath, fixedPath);
    return fixedPath;
  } catch (e) {
    return imagePath;
  }
}

// Helper: Convert any SVG data URLs in slideData.elements to PNG files on disk.
// pptxgenjs's addImage() rejects `data:image/svg+xml;...` URLs (PowerPoint's SVG
// support is partial, and pptxgenjs validates the data URL MIME type before
// embedding). We rasterize with sharp at 2× the slide density so the PNG looks
// crisp at typical zoom levels, then swap el.src to point at the temp PNG.
async function rasterizeSvgImages(slideData, tmpDir) {
  if (!slideData || !Array.isArray(slideData.elements)) return;
  // Collect tasks first so we can run them in parallel
  const tasks = [];
  for (const el of slideData.elements) {
    if (el.type !== 'image' || !el.src) continue;
    if (!el.src.startsWith('data:image/svg+xml')) continue;
    tasks.push((async () => {
      try {
        // Strip the data URL prefix — handle both base64 and URL-encoded variants
        let svgBuffer;
        if (el.src.includes(';base64,')) {
          const b64 = el.src.split(';base64,')[1];
          svgBuffer = Buffer.from(b64, 'base64');
        } else {
          // data:image/svg+xml,<urlencoded>
          const raw = el.src.replace(/^data:image\/svg\+xml,/, '');
          svgBuffer = Buffer.from(decodeURIComponent(raw), 'utf8');
        }

        // Target raster size: 2× the placed inch size at 96 DPI = 192 DPI
        const widthPx = Math.max(1, Math.round((el.position?.w || 1) * 192));
        const heightPx = Math.max(1, Math.round((el.position?.h || 1) * 192));
        const filename = `h2p-svg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}.png`;
        const outPath = path.join(tmpDir, filename);
        await sharp(svgBuffer, { density: 192 })
          .resize(widthPx, heightPx, { fit: 'fill' })
          .png()
          .toFile(outPath);
        el.src = outPath;
      } catch (err) {
        // Mark for skip so addElements doesn't try to embed a broken data URL
        el._skipRender = true;
        el._skipReason = `SVG rasterize failed: ${err.message}`;
      }
    })());
  }
  if (tasks.length > 0) await Promise.all(tasks);
}

function clampNumber(value, min, max) {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, value));
}

function parseCssObjectPosition(value) {
  const pos = { x: 0.5, y: 0.5 };
  if (!value || typeof value !== 'string') return pos;

  const tokens = value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const toFraction = (token, axis) => {
    if (token === 'left') return axis === 'x' ? 0 : null;
    if (token === 'right') return axis === 'x' ? 1 : null;
    if (token === 'top') return axis === 'y' ? 0 : null;
    if (token === 'bottom') return axis === 'y' ? 1 : null;
    if (token === 'center') return 0.5;
    if (/%$/.test(token)) return clampNumber(parseFloat(token) / 100, 0, 1);
    return null;
  };

  let xSet = false;
  let ySet = false;
  for (const token of tokens) {
    const xVal = toFraction(token, 'x');
    const yVal = toFraction(token, 'y');
    if (!xSet && xVal !== null && (token !== 'center' || !ySet)) {
      pos.x = xVal;
      xSet = true;
      continue;
    }
    if (!ySet && yVal !== null) {
      pos.y = yVal;
      ySet = true;
    }
  }

  if (tokens.length >= 2) {
    const firstX = toFraction(tokens[0], 'x');
    const firstY = toFraction(tokens[0], 'y');
    const secondX = toFraction(tokens[1], 'x');
    const secondY = toFraction(tokens[1], 'y');
    if (firstX !== null && firstY === null) pos.x = firstX;
    if (firstY !== null && firstX === null) pos.y = firstY;
    if (secondY !== null && secondX === null) pos.y = secondY;
    else if (secondX !== null && secondY === null) pos.x = secondX;
    else if (secondX !== null && secondY !== null) pos.y = secondY;
  }

  return pos;
}

function decodeDataUrlToBuffer(dataUrl) {
  const match = String(dataUrl).match(/^data:([^;,]+)?((?:;[^,]+)*),(.*)$/);
  if (!match) throw new Error('invalid data URL');
  const meta = match[2] || '';
  const payload = match[3] || '';
  if (meta.includes(';base64')) return Buffer.from(payload, 'base64');
  return Buffer.from(decodeURIComponent(payload), 'utf8');
}

function downloadToBuffer(url, redirects = 4) {
  return new Promise((resolve, reject) => {
    const client = /^https:/i.test(url) ? https : http;
    const req = client.get(url, res => {
      const status = res.statusCode || 0;
      const loc = res.headers.location;
      if (status >= 300 && status < 400 && loc && redirects > 0) {
        res.resume();
        const nextUrl = new URL(loc, url).toString();
        downloadToBuffer(nextUrl, redirects - 1).then(resolve, reject);
        return;
      }
      if (status < 200 || status >= 300) {
        res.resume();
        reject(new Error(`HTTP ${status}`));
        return;
      }
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    });
    req.on('error', reject);
    req.setTimeout(20000, () => {
      req.destroy(new Error('image download timed out'));
    });
  });
}

async function loadImageBuffer(src, cache) {
  if (cache.has(src)) return cache.get(src);
  let buffer;
  if (/^data:/i.test(src)) {
    buffer = decodeDataUrlToBuffer(src);
  } else if (/^https?:\/\//i.test(src)) {
    buffer = await downloadToBuffer(src);
  } else {
    const filePath = src.startsWith('file://') ? src.replace('file://', '') : src;
    buffer = await fs.promises.readFile(filePath);
  }
  cache.set(src, buffer);
  return buffer;
}

async function materializeObjectFitImages(slideData, tmpDir) {
  if (!slideData || !Array.isArray(slideData.elements)) return;
  const cache = new Map();
  const tasks = slideData.elements.map(async (el) => {
    if (el.type !== 'image' || !el.src) return;
    if (el.objectFit !== 'cover' && el.objectFit !== 'contain') return;
    if (!el.position || !Number.isFinite(el.position.w) || !Number.isFinite(el.position.h)) return;

    const targetW = Math.max(1, Math.round(el.position.w * 192));
    const targetH = Math.max(1, Math.round(el.position.h * 192));
    try {
      const input = await loadImageBuffer(el.src, cache);
      const meta = await sharp(input).metadata();
      if (!meta.width || !meta.height) return;

      const pos = parseCssObjectPosition(el.objectPosition);
      const filename = `h2p-fit-${Date.now()}-${Math.random().toString(36).slice(2, 8)}.png`;
      const outPath = path.join(tmpDir, filename);

      if (el.objectFit === 'cover') {
        const scale = Math.max(targetW / meta.width, targetH / meta.height);
        const resizedW = Math.max(targetW, Math.ceil(meta.width * scale));
        const resizedH = Math.max(targetH, Math.ceil(meta.height * scale));
        const left = clampNumber(Math.round((resizedW - targetW) * pos.x), 0, resizedW - targetW);
        const top = clampNumber(Math.round((resizedH - targetH) * pos.y), 0, resizedH - targetH);
        await sharp(input)
          .rotate()
          .resize(resizedW, resizedH, { fit: 'fill' })
          .extract({ left, top, width: targetW, height: targetH })
          .png()
          .toFile(outPath);
      } else {
        const scale = Math.min(targetW / meta.width, targetH / meta.height);
        const resizedW = Math.max(1, Math.round(meta.width * scale));
        const resizedH = Math.max(1, Math.round(meta.height * scale));
        const left = clampNumber(Math.round((targetW - resizedW) * pos.x), 0, targetW - resizedW);
        const top = clampNumber(Math.round((targetH - resizedH) * pos.y), 0, targetH - resizedH);
        const resized = await sharp(input)
          .rotate()
          .resize(resizedW, resizedH, { fit: 'fill' })
          .png()
          .toBuffer();
        await sharp({
          create: {
            width: targetW,
            height: targetH,
            channels: 4,
            background: { r: 0, g: 0, b: 0, alpha: 0 }
          }
        })
          .composite([{ input: resized, left, top }])
          .png()
          .toFile(outPath);
      }

      el.src = outPath;
      el.objectFit = 'fill';
      el._objectFitMaterialized = true;
    } catch (err) {
      console.warn(`[html2pptx] object-fit image fallback (${el.src}): ${err.message}`);
    }
  });
  await Promise.all(tasks);
}


// Helper: Get body dimensions and check for overflow
async function getBodyDimensions(page) {
  const bodyDimensions = await page.evaluate(() => {
    // Normalize box-sizing before measuring overflow, so that a child like
    // `width:720pt; padding:0 48pt` doesn't falsely appear to overflow the
    // 720pt body under default content-box sizing.
    document.querySelectorAll('*').forEach(el => { el.style.boxSizing = 'border-box'; });
    void document.body.offsetHeight;
    const body = document.body;
    const slideRoot = document.querySelector('.slide') || body;
    const rect = slideRoot.getBoundingClientRect();
    const style = window.getComputedStyle(slideRoot);
    const bodyStyle = window.getComputedStyle(body);
    const padX = (parseFloat(bodyStyle.paddingLeft) || 0) + (parseFloat(bodyStyle.paddingRight) || 0);
    const padY = (parseFloat(bodyStyle.paddingTop) || 0) + (parseFloat(bodyStyle.paddingBottom) || 0);
    const rootW = Math.max(rect.width || 0, slideRoot.scrollWidth || 0, parseFloat(style.width) || 0);
    const rootH = Math.max(rect.height || 0, slideRoot.scrollHeight || 0, parseFloat(style.height) || 0);

    return {
      width: rootW + padX,
      height: rootH + padY,
      scrollWidth: slideRoot.scrollWidth || rootW,
      scrollHeight: slideRoot.scrollHeight || rootH
    };
  });

  const errors = [];
  const widthOverflowPx = Math.max(0, bodyDimensions.scrollWidth - bodyDimensions.width - 1);
  const heightOverflowPx = Math.max(0, bodyDimensions.scrollHeight - bodyDimensions.height - 1);

  const widthOverflowPt = widthOverflowPx * PT_PER_PX;
  const heightOverflowPt = heightOverflowPx * PT_PER_PX;

  const OVERFLOW_TOLERANCE_PT = 12;
  // Severe overflow ("超长很多") — content spills past the canvas by more than
  // ~1 inch. This is almost always real content getting silently clipped, so we
  // escalate it to a louder, must-fix CRITICAL message. Output is NOT blocked
  // (pptx still writes, exit code stays 0) — the message is the signal that the
  // caller MUST fix the source HTML and re-run.
  const OVERFLOW_SEVERE_PT = 72;
  const maxOverflowPt = Math.max(widthOverflowPt, heightOverflowPt);
  if (widthOverflowPt > OVERFLOW_TOLERANCE_PT || heightOverflowPt > OVERFLOW_TOLERANCE_PT) {
    const directions = [];
    if (widthOverflowPt > OVERFLOW_TOLERANCE_PT) directions.push(`${widthOverflowPt.toFixed(1)}pt horizontally`);
    if (heightOverflowPt > OVERFLOW_TOLERANCE_PT) directions.push(`${heightOverflowPt.toFixed(1)}pt vertically`);
    const reminder = heightOverflowPt > OVERFLOW_TOLERANCE_PT ? ' (leave 0.5" margin at bottom)' : '';
    if (maxOverflowPt > OVERFLOW_SEVERE_PT) {
      // Severe: spilled by >1in — content is being clipped, MUST be fixed.
      errors.push(`🚨🚨 CRITICAL OVERFLOW (MUST FIX): HTML content overflows body by ${directions.join(' and ')}${reminder} — content is being clipped; reduce content / font size or restructure the source HTML and re-run.`);
    } else {
      errors.push(`🚨 CRITICAL OVERFLOW: HTML content overflows body by ${directions.join(' and ')}${reminder}`);
    }
  }

  return { ...bodyDimensions, errors };
}

// Helper: Add background to slide
async function addBackground(slideData, targetSlide, pres, tmpDir) {
  const slideW = pres.presLayout ? pres.presLayout.width / EMU_PER_IN : 10;
  const slideH = pres.presLayout ? pres.presLayout.height / EMU_PER_IN : 5.625;
  // Rasterized CSS-gradient canvas background (linear/radial mesh) — emitted as
  // a PNG data URL that covers the whole slide.
  if (slideData.background.type === 'image' && slideData.background.dataUrl) {
    try {
      targetSlide.addImage({
        data: slideData.background.dataUrl,
        x: 0, y: 0, w: slideW, h: slideH,
        sizing: { type: 'cover', w: slideW, h: slideH }
      });
      return;
    } catch (err) {
      console.warn(`[html2pptx] gradient background failed: ${err.message}`);
      if (slideData.background.fallbackColor) {
        targetSlide.background = { color: slideData.background.fallbackColor };
      }
      return;
    }
  }
  if (slideData.background.type === 'image' && slideData.background.path) {
    let imagePath = slideData.background.path.startsWith('file://')
      ? slideData.background.path.replace('file://', '')
      : slideData.background.path;
    // PptxGenJS slide.background = { path } is unreliable for local files;
    // use addImage at (0,0) covering the full slide instead.
    try {
      targetSlide.addImage({
        path: fixImageExtension(imagePath, tmpDir),
        x: 0, y: 0, w: slideW, h: slideH,
        sizing: { type: 'cover', w: slideW, h: slideH }
      });
    } catch (err) {
      console.warn(`[html2pptx] background image failed (${imagePath}): ${err.message}`);
      // Fall back to a solid fill if a representative color was provided
      if (slideData.background.fallbackColor) {
        targetSlide.background = { color: slideData.background.fallbackColor };
      }
    }
  } else if (slideData.background.type === 'color' && slideData.background.value) {
    targetSlide.background = { color: slideData.background.value };
  }
}

// Helper: Pick a PPT shape constant based on the element's `shape` block
function pickShapeKind(pres, shapeMeta) {
  if (!shapeMeta) return pres.ShapeType.rect;
  if (shapeMeta.kind === 'ellipse') return pres.ShapeType.ellipse;
  if (shapeMeta.rectRadius && shapeMeta.rectRadius > 0) return pres.ShapeType.roundRect;
  return pres.ShapeType.rect;
}

// Helper: Add elements to slide
function addElements(slideData, targetSlide, pres, tmpDir) {
  const slideWidthIn = pres.presLayout ? pres.presLayout.width / EMU_PER_IN : 10;
  const slideHeightIn = pres.presLayout ? pres.presLayout.height / EMU_PER_IN : 5.625;
  const MAX_TEXT_WIDTH_IN = 680 / 72; // ~9.44in — cap after compensation to avoid overflow

  // v3: Sort by z-index for correct visual layering. Treat 'auto' (NaN) as 0
  // but preserve insertion order via a secondary key so equal z-index keeps DOM order.
  const sortedElements = slideData.elements
    .map((el, idx) => ({ el, idx, z: Number.isFinite(el.zIndex) ? el.zIndex : 0 }))
    .sort((a, b) => (a.z - b.z) || (a.idx - b.idx))
    .map(x => x.el);

  for (const el of sortedElements) {
    if (el.type === 'image') {
      // Honor the skip flag set by rasterizeSvgImages on failure
      if (el._skipRender) {
        if (el._skipReason) console.warn(`[html2pptx] image skipped — ${el._skipReason}`);
        continue;
      }
      let imagePath = el.src && el.src.startsWith('file://') ? el.src.replace('file://', '') : el.src;
      if (!imagePath) continue;
      // Defensive: if for any reason an SVG data URL slipped past the rasterizer,
      // skip it instead of letting pptxgenjs throw "Unable to read media".
      if (typeof imagePath === 'string' && imagePath.startsWith('data:image/svg+xml')) {
        console.warn('[html2pptx] dropping un-rasterized SVG data URL — sharp may have failed earlier');
        continue;
      }
      const opts = {
        x: el.position.x, y: el.position.y, w: el.position.w, h: el.position.h
      };
      // object-fit support — pptxgenjs `sizing` controls crop/contain/cover behaviour
      if (el.objectFit === 'cover') {
        opts.sizing = { type: 'cover', w: el.position.w, h: el.position.h };
      } else if (el.objectFit === 'contain') {
        opts.sizing = { type: 'contain', w: el.position.w, h: el.position.h };
      } else if (el.objectFit === 'crop' && el.crop) {
        opts.sizing = { type: 'crop', w: el.position.w, h: el.position.h, x: el.crop.x, y: el.crop.y };
      }
      // border-radius approximation — pptxgenjs has limited support for image clipping;
      // we expose the value and let the user opt-in via rounding when supported.
      if (el.rounding) opts.rounding = true;
      // Forward image opacity / shadow if present
      if (el.transparency != null) opts.transparency = el.transparency;
      if (el.shadow) opts.shadow = el.shadow;
      if (el.hyperlink) opts.hyperlink = el.hyperlink;
      try {
        // Only run extension-fixup on actual filesystem paths; use data for data URLs.
        const isDataUrl = typeof imagePath === 'string' && imagePath.startsWith('data:');
        const isLocalFile = typeof imagePath === 'string'
          && !isDataUrl
          && !/^https?:\/\//i.test(imagePath);
        if (isDataUrl) opts.data = imagePath;
        else opts.path = isLocalFile ? fixImageExtension(imagePath, tmpDir) : imagePath;
        targetSlide.addImage(opts);
      } catch (err) {
        console.warn(`[html2pptx] failed to add image ${imagePath}: ${err.message}`);
      }
    } else if (el.type === 'line') {
      const lineOptions = {
        x: el.x1, y: el.y1, w: el.x2 - el.x1, h: el.y2 - el.y1,
        line: { color: el.color, width: el.width, dashType: el.dashType }
      };
      if (el.transparency !== null && el.transparency !== undefined) {
        lineOptions.line.transparency = el.transparency;
      }
      targetSlide.addShape(pres.ShapeType.line, lineOptions);
    } else if (el.type === 'hr') {
      // Horizontal rule rendered as a thin line shape across its measured width
      targetSlide.addShape(pres.ShapeType.line, {
        x: el.position.x,
        y: el.position.y + el.position.h / 2,
        w: el.position.w,
        h: 0,
        line: { color: el.color || '888888', width: el.thickness || 0.75, dashType: el.dashType || 'solid' }
      });
    } else if (el.type === 'table') {
      // Native PptxGenJS table support
      const tableOpts = {
        x: el.position.x, y: el.position.y, w: el.position.w,
        // height is best left adaptive — pptxgenjs will auto-fit rows
        colW: el.colWidths || undefined,
        border: el.tableBorder || { type: 'solid', color: 'CCCCCC', pt: 0.5 },
        fontFace: el.style?.fontFace,
        fontSize: el.style?.fontSize,
        color: el.style?.color,
        valign: 'top',
        autoPage: false
      };
      try {
        targetSlide.addTable(el.rows, tableOpts);
      } catch (err) {
        console.warn(`[html2pptx] failed to add table: ${err.message}`);
      }
    } else if (el.type === 'shape') {
      const shapeOptions = {
        x: el.position.x, y: el.position.y, w: el.position.w, h: el.position.h,
        shape: pickShapeKind(pres, el.shape)
      };
      if (el.shape.fill) {
        // String fill = solid color; object fill = gradient (best-effort)
        if (typeof el.shape.fill === 'string') {
          shapeOptions.fill = { color: el.shape.fill };
          if (el.shape.transparency != null) shapeOptions.fill.transparency = el.shape.transparency;
        } else {
          shapeOptions.fill = el.shape.fill;
        }
      }
      if (el.shape.line) shapeOptions.line = el.shape.line;
      if (el.shape.rectRadius > 0) shapeOptions.rectRadius = el.shape.rectRadius;
      if (el.shape.shadow) shapeOptions.shadow = el.shape.shadow;
      if (el.shape.rotate != null) shapeOptions.rotate = el.shape.rotate;
      targetSlide.addText(el.text || '', shapeOptions);
    } else if (el.type === 'list') {
      // v3: Height compensation for lists
      let adjustedH = el.position.h * (1 + COMPENSATION.LIST_HEIGHT) +
        getListSpacingHeightBonus(el);
      // Clamp list height to slide bottom
      if (el.position.y + adjustedH > slideHeightIn) adjustedH = slideHeightIn - el.position.y;
      if (adjustedH < 0.1) adjustedH = 0.1;
      // Clamp list width to slide right edge
      let listX = el.position.x;
      let listW = el.position.w;
      if (listX + listW > slideWidthIn) listW = slideWidthIn - listX;
      if (listW < 0.1) listW = 0.1;
      if (listW > MAX_TEXT_WIDTH_IN) listW = MAX_TEXT_WIDTH_IN;
      const listOptions = {
        x: listX, y: el.position.y, w: listW, h: adjustedH,
        fontSize: el.style.fontSize, fontFace: el.style.fontFace, color: el.style.color,
        align: el.style.align, valign: 'top', charSpacing: el.style.charSpacing,
        lineSpacing: el.style.lineSpacing, paraSpaceBefore: el.style.paraSpaceBefore,
        paraSpaceAfter: el.style.paraSpaceAfter, margin: el.style.margin,
        lineSpacingMultiple: el.style.lineSpacingMultiple
      };
      if (el.style.margin) listOptions.margin = el.style.margin;
      targetSlide.addText(el.items, listOptions);
    } else {
      // ── Text elements (p, h1-h6) with v3 adaptive compensation ──
      // Hints set in extractSlideData (see baseStyle._* fields).
      const hasBrBreaks = el.style?._hasBrBreaks;
      const iconOnlyText = el.style?._isIcon === true;
      const centerInFrame = el.style?._centerInFrame || (iconOnlyText && !el.style?._inlineLeadGlyph);
      const hasContainerPadding = el.style?._hasContainerPadding;

      // When the element is a padded container that also rendered a shape behind
      // itself (e.g. .bubble), expanding the text frame would push lines past the
      // visible shape edge. Skip width compensation in that case — the explicit
      // padding already provides safe inset for text wrapping.
      // Centered icon/badge containers already use the visual frame as their
      // text frame. Expanding them for PPT font compensation moves the glyph
      // center away from the background circle/pill.
      const isRotatedText = el.style?.rotate !== undefined;
      const isHeadingWithBreaks = hasBrBreaks && /^h[1-6]$/.test(el.type);
      const widthFactor = (centerInFrame || hasContainerPadding || isRotatedText)
        ? 0
        : Math.max(calculateWidthCompensation(el, slideWidthIn), isHeadingWithBreaks ? COMPENSATION.HEADING_WIDTH : 0);
      const widthIncrease = el.position.w * widthFactor;

      let adjustedX = el.position.x;
      let adjustedW = el.position.w;
      const align = el.style.align;

      if (align === 'center') {
        adjustedX -= widthIncrease / 2;
        adjustedW += widthIncrease;
      } else if (align === 'right') {
        adjustedX -= widthIncrease;
        adjustedW += widthIncrease;
      } else {
        adjustedW += widthIncrease;
      }

      // Flex rows often use a left title plus right-aligned tags/badges.
      // Chromium reports the title's wrapped line box; PPT then preserves that
      // narrow box and wraps earlier. If extraction found clear free space up
      // to the next flex sibling, use it as the textbox's right edge.
      const preferredRightBound = el.style?._preferredRightBound;
      if (!isRotatedText && !el.style?._inlineLeadGlyph && Number.isFinite(preferredRightBound) &&
          preferredRightBound > adjustedX + adjustedW &&
          (align === 'left' || align === undefined)) {
        adjustedW = preferredRightBound - adjustedX;
      }

      // v3: Height compensation for all text. When the source font-size was
      // clamped UP to MIN_FONT_SIZE_PT, the browser laid the box out at the
      // intended (smaller) size; the PPT box must grow proportionally so the
      // larger PPT font has room without spilling into a sibling element.
      const clampRatio = el.style?._fontSizeClampRatio || 1;
      let adjustedH = centerInFrame ? el.position.h : el.position.h * (1 + COMPENSATION.TEXT_HEIGHT) * clampRatio;
      // Clamp height to slide bottom
      if (el.position.y + adjustedH > slideHeightIn) adjustedH = slideHeightIn - el.position.y;
      if (adjustedH < 0.1) adjustedH = 0.1;

      // Centered headings: expand width symmetrically for PPT center alignment
      if (el.style.align === 'center' && /^h[1-6]$/.test(el.type)) {
        const centerX = adjustedX + adjustedW / 2;
        const margin = 0.3;
        const maxExpand = Math.min(centerX - margin, slideWidthIn - centerX - margin);
        if (maxExpand > adjustedW / 2) {
          adjustedX = centerX - maxExpand;
          adjustedW = maxExpand * 2;
        }
      }

      // Clamp to nearest visual parent first. Text inside cards/panels should not
      // grow past the parent's padded content box just because we compensate for
      // PPT font substitution.
      const clip = el.style?._clipBounds;
      let flowHeightClamped = false;
      if (clip) {
        const clipRight = clip.x + clip.w + getNarrowBodyTextClipSlack(el) +
          getMediumSingleLineClipSlack(el);
        if (adjustedX < clip.x) {
          adjustedW -= (clip.x - adjustedX);
          adjustedX = clip.x;
        }
        if (adjustedX + adjustedW > clipRight) {
          const overflowRight = adjustedX + adjustedW - clipRight;
          // Preserve the left edge for left-aligned text inside cards/panels.
          // Shifting left to save compensated width makes stacked card labels
          // (e.g. RESOURCE 01 / title / formula) visibly misalign. For right
          // and centered text, shifting is still the closest match to browser
          // layout because the visual anchor is not the left edge.
          const canShiftLeft = align === 'right' || align === 'center';
          const shiftLeft = canShiftLeft ? Math.min(overflowRight, Math.max(0, adjustedX - clip.x)) : 0;
          adjustedX -= shiftLeft;
          adjustedW -= (overflowRight - shiftLeft);
        }
        if (el.position.y + adjustedH > clip.y + clip.h) adjustedH = (clip.y + clip.h) - el.position.y;
      }
      const beforeFlowClampH = adjustedH;
      adjustedH = clampHeightToNextTextBound(el, adjustedH);
      flowHeightClamped = adjustedH < beforeFlowClampH - 0.001;

      // Clamp to slide bounds (safety net). Rotated text may need an
      // off-slide unrotated frame to keep the rotated visual bbox aligned with
      // the browser bbox, e.g. a vertical side label at left:24px.
      if (!isRotatedText) {
        if (adjustedX < 0) { adjustedW += adjustedX; adjustedX = 0; }
        if (adjustedX + adjustedW > slideWidthIn) adjustedW = slideWidthIn - adjustedX;
      }
      if (adjustedW < 0.1) adjustedW = 0.1;
      if (adjustedH < 0.1) adjustedH = 0.1;
      // Cap at 680pt to prevent over-expansion from width compensation.
      // Do not cap rotated frames: their width is often the visual height.
      if (!isRotatedText && adjustedW > MAX_TEXT_WIDTH_IN) adjustedW = MAX_TEXT_WIDTH_IN;

      // ── Anti-wrap adjustments for single-line text ──────────────────────
      // These run after the box width is finalized so we know the real frame.
      {
        const _txt = extractTextContent(el).replace(/\s+/g, ' ').trim();
        const _compact = _txt.replace(/\s+/g, '');
        const _fsPt = Number(el.style?.fontSize) || 0;
        const _linePt = Number(el.style?.lineSpacing) || _fsPt * 1.35;
        // Treat as one visual line when the source had no <br>/breakLine and the
        // measured browser box is ≤ ~1.8 line-heights tall.
        const _oneLine = _fsPt > 0 && !hasExplicitTextBreaks(el) &&
          (Number(el.position?.h) || 0) * 72 <= _linePt * 1.8;

        // (B) Shrink-to-fit: when a sub-8pt source font was clamped UP to the
        // readability floor (see fontSizeClampRatio / getMinFontSize), the glyph
        // run grows by that ratio. Inside a fixed-width container (card, side
        // panel) the larger PPT font then overflows and wraps to a 2nd line,
        // which collides with the row below (e.g. slide 11 "register() · login()
        // · updateProfile()" over-running the object-oriented-design panel).
        // The browser fit the text on one line at the intended smaller size, so
        // reduce the font just enough to fit again — never below the raw source
        // size, floored at 6pt for legibility.
        const _clampRatio = Number(el.style?._fontSizeClampRatio) || 1;
        if (_oneLine && !centerInFrame && _clampRatio > 1.01) {
          const _boxPt = adjustedW * 72;
          // The width heuristic runs a few percent under real renderers (PPT/
          // LibreOffice substitute fonts are wider), so apply a safety factor
          // when deciding whether the run will overflow and wrap.
          const _estPt = estimateTextWidthPt(_txt, _fsPt) * 1.12;
          if (_boxPt > 0 && _estPt > _boxPt) {
            // The browser fit the run on one line at the intended (pre-clamp)
            // source size, so undo the readability up-clamp — down to a 6pt
            // legibility floor — which guarantees it fits again. Chasing a
            // precise "fit" font is unreliable because real renderers run wider
            // than the width heuristic.
            const _rawPt = _fsPt / _clampRatio;
            const _newFs = Math.max(6, _rawPt);
            if (_newFs < _fsPt - 0.05) {
              const _scale = _newFs / _fsPt;
              el.style.fontSize = _newFs;
              if (Array.isArray(el.text)) {
                el.text.forEach(r => {
                  if (r.options && Number(r.options.fontSize)) {
                    r.options.fontSize = Math.max(6, r.options.fontSize * _scale);
                  }
                });
              }
            }
          }
        }

        // (A) Minimum width for very short single-line labels. Tiny numeric /
        // badge captions ("01", "PHP", "→") are measured tight to the browser
        // glyph run; the wider PPT substitute font (plus any up-clamp) then wraps
        // a 2-char label into two stacked chars (e.g. slide 18 card numbers
        // "01" → "0"/"1"). Guarantee the frame is wide enough to hold the run on
        // one line. Grow symmetrically around the current center so corner-
        // anchored labels barely move. Only act when the current box is tight.
        const _fsPt2 = Number(el.style?.fontSize) || 0;
        if (!isRotatedText && !el.style?._inlineLeadGlyph && _oneLine && _fsPt2 > 0 &&
            _compact.length > 0 && _compact.length <= 12) {
          const _estPt2 = estimateTextWidthPt(_txt, _fsPt2);
          const _curPt = adjustedW * 72;
          if (_estPt2 > _curPt * 0.72) {
            const _needIn = (_estPt2 * 1.18 + _fsPt2 * 0.35) / 72;
            if (_needIn > adjustedW) {
              const _grow = _needIn - adjustedW;
              adjustedX -= _grow / 2;
              adjustedW += _grow;
              // Re-clamp to slide edges (skip for rotated frames handled above).
              if (adjustedX < 0) { adjustedW += adjustedX; adjustedX = 0; }
              if (adjustedX + adjustedW > slideWidthIn) adjustedX = Math.max(0, slideWidthIn - adjustedW);
            }
          }
        }
      }

      // Effective alignment / vertical alignment.
      // - center-in-frame containers (grid/flex place-items:center) → middle+center
      //   so single-char circular badges (.teacher, .thumb-num) sit at the visual
      //   center of the surrounding ellipse instead of the top-left.
      const valignOut = centerInFrame ? 'middle' : 'top';
      const alignOut2 = centerInFrame ? 'center' : (el.style.align || undefined);

      // CSS margins are already reflected in getBoundingClientRect() through
      // normal layout. Re-applying them as PPT paragraph spacing shifts text
      // downward inside its measured box (especially small labels with
      // margin-top). Keep the textbox anchored to the browser bbox.
      const paraBefore = 0;
      const paraAfter  = 0;

      const textOptions = {
        x: adjustedX, y: el.position.y, w: adjustedW, h: adjustedH,
        // Avoid general PowerPoint shrink-to-fit; only use it when a
        // normal-flow sibling below would otherwise be overlapped by height
        // compensation after PPT font substitution/wrapping.
        fit: flowHeightClamped ? 'shrink' : 'none',
        fontSize: el.style.fontSize, fontFace: el.style.fontFace, color: el.style.color,
        bold: el.style.bold, italic: el.style.italic, underline: el.style.underline,
        strike: el.style.strike,
        valign: valignOut, charSpacing: el.style.charSpacing, lineSpacing: el.style.lineSpacing,
        lineSpacingMultiple: el.style.lineSpacingMultiple,
        paraSpaceBefore: paraBefore, paraSpaceAfter: paraAfter,
      };
      const textPayload = Array.isArray(el.text)
        ? el.text.map((run) => {
            const options = { ...(run.options || {}) };
            delete options.paraSpaceBefore;
            delete options.paraSpaceAfter;
            return { ...run, options };
          })
        : el.text;
      // Only zero the inset when the element has no padding of its own; padded
      // containers (e.g. .bubble) need the padding to render as inset so text
      // wraps inside the visible shape.
      const zeroTextInset = el.style?._zeroTextInset === true;
      if (!hasContainerPadding || iconOnlyText || zeroTextInset) textOptions.inset = 0;
      if (alignOut2) textOptions.align = alignOut2;
      if (iconOnlyText || zeroTextInset) textOptions.margin = [0, 0, 0, 0];
      else if (el.style.margin) textOptions.margin = el.style.margin;
      if (el.style.rotate !== undefined) textOptions.rotate = el.style.rotate;
      if (el.style._pptxVert) textOptions.vert = el.style._pptxVert;
      if (el.style.transparency !== null && el.style.transparency !== undefined) textOptions.transparency = el.style.transparency;
      if (el.style.shadow) textOptions.shadow = el.style.shadow;
      // Headings with explicit <br> breaks normally render with wrap:false so
      // PPT preserves the author's exact line breaks. But when a single
      // break-delimited segment is itself wider than the frame (e.g. multi_3
      // slide-2 "building foundation models." — a long second line that the
      // browser re-wraps inside the column), wrap:false lets it bleed off to the
      // right over neighbouring content. Detect that case and allow wrapping so
      // the overflowing segment breaks like it does in the browser.
      let headingBreaksOverflow = false;
      if (isHeadingWithBreaks && Array.isArray(el.text)) {
        const _hfs = Number(el.style?.fontSize) || 0;
        const _boxPt = adjustedW * 72;
        if (_hfs > 0 && _boxPt > 0) {
          let _seg = '';
          const _segPts = [];
          const _flush = () => {
            const s = _seg.replace(/\s+/g, ' ').trim();
            if (s) _segPts.push(estimateTextWidthPt(s, _hfs));
            _seg = '';
          };
          for (const run of el.text) {
            const t = typeof run === 'string' ? run : (run && run.text) || '';
            _seg += t;
            if (run && run.options && run.options.breakLine) _flush();
          }
          _flush();
          const _maxPt = _segPts.length ? Math.max(..._segPts) : 0;
          if (_maxPt > _boxPt * 1.02) {
            // A single <br>-segment is wider than the frame. With wrap:false it
            // would bleed off to the right over adjacent content (multi_3
            // slide-2 "building foundation models." running over the diagram
            // card). Allow wrapping so the segment breaks like it does in the
            // browser; the frame keeps its compensated width so short segments
            // don't over-wrap.
            headingBreaksOverflow = true;
          }
        }
      }
      if (!el.style?._allowWrap && (el.noWrap || isShortAutoNoWrapText(el) || (isHeadingWithBreaks && !headingBreaksOverflow))) textOptions.wrap = false;

      targetSlide.addText(textPayload, textOptions);
    }
  }
}

// Helper: Extract slide data from HTML page
async function extractSlideData(page, slideDims) {
  return await page.evaluate((slideDims) => {
    const PT_PER_PX = 0.75;
    const PX_PER_IN = 96;

    // Switch every element to border-box BEFORE measuring body size. Without this,
    // a child like `width:720pt; padding:0 48pt` overflows the 720pt body under
    // default content-box, making scrollWidth report 1088px instead of 960px —
    // which then shrinks SCALE and leaves empty space on the side of the slide.
    document.querySelectorAll('*').forEach(el => { el.style.boxSizing = 'border-box'; });
    // Force reflow so the new box-sizing affects layout measurements below.
    void document.body.offsetHeight;

    // HTML slide templates are usually authored at a fixed pixel viewport
    // (e.g. 1280×720) that maps to the PPT slide size (e.g. 10×5.625 in).
    // Scale every position/dimension by slideWidthIn / (bodyWidth / 96) so the
    // 1280-wide design fills the 10-inch slide exactly instead of overflowing.
    const slideRoot = document.querySelector('.slide') || document.body;
    const slideRootRect = slideRoot.getBoundingClientRect();
    const CANVAS_LEFT = slideRootRect.left || 0;
    const CANVAS_TOP = slideRootRect.top || 0;
    const bodyWPx = slideRootRect.width || slideRoot.scrollWidth || document.body.clientWidth || 1280;
    const bodyHPx = slideRootRect.height || slideRoot.scrollHeight || document.body.clientHeight || 720;
    const SCALE_X = slideDims.widthIn / (bodyWPx / PX_PER_IN);
    const SCALE_Y = slideDims.heightIn / (bodyHPx / PX_PER_IN);
    // Use a single uniform scale (derived from width) for aspect-preserving
    // layout.  Height overflow is still reported, but scaling width keeps the
    // design identical to HTML proportions.
    const SCALE = SCALE_X;

    // Fonts that are single-weight and should not have bold applied
    // (applying bold causes PowerPoint to use faux bold which makes text wider)
    const SINGLE_WEIGHT_FONTS = ['impact'];

    // Helper: Check if a font should skip bold formatting
    const shouldSkipBold = (fontFamily) => {
      if (!fontFamily) return false;
      const normalizedFont = fontFamily.toLowerCase().replace(/['"]/g, '').split(',')[0].trim();
      return SINGLE_WEIGHT_FONTS.includes(normalizedFont);
    };

    // Known CJK font name fragments (lowercase) — presence means the element targets CJK text
    const CJK_FONT_FRAGMENTS = [
      'yahei', '雅黑', 'noto sans sc', '黑体', 'noto serif sc', '宋体', 'kaiti', '楷体',
      'fangsong', '仿宋', 'pingfang', 'hiragino', 'noto sans cjk', 'noto sans sc',
      'noto sans tc', 'noto sans hk', 'source han sans', '思源黑体', '思源宋体',
      'wenquanyi', 'lxgw wenkai', '霞鹜文楷', 'arial unicode', 'yugothic', 'meiryo', 'ms gothic', 'ms mincho',
      'malgun gothic', 'apple sd gothic', 'heiti', 'songti', 'wawati', 'weibei',
      'libian', 'xingkai', 'baoli', 'yuanti', 'dengxian', '等线', 'stxihei',
      'stheiti', 'stkaiti', 'stsong', 'stfangsong'
    ];

    // Detect if text content contains CJK characters
    const hasCJKChars = (text) => /[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/.test(text);

    // v3: Smart font mapping — PPT-safe fonts pass through, others get mapped
    // fontConfig from caller is still respected as ultimate fallback for CJK/Latin defaults
    const _fc = window.__FONT_CONFIG__ || {};

    // macOS-only / web fonts → cross-platform PPT-safe equivalents
    const FONT_FALLBACK_MAP = {
      'pingfang sc': 'Microsoft YaHei', 'pingfang tc': 'Microsoft YaHei', 'pingfang hk': 'Microsoft YaHei',
      'hiragino sans': 'Microsoft YaHei', 'hiragino sans gb': 'Microsoft YaHei',
      'hiragino mincho pron': 'SimSun', 'hiragino maru gothic pro': 'Microsoft YaHei',
      'heiti sc': 'Microsoft YaHei', 'heiti tc': 'Microsoft YaHei', 'songti sc': 'SimSun',
      'stxihei': 'Microsoft YaHei', 'stheiti': 'Microsoft YaHei', 'stkaiti': 'KaiTi',
      'stsong': 'SimSun', 'stfangsong': 'KaiTi', 'apple sd gothic neo': 'Microsoft YaHei',
      'noto sans sc': 'Microsoft YaHei', 'noto sans tc': 'Microsoft YaHei',
      'noto sans cjk sc': 'Microsoft YaHei', 'noto serif sc': 'SimSun',
      'source han sans sc': 'Microsoft YaHei', 'source han serif sc': 'SimSun',
      'source han sans': 'Microsoft YaHei', 'source han serif': 'SimSun',
      '思源黑体': 'Microsoft YaHei', '思源宋体': 'SimSun',
      '阿里巴巴普惠体': 'Microsoft YaHei',
      'lxgw wenkai': 'KaiTi', 'lxgw wenkai tc': 'KaiTi',
      'lxgw wenkai gb': 'KaiTi', '霞鹜文楷': 'KaiTi', '霞鹜文楷 tc': 'KaiTi',
      'fredoka': 'Arial Rounded MT Bold', 'fredoka one': 'Arial Rounded MT Bold',
      'system-ui': 'Carlito', '-apple-system': 'Carlito', 'blinkmacsystemfont': 'Carlito',
      'segoe ui': 'Carlito', 'helvetica neue': 'Liberation Sans', 'helvetica': 'Liberation Sans',
      'sans-serif': 'Carlito', 'serif': 'Tinos', 'monospace': 'Courier New',
      'inter': 'Carlito', 'roboto': 'Liberation Sans', 'roboto slab': 'Tinos',
      'open sans': 'Carlito', 'lato': 'Carlito', 'montserrat': 'Carlito',
      'poppins': 'Carlito', 'raleway': 'Carlito', 'nunito': 'Carlito',
      'nunito sans': 'Carlito', 'source sans pro': 'Carlito', 'source sans 3': 'Carlito',
      'source serif pro': 'Tinos', 'work sans': 'Carlito', 'dm sans': 'Carlito',
      'space grotesk': 'Carlito', 'plus jakarta sans': 'Carlito',
      'manrope': 'Carlito', 'fira sans': 'Carlito', 'playfair display': 'Tinos',
      'merriweather': 'Tinos', 'libre baskerville': 'Tinos',
      'pt sans': 'Carlito', 'pt serif': 'Tinos', 'ubuntu': 'Carlito',
      'arial': 'Liberation Sans', 'arial black': 'Liberation Sans',
      'arial narrow': 'Liberation Sans', 'georgia': 'Tinos',
      'gill sans mt': 'Carlito', 'century gothic': 'Carlito',
      'palatino linotype': 'Tinos', 'palatino': 'Tinos',
      'trebuchet ms': 'Carlito', 'garamond': 'Tinos',
      'rockwell': 'Tinos', 'candara': 'Carlito', 'corbel': 'Carlito',
      'constantia': 'Tinos', 'cambria': 'Tinos',
      'verdana': 'Carlito', 'tahoma': 'Carlito', 'impact': 'Liberation Sans Narrow',
      'comic sans ms': 'Arial Rounded MT Bold', 'lucida sans': 'Carlito',
      'franklin gothic medium': 'Liberation Sans', 'bodoni mt': 'Tinos',
      'copperplate gothic': 'Carlito', 'tw cen mt': 'Carlito',
      'century schoolbook': 'Tinos', 'book antiqua': 'Tinos',
      // Condensed / display sans → Liberation Sans Narrow (closer geometry)
      'bebas neue': 'Liberation Sans Narrow', 'bebas neue pro': 'Liberation Sans Narrow',
      'oswald': 'Liberation Sans Narrow', 'anton': 'Liberation Sans Narrow',
      'fjalla one': 'Liberation Sans Narrow', 'teko': 'Liberation Sans Narrow',
      'saira condensed': 'Liberation Sans Narrow', 'saira': 'Carlito',
      'roboto condensed': 'Liberation Sans Narrow', 'archivo narrow': 'Liberation Sans Narrow',
      'barlow condensed': 'Liberation Sans Narrow', 'barlow semi condensed': 'Liberation Sans Narrow',
      'encode sans condensed': 'Liberation Sans Narrow',
      'pt sans narrow': 'Liberation Sans Narrow',
      'league spartan': 'Liberation Sans Narrow', 'league gothic': 'Liberation Sans Narrow',
      'six caps': 'Liberation Sans Narrow', 'big shoulders display': 'Liberation Sans Narrow',
      'big shoulders text': 'Liberation Sans Narrow',
      'alumni sans': 'Liberation Sans Narrow', 'dharma gothic e': 'Liberation Sans Narrow',
      'titillium web': 'Liberation Sans Narrow', 'staatliches': 'Liberation Sans Narrow',
      'bungee': 'Liberation Sans Narrow', 'bungee shade': 'Liberation Sans Narrow', 'bungee inline': 'Liberation Sans Narrow',
      'orbitron': 'Liberation Sans Narrow', 'rajdhani': 'Liberation Sans Narrow',
      // Pixel / retro fonts — none ship with PPT; map to a monospaced
      // pass-through so glyphs at least keep a uniform Latin width.
      'vt323': 'Liberation Mono', 'press start 2p': 'Liberation Mono',
      'major mono display': 'Liberation Mono', 'silkscreen': 'Liberation Mono',
      'pixelify sans': 'Liberation Mono', 'jersey 10': 'Liberation Mono',
      // Modern web sans-serif families that LLMs love to reach for
      'inter tight': 'Carlito', 'recursive': 'Carlito', 'figtree': 'Carlito',
      'sora': 'Carlito', 'urbanist': 'Carlito', 'be vietnam pro': 'Carlito',
      'rubik': 'Carlito', 'archivo': 'Carlito', 'instrument sans': 'Carlito',
      'instrument serif': 'Tinos', 'cormorant garamond': 'Tinos',
      'eb garamond': 'Tinos', 'lora': 'Tinos', 'crimson text': 'Tinos',
      'crimson pro': 'Tinos', 'fraunces': 'Tinos', 'spectral': 'Tinos',
      'literata': 'Tinos', 'newsreader': 'Tinos',
      // Newer web fonts (2023-2026 design trend choices)
      'geist': 'Carlito', 'geist sans': 'Carlito',
      'onest': 'Carlito', 'satoshi': 'Carlito', 'general sans': 'Carlito',
      'switzer': 'Carlito', 'syne': 'Carlito', 'red hat display': 'Carlito',
      'red hat text': 'Carlito', 'public sans': 'Carlito',
      'reddit sans': 'Carlito', 'mulish': 'Carlito', 'hanken grotesk': 'Carlito',
      'karla': 'Carlito', 'outfit': 'Carlito', 'bricolage grotesque': 'Carlito',
      'host grotesk': 'Carlito', 'unbounded': 'Carlito',
      'ibm plex sans': 'Carlito', 'ibm plex serif': 'Tinos',
      'noto sans': 'Carlito', 'noto serif': 'Tinos',
      'libre franklin': 'Carlito', 'oswald': 'Liberation Sans Narrow',
      'barlow': 'Carlito', 'barlow condensed': 'Liberation Sans Narrow',
      'epilogue': 'Carlito', 'overpass': 'Carlito', 'sofia sans': 'Carlito',
      'gabarito': 'Carlito', 'wix madefor display': 'Carlito',
      'wix madefor text': 'Carlito',
      // More serif options
      'bitter': 'Tinos', 'vollkorn': 'Tinos', 'pt serif': 'Tinos',
      'cardo': 'Tinos', 'old standard tt': 'Tinos',
      'noto serif display': 'Tinos', 'tinos': 'Tinos',
      'big shoulders display': 'Liberation Sans Narrow', 'roboto serif': 'Tinos',
      'dm serif display': 'Tinos', 'dm serif text': 'Tinos',
      // Programming / monospaced web fonts → Courier New (PPT-safe)
      'jetbrains mono': 'Courier New', 'fira code': 'Courier New',
      'source code pro': 'Courier New', 'ibm plex mono': 'Courier New',
      'space mono': 'Courier New', 'roboto mono': 'Courier New',
      'cascadia code': 'Courier New', 'cascadia mono': 'Courier New',
      'ubuntu mono': 'Courier New', 'geist mono': 'Courier New',
      'departure mono': 'Courier New', 'inconsolata': 'Courier New',
      'commit mono': 'Courier New', 'martian mono': 'Courier New',
      // CJK display fonts that aren't in PPT — map to Microsoft YaHei
      'smiley sans': 'Microsoft YaHei', 'smiley sans oblique': 'Microsoft YaHei',
      'lxgw wenkai screen': 'KaiTi', 'zcool kuaile': 'KaiTi',
      'zcool xiaowei': 'SimSun', 'zcool qingke huangyou': 'KaiTi',
      'long cang': 'KaiTi', 'ma shan zheng': 'KaiTi',
      'liu jian mao cao': 'KaiTi',
      'kaiti': 'KaiTi', '楷体': 'KaiTi',
      'fangsong': 'KaiTi', '仿宋': 'KaiTi',
      'dengxian': 'Microsoft YaHei', '等线': 'Microsoft YaHei',
      '黑体': 'Microsoft YaHei', '宋体': 'SimSun',
      'simhei': 'Microsoft YaHei', 'simsun': 'SimSun',
      'microsoft yahei': 'Microsoft YaHei',
      // Modern Chinese-friendly variants
      'harmonyos sans': 'Microsoft YaHei', 'harmonyos sans sc': 'Microsoft YaHei',
      'opposans': 'Microsoft YaHei', 'oppo sans': 'Microsoft YaHei',
      'misans': 'Microsoft YaHei', 'mi sans': 'Microsoft YaHei',
      '小米兰亭': 'Microsoft YaHei', 'xiaomi lanting': 'Microsoft YaHei',
      '霞鹜文楷': 'KaiTi', 'lxgw wenkai gb': 'KaiTi',
      '阿里妈妈数黑体': 'Microsoft YaHei', 'alimama shuheiti': 'Microsoft YaHei',
      'noto serif hk': 'SimSun', 'noto sans hk': 'Microsoft YaHei',
      'noto sans tc': 'Microsoft YaHei', 'noto serif tc': 'SimSun',
      'noto sans jp': 'Microsoft YaHei', 'noto serif jp': 'SimSun',
      'noto sans kr': 'Microsoft YaHei', 'noto serif kr': 'SimSun',
      // Calligraphic/handwriting Chinese → KaiTi (warmest substitute)
      '楷书': 'KaiTi', '行楷': 'KaiTi', '隶书': 'KaiTi',
      'cangerjinkai': 'KaiTi', 'cangermingbo': 'SimSun',
      // Additional commonly-referenced Chinese families
      'wenquanyi micro hei': 'Microsoft YaHei', 'wenquanyi zen hei': 'Microsoft YaHei',
      '文泉驿微米黑': 'Microsoft YaHei', '文泉驿正黑': 'Microsoft YaHei',
      'adobe heiti std': 'Microsoft YaHei', 'adobe fangsong std': 'KaiTi',
      'adobe kaiti std': 'KaiTi', 'adobe song std': 'SimSun',
      'ar pl ukai cn': 'KaiTi', 'ar pl uming cn': 'SimSun',
      'fzhei': 'Microsoft YaHei', 'fzkai': 'KaiTi', 'fzsong': 'SimSun',
      '方正黑体': 'Microsoft YaHei', '方正楷体': 'KaiTi', '方正宋体': 'SimSun',
      '方正书宋': 'SimSun', '方正仿宋': 'KaiTi',
      '汉仪旗黑': 'Microsoft YaHei', '汉仪文黑': 'Microsoft YaHei',
      'hyqihei': 'Microsoft YaHei', 'hywenhei': 'Microsoft YaHei',
      'ruiziyun': 'Microsoft YaHei', '锐字': 'Microsoft YaHei',
      'dingtalk jinbuti': 'Microsoft YaHei', '钉钉进步体': 'Microsoft YaHei',
      'youshebiaotihei': 'Microsoft YaHei', '优设标题黑': 'Microsoft YaHei',
      'pangmen': 'Microsoft YaHei', '庞门正道标题体': 'Microsoft YaHei',
      'aocomic': 'KaiTi', 'maoken': 'KaiTi',
      'tw-kai': 'KaiTi', 'mingliu': 'SimSun', 'pmingliu': 'SimSun',
      // Korean web fonts
      'noto sans korean': 'Microsoft YaHei', 'noto serif korean': 'SimSun',
      'spoqa han sans': 'Microsoft YaHei', 'spoqa han sans neo': 'Microsoft YaHei',
      'nanum gothic': 'Microsoft YaHei', 'nanum myeongjo': 'SimSun',
      'nanum barun gothic': 'Microsoft YaHei', 'nanum pen script': 'KaiTi',
      'gowun batang': 'SimSun', 'gowun dodum': 'Microsoft YaHei',
      'do hyeon': 'Microsoft YaHei', 'jua': 'Microsoft YaHei',
      'black han sans': 'Microsoft YaHei', 'black and white picture': 'Microsoft YaHei',
      'sunflower': 'Microsoft YaHei', 'gaegu': 'KaiTi',
      // Japanese display fonts
      'kosugi maru': 'Microsoft YaHei', 'kosugi': 'Microsoft YaHei',
      'sawarabi gothic': 'Microsoft YaHei', 'sawarabi mincho': 'SimSun',
      'm plus 1p': 'Microsoft YaHei', 'm plus rounded 1c': 'Microsoft YaHei',
      'm plus 1': 'Microsoft YaHei', 'm plus 2': 'Microsoft YaHei',
      'klee one': 'KaiTi', 'shippori mincho': 'SimSun',
      'shippori mincho b1': 'SimSun', 'rampart one': 'Microsoft YaHei',
      'rocknroll one': 'Microsoft YaHei', 'reggae one': 'Microsoft YaHei',
      'dot gothic 16': 'Liberation Mono', 'dotgothic16': 'Liberation Mono',
      'yusei magic': 'Microsoft YaHei', 'mochiy pop one': 'Microsoft YaHei',
      'kaisei opti': 'SimSun', 'kaisei tokumin': 'SimSun',
      // Additional modern Google Fonts not yet covered
      'albert sans': 'Carlito', 'cabinet grotesk': 'Carlito',
      'clash display': 'Liberation Sans Narrow', 'clash grotesk': 'Carlito',
      'general sans': 'Carlito', 'supreme': 'Carlito', 'chillax': 'Carlito',
      'erode': 'Tinos', 'gambarino': 'Tinos', 'melodrama': 'Tinos',
      'tanker': 'Liberation Sans Narrow', 'panchang': 'Liberation Sans Narrow',
      'array': 'Liberation Sans Narrow', 'sentient': 'Tinos',
      'familjen grotesk': 'Carlito', 'instrument display': 'Tinos',
      'fragment mono': 'Courier New', 'redaction': 'Tinos',
      'authentic sans': 'Carlito', 'space grotesk variable': 'Carlito',
      'national park': 'Liberation Sans Narrow',
      'reddit mono': 'Courier New', 'noto sans mono': 'Courier New',
      'azeret mono': 'Courier New', 'sometype mono': 'Courier New',
      // Display script families occasionally requested
      'lobster': 'Tinos', 'pacifico': 'Tinos', 'great vibes': 'Tinos',
      'sacramento': 'Tinos', 'allura': 'Tinos', 'tangerine': 'Tinos',
      'dancing script': 'Tinos', 'satisfy': 'Tinos', 'parisienne': 'Tinos',
      'amatic sc': 'Carlito', 'shadows into light': 'Tinos',
      'caveat': 'Tinos', 'kalam': 'Tinos', 'patrick hand': 'Tinos',
      'gloria hallelujah': 'Tinos', 'architects daughter': 'Tinos',
      'permanent marker': 'Tinos', 'indie flower': 'Tinos',
      'homemade apple': 'Tinos', 'rock salt': 'Tinos',
      // Decorative serifs and slab serifs
      'abril fatface': 'Tinos', 'alfa slab one': 'Tinos',
      'josefin slab': 'Tinos', 'zilla slab': 'Tinos',
      'roboto slab': 'Tinos', 'arvo': 'Tinos',
      'patua one': 'Tinos', 'sansita': 'Carlito',
    };

    // PPT-safe fonts — pass through directly without mapping.
    // Liberation Sans Narrow is shipped widely and is the closest stand-in for
    // condensed display fonts (Bebas Neue, Oswald, Barlow Condensed, …).
    const PPT_SAFE_FONTS = new Set([
      "microsoft yahei", "simsun", "kaiti", "microsoft jhenghei", "dengxian",
      "carlito", "liberation sans", "liberation sans narrow",
      "liberation serif", "liberation mono", "arial rounded mt bold",
      "aptos", "aptos display", "aptos narrow",
      "tinos", "courier new", "segoe ui symbol", "noto color emoji",
    ]);

    // Heuristic classifier — for unknown font names, infer the closest PPT-safe
    // substitute from keywords in the family name. This lets new Google/web
    // fonts the explicit map doesn't cover still get a sensible mapping
    // (e.g. "Bebas Neue Pro" → Liberation Sans Narrow because of "neue"/condensed
    // pattern, "Source Han Sans HW" → Microsoft YaHei because of "han"/"sans").
    // Returns null if no confident match — caller decides the final fallback.
    const heuristicMapFont = (font, cjkText) => {
      const lower = font.toLowerCase();
      // Strip common weight / style modifiers so "Foo Bold Condensed" → "foo condensed"
      const cleaned = lower
        .replace(/\b(thin|extralight|ultralight|light|regular|book|medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy)\b/g, ' ')
        .replace(/\b(italic|oblique|roman|upright)\b/g, ' ')
        .replace(/\bw\d{1,3}\b/g, ' ') // Weight numbers like "W400"
        .replace(/\s+/g, ' ')
        .trim();

      // ── CJK keyword routing ────────────────────────────────────────────
      // Heiti / sans-style Chinese
      if (/(\bhei\b|黑|gothic|gothik|sans.*(cn|sc|tc|hk|jp|kr|cjk|chinese|chn|han|hans|hant)|(cn|sc|tc|hk|jp|kr|cjk|chinese|chn|han|hans|hant).*sans)/.test(cleaned)) {
        return 'Microsoft YaHei';
      }
      // Songti / Mincho / serif Chinese
      if (/(\bsong\b|宋|\bming\b|明朝|明体|mincho|serif.*(cn|sc|tc|hk|jp|kr|cjk|chinese|han|hans|hant)|(cn|sc|tc|hk|jp|kr|cjk|chinese|han|hans|hant).*serif)/.test(cleaned)) {
        return 'SimSun';
      }
      // Kaiti / Fangsong / handwriting / brush
      if (/(\bkai\b|楷|fangsong|仿宋|xing(kai|shu)?|行楷|行书|li ?bian|隶书|maru|手写|brush|caoshu|草书|手书|hand|script)/.test(cleaned)) {
        return 'KaiTi';
      }
      // Any other recognisable CJK-script tag → Microsoft YaHei default
      if (CJK_FONT_FRAGMENTS.some(f => lower.includes(f))) {
        return 'Microsoft YaHei';
      }
      // Text content is CJK but the font is something else → caller's CJK default
      if (cjkText) return _fc.cjk || 'Microsoft YaHei';

      // ── Latin keyword routing ──────────────────────────────────────────
      // Monospace / code fonts
      if (/(\bmono\b|\bcode\b|console|courier|terminal|typewriter|fixedsys|menlo|monaco|consolas|hack|iosevka|berkeley mono|comic mono)/.test(cleaned)) {
        return 'Courier New';
      }
      // Condensed / narrow / compressed display fonts → Liberation Sans Narrow
      if (/(condensed|narrow|compressed|compact|extended|cond\b|cn\b)/.test(cleaned)) {
        return 'Liberation Sans Narrow';
      }
      // Well-known condensed display families even without the keyword
      if (/(bebas|oswald|anton|teko|saira|fjalla|tungsten|alfa slab|six caps|big shoulders|archivo narrow|barlow condensed|roboto condensed|encode sans condensed|league spartan|league gothic|alumni sans|dharma gothic)/.test(cleaned)) {
        return 'Liberation Sans Narrow';
      }
      // Slab serifs → Tinos (closer in colour than Carlito)
      if (/(slab|rockwell|chunk|courier prime|josefin slab|zilla slab|alfa)/.test(cleaned)) {
        return 'Tinos';
      }
      // Generic serif markers
      if (/(\bserif\b|antiqua|times|roman|garamond|georgia|caslon|baskerville|didot|bodoni|jenson|sabon|trajan|minion|palatino|fraktur|book|elephant|venetian)/.test(cleaned)) {
        return 'Tinos';
      }
      // Script / handwriting / brush Latin → Tinos (closest stylised humanist)
      if (/(script|hand|brush|cursive|calligraphic|signature|pen|ink|chalk|marker|kalam|caveat|pacifico|dancing|sacramento|satisfy|allura|great vibes|tangerine|parisienne|amatic|shadows|gloria|architects|patrick|reenie|indie|covered by your grace|nothing you could do|rock salt|permanent marker|homemade|just another hand)/.test(cleaned)) {
        return 'Tinos';
      }
      // Pixel / retro display → Liberation Mono (uniform width preserves block style)
      if (/(pixel|pixelify|press start|vt323|silkscreen|jersey|retro|8.?bit|terminal)/.test(cleaned)) {
        return 'Liberation Mono';
      }
      // Anything explicitly "sans" / "grotesk" / "gothic" / "neue" / common humanist → Carlito
      if (/(\bsans\b|\bgrotesk\b|grotesque|gothic|neue|deck|display|text|ui|interface|system|humanist|geometric|neo|standard|modern)/.test(cleaned)) {
        return 'Carlito';
      }
      return null;
    };

    const mapFontFace = (fontFamily, textContent = '') => {
      if (!fontFamily) {
        return hasCJKChars(textContent) ? (_fc.cjk || 'Microsoft YaHei') : (_fc.latin || 'Carlito');
      }
      const fonts = fontFamily.split(',').map(f => f.trim().replace(/['"]/g, ''));
      const cjkText = hasCJKChars(textContent);
      // First pass: any safe / mapped font wins. Track the first unknown
      // (non-generic, non-CJK-fragment) font for the heuristic second pass —
      // the previous behaviour returned the raw unknown name, which meant the
      // chain "VT323, Microsoft YaHei, monospace" never reached the YaHei →
      // Microsoft YaHei fallback or the monospace generic for English text.
      let firstUnknown = null;
      for (const font of fonts) {
        const lower = font.toLowerCase();
        const isCJKFont = CJK_FONT_FRAGMENTS.some(f => lower.includes(f));
        if (PPT_SAFE_FONTS.has(lower)) {
          // CJK font specified but text has no CJK characters → use Latin font to avoid
          // mixing Carlito and Microsoft YaHei for English-only content
          if (isCJKFont && !cjkText) return _fc.latin || 'Carlito';
          return font;
        }
        if (FONT_FALLBACK_MAP[lower]) {
          const mapped = FONT_FALLBACK_MAP[lower];
          const mappedIsCJK = CJK_FONT_FRAGMENTS.some(f => mapped.toLowerCase().includes(f));
          // Keep script families coherent: CJK text should not fall back to a
          // Latin web-font substitute, and Latin-only text should not inherit a
          // Chinese face just because the surrounding template uses one.
          if (!mappedIsCJK && cjkText) continue;
          if (mappedIsCJK && !cjkText) continue;
          return mapped;
        }
        if (['sans-serif', 'serif', 'monospace', 'cursive', 'fantasy'].includes(lower)) continue;
        if (isCJKFont && !cjkText) continue;
        if (isCJKFont || cjkText) return _fc.cjk || 'Microsoft YaHei';
        // Unknown non-CJK font with non-CJK text — remember and keep looking
        // so the next font in the chain (often a system fallback) gets a turn.
        if (!firstUnknown) firstUnknown = font;
      }
      // Second pass: nothing in the chain matched the explicit map. Try the
      // keyword heuristic on each font in order before giving up.
      for (const font of fonts) {
        const lower = font.toLowerCase();
        if (PPT_SAFE_FONTS.has(lower)) continue;
        if (FONT_FALLBACK_MAP[lower]) continue;
        if (['sans-serif', 'serif', 'monospace', 'cursive', 'fantasy'].includes(lower)) continue;
        const guessed = heuristicMapFont(font, cjkText);
        if (guessed) {
          const guessedIsCJK = CJK_FONT_FRAGMENTS.some(f => guessed.toLowerCase().includes(f));
          if (!guessedIsCJK && cjkText) continue;
          return guessed;
        }
      }
      // Last-resort generic fallback by text script — do NOT return the raw
      // unknown font name, because PPT will substitute it with whatever the
      // viewer has installed (often unreadable for CJK). Carlito / Microsoft YaHei
      // are always present in the deck workflow.
      if (cjkText) return _fc.cjk || 'Microsoft YaHei';
      return _fc.latin || 'Carlito';
    };

    const hasLatinChars = (text = "") => /[A-Za-z]/.test(text);
    const hasDigitChars = (text = "") => /[0-9０-９]/.test(text);
    const hasEmojiChars = (text = "") => /[\u2600-\u27BF]|[\uD800-\uDBFF][\uDC00-\uDFFF]/.test(text);
    const hasIconSymbolChars = (text = "") => /[\u2190-\u21FF\u2300-\u23FF\u2900-\u297F\u2460-\u24FF\u25A0-\u27BF\u2B00-\u2BFF]|[\uD800-\uDBFF][\uDC00-\uDFFF]/.test(text);
    const isIconOnlyText = (text = "") => {
      const t = String(text).trim();
      if (!t) return false;
      const compact = t.replace(/[\s\uFE0E\uFE0F\u200D\u20E3]/g, "");
      if (!compact || Array.from(compact).length > 4) return false;
      if (hasCJKChars(compact) || /[A-Za-z0-9０-９]/.test(compact)) return false;
      return hasIconSymbolChars(compact);
    };
    const shouldApplyPptBold = (fontWeight) => fontWeight === "bold" || (parseInt(fontWeight, 10) || 0) >= 700;
    const isMediumOrBold = (fontWeight) => fontWeight === "bold" || (parseInt(fontWeight, 10) || 0) >= 600;

    const shouldUseEmphasisFont = (text = "") => {
      const t = String(text).trim();
      if (!t || hasCJKChars(t) || !hasDigitChars(t)) return false;
      if (t.length > 36) return false;
      const compact = t.replace(/\s+/g, "");
      const useful = compact.replace(/[^0-9０-９A-Za-z.,:;_#%+\-\/()\[\]·]/g, "");
      const ratio = useful.length / Math.max(1, compact.length);
      const labelPrefix = /^(?:lv|no|honor|resource|step|part|section|chapter|page|slide|p|q|a|item|case|fig|table)\b/i.test(compact);
      return ratio >= 0.65 || labelPrefix;
    };

    const sameRunOptions = (a = {}, b = {}) => {
      const keys = ["fontFace", "fontSize", "color", "bold", "italic", "underline", "strike", "charSpacing", "transparency", "highlight", "subscript", "superscript"];
      return keys.every(k => a[k] === b[k]);
    };

    const pushTextRun = (runs, text, options) => {
      if (!text) return;
      const cleanOptions = { ...options };
      const prev = runs[runs.length - 1];
      if (prev && sameRunOptions(prev.options, cleanOptions)) prev.text += text;
      else runs.push({ text, options: cleanOptions });
    };

    const appendTextRuns = (runs, text, baseOptions = {}) => {
      if (!text) return;
      const fullText = String(text);
      const whole = fullText.trim();
      if (whole && !hasCJKChars(whole) && shouldUseEmphasisFont(whole)) {
        pushTextRun(runs, fullText, { ...baseOptions, fontFace: _fc.emphasis || "Liberation Sans Narrow" });
        return;
      }
      if (whole && hasEmojiChars(whole) && Array.from(whole).length <= 4) {
        pushTextRun(runs, fullText, { ...baseOptions, fontFace: _fc.symbol || "Segoe UI Symbol", bold: false });
        return;
      }
      const shouldSplit = (hasCJKChars(fullText) && (hasLatinChars(fullText) || hasDigitChars(fullText) || hasEmojiChars(fullText))) || hasEmojiChars(fullText);
      if (!shouldSplit) {
        pushTextRun(runs, fullText, baseOptions);
        return;
      }
      const tokenRe = /([\uD800-\uDBFF][\uDC00-\uDFFF]|[A-Za-z]+\.?\d[A-Za-z0-9._:/+%\-]*|[+\-]?\d[\d.,:/+%\-]*(?:[A-Za-z]+)?|[A-Za-z]+(?:[-_][A-Za-z]+)*)/g;
      let last = 0;
      let match;
      while ((match = tokenRe.exec(fullText)) !== null) {
        if (match.index > last) pushTextRun(runs, fullText.slice(last, match.index), baseOptions);
        const token = match[0];
        const tokenOptions = { ...baseOptions };
        if (hasEmojiChars(token)) {
          tokenOptions.fontFace = _fc.symbol || "Segoe UI Symbol";
          tokenOptions.bold = false;
        } else if (shouldUseEmphasisFont(token)) {
          tokenOptions.fontFace = _fc.emphasis || "Liberation Sans Narrow";
        } else if (hasLatinChars(token) && hasCJKChars(fullText)) {
          tokenOptions.fontFace = _fc.latin || "Carlito";
        }
        pushTextRun(runs, token, tokenOptions);
        last = match.index + token.length;
      }
      if (last < fullText.length) pushTextRun(runs, fullText.slice(last), baseOptions);
    };

    const splitTextIntoFontRuns = (text, baseOptions = {}) => {
      const runs = [];
      appendTextRuns(runs, text, baseOptions);
      return runs.length > 1 || (runs[0] && !sameRunOptions(runs[0].options, baseOptions)) ? runs : null;
    };

    // Unit conversion helpers — all use SCALE so 1280×720 HTML maps to 10×5.625" slide.
    const pxToInch = (px) => (px / PX_PER_IN) * SCALE;
    const relX = (x) => x - CANVAS_LEFT;
    const relY = (y) => y - CANVAS_TOP;
    const rectPosition = (rect) => ({
      x: pxToInch(relX(rect.left)),
      y: pxToInch(relY(rect.top)),
      w: pxToInch(rect.width),
      h: pxToInch(rect.height)
    });
    const pxToPoints = (pxStr) => parseFloat(pxStr) * PT_PER_PX * SCALE;
    // Font sizes specifically: keep the floor readable, but allow dense CJK body
    // text to stay closer to the browser layout. A blanket 8pt clamp makes
    // 12.5px Chinese text about 14% wider on 1280px templates, which causes
    // premature wrapping inside cards.
    const MIN_FONT_SIZE_PT = 8;
    const MIN_CJK_BODY_FONT_SIZE_PT = 7;
    const getMinFontSize = (textContent = '') => hasCJKChars(textContent) ? MIN_CJK_BODY_FONT_SIZE_PT : MIN_FONT_SIZE_PT;
    const pxToFontSize = (pxStr, textContent = '') => Math.max(getMinFontSize(textContent), pxToPoints(pxStr));
    // Returns >1 when pxToFontSize had to clamp the value upward (i.e. the
    // PPT font is bigger than the source HTML font would be at slide scale).
    // Callers use this to bump the text-frame height accordingly so the
    // larger PPT font doesn't overflow the box that was sized for the
    // smaller browser font.
    const fontSizeClampRatio = (pxStr, textContent = '') => {
      const raw = pxToPoints(pxStr);
      const minFontSize = getMinFontSize(textContent);
      if (!Number.isFinite(raw) || raw >= minFontSize) return 1;
      return minFontSize / Math.max(raw, 0.1);
    };
    const rgbToHex = (rgbStr) => {
      // Handle transparent backgrounds by defaulting to white
      if (!rgbStr) return 'FFFFFF';
      if (rgbStr === 'rgba(0, 0, 0, 0)' || rgbStr === 'transparent') return 'FFFFFF';

      // Already a hex value? (#xxx / #xxxxxx / #xxxxxxxx)
      if (rgbStr.startsWith('#')) {
        const hex = rgbStr.replace('#', '');
        if (hex.length === 3) {
          return hex.split('').map(c => c + c).join('').toUpperCase();
        }
        if (hex.length === 4) {
          // #RGBA — drop alpha
          return hex.slice(0, 3).split('').map(c => c + c).join('').toUpperCase();
        }
        if (hex.length === 6) return hex.toUpperCase();
        if (hex.length === 8) return hex.slice(0, 6).toUpperCase();
        return 'FFFFFF';
      }

      // RGB / RGBA (browsers normalize most named colors into rgb() form already)
      const rgbMatch = rgbStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
      if (rgbMatch) {
        return rgbMatch.slice(1).map(n => parseInt(n).toString(16).padStart(2, '0')).join('').toUpperCase();
      }

      // HSL / HSLA — convert to RGB then hex
      const hslMatch = rgbStr.match(/hsla?\(\s*([\d.]+)(?:deg)?\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%/);
      if (hslMatch) {
        const h = parseFloat(hslMatch[1]) / 360;
        const s = parseFloat(hslMatch[2]) / 100;
        const l = parseFloat(hslMatch[3]) / 100;
        const hue2rgb = (p, q, t) => {
          if (t < 0) t += 1;
          if (t > 1) t -= 1;
          if (t < 1 / 6) return p + (q - p) * 6 * t;
          if (t < 1 / 2) return q;
          if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
          return p;
        };
        let r, g, b;
        if (s === 0) {
          r = g = b = l;
        } else {
          const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
          const p = 2 * l - q;
          r = hue2rgb(p, q, h + 1 / 3);
          g = hue2rgb(p, q, h);
          b = hue2rgb(p, q, h - 1 / 3);
        }
        return [r, g, b]
          .map(v => Math.round(v * 255).toString(16).padStart(2, '0'))
          .join('').toUpperCase();
      }

      // Fallback — unknown color spec
      return 'FFFFFF';
    };

    const extractAlpha = (rgbStr) => {
      if (!rgbStr) return null;
      // RGBA
      const rgbaMatch = rgbStr.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/);
      if (rgbaMatch && rgbaMatch[4]) {
        const alpha = parseFloat(rgbaMatch[4]);
        if (!Number.isFinite(alpha) || alpha >= 1) return null;
        return Math.round((1 - alpha) * 100);
      }
      // HSLA
      const hslaMatch = rgbStr.match(/hsla\(\s*[\d.]+(?:deg)?\s*,\s*[\d.]+%\s*,\s*[\d.]+%\s*,\s*([\d.]+)\)/);
      if (hslaMatch && hslaMatch[1]) {
        const alpha = parseFloat(hslaMatch[1]);
        if (!Number.isFinite(alpha) || alpha >= 1) return null;
        return Math.round((1 - alpha) * 100);
      }
      // 8-digit hex (#RRGGBBAA)
      if (rgbStr.startsWith('#') && rgbStr.length === 9) {
        const a = parseInt(rgbStr.slice(7, 9), 16) / 255;
        if (!Number.isFinite(a) || a >= 1) return null;
        return Math.round((1 - a) * 100);
      }
      return null;
    };

    // Combine an rgba/hsla color's alpha channel with the element's CSS `opacity`
    // into a single transparency value (0–100, where higher = more transparent —
    // the convention pptxgenjs expects). Both reduce visibility, so we use:
    //   finalOpacity = colorOpacity × elementOpacity
    //   transparency = (1 − finalOpacity) × 100
    // Returns null when neither dimension reduces visibility (i.e. fully opaque).
    //
    // This is what the user's `<span class="watermark">液</span>` case needs:
    // its color is opaque rgb(...) but `opacity: 0.05` makes it nearly invisible.
    // Without this helper, the watermark renders at 100% opacity in PPT.
    const computeTransparency = (colorStr, opacityStr) => {
      const colorT = extractAlpha(colorStr); // 0..100 or null
      const cssOpacity = parseFloat(opacityStr);
      const opacityT = (Number.isFinite(cssOpacity) && cssOpacity < 1)
        ? Math.round((1 - cssOpacity) * 100)
        : null;
      if (colorT === null && opacityT === null) return null;
      const colorOpacity = (100 - (colorT || 0)) / 100;
      const elementOpacity = (100 - (opacityT || 0)) / 100;
      const finalT = Math.round((1 - colorOpacity * elementOpacity) * 100);
      return finalT > 0 ? finalT : null;
    };


    const splitCssTopLevel = (value) => {
      const out = [];
      let cur = '';
      let depth = 0;
      for (const ch of String(value || '')) {
        if (ch === '(') depth++;
        else if (ch === ')') depth = Math.max(0, depth - 1);
        if (ch === ',' && depth === 0) {
          out.push(cur.trim());
          cur = '';
        } else {
          cur += ch;
        }
      }
      if (cur.trim()) out.push(cur.trim());
      return out;
    };

    const cssGradientAngle = (dir) => {
      const d = String(dir || '').trim().toLowerCase();
      const deg = d.match(/(-?[\d.]+)deg/);
      if (deg) return ((parseFloat(deg[1]) % 360) + 360) % 360;
      const turn = d.match(/(-?[\d.]+)turn/);
      if (turn) return ((parseFloat(turn[1]) * 360 % 360) + 360) % 360;
      if (/to\s+bottom\s+right/.test(d)) return 135;
      if (/to\s+top\s+right/.test(d)) return 45;
      if (/to\s+bottom\s+left/.test(d)) return 225;
      if (/to\s+top\s+left/.test(d)) return 315;
      if (/to\s+right/.test(d)) return 90;
      if (/to\s+left/.test(d)) return 270;
      if (/to\s+bottom/.test(d)) return 180;
      if (/to\s+top/.test(d)) return 0;
      return 180;
    };

    const parseLinearGradientLayer = (layer) => {
      const m = String(layer || '').trim().match(/^linear-gradient\((.*)\)$/i);
      if (!m) return null;
      const parts = splitCssTopLevel(m[1]);
      if (parts.length < 2) return null;
      let angle = 180;
      let stopParts = parts;
      if (/^(to\b|[-\d.]+(?:deg|turn|rad)\b)/i.test(parts[0])) {
        angle = cssGradientAngle(parts[0]);
        stopParts = parts.slice(1);
      }
      const stops = stopParts.map((part, idx) => {
        const p = part.trim();
        const cm = p.match(/^(rgba?\([^)]*\)|hsla?\([^)]*\)|#[0-9a-fA-F]{3,8}|transparent|[a-zA-Z]+)\s*(.*)$/i);
        if (!cm) return null;
        const posM = cm[2].match(/(-?[\d.]+)%/);
        return {
          color: cm[1],
          pos: posM ? Math.max(0, Math.min(1, parseFloat(posM[1]) / 100)) : (stopParts.length === 1 ? 0 : idx / (stopParts.length - 1))
        };
      }).filter(Boolean);
      return stops.length >= 2 ? { angle, stops } : null;
    };

    // Parse a single `radial-gradient(...)` layer. Handles the common authored
    // forms: an optional leading config (shape / explicit "<rx>% <ry>%" size /
    // "at <x>% <y>%" position) followed by colour stops. Position defaults to
    // center; size defaults to cover (max dimension). Used both for mesh cover
    // backgrounds and standalone glow "orb" divs.
    const parseRadialGradientLayer = (layer) => {
      const m = String(layer || '').trim().match(/^radial-gradient\((.*)\)$/i);
      if (!m) return null;
      const parts = splitCssTopLevel(m[1]);
      if (parts.length < 2) return null;
      let cxPct = 50, cyPct = 50, rxPct = null, ryPct = null, shape = 'ellipse';
      let stopParts = parts;
      const first = parts[0].trim();
      const isColorFirst = /^(rgba?\(|hsla?\(|#|transparent\b)/i.test(first);
      const isConfig = !isColorFirst &&
        /(^|\s)(at|circle|ellipse|closest-side|closest-corner|farthest-side|farthest-corner)\b/i.test(first) ||
        (!isColorFirst && /^[\d.]+%\s+[\d.]+%/.test(first));
      if (isConfig) {
        stopParts = parts.slice(1);
        const atM = first.match(/at\s+([\d.]+)%\s+([\d.]+)%/i);
        if (atM) { cxPct = parseFloat(atM[1]); cyPct = parseFloat(atM[2]); }
        if (/\bcircle\b/i.test(first)) shape = 'circle';
        const sizeM = first.replace(/\bat\b.*$/i, '').match(/([\d.]+)%\s+([\d.]+)%/);
        if (sizeM) { rxPct = parseFloat(sizeM[1]); ryPct = parseFloat(sizeM[2]); }
      }
      const stops = stopParts.map((part, idx) => {
        const p = part.trim();
        const cm = p.match(/^(rgba?\([^)]*\)|hsla?\([^)]*\)|#[0-9a-fA-F]{3,8}|transparent|[a-zA-Z]+)\s*(.*)$/i);
        if (!cm) return null;
        const posM = cm[2].match(/(-?[\d.]+)%/);
        return {
          color: cm[1],
          pos: posM ? Math.max(0, Math.min(1, parseFloat(posM[1]) / 100)) : (stopParts.length === 1 ? 0 : idx / (stopParts.length - 1))
        };
      }).filter(Boolean);
      return stops.length >= 2 ? { type: 'radial', cxPct, cyPct, rxPct, ryPct, shape, stops } : null;
    };

    const isFullyTransparentCssColor = (colorStr) => {
      const c = String(colorStr || '').trim().toLowerCase();
      if (!c) return false;
      if (c === 'transparent') return true;
      const t = extractAlpha(c);
      return typeof t === 'number' && t >= 100;
    };

    const hasTextBackgroundClip = (computed) => {
      const clip = [
        computed.backgroundClip,
        computed.webkitBackgroundClip,
        computed.WebkitBackgroundClip
      ].filter(Boolean).join(' ').toLowerCase();
      return /\btext\b/.test(clip);
    };

    const pickGradientTextColor = (computed) => {
      const bgImage = computed.backgroundImage;
      if (!bgImage || bgImage === 'none') return null;
      const layers = splitCssTopLevel(bgImage)
        .map(parseLinearGradientLayer)
        .filter(Boolean);
      for (const layer of layers) {
        const visibleStops = layer.stops.filter(stop => {
          const t = extractAlpha(stop.color);
          return t === null || t < 100;
        });
        if (visibleStops.length === 0) continue;
        const picked = visibleStops.reduce((best, stop) =>
          Math.abs(stop.pos - 0.5) < Math.abs(best.pos - 0.5) ? stop : best
        );
        return rgbToHex(picked.color);
      }
      return null;
    };

    const findGradientTextColor = (computed, element = null) => {
      if (hasTextBackgroundClip(computed)) {
        const ownColor = pickGradientTextColor(computed);
        if (ownColor) return ownColor;
      }
      let cur = element ? element.parentElement : null;
      while (cur && cur !== document.body) {
        const curStyle = window.getComputedStyle(cur);
        if (hasTextBackgroundClip(curStyle)) {
          const inheritedColor = pickGradientTextColor(curStyle);
          if (inheritedColor) return inheritedColor;
        }
        cur = cur.parentElement;
      }
      return null;
    };

    const resolveTextPaintStyle = (computed, element = null) => {
      const fillColor = computed.webkitTextFillColor && computed.webkitTextFillColor !== 'currentcolor'
        ? computed.webkitTextFillColor
        : computed.color;
      const transparentTextPaint =
        isFullyTransparentCssColor(fillColor) ||
        isFullyTransparentCssColor(computed.color);

      if (transparentTextPaint) {
        const gradientColor = findGradientTextColor(computed, element);
        if (gradientColor) {
          return {
            color: gradientColor,
            transparency: computeTransparency(null, computed.opacity),
            _gradientTextFallback: true
          };
        }
      }

      return {
        color: rgbToHex(fillColor),
        transparency: computeTransparency(fillColor, computed.opacity),
        _gradientTextFallback: false
      };
    };

    const renderLinearGradientBackground = (bgImage, widthPx, heightPx) => {
      const layers = splitCssTopLevel(bgImage)
        .map(l => parseLinearGradientLayer(l) || parseRadialGradientLayer(l))
        .filter(Boolean);
      if (layers.length === 0 || widthPx <= 0 || heightPx <= 0) return null;
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(widthPx));
      canvas.height = Math.max(1, Math.round(heightPx));
      const ctx = canvas.getContext('2d');
      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      // CSS paints the first-listed layer on top, so draw in reverse (last first).
      for (const layer of layers.reverse()) {
        if (layer.type === 'radial') {
          const rcx = (layer.cxPct / 100) * canvas.width;
          const rcy = (layer.cyPct / 100) * canvas.height;
          // Default size (no explicit "<rx>% <ry>%") is farthest-corner: the
          // distance from the center to the furthest box corner. Using the box's
          // max dimension instead pushes the fade past the edges, so the glow
          // gets clipped into a boxy square (visible on the cover "orb" glows).
          const dx = Math.max(rcx, canvas.width - rcx);
          const dy = Math.max(rcy, canvas.height - rcy);
          const farCorner = Math.sqrt(dx * dx + dy * dy);
          let rx = layer.rxPct != null ? (layer.rxPct / 100) * canvas.width : farCorner;
          let ry = layer.ryPct != null ? (layer.ryPct / 100) * canvas.height : farCorner;
          rx = Math.max(1, rx); ry = Math.max(1, ry);
          ctx.save();
          ctx.translate(rcx, rcy);
          ctx.scale(1, ry / rx); // squash the circular gradient into an ellipse
          const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
          for (const stop of layer.stops) grad.addColorStop(Math.max(0, Math.min(1, stop.pos)), stop.color);
          ctx.fillStyle = grad;
          // Fill generously in the transformed space so the ellipse covers the box.
          ctx.fillRect(-canvas.width * 2, -canvas.height * 2, canvas.width * 4, canvas.height * 4);
          ctx.restore();
        } else {
          const rad = layer.angle * Math.PI / 180;
          const vx = Math.sin(rad);
          const vy = -Math.cos(rad);
          const len = Math.abs(canvas.width * vx) + Math.abs(canvas.height * vy) || Math.max(canvas.width, canvas.height);
          const grad = ctx.createLinearGradient(cx - vx * len / 2, cy - vy * len / 2, cx + vx * len / 2, cy + vy * len / 2);
          for (const stop of layer.stops) grad.addColorStop(stop.pos, stop.color);
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
      }
      return canvas.toDataURL('image/png');
    };

    const applyTextTransform = (text, textTransform) => {
      if (textTransform === 'uppercase') return text.toUpperCase();
      if (textTransform === 'lowercase') return text.toLowerCase();
      if (textTransform === 'capitalize') {
        return text.replace(/\b\w/g, c => c.toUpperCase());
      }
      return text;
    };

    const normalizeWhitespaceForPpt = (text, whiteSpace = 'normal') => {
      let out = String(text || '').replace(/\r\n?/g, '\n');
      if (whiteSpace === 'pre' || whiteSpace === 'pre-wrap' || whiteSpace === 'break-spaces') {
        return out;
      }
      if (whiteSpace === 'pre-line') {
        return out.replace(/[ \t\f\v]+/g, ' ');
      }
      return out.replace(/\s+/g, ' ');
    };

    // Extract rotation angle from CSS transform and writing-mode
    const getRotation = (transform, writingMode) => {
      let angle = 0;

      // Handle writing-mode first
      // PowerPoint: 90° = text rotated 90° clockwise (reads top to bottom, letters upright)
      // PowerPoint: 270° = text rotated 270° clockwise (reads bottom to top, letters upright)
      if (writingMode === 'vertical-rl') {
        // vertical-rl alone = text reads top to bottom = 90° in PowerPoint
        angle = 90;
      } else if (writingMode === 'vertical-lr') {
        // vertical-lr alone = text reads bottom to top = 270° in PowerPoint
        angle = 270;
      }

      // Then add any transform rotation
      if (transform && transform !== 'none') {
        // Try to match rotate() function
        const rotateMatch = transform.match(/rotate\((-?\d+(?:\.\d+)?)deg\)/);
        if (rotateMatch) {
          angle += parseFloat(rotateMatch[1]);
        } else {
          // Browser may compute as matrix - extract rotation from matrix
          const matrixMatch = transform.match(/matrix\(([^)]+)\)/);
          if (matrixMatch) {
            const values = matrixMatch[1].split(',').map(parseFloat);
            // matrix(a, b, c, d, e, f) where rotation = atan2(b, a)
            const matrixAngle = Math.atan2(values[1], values[0]) * (180 / Math.PI);
            angle += Math.round(matrixAngle);
          }
        }
      }

      // Normalize to 0-359 range
      angle = angle % 360;
      if (angle < 0) angle += 360;

      return angle === 0 ? null : angle;
    };

    // Get position/dimensions accounting for rotation
    const getPositionAndSize = (el, rect, rotation) => {
      if (rotation === null) {
        return { x: rect.left, y: rect.top, w: rect.width, h: rect.height };
      }

      // For 90° or 270° rotations, swap width and height
      // because PowerPoint applies rotation to the original (unrotated) box
      const isVertical = rotation === 90 || rotation === 270;

      if (isVertical) {
        // The browser shows us the rotated dimensions (tall box for vertical text)
        // But PowerPoint needs the pre-rotation dimensions (wide box that will be rotated)
        // So we swap: browser's height becomes PPT's width, browser's width becomes PPT's height
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        return {
          x: centerX - rect.height / 2,
          y: centerY - rect.width / 2,
          w: rect.height,
          h: rect.width
        };
      }

      // For other rotations, use element's offset dimensions
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      return {
        x: centerX - el.offsetWidth / 2,
        y: centerY - el.offsetHeight / 2,
        w: el.offsetWidth,
        h: el.offsetHeight
      };
    };

    // Parse CSS box-shadow into PptxGenJS shadow properties
    const parseBoxShadow = (boxShadow) => {
      if (!boxShadow || boxShadow === 'none') return null;

      // Browser computed style format: "rgba(0, 0, 0, 0.3) 2px 2px 8px 0px [inset]"
      // CSS format: "[inset] 2px 2px 8px 0px rgba(0, 0, 0, 0.3)"

      const insetMatch = boxShadow.match(/inset/);

      // IMPORTANT: PptxGenJS/PowerPoint doesn't properly support inset shadows
      // Only process outer shadows to avoid file corruption
      if (insetMatch) return null;

      // Extract color first (rgba or rgb at start)
      const colorMatch = boxShadow.match(/rgba?\([^)]+\)/);

      // Extract numeric values (handles both px and pt units)
      const parts = boxShadow.match(/([-\d.]+)(px|pt)/g);

      if (!parts || parts.length < 2) return null;

      const offsetX = parseFloat(parts[0]);
      const offsetY = parseFloat(parts[1]);
      const blur = parts.length > 2 ? parseFloat(parts[2]) : 0;

      // Calculate angle from offsets (in degrees, 0 = right, 90 = down)
      let angle = 0;
      if (offsetX !== 0 || offsetY !== 0) {
        angle = Math.atan2(offsetY, offsetX) * (180 / Math.PI);
        if (angle < 0) angle += 360;
      }

      // Calculate offset distance (hypotenuse)
      const offset = Math.sqrt(offsetX * offsetX + offsetY * offsetY) * PT_PER_PX;

      // Extract opacity from rgba/hsla. PptxGenJS expects 0..1 opacity, not 0..100.
      let opacity = 0.5;
      if (colorMatch) {
        const colorTransparency = extractAlpha(colorMatch[0]);
        if (colorTransparency !== null) {
          opacity = (100 - colorTransparency) / 100;
        }
      }

      return {
        type: 'outer',
        angle: Math.round(angle),
        blur: blur * 0.75, // Convert to points
        color: colorMatch ? rgbToHex(colorMatch[0]) : '000000',
        offset: offset,
        opacity
      };
    };

    // Parse inline formatting tags (<b>, <i>, <u>, <strong>, <em>, <span>) into text runs
    const parseInlineFormatting = (element, baseOptions = {}, runs = [], baseTextTransform = (x) => x) => {
      let prevNodeIsText = false;
      const elementWhiteSpace = window.getComputedStyle(element).whiteSpace;

      element.childNodes.forEach((node) => {
        let textTransform = baseTextTransform;

        const isText = node.nodeType === Node.TEXT_NODE || node.tagName === 'BR';
        if (isText) {
          const text = node.tagName === 'BR' ? '\n' : textTransform(normalizeWhitespaceForPpt(node.textContent, elementWhiteSpace));
          appendTextRuns(runs, text, baseOptions);

        } else if (node.nodeType === Node.ELEMENT_NODE && node.textContent.trim()) {
          // Icon element appearing inline inside a text container — emit mapped
          // glyph with a symbol-capable font instead of the raw ligature name.
          if (node._isIcon) {
            const iconComputed = window.getComputedStyle(node);
            runs.push({
              text: node._iconGlyph,
              options: {
                ...baseOptions,
                fontFace: 'Segoe UI Symbol',
                color: rgbToHex(iconComputed.color),
                _isIcon: true
              }
            });
            prevNodeIsText = false;
            return;
          }
          const options = { ...baseOptions };
          const computed = window.getComputedStyle(node);

          // Handle inline elements with computed styles
          const tag = node.tagName;
          if (tag === 'SPAN' || tag === 'B' || tag === 'STRONG' || tag === 'I' || tag === 'EM' || tag === 'U' ||
              tag === 'A' || tag === 'SUB' || tag === 'SUP' || tag === 'S' || tag === 'DEL' || tag === 'STRIKE' ||
              tag === 'MARK' || tag === 'CODE' || tag === 'SMALL' || tag === 'BIG' || tag === 'CITE' || tag === 'ABBR' ||
              tag === 'TIME' || tag === 'LABEL') {
            // If this inline-tag has been promoted to block-display via CSS
            // (e.g. <h1>看见<span class="accent" style="display:block">无家可归者</span></h1>
            // where `.accent { display:block }` puts the span on its own
            // visual line), insert a newline so the run starts on a new
            // paragraph line in PowerPoint instead of continuing inline.
            const dispMode = computed.display;
            const parentComputed = node.parentElement ? window.getComputedStyle(node.parentElement) : null;
            const parentIsRowFlex = parentComputed &&
              (parentComputed.display === 'flex' || parentComputed.display === 'inline-flex') &&
              !String(parentComputed.flexDirection || 'row').startsWith('column');
            const isBlockSpan = !parentIsRowFlex &&
              (dispMode === 'block' || dispMode === 'flex' || dispMode === 'grid' || dispMode === 'list-item');
            if (isBlockSpan) {
              const prevRun = runs[runs.length - 1];
              if (prevRun && !/\n$/.test(prevRun.text)) {
                prevRun.text += '\n';
              } else if (!prevRun) {
                // Span is the first child — no leading newline needed.
              }
            }
            const isBold = shouldApplyPptBold(computed.fontWeight);
            if (isBold && !shouldSkipBold(computed.fontFamily)) options.bold = true;
            if (computed.fontStyle === 'italic') options.italic = true;
            if (computed.textDecoration && computed.textDecoration.includes('underline')) options.underline = true;
            // line-through (DEL/S/STRIKE or any element with text-decoration:line-through)
            if (tag === 'S' || tag === 'DEL' || tag === 'STRIKE' ||
                (computed.textDecoration && computed.textDecoration.includes('line-through'))) {
              options.strike = true;
            }
            // Hyperlink — preserve URL & tooltip on the run
            if (tag === 'A' && node.href) {
              options.hyperlink = { url: node.href };
              if (node.title) options.hyperlink.tooltip = node.title;
            }
            // Subscript / superscript — pptxgenjs supports {subscript: true} / {superscript: true}
            if (tag === 'SUB') options.subscript = true;
            if (tag === 'SUP') options.superscript = true;
            // Keep inline runs on the same resolved font as the browser-computed span.
            // Without this, PowerPoint may substitute a wider default font at run boundaries.
            if (computed.fontFamily) options.fontFace = mapFontFace(computed.fontFamily, node.textContent);
            // <code> — use a monospace stand-in font.
            if (tag === 'CODE') options.fontFace = 'Courier New';
            // Inline background highlight: <mark> and styled spans like .mark.
            const inlineBg = computed.backgroundColor;
            const hasInlineBg = inlineBg && inlineBg !== 'rgba(0, 0, 0, 0)' && inlineBg !== 'transparent';
            if (tag === 'MARK' || hasInlineBg) {
              options.highlight = hasInlineBg ? rgbToHex(inlineBg) : 'FFFF00';
            }
            const inlineTextPaint = resolveTextPaintStyle(computed, node);
            if ((computed.color && computed.color !== 'rgb(0, 0, 0)') || inlineTextPaint._gradientTextFallback) {
              options.color = inlineTextPaint.color;
            }
            // Combine color alpha + element opacity into a single per-run transparency.
            // For CSS gradient text, transparent glyph paint is replaced with a
            // representative solid color, so only element opacity applies.
            if (inlineTextPaint.transparency !== null) options.transparency = inlineTextPaint.transparency;
            if (computed.fontSize) options.fontSize = pxToFontSize(computed.fontSize, node.textContent);
            if (computed.letterSpacing && computed.letterSpacing !== "normal") options.charSpacing = pxToPoints(computed.letterSpacing);
            if (isMediumOrBold(computed.fontWeight) && shouldUseEmphasisFont(node.textContent)) options.fontFace = _fc.emphasis || "Liberation Sans Narrow";

            // Apply text-transform on the span element itself
            if (computed.textTransform && computed.textTransform !== 'none') {
              const transformStr = computed.textTransform;
              textTransform = (text) => applyTextTransform(text, transformStr);
            }

            // <sub>/<sup>/<small>/<big>: leaf-style — emit text directly with run options
            if (tag === 'SUB' || tag === 'SUP' || tag === 'SMALL' || tag === 'BIG' || tag === 'A') {
              // Flatten any nested formatting inside an <a>: process children with current options
              if (node.childNodes.length > 0 && (tag === 'A' || tag === 'SMALL' || tag === 'BIG')) {
                parseInlineFormatting(node, options, runs, textTransform);
              } else {
                const txt = textTransform(normalizeWhitespaceForPpt(node.textContent, computed.whiteSpace));
                if (txt.trim()) appendTextRuns(runs, txt, options);
              }
            } else {
              // Recursively process the child node — flatten nested spans into multiple runs.
              parseInlineFormatting(node, options, runs, textTransform);
            }
            // If this span was promoted to block-display, append a trailing
            // newline so any following sibling text/spans start on a fresh line.
            if (isBlockSpan) {
              const lastRun = runs[runs.length - 1];
              if (lastRun && !/\n$/.test(lastRun.text)) lastRun.text += '\n';
              prevNodeIsText = false;
            } else if (parentIsRowFlex && node.nextSibling && node.nextSibling.textContent.trim()) {
              const lastRun = runs[runs.length - 1];
              if (lastRun && !/\s$/.test(lastRun.text)) appendTextRuns(runs, ' ', baseOptions);
            }
          } else {
            // Unknown inline element (e.g. <a>, <code>, <sub>, <sup>, <mark>) —
            // extract its text content as plain text to avoid silent data loss.
            const text = textTransform(normalizeWhitespaceForPpt(node.textContent, computed.whiteSpace));
            if (text.trim()) runs.push({ text, options: { ...baseOptions } });
          }
        }

        prevNodeIsText = isText;
      });

      // Trim leading space from first run and trailing space from last run
      if (runs.length > 0) {
        runs[0].text = runs[0].text.replace(/^\s+/, '');
        runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, '');
      }

      // Collapse whitespace around explicit line breaks. Source HTML like
      //   <h1>foo<br>\n  <span>bar</span></h1>
      // produces runs ["foo\n ", "bar"] — pptxgenjs splits on '\n' and the
      // standalone " " becomes a visible blank paragraph between "foo" and
      // "bar". Strip whitespace immediately before/after each '\n' so we get
      // a clean two-line layout. Also trim leading whitespace from a run when
      // the previous run ends with '\n'.
      for (const run of runs) {
        run.text = run.text.replace(/[ \t]+\n/g, '\n').replace(/\n[ \t]+/g, '\n');
      }
      for (let i = 1; i < runs.length; i++) {
        if (runs[i - 1].text.endsWith('\n')) {
          runs[i].text = runs[i].text.replace(/^[ \t]+/, '');
        }
      }

      // PptxGenJS splits rich-text runs containing \n by marking every
      // resulting segment as breakLine, so a run like "line1\nline2" followed by
      // a styled span incorrectly puts the span into a new paragraph. Convert
      // explicit line breaks to breakLine on the preceding run ourselves.
      const expandedRuns = [];
      for (const run of runs) {
        const parts = String(run.text || '').split('\n');
        parts.forEach((part, idx) => {
          if (idx > 0 && expandedRuns.length > 0) {
            expandedRuns[expandedRuns.length - 1].options = {
              ...expandedRuns[expandedRuns.length - 1].options,
              breakLine: true
            };
          }
          if (part.length > 0) {
            expandedRuns.push({ text: part, options: { ...run.options } });
          }
        });
      }

      return expandedRuns.filter(r => r.text.length > 0);
    };

    // Extract background from the actual slide canvas, not the presentation body/chrome.
    const body = document.body;
    const canvasStyle = window.getComputedStyle(slideRoot || body);
    const bgImage = canvasStyle.backgroundImage;
    const bgColor = canvasStyle.backgroundColor;

    // Collect validation errors
    const errors = [];
    // Collect non-blocking warnings (browser scope)
    const warnings = [];

    const extractNotesText = (noteEl) => {
      const items = Array.from(noteEl.querySelectorAll('li'))
        .map(li => normalizeWhitespaceForPpt(li.textContent, 'normal').trim())
        .filter(Boolean);
      if (items.length > 0) return items.map(t => '- ' + t).join('\n');
      return normalizeWhitespaceForPpt(noteEl.textContent, 'pre-line').trim();
    };
    const noteElements = Array.from(document.querySelectorAll('[data-notes]'));
    const notes = noteElements
      .map(extractNotesText)
      .filter(Boolean)
      .join('\n');
    // Notes are speaker metadata, not slide artwork. Remove them after extraction
    // so later element collection never renders them into the visible slide.
    noteElements.forEach(noteEl => noteEl.remove());

    let background;
    if (bgImage && bgImage !== 'none') {
      // Extract URL from url("...") or url(...)
      const urlMatch = bgImage.match(/url\(["']?([^"')]+)["']?\)/);
      if (urlMatch) {
        background = {
          type: 'image',
          path: urlMatch[1]
        };
      } else {
        // Not a url() — this is a CSS gradient (linear/radial mesh) used as the
        // slide canvas background (e.g. multi_3 cover `.cover-bg` grad-mesh).
        // Rasterize it to a PNG so the full colour transition survives; the flat
        // bgColor is kept only as a fallback if the raster fails.
        const canvasGrad = renderLinearGradientBackground(bgImage, bodyWPx, bodyHPx);
        if (canvasGrad) {
          background = {
            type: 'image',
            dataUrl: canvasGrad,
            fallbackColor: rgbToHex(bgColor)
          };
        } else {
          background = {
            type: 'color',
            value: rgbToHex(bgColor)
          };
        }
      }
    } else {
      background = {
        type: 'color',
        value: rgbToHex(bgColor)
      };
    }

    // Process all elements
    const elements = [];
    const placeholders = [];
    const textTags = ['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'UL', 'OL', 'LI'];
    // Block container elements treated identically to DIV (background → shape, unwrapped text → error)
    const blockContainerTags = new Set(['DIV', 'SECTION', 'HEADER', 'FOOTER', 'ARTICLE', 'ASIDE', 'MAIN', 'NAV', 'FIGURE']);
    // Inline elements that LLMs sometimes use as standalone block text containers
    const inlineAsBlockTags = new Set(['SPAN', 'STRONG', 'B', 'EM', 'I', 'A', 'LABEL', 'CODE', 'MARK', 'TIME', 'CITE', 'ABBR', 'S', 'U']);
    // Block elements that are text-leaf-ish (rarely contain P/H* children)
    const leafBlockTags = new Set(['FIGCAPTION', 'DT', 'DD', 'CAPTION', 'BLOCKQUOTE', 'TD', 'TH', 'SUMMARY']);
    const processed = new Set();

    // (box-sizing: border-box is already applied at the top of extractSlideData.)

    // ── Icon-font handling ──
    // <i class="material-icons">spa</i> etc. use a webfont to render icon glyphs.
    // In PPT we cannot embed those fonts, so the raw ligature name ("spa") would
    // render as literal text. Map known names to Unicode equivalents and treat as
    // a short symbol run with a PPT-safe font.
    // Material Icons → Unicode glyph map.
    // Strongly prefer single-codepoint BMP symbols (Geometric Shapes, Dingbats,
    // Misc Symbols, Arrows blocks) — they render in nearly every PPT-safe font
    // and produce the clean monochrome look of Material Icons. Multi-codepoint
    // emoji are a last resort for concepts (people, megaphone, plant) with no
    // BMP equivalent. The icon font is set to a symbol font (Segoe UI Symbol)
    // so even emoji codepoints render as monochrome glyphs in PowerPoint.
    const MATERIAL_ICON_MAP = {
      // Search / view / visibility
      search: '⌕', visibility: '◉', visibility_off: '⊘', preview: '◉',
      pageview: '⌕', find_in_page: '⌕', zoom_in: '⊕', zoom_out: '⊖',
      // People / community
      person: '☻', person_outline: '☺', people: '♟', people_outline: '♟',
      group: '♟', groups: '♟', group_add: '♟', person_add: '☻',
      family_restroom: '♟', diversity_1: '♟', diversity_3: '♟',
      account_circle: '◉', supervised_user_circle: '◉', face: '☻',
      handshake: '✻', volunteer_activism: '♥', favorite_border: '♡',
      favorite: '♥', loyalty: '♥',
      // Communication
      campaign: '◖', record_voice_over: '◖', voice_chat: '◖',
      mail: '✉', email: '✉', drafts: '✉', mark_email_read: '✉',
      mark_email_unread: '✉', forward_to_inbox: '✉', send: '➤',
      phone: '☎', call: '☎', call_end: '☎', dialpad: '⌨',
      chat: '◌', chat_bubble: '◌', chat_bubble_outline: '◌',
      forum: '◌', sms: '◌', comment: '◌', message: '◌',
      question_answer: '◌', notifications: '◔', notifications_active: '◔',
      // Actions / status
      check: '✓', check_circle: '✓', check_circle_outline: '✓',
      done: '✓', done_all: '✓', done_outline: '✓', verified: '✓',
      task_alt: '✓', fact_check: '✓', playlist_add_check: '✓',
      close: '✕', cancel: '✕', highlight_off: '✕', block: '⊘', do_not_disturb: '⊘',
      add: '＋', add_circle: '⊕', add_circle_outline: '⊕', remove: '−',
      remove_circle: '⊖', remove_circle_outline: '⊖',
      edit: '✎', mode_edit: '✎', create: '✎', draw: '✎', border_color: '✎',
      delete: '✕', delete_outline: '✕', delete_forever: '✕',
      refresh: '↻', sync: '↻', autorenew: '↻', cached: '↻', update: '↻',
      restore: '↺', undo: '↶', redo: '↷',
      info: 'ⓘ', info_outline: 'ⓘ', warning: '⚠', warning_amber: '⚠',
      error: '⊗', error_outline: '⊗', report: '⚠', report_problem: '⚠',
      help: '?', help_outline: '?', help_center: '?', live_help: '?',
      question_mark: '?', priority_high: '!',
      // Arrows / navigation
      arrow_forward: '→', arrow_back: '←', arrow_upward: '↑', arrow_downward: '↓',
      arrow_forward_ios: '›', arrow_back_ios: '‹',
      chevron_right: '›', chevron_left: '‹',
      navigate_next: '›', navigate_before: '‹',
      keyboard_arrow_right: '›', keyboard_arrow_left: '‹',
      keyboard_arrow_up: '▲', keyboard_arrow_down: '▼',
      expand_more: '▼', expand_less: '▲',
      arrow_drop_down: '▼', arrow_drop_up: '▲',
      arrow_right: '▶', arrow_left: '◀',
      play_arrow: '▶', pause: '⏸', stop: '■', skip_next: '⏭', skip_previous: '⏮',
      fast_forward: '⏩', fast_rewind: '⏪',
      first_page: '⇤', last_page: '⇥',
      north: '↑', south: '↓', east: '→', west: '←',
      north_east: '↗', north_west: '↖', south_east: '↘', south_west: '↙',
      swap_horiz: '⇄', swap_vert: '⇅', sort: '⇅', sort_by_alpha: '⇅',
      compare_arrows: '⇄', sync_alt: '⇄', import_export: '⇅',
      // Menu / list
      menu: '☰', menu_open: '☰', filter_list: '☰', tune: '⚙', sort: '⇅',
      view_list: '☰', view_module: '▦', view_quilt: '▦', view_comfy: '▦',
      grid_view: '▦', dashboard: '▦', apps: '▦', widgets: '▦',
      more_horiz: '⋯', more_vert: '⋮', drag_handle: '☰', drag_indicator: '⋮',
      // Files / docs
      folder: '▣', folder_open: '▣', folder_shared: '▣', create_new_folder: '▣',
      file_copy: '⎘', content_copy: '⎘', content_paste: '⎘', content_cut: '✂',
      attach_file: '⫶', attachment: '⫶', upload_file: '↑', cloud_upload: '↑',
      cloud_download: '↓', download: '↓', download_for_offline: '↓',
      file_download: '↓', file_upload: '↑', save: '⤓', save_alt: '⤓',
      description: '▤', article: '▤', text_snippet: '▤', notes: '▤',
      assignment: '▤', list_alt: '▤', receipt: '▤', receipt_long: '▤',
      book: '▤', menu_book: '▤', auto_stories: '▤', import_contacts: '▤',
      bookmark: '❏', bookmark_border: '❏', bookmarks: '❏', collections_bookmark: '❏',
      flag: '⚑', outlined_flag: '⚐', tour: '⚑',
      tag: '#', label: '⌧', label_outline: '⌧', new_releases: '✦',
      print: '⎙', share: '↗', launch: '↗', open_in_new: '↗', link: '⌘',
      // Settings / tools
      settings: '⚙', settings_applications: '⚙', settings_suggest: '⚙',
      build: '⚒', build_circle: '⚒', construction: '⚒', engineering: '⚒',
      handyman: '⚒', home_repair_service: '⚒',
      // Security
      lock: '⚿', lock_outline: '⚿', lock_open: '◯', no_encryption: '◯',
      enhanced_encryption: '⚿', vpn_key: '⚿', security: '⛨', shield: '⛨',
      verified_user: '⛨', gpp_good: '⛨', admin_panel_settings: '⛨',
      privacy_tip: 'ⓘ', policy: '▤', gavel: '⚖', balance: '⚖',
      // Stars / awards / highlights
      star: '★', star_border: '☆', star_half: '⯨', star_outline: '☆',
      grade: '★', stars: '★', auto_awesome: '✦', auto_awesome_motion: '✦',
      tips_and_updates: '◆', insights: '◆', lightbulb: '◆', lightbulb_outline: '◇',
      whatshot: '✦', local_fire_department: '✦', emoji_events: '♛', trophy: '♛',
      military_tech: '✦', workspace_premium: '♛', diamond: '◆',
      celebration: '✦', sparkles: '✦', new_releases: '✦',
      thumb_up: '👍', thumb_down: '👎', recommend: '👍',
      // Charts / data
      trending_up: '↗', trending_down: '↘', trending_flat: '→',
      show_chart: '⌇', timeline: '⌇', stacked_line_chart: '⌇',
      bar_chart: '▦', equalizer: '▤', leaderboard: '▦',
      pie_chart: '◐', donut_large: '◐', donut_small: '◑',
      analytics: '▦', monitoring: '⌇', query_stats: '⌇',
      data_usage: '◐', insights: '◆', poll: '▦',
      // Time / calendar
      access_time: '◔', schedule: '◔', timer: '◔', timelapse: '◔',
      hourglass_top: '⧗', hourglass_bottom: '⧗', hourglass_empty: '⧖',
      alarm: '◔', alarm_on: '◔', snooze: '◔', av_timer: '◔', watch_later: '◔',
      calendar_today: '▦', calendar_month: '▦', date_range: '▦',
      event: '▦', event_available: '▦', event_note: '▦', today: '▦',
      // Money / commerce
      attach_money: '$', monetization_on: '$', payments: '$', paid: '$',
      account_balance: '🏛', account_balance_wallet: '◫', savings: '◫', wallet: '◫',
      credit_card: '▭', payment: '▭', local_atm: '$',
      shopping_cart: '🛒', shopping_bag: '🛍', shopping_basket: '🛒',
      add_shopping_cart: '🛒', store: '🏪', storefront: '🏪',
      local_offer: '⌧', sell: '⌧', loyalty: '♥',
      // Tech / device
      computer: '▢', desktop_windows: '▢', laptop: '▢', laptop_mac: '▢',
      phone_iphone: '▯', smartphone: '▯', tablet: '▭', tablet_mac: '▭',
      tv: '▭', cast: '▱', headphones: '◯',
      keyboard: '⌨', keyboard_alt: '⌨', mouse: '◯',
      memory: '▦', sd_storage: '▦', storage: '▦', dns: '▦',
      cloud: '☁', cloud_done: '☁', cloud_off: '☁', wb_cloudy: '☁',
      wifi: '◌', wifi_off: '◌', signal_cellular_alt: '⌇', router: '◌',
      bluetooth: 'ᛒ', bluetooth_connected: 'ᛒ',
      battery_full: '▮', battery_charging_full: '▮',
      power: '⚡', flash_on: '⚡', bolt: '⚡', power_settings_new: '⏻',
      // Media
      photo: '▣', image: '▣', collections: '▣', camera_alt: '◉', photo_camera: '◉',
      videocam: '▶', movie: '▶', play_circle: '▶', play_circle_outline: '▶',
      mic: '◖', mic_off: '◖', music_note: '♪', library_music: '♪', queue_music: '♪',
      headphones: '◯', volume_up: '◀', volume_off: '◀', volume_mute: '◀',
      audiotrack: '♪', album: '◯', radio: '◯',
      // Location / map / travel
      my_location: '◎', location_on: '◎', location_pin: '◎', place: '◎',
      pin_drop: '◎', room: '◎', not_listed_location: '◎',
      map: '▣', explore: '✦', navigation: '➤', near_me: '➤',
      directions: '➤', directions_car: '⊟', directions_walk: '⫯',
      directions_run: '⫯', hiking: '△', directions_bike: '⊕', directions_bus: '⊟',
      directions_subway: '⊟', directions_train: '⊟', directions_boat: '⊟',
      directions_transit: '⊟', flight: '✈', flight_takeoff: '✈',
      flight_land: '✈', train: '⊟', tram: '⊟', subway: '⊟',
      local_taxi: '⊟', local_shipping: '⊟', local_parking: 'P',
      local_gas_station: '⛽', ev_station: '⚡',
      // Home / building
      home: '⌂', house: '⌂', home_filled: '⌂', cottage: '⌂',
      apartment: '▥', business: '▥', business_center: '▥', domain: '▥',
      hotel: '▥', meeting_room: '▥', other_houses: '⌂',
      maps_home_work: '▥', corporate_fare: '▥',
      // Education / work
      school: '▿', menu_book: '▤', auto_stories: '▤',
      cast_for_education: '▿', psychology: '◯', science: '⚗', biotech: '⚗',
      work: '▭', work_outline: '▭', business_center: '▭',
      // Health / nature
      medical_services: '✚', local_hospital: '✚', healing: '✚',
      medication: '◯', vaccines: '✚', monitor_heart: '♥', favorite: '♥',
      eco: '✿', local_florist: '✿', spa: '✿', park: '✿',
      nature: '✿', forest: '✿', grass: '✿', water_drop: '◐',
      pets: '◯',
      restaurant: '⊕', restaurant_menu: '⊕', local_dining: '⊕',
      local_cafe: '◯', coffee: '◯', local_drink: '◯', wine_bar: '◯',
      // Weather
      wb_sunny: '☀', sunny: '☀', wb_twighlight: '☀',
      brightness_high: '☀', brightness_low: '☾', dark_mode: '☾',
      light_mode: '☀', nightlight: '☾', bedtime: '☾',
      cloud: '☁', wb_cloudy: '☁', cloudy_snowing: '☁',
      thunderstorm: '⚡', umbrella: '☂', beach_access: '☂', ac_unit: '❄',
      water: '◐', waves: '〜', terrain: '△',
      // Misc / objects
      inventory: '▣', inventory_2: '▣', category: '▣',
      backpack: '▣', luggage: '▣', shopping_bag: '▣',
      key: '⚿', vpn_key: '⚿', emoji_objects: '◆',
      gavel: '⚖', balance: '⚖', policy: '▤', rule: '▤',
      kitchen: '▤', dining: '⊕', fitness_center: '▣', sports_kabaddi: '♟',
      pet_supplies: '◯', auto_awesome: '✦',
      gif: '▣', emoji_emotions: '☻', sentiment_satisfied: '☻',
      sentiment_dissatisfied: '☹', sentiment_very_satisfied: '☻',
      sentiment_very_dissatisfied: '☹', mood: '☻', mood_bad: '☹',
      // Globe / language
      language: '◯', public: '◯', translate: '⇄', g_translate: '⇄',
      // Misc symbols
      rocket_launch: '➤', rocket: '➤',
    };

    // Font Awesome icon class → Unicode glyph map.
    // Key is the part AFTER `fa-` (e.g. for `<i class="fas fa-user">`, key is 'user').
    // Reuses the Material map's well-tested glyphs.
    const FA_ICON_MAP = {
      // people
      'user': '☻', 'users': '♟', 'user-circle': '◉', 'user-friends': '♟',
      'user-plus': '☻', 'user-tie': '☻', 'address-book': '▤', 'id-card': '▭',
      'people-group': '♟', 'people-arrows': '♟', 'people-line': '♟',
      'face-smile': '☻', 'face-frown': '☹',
      // actions
      'check': '✓', 'check-circle': '✓', 'check-square': '✓', 'check-double': '✓',
      'circle-check': '✓', 'square-check': '✓',
      'xmark': '✕', 'times': '✕', 'times-circle': '✕', 'circle-xmark': '✕',
      'ban': '⊘', 'minus': '−', 'minus-circle': '⊖', 'circle-minus': '⊖',
      'plus': '＋', 'plus-circle': '⊕', 'circle-plus': '⊕',
      'pen': '✎', 'pencil': '✎', 'pen-to-square': '✎', 'edit': '✎',
      'trash': '✕', 'trash-can': '✕', 'trash-alt': '✕',
      'rotate': '↻', 'rotate-right': '↻', 'rotate-left': '↺',
      'arrows-rotate': '↻', 'sync': '↻', 'redo': '↷', 'undo': '↶',
      // alerts
      'info': 'ⓘ', 'info-circle': 'ⓘ', 'circle-info': 'ⓘ',
      'triangle-exclamation': '⚠', 'exclamation-triangle': '⚠',
      'circle-exclamation': '⊗', 'exclamation-circle': '⊗',
      'question': '?', 'question-circle': '?', 'circle-question': '?',
      // arrows / nav
      'arrow-right': '→', 'arrow-left': '←', 'arrow-up': '↑', 'arrow-down': '↓',
      'arrow-up-right': '↗', 'arrow-up-long': '↑',
      'angle-right': '›', 'angle-left': '‹', 'angle-up': '▲', 'angle-down': '▼',
      'angles-right': '»', 'angles-left': '«',
      'chevron-right': '›', 'chevron-left': '‹',
      'chevron-up': '▲', 'chevron-down': '▼',
      'caret-right': '▶', 'caret-left': '◀', 'caret-up': '▲', 'caret-down': '▼',
      'arrow-trend-up': '↗', 'arrow-trend-down': '↘',
      'arrow-right-arrow-left': '⇄', 'arrows-left-right': '⇄',
      'arrows-up-down': '⇅',
      'play': '▶', 'pause': '⏸', 'stop': '■', 'forward': '⏩', 'backward': '⏪',
      'forward-step': '⏭', 'backward-step': '⏮',
      // menu / list
      'bars': '☰', 'list': '☰', 'list-ul': '☰', 'list-ol': '☰',
      'th': '▦', 'th-large': '▦', 'border-all': '▦', 'table-cells': '▦',
      'ellipsis': '⋯', 'ellipsis-vertical': '⋮',
      'filter': '☰', 'sliders': '☰',
      // files
      'folder': '▣', 'folder-open': '▣', 'folder-plus': '▣',
      'file': '▤', 'file-lines': '▤', 'file-alt': '▤', 'file-pdf': '▤',
      'file-word': '▤', 'file-excel': '▤', 'file-powerpoint': '▤',
      'file-image': '▣', 'file-video': '▶', 'file-audio': '♪',
      'copy': '⎘', 'paste': '⎘', 'cut': '✂', 'scissors': '✂',
      'paperclip': '⫶', 'link': '⌘', 'unlink': '⌘',
      'upload': '↑', 'download': '↓', 'cloud-upload': '↑', 'cloud-download': '↓',
      'cloud-arrow-up': '↑', 'cloud-arrow-down': '↓',
      'save': '⤓', 'floppy-disk': '⤓',
      'book': '▤', 'book-open': '▤', 'bookmark': '❏',
      'flag': '⚑', 'tag': '#', 'tags': '#',
      'print': '⎙', 'share': '↗', 'share-nodes': '↗', 'up-right-from-square': '↗',
      // settings
      'gear': '⚙', 'cog': '⚙', 'gears': '⚙', 'cogs': '⚙', 'wrench': '⚒',
      'screwdriver-wrench': '⚒', 'tools': '⚒', 'hammer': '⚒',
      // security
      'lock': '⚿', 'lock-open': '◯', 'unlock': '◯', 'key': '⚿',
      'shield': '⛨', 'shield-halved': '⛨', 'shield-alt': '⛨',
      'user-shield': '⛨', 'user-lock': '⚿',
      // stars / awards
      'star': '★', 'star-half': '⯨', 'star-of-life': '✦',
      'award': '♛', 'trophy': '♛', 'crown': '♛', 'medal': '✦',
      'gem': '◆', 'diamond': '◆',
      'fire': '✦', 'lightbulb': '◆', 'wand-magic-sparkles': '✦',
      'heart': '♥', 'heart-circle-check': '♥',
      'thumbs-up': '👍', 'thumbs-down': '👎',
      // charts / data
      'chart-line': '⌇', 'chart-bar': '▦', 'chart-column': '▦',
      'chart-pie': '◐', 'chart-area': '⌇', 'chart-simple': '▦',
      'arrow-up-right-dots': '↗', 'magnifying-glass-chart': '▦',
      // time
      'clock': '◔', 'clock-rotate-left': '↺', 'stopwatch': '◔',
      'hourglass': '⧗', 'hourglass-half': '⧗', 'hourglass-end': '⧗',
      'calendar': '▦', 'calendar-days': '▦', 'calendar-check': '▦',
      // money
      'dollar-sign': '$', 'euro-sign': '€', 'yen-sign': '¥', 'pound-sign': '£',
      'money-bill': '$', 'money-bill-wave': '$', 'sack-dollar': '$',
      'wallet': '◫', 'piggy-bank': '◫',
      'credit-card': '▭', 'cart-shopping': '🛒', 'shopping-cart': '🛒',
      'bag-shopping': '🛍', 'shopping-bag': '🛍', 'store': '🏪',
      // tech
      'desktop': '▢', 'laptop': '▢', 'computer': '▢', 'display': '▢',
      'mobile': '▯', 'mobile-screen': '▯', 'tablet': '▭',
      'keyboard': '⌨', 'mouse': '◯', 'headphones': '◯',
      'database': '▦', 'server': '▦', 'hard-drive': '▦', 'microchip': '▦',
      'cloud': '☁', 'wifi': '◌', 'signal': '⌇', 'tower-broadcast': '⌇',
      'bluetooth': 'ᛒ', 'battery-full': '▮', 'plug': '⚡', 'bolt': '⚡',
      // media
      'image': '▣', 'images': '▣', 'photo-film': '▣',
      'camera': '◉', 'camera-retro': '◉', 'video': '▶', 'film': '▶',
      'circle-play': '▶', 'play-circle': '▶',
      'microphone': '◖', 'mic': '◖', 'music': '♪', 'headphones-simple': '◯',
      'volume-high': '◀', 'volume-low': '◀', 'volume-xmark': '◀', 'volume-off': '◀',
      // location
      'location-dot': '◎', 'map-marker': '◎', 'map-marker-alt': '◎',
      'map-pin': '◎', 'map': '▣', 'compass': '✦',
      'paper-plane': '➤', 'plane': '✈', 'plane-departure': '✈', 'plane-arrival': '✈',
      'car': '⊟', 'bus': '⊟', 'train': '⊟', 'truck': '⊟', 'taxi': '⊟',
      'bicycle': '⊕', 'person-walking': '⫯', 'person-running': '⫯',
      'gas-pump': '⛽', 'charging-station': '⚡',
      // home / building
      'house': '⌂', 'home': '⌂', 'house-chimney': '⌂',
      'building': '▥', 'city': '▥', 'industry': '▥', 'hotel': '▥', 'school': '▿',
      // education / science
      'graduation-cap': '▿', 'book-open-reader': '▤', 'brain': '◯',
      'flask': '⚗', 'vial': '⚗', 'atom': '⚛', 'dna': '⚗', 'microscope': '⚗',
      'briefcase': '▭',
      // health / nature
      'plus-square': '✚', 'square-plus': '✚', 'hospital': '✚',
      'stethoscope': '✚', 'heart-pulse': '♥', 'pills': '◯', 'syringe': '✚',
      'leaf': '✿', 'seedling': '✿', 'tree': '✿', 'spa': '✿',
      'water': '◐', 'droplet': '◐', 'snowflake': '❄',
      // weather
      'sun': '☀', 'moon': '☾', 'cloud-sun': '☁', 'cloud-moon': '☁',
      'cloud-rain': '☁', 'cloud-bolt': '⚡', 'umbrella': '☂',
      'temperature-high': '☀', 'temperature-low': '☾',
      // communication
      'envelope': '✉', 'envelope-open': '✉', 'at': '@',
      'phone': '☎', 'phone-volume': '☎', 'mobile-button': '▯',
      'message': '◌', 'comment': '◌', 'comments': '◌',
      'comment-dots': '◌', 'bullhorn': '◖', 'microphone-lines': '◖',
      'bell': '◔', 'bell-slash': '◔',
      'paper-plane-top': '➤',
      // misc
      'globe': '◯', 'earth-americas': '◯', 'earth-europe': '◯', 'earth-asia': '◯',
      'rocket': '➤', 'magnifying-glass': '⌕', 'search': '⌕',
      'eye': '◉', 'eye-slash': '⊘',
      'gift': '◆', 'cake-candles': '◆', 'wand-sparkles': '✦',
      'arrow-pointer': '➤', 'hand': '✋', 'hand-pointer': '☞',
      'circle': '●', 'circle-dot': '◉', 'square': '▢', 'square-full': '▢',
      'asterisk': '✦', 'hashtag': '#',
      'quote-left': '“', 'quote-right': '”',
    };

    // Bootstrap Icons class → Unicode glyph map.
    // Key is the part AFTER `bi-` (e.g. for `<i class="bi bi-check">`, key is 'check').
    const BI_ICON_MAP = {
      'check': '✓', 'check2': '✓', 'check-circle': '✓', 'check2-circle': '✓',
      'check-square': '✓', 'check-all': '✓',
      'x': '✕', 'x-circle': '✕', 'x-square': '✕', 'x-lg': '✕',
      'plus': '＋', 'plus-circle': '⊕', 'plus-lg': '＋', 'plus-square': '⊕',
      'dash': '−', 'dash-circle': '⊖', 'dash-lg': '−',
      'pencil': '✎', 'pencil-square': '✎', 'pencil-fill': '✎',
      'trash': '✕', 'trash-fill': '✕', 'trash3': '✕',
      'arrow-clockwise': '↻', 'arrow-counterclockwise': '↺', 'arrow-repeat': '↻',
      'info-circle': 'ⓘ', 'info-square': 'ⓘ',
      'exclamation-triangle': '⚠', 'exclamation-circle': '⊗',
      'question-circle': '?', 'question-square': '?',
      'arrow-right': '→', 'arrow-left': '←', 'arrow-up': '↑', 'arrow-down': '↓',
      'arrow-up-right': '↗', 'arrow-down-right': '↘',
      'chevron-right': '›', 'chevron-left': '‹', 'chevron-up': '▲', 'chevron-down': '▼',
      'caret-right': '▶', 'caret-left': '◀', 'caret-up': '▲', 'caret-down': '▼',
      'graph-up': '↗', 'graph-down': '↘', 'graph-up-arrow': '↗',
      'play': '▶', 'play-fill': '▶', 'pause': '⏸', 'pause-fill': '⏸',
      'stop': '■', 'skip-forward': '⏭', 'skip-backward': '⏮',
      'list': '☰', 'list-ul': '☰', 'list-ol': '☰', 'list-check': '☰',
      'grid': '▦', 'grid-3x3': '▦', 'grid-fill': '▦',
      'three-dots': '⋯', 'three-dots-vertical': '⋮',
      'funnel': '☰', 'sliders': '☰',
      'folder': '▣', 'folder-fill': '▣', 'folder-plus': '▣', 'folder2': '▣',
      'file': '▤', 'file-earmark': '▤', 'file-text': '▤', 'file-pdf': '▤',
      'file-word': '▤', 'file-excel': '▤', 'file-image': '▣',
      'paperclip': '⫶', 'link': '⌘', 'link-45deg': '⌘',
      'upload': '↑', 'download': '↓', 'cloud-upload': '↑', 'cloud-download': '↓',
      'save': '⤓', 'save2': '⤓',
      'book': '▤', 'bookmark': '❏', 'bookmark-fill': '❏',
      'flag': '⚑', 'flag-fill': '⚑', 'tag': '#', 'tags': '#',
      'printer': '⎙', 'share': '↗', 'share-fill': '↗', 'box-arrow-up-right': '↗',
      'gear': '⚙', 'gear-fill': '⚙', 'wrench': '⚒', 'tools': '⚒', 'hammer': '⚒',
      'lock': '⚿', 'lock-fill': '⚿', 'unlock': '◯', 'key': '⚿', 'key-fill': '⚿',
      'shield': '⛨', 'shield-check': '⛨', 'shield-fill': '⛨', 'shield-lock': '⚿',
      'person': '☻', 'person-fill': '☻', 'person-circle': '◉',
      'people': '♟', 'people-fill': '♟', 'person-plus': '☻',
      'star': '★', 'star-fill': '★', 'star-half': '⯨',
      'trophy': '♛', 'trophy-fill': '♛', 'award': '♛', 'gem': '◆',
      'heart': '♥', 'heart-fill': '♥', 'hand-thumbs-up': '👍', 'hand-thumbs-down': '👎',
      'lightbulb': '◆', 'lightbulb-fill': '◆', 'fire': '✦', 'magic': '✦',
      'bar-chart': '▦', 'bar-chart-fill': '▦', 'pie-chart': '◐', 'pie-chart-fill': '◐',
      'graph-up-arrow': '↗',
      'clock': '◔', 'clock-fill': '◔', 'stopwatch': '◔',
      'hourglass': '⧗', 'hourglass-split': '⧗',
      'calendar': '▦', 'calendar-event': '▦', 'calendar-check': '▦',
      'currency-dollar': '$', 'currency-euro': '€', 'currency-yen': '¥', 'currency-pound': '£',
      'cash': '$', 'cash-stack': '$', 'wallet': '◫', 'wallet2': '◫',
      'credit-card': '▭', 'cart': '🛒', 'cart-fill': '🛒', 'cart3': '🛒',
      'bag': '🛍', 'bag-fill': '🛍', 'shop': '🏪', 'shop-window': '🏪',
      'laptop': '▢', 'pc-display': '▢', 'tv': '▭',
      'phone': '▯', 'phone-fill': '▯', 'tablet': '▭',
      'keyboard': '⌨', 'mouse': '◯', 'headphones': '◯', 'headset': '◯',
      'database': '▦', 'server': '▦', 'hdd': '▦', 'cpu': '▦',
      'cloud': '☁', 'cloud-fill': '☁', 'wifi': '◌', 'reception-4': '⌇',
      'bluetooth': 'ᛒ', 'battery-full': '▮', 'battery-charging': '▮',
      'lightning': '⚡', 'lightning-fill': '⚡', 'plug': '⚡',
      'image': '▣', 'images': '▣', 'camera': '◉', 'camera-fill': '◉',
      'camera-video': '▶', 'film': '▶',
      'mic': '◖', 'mic-fill': '◖', 'music-note': '♪', 'music-note-beamed': '♪',
      'volume-up': '◀', 'volume-down': '◀', 'volume-mute': '◀',
      'geo-alt': '◎', 'geo': '◎', 'pin-map': '◎', 'map': '▣', 'compass': '✦',
      'send': '➤', 'send-fill': '➤', 'airplane': '✈', 'airplane-fill': '✈',
      'car-front': '⊟', 'truck': '⊟', 'bicycle': '⊕',
      'house': '⌂', 'house-fill': '⌂', 'house-door': '⌂',
      'building': '▥', 'buildings': '▥', 'hospital': '✚',
      'mortarboard': '▿', 'book-half': '▤', 'brain': '◯',
      'flask': '⚗', 'eyedropper': '⚗',
      'briefcase': '▭', 'briefcase-fill': '▭',
      'plus-square-fill': '✚', 'bandaid': '✚', 'heart-pulse': '♥',
      'tree': '✿', 'flower1': '✿', 'flower2': '✿', 'flower3': '✿',
      'droplet': '◐', 'snow': '❄', 'snow2': '❄', 'snow3': '❄',
      'sun': '☀', 'sun-fill': '☀', 'moon': '☾', 'moon-fill': '☾',
      'cloud-sun': '☁', 'cloud-rain': '☁', 'cloud-lightning': '⚡', 'umbrella': '☂',
      'envelope': '✉', 'envelope-fill': '✉', 'envelope-open': '✉', 'at': '@',
      'telephone': '☎', 'telephone-fill': '☎',
      'chat': '◌', 'chat-fill': '◌', 'chat-dots': '◌', 'chat-square': '◌',
      'megaphone': '◖', 'broadcast': '◖',
      'bell': '◔', 'bell-fill': '◔', 'bell-slash': '◔',
      'globe': '◯', 'globe2': '◯', 'translate': '⇄',
      'rocket': '➤', 'rocket-takeoff': '➤',
      'search': '⌕', 'eye': '◉', 'eye-fill': '◉', 'eye-slash': '⊘',
      'gift': '◆', 'gift-fill': '◆',
      'hand-index': '☞', 'hand-index-thumb': '☞',
      'circle': '●', 'circle-fill': '●', 'square': '▢', 'square-fill': '▢',
      'asterisk': '✦', 'hash': '#',
    };

    // Generic icon-name → glyph heuristic (used when no explicit map hits).
    // Inspects keywords commonly found in icon class names / Material ligatures.
    // Returns null when nothing recognisable matches — caller falls back to a
    // neutral default.
    const ICON_KEYWORD_RULES = [
      [/check|done|tick|verified|complete|ok\b/, '✓'],
      [/close|cancel|xmark|times|wrong|reject/, '✕'],
      [/ban|block|disable|forbidden|prohibit/, '⊘'],
      [/plus|add|create|new\b/, '＋'],
      [/minus|subtract|less|reduce/, '−'],
      [/edit|pencil|pen|write|compose|modify/, '✎'],
      [/trash|delete|bin|remove/, '✕'],
      [/refresh|reload|sync|rotate|cycle/, '↻'],
      [/undo|revert/, '↶'],
      [/redo/, '↷'],
      [/info|about/, 'ⓘ'],
      [/warn|alert|caution/, '⚠'],
      [/error|fail|critical/, '⊗'],
      [/help|question|faq|inquir/, '?'],
      [/forward|next|right/, '→'],
      [/back|previous|prev|left/, '←'],
      [/upload|cloud[\s_-]*up/, '↑'],
      [/download|cloud[\s_-]*down/, '↓'],
      [/up\b|top|north/, '↑'],
      [/down\b|bottom|south/, '↓'],
      [/expand|more|chevron[\s_-]*down|caret[\s_-]*down/, '▼'],
      [/collapse|less|chevron[\s_-]*up|caret[\s_-]*up/, '▲'],
      [/swap|exchange|transfer|convert/, '⇄'],
      [/menu|bars|hamburger|drawer/, '☰'],
      [/grid|dashboard|apps|tiles|widgets/, '▦'],
      [/list/, '☰'],
      [/more[\s_-]*horiz|dots[\s_-]*horizontal/, '⋯'],
      [/more[\s_-]*vert|dots[\s_-]*vertical|kebab/, '⋮'],
      [/filter|funnel|sort|slider|tune/, '☰'],
      [/folder|directory/, '▣'],
      [/file|document|doc\b|paper|article|page/, '▤'],
      [/copy|duplicate|clone/, '⎘'],
      [/cut|scissors/, '✂'],
      [/attach|paperclip|clip/, '⫶'],
      [/link|url|chain/, '⌘'],
      [/save|disk|floppy/, '⤓'],
      [/print/, '⎙'],
      [/share|export|external|launch/, '↗'],
      [/book|read|library|stories/, '▤'],
      [/bookmark/, '❏'],
      [/flag|pennant|tour/, '⚑'],
      [/tag|label|hash/, '#'],
      [/settings?|preferences?|config|gear|cog|wrench/, '⚙'],
      [/build|construct|hammer|tool|repair|fix/, '⚒'],
      [/lock|secure|password|encrypt|key/, '⚿'],
      [/shield|security|guard|protect|defend|admin/, '⛨'],
      [/star|favori?te|grade|stellar/, '★'],
      [/trophy|award|medal|champion|crown|premium/, '♛'],
      [/diamond|gem|jewel/, '◆'],
      [/heart|love|romance|liked?\b/, '♥'],
      [/thumb[\s_-]*up|like\b|approve/, '👍'],
      [/thumb[\s_-]*down|dislike|disapprove/, '👎'],
      [/spark|magic|wand|shine|glow|awesome|celebrat|fire|hot|flame|sun\b|light|bulb|idea/, '✦'],
      [/insight|tip|update|highlight/, '◆'],
      [/chart|graph|analytic|stats|metric|bar/, '▦'],
      [/pie|donut|doughnut/, '◐'],
      [/trend|growth|increase|rise/, '↗'],
      [/decrease|decline|drop|fall/, '↘'],
      [/timeline|line[\s_-]*chart|wave|pulse|monitor/, '⌇'],
      [/clock|time|schedule|watch|stopwatch|alarm|snooze|deadline/, '◔'],
      [/hourglass|sandglass/, '⧗'],
      [/calendar|date|event|day|today|month|year|week/, '▦'],
      [/dollar|money|cash|payment|cost|price|pay|income|revenue/, '$'],
      [/euro/, '€'],
      [/yen|rmb/, '¥'],
      [/pound/, '£'],
      [/wallet|savings|bank/, '◫'],
      [/credit[\s_-]*card|card\b/, '▭'],
      [/cart|basket/, '🛒'],
      [/bag|shopping/, '🛍'],
      [/store|shop|market/, '🏪'],
      [/laptop|desktop|computer|monitor|display|pc\b/, '▢'],
      [/mobile|phone|smartphone/, '▯'],
      [/tablet|ipad/, '▭'],
      [/keyboard|typing/, '⌨'],
      [/mouse(?!.*hover)/, '◯'],
      [/headphone|headset|earbud/, '◯'],
      [/database|server|storage|disk|drive|hdd|ssd|cpu|memory|chip/, '▦'],
      [/cloud/, '☁'],
      [/wifi|signal|network|router|broadcast/, '◌'],
      [/bluetooth/, 'ᛒ'],
      [/battery|charge/, '▮'],
      [/bolt|lightning|flash|power|electric|energy/, '⚡'],
      [/image|photo|picture|gallery|album/, '▣'],
      [/camera/, '◉'],
      [/video|movie|film|clip|play/, '▶'],
      [/pause/, '⏸'],
      [/stop\b/, '■'],
      [/mic|microphone|broadcast|voice|record/, '◖'],
      [/music|song|audio|track|note/, '♪'],
      [/volume|speaker|sound/, '◀'],
      [/location|pin|marker|place|map[\s_-]*marker|geo/, '◎'],
      [/map\b/, '▣'],
      [/compass|navigate|near|direction|explor/, '✦'],
      [/send|paperplane|paper-plane|airplane|flight|plane/, '➤'],
      [/car|truck|bus|taxi|train|tram|subway|metro|vehicle|transport/, '⊟'],
      [/bicycle|bike/, '⊕'],
      [/walk|run|person[\s_-]*walk|person[\s_-]*run/, '⫯'],
      [/gas|fuel|pump/, '⛽'],
      [/home|house|cottage/, '⌂'],
      [/building|office|apartment|hotel|business|company|domain|corporate|city|industry/, '▥'],
      [/school|education|graduat|academic|study/, '▿'],
      [/brain|psychology|mind/, '◯'],
      [/science|flask|atom|chemistry|biology|biotech|lab|experiment|test[\s_-]*tube|vial/, '⚗'],
      [/work|job|brief|portfolio|case/, '▭'],
      [/hospital|medical|medicine|doctor|nurse|care|clinic|heal|first[\s_-]*aid|pill|drug|vaccin|syring/, '✚'],
      [/pulse|heartbeat/, '♥'],
      [/eco|plant|leaf|tree|flower|garden|park|forest|nature|grass|sprout|seed/, '✿'],
      [/water|drop|liquid/, '◐'],
      [/snow|frost|cold|ice|winter/, '❄'],
      [/wave|ocean|sea|beach/, '〜'],
      [/sun|sunny|bright|day|light[\s_-]*mode/, '☀'],
      [/moon|night|dark[\s_-]*mode|bedtime/, '☾'],
      [/rain|storm|thunder|umbrella/, '☂'],
      [/mail|envelope|email|inbox|message[\s_-]*read/, '✉'],
      [/at[\s_-]*sign|@/, '@'],
      [/telephone|call|phone/, '☎'],
      [/chat|comment|message|sms|forum|conversation/, '◌'],
      [/megaphone|campaign|announce|broadcast|bullhorn/, '◖'],
      [/bell|notification|notify|ring/, '◔'],
      [/globe|earth|world|planet|public|language|international/, '◯'],
      [/translate|i18n|locale/, '⇄'],
      [/rocket|launch/, '➤'],
      [/search|find|magnif|loupe/, '⌕'],
      [/eye|visibility|view|preview|watch/, '◉'],
      [/hidden|invisible|eye[\s_-]*slash|eye[\s_-]*off/, '⊘'],
      [/gift|present|reward|bonus|celebrate|cake|birthday/, '◆'],
      [/hand|pointer|cursor|tap|click|touch/, '☞'],
      [/circle/, '●'],
      [/square|box|rectangle/, '▢'],
      [/triangle/, '△'],
      [/asterisk|sparkle|new\b/, '✦'],
      [/quote/, '“'],
      [/face|smile|happy|emoji|sentiment/, '☻'],
      [/sad|frown/, '☹'],
      [/user|person|profile|account|avatar/, '☻'],
      [/people|team|group|community|members?|crowd/, '♟'],
      [/handshake|partner|deal|agreement/, '✻'],
    ];
    const inferIconByKeyword = (name) => {
      if (!name) return null;
      const lower = name.toLowerCase().replace(/[_-]+/g, ' ');
      for (const [re, glyph] of ICON_KEYWORD_RULES) {
        if (re.test(lower)) return glyph;
      }
      return null;
    };
    const ICON_CLASS_PATTERN = /(?:^|\s)(material-icons|material-symbols-(?:outlined|rounded|sharp)|fa-[a-z0-9-]+|fas|far|fab|fal|fad|bi-[a-z0-9-]+|icon-[a-z0-9-]+)(?:\s|$)/;
    const MATERIAL_ICON_CLASS_PATTERN = /(?:^|\s)(material-icons|material-symbols-(?:outlined|rounded|sharp))(?:\s|$)/;
    const isIconElement = (el) => {
      if (!el) return false;
      if (el.tagName !== 'I' && el.tagName !== 'SPAN') return false;
      const cls = typeof el.className === 'string' ? el.className : (el.className.baseVal || '');
      if (ICON_CLASS_PATTERN.test(cls)) return true;
      const ff = (window.getComputedStyle(el).fontFamily || '').toLowerCase();
      return ff.includes('material icons') || ff.includes('material symbols') ||
             ff.includes('font awesome') || ff.includes('fontawesome') ||
             ff.includes('bootstrap-icons') || ff.includes('feather');
    };
    const isMaterialLigatureIcon = (el) => {
      if (!el) return false;
      const raw = (el.textContent || '').trim();
      if (raw.length <= 1) return false;
      const cls = typeof el.className === 'string' ? el.className : (el.className?.baseVal || '');
      if (MATERIAL_ICON_CLASS_PATTERN.test(cls)) return true;
      const ff = (window.getComputedStyle(el).fontFamily || '').toLowerCase();
      return ff.includes('material icons') || ff.includes('material symbols');
    };
    const normalizeIconBoxForMeasurement = (el) => {
      if (!isMaterialLigatureIcon(el)) return;
      const computed = window.getComputedStyle(el);
      const fsPx = parseFloat(computed.fontSize) || 16;
      // Material Icons ligatures are visually a 1em square. If the webfont is
      // unavailable during conversion, Chromium measures raw names such as
      // business_center as long words, which corrupts flex layout and
      // produces inconsistent PPT icon widths. Force the measured box to match
      // the symbol we will emit into PowerPoint.
      const boxPx = Math.max(1, fsPx);
      el._h2pIconBoxPx = boxPx;
      if (el._iconGlyph) el.textContent = el._iconGlyph;
      el.style.setProperty('display', 'inline-flex', 'important');
      el.style.setProperty('align-items', 'center', 'important');
      el.style.setProperty('justify-content', 'center', 'important');
      el.style.setProperty('width', boxPx + 'px', 'important');
      el.style.setProperty('height', boxPx + 'px', 'important');
      el.style.setProperty('min-width', boxPx + 'px', 'important');
      el.style.setProperty('max-width', boxPx + 'px', 'important');
      el.style.setProperty('line-height', boxPx + 'px', 'important');
      el.style.setProperty('overflow', 'hidden', 'important');
      el.style.setProperty('white-space', 'nowrap', 'important');
      el.style.setProperty('flex', '0 0 ' + boxPx + 'px', 'important');
      el.style.setProperty('font-family', 'Segoe UI Symbol', 'important');
    };
    // Extract the bare icon name from a class string (`fa-user`, `bi-check-circle`).
    const extractIconNameFromClass = (cls) => {
      if (!cls) return null;
      // Try FA first (`fa-` prefix)
      const fa = cls.match(/(?:^|\s)fa-([a-z0-9-]+)(?:\s|$)/);
      if (fa && !/^(solid|regular|brands|light|duotone|sharp|thin|stack|spin|pulse|fw|li|lg|sm|xs|2x|3x|4x|5x|6x|7x|8x|9x|10x|inverse|rotate|flip|pull|border)$/.test(fa[1])) {
        return fa[1];
      }
      // Bootstrap Icons (`bi-` prefix)
      const bi = cls.match(/(?:^|\s)bi-([a-z0-9-]+)(?:\s|$)/);
      if (bi) return bi[1];
      // Generic icon-XYZ pattern
      const ic = cls.match(/(?:^|\s)icon-([a-z0-9-]+)(?:\s|$)/);
      if (ic) return ic[1];
      return null;
    };
    const resolveIconGlyph = (el) => {
      const raw = (el.textContent || '').trim().toLowerCase().replace(/\s+/g, '_');
      // 1. Material Icons (ligature is the text content)
      if (raw && MATERIAL_ICON_MAP[raw]) return MATERIAL_ICON_MAP[raw];
      // 2. Font Awesome / Bootstrap Icons / generic — class-based lookup
      const cls = typeof el.className === 'string' ? el.className : (el.className?.baseVal || '');
      const iconName = extractIconNameFromClass(cls);
      if (iconName) {
        if (FA_ICON_MAP[iconName]) return FA_ICON_MAP[iconName];
        if (BI_ICON_MAP[iconName]) return BI_ICON_MAP[iconName];
        if (MATERIAL_ICON_MAP[iconName.replace(/-/g, '_')]) {
          return MATERIAL_ICON_MAP[iconName.replace(/-/g, '_')];
        }
      }
      // 3. Read ::before pseudo content (FA/Bootstrap render glyphs via CSS)
      try {
        const beforeContent = window.getComputedStyle(el, '::before').content;
        const m = beforeContent && beforeContent.match(/^"(.+)"$/);
        if (m && m[1] && m[1] !== 'none') return m[1];
      } catch (e) { /* ignore */ }
      // 4. Keyword heuristic on the icon name OR class — picks a glyph that
      // matches the icon's *meaning* instead of a literal "▢" placeholder.
      const guessed = inferIconByKeyword(iconName || raw) || inferIconByKeyword(cls);
      if (guessed) return guessed;
      // 5. Last-resort fallback — a star is a friendlier neutral icon than
      // an empty square. It reads as "marker / highlight" rather than
      // "broken glyph", so a missed mapping still looks intentional.
      return '✦';
    };
    // Mark icon elements so they are extracted with mapped glyph + PPT-safe font
    document.querySelectorAll('i, span').forEach(el => {
      if (isIconElement(el)) {
        el._isIcon = true;
        el._iconGlyph = resolveIconGlyph(el);
        normalizeIconBoxForMeasurement(el);
      }
    });
    // The inline style changes above intentionally affect flex/grid layout.
    // Flush once before any bounding boxes are collected.
    void document.body.offsetHeight;

    // Pre-pass: heading/paragraph elements whose only text-bearing children are
    // block-display inline tags (e.g. `<h1><span class="block">A</span><span class="block">B</span></h1>`)
    // would otherwise be flattened into a single paragraph of inline runs by
    // parseInlineFormatting, causing the children to render side-by-side in
    // PowerPoint. Detect this case and split into per-child text frames so each
    // gets its own bounding box, font size, and line spacing.
    const _isBlockDisplay = (n) => {
      const d = window.getComputedStyle(n).display;
      return d === 'block' || d === 'flex' || d === 'grid' || d === 'list-item';
    };
    document.querySelectorAll('h1,h2,h3,h4,h5,h6,p').forEach(parent => {
      const children = Array.from(parent.children);
      if (children.length < 2) return;
      const blockTextChildren = children.filter(c =>
        ['SPAN','B','STRONG','I','EM','U','A','LABEL','CODE','MARK','TIME','CITE','ABBR','S'].includes(c.tagName)
        && c.textContent.trim()
        && _isBlockDisplay(c)
      );
      // Require ALL text-bearing children to be block-display — mixed content
      // (some inline, some block) is risky to split.
      const textBearingChildren = children.filter(c => c.textContent.trim());
      if (blockTextChildren.length < 2 || blockTextChildren.length !== textBearingChildren.length) return;
      // No direct text nodes at the parent level.
      const hasDirectText = Array.from(parent.childNodes).some(n =>
        n.nodeType === Node.TEXT_NODE && n.textContent.trim()
      );
      if (hasDirectText) return;
      parent._skipTextExtraction = true;
      blockTextChildren.forEach(c => { c._treatAsP = true; });
    });

    // Mixed direct text + block-display inline child, e.g.
    // <div class="chap-num">01<span class="slash">— Tsinghua</span></div>.
    // Keeping this as one rich-text frame makes the small block child inherit
    // the large parent's paragraph line height in PPT. Split the parent direct
    // text and each block child into their own measured text frames.
    const INLINE_TEXT_CHILD_TAGS = ['SPAN','B','STRONG','I','EM','U','A','LABEL','CODE','MARK','TIME','CITE','ABBR','S'];
    document.querySelectorAll('*').forEach(parent => {
      const directTextNodes = Array.from(parent.childNodes).filter(n =>
        n.nodeType === Node.TEXT_NODE && n.textContent.trim()
      );
      if (directTextNodes.length === 0) return;
      const blockTextChildren = Array.from(parent.children).filter(c =>
        INLINE_TEXT_CHILD_TAGS.includes(c.tagName) && c.textContent.trim() && _isBlockDisplay(c)
      );
      if (blockTextChildren.length === 0) return;
      parent._directTextOnly = true;
      blockTextChildren.forEach(c => { c._treatAsP = true; });
    });

    // Inline sibling spans of very different font sizes on the SAME line, e.g.
    // <div><span class="ch-num">01</span><span class="ch-num-tail">/ 04</span></div>
    // where 01 is 140px and "/ 04" is 38px. Emitting each span as its own text
    // frame anchors both at their individual bounding-box tops; because the small
    // span's box sits at the big span's baseline (CSS vertical-align:baseline), it
    // renders far below the big number in PPT instead of hugging its bottom-right.
    // Merge such a row into ONE rich-text frame so PowerPoint baseline-aligns the
    // runs exactly like the browser. Restricted to normal (non-flex/grid) flow and
    // a clear size gap so flex "label … value" rows (justify-between) are untouched.
    document.querySelectorAll('*').forEach(parent => {
      if (parent._treatAsP || parent._directTextOnly || parent._skipTextExtraction) return;
      if (parent.closest('p,h1,h2,h3,h4,h5,h6,li')) return;
      const pdisp = window.getComputedStyle(parent).display;
      if (pdisp === 'flex' || pdisp === 'inline-flex' || pdisp === 'grid' || pdisp === 'inline-grid') return;
      const kids = Array.from(parent.children);
      if (kids.length < 2) return;
      const textKids = kids.filter(c => c.textContent.trim());
      if (textKids.length < 2) return;
      // Every text-bearing child must be an inline (non-block) span-like element.
      const allInline = textKids.every(c =>
        INLINE_TEXT_CHILD_TAGS.includes(c.tagName) && !_isBlockDisplay(c)
      );
      if (!allInline) return;
      // No direct text at the parent level (handled by the _directTextOnly pass).
      const hasDirectText = Array.from(parent.childNodes).some(n =>
        n.nodeType === Node.TEXT_NODE && n.textContent.trim()
      );
      if (hasDirectText) return;
      // All children must share one visual row (vertical overlap).
      const rects = textKids.map(c => c.getBoundingClientRect());
      if (rects.some(r => r.width === 0 || r.height === 0)) return;
      const rowTop = Math.max(...rects.map(r => r.top));
      const rowBottom = Math.min(...rects.map(r => r.bottom));
      if (rowBottom <= rowTop) return; // no common vertical band → not one line
      // Require a clear font-size gap — this is the case where separate frames
      // misalign. Similarly-sized siblings already line up when split.
      const sizes = textKids.map(c => parseFloat(window.getComputedStyle(c).fontSize) || 0);
      const maxS = Math.max(...sizes), minS = Math.min(...sizes);
      if (!(minS > 0 && maxS / minS >= 1.4)) return;
      parent._treatAsP = true;
      parent._mergeInlineRow = true;
      textKids.forEach(c => { c._mergedIntoInlineRow = true; });
    });

    // Effective z-index — a descendant of a z-indexed ancestor paints inside
    // that ancestor's stacking context (per CSS painting rules). In our flat
    // z-index model we approximate that by promoting each element's z-index
    // to the maximum of its own and any ancestor's. Without this, a panel
    // like `.text-overlay { background:#fff; z-index:20 }` would end up
    // rendering ON TOP of the text it contains because the children default
    // to z=0 and the panel shape is drawn last.
    const getEffectiveZIndex = (el) => {
      const ownRaw = parseInt(window.getComputedStyle(el).zIndex, 10);
      let effective = Number.isFinite(ownRaw) ? ownRaw : 0;
      let p = el.parentElement;
      while (p && p !== document.body && p !== document.documentElement) {
        const pZ = parseInt(window.getComputedStyle(p).zIndex, 10);
        if (Number.isFinite(pZ) && pZ > effective) effective = pZ;
        p = p.parentElement;
      }
      return effective;
    };

    const getNearestTextClipBounds = (el) => {
      let p = el.parentElement;
      while (p && p !== document.body && p !== document.documentElement) {
        if (p.classList && p.classList.contains('slide')) return null;
        const cs = window.getComputedStyle(p);
        const r = p.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) {
          p = p.parentElement;
          continue;
        }
        const bg = cs.backgroundColor;
        const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
        const hasBgImage = cs.backgroundImage && cs.backgroundImage !== 'none';
        const borders = [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth]
          .map(v => parseFloat(v) || 0);
        const hasBorder = borders.some(v => v > 0);
        const hasShadow = cs.boxShadow && cs.boxShadow !== 'none';
        const hasRadius = (parseFloat(cs.borderRadius) || 0) > 0;
        if (hasBg || hasBgImage || hasBorder || hasShadow || hasRadius) {
          const padL = parseFloat(cs.paddingLeft) || 0;
          const padR = parseFloat(cs.paddingRight) || 0;
          const padT = parseFloat(cs.paddingTop) || 0;
          const padB = parseFloat(cs.paddingBottom) || 0;
          const x = r.left + borders[3] + padL;
          const y = r.top + borders[0] + padT;
          const w = Math.max(1, r.width - borders[1] - borders[3] - padL - padR);
          const h = Math.max(1, r.height - borders[0] - borders[2] - padT - padB);
          return { x: pxToInch(relX(x)), y: pxToInch(relY(y)), w: pxToInch(w), h: pxToInch(h) };
        }
        p = p.parentElement;
      }
      return null;
    };

    const getFlexTextRightBound = (el, rect) => {
      const p = el.parentElement;
      if (!p) return null;
      const pcs = window.getComputedStyle(p);
      if (pcs.display !== 'flex' && pcs.display !== 'inline-flex') return null;
      if (String(pcs.flexDirection || 'row').startsWith('column')) return null;

      const pRect = p.getBoundingClientRect();
      if (pRect.width <= 0 || pRect.height <= 0) return null;
      const gap = parseFloat(pcs.columnGap || pcs.gap) || 0;
      const padR = parseFloat(pcs.paddingRight) || 0;
      const siblingRects = Array.from(p.children)
        .filter(c => c !== el)
        .map(c => c.getBoundingClientRect())
        .filter(r => r.width > 0 && r.height > 0);
      const nextRightSibling = siblingRects
        .filter(r => r.left >= rect.right - 1 || r.left > rect.left + rect.width * 0.5)
        .sort((a, b) => a.left - b.left)[0];
      const rightPx = nextRightSibling
        ? nextRightSibling.left - Math.max(2, gap * 0.5)
        : pRect.right - padR;
      if (rightPx <= rect.left + rect.width + 1) return null;
      return pxToInch(relX(rightPx));
    };

    const getNextFlowTextTopBound = (el, rect) => {
      const p = el.parentElement;
      if (!p) return null;
      const cs = window.getComputedStyle(el);
      if (cs.position === 'absolute' || cs.position === 'fixed') return null;
      if (cs.float && cs.float !== 'none') return null;
      const pcs = window.getComputedStyle(p);
      const parentDisplay = pcs.display || 'block';
      if (parentDisplay.includes('grid')) return null;
      if (parentDisplay.includes('flex') && !String(pcs.flexDirection || 'row').startsWith('column')) {
        return null;
      }
      for (let sib = el.nextElementSibling; sib; sib = sib.nextElementSibling) {
        const sr = sib.getBoundingClientRect();
        if (sr.width <= 0 || sr.height <= 0) continue;
        if (sr.top <= rect.top + 1) return null;
        const scs = window.getComputedStyle(sib);
        if (scs.display === 'none' || scs.visibility === 'hidden') continue;
        const txt = normalizeWhitespaceForPpt(sib.textContent || '', scs.whiteSpace).trim();
        if (!txt) continue;
        return pxToInch(relY(sr.top));
      }
      return null;
    };

    document.querySelectorAll('*').forEach((el) => {
      if (processed.has(el)) return;

      // Inline spans that were merged into a single parent rich-text frame by the
      // same-line size-gap pre-pass. The parent emits their text as runs; emitting
      // them again here would duplicate the glyphs.
      if (el._mergedIntoInlineRow) {
        processed.add(el);
        el.querySelectorAll('*').forEach(child => processed.add(child));
        return;
      }

      // ── Icon elements (Material Icons / Font Awesome / Bootstrap Icons / etc.) ──
      if (el._isIcon) {
        // If this icon is inside a text container, parseInlineFormatting emits it
        // inline — do not double-extract here.
        if (el.closest('p,h1,h2,h3,h4,h5,h6,li,ul,ol')) {
          processed.add(el);
          return;
        }
        let rect = el.getBoundingClientRect();
        const iconParent = el.parentElement;
        const parentComputed = iconParent ? window.getComputedStyle(iconParent) : null;
        const parentRect = iconParent ? iconParent.getBoundingClientRect() : null;
        const textBearingSiblings = iconParent
          ? Array.from(iconParent.children).filter(c => c !== el && (c.textContent || '').trim())
          : [];
        const parentCentersIcon = parentComputed && parentRect &&
          (parentComputed.display === 'flex' || parentComputed.display === 'inline-flex' || parentComputed.display === 'grid' || parentComputed.display === 'inline-grid') &&
          parentComputed.alignItems === 'center' &&
          (parentComputed.justifyContent === 'center' || parentComputed.justifyItems === 'center') &&
          textBearingSiblings.length === 0;
        if (parentCentersIcon && parentRect.width > 0 && parentRect.height > 0) {
          const computed = window.getComputedStyle(el);
          const fsPx = parseFloat(computed.fontSize) || Math.min(parentRect.width, parentRect.height);
          // HTML icon fonts draw the glyph inside a centered 1em box. In PPT the
          // fallback Unicode symbol has different font metrics, so using the
          // whole visual container as the text box can look off-center. Rebuild
          // the 1em-ish glyph box at the center of the parent frame instead.
          const minFrame = Math.min(parentRect.width, parentRect.height);
          const glyphBox = Math.max(1, Math.min(minFrame, fsPx * 1.45));
          rect = {
            left: parentRect.left + (parentRect.width - glyphBox) / 2,
            top: parentRect.top + (parentRect.height - glyphBox) / 2,
            width: glyphBox,
            height: glyphBox
          };
        }
        if (rect.width > 0 && rect.height > 0) {
          const computed = window.getComputedStyle(el);
          const fsPx = parseFloat(computed.fontSize) || rect.height;
          // Size the glyph to match the icon's visible box. Material Icons
          // render at ~1em with the glyph filling the full box, but most
          // Unicode symbols leave much more empty padding around their
          // glyph. Bumping the font size up to ~1.25× the source font-size
          // (capped at 48pt) gets the rendered symbol closer to the
          // original icon's optical size.
          const glyphFontSize = Math.max(8, Math.min(fsPx * PT_PER_PX * SCALE * 1.25, 48));
          elements.push({
            type: 'p',
            text: el._iconGlyph,
            noWrap: true,
            zIndex: getEffectiveZIndex(el),
            position: rectPosition(rect),
            style: {
              fontSize: glyphFontSize,
              // Segoe UI Symbol is shipped with Windows by default and has
              // broad coverage of Unicode BMP symbols, geometric shapes,
              // dingbats, and basic emoji — far more reliable in
              // PowerPoint than Noto Color Emoji. On Mac/Linux the OS
              // falls back to a font with the needed glyph automatically.
              fontFace: 'Segoe UI Symbol',
              color: rgbToHex(computed.color),
              align: 'center',
              charSpacing: undefined,
              lineSpacing: null,
              paraSpaceBefore: 0,
              paraSpaceAfter: 0,
              margin: [0, 0, 0, 0],
              bold: false,
              italic: false,
              underline: false,
              _isIcon: true,
              _centerInFrame: parentCentersIcon
            }
          });
        }
        processed.add(el);
        el.querySelectorAll('*').forEach(child => processed.add(child));
        return;
      }

      // Extract placeholder elements (for charts, etc.). Do not treat a bare
      // decorative class token like `.placeholder` as a chart placeholder:
      // authors also use it for styled content cards.
      const classTokens = el.classList ? Array.from(el.classList) : [];
      const isPlaceholderElement =
        el.hasAttribute('data-placeholder') ||
        el.hasAttribute('data-chart') ||
        /^placeholder(?:-|$)/i.test(el.id || '') ||
        classTokens.some(cls => /^(chart|plot|viz|graph)-?placeholder$/i.test(cls));
      if (isPlaceholderElement) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          const computed = window.getComputedStyle(el);
          placeholders.push({
            id: el.id || `placeholder-${placeholders.length}`,
            ...rectPosition(rect),
            zIndex: getEffectiveZIndex(el)
          });
        }
        processed.add(el);
        el.querySelectorAll('*').forEach(child => processed.add(child));
        return;
      }

      // Rasterize <canvas> (ECharts / Chart.js data visualizations) to a PNG so
      // charts survive into the deck. The canvas is already painted by the time
      // extraction runs (see the chart-render wait after page load). A blank or
      // not-yet-painted canvas produces a tiny transparent PNG — skip those.
      if (el.tagName === 'CANVAS') {
        const rect = el.getBoundingClientRect();
        if (rect.width > 1 && rect.height > 1) {
          let dataUrl = null;
          try { dataUrl = el.toDataURL('image/png'); } catch (e) { dataUrl = null; }
          if (dataUrl && dataUrl.length > 2000) {
            elements.push({
              type: 'image',
              src: dataUrl,
              objectFit: 'fill',
              zIndex: getEffectiveZIndex(el),
              position: rectPosition(rect)
            });
          }
        }
        processed.add(el);
        el.querySelectorAll('*').forEach(child => processed.add(child));
        return;
      }

      // Silently skip media/embed elements that we cannot render in PPT
      // (these would otherwise emit empty shapes from the container fallback)
      if (el.tagName === 'IFRAME' || el.tagName === 'VIDEO' || el.tagName === 'AUDIO' ||
          el.tagName === 'EMBED' || el.tagName === 'OBJECT' ||
          el.tagName === 'SOURCE' || el.tagName === 'TRACK' || el.tagName === 'PARAM') {
        processed.add(el);
        el.querySelectorAll('*').forEach(child => processed.add(child));
        return;
      }

      // Horizontal rules → thin line shape
      if (el.tagName === 'HR') {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0) {
          const computed = window.getComputedStyle(el);
          // Prefer border-top color & width (most browsers render <hr> via border)
          let widthPx = parseFloat(computed.borderTopWidth) || 1;
          let color = computed.borderTopColor && computed.borderTopColor !== 'rgba(0, 0, 0, 0)'
            ? rgbToHex(computed.borderTopColor)
            : rgbToHex(computed.color);
          const styleVal = computed.borderTopStyle;
          const dashType = styleVal === 'dashed' ? 'dash' : styleVal === 'dotted' ? 'dot' : 'solid';
          elements.push({
            type: 'hr',
            color,
            thickness: widthPx * PT_PER_PX * SCALE,
            dashType,
            position: rectPosition(rect)
          });
        }
        processed.add(el);
        return;
      }

      // Inline SVG → serialize, embed as data URL image
      if (el.tagName === 'svg' || el.tagName === 'SVG' ||
          (el.namespaceURI === 'http://www.w3.org/2000/svg' && el.tagName.toLowerCase() === 'svg')) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          try {
            const computed = window.getComputedStyle(el);
            // Ensure xmlns is set for standalone parsing
            let svgEl = el.cloneNode(true);
            if (!svgEl.getAttribute('xmlns')) svgEl.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            // Standalone SVG rasterization cannot see page CSS. Inline the
            // computed paint on descendants so rules like `.starburst path` keep
            // their intended color after sharp renders the SVG data URL.
            const srcNodes = [el, ...Array.from(el.querySelectorAll('*'))];
            const cloneNodes = [svgEl, ...Array.from(svgEl.querySelectorAll('*'))];
            srcNodes.forEach((srcNode, idx) => {
              const cloneNode = cloneNodes[idx];
              if (!cloneNode) return;
              const cs = window.getComputedStyle(srcNode);
              if (cs.fill && cs.fill !== 'none' && cs.fill !== 'rgba(0, 0, 0, 0)') cloneNode.setAttribute('fill', cs.fill);
              if (cs.stroke && cs.stroke !== 'none' && cs.stroke !== 'rgba(0, 0, 0, 0)') cloneNode.setAttribute('stroke', cs.stroke);
            });
            // Lock viewBox and explicit pixel size so the rasterizer respects layout.
            if (!svgEl.getAttribute('width')) svgEl.setAttribute('width', String(rect.width));
            if (!svgEl.getAttribute('height')) svgEl.setAttribute('height', String(rect.height));
            const svgStr = new XMLSerializer().serializeToString(svgEl);
            // base64 in browser via btoa with utf-8 safe encoding
            const utf8 = unescape(encodeURIComponent(svgStr));
            const dataUrl = 'data:image/svg+xml;base64,' + btoa(utf8);
            const transparency = computeTransparency(null, computed.opacity);
            const imageEl = {
              type: 'image',
              src: dataUrl,
              position: rectPosition(rect)
            };
            if (transparency !== null) imageEl.transparency = transparency;
            elements.push(imageEl);
          } catch (e) {
            // Best effort — if serialization fails, just drop it
          }
        }
        processed.add(el);
        el.querySelectorAll('*').forEach(child => processed.add(child));
        return;
      }

      // Extract images
      if (el.tagName === 'IMG') {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          const computed = window.getComputedStyle(el);
          // object-fit: fill (default), cover, contain — all map to PptxGenJS sizing types
          let objectFit = null;
          const fit = computed.objectFit;
          if (fit === 'cover') objectFit = 'cover';
          else if (fit === 'contain') objectFit = 'contain';
          // opacity → transparency (image has no color so we pass null for color)
          const transparency = computeTransparency(null, computed.opacity);
          // box-shadow on image
          const shadow = parseBoxShadow(computed.boxShadow);
          // border-radius rounding hint
          let rounding = false;
          const br = parseFloat(computed.borderRadius);
          if (br > 0 && computed.borderRadius.includes('%') && br >= 50 &&
              Math.abs(rect.width - rect.height) < 2) {
            rounding = true;
          }
          // hyperlink — if wrapped in <a>
          let hyperlink = null;
          const a = el.closest('a');
          if (a && a.href) {
            hyperlink = { url: a.href };
            if (a.title) hyperlink.tooltip = a.title;
          }
          elements.push({
            type: 'image',
            src: el.src,
            objectFit,
            objectPosition: computed.objectPosition,
            rounding,
            transparency,
            shadow,
            hyperlink,
            zIndex: getEffectiveZIndex(el),
            position: rectPosition(rect)
          });
          processed.add(el);
          return;
        }
      }

      // Extract <table> as native PptxGenJS table (handle here BEFORE the container/text fallback)
      if (el.tagName === 'TABLE') {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          const tableComputed = window.getComputedStyle(el);
          const rows = [];
          // Collect rows in document order across thead/tbody/tfoot
          const trList = Array.from(el.querySelectorAll('tr'));
          const getSpan = (node, attr) => {
            const n = parseInt(node.getAttribute(attr), 10);
            return Number.isFinite(n) && n > 0 ? n : 1;
          };
          const colGroupWidths = [];
          for (const col of Array.from(el.querySelectorAll('colgroup col'))) {
            const span = getSpan(col, 'span');
            const colComputed = window.getComputedStyle(col);
            const styleWidth = parseFloat(col.style.width || colComputed.width) || 0;
            const rectWidth = col.getBoundingClientRect ? col.getBoundingClientRect().width : 0;
            const widthPx = rectWidth || styleWidth;
            if (widthPx > 0) {
              for (let i = 0; i < span; i++) colGroupWidths.push(pxToInch(widthPx / span));
            }
          }
          let colWidths = colGroupWidths.length > 0 ? colGroupWidths : undefined;
          if (!colWidths) {
            let bestCells = [];
            let bestExpandedCount = 0;
            for (const tr of trList) {
              const cells = Array.from(tr.children).filter(c => c.tagName === 'TD' || c.tagName === 'TH');
              const expandedCount = cells.reduce((sum, c) => sum + getSpan(c, 'colspan'), 0);
              if (expandedCount > bestExpandedCount || (expandedCount === bestExpandedCount && cells.length > bestCells.length)) {
                bestCells = cells;
                bestExpandedCount = expandedCount;
              }
            }
            if (bestCells.length > 0) {
              colWidths = [];
              for (const cell of bestCells) {
                const span = getSpan(cell, 'colspan');
                const width = pxToInch(cell.getBoundingClientRect().width) / span;
                for (let i = 0; i < span; i++) colWidths.push(width);
              }
            }
          }
          for (const tr of trList) {
            const cells = Array.from(tr.children).filter(c => c.tagName === 'TD' || c.tagName === 'TH');
            if (cells.length === 0) continue;
            const rowOut = cells.map(cell => {
              const cellComputed = window.getComputedStyle(cell);
              const isHeader = cell.tagName === 'TH';
              const cellAlign = cellComputed.textAlign === 'start' ? 'left'
                : cellComputed.textAlign === 'end' ? 'right' : cellComputed.textAlign;
              const valignMap = { top: 'top', middle: 'middle', bottom: 'bottom' };
              const cellOpts = {
                bold: isHeader || cellComputed.fontWeight === 'bold' || parseInt(cellComputed.fontWeight) >= 700,
                fontFace: mapFontFace(cellComputed.fontFamily, cell.textContent),
                fontSize: pxToFontSize(cellComputed.fontSize, cell.textContent),
                color: rgbToHex(cellComputed.color),
                align: cellAlign === 'left' || cellAlign === 'right' || cellAlign === 'center' || cellAlign === 'justify' ? cellAlign : 'left',
                valign: valignMap[cellComputed.verticalAlign] || 'middle',
                margin: [
                  pxToPoints(cellComputed.paddingLeft),
                  pxToPoints(cellComputed.paddingRight),
                  pxToPoints(cellComputed.paddingBottom),
                  pxToPoints(cellComputed.paddingTop)
                ]
              };
              const bgc = cellComputed.backgroundColor;
              if (bgc && bgc !== 'rgba(0, 0, 0, 0)' && bgc !== 'transparent') {
                const cellT = extractAlpha(bgc); // null when opaque, else 0..100
                // Skip near-invisible tints (alpha < 0.08 → transparency > 92).
                // Otherwise a `background: rgba(44,62,93,0.05)` row tint would
                // render as a SOLID indigo cell because rgbToHex drops alpha.
                if (cellT === null || cellT < 92) {
                  cellOpts.fill = { color: rgbToHex(bgc) };
                  if (cellT !== null) cellOpts.fill.transparency = cellT;
                }
              }
              // Colspan / rowspan
              const colspan = parseInt(cell.getAttribute('colspan')) || 1;
              const rowspan = parseInt(cell.getAttribute('rowspan')) || 1;
              if (colspan > 1) cellOpts.colspan = colspan;
              if (rowspan > 1) cellOpts.rowspan = rowspan;
              return { text: cell.textContent.replace(/\s+/g, ' ').trim(), options: cellOpts };
            });
            rows.push(rowOut);
          }
          if (rows.length > 0) {
            // Border defaults from computed styles
            const borderColor = tableComputed.borderTopColor && tableComputed.borderTopColor !== 'rgba(0, 0, 0, 0)'
              ? rgbToHex(tableComputed.borderTopColor)
              : 'CCCCCC';
            const borderPt = Math.max(0.25, pxToPoints(tableComputed.borderTopWidth) || 0.5);
            elements.push({
              type: 'table',
              rows,
              colWidths,
              tableBorder: { type: 'solid', color: borderColor, pt: borderPt },
              zIndex: getEffectiveZIndex(el),
              position: rectPosition(rect),
              style: {
                fontSize: pxToFontSize(tableComputed.fontSize, el.textContent),
                fontFace: mapFontFace(tableComputed.fontFamily, el.textContent),
                color: rgbToHex(tableComputed.color)
              }
            });
            processed.add(el);
            el.querySelectorAll('*').forEach(child => processed.add(child));
            return;
          }
        }
      }

      // Extract container elements with backgrounds/borders as shapes.
      // Some badge/pill labels are authored as standalone spans (e.g.
      // <span class="num-tag">PRINCIPLE 01</span>). They are not block
      // containers, but their background is a real visual shape and must be
      // emitted before the text.
      const isStandaloneInlineShape = inlineAsBlockTags.has(el.tagName) &&
        !el.closest('p,h1,h2,h3,h4,h5,h6,li,ul,ol');
      const isContainer = blockContainerTags.has(el.tagName) || isStandaloneInlineShape;
      if (isContainer) {
        const computed = window.getComputedStyle(el);
        const isSlideCanvasElement = el === slideRoot;
        // background-clip:text uses the element background as glyph paint.
        // Exporting it as a normal shape/image creates a visible gradient box
        // around KPI numbers and headings, so only the text extractor may use it.
        const isTextClippedBackground = hasTextBackgroundClip(computed);
        let hasBg = !isTextClippedBackground && computed.backgroundColor && computed.backgroundColor !== 'rgba(0, 0, 0, 0)';
        let bgFillValue = hasBg ? computed.backgroundColor : null;  // rgb/rgba/#hex string

        // Check for background images on shapes.
        //   - Linear gradients → emit a multi-stop gradient fill object that pptxgenjs
        //     accepts (best effort; pptxgenjs gradient support is partial).
        //   - Radial / conic / repeating gradients → fall back to a representative
        //     color stop (no first-class radial support in PPTX shape fill).
        //   - url() background images → emit a SEPARATE image element layered under
        //     this shape (so the texture is preserved instead of dropped silently).
        const bgImage = computed.backgroundImage;
        // Capture extracted gradient data for richer fill output below
        let gradientFill = null;
        // When a gradient has only translucent stops (e.g. a "scrim" overlay
        // like rgba(0,0,0,0.45)→rgba(0,0,0,0)), carry an average transparency
        // so the solid fallback still reads as a tint rather than an opaque mask.
        let gradientTransparency = null;
        if (!isTextClippedBackground && bgImage && bgImage !== 'none') {
          const isLinear = /^linear-gradient/.test(bgImage);
          const isOtherGradient = /^(repeating-)?(linear|radial|conic)-gradient/.test(bgImage) && !isLinear;
          // Collect all url() entries from possibly multi-layer backgroundImage
          const urlMatches = [...bgImage.matchAll(/url\(["']?([^"')]+)["']?\)/g)].map(m => m[1]);
          const hostBgRect = el.getBoundingClientRect();
          const gradientDataUrl = renderLinearGradientBackground(bgImage, hostBgRect.width, hostBgRect.height);
          if (gradientDataUrl && hostBgRect.width > 0 && hostBgRect.height > 0) {
            const gradientImg = {
              type: 'image',
              src: gradientDataUrl,
              objectFit: 'fill',
              zIndex: getEffectiveZIndex(el),
              position: rectPosition(hostBgRect)
            };
            const gradientOpacityT = computeTransparency(null, computed.opacity);
            if (gradientOpacityT !== null) gradientImg.transparency = gradientOpacityT;
            elements.push(gradientImg);
          }

          if (isLinear && !gradientDataUrl) {
            // Parse the angle (e.g. "linear-gradient(135deg, ...)" or "to right, ...")
            const linearMatch = bgImage.match(/linear-gradient\(\s*([^,]+),(.*)\)/);
            let angle = 90; // default top-to-bottom
            if (linearMatch) {
              const head = linearMatch[1].trim();
              const angleM = head.match(/(-?[\d.]+)deg/);
              if (angleM) angle = ((parseFloat(angleM[1]) % 360) + 360) % 360;
              else if (/to\s+right/.test(head)) angle = 90;
              else if (/to\s+left/.test(head)) angle = 270;
              else if (/to\s+bottom/.test(head)) angle = 180;
              else if (/to\s+top/.test(head)) angle = 0;
              else if (/to\s+bottom\s+right/.test(head)) angle = 135;
              else if (/to\s+top\s+right/.test(head)) angle = 45;
              else if (/to\s+bottom\s+left/.test(head)) angle = 225;
              else if (/to\s+top\s+left/.test(head)) angle = 315;
            }
            const colorTokens = bgImage.match(/(rgba?\([^)]+\)|hsla?\([^)]+\)|#[0-9a-fA-F]{3,8})/g) || [];
            if (colorTokens.length >= 2) {
              // pptxgenjs (v4) does NOT support shape gradient fills via the
              // {type:'gradient',angle,stops} structure — passing it as `fill`
              // silently emits a shape with no fill at all. That hid the
              // semi-transparent overlay panel on cover slides, leaving only
              // the slide-canvas-level gradient (resolved to a single solid
              // hex below) to fill the entire slide. Until pptxgenjs grows
              // proper gradient support, fall back to a representative solid:
              //   - opaque stop → use that color directly
              //   - all stops have alpha → carry the average alpha as
              //     transparency so a "fade" still reads as a translucent panel
              const stops = colorTokens.map(tok => ({
                hex: rgbToHex(tok),
                t: extractAlpha(tok) || 0  // 0..100 transparency
              }));
              const opaqueStop = stops.find(s => s.t === 0);
              const translucentStop = stops.find(s => s.t > 0);
              // Mixed-alpha gradient (directional fade between opaque and
              // translucent stops, e.g. a "scrim" that fades from solid beige
              // on the left to translucent on the right so a backdrop image
              // bleeds through): a single opaque solid would hide whatever
              // sits under the faded side. Use the average alpha across stops
              // so the resulting flat panel still lets the underlying layer
              // partly show through.
              const mixedAlpha = opaqueStop && translucentStop;
              const repStop = (opaqueStop && !mixedAlpha) ? opaqueStop : stops[Math.floor(stops.length / 2)];
              gradientFill = null;  // intentionally not emitted
              hasBg = true;
              bgFillValue = '#' + repStop.hex;
              if (!opaqueStop || mixedAlpha) {
                // All-translucent OR mixed gradient: carry the average alpha
                // as transparency so the panel reads as a tint instead of an
                // opaque mask that hides everything underneath.
                gradientTransparency = Math.round(
                  stops.reduce((acc, s) => acc + s.t, 0) / stops.length
                );
              }
            }
          } else if (isOtherGradient) {
            const rgbStops = bgImage.match(/rgba?\([^)]+\)/g);
            const hexStops = bgImage.match(/#[0-9a-fA-F]{3,8}\b/g);
            let picked = null;
            if (rgbStops && rgbStops.length > 0) {
              picked = rgbStops[Math.floor(rgbStops.length / 2)];
            } else if (hexStops && hexStops.length > 0) {
              picked = hexStops[Math.floor(hexStops.length / 2)];
            }
            if (picked) {
              hasBg = true;
              bgFillValue = picked;
            }
          }

          // Also emit url() bg images as their own image layer. Use the same
          // z-index as the host element (not z-1): in CSS a div's url()
          // background paints ON TOP of the parent's background-color but
          // below child content. Subtracting 1 makes the image render BELOW
          // sibling shapes that sit at z=0 (e.g. a parent panel with a solid
          // background-color), hiding the image entirely. Insertion order
          // ensures it still lands above the parent's shape (which was pushed
          // earlier when we visited the parent element).
          if (urlMatches.length > 0 && !isSlideCanvasElement) {
            const r = hostBgRect;
            // Forward host element's opacity to the bg image. Decorative bg
            // images often rely on `opacity: 0.2` (or a radial mask-image) to
            // fade visually into the page; without forwarding opacity, the
            // image dominates the slide as a sharp full-strength rectangle.
            // We can't replicate `mask-image: radial-gradient(...)` exactly,
            // but a uniformly translucent image is a much closer match than
            // a fully opaque one.
            const bgImgT = computeTransparency(null, computed.opacity);
            for (const u of urlMatches) {
              if (r.width > 0 && r.height > 0) {
                const imgEl = {
                  type: 'image',
                  src: u,
                  objectFit: computed.backgroundSize === 'contain' ? 'contain' : 'cover',
                  objectPosition: computed.backgroundPosition,
                  zIndex: getEffectiveZIndex(el),
                  position: rectPosition(r)
                };
                if (bgImgT !== null) imgEl.transparency = bgImgT;
                elements.push(imgEl);
              }
            }
          }
        }

        // Check for borders - both uniform and partial
        const borderTop = computed.borderTopWidth;
        const borderRight = computed.borderRightWidth;
        const borderBottom = computed.borderBottomWidth;
        const borderLeft = computed.borderLeftWidth;
        const borders = [borderTop, borderRight, borderBottom, borderLeft].map(b => parseFloat(b) || 0);
        const hasBorder = borders.some(b => b > 0);
        const borderColors = [
          computed.borderTopColor,
          computed.borderRightColor,
          computed.borderBottomColor,
          computed.borderLeftColor
        ];
        const isTransparentBorderColor = (c) => {
          const v = String(c || '').trim().toLowerCase();
          return v === 'transparent' || extractAlpha(v) === 100;
        };
        // CSS triangles are commonly authored as width/height:0 plus large
        // transparent side borders and one colored border. Rendering those as
        // four PPT border lines creates huge white/gold blocks. They are
        // decorative shape construction, not real borders.
        const cssBoxW = parseFloat(computed.width) || 0;
        const cssBoxH = parseFloat(computed.height) || 0;
        const contentBoxTriangle = cssBoxW <= 0.5 && cssBoxH <= 0.5;
        const borderBoxTriangle =
          Math.abs(cssBoxW - (borders[1] + borders[3])) <= 1 &&
          Math.abs(cssBoxH - (borders[0] + borders[2])) <= 1;
        const isCssBorderTriangle =
          (contentBoxTriangle || borderBoxTriangle) &&
          borders.filter(b => b > 0).length >= 2 &&
          borderColors.some(isTransparentBorderColor) &&
          borderColors.some(c => !isTransparentBorderColor(c));
        const hasExportableBorder = hasBorder && !isCssBorderTriangle;
        const hasUniformBorder = hasExportableBorder && borders.every(b => b === borders[0]);
        const borderLines = [];

        if (hasExportableBorder && !hasUniformBorder) {
          const rect = el.getBoundingClientRect();
          const pos = rectPosition(rect);
          const x = pos.x;
          const y = pos.y;
          const w = pos.w;
          const h = pos.h;

          // Helper: map border-style to PPT dash type
          const styleToDash = (s) => s === 'dashed' ? 'dash' : s === 'dotted' ? 'dot' : 'solid';

          // Collect lines to add after shape (inset by half the line width to center on edge)
          if (parseFloat(borderTop) > 0) {
            const widthPt = pxToPoints(borderTop);
            const inset = (widthPt / 72) / 2; // Convert points to inches, then half
            borderLines.push({
              type: 'line',
              x1: x, y1: y + inset, x2: x + w, y2: y + inset,
              width: widthPt,
              color: rgbToHex(computed.borderTopColor),
              dashType: styleToDash(computed.borderTopStyle)
            });
          }
          if (parseFloat(borderRight) > 0) {
            const widthPt = pxToPoints(borderRight);
            const inset = (widthPt / 72) / 2;
            borderLines.push({
              type: 'line',
              x1: x + w - inset, y1: y, x2: x + w - inset, y2: y + h,
              width: widthPt,
              color: rgbToHex(computed.borderRightColor),
              dashType: styleToDash(computed.borderRightStyle)
            });
          }
          if (parseFloat(borderBottom) > 0) {
            const widthPt = pxToPoints(borderBottom);
            const inset = (widthPt / 72) / 2;
            borderLines.push({
              type: 'line',
              x1: x, y1: y + h - inset, x2: x + w, y2: y + h - inset,
              width: widthPt,
              color: rgbToHex(computed.borderBottomColor),
              dashType: styleToDash(computed.borderBottomStyle)
            });
          }
          if (parseFloat(borderLeft) > 0) {
            const widthPt = pxToPoints(borderLeft);
            const inset = (widthPt / 72) / 2;
            borderLines.push({
              type: 'line',
              x1: x + inset, y1: y, x2: x + inset, y2: y + h,
              width: widthPt,
              color: rgbToHex(computed.borderLeftColor),
              dashType: styleToDash(computed.borderLeftStyle)
            });
          }
        }

        if ((hasBg && !isSlideCanvasElement) || hasExportableBorder) {
          const rect = el.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            const shadow = parseBoxShadow(computed.boxShadow);

            // Only add shape if there's background or uniform border
            if (hasBg || hasUniformBorder) {
              // gradientFill is currently always null (pptxgenjs cannot render
              // shape gradients); the gradient parser populates bgFillValue
              // with a representative solid hex. We may also have a
              // gradientTransparency for "all-translucent" overlays.
              let fillOut;
              let fillTransparency = null;
              if (gradientFill) {
                fillOut = gradientFill;
              } else if (hasBg) {
                fillOut = bgFillValue.startsWith('#')
                  ? bgFillValue.substring(1).toUpperCase()
                  : rgbToHex(bgFillValue);
                // Combine bg color alpha with the container's CSS opacity so a
                // 5%-opaque card panel renders as a faded panel in PPT, not solid.
                fillTransparency = computeTransparency(bgFillValue, computed.opacity);
                if (gradientTransparency !== null) {
                  // Prefer the average gradient alpha when present (the bg
                  // color itself is the rep stop, often opaque on its own).
                  fillTransparency = gradientTransparency;
                }
              } else {
                fillOut = null;
              }

              // Determine shape kind: ellipse for ~square boxes with border-radius >= 50%
              const radiusStr = computed.borderRadius || '0';
              const radiusVal = parseFloat(radiusStr) || 0;
              const isAlmostSquare = Math.abs(rect.width - rect.height) < 2;
              const isFullRound = radiusStr.includes('%') && radiusVal >= 50;
              const shapeKind = (isAlmostSquare && isFullRound) ? 'ellipse' : 'rect';

              // Border styling — pick up dashed / dotted styles too
              let lineSpec = null;
              if (hasUniformBorder) {
                const dashType = computed.borderTopStyle === 'dashed' ? 'dash'
                  : computed.borderTopStyle === 'dotted' ? 'dot' : 'solid';
                lineSpec = {
                  color: rgbToHex(computed.borderColor),
                  width: pxToPoints(computed.borderWidth),
                  dashType
                };
              }

              // No real border but an `inset 0 0 0 Npx COLOR` box-shadow:
              // simulate as a colored stroke. Classic seal/stamp pattern in
              // these decks (`.seal-rect` uses inset shadows to fake a double
              // border around a red square); without this the seal would
              // render as a flat fill with no border, losing the stamp look.
              if (!lineSpec && computed.boxShadow && computed.boxShadow !== 'none' &&
                  /\binset\b/.test(computed.boxShadow)) {
                // Browser serialises each shadow comma-separated. Find the
                // first inset layer that's a uniform border (0 0 0 Npx COLOR).
                const layers = computed.boxShadow.split(/,(?![^()]*\))/);
                for (const layer of layers) {
                  if (!/\binset\b/.test(layer)) continue;
                  const cM = layer.match(/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}/);
                  // Match `0px 0px 0px Npx` (offsets and blur all zero, spread N)
                  const spreadM = layer.match(/0px\s+0px\s+0px\s+([\d.]+)px/);
                  if (cM && spreadM) {
                    const spreadPx = parseFloat(spreadM[1]);
                    if (spreadPx > 0) {
                      lineSpec = {
                        color: rgbToHex(cM[0]),
                        width: pxToPoints(`${spreadPx}px`),
                        dashType: 'solid'
                      };
                      break;
                    }
                  }
                }
              }
              let shapePosition = rectPosition(rect);
              const ownShapeText = normalizeWhitespaceForPpt(el.textContent || '', computed.whiteSpace).trim();
              const shapePadX = (parseFloat(computed.paddingLeft) || 0) + (parseFloat(computed.paddingRight) || 0);
              const shapePadY = (parseFloat(computed.paddingTop) || 0) + (parseFloat(computed.paddingBottom) || 0);
              const isShortPaddedBadgeShape = ownShapeText && ownShapeText.length <= 24 &&
                (shapePadX + shapePadY) > 0 && rect.height <= 48 && rect.width <= 260;
              if (isShortPaddedBadgeShape) {
                let extraX = Math.min(0.025, Math.max(0.012, shapePosition.w * 0.04));
                const extraY = Math.min(0.014, Math.max(0.006, shapePosition.h * 0.06));
                // Horizontal inflation gives an isolated badge visual breathing
                // room, but when badges sit in a tight row (e.g. slide-26
                // HTML/CSS/JS stack pills 6px apart, or slide-27 dep-chips)
                // inflating both facing edges by ~1.5px collapses the gap and the
                // borders look fused. Skip horizontal inflation when a same-row
                // sibling is close; keep the (harmless) vertical inflation.
                try {
                  const sibs = el.parentElement ? Array.from(el.parentElement.children) : [];
                  let minGapPx = Infinity;
                  for (const s of sibs) {
                    if (s === el) continue;
                    const r = s.getBoundingClientRect();
                    const vOverlap = Math.min(rect.bottom, r.bottom) - Math.max(rect.top, r.top);
                    if (vOverlap <= 2) continue; // not on the same row
                    let gap = Infinity;
                    if (r.left >= rect.right) gap = r.left - rect.right;
                    else if (r.right <= rect.left) gap = rect.left - r.right;
                    else continue; // horizontally overlapping — ignore
                    if (gap < minGapPx) minGapPx = gap;
                  }
                  if (Number.isFinite(minGapPx) && minGapPx < 16) extraX = 0;
                } catch (e) { /* keep default extraX */ }
                shapePosition = {
                  x: shapePosition.x - extraX,
                  y: shapePosition.y - extraY,
                  w: shapePosition.w + extraX * 2,
                  h: shapePosition.h + extraY * 2
                };
              }
              if (lineSpec && !isShortPaddedBadgeShape) {
                const strokeInset = (lineSpec.width / 72) / 2;
                const insetX = Math.max(0, Math.min(strokeInset, shapePosition.w / 2 - 0.001));
                const insetY = Math.max(0, Math.min(strokeInset, shapePosition.h / 2 - 0.001));
                if (insetX > 0 || insetY > 0) {
                  shapePosition = {
                    x: shapePosition.x + insetX,
                    y: shapePosition.y + insetY,
                    w: Math.max(0.001, shapePosition.w - insetX * 2),
                    h: Math.max(0.001, shapePosition.h - insetY * 2)
                  };
                }
              }


              // Rotation propagated to shape (so transformed cards rotate correctly)
              const containerRotation = getRotation(computed.transform, computed.writingMode);
              const ownTextForLine = ownShapeText.replace(/\s+/g, '');
              const cssBoxW = el.offsetWidth || parseFloat(computed.width) || 0;
              const cssBoxH = el.offsetHeight || parseFloat(computed.height) || 0;
              const isThinRotatedFillBox = containerRotation !== null && hasBg && !lineSpec &&
                !ownTextForLine && shapeKind === 'rect' && cssBoxW >= 8 && cssBoxH > 0 && cssBoxH <= 4;

              if (isThinRotatedFillBox) {
                const matrixMatch = computed.transform.match(/matrix\(([^)]+)\)/);
                const vals = matrixMatch ? matrixMatch[1].split(',').map(v => parseFloat(v.trim())) : null;
                const angleRad = containerRotation * Math.PI / 180;
                const a = vals && Number.isFinite(vals[0]) ? vals[0] : Math.cos(angleRad);
                const b = vals && Number.isFinite(vals[1]) ? vals[1] : Math.sin(angleRad);
                const c = vals && Number.isFinite(vals[2]) ? vals[2] : -Math.sin(angleRad);
                const d = vals && Number.isFinite(vals[3]) ? vals[3] : Math.cos(angleRad);
                const originParts = String(computed.transformOrigin || '0 0').split(/\s+/);
                const ox = parseFloat(originParts[0]) || 0;
                const oy = parseFloat(originParts[1]) || 0;
                const txPoint = (x0, y0) => ({
                  x: a * (x0 - ox) + c * (y0 - oy) + ox,
                  y: b * (x0 - ox) + d * (y0 - oy) + oy
                });
                const corners = [txPoint(0, 0), txPoint(cssBoxW, 0), txPoint(cssBoxW, cssBoxH), txPoint(0, cssBoxH)];
                const minX = Math.min(...corners.map(p => p.x));
                const minY = Math.min(...corners.map(p => p.y));
                const untransformedLeft = rect.left - minX;
                const untransformedTop = rect.top - minY;
                const p1 = txPoint(0, cssBoxH / 2);
                const p2 = txPoint(cssBoxW, cssBoxH / 2);
                const lineEl = {
                  type: 'line',
                  x1: pxToInch(relX(untransformedLeft + p1.x)),
                  y1: pxToInch(relY(untransformedTop + p1.y)),
                  x2: pxToInch(relX(untransformedLeft + p2.x)),
                  y2: pxToInch(relY(untransformedTop + p2.y)),
                  width: Math.max(0.5, pxToPoints(String(Math.max(1, cssBoxH)) + 'px')),
                  color: fillOut || rgbToHex(bgFillValue),
                  dashType: 'solid',
                  zIndex: getEffectiveZIndex(el)
                };
                if (fillTransparency !== null && fillTransparency !== undefined) lineEl.transparency = fillTransparency;
                elements.push(lineEl);
              } else {
                elements.push({
                  type: 'shape',
                  text: '',  // Shape only - child text elements render on top
                  zIndex: getEffectiveZIndex(el),
                  position: shapePosition,
                  shape: {
                    kind: shapeKind,
                    fill: fillOut,
                    transparency: fillTransparency,
                    line: lineSpec,
                    rotate: containerRotation,
                    // Convert border-radius to rectRadius (in inches)
                    // % values: 50%+ = circle (1), <50% = percentage of min dimension
                    // pt values: divide by 72 (72pt = 1 inch)
                    // px values: divide by 96 (96px = 1 inch)
                    rectRadius: (() => {
                      if (shapeKind === 'ellipse') return 0; // ellipse ignores rectRadius
                      const radius = computed.borderRadius;
                      const radiusValue = parseFloat(radius);
                      if (!Number.isFinite(radiusValue) || radiusValue === 0) return 0;

                      if (radius.includes('%')) {
                        if (radiusValue >= 50) return 1;
                        // Calculate percentage of smaller dimension
                        const minDim = Math.min(rect.width, rect.height);
                        return (radiusValue / 100) * pxToInch(minDim);
                      }

                      if (radius.includes('pt')) return radiusValue / 72;
                      return radiusValue / PX_PER_IN;
                    })(),
                    shadow: shadow
                  }
                });
              }
            }

            // Add partial border lines
            elements.push(...borderLines);

            // If this shape-emitting container carries its own direct text
            // (no block-level child handles it), fall through so that text
            // renders on top of the shape as a separate text frame.
            const BLOCK_TEXT_CHILD_TAGS = new Set([
              'DIV','SECTION','HEADER','FOOTER','ARTICLE','ASIDE','MAIN','NAV','FIGURE',
              'P','H1','H2','H3','H4','H5','H6','UL','OL','LI','TABLE','BLOCKQUOTE',
              'FIGCAPTION','DT','DD'
            ]);
            const hasBlockTextChild = Array.from(el.children).some(
              c => BLOCK_TEXT_CHILD_TAGS.has(c.tagName) && c.textContent.trim()
            );
            // Also bail if any inline child (span/strong/em/…) carries text —
            // those will be extracted as their own text frame via _treatAsP,
            // so claiming their text here would duplicate it.
            const directText = Array.from(el.childNodes)
              .filter(n => n.nodeType === Node.TEXT_NODE)
              .map(n => n.textContent).join('').trim();
            const hasInlineTextChild = Array.from(el.children).some(
              c => !BLOCK_TEXT_CHILD_TAGS.has(c.tagName) && c.textContent.trim()
            );
            const shouldClaimText = !hasBlockTextChild && (directText || !hasInlineTextChild);
            if (shouldClaimText && el.textContent.trim()) {
              el._treatAsP = true;
              // fall through — don't mark processed, don't return
            } else {
              processed.add(el);
              return;
            }
          }
        } else {
          // No background / no border: treat as a plain text container if it
          // directly holds text with no block-level text descendants.
          const BLOCK_TEXT_CHILD_TAGS = new Set([
            'DIV','SECTION','HEADER','FOOTER','ARTICLE','ASIDE','MAIN','NAV','FIGURE',
            'P','H1','H2','H3','H4','H5','H6','UL','OL','LI','TABLE','BLOCKQUOTE',
            'FIGCAPTION','DT','DD'
          ]);
          const hasBlockTextChild = Array.from(el.children).some(
            c => BLOCK_TEXT_CHILD_TAGS.has(c.tagName) && c.textContent.trim()
          );
          // If any inline child (span/strong/em/…) carries text, it will be
          // extracted as its own text frame via _treatAsP — don't swallow it
          // into the parent unless the parent also has its own direct text.
          const directText = Array.from(el.childNodes)
            .filter(n => n.nodeType === Node.TEXT_NODE)
            .map(n => n.textContent).join('').trim();
          const hasInlineTextChild = Array.from(el.children).some(
            c => !BLOCK_TEXT_CHILD_TAGS.has(c.tagName) && c.textContent.trim()
          );
          const shouldClaimText = !hasBlockTextChild && (directText || !hasInlineTextChild);
          if (shouldClaimText && el.textContent.trim()) {
            el._treatAsP = true;
          }
        }
      }

      // Extract bullet lists as single text block
      if (el.tagName === 'UL' || el.tagName === 'OL') {
        // Skip nested lists — the outer list will already encompass them.
        // Without this guard, an inner <ul> placed inside a parent <ul>'s <li>
        // would emit a second text frame on top of the first, duplicating bullets.
        if (el.parentElement && el.parentElement.closest('ul, ol')) {
          // Mark inner list (and items) processed so they aren't re-handled,
          // but don't emit them as separate frames.
          processed.add(el);
          el.querySelectorAll('*').forEach(c => processed.add(c));
          return;
        }

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

        const isOrdered = el.tagName === 'OL';
        // Only collect direct LI children (so nested lists' items don't bleed in)
        const liElements = Array.from(el.children).filter(c => c.tagName === 'LI');
        const items = [];
        const ulComputed = window.getComputedStyle(el);
        const cssLengthToPoints = (value) => {
          const n = parseFloat(value);
          return Number.isFinite(n) ? n * PT_PER_PX * SCALE : 0;
        };
        const ulPaddingLeftPt = cssLengthToPoints(ulComputed.paddingLeft);
        const isFlexColumnList =
          (ulComputed.display === 'flex' || ulComputed.display === 'inline-flex') &&
          String(ulComputed.flexDirection || '').startsWith('column');
        const flexListGapPt = isFlexColumnList
          ? Math.max(cssLengthToPoints(ulComputed.rowGap), cssLengthToPoints(ulComputed.gap))
          : 0;
        const liMarginBottomPt = liElements.reduce((max, li) => {
          const liStyle = window.getComputedStyle(li);
          return Math.max(max, cssLengthToPoints(liStyle.marginBottom));
        }, 0);

        // Split: margin-left for bullet position, indent for text position
        // margin-left + indent = ul padding-left
        const marginLeft = ulPaddingLeftPt * 0.5;
        const textIndent = ulPaddingLeftPt * 0.5;

        // Detect custom CSS bullets: list-style: none + li::before with a visible
        // background (rendered as a colored circle/square). PptxGenJS only emits
        // a plain <a:buChar char="•"/> with no color control, so a styled CSS
        // bullet would otherwise be lost. Capture the ::before color and emit
        // the bullet as an inline run with that color instead.
        let customBullet = null;
        if (!isOrdered && liElements.length > 0) {
          const firstLi = liElements[0];
          const liStyle = window.getComputedStyle(firstLi);
          const ulStyle = ulComputed;
          const listStyleNone = (liStyle.listStyleType === 'none' && ulStyle.listStyleType === 'none')
                              || liStyle.listStyleType === 'none';
          if (listStyleNone) {
            const before = window.getComputedStyle(firstLi, '::before');
            const beforeContent = before && before.content;
            // ::before is "active" if content is set (even empty string '')
            const hasBefore = beforeContent && beforeContent !== 'none' && beforeContent !== 'normal';
            if (hasBefore) {
              const bg = before.backgroundColor;
              const col = before.color;
              const bgVisible = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
              const colorPick = bgVisible ? bg : col;
              const liFs = pxToFontSize(liStyle.fontSize, firstLi.textContent) || 12;
              customBullet = {
                char: '●', // ● black circle — renders reliably
                color: rgbToHex(colorPick),
                fontSize: Math.max(6, Math.round(liFs * 0.55)),
              };
            }
          }
        }

        liElements.forEach((li, idx) => {
          const isLast = idx === liElements.length - 1;
          const liComputed = window.getComputedStyle(li);
          const liIsFlex = liComputed.display === 'flex' || liComputed.display === 'inline-flex';
          const runs = liIsFlex
            ? [{
                text: applyTextTransform(
                  normalizeWhitespaceForPpt(li.textContent, liComputed.whiteSpace).trim(),
                  liComputed.textTransform
                ),
                options: { breakLine: false }
              }]
            : parseInlineFormatting(li, { breakLine: false });
          // Clean manual bullets/numbering from first run
          if (runs.length > 0) {
            runs[0].text = runs[0].text.replace(/^[•·\-\*▪▸○●◆◇■□]\s*/, '');
            // Strip explicit "1." / "1)" prefixes that authors sometimes type
            runs[0].text = runs[0].text.replace(/^\d+[\.\)]\s+/, '');
            if (customBullet) {
              // Prepend bullet as an inline run with custom color/size and
              // disable the PPT auto-bullet on this paragraph.
              runs.unshift({
                text: customBullet.char + '  ',
                options: {
                  color: customBullet.color,
                  fontSize: customBullet.fontSize,
                  bullet: false,
                }
              });
            } else {
              // PptxGenJS bullet: { type: 'number' } yields auto-numbered list
              runs[0].options.bullet = isOrdered
                ? { type: 'number', indent: textIndent }
                : { indent: textIndent };
            }
          }
          // Set breakLine on last run
          if (runs.length > 0 && !isLast) {
            runs[runs.length - 1].options.breakLine = true;
          }
          items.push(...runs);
        });

        const computed = window.getComputedStyle(liElements[0] || el);
        const taLi = computed.textAlign;
        const alignList = taLi === 'start' ? 'left'
          : taLi === 'end' ? 'right'
          : (taLi === 'left' || taLi === 'right' || taLi === 'center' || taLi === 'justify') ? taLi
          : 'left';
        const listTextPaint = resolveTextPaintStyle(computed, liElements[0] || el);

        elements.push({
          type: 'list',
          items: items,
          zIndex: getEffectiveZIndex(el),
          position: rectPosition(rect),
          style: {
            fontSize: pxToFontSize(computed.fontSize, el.textContent),
            fontFace: mapFontFace(computed.fontFamily, el.textContent),
            color: listTextPaint.color,
            transparency: listTextPaint.transparency,
            align: alignList,
            lineSpacing: computed.lineHeight && computed.lineHeight !== 'normal' ? pxToPoints(computed.lineHeight) : null,
            charSpacing: computed.letterSpacing && computed.letterSpacing !== 'normal' ? pxToPoints(computed.letterSpacing) : undefined,
            paraSpaceBefore: 0,
            paraSpaceAfter: Math.max(cssLengthToPoints(computed.marginBottom), flexListGapPt, liMarginBottomPt),
            _itemCount: liElements.length,
            // PptxGenJS margin array is [left, right, bottom, top]
            margin: [marginLeft, 0, 0, 0]
          }
        });

        liElements.forEach(li => {
          processed.add(li);
          li.querySelectorAll('*').forEach(c => processed.add(c));
        });
        processed.add(el);
        return;
      }

      // If a pre-pass marked this text element as splittable (block-display
      // inline children handled separately), skip extracting it as one frame
      // AND don't mark descendants processed — let each child be emitted on
      // its own with the correct bounding box and per-paragraph line height.
      if (el._skipTextExtraction) {
        processed.add(el);
        return;
      }

      // Elements used as block-level text containers outside of any text tag:
      // 1. Inline elements (span/strong/b/em/i/a/label/code/…) misused as block containers
      // 2. Leaf-block elements (figcaption/dt/dd/td/th/blockquote/…) that directly hold text
      //    — only when they contain no block-text descendants to avoid duplicate extraction
      if (inlineAsBlockTags.has(el.tagName) && !el.closest('p,h1,h2,h3,h4,h5,h6,li')) {
        el._treatAsP = true;
      } else if (leafBlockTags.has(el.tagName) && !el.closest('p,h1,h2,h3,h4,h5,h6,li')) {
        if (!el.querySelector('p,h1,h2,h3,h4,h5,h6,ul,ol')) {
          el._treatAsP = true;
        }
      }

      // Extract text elements (P, H1, H2, etc.)
      if (!textTags.includes(el.tagName) && !el._treatAsP) return;

      let rect = el.getBoundingClientRect();
      const computed = window.getComputedStyle(el);
      let text = normalizeWhitespaceForPpt(el.textContent, computed.whiteSpace).trim();
      if (el._directTextOnly) {
        const directTextNodes = Array.from(el.childNodes).filter(n =>
          n.nodeType === Node.TEXT_NODE && n.textContent.trim()
        );
        text = normalizeWhitespaceForPpt(directTextNodes.map(n => n.textContent).join(' '), computed.whiteSpace).trim();
        const rects = [];
        for (const n of directTextNodes) {
          const range = document.createRange();
          range.selectNodeContents(n);
          const rr = range.getBoundingClientRect();
          if (rr.width > 0 && rr.height > 0) rects.push(rr);
          range.detach?.();
        }
        if (rects.length > 0) {
          const left = Math.min(...rects.map(r => r.left));
          const top = Math.min(...rects.map(r => r.top));
          const right = Math.max(...rects.map(r => r.right));
          const bottom = Math.max(...rects.map(r => r.bottom));
          rect = { left, top, right, bottom, width: right - left, height: bottom - top };
        }
      }
      if (rect.width === 0 || rect.height === 0 || !text) return;

      // Validate: Check for manual bullet symbols in text elements (not in lists)
      if (el.tagName !== 'LI' && /^[•·\-\*▪▸○●◆◇■□]\s/.test(text.trimStart())) {
        warnings.push(
          `Text element <${el.tagName.toLowerCase()}> starts with bullet symbol "${text.substring(0, 20)}...". ` +
          'Use <ul> or <ol> lists instead of manual bullet symbols.'
        );
      }

      let rotation = getRotation(computed.transform, computed.writingMode);
      // CJK vertical-text fix: `writing-mode: vertical-rl/lr` on CJK content
      // should render as upright characters stacked top-to-bottom — that's
      // what the browser shows. The default rotation path rotates the whole
      // text box 90°, which makes Chinese characters lie on their sides
      // (because CJK glyphs are not auto-uprighted in PPT the way the
      // browser uprights them for vertical writing-mode). For Latin text in
      // a vertical writing mode (e.g. `Natural · Aesthetics`), sideways is
      // the conventional rendering — keep the rotation path.
      const isVerticalWM = computed.writingMode === 'vertical-rl' || computed.writingMode === 'vertical-lr';
      let cjkVerticalStack = false;
      if (isVerticalWM && hasCJKChars(text)) {
        const nonSpace = text.replace(/\s/g, '');
        const cjkCount = Array.from(nonSpace).filter(c =>
          /[一-鿿぀-ヿ가-힯]/.test(c)
        ).length;
        if (nonSpace.length > 0 && cjkCount / nonSpace.length >= 0.7) {
          cjkVerticalStack = true;
          rotation = null;  // Skip rotation; rect already has the right (narrow & tall) dims
        }
      }
      const { x, y, w, h } = getPositionAndSize(el, rect, rotation);

      // v3: Detect white-space: nowrap and z-index
      const isRowFlexText = (computed.display === 'flex' || computed.display === 'inline-flex') &&
        !String(computed.flexDirection || 'row').startsWith('column') &&
        text.length <= 32;
      const flexTextRightBound = getFlexTextRightBound(el, rect);
      const isFlexRowTitleText = flexTextRightBound !== null &&
        text.length <= 64 &&
        !el.querySelector('br') &&
        (isMediumOrBold(computed.fontWeight) || pxToFontSize(computed.fontSize, text) >= 8.5);
      const noWrap = computed.whiteSpace === 'nowrap' || computed.whiteSpace === 'pre' ||
        isRowFlexText || isFlexRowTitleText;
      // Effective z-index propagates the highest ancestor z-index down so
      // text inside a z-indexed panel paints above the panel's background.
      const cssZIndex = getEffectiveZIndex(el);

      // text-align mapping — start/end depend on writing direction (assume LTR);
      // pass through left/right/center/justify directly.
      const taRaw = computed.textAlign;
      let alignOut;
      if (taRaw === 'start') alignOut = 'left';
      else if (taRaw === 'end') alignOut = 'right';
      else if (taRaw === 'left' || taRaw === 'right' || taRaw === 'center' || taRaw === 'justify') alignOut = taRaw;
      else alignOut = 'left';

      // Parse text-shadow → run-level glow approximation
      const parseTextShadow = (ts) => {
        if (!ts || ts === 'none') return null;
        const colorM = ts.match(/rgba?\([^)]+\)|hsla?\([^)]+\)|#[0-9a-fA-F]{3,8}/);
        const numM = ts.match(/(-?[\d.]+)px/g);
        if (!numM || numM.length < 2) return null;
        const offsetX = parseFloat(numM[0]);
        const offsetY = parseFloat(numM[1]);
        const blur = numM.length > 2 ? parseFloat(numM[2]) : 0;
        const offset = Math.sqrt(offsetX * offsetX + offsetY * offsetY) * PT_PER_PX;
        const angle = (offsetX === 0 && offsetY === 0) ? 0
          : ((Math.atan2(offsetY, offsetX) * 180 / Math.PI) + 360) % 360;
        return {
          type: 'outer',
          color: colorM ? rgbToHex(colorM[0]) : '000000',
          blur: blur * PT_PER_PX,
          offset,
          angle: Math.round(angle),
          opacity: colorM && extractAlpha(colorM[0]) !== null ? (100 - extractAlpha(colorM[0])) / 100 : 0.5
        };
      };
      const textShadow = parseTextShadow(computed.textShadow);
      const textPaint = resolveTextPaintStyle(computed, el);

      const baseStyle = {
        fontSize: pxToFontSize(computed.fontSize, text),
        fontFace: mapFontFace(computed.fontFamily, text),
        color: textPaint.color,
        align: alignOut,
        charSpacing: computed.letterSpacing && computed.letterSpacing !== 'normal' ? pxToPoints(computed.letterSpacing) : undefined,
        lineSpacing: computed.lineHeight && computed.lineHeight !== 'normal' ? pxToPoints(computed.lineHeight) : null,
        paraSpaceBefore: pxToPoints(computed.marginTop),
        paraSpaceAfter: pxToPoints(computed.marginBottom),
        // PptxGenJS margin array is [left, right, bottom, top] (not [top, right, bottom, left] as documented)
        margin: [
          pxToPoints(computed.paddingLeft),
          pxToPoints(computed.paddingRight),
          pxToPoints(computed.paddingBottom),
          pxToPoints(computed.paddingTop)
        ]
      };
      // _fontSizeClampRatio: >1 when the source font-size was clamped up to
      // MIN_FONT_SIZE_PT. The browser laid the box out using the smaller
      // intended font, so PPT lines are taller than the box can hold —
      // addElements scales the text frame height by this ratio to compensate.
      baseStyle._fontSizeClampRatio = fontSizeClampRatio(computed.fontSize, text);
      // Merged inline row (big number + small tail on one baseline): the parent
      // div's own line-height is sized for its small inherited font, so forcing
      // it as the paragraph line spacing crushes the large child run's line box
      // and the tall glyph overflows upward over the element above. Size the line
      // spacing to the tallest child run instead (its own line-height ≈ 1).
      if (el._mergeInlineRow) {
        let maxChildFsPt = 0;
        el.querySelectorAll('*').forEach((c) => {
          if (!c.textContent || !c.textContent.trim()) return;
          const fsPt = pxToFontSize(window.getComputedStyle(c).fontSize, c.textContent);
          if (fsPt > maxChildFsPt) maxChildFsPt = fsPt;
        });
        baseStyle.lineSpacing = maxChildFsPt > 0 ? maxChildFsPt : null;
      }
      // Hints consumed by addElements (prefixed with _ so they don't accidentally
      // pass through to PptxGenJS textOptions):
      // - _hasBrBreaks: element contains <br>; pptxgenjs would otherwise apply
      //   paraSpaceBefore/After to each line-broken paragraph, inflating the gap.
      // - _centerInFrame: element uses grid/flex centering (place-items:center
      //   etc.) — text should be vertically AND horizontally centered in its frame
      //   (think single-character circular badges like .teacher / .thumb-num).
      // - _hasContainerPadding: element has its own horizontal padding (i.e. is
      //   a padded box that also drew a shape behind itself). Width compensation
      //   would push the text frame past the shape edge, causing visible overflow.
      baseStyle._hasBrBreaks = !!el.querySelector('br');
      const isGridCenter = computed.display === 'grid'
        && computed.alignItems === 'center'
        && (computed.justifyItems === 'center' || computed.justifyContent === 'center');
      const isFlexCenter = (computed.display === 'flex' || computed.display === 'inline-flex')
        && computed.alignItems === 'center'
        && computed.justifyContent === 'center';
      baseStyle._centerInFrame = isGridCenter || isFlexCenter;
      const padLpx = parseFloat(computed.paddingLeft) || 0;
      const padRpx = parseFloat(computed.paddingRight) || 0;
      baseStyle._hasContainerPadding = (padLpx + padRpx) > 1;
      const textIsIconOnly = isIconOnlyText(text);
      if (textIsIconOnly) {
        baseStyle.fontFace = _fc.symbol || "Segoe UI Symbol";
        baseStyle.lineSpacing = null;
        baseStyle.margin = [0, 0, 0, 0];
        // An inline lead-in glyph (e.g. slide-27 dep-chip "→" before the label)
        // has a following inline sibling that carries text. Centering it inside
        // its own tight frame both wastes the natural margin before the label and
        // risks a right-bleed collision. Left-anchor so the glyph stays at its
        // measured x and the ~margin gap to the following text is preserved.
        let inlineLeadGlyph = false;
        try {
          const sib = el.nextSibling;
          inlineLeadGlyph = !!(sib && (
            (sib.nodeType === 3 && sib.textContent.trim().length > 0) ||
            (sib.nodeType === 1 && (sib.textContent || '').trim().length > 0)));
        } catch (e) { /* default false */ }
        if (inlineLeadGlyph) {
          baseStyle.align = "left";
          baseStyle._inlineLeadGlyph = true;
        } else {
          baseStyle.align = "center";
        }
      }
      baseStyle._isIcon = textIsIconOnly;
      baseStyle._clipBounds = getNearestTextClipBounds(el);
      const nextFlowTextTopBound = getNextFlowTextTopBound(el, rect);
      if (nextFlowTextTopBound !== null) baseStyle._nextTextTopBound = nextFlowTextTopBound;
      if (flexTextRightBound !== null) baseStyle._preferredRightBound = flexTextRightBound;
      const isShortPaddedBadgeText = baseStyle._hasContainerPadding &&
        text.length <= 24 &&
        rect.height <= 48 &&
        (computed.whiteSpace === 'nowrap' || (parseFloat(computed.borderRadius) || 0) > 0);
      // A compound inline chip has BOTH a child element that renders as its own
      // box AND a direct text node (e.g. slide-27 dep-chip:
      // `<span class="arrow">→</span>Order Processing`). Its two pieces sit
      // side-by-side on one line, so centering the text piece inside its own
      // tight, wrap:none frame makes it bleed leftward and collide with the
      // preceding arrow glyph. Keep such text left-anchored.
      const isCompoundInline = (() => {
        try {
          const hasChildText = Array.from(el.children || []).some(c => (c.textContent || '').trim().length > 0);
          const hasDirectText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
          return hasChildText && hasDirectText;
        } catch (e) { return false; }
      })();
      if (isShortPaddedBadgeText) {
        // The measured badge rect already includes CSS padding. Re-applying
        // that padding as PPT text inset leaves very little usable width for
        // compact labels such as T1/T2/T3/T4 — zero it either way.
        baseStyle._zeroTextInset = true;
        baseStyle.margin = [0, 0, 0, 0];
        if (!isCompoundInline) {
          baseStyle._centerInFrame = true;
          if (baseStyle.align === 'left') baseStyle.align = 'center';
        }
      }
      if (textShadow) baseStyle.shadow = textShadow;

      // Combine color alpha + element opacity. The watermark span case in
      // 五粮液 cover.html is the canonical example: color is opaque rgb(...) but
      // opacity is 0.05, so without folding opacity in, the giant character
      // renders at full strength in PowerPoint.
      if (textPaint.transparency !== null) baseStyle.transparency = textPaint.transparency;

      if (rotation !== null) baseStyle.rotate = rotation;

      const pushInlineBackgroundShapes = () => {
        const inlineNodes = Array.from(el.querySelectorAll("span,mark,b,strong,i,em,u,a,code,small,big,label"));
        for (const node of inlineNodes) {
          const nodeStyle = window.getComputedStyle(node);
          const nodeBg = nodeStyle.backgroundColor;
          const hasNodeBg = nodeBg && nodeBg !== "rgba(0, 0, 0, 0)" && nodeBg !== "transparent";
          if (!hasNodeBg) continue;
          const nodeRect = node.getBoundingClientRect();
          if (nodeRect.width <= 0 || nodeRect.height <= 0) continue;
          const radius = nodeStyle.borderRadius || "0";
          const radiusValue = parseFloat(radius) || 0;
          let rectRadius = 0;
          if (radiusValue > 0) {
            if (radius.includes("%")) rectRadius = (Math.min(nodeRect.width, nodeRect.height) * radiusValue / 100) / PX_PER_IN;
            else if (radius.includes("pt")) rectRadius = radiusValue / 72;
            else rectRadius = radiusValue / PX_PER_IN;
          }
          elements.push({
            type: "shape",
            text: "",
            zIndex: cssZIndex,
            position: rectPosition(nodeRect),
            shape: {
              kind: "rect",
              fill: rgbToHex(nodeBg),
              transparency: computeTransparency(nodeBg, nodeStyle.opacity),
              line: null,
              rectRadius
            }
          });
        }
      };
      pushInlineBackgroundShapes();

      let textPosition = { x: pxToInch(relX(x)), y: pxToInch(relY(y)), w: pxToInch(w), h: pxToInch(h) };
      if (textIsIconOnly && baseStyle._centerInFrame && rotation === null) {
        const fsPx = parseFloat(computed.fontSize) || Math.min(rect.width, rect.height);
        const lineHeightPx = computed.lineHeight && computed.lineHeight !== "normal" ? parseFloat(computed.lineHeight) : fsPx * 1.2;
        const iconBoxPx = Math.max(1, Math.min(Math.min(rect.width, rect.height), Math.max(fsPx, lineHeightPx)));
        const iconRect = {
          left: rect.left + (rect.width - iconBoxPx) / 2,
          top: rect.top + (rect.height - iconBoxPx) / 2,
          width: iconBoxPx,
          height: iconBoxPx
        };
        textPosition = rectPosition(iconRect);
      }

      // Look for richer inline formatting too — links, sub/sup, code, mark, strike
      const hasFormatting = !el._directTextOnly && el.querySelector('b, i, u, strong, em, span, br, a, sub, sup, s, del, strike, mark, code, small, big');

      if (hasFormatting) {
        // Text with inline formatting
        const transformStr = computed.textTransform;
        const baseTextDecoration = computed.textDecoration || "";
        const baseRunOptions = {
          fontSize: baseStyle.fontSize,
          fontFace: baseStyle.fontFace,
          color: baseStyle.color,
          charSpacing: baseStyle.charSpacing,
          transparency: baseStyle.transparency,
          bold: shouldApplyPptBold(computed.fontWeight) && !shouldSkipBold(computed.fontFamily),
          italic: computed.fontStyle === "italic",
          underline: baseTextDecoration.includes("underline"),
          strike: baseTextDecoration.includes("line-through")
        };
        const runs = parseInlineFormatting(el, baseRunOptions, [], (str) => applyTextTransform(str, transformStr));

        // Adjust lineSpacing based on largest fontSize in runs.
        const adjustedStyle = { ...baseStyle };
        if (adjustedStyle.lineSpacing && adjustedStyle.fontSize) {
          const maxFontSize = Math.max(
            adjustedStyle.fontSize,
            ...runs.map(r => r.options?.fontSize || 0)
          );
          const lineHeightMultiplier = adjustedStyle.lineSpacing / adjustedStyle.fontSize;
          if (maxFontSize > adjustedStyle.fontSize) {
            // CAP the inflation. The old behaviour (`maxFontSize * multiplier`)
            // blew up the global spacing to fit the *largest* inline run —
            // an inline 88px `.qmark` inside a 32px pullquote would push every
            // body line 2.7× apart, dragging text past the box bottom and into
            // the columns/footer below. Capping at 1.5× of the base prevents
            // the body lines from being yanked apart, while still giving the
            // big run enough room to not crowd its neighbours.
            const cappedMax = Math.min(maxFontSize, adjustedStyle.fontSize * 1.5);
            adjustedStyle.lineSpacing = cappedMax * lineHeightMultiplier;
            // Additionally publish a percent-based fallback so PPT viewers
            // that honour `<a:spcPct>` per-paragraph can give each paragraph
            // line spacing proportional to its own font. (pptxgenjs only
            // applies this when `lineSpacing` is unset, so it's a no-op for
            // the primary code path, but persists as a downstream hint.)
            adjustedStyle.lineSpacingMultiple = lineHeightMultiplier;
          }
        }

        elements.push({
          type: el._treatAsP ? 'p' : el.tagName.toLowerCase(),
          text: runs,
          noWrap,
          zIndex: cssZIndex,
          position: textPosition,
          style: adjustedStyle
        });
      } else {
        // Plain text - inherit CSS formatting
        const textTransform = computed.textTransform;
        let transformedText = applyTextTransform(text, textTransform);

        // CJK vertical text: use native PowerPoint East Asian vertical
        // layout. The old fallback emitted one character per paragraph; that
        // made spaces around separators become blank lines and could overflow
        // short vertical labels such as "千年汴梁 · 梵音塔影".
        const cjkStyle = { ...baseStyle };
        if (cjkVerticalStack) {
          transformedText = transformedText.trim();
          cjkStyle._pptxVert = "eaVert";
          cjkStyle._allowWrap = true;
          cjkStyle.align = "center";
          cjkStyle._centerInFrame = true;
        }

        const isBold = shouldApplyPptBold(computed.fontWeight);
        const td = computed.textDecoration || "";
        const plainStyle = {
          ...cjkStyle,
          bold: isBold && !shouldSkipBold(computed.fontFamily),
          italic: computed.fontStyle === "italic",
          underline: td.includes("underline"),
          strike: td.includes("line-through")
        };
        if (isMediumOrBold(computed.fontWeight) && shouldUseEmphasisFont(transformedText)) plainStyle.fontFace = _fc.emphasis || "Liberation Sans Narrow";
        const fontRuns = splitTextIntoFontRuns(transformedText, plainStyle);

        elements.push({
          type: el._treatAsP ? "p" : el.tagName.toLowerCase(),
          text: fontRuns || transformedText,
          noWrap,
          zIndex: cssZIndex,
          position: textPosition,
          style: plainStyle
        });
      }

      processed.add(el);
      // Also mark descendants as processed so their spans/inline elements
      // aren't re-extracted as separate text frames. When direct text was
      // split from block-display children, those children still need their
      // own pass below.
      if (!el._directTextOnly) el.querySelectorAll('*').forEach(d => processed.add(d));
    });

    return { background, elements, placeholders, errors, warnings, notes };
  }, slideDims);
}

async function html2pptx(htmlFile, pres, options = {}) {
  const {
    tmpDir = process.env.TMPDIR || '/tmp',
    slide = null,
    fontConfig = null  // { cjk, latin, emphasis, display, symbol }
  } = options;
  const effectiveFontConfig = { ...DEFAULT_FONT_CONFIG, ...(fontConfig || {}) };

  try {
    // Use Chrome on macOS, default Chromium on Unix
    const launchOptions = { env: { TMPDIR: tmpDir } };
    if (process.platform === 'darwin') {
      launchOptions.channel = 'chrome';
    }

    const browser = await chromium.launch(launchOptions);

    let bodyDimensions;
    let slideData;

    const filePath = path.isAbsolute(htmlFile) ? htmlFile : path.join(process.cwd(), htmlFile);
    try {
      const page = await browser.newPage();
      page.on('console', (msg) => {
        // Log the message text to your test runner's console
        console.log(`Browser console: ${msg.text()}`);
      });

      // External web-font CSS can block parser-executed scripts and keep
      // DOMContentLoaded from firing. Fonts are mapped to PPT-safe faces later,
      // so remote font downloads must not block conversion.
      //
      // CRITICAL: A local <link href="global.css"> whose file starts with
      // `@import url(<remote-font-css>)` will NOT apply ANY of its own rules
      // until every pending remote @import resolves or errors. Chromium keeps
      // those @import stylesheet requests pending indefinitely on file:// pages
      // under waitUntil:'domcontentloaded', so the local stylesheet's rules
      // (.slide { height:720px }, :root { --accent } …) never take effect — the
      // slide collapses to height 0, backgrounds/colors vanish, and
      // justify-center content is pushed to negative Y. To avoid this we
      // short-circuit ALL remote requests by resource type:
      //   - stylesheet → fulfill empty CSS immediately (unblocks local sheets;
      //                  fonts are remapped to PPT-safe faces downstream anyway)
      //   - font       → abort (never needed for layout/measurement)
      //   - script     → allow (e.g. cdn.tailwindcss.com — required for layout)
      //   - image/other→ allow (remote images may be real slide content)
      try {
        await page.route(/^https?:\/\//i, async (route) => {
          let type = '';
          try { type = route.request().resourceType(); } catch (e) { /* ignore */ }
          try {
            if (type === 'stylesheet') {
              await route.fulfill({ status: 200, contentType: 'text/css', body: '' });
            } else if (type === 'font') {
              await route.abort();
            } else {
              await route.continue();
            }
          } catch (e) {
            try { await route.abort(); } catch (e2) { /* ignore */ }
          }
        });
      } catch (e) { /* ignore */ }

      // Use 'domcontentloaded' to avoid hanging on slow/absent CDN resources
      // (Google Fonts, Tailwind JIT). Then give fonts/JIT a chance to apply.
      await page.goto(`file://${filePath}`, { waitUntil: 'domcontentloaded', timeout: 120000 });

      // Inject font config into the page for extractSlideData to use
      await page.evaluate((fc) => { window.__FONT_CONFIG__ = fc; }, effectiveFontConfig);

      // domcontentloaded does NOT wait for <link rel="stylesheet"> resources, so
      // local stylesheets like ./global.css may not be applied yet. Explicitly
      // wait for each link element's sheet to be available, with a per-link
      // timeout so remote/CDN stylesheets that hang don't block the whole run.
      try {
        await page.evaluate(async () => {
          const links = Array.from(document.querySelectorAll('link[rel~="stylesheet"]'));
          await Promise.all(links.map((link) => {
            // .sheet is non-null once the CSS has been parsed.
            if (link.sheet) return Promise.resolve();
            return new Promise((resolve) => {
              const done = () => resolve();
              link.addEventListener('load', done, { once: true });
              link.addEventListener('error', done, { once: true });
              // Per-link timeout (ms): same-origin file:// CSS should resolve
              // almost instantly; this caps wait for slow CDN links.
              setTimeout(done, 3000);
            });
          }));
        });
      } catch (e) { /* ignore */ }

      // Wait for web fonts to settle (Google Fonts etc.) and Tailwind JIT to emit styles.
      // document.fonts.ready resolves once all @font-face loads have completed or failed.
      try {
        await page.evaluate(() => {
          if (!document.fonts || !document.fonts.ready) return null;
          return Promise.race([
            document.fonts.ready,
            new Promise((resolve) => setTimeout(resolve, 3000))
          ]);
        });
      } catch (e) { /* ignore */ }
      // Tailwind Play CDN observes DOM and injects styles asynchronously on first paint.
      // When it is present, prefer waiting for utility classes to actually affect
      // computed styles instead of blindly falling back to unstyled layout.
      try {
        await page.evaluate(async () => {
          const hasTailwindCdn = Array.from(document.scripts || []).some(s => /cdn\.tailwindcss\.com/i.test(s.src || ''));
          if (!hasTailwindCdn) return;

          const classTokens = (el) => String(el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
          const tailwindLooksActive = () => {
            const nodes = Array.from(document.querySelectorAll('[class]'));
            for (const el of nodes) {
              const cs = getComputedStyle(el);
              const tokens = classTokens(el);
              if (tokens.includes('absolute') && cs.position === 'absolute') return true;
              if (tokens.includes('flex') && cs.display === 'flex') return true;
              if (tokens.includes('grid') && cs.display === 'grid') return true;
              if (tokens.some(t => /^top-\[/.test(t)) && cs.top !== 'auto') return true;
              if (tokens.some(t => /^right-\[/.test(t)) && cs.right !== 'auto') return true;
              if (tokens.includes('-translate-y-1/2') && cs.transform && cs.transform !== 'none') return true;
            }
            return false;
          };

          if (tailwindLooksActive()) return;
          const deadline = Date.now() + 5000;
          await new Promise((resolve) => {
            const tick = () => {
              if (tailwindLooksActive() || Date.now() >= deadline) resolve();
              else requestAnimationFrame(tick);
            };
            tick();
          });
        });
      } catch (e) { /* ignore */ }
      await page.waitForTimeout(200);

      bodyDimensions = await getBodyDimensions(page);

      // Defensive clamp: the viewport resize is meant to GROW the page to
      // capture overflowing content, never to shrink it below the authored
      // design size. If a stylesheet failed to apply (e.g. a fixed-size .slide
      // measured 0 tall before its CSS loaded), setting the viewport to that
      // degenerate size would collapse justify-center/absolute layouts and push
      // content to negative coordinates. Keep at least the current viewport
      // size and a sane 16:9 floor derived from the measured width.
      const curVp = page.viewportSize() || { width: 1280, height: 720 };
      const measuredW = Math.round(bodyDimensions.width) || curVp.width;
      const minHeightFromWidth = Math.round(measuredW * (720 / 1280));
      const vpW = Math.max(measuredW, curVp.width, 320);
      const vpH = Math.max(Math.round(bodyDimensions.height), curVp.height, minHeightFromWidth, 240);

      await page.setViewportSize({ width: vpW, height: vpH });

      // Force a layout reflow after viewport resize so flex centering takes effect
      await page.evaluate(() => void document.body.offsetHeight);
      await page.waitForTimeout(200);

      // Re-read body dimensions after reflow to capture correct layout
      bodyDimensions = await getBodyDimensions(page);

      // Chart libraries (ECharts / Chart.js) paint into <canvas> asynchronously
      // after their CDN script loads, and re-draw (with entry animation) on the
      // viewport resize above. Wait until every canvas has real pixels — polled
      // via toDataURL length — so extractSlideData captures the finished chart
      // instead of a blank canvas. Bounded so pages without charts (or with
      // canvases that never paint, e.g. offline CDN) don't stall the run.
      try {
        const hasCanvas = await page.evaluate(() => document.querySelectorAll('canvas').length > 0);
        if (hasCanvas) {
          await page.waitForFunction(() => {
            const cs = Array.from(document.querySelectorAll('canvas'));
            if (cs.length === 0) return true;
            return cs.every(c => {
              const r = c.getBoundingClientRect();
              if (r.width <= 1 || r.height <= 1) return true; // ignore hidden/degenerate
              try { return c.toDataURL('image/png').length > 2000; } catch (e) { return true; }
            });
          }, { timeout: 6000, polling: 250 }).catch(() => {});
          // Small settle for entry animations to reach their final frame.
          await page.waitForTimeout(400);
        }
      } catch (e) { /* ignore — charts are best-effort */ }

      const slideWIn = pres.presLayout ? pres.presLayout.width / EMU_PER_IN : 10;
      const slideHIn = pres.presLayout ? pres.presLayout.height / EMU_PER_IN : 5.625;
      slideData = await extractSlideData(page, { widthIn: slideWIn, heightIn: slideHIn });
    } finally {
      await browser.close();
    }

    // Apply emphasis/symbol fonts to numeric labels and direct emoji text.
    applyEmphasisFont(slideData, effectiveFontConfig);

    // v4: Rasterize any inline-SVG images to PNG before they reach pptxgenjs.
    // pptxgenjs.addImage() rejects data:image/svg+xml URLs outright.
    await rasterizeSvgImages(slideData, tmpDir);
    // Materialize CSS object-fit before addImage(); pptxgenjs cannot infer original image dimensions.
    await materializeObjectFitImages(slideData, tmpDir);

    // Collect warnings
    const overflowWarnings = [];
    if (bodyDimensions.errors && bodyDimensions.errors.length > 0) {
      overflowWarnings.push(...bodyDimensions.errors);
    }

    // v3: Collect all non-blocking warnings
    const slideWidthIn = pres.presLayout ? pres.presLayout.width / EMU_PER_IN : 10;
    const slideHeightIn = pres.presLayout ? pres.presLayout.height / EMU_PER_IN : 5.625;
    const allWarnings = [...overflowWarnings];
    if (slideData.errors) allWarnings.push(...slideData.errors);
    if (slideData.warnings) allWarnings.push(...slideData.warnings);
    allWarnings.push(...checkElementBounds(slideData, slideWidthIn, slideHeightIn));
    allWarnings.push(...checkTextOverlaps(slideData));

    const targetSlide = slide || pres.addSlide();

    await addBackground(slideData, targetSlide, pres, tmpDir);
    addElements(slideData, targetSlide, pres, tmpDir);
    if (slideData.notes && typeof targetSlide.addNotes === 'function') {
      targetSlide.addNotes(slideData.notes);
    }

    // Print warnings after successful conversion (non-blocking)
    if (allWarnings.length > 0) {
      const suggestions = allWarnings.map((w, i) => `  ${i + 1}. ${w}`).join('\n');
      console.warn(`[html2pptx] ${htmlFile}: ${allWarnings.length} warning(s):\n${suggestions}`);
    }

    return { slide: targetSlide, placeholders: slideData.placeholders, warnings: allWarnings };
  } catch (error) {
    if (!error.message.startsWith(htmlFile)) {
      throw new Error(`${htmlFile}: ${error.message}`);
    }
    throw error;
  }
}

module.exports = html2pptx;