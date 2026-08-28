#!/usr/bin/env node
/**
 * 使用 Playwright 获取 JS 渲染后的完整 DOM 和 WebGL 元数据
 *
 * Usage:
 *   node fetch-rendered-dom.mjs <URL> [outDir]
 *
 * 首次运行会自动安装 playwright 到 ~/.cache/playwright-runner/
 *
 * 输出到 outDir (默认 /tmp/rendered):
 *   dom.html         — 完整渲染后 HTML
 *   canvas-info.json — 所有 canvas 元素的信息
 *   webgl-info.json  — WebGL 上下文元数据
 *   console.log      — 页面 console 输出
 *   screenshot.png   — 页面截图
 *   network.json     — 运行时加载的 JS/资源 URL
 */

import { execSync } from 'child_process';
import { existsSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

const url = process.argv[2];
const outDir = process.argv[3] || '/tmp/rendered';

if (!url) {
  console.error('Usage: node fetch-rendered-dom.mjs <URL> [outDir]');
  process.exit(1);
}

// Auto-install playwright to a persistent cache directory
const runnerDir = join(homedir(), '.cache', 'playwright-runner');
const pwDir = join(runnerDir, 'node_modules', 'playwright');
const chromiumMarker = join(runnerDir, '.chromium-installed');

if (!existsSync(pwDir)) {
  console.log('Installing playwright (one-time setup)...');
  mkdirSync(runnerDir, { recursive: true });
  writeFileSync(join(runnerDir, 'package.json'), '{"type":"module"}');
  try {
    execSync('npm install playwright', { cwd: runnerDir, stdio: 'inherit' });
  } catch {
    console.log('npm install failed, retrying with registry mirror...');
    execSync('npm install playwright --registry=https://registry.npmmirror.com', { cwd: runnerDir, stdio: 'inherit' });
  }
}

if (!existsSync(chromiumMarker)) {
  console.log('Installing chromium browser...');
  try {
    execSync('npx playwright install chromium', { cwd: runnerDir, stdio: 'inherit' });
  } catch {
    console.log('Chromium download failed, retrying with mirror...');
    execSync('PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright npx playwright install chromium', { cwd: runnerDir, stdio: 'inherit' });
  }
  writeFileSync(chromiumMarker, new Date().toISOString());
}

// Dynamic import from the cached location
const pw = await import(join(pwDir, 'index.mjs'));
const { chromium } = pw;

mkdirSync(outDir, { recursive: true });

const consoleLogs = [];
const networkRequests = [];

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 2,
});
const page = await context.newPage();

// Capture console
page.on('console', msg => {
  consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
});

// Capture network (JS, WASM, bin, glsl, image files)
page.on('response', async response => {
  const reqUrl = response.url();
  const type = response.headers()['content-type'] || '';
  if (/\.(js|mjs|wasm|bin|glsl|frag|vert|svg)(\?|$)/.test(reqUrl) || type.includes('javascript')) {
    networkRequests.push({
      url: reqUrl,
      status: response.status(),
      type: type.split(';')[0],
      size: parseInt(response.headers()['content-length'] || '0'),
    });
  }
});

console.log(`Navigating to ${url} ...`);
await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

// Wait for WebGL initialization
await page.waitForTimeout(3000);

// 1. Full rendered DOM
const html = await page.content();
writeFileSync(join(outDir, 'dom.html'), html);
console.log(`dom.html — ${html.length} bytes`);

// 2. Canvas info
const canvasInfo = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('canvas')).map((c, i) => ({
    index: i,
    outerHTML: c.outerHTML.slice(0, 500),
    width: c.width,
    height: c.height,
    clientWidth: c.clientWidth,
    clientHeight: c.clientHeight,
    dataEngine: c.dataset.engine || null,
    id: c.id || null,
    className: c.className || null,
    parentTag: c.parentElement?.tagName || null,
    parentClass: c.parentElement?.className?.slice(0, 100) || null,
  }));
});
writeFileSync(join(outDir, 'canvas-info.json'), JSON.stringify(canvasInfo, null, 2));
console.log(`canvas-info.json — ${canvasInfo.length} canvas(es) found`);

// 3. WebGL info
const webglInfo = await page.evaluate(() => {
  const canvas = document.querySelector('canvas');
  if (!canvas) return { error: 'no canvas found' };
  // Don't create new context, just report what we can
  return {
    found: true,
    width: canvas.width,
    height: canvas.height,
    dataEngine: canvas.dataset.engine || null,
  };
});
writeFileSync(join(outDir, 'webgl-info.json'), JSON.stringify(webglInfo, null, 2));
console.log(`webgl-info.json — ${JSON.stringify(webglInfo).slice(0, 100)}`);

// 4. Console logs
writeFileSync(join(outDir, 'console.log'), consoleLogs.join('\n'));
console.log(`console.log — ${consoleLogs.length} entries`);

// 5. Screenshot
await page.screenshot({ path: join(outDir, 'screenshot.png'), fullPage: false });
console.log(`screenshot.png — saved`);

// 6. Network requests
writeFileSync(join(outDir, 'network.json'), JSON.stringify(networkRequests, null, 2));
console.log(`network.json — ${networkRequests.length} JS/resource requests captured`);

await browser.close();
console.log(`\nDone. Files saved to ${outDir}`);
