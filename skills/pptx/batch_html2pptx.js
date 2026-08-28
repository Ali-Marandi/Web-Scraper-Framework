// batch_html2pptx.js
// Convert slide_*.html files into a single .pptx using html2pptx1.js.
//
// Two modes:
//
//  1) Single-directory mode (default — most common after Stage 4):
//       node batch_html2pptx.js <slides_dir> [output.pptx]
//     Converts every slide_*.html under <slides_dir> (sorted) into ONE pptx.
//     If [output.pptx] is omitted, the file is saved next to <slides_dir> as
//     <parent_basename>.pptx (e.g. .../my_deck/slides → .../my_deck/my_deck.pptx).
//
//  2) Batch mode (legacy — walks <base>/ppt_*/download/*/slides):
//       node batch_html2pptx.js --batch <base_dir>
//     Each slides/ folder becomes one .pptx, saved in the parent <name>/ folder.
//
// NODE_PATH=/share/hc/utils/superz/p-p-p-x/ppt0403/node_modules \
//   node batch_html2pptx.js <slides_dir>

const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');
const html2pptx = require(path.join(__dirname, 'html2pptx1.js'));

function safeReaddir(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true });
}

function findSlidesDirs(baseDir) {
  // Match: <baseDir>/ppt_*/download/*/slides
  const results = [];
  for (const pptDir of safeReaddir(baseDir)) {
    if (!/^ppt_/.test(pptDir.name) || !pptDir.isDirectory()) continue;
    const downloadDir = path.join(baseDir, pptDir.name, 'download');
    for (const sub of safeReaddir(downloadDir)) {
      if (!sub.isDirectory()) continue;
      const slidesDir = path.join(downloadDir, sub.name, 'slides');
      if (fs.existsSync(slidesDir) && fs.statSync(slidesDir).isDirectory()) {
        results.push(slidesDir);
      }
    }
  }
  return results;
}

function collectHtmlFiles(slidesDir) {
  return fs.readdirSync(slidesDir)
    .filter(f => /^slide.*\.html$/i.test(f))
    .sort()
    .map(f => path.join(slidesDir, f));
}

async function buildPptxFromDir(slidesDir, outputPath, options = {}) {
  const { strict = false, fontConfig = null, concurrency = 4 } = options;
  const htmlFiles = collectHtmlFiles(slidesDir);

  if (htmlFiles.length === 0) {
    console.log(`  [skip] no slide_*.html in ${slidesDir}`);
    return null;
  }

  console.log(`  ${htmlFiles.length} slides → ${outputPath} (concurrency=${concurrency})`);

  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';

  // Pre-allocate slides in HTML-file order so final slide order is deterministic
  // regardless of parallel completion order. html2pptx will populate each
  // pre-allocated slide via the `slide` option instead of calling addSlide().
  const tasks = htmlFiles.map((htmlFile) => ({
    htmlFile,
    slide: pptx.addSlide(),
  }));

  const failures = [];
  const mustFix = [];
  let nextIndex = 0;
  let doneCount = 0;
  const total = tasks.length;

  async function worker() {
    while (true) {
      const i = nextIndex++;
      if (i >= total) return;
      const { htmlFile, slide } = tasks[i];
      const base = path.basename(htmlFile);
      console.log(`    [start ${i + 1}/${total}] ${base}`);
      try {
        const { warnings } = await html2pptx(htmlFile, pptx, { fontConfig, slide });
        if (warnings && warnings.length > 0) {
          warnings.forEach(w => {
            // Severe overflow is a must-fix signal — surface it loudly but do
            // NOT block output (pptx still writes, exit code stays 0).
            if (w.includes('MUST FIX')) {
              mustFix.push({ file: base, message: w });
              console.error(`      ${base}: ${w}`);
            } else {
              console.warn(`      ${base}: ${w}`);
            }
          });
        }
      } catch (err) {
        console.error(`      [error] ${base}: ${err.message}`);
        failures.push({ file: htmlFile, error: err });
        if (strict) throw err;
      } finally {
        doneCount++;
        console.log(`    [done  ${doneCount}/${total}] ${base}`);
      }
    }
  }

  const workerCount = Math.max(1, Math.min(concurrency, total));
  await Promise.all(Array.from({ length: workerCount }, () => worker()));

  if (failures.length > 0) {
    console.warn(`  ${failures.length} slide(s) failed during conversion.`);
  }

  // Severe-overflow slides do not block output, but they MUST be fixed — print a
  // consolidated, hard-to-miss list so the caller knows exactly what to re-render.
  if (mustFix.length > 0) {
    console.error(`\n  🚨🚨 ${mustFix.length} slide(s) with SEVERE overflow — MUST FIX and re-run:`);
    mustFix.forEach(({ file, message }) => console.error(`     - ${file}: ${message}`));
    console.error('');
  }

  await pptx.writeFile({ fileName: outputPath });
  console.log(`  saved: ${outputPath}`);
  return outputPath;
}

