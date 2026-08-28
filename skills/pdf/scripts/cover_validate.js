#!/usr/bin/env node
/**
 * cover_validate.js — Cover page overlap detection via Playwright rendering
 *
 * Two detection passes:
 *   Pass 1: Text vs decorative line overlap (original)
 *   Pass 2: Layer 3 text vs text zone overflow (NEW)
 *
 * Pass 2 detects foreground text blocks that overlap each other on the
 * same z-layer (Layer 3). It excludes Layer 1 elements (watermarks,
 * sidebar decorative text) by checking opacity ≤ 0.10 or z-index ≤ 1.
 *
 * Usage:
 *   node cover_validate.js cover.html
 *   node cover_validate.js cover.html --width 210mm --height 297mm
 *   node cover_validate.js cover.html --min-gap 30   # custom min gap in px (default: auto = 5% of width)
 *   node cover_validate.js cover.html --no-text-overlap  # skip Pass 2 (text vs text)
 *
 * Exit codes:
 *   0 = no overlap issues found
 *   1 = overlap detected (prints details to stderr)
 *   2 = script error (missing file, browser launch failure, etc.)
 *
 * This script is ONLY for cover pages. Do NOT use it on:
 *   - Multi-page documents (use html2pdf-next.js pre-render checks)
 *   - Posters (use html2poster.js which handles overflow automatically)
 */

'use strict';

const fs = require('fs');
const path = require('path');

// ── Playwright import ──

let playwright;
try {
  playwright = require('playwright');
} catch {
  try {
    playwright = require('playwright-core');
  } catch {
    console.error('✗ Neither playwright nor playwright-core is installed.');
    process.exit(2);
  }
}

// ── Chromium resolution (shared logic with html2poster.js) ──

function resolveChromium(chromiumObj) {
  let exe;
  try { exe = chromiumObj.executablePath(); } catch (_) { exe = null; }
  if (exe && fs.existsSync(exe)) return { status: 'ok', executablePath: exe };

  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/google-chrome',
  ];
  if (process.env.PLAYWRIGHT_CHROMIUM_PATH) candidates.unshift(process.env.PLAYWRIGHT_CHROMIUM_PATH);

  for (const c of candidates) {
    if (fs.existsSync(c)) return { status: 'fallback', executablePath: c };
  }
  return { status: 'missing', executablePath: exe || '' };
}

// ── CLI parsing ──

function parseArgs(argv) {
  const tokens = argv.slice(2);
  let input = null, width = '210mm', height = '297mm', minGap = null, noTextOverlap = false;

  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (t === '--width') width = tokens[++i];
    else if (t === '--height') height = tokens[++i];
    else if (t === '--min-gap') minGap = parseFloat(tokens[++i]);
    else if (t === '--no-text-overlap') noTextOverlap = true;
    else if (t === '--help' || t === '-h') {
      console.log(`Usage: node cover_validate.js <cover.html> [options]

Options:
  --width <val>         Page width (default: 210mm)
  --height <val>        Page height (default: 297mm)
  --min-gap <px>        Minimum gap between text and decorative lines (default: 5% of width)
  --no-text-overlap     Skip Pass 2 (text vs text zone overlap detection)
  --help                Show this help`);
      process.exit(0);
    } else if (!t.startsWith('-') && !input) {
      input = t;
    }
  }
  return { input, width, height, minGap, noTextOverlap };
}

// ── Convert CSS dimension string to px for viewport ──

function dimToPx(dim) {
  if (!dim) return null;
  const s = String(dim).trim();
  const num = parseFloat(s);
  if (s.endsWith('mm')) return Math.round(num * 3.7795);  // 1mm ≈ 3.7795px at 96dpi
  if (s.endsWith('cm')) return Math.round(num * 37.795);
  if (s.endsWith('in')) return Math.round(num * 96);
  if (s.endsWith('px') || !isNaN(num)) return Math.round(num);
  return null;
}

