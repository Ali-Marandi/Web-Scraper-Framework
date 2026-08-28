#!/usr/bin/env node
/**
 * html2pdf-next.js — HTML → PDF converter using Playwright + Paged.js + pdf-lib
 *
 * Uses Paged.js polyfill for pagination (break-inside/before/after, named pages,
 * orphans/widows) and Chromium for rendering. pdf-lib for post-processing.
 *
 * Usage:
 *   node html2pdf-next.js input.html
 *   node html2pdf-next.js input.html --output result.pdf
 *   node html2pdf-next.js input.html --css extra.css
 *   node html2pdf-next.js input.html --width 720px --height 960px
 *   node html2pdf-next.js input.html --merge a.pdf b.pdf  (merge additional PDFs after)
 *
 * Architecture:
 *   1. Playwright loads HTML, runs pre-render hooks (Mermaid, KaTeX, overflow detection)
 *   2. Paged.js polyfill injected — reads @page rules, chunks content into .pagedjs_page containers
 *   3. Chromium renders the Paged.js output to PDF via page.pdf()
 *   4. pdf-lib for merge, metadata, page count extraction
 *   5. Continuous-canvas mode (design_engine.py) skips Paged.js, uses Chromium native print
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ═══════════════════════════════════════════════════════════════════
// Playwright / Chromium resolution (self-contained, no external helper)
// ═══════════════════════════════════════════════════════════════════

function loadPlaywright() {
  // Try direct require first
  try { return require('playwright'); } catch (_) {}

  // Search common global paths
  const Module = require('module');
  const roots = new Set();
  if (process.env.PLAYWRIGHT_PATH) roots.add(process.env.PLAYWRIGHT_PATH);
  if (process.env.NODE_PATH) {
    process.env.NODE_PATH.split(path.delimiter).filter(Boolean).forEach(p => roots.add(p));
  }
  try {
    const g = execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
    if (g) roots.add(g);
  } catch (_) {}

  for (const base of roots) {
    const pkg = path.join(base, 'playwright', 'package.json');
    if (!fs.existsSync(pkg)) continue;
    try { return Module.createRequire(pkg)('playwright'); } catch (_) {}
  }
  throw new Error('Playwright not found. Install: npm install -g playwright@1.50.0');
}

function loadPdfLib() {
  try { return require('pdf-lib'); } catch (_) {}
  const Module = require('module');
  try {
    const g = execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
    const pkg = path.join(g, 'pdf-lib', 'package.json');
    if (fs.existsSync(pkg)) return Module.createRequire(pkg)('pdf-lib');
  } catch (_) {}
  throw new Error('pdf-lib not found. Install: npm install -g pdf-lib');
}

function resolveChromium(chromiumObj, allowInstall = false) {
  let exe;
  try { exe = chromiumObj.executablePath(); } catch (_) { exe = null; }

  if (exe && fs.existsSync(exe)) {
    return { status: 'ok', executablePath: exe };
  }

  // Try system Chrome/Chromium
  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/google-chrome',
  ];
  if (process.env.PLAYWRIGHT_CHROMIUM_PATH) candidates.unshift(process.env.PLAYWRIGHT_CHROMIUM_PATH);

  for (const c of candidates) {
    if (fs.existsSync(c)) return { status: 'fallback', executablePath: c };
  }

  if (allowInstall) {
    const r = spawnSync('npx', ['playwright', 'install', 'chromium'], { stdio: 'inherit', shell: true });
    if (r.status === 0) {
      try { exe = chromiumObj.executablePath(); } catch (_) {}
      if (exe && fs.existsSync(exe)) return { status: 'installed', executablePath: exe };
    }
  }

  return { status: 'missing', executablePath: exe || '' };
}

// ═══════════════════════════════════════════════════════════════════
// CLI
// ═══════════════════════════════════════════════════════════════════

function cli() {
  const tokens = process.argv.slice(2);
  if (!tokens.length || tokens[0] === '-h' || tokens[0] === '--help') {
    console.log(`
Usage: node html2pdf-next.js <input.html> [options]

Options:
  --output, -o <file>   Output PDF path (default: <input>.pdf)
  --css <file>          Inject extra stylesheet
  --width <px>          Custom page width  (e.g. 720px)
  --height <px>         Custom page height (e.g. 960px)
  --nopaged             Skip Paged.js, use Chromium native @page pagination
  --merge <files...>    Append additional PDF files after conversion
  --title <text>        Set PDF document title metadata
  --help, -h            Show help
`);
    process.exit(0);
  }

  const inputFile = tokens[0];
  let outputFile = null, customCSS = null, width = null, height = null;
  let mergeFiles = [], title = null, noPaged = false;

  for (let i = 1; i < tokens.length; i++) {
    const t = tokens[i];
    if (t === '--output' || t === '-o') outputFile = tokens[++i];
    else if (t === '--css') customCSS = tokens[++i];
    else if (t === '--width') width = tokens[++i];
    else if (t === '--height') height = tokens[++i];
    else if (t === '--direct' || t === '--nopaged') { noPaged = true; }
    else if (t === '--title') title = tokens[++i];
    else if (t === '--merge') {
      while (i + 1 < tokens.length && !tokens[i + 1].startsWith('--')) {
        mergeFiles.push(tokens[++i]);
      }
    }
  }

  if (!outputFile) {
    const p = path.parse(inputFile);
    outputFile = path.join(p.dir || '.', p.name + '.pdf');
  }

  return { inputFile, outputFile, customCSS, width, height, mergeFiles, title, noPaged };
}

// ═══════════════════════════════════════════════════════════════════
// Helpers
// ═══════════════════════════════════════════════════════════════════

function prettyBytes(n) {
  const units = ['B', 'KB', 'MB', 'GB'];
  let u = 0;
  while (n >= 1024 && u < units.length - 1) { n /= 1024; u++; }
  return `${n.toFixed(1)} ${units[u]}`;
}

// ═══════════════════════════════════════════════════════════════════
// Pre-render hooks (run in browser context before PDF export)
// ═══════════════════════════════════════════════════════════════════

async function preRenderHooks(page) {
  const warnings = [];

  // 1. Wait for Mermaid diagrams
  const hasMermaid = await page.evaluate(() => document.querySelectorAll('.mermaid').length > 0);
  if (hasMermaid) {
    console.log('  ⏳ Waiting for Mermaid diagrams...');
    try {
      await page.waitForFunction(() => {
        for (const m of document.querySelectorAll('.mermaid'))
          if (!m.querySelector('svg') && !m.getAttribute('data-processed')) return false;
        return true;
      }, { timeout: 30000 });
      await sleep(2000);
      console.log('  ✓ Mermaid rendered');
    } catch (_) {
      warnings.push('Mermaid rendering timed out (30s)');
    }
  }

  // 2. Trigger KaTeX math rendering
  const katexStatus = await page.evaluate(() => ({
    lib: typeof renderMathInElement === 'function' || typeof katex !== 'undefined',
    rendered: document.querySelectorAll('.katex').length > 0,
    raw: /\$[^$]+\$|\$\$[^$]+\$\$|\\\(.*?\\\)|\\\[.*?\\\]/.test(document.body.innerText),
  }));

  // Auto-inject KaTeX CDN if raw math detected but library not loaded
  if (!katexStatus.lib && katexStatus.raw && !katexStatus.rendered) {
    console.log('  ⏳ Auto-injecting KaTeX CDN (math formulas detected but KaTeX not loaded)...');
    await page.addStyleTag({ url: 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css' });
    await page.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.js' });
    await page.addScriptTag({ url: 'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/contrib/auto-render.min.js' });
    await sleep(2000); // Wait for CDN scripts to load
    // Re-check
    const recheckLib = await page.evaluate(() => typeof renderMathInElement === 'function');
    if (recheckLib) {
      console.log('  ✓ KaTeX CDN loaded successfully');
    } else {
      console.log('  ⚠ KaTeX CDN failed to load — math will render as raw text');
      warnings.push('KaTeX CDN injection failed; math formulas may appear as raw LaTeX code');
    }
  }

  // Re-evaluate after potential CDN injection
  const katexReady = await page.evaluate(() => ({
    lib: typeof renderMathInElement === 'function' || typeof katex !== 'undefined',
    rendered: document.querySelectorAll('.katex').length > 0,
    raw: /\$[^$]+\$|\$\$[^$]+\$\$|\\\(.*?\\\)|\\\[.*?\\\]/.test(document.body.innerText),
  }));

  if (katexReady.lib && !katexReady.rendered && katexReady.raw) {
    console.log('  ⏳ Triggering KaTeX rendering...');
    await page.evaluate(() => {
      if (typeof renderMathInElement === 'function')
        renderMathInElement(document.body, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true },
          ],
          throwOnError: false,
        });
    });
    await sleep(1000);
    console.log('  ✓ KaTeX rendered');
  } else if (katexReady.rendered) {
    await sleep(500); // Font loading settle
  }

  // 3. Fix oversized elements that prevent page breaks
  const nFixed = await page.evaluate(() => {
    const LIMIT = 1000;
    let n = 0;
    document.querySelectorAll(
      '[style*="page-break-inside: avoid"],[style*="break-inside: avoid"],' +
      '.avoid-break,table,figure,.theorem,.algorithm'
    ).forEach(el => {
      if (el.getBoundingClientRect().height > LIMIT) {
        el.style.pageBreakInside = 'auto';
        el.style.breakInside = 'auto';
        n++;
      }
    });
    return n;
  });
  if (nFixed) {
    console.log(`  ⚠ Fixed ${nFixed} oversized elements (removed break-inside: avoid)`);
  }

  // 4. Detect overflow (horizontal AND vertical)
  const overflows = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('pre,table,figure,img,svg,.mermaid,blockquote,.equation').forEach(el => {
      const hDiff = el.scrollWidth - el.clientWidth;
      const vDiff = el.scrollHeight - el.clientHeight;
      if (hDiff > 2 || vDiff > 2) out.push({
        tag: el.tagName.toLowerCase(),
        cls: el.className || '',
        hOverflow: hDiff > 2 ? hDiff : 0,
        vOverflow: vDiff > 2 ? vDiff : 0,
        preview: (el.textContent || '').slice(0, 50).replace(/\s+/g, ' '),
      });
    });
    return out;
  });
  if (overflows.length) {
    console.log('  ⚠ Overflow detected:');
    overflows.forEach(o => {
      const parts = [];
      if (o.hOverflow) parts.push(`H +${o.hOverflow}px`);
      if (o.vOverflow) parts.push(`V +${o.vOverflow}px`);
      console.log(`    <${o.tag}${o.cls ? '.' + o.cls.split(' ')[0] : ''}> ${parts.join(', ')}`);
    });
    warnings.push(`${overflows.length} element(s) have overflow`);
  }

  // 4b. Remove overflow:hidden BEFORE Paged.js injection.
  //     Paged.js reads the DOM layout to chunk content into pages.
  //     If a container has overflow:hidden + fixed height, Paged.js only sees
  //     the visible portion and silently loses the clipped content.
  //     We must remove overflow:hidden first so Paged.js gets the full content.
  const vOverflowFix = await page.evaluate(() => {
    const fixes = [];
    const candidates = [document.documentElement, document.body];
    const bodyChildren = document.body.children;
    for (let i = 0; i < bodyChildren.length; i++) {
      const child = bodyChildren[i];
      const tag = child.tagName.toLowerCase();
      if (tag === 'svg' || tag === 'script' || tag === 'style' || tag === 'link') continue;
      candidates.push(child);
      for (let j = 0; j < child.children.length; j++) {
        const grandchild = child.children[j];
        const gtag = grandchild.tagName.toLowerCase();
        if (gtag === 'svg' || gtag === 'script' || gtag === 'style') continue;
        candidates.push(grandchild);
      }
    }

    for (const el of candidates) {
      const computed = getComputedStyle(el);
      const overflow = computed.overflow || computed.overflowY;
      const hasHiddenOverflow = overflow === 'hidden' || overflow === 'clip';
      const diff = el.scrollHeight - el.clientHeight;

      if (hasHiddenOverflow && diff > 5) {
        const tag = el.tagName.toLowerCase();
        const id = el.id ? `#${el.id}` : '';
        const cls = el.className ? `.${String(el.className).split(' ')[0]}` : '';
        const selector = `${tag}${id}${cls}`;

        // ONLY remove overflow — do NOT touch height, position, or any
        // other layout property (preserves absolute-positioned layouts).
        el.style.overflow = 'visible';
        el.style.overflowY = 'visible';

        fixes.push({ selector, clipped: diff });
      }
    }

    const finalHeight = Math.max(
      document.documentElement.scrollHeight,
      document.body.scrollHeight
    );
    return { fixes, finalHeight };
  });

  if (vOverflowFix.fixes.length) {
    console.log('  ⚠️  Removed overflow:hidden (content was clipped):');
    vOverflowFix.fixes.forEach(f => {
      console.log(`    ${f.selector}: ${f.clipped}px clipped → overflow:visible`);
    });
  }

  // Measure content height for diagnostics
  const contentHeight = vOverflowFix.fixes.length > 0
    ? vOverflowFix.finalHeight
    : await page.evaluate(() => Math.max(
        document.documentElement.scrollHeight,
        document.body.scrollHeight
      ));

  // 5. Inject minimal @page CSS fallback
  await page.evaluate(() => {
    const styles = Array.from(document.querySelectorAll('style'));
    const hasPageRule = styles.some(s => (s.textContent || '').includes('@page'));
    if (!hasPageRule) {
      const s = document.createElement('style');
      s.textContent = `@page { margin: 20mm; }`;
      document.head.appendChild(s);
    }
  });

  // 6. (Removed) — Paged.js handles cover sections (100vh, break-after: page,
  //     page-break-inside: avoid) natively. No manual fixup needed.

  return { warnings, contentHeight };
}

// ═══════════════════════════════════════════════════════════════════
// Content statistics (post-render, from PDF or page)
// ═══════════════════════════════════════════════════════════════════

async function collectStats(page) {
  return page.evaluate(() => {
    const body = document.body;
    const text = body.innerText || '';
    const zhChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
    const enWords = (text.match(/[a-zA-Z]+/g) || []).length;
    return {
      wordCount: zhChars + enWords,
      figures: document.querySelectorAll('figure,.figure,img').length,
      tables: document.querySelectorAll('table').length,
    };
  });
}

// ═══════════════════════════════════════════════════════════════════
// pdf-lib post-processing: page count, metadata, merge
// ═══════════════════════════════════════════════════════════════════

async function postProcess(pdfPath, options = {}) {
  const { PDFDocument } = loadPdfLib();
  const pdfBytes = fs.readFileSync(pdfPath);
  const doc = await PDFDocument.load(pdfBytes);

  // Set metadata
  if (options.title) doc.setTitle(options.title);
  doc.setProducer('html2pdf-next (Playwright + pdf-lib)');
  doc.setCreationDate(new Date());

  const pageCount = doc.getPageCount();

  // Merge additional PDFs
  if (options.mergeFiles && options.mergeFiles.length) {
    for (const mf of options.mergeFiles) {
      if (!fs.existsSync(mf)) {
        console.log(`  ⚠ Merge file not found: ${mf}`);
        continue;
      }
      console.log(`  📎 Merging: ${path.basename(mf)}`);
      const donorBytes = fs.readFileSync(mf);
      const donorDoc = await PDFDocument.load(donorBytes);
      const copiedPages = await doc.copyPages(donorDoc, donorDoc.getPageIndices());
      copiedPages.forEach(p => doc.addPage(p));
    }
  }

  // Save
  const finalBytes = await doc.save();
  fs.writeFileSync(pdfPath, finalBytes);

  return { pageCount: doc.getPageCount(), originalPages: pageCount };
}

// ═══════════════════════════════════════════════════════════════════
// Main pipeline
// ═══════════════════════════════════════════════════════════════════

async function convert(inputFile, outputFile, customCSS, options = {}) {
  const { width, height, mergeFiles, title, noPaged } = options;

  if (!fs.existsSync(inputFile)) {
    console.error(`✗ File not found: ${inputFile}`);
    process.exit(1);
  }

  const playwright = loadPlaywright();
  const { chromium } = playwright;

  // Resolve browser
  const canInstall = process.env.PDF_SKIP_BROWSER_INSTALL !== '1';
  const bInfo = resolveChromium(chromium, canInstall);

  if (bInfo.status === 'missing') {
    console.error('\n✗ Chromium not found. Run: npx playwright install chromium\n');
    process.exit(2);
  }
  if (bInfo.status === 'fallback') {
    console.log(`⚠ Using fallback Chromium: ${bInfo.executablePath}`);
  }

  const absIn = path.resolve(inputFile);
  const absOut = path.resolve(outputFile);

  console.log(`\n🔄 Converting ${path.basename(inputFile)}...`);
  console.log(`   Engine: Playwright + ${noPaged ? 'Chromium native @page' : 'Paged.js'}`);

  // Read and optionally inject CSS
  let html = fs.readFileSync(absIn, 'utf-8');
  if (customCSS) {
    if (!fs.existsSync(customCSS)) {
      console.error(`✗ CSS file not found: ${customCSS}`);
      process.exit(1);
    }
    const tag = `<style>${fs.readFileSync(customCSS, 'utf-8')}</style>`;
    html = html.includes('</head>') ? html.replace('</head>', tag + '\n</head>') : tag + '\n' + html;
    // Write modified HTML for Playwright to load
    const tmpHtml = absIn + '.tmp.html';
    fs.writeFileSync(tmpHtml, html);
    // We'll clean up later
  }

  // Launch browser
  let browser;
  try {
    const opts = { headless: true };
    if (bInfo.status === 'fallback') opts.executablePath = bInfo.executablePath;
    browser = await chromium.launch(opts);
  } catch (err) {
    const msg = err.message || '';
    if (msg.includes('shared libraries') || msg.includes('.so')) {
      console.error('\n✗ Missing system libraries. Run: npx playwright install-deps chromium\n');
    } else {
      console.error(`\n✗ Browser launch failed: ${msg}\n`);
    }
    process.exit(1);
  }

  try {
    const page = await browser.newPage();
    const loadFile = customCSS ? absIn + '.tmp.html' : absIn;
    await page.goto('file://' + loadFile, { waitUntil: 'networkidle' });

    // ── Pre-render hooks ──
    console.log('\n📋 Pre-render checks:');
    const preRenderResult = await preRenderHooks(page);
    const warnings = preRenderResult.warnings;
    const measuredContentHeight = preRenderResult.contentHeight;

    // ── Detect continuous-canvas mode (design_engine.py output) ──
    const continuousInfo = await page.evaluate(() => {
      const el = document.querySelector('.continuous-canvas');
      if (!el) return null;
      const root = getComputedStyle(document.documentElement);
      return {
        width: root.getPropertyValue('--canvas-w').trim() || '720px',
        height: root.getPropertyValue('--canvas-h').trim() || '960px',
        pages: el.querySelectorAll('.page-section').length,
      };
    });

    if (continuousInfo) {
      // Creative PDF: design_engine.py output with fixed-canvas page-sections.
      // These are already laid out as absolute-positioned pages — skip Paged.js,
      // use Chromium native print directly.
      console.log(`\n🎨 Creative layout: ${continuousInfo.pages} pages @ ${continuousInfo.width} × ${continuousInfo.height}`);
      await page.pdf({
        path: absOut,
        printBackground: true,
        preferCSSPageSize: false,
        margin: { top: 0, right: 0, bottom: 0, left: 0 },
        width: continuousInfo.width,
        height: continuousInfo.height,
      });
    } else if (noPaged) {
      // ── Chromium native pagination (--nopaged flag) ──
      console.log('\n📄 Rendering PDF (Chromium native @page)...');
      const pdfOpts = {
        path: absOut,
        printBackground: true,
        preferCSSPageSize: true,
        tagged: true,
      };

      if (width || height) {
        if (width) pdfOpts.width = width;
        if (height) pdfOpts.height = height;
        pdfOpts.margin = { top: 0, right: 0, bottom: 0, left: 0 };
        console.log(`   Custom size: ${pdfOpts.width || 'auto'} × ${pdfOpts.height || 'auto'}`);
      } else {
        const pageSize = await page.evaluate(() => {
          const styles = Array.from(document.querySelectorAll('style'));
          for (const s of styles) {
            const text = s.textContent || '';
            const match = text.match(/@page\s*\{[^}]*size:\s*([\d.]+)px\s+([\d.]+)px/);
            if (match) return { width: parseFloat(match[1]), height: parseFloat(match[2]) };
          }
          return null;
        });
        if (pageSize) {
          pdfOpts.margin = { top: 0, right: 0, bottom: 0, left: 0 };
          console.log(`   @page size: ${pageSize.width}px × ${pageSize.height}px`);
        } else {
          pdfOpts.format = 'A4';
        }
      }

      await page.pdf(pdfOpts);
    } else {
      // Inject Paged.js polyfill to take over pagination.
      // Paged.js reads @page rules, chunks content into .pagedjs_page containers,
      // and handles break-inside/before/after, orphans/widows, named pages, etc.
      console.log('\n📖 Injecting Paged.js for pagination...');

      // Resolve the paged.polyfill.js path
      const pagedPolyfillPath = (() => {
        // Try workspace node_modules first
        const candidates = [
          path.resolve(__dirname, '..', '..', '..', 'node_modules', 'pagedjs', 'dist', 'paged.polyfill.js'),
          path.resolve(process.cwd(), 'node_modules', 'pagedjs', 'dist', 'paged.polyfill.js'),
        ];
        for (const c of candidates) {
          if (fs.existsSync(c)) return c;
        }
        // Try require.resolve
        try {
          const mod = require.resolve('pagedjs/dist/paged.polyfill.js');
          return mod;
        } catch (_) {}
        return null;
      })();

      if (!pagedPolyfillPath) {
        console.error('\n✗ pagedjs not found. Run: npm install pagedjs');
        process.exit(1);
      }

      const pagedScript = fs.readFileSync(pagedPolyfillPath, 'utf-8');
      await page.addScriptTag({ content: pagedScript });

      // Wait for Paged.js to finish rendering
      try {
        await page.waitForSelector('.pagedjs_page', { timeout: 30000 });
        // Give it extra time for all pages to settle
        await sleep(2000);
      } catch (_) {
        console.log('  ⚠ Paged.js did not create .pagedjs_page elements (timeout 30s)');
        console.log('    Falling back to Chromium native @page pagination.');
        warnings.push('Paged.js rendering timed out; fell back to native pagination');
      }

      // Check Paged.js results
      const pagedInfo = await page.evaluate(() => {
        const pages = document.querySelectorAll('.pagedjs_page');
        if (pages.length === 0) return null;
        return {
          pageCount: pages.length,
          pageWidth: pages[0].offsetWidth,
          pageHeight: pages[0].offsetHeight,
        };
      });

      if (pagedInfo) {
        console.log(`  ✓ Paged.js: ${pagedInfo.pageCount} pages @ ${pagedInfo.pageWidth}×${pagedInfo.pageHeight}px`);
      }

      // ── Post-Paged.js background & centering fix ──
      // Paged.js creates .pagedjs_page containers that are transparent by default.
      // If body has a background color/image, the empty areas of each page may show
      // the wrong color. Fix: propagate background to .pagedjs_page containers.
      const bgFix = await page.evaluate(() => {
        const body = document.body;
        const html = document.documentElement;
        const bodyStyle = getComputedStyle(body);
        const htmlStyle = getComputedStyle(html);
        const bodyBg = bodyStyle.backgroundColor;
        const htmlBg = htmlStyle.backgroundColor;
        const bodyBgImg = bodyStyle.backgroundImage;
        const htmlBgImg = htmlStyle.backgroundImage;

        const isTransparent = (c) => !c || c === 'rgba(0, 0, 0, 0)' || c === 'transparent';
        const hasGradient = (img) => img && img !== 'none';

        // Check if body or html uses a gradient/image background
        const bodyHasGradient = hasGradient(bodyBgImg);
        const htmlHasGradient = hasGradient(htmlBgImg);

        // If body uses gradient, propagate the full background shorthand
        // (not just backgroundColor, which would be transparent for gradients)
        if (bodyHasGradient) {
          // Copy body's full background to each .pagedjs_page
          const pages = document.querySelectorAll('.pagedjs_page');
          pages.forEach(p => {
            p.style.backgroundImage = bodyBgImg;
            p.style.backgroundSize = bodyStyle.backgroundSize;
            p.style.backgroundPosition = bodyStyle.backgroundPosition;
            p.style.backgroundRepeat = bodyStyle.backgroundRepeat;
            if (!isTransparent(bodyBg)) p.style.backgroundColor = bodyBg;
          });
          // Unify html to prevent color leaking
          html.style.backgroundColor = isTransparent(bodyBg) ? '#000' : bodyBg;
          html.style.backgroundImage = bodyBgImg;

          const pagesContainer = document.querySelector('.pagedjs_pages');
          if (pagesContainer) { pagesContainer.style.margin = '0'; pagesContainer.style.padding = '0'; }

          return { pageBg: 'gradient', pagesFixed: pages.length, bodyBg, htmlBg, gradient: true };
        }

        // Solid color path: body bg > html bg > white
        const pageBg = !isTransparent(bodyBg) ? bodyBg
                     : !isTransparent(htmlBg) ? htmlBg
                     : 'white';

        const pages = document.querySelectorAll('.pagedjs_page');
        let fixed = 0;
        pages.forEach(p => {
          if (isTransparent(getComputedStyle(p).backgroundColor)) {
            p.style.backgroundColor = pageBg;
            fixed++;
          }
        });

        // Unify html/body background to match (prevents color leaking around pages)
        html.style.backgroundColor = pageBg;
        // Only set body bg if it was transparent (don't override an intentional body bg)
        if (isTransparent(bodyBg)) body.style.backgroundColor = pageBg;

        const pagesContainer = document.querySelector('.pagedjs_pages');
        if (pagesContainer) { pagesContainer.style.margin = '0'; pagesContainer.style.padding = '0'; }

        return { pageBg, pagesFixed: fixed, bodyBg, htmlBg, gradient: false };
      });

      if (bgFix.pagesFixed > 0) {
        console.log(`  ✓ Background fix: ${bgFix.pagesFixed} pages → ${bgFix.pageBg}`);
      }

      // ── Post-Paged.js layout alignment fix ──
      // Paged.js renders pages inside .pagedjs_pages with padding/margin for screen
      // preview (visual spacing between pages). In print/PDF mode this causes the
      // .pagedjs_page to start at (40,40) instead of (0,0), shifting content.
      // Fix: reset all Paged.js wrapper margins/paddings so pages start at origin.
      if (pagedInfo) {
        const alignFix = await page.evaluate(() => {
          // Reset pagedjs_pages container
          const pc = document.querySelector('.pagedjs_pages');
          if (pc) {
            pc.style.margin = '0';
            pc.style.padding = '0';
          }
          // Reset all pagedjs_page wrappers
          document.querySelectorAll('.pagedjs_page').forEach(p => {
            p.style.margin = '0';
          });
          // Reset body/html margins
          document.body.style.margin = '0';
          document.body.style.padding = '0';
          document.documentElement.style.margin = '0';
          document.documentElement.style.padding = '0';
          // Check final alignment
          const firstPage = document.querySelector('.pagedjs_page');
          if (!firstPage) return { fixed: false };
          const rect = firstPage.getBoundingClientRect();
          return { fixed: true, x: rect.x, y: rect.y, w: rect.width, h: rect.height };
        });
        if (alignFix.fixed && (alignFix.x > 1 || alignFix.y > 1)) {
          console.log(`  ⚠ Page offset after reset: (${alignFix.x}, ${alignFix.y}) — may still have internal pagedjs margins`);
        }
      }

      // Generate PDF
      console.log('\n📄 Rendering PDF...');
      const pdfOpts = {
        path: absOut,
        printBackground: true,
        preferCSSPageSize: true,
        tagged: true,
        margin: { top: 0, right: 0, bottom: 0, left: 0 },
      };

      if (width || height) {
        if (width) pdfOpts.width = width;
        if (height) pdfOpts.height = height;
        console.log(`   Custom size: ${pdfOpts.width || 'auto'} × ${pdfOpts.height || 'auto'}`);
      } else if (!pagedInfo) {
        // Paged.js didn't run (fallback) — detect @page or use A4
        const pageSize = await page.evaluate(() => {
          const styles = Array.from(document.querySelectorAll('style'));
          for (const s of styles) {
            const text = s.textContent || '';
            const match = text.match(/@page\s*\{[^}]*size:\s*([\d.]+)px\s+([\d.]+)px/);
            if (match) return { width: parseFloat(match[1]), height: parseFloat(match[2]) };
          }
          return null;
        });
        if (pageSize) {
          console.log(`   @page size: ${pageSize.width}px × ${pageSize.height}px`);
        } else {
          pdfOpts.format = 'A4';
        }
      }

      await page.pdf(pdfOpts);
    }

    // Collect content stats from the page
    const stats = await collectStats(page);

    // ── pdf-lib post-processing ──
    console.log('\n🔧 Post-processing (pdf-lib):');
    const postResult = await postProcess(absOut, { mergeFiles, title });

    // Clean up temp HTML
    const tmpHtml = absIn + '.tmp.html';
    if (fs.existsSync(tmpHtml)) fs.unlinkSync(tmpHtml);

    // ── Report ──
    const sz = fs.statSync(absOut).size;
    console.log('\n' + '═'.repeat(40));
    console.log('  PDF Generated Successfully');
    console.log('═'.repeat(40));
    console.log(`  File:    ${path.basename(absOut)}`);
    console.log(`  Pages:   ${postResult.pageCount}`);
    console.log(`  Size:    ${prettyBytes(sz)}`);
    console.log(`  Words:   ~${stats.wordCount.toLocaleString()}`);
    console.log(`  Assets:  ${stats.figures} figures, ${stats.tables} tables`);
    const engineLabel = continuousInfo ? 'Playwright (Creative canvas)'
                      : noPaged ? 'Playwright (Chromium native @page)'
                      : 'Playwright + Paged.js';
    console.log(`  Engine:  ${engineLabel}`);
    console.log(`  Path:    ${absOut}`);

    if (mergeFiles && mergeFiles.length && postResult.pageCount > postResult.originalPages) {
      console.log(`  Merged:  +${postResult.pageCount - postResult.originalPages} pages from ${mergeFiles.length} file(s)`);
    }

    if (warnings.length) {
      console.log('\n⚠ Warnings:');
      warnings.forEach(w => console.log(`  · ${w}`));
    }

    // Anomaly detection
    if (postResult.pageCount > 1 && stats.wordCount > 0) {
      const avgWordsPerPage = stats.wordCount / postResult.pageCount;
      if (avgWordsPerPage < 30) {
        console.log(`\n⚠ Low content density: ~${Math.round(avgWordsPerPage)} words/page (expected 100+)`);
      }
    }

  } catch (err) {
    console.error('\n✗ Conversion failed:', err.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// ═══════════════════════════════════════════════════════════════════
// Entry
// ═══════════════════════════════════════════════════════════════════

(async () => {
  try {
    const args = cli();
    await convert(args.inputFile, args.outputFile, args.customCSS, {
      width: args.width,
      height: args.height,
      mergeFiles: args.mergeFiles,
      title: args.title,
      noPaged: args.noPaged,
    });
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
})();