function defaultOutputPath(slidesDir) {
  // Save the pptx next to the slides/ folder (one folder up),
  // named after the parent directory.
  const parentDir = path.dirname(path.resolve(slidesDir));
  return path.join(parentDir, `${path.basename(parentDir)}.pptx`);
}

async function runSingle(slidesDir, outputPath, options = {}) {
  if (!fs.existsSync(slidesDir) || !fs.statSync(slidesDir).isDirectory()) {
    throw new Error(`slides_dir not found or not a directory: ${slidesDir}`);
  }
  const out = outputPath || defaultOutputPath(slidesDir);
  await buildPptxFromDir(slidesDir, out, options);
}

async function runBatch(baseDir, options = {}) {
  const slidesDirs = findSlidesDirs(baseDir);
  console.log(`Found ${slidesDirs.length} slides directories under ${baseDir}`);

  for (const slidesDir of slidesDirs) {
    const label = path.relative(baseDir, slidesDir);
    console.log(`\nProcessing: ${label}`);
    try {
      const parentDir = path.dirname(slidesDir);
      const outputPath = path.join(parentDir, `${path.basename(parentDir)}.pptx`);
      await buildPptxFromDir(slidesDir, outputPath, options);
    } catch (err) {
      console.error(`  [error] ${slidesDir}: ${err.message}`);
      if (options.strict) throw err;
    }
  }
}

function printUsageAndExit(code = 1) {
  console.error(
    'Usage:\n' +
    '  node batch_html2pptx.js [--strict] [--concurrency=N] <slides_dir> [output.pptx]\n' +
    '  node batch_html2pptx.js [--strict] [--concurrency=N] --batch <base_dir>\n'
  );
  process.exit(code);
}

async function main() {
  const args = process.argv.slice(2);
  const strict = args.includes('--strict');

  let concurrency = 8;
  const concIdx = args.findIndex(a => a === '--concurrency' || a.startsWith('--concurrency='));
  if (concIdx !== -1) {
    const arg = args[concIdx];
    if (arg.includes('=')) {
      concurrency = parseInt(arg.split('=')[1], 10);
    } else {
      concurrency = parseInt(args[concIdx + 1], 10);
    }
    if (!Number.isFinite(concurrency) || concurrency < 1) {
      console.error(`invalid --concurrency value`);
      process.exit(1);
    }
  }

  const filteredArgs = args.filter((arg, i) => {
    if (arg === '--strict') return false;
    if (arg === '--concurrency' || arg.startsWith('--concurrency=')) return false;
    if (concIdx !== -1 && !args[concIdx].includes('=') && i === concIdx + 1) return false;
    return true;
  });

  if (filteredArgs.length === 0) printUsageAndExit();

  const runOpts = { strict, concurrency };

  if (filteredArgs[0] === '--batch') {
    if (!filteredArgs[1]) printUsageAndExit();
    await runBatch(filteredArgs[1], runOpts);
  } else if (filteredArgs[0] === '--dir') {
    // Backwards-compatible alias for batch mode.
    if (!filteredArgs[1]) printUsageAndExit();
    await runBatch(filteredArgs[1], runOpts);
  } else {
    const slidesDir = filteredArgs[0];
    const outputPath = filteredArgs[1];
    await runSingle(slidesDir, outputPath, runOpts);
  }

  console.log('\nDone.');
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