// ── Decorative line detection heuristics ──
// A decorative line is an element that:
//   - Is very thin in one dimension (height ≤ 5px or width ≤ 5px)
//   - OR is an <hr> element
//   - OR has a large aspect ratio (> 10:1 or < 1:10)
//   - AND is not inside a text element

const DECORATIVE_LINE_DETECTION = `
(function detectOverlaps(minGapPx) {
  // Collect all elements
  const allElements = document.querySelectorAll('*');
  
  const textElements = [];
  const lineElements = [];
  
  // Classify elements
  for (const el of allElements) {
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    
    const tag = el.tagName.toLowerCase();
    const style = getComputedStyle(el);
    
    // Skip invisible elements
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
    
    // Detect decorative lines
    const isHR = tag === 'hr';
    const isThinH = rect.height <= 5 && rect.width > 20;  // thin horizontal line
    const isThinV = rect.width <= 5 && rect.height > 20;   // thin vertical line
    const aspectH = rect.width / rect.height;
    const aspectV = rect.height / rect.width;
    const isWideRatio = aspectH > 15 && rect.height <= 8;  // very wide, very thin
    const isTallRatio = aspectV > 15 && rect.width <= 8;   // very tall, very thin
    
    // Check if element has only border (no text content, no background image)
    const hasOnlyBorder = (
      el.textContent.trim() === '' &&
      style.backgroundImage === 'none' &&
      (style.borderTopWidth !== '0px' || style.borderBottomWidth !== '0px' ||
       style.borderLeftWidth !== '0px' || style.borderRightWidth !== '0px')
    );
    const isBorderLine = hasOnlyBorder && (rect.height <= 8 || rect.width <= 8);
    
    if (isHR || isThinH || isThinV || isWideRatio || isTallRatio || isBorderLine) {
      lineElements.push({
        tag: tag,
        class: el.className || '',
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        type: isThinH || isWideRatio ? 'horizontal' : (isThinV || isTallRatio ? 'vertical' : (rect.width >= rect.height ? 'horizontal' : 'vertical')),
      });
      continue;
    }
    
    // Detect text elements (has direct text content or is a heading/paragraph)
    const textTags = ['h1','h2','h3','h4','h5','h6','p','span','a','li','td','th','label','summary'];
    const hasDirectText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    
    if (textTags.includes(tag) || hasDirectText) {
      // Skip if this is inside a decorative element
      if (rect.height < 3) continue;
      
      // Determine layer: Layer 1 = background decoration (low opacity, low z-index)
      // Layer 3 = foreground text (normal opacity, higher z-index)
      const opacity = parseFloat(style.opacity);
      const zIndex = parseInt(style.zIndex, 10) || 0;
      const parentOpacity = el.parentElement ? parseFloat(getComputedStyle(el.parentElement).opacity) : 1;
      const effectiveOpacity = opacity * parentOpacity;
      const isPointerNone = style.pointerEvents === 'none';
      
      // Parse color alpha from rgba(r, g, b, a) using string split (regex unreliable in evaluate)
      let colorAlpha = 1;
      const colorStr = style.color;
      if (colorStr.indexOf('rgba') === 0) {
        const parts = colorStr.replace('rgba(', '').replace(')', '').split(',');
        if (parts.length >= 4) {
          const a = parseFloat(parts[3].trim());
          if (!isNaN(a)) colorAlpha = a;
        }
      }
      const visualOpacity = effectiveOpacity * colorAlpha;
      
      // Layer 1 heuristic: very low visual opacity (CSS opacity * color alpha)
      // These are watermarks, sidebar decoration text, etc.
      const isLayer1 = (
        visualOpacity <= 0.10 ||
        (zIndex <= 1 && visualOpacity <= 0.15) ||
        (isPointerNone && visualOpacity <= 0.20)
      );
      
      textElements.push({
        tag: tag,
        class: el.className || '',
        text: el.textContent.trim().substring(0, 60),
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        layer: isLayer1 ? 1 : 3,
        opacity: Math.round(visualOpacity * 1000) / 1000,
        zIndex: zIndex,
      });
    }
  }
  
  // De-duplicate: if a parent and child text element both overlap the same line,
  // only keep the more specific (smaller) one to avoid duplicate reports.
  // Sort text elements by area (smallest first) so we can skip parents.
  textElements.sort((a, b) => (a.rect.width * a.rect.height) - (b.rect.width * b.rect.height));
  
  // Check overlaps between text elements and line elements
  const overlaps = [];
  const reportedPairs = new Set(); // track "lineIndex:textContent" to deduplicate
  
  for (const text of textElements) {
    for (const line of lineElements) {
      const tr = text.rect;
      const lr = line.rect;
      
      if (line.type === 'horizontal') {
        // Check vertical overlap/proximity
        const textTop = tr.y;
        const textBottom = tr.y + tr.height;
        const lineTop = lr.y;
        const lineBottom = lr.y + lr.height;
        
        // Check horizontal overlap (they must share some X range)
        const xOverlap = !(tr.x + tr.width < lr.x || lr.x + lr.width < tr.x);
        if (!xOverlap) continue;
        
        // Calculate vertical gap
        let vGap;
        if (lineTop >= textBottom) {
          vGap = lineTop - textBottom;  // line is below text
        } else if (textTop >= lineBottom) {
          vGap = textTop - lineBottom;  // line is above text
        } else {
          vGap = 0;  // overlapping
        }
        
        if (vGap < minGapPx) {
          // De-dup: same line region, only report the smallest (most specific) text element
          const lineKey = 'h:' + Math.round(lr.x) + ',' + Math.round(lr.y);
          if (!reportedPairs.has(lineKey)) {
            reportedPairs.add(lineKey);
            overlaps.push({
              text: text.text,
              textTag: text.tag,
              textClass: text.class,
              textRect: tr,
              lineTag: line.tag,
              lineClass: line.class,
              lineRect: lr,
              lineType: line.type,
              gap: Math.round(vGap * 10) / 10,
              required: minGapPx,
            });
          }
        }
      } else if (line.type === 'vertical') {
        // Check horizontal overlap/proximity
        const textLeft = tr.x;
        const textRight = tr.x + tr.width;
        const lineLeft = lr.x;
        const lineRight = lr.x + lr.width;
        
        // Check vertical overlap (they must share some Y range)
        const yOverlap = !(tr.y + tr.height < lr.y || lr.y + lr.height < tr.y);
        if (!yOverlap) continue;
        
        // Calculate horizontal gap
        let hGap;
        if (lineLeft >= textRight) {
          hGap = lineLeft - textRight;
        } else if (textLeft >= lineRight) {
          hGap = textLeft - lineRight;
        } else {
          hGap = 0;
        }
        
        if (hGap < minGapPx) {
          const lineKey = 'v:' + Math.round(lr.x) + ',' + Math.round(lr.y);
          if (!reportedPairs.has(lineKey)) {
            reportedPairs.add(lineKey);
            overlaps.push({
              text: text.text,
              textTag: text.tag,
              textClass: text.class,
              textRect: tr,
              lineTag: line.tag,
              lineClass: line.class,
              lineRect: lr,
              lineType: line.type,
              gap: Math.round(hGap * 10) / 10,
              required: minGapPx,
            });
          }
        }
      }
    }
  }
  
  return {
    textElements: textElements.length,
    textElements_by_layer: {
      layer3: textElements.filter(t => t.layer === 3).length,
      layer1: textElements.filter(t => t.layer === 1).length,
    },
    lineElements: lineElements.length,
    overlaps: overlaps,
  };
})
`;

// ── Pass 2: Layer 3 text vs text zone overlap detection ──
// Only checks foreground text (Layer 3) against each other.
// Skips Layer 1 elements (watermarks, sidebar decoration) to avoid false positives.
// A "zone overflow" is when two Layer 3 text blocks' bounding boxes overlap
// or are closer than minGapPx on the Y axis (both must share X range).

const TEXT_ZONE_DETECTION = `
(function detectTextZoneOverlaps(minGapPx) {
  const allElements = document.querySelectorAll('*');
  const layer3Blocks = [];
  const layer1Count = { value: 0 };
  
  const textTags = ['h1','h2','h3','h4','h5','h6','p','span','a','li','td','th','label','summary','div'];
  
  for (const el of allElements) {
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) continue;
    
    const tag = el.tagName.toLowerCase();
    const style = getComputedStyle(el);
    
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
    
    // Must have direct text content
    const hasDirectText = Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
    if (!textTags.includes(tag) && !hasDirectText) continue;
    if (!el.textContent.trim()) continue;
    if (rect.height < 5) continue;
    
    // Compute effective opacity (walk up to find multiplicative opacity)
    const opacity = parseFloat(style.opacity);
    let parentEl = el.parentElement;
    let parentOpacity = 1;
    while (parentEl) {
      const po = parseFloat(getComputedStyle(parentEl).opacity);
      if (!isNaN(po)) parentOpacity *= po;
      parentEl = parentEl.parentElement;
    }
    const effectiveOpacity = opacity * parentOpacity;
    
    // Parse color alpha from rgba(r, g, b, a) using string split
    let colorAlpha = 1;
    const colorStr = style.color;
    if (colorStr.indexOf('rgba') === 0) {
      const parts = colorStr.replace('rgba(', '').replace(')', '').split(',');
      if (parts.length >= 4) {
        const a = parseFloat(parts[3].trim());
        if (!isNaN(a)) colorAlpha = a;
      }
    }
    const visualOpacity = effectiveOpacity * colorAlpha;
    
    const zIndex = parseInt(style.zIndex, 10) || 0;
    const isPointerNone = style.pointerEvents === 'none';
    
    // Layer 1 detection: watermark / sidebar decoration
    // Uses visualOpacity (CSS opacity * color alpha) to catch both patterns:
    //   - opacity: 0.03 (CSS property)
    //   - color: rgba(0,0,0,0.03) (color alpha)
    const isLayer1 = (
      visualOpacity <= 0.10 ||
      (zIndex <= 1 && visualOpacity <= 0.15) ||
      (isPointerNone && visualOpacity <= 0.20)
    );
    
    if (isLayer1) {
      layer1Count.value++;
      continue; // Skip Layer 1 entirely
    }
    
    // Also skip decorative lines (thin elements) — they're handled by Pass 1
    const isThin = (rect.height <= 5 && rect.width > 20) || (rect.width <= 5 && rect.height > 20);
    if (isThin) continue;
    
    layer3Blocks.push({
      tag: tag,
      class: el.className || '',
      text: el.textContent.trim().substring(0, 60),
      rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      opacity: Math.round(effectiveOpacity * 100) / 100,
      zIndex: zIndex,
      area: rect.width * rect.height,
    });
  }
  
  // De-duplicate: keep only the most specific (smallest area) text block
  // when a parent and child both contain the same text region.
  // Sort by area ascending, then for each block, remove any larger block
  // that fully contains it.
  layer3Blocks.sort((a, b) => a.area - b.area);
  
  const filtered = [];
  for (const block of layer3Blocks) {
    // Check if this block is a parent container of an already-added smaller block
    const isParent = filtered.some(existing => {
      return (
        block.rect.x <= existing.rect.x &&
        block.rect.y <= existing.rect.y &&
        block.rect.x + block.rect.width >= existing.rect.x + existing.rect.width &&
        block.rect.y + block.rect.height >= existing.rect.y + existing.rect.height
      );
    });
    if (!isParent) {
      filtered.push(block);
    }
  }
  
  // Check pairwise overlaps among Layer 3 blocks
  const overlaps = [];
  const reported = new Set();
  
  for (let i = 0; i < filtered.length; i++) {
    for (let j = i + 1; j < filtered.length; j++) {
      const a = filtered[i];
      const b = filtered[j];
      const ar = a.rect;
      const br = b.rect;
      
      // Check X-axis overlap (they must share horizontal range)
      const xOverlap = !(ar.x + ar.width < br.x || br.x + br.width < ar.x);
      if (!xOverlap) continue;
      
      // Calculate Y-axis gap
      const aTop = ar.y;
      const aBottom = ar.y + ar.height;
      const bTop = br.y;
      const bBottom = br.y + br.height;
      
      let yGap;
      if (bTop >= aBottom) {
        yGap = bTop - aBottom;
      } else if (aTop >= bBottom) {
        yGap = aTop - bBottom;
      } else {
        yGap = -Math.min(aBottom - bTop, bBottom - aTop); // negative = overlapping
      }
      
      // Only flag if blocks actually overlap (yGap < 0) or touch (yGap == 0)
      // We use 0 as threshold, NOT minGapPx — because tight spacing between
      // Kicker and Hero Title is intentional design (gap may be only 8-15px).
      // Zone overflow means actual pixel overlap, not "too close".
      if (yGap < 0) {
        const key = a.text.substring(0, 20) + ':' + b.text.substring(0, 20);
        if (reported.has(key)) continue;
        reported.add(key);
        
        overlaps.push({
          a: { tag: a.tag, class: a.class, text: a.text, rect: ar, opacity: a.opacity },
          b: { tag: b.tag, class: b.class, text: b.text, rect: br, opacity: b.opacity },
          axis: 'vertical',
          overlap: Math.round(Math.abs(yGap)),
          required: 0, // actual pixel overlap, not gap threshold
        });
      }
    }
  }
  
  return {
    layer3Count: filtered.length,
    layer1Count: layer1Count.value,
    overlaps: overlaps,
  };
})
`;

// ── Main ──

async function main() {
  const { input, width, height, minGap, noTextOverlap } = parseArgs(process.argv);

  if (!input) {
    console.error('✗ No input file specified. Usage: node cover_validate.js cover.html');
    process.exit(2);
  }

  const absIn = path.resolve(input);
  if (!fs.existsSync(absIn)) {
    console.error(`✗ File not found: ${absIn}`);
    process.exit(2);
  }

  const widthPx = dimToPx(width) || 794;   // A4 width in px
  const heightPx = dimToPx(height) || 1123; // A4 height in px
  const gap = minGap || Math.round(widthPx * 0.05);  // 1U = 5% of page width

  console.log(`🔍 cover_validate — Cover overlap detection`);
  console.log(`   Input:  ${absIn}`);
  console.log(`   Page:   ${widthPx}×${heightPx}px`);
  console.log(`   Min gap: ${gap}px (1U)`);
  console.log(`   Pass 2 (text↔text): ${noTextOverlap ? 'DISABLED' : 'enabled'}`);

  const { chromium } = playwright;
  const bInfo = resolveChromium(chromium);

  if (bInfo.status === 'missing') {
    console.error('✗ No Chromium found. Install via: npx playwright install chromium');
    process.exit(2);
  }

  let browser;
  try {
    const opts = { headless: true };
    if (bInfo.status === 'fallback') opts.executablePath = bInfo.executablePath;
    browser = await chromium.launch(opts);
  } catch (err) {
    console.error(`✗ Browser launch failed: ${err.message}`);
    process.exit(2);
  }

  try {
    const page = await browser.newPage({ viewport: { width: widthPx, height: heightPx } });
    await page.goto('file://' + absIn, { waitUntil: 'networkidle' });
    console.log(`   ✓ HTML loaded`);

    // Wait for fonts
    const fontsLoaded = await page.evaluate(() =>
      document.fonts.ready.then(() => document.fonts.size)
    ).catch(() => 0);
    console.log(`   ✓ Fonts: ${fontsLoaded} loaded`);

    // Run Pass 1: text vs decorative line overlap detection
    const result = await page.evaluate(`(${DECORATIVE_LINE_DETECTION})(${gap})`);

    const layer3Text = result.textElements_by_layer ? result.textElements_by_layer.layer3 : '?';
    const layer1Text = result.textElements_by_layer ? result.textElements_by_layer.layer1 : '?';
    console.log(`   ✓ Found ${result.textElements} text elements (L3: ${layer3Text}, L1: ${layer1Text}), ${result.lineElements} decorative lines`);

    let allIssues = [];

    // Pass 1 results
    if (result.overlaps.length > 0) {
      console.error(`\n   ❌ Pass 1: Found ${result.overlaps.length} text-line overlap(s):`);
      for (const o of result.overlaps) {
        const direction = o.lineType === 'vertical' ? 'horizontal' : 'vertical';
        console.error(`\n   ERROR [text↔line]: ${direction} gap = ${o.gap}px (required ≥ ${o.required}px)`);
        console.error(`     Text: <${o.textTag}> "${o.text}" @ y=${Math.round(o.textRect.y)}-${Math.round(o.textRect.y + o.textRect.height)}`);
        console.error(`     Line: <${o.lineTag}${o.lineClass ? '.' + o.lineClass.split(' ')[0] : ''}> [${o.lineType}] @ y=${Math.round(o.lineRect.y)}-${Math.round(o.lineRect.y + o.lineRect.height)}`);
        console.error(`     Fix: Move the decorative line at least ${Math.ceil(o.required - o.gap)}px away from the text.`);
      }
      allIssues.push(...result.overlaps.map(o => ({ pass: 1, ...o })));
    } else {
      console.log(`   ✅ Pass 1: No text-line overlaps`);
    }

    // Pass 2: Layer 3 text vs text zone overlap detection
    if (!noTextOverlap) {
      const textOverlaps = await page.evaluate(`(${TEXT_ZONE_DETECTION})(${gap})`);

      if (textOverlaps.overlaps.length > 0) {
        console.error(`\n   ❌ Pass 2: Found ${textOverlaps.overlaps.length} text-text zone overflow(s):`);
        for (const o of textOverlaps.overlaps) {
          console.error(`\n   ERROR [text↔text]: ${o.axis} overlap = ${o.overlap}px (gap should be ≥ ${o.required}px)`);
          console.error(`     Block A: <${o.a.tag}.${o.a.class.split(' ')[0] || '?'}> "${o.a.text}" @ y=${Math.round(o.a.rect.y)}-${Math.round(o.a.rect.y + o.a.rect.height)}`);
          console.error(`     Block B: <${o.b.tag}.${o.b.class.split(' ')[0] || '?'}> "${o.b.text}" @ y=${Math.round(o.b.rect.y)}-${Math.round(o.b.rect.y + o.b.rect.height)}`);
          console.error(`     Fix: Move block B down by at least ${Math.ceil(o.overlap + o.required)}px, or reduce block A font size.`);
        }
        allIssues.push(...textOverlaps.overlaps.map(o => ({ pass: 2, ...o })));
      } else {
        console.log(`   ✅ Pass 2: No text-text zone overflows (checked ${textOverlaps.layer3Count} L3 blocks, skipped ${textOverlaps.layer1Count} L1 blocks)`);
      }
    }

    if (allIssues.length === 0) {
      console.log(`\n   ✅ All checks passed`);
      process.exit(0);
    } else {
      console.error(`\n   ❌ Total: ${allIssues.length} issue(s) found`);
      process.exit(1);
    }

  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error(`✗ Unexpected error: ${err.message}`);
  process.exit(2);
});
