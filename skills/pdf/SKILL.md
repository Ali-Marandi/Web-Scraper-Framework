---
name: pdf
metadata:
  author: Z.AI
  version: "1.0"
description: "Professional PDF toolkit with four production lines:(1) Report - structured documents via ReportLab (reports, proposals, contracts, white papers); (2) Creative - visual design via JSON Blueprint → design_engine.py → Playwright snapshot (posters, infographics, invitations, dashboards). The LLM acts as Art Director outputting ONLY JSON spatial blueprints; convert.blueprint compiles to pixel-perfect PDF. (3) Academic - scholarly work via LaTeX/Tectonic (papers, theses, math-heavy documents); (4) Process - manipulate existing PDFs (extract, merge, split, fill forms, convert);Auto-routes based on document type. Includes ATS/creative/academic resume sub-paths."
license: Proprietary. LICENSE.txt has complete terms
---

# PDF - Document Production Workbench

## Script Path Setup (MANDATORY before any script call)

All paths are relative to `$PDF_SKILL_DIR`. Resolve it once before calling any script:

```bash
PDF_SKILL_DIR="<skill_directory>"   # ← parent directory of this SKILL.md
```

**For Python imports** (when generation code needs to import skill modules):

```python
import sys, os
PDF_SKILL_DIR = "<skill_directory>"
_scripts = os.path.join(PDF_SKILL_DIR, "scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)
```

## Triage

Determine task weight to control how much context to load:

| Weight | Triggers | What to Load |
|--------|----------|--------------|
| **Light** | Format conversion, form fill, text extract, merge/split, simple certificate | SKILL.md + `briefs/process.md` only |
| **Standard** | Multi-page report, poster, academic paper, resume, reformat - any document with design decisions | SKILL.md + `configs/fonts.md` + matched brief + **ALL files referenced by the brief** (typesetting, configs, etc.) |
 
### ⚠️ Pre-Routing Checks (run BEFORE matching brief)

1. **Emoji Check** - Scan user content for intentional emoji (decorative 📊🎯🔥, not OS-level emoji input). If found → **force Creative pipeline** (Fixed-Canvas or Flow depending on document type) regardless of original routing. ReportLab renders emoji as □ squares; LaTeX drops them entirely.
2. **CJK Check** - Chinese/Japanese/Korean content needs font coverage. Report brief must register CJK fonts - **probe first** with `ls /usr/share/fonts/truetype/chinese/` (Linux) or check `$FONT_DIR` (macOS) to confirm which fonts exist, then register accordingly (prefer NotoSerifSC > Noto Sans SC; never hardcode a font name without verifying it exists). Creative Fixed-Canvas and Creative Flow briefs must load Google Fonts Noto Sans SC with `font-display: swap`; Academic brief must use `\usepackage{ctex}`.
3. **Size Check** - Non-standard page sizes (not A4/Letter/A3) → prefer Creative brief (Playwright handles any dimension). ReportLab can do custom sizes but pagination is manual.
4. **Character Safety Check** - Before writing any content string, scan for Japanese kana (の、が、は etc.), unusual Unicode symbols, or non-CJK characters that may corrupt during encoding transit ( Especially when code is written via heredoc/base64/LLM output). Replace with plain Chinese equivalents: `の`→`之/的/缔`, `々`→omit or write full character. **If content must preserve Japanese, use only standard CJK Unified Ideographs (U+4E00-U+9FFF) and common kana; avoid rare/private-use codepoints.**

---

## Briefing

Match the user's intent to a production brief. Each brief contains the full workflow, tech stack specifics, and references to shared typesetting assets.

```
User Request
│
├─ Work with existing PDF? ─────────────┬─ Extract/merge/split/fill/convert → briefs/process.md
│                                       ├─ Reformat/redesign → briefs/process.md (extract) → delegate to report or creative brief
│                                       └─ User provides a PDF template/reference to match style
│                                          → briefs/process.md "Template-Guided Reformat" → delegate to matched brief
│
├─ Report / proposal / white paper / contract / analysis?
│  └─ ────────────────────────────────── → briefs/report.md   (ReportLab)
│
├─ Poster / invitation / infographic / dashboard / creative layout?
│  └─ ────────────────────────────────── → briefs/creative-fixed-canvas.md  (Playwright, fixed-canvas)
│
├─ Guide / handbook / catalog / introduction / collection (text-heavy + design)?
│  └─ ────────────────────────────────── → briefs/creative-flow.md  (Playwright, flowing content)
│
├─ Academic paper / thesis / math / IEEE / ACM / LaTeX?
│  └─ ────────────────────────────────── → briefs/academic.md  (Tectonic)
│
├─ Math-heavy doc / TikZ diagram / algorithm pseudocode / Beamer slides?
│  └─ ────────────────────────────────── → briefs/academic.md  (Tectonic, Scenarios A-D)
│
├─ Document needs complex embedded diagrams (flowcharts, architecture, neural nets)?
│  └─ Route by target brief:
│     ├─ Report → Playwright+CSS → PNG → ReportLab Image() flowable
│     ├─ Creative → directly in HTML (CSS flexbox/grid + connectors)
│     └─ Academic → complexity-based:
│        ├─ Simple (≤6 nodes, linear/tree) → TikZ native (vector)
│        └─ Complex (>6 nodes, branches, annotations) → Playwright+CSS → PNG → \includegraphics
│
└─ Resume / CV?
   ├─ ATS-safe / corporate ─────────── → briefs/resume.md
   ├─ Creative / design industry ────── → briefs/creative-fixed-canvas.md   (resume sub-section)
   └─ Academic CV / publications ────── → briefs/academic.md   (resume sub-section)
```

### Detection Keywords

| Brief | Keywords |
|-------|----------|
| Report | 报告, report, 分析, analysis, 白皮书, white paper, 提案, proposal, 合同, contract, 方案, 规划, 发票, invoice, 收据, receipt, 试卷, exam, quiz, test paper, 练习, exercise, worksheet, 考试, 测验 |
| Creative Fixed-Canvas | 海报, poster, 邀请函, invitation, 信息图, infographic, 仪表盘, dashboard, 传单, flyer, 证书, certificate, 菜单, menu, 名片, business card, 奖状, award, 标签, label, 信封, envelope, 贺卡, greeting card → `briefs/creative-fixed-canvas.md` |
| Creative (Poster) | 海报, poster, 传单, flyer, 宣传页, 宣传单 → additionally load `briefs/poster.md` scene layer rules on top of creative-fixed-canvas.md |
| Creative Flow | 图鉴, guide, 手册, handbook, 目录, catalog, 介绍, introduction, 合集, collection → `briefs/creative-flow.md` |
| Academic | 论文, paper, 学术, academic, LaTeX, 数学, math, IEEE, ACM, 毕业, thesis, 研究, research, Beamer, slides, 开题报告, 学位, dissertation, proposal |
| Process | 提取, extract, 合并, merge, 拆分, split, 填写, fill, 转换, convert, OCR, 重排, reformat, 重新排版, redesign, 模板, template, 参照, 照着这个做, match this style, 压缩, compress, 水印, watermark, 加密, encrypt, 签名, sign |

### Complete Scenario Routing Matrix

Below is an exhaustive map of every known PDF request type to its handling strategy. If a scenario is not listed, route to the closest match or ask the user.

#### Creation (Generate PDF from scratch)

| Scenario | Route | Notes |
|----------|-------|-------|
| Report / white paper / analysis | report.md | ReportLab structured document |
| Report with emoji | **creative-fixed-canvas.md** |  Emoji rule override |
| Business proposal | report.md | Structured + data tables |
| Contract / legal document | report.md | Add signature placeholders (dotted line + label) |
| Invoice / receipt | report.md | Table-heavy, precision alignment |
| Exam / quiz / test paper / worksheet | report.md | Indented options, answer space reservation, structured numbering (see Exam Paper Rules in report.md) |
| Math exam / math worksheet (with formulas/equations) | academic.md | LaTeX for proper math typesetting. See §Exam Paper Rules in academic.md |
| Poster / flyer | creative-fixed-canvas.md + **poster.md** | Visual design + poster density/sizing rules |
| Invitation / greeting card | creative-fixed-canvas.md | Non-standard size, decorative |
| Certificate / award | creative-fixed-canvas.md | Single page, centered layout, decorative border |
| Business card | creative-fixed-canvas.md | Tiny size (90×54mm), Playwright native support |
| Envelope / label | creative-fixed-canvas.md | Non-standard size, simple layout |
| Menu / price list | creative-fixed-canvas.md | Visual layout + may contain emoji |
| Resume (ATS) | resume.md | Plain text structure |
| Resume (creative) | creative-fixed-canvas.md | Visual design |
| Resume (academic CV) | academic.md | Publication list + BibTeX |
| Academic paper | academic.md | LaTeX/Tectonic |
| Math-heavy document | academic.md | LaTeX typesetting |
| Presentation / PPT-style | creative-fixed-canvas.md | Landscape (1280×720), one topic per page |
| Book / long document | report.md | Add TOC + chapter numbering, validate with toc_validate.py |
| CJK vertical text | creative-fixed-canvas.md | HTML `writing-mode: vertical-rl` + `text-orientation: upright` + `white-space: nowrap` + Playwright |
| RTL document (Arabic/Hebrew) | creative-fixed-canvas.md | HTML `dir="rtl"` + Playwright |
| Batch generation (mail merge) | report.md | Python loop + template variable substitution |
| Infographic | creative-fixed-canvas.md | Data visualization + design |
| Calendar / schedule | creative-fixed-canvas.md | Grid layout + custom dimensions |
| Guide / handbook / catalog / introduction / collection | creative-flow.md | Flowing-document mode — text-heavy with design flair, content flows across pages naturally |

#### Processing (Manipulate existing PDF)

| Scenario | Route | Command / Method |
|----------|-------|------------------|
| Merge multiple PDFs | process.md | `pages.merge a.pdf b.pdf -o out.pdf` |
| Split PDF | process.md | `pages.split input.pdf -o ./output/` |
| Extract text | process.md | `extract.text input.pdf` |
| Extract tables | process.md | `extract.table input.pdf` |
| Extract images | process.md | `extract.image input.pdf` |
| Fill forms | process.md | `form.fill input.pdf` |
| Office → PDF | process.md | `convert.office input.docx` |
| HTML → PDF (documents) | process.md | `convert.html input.html` or `node html2pdf-next.js` |
| HTML → PDF (posters) | poster.md | `node html2poster.js poster.html` |
| Image → PDF | process.md | pikepdf: one image per page, embed as XObject |
| PDF → image | process.md | pypdfium2 render each page to PNG |
| Encrypt / decrypt | process.md | qpdf / pypdf encryption |
| Add watermark | process.md | pikepdf overlay: create watermark page → merge onto each page |
| Compress PDF | process.md | Ghostscript: `gs -sDEVICE=pdfwrite -dPDFSETTINGS=/screen` |
| OCR scanned PDF | process.md | pytesseract + pdf2image |
| Rotate pages | process.md | `pages.rotate input.pdf 90 -o out.pdf` |
| Crop pages | process.md | `pages.crop input.pdf l,b,r,t -o out.pdf` |
| Remove blank pages | process.md | `pages.clean input.pdf` |
| Reformat by template | process.md → delegate | Extract content → regenerate via report/creative |
| PDF diff / compare | process.md | `diff-pdf` CLI or Python per-page text comparison |
| Digital signature | process.md | `pyhanko` library (requires extra install) |
| Edit metadata | process.md | `meta.set input.pdf -o out.pdf -d '{...}'` |

### Special Routing Rules

** Emoji rule (CRITICAL - check FIRST)**: Content with intentional emoji (📊🎯🔥💡 etc.) → force **Creative pipeline** (use `briefs/creative-fixed-canvas.md` for visual-first designs, `briefs/creative-flow.md` for text-heavy documents) regardless of original routing. ReportLab renders emoji as □ squares; LaTeX silently drops them. This rule overrides Report/Academic routing. Even if the user says "report" - if the content has emoji, use a Creative brief.

**Non-standard page size rule**: Dimensions other than A4/Letter/A3 → strongly prefer **Creative pipeline** (`briefs/creative-fixed-canvas.md` or `briefs/creative-flow.md`). Playwright handles any arbitrary page size natively. ReportLab requires manual pagination math.

**Academic auto-detect**: Papers, theses, or heavy math → **briefs/academic.md** even without explicit "LaTeX" mention.

**Template-guided rule**: When the user uploads a PDF and says "match this template" / "follow this style" / "reformat like this" → **briefs/process.md** Template-Guided Reformat section. This is a Standard triage (not Light), because it involves design decisions.

**Resume routing**: Default to Resume brief (ATS-safe). Creative industry → Creative brief. Academic CV with publications → Academic brief.

---

## Shared Assets

These are referenced by multiple briefs. Each brief tells you when and what to load.

| Asset | Path | Used By | Purpose |
|-------|------|---------|---------|
| Palette & Typography | `typesetting/palette.md` | Report, Fixed-Canvas, Flow | Color system, font rules, anti-patterns, spacing |
| Cover Layout System V2.1 | `typesetting/cover.md` | **Report + Fixed-Canvas + Flow + Academic** | 5 industrial-grade templates with absolute anchor grid, Z-index layers, typography weight system, mandatory Summary Block, code-level safety (5 checks), base unit `U = W*0.05`. **Unified HTML/Playwright cover system for all routes.** |
| Chart Styling & Anti-Stacking | `typesetting/charts.md` | Report, Fixed-Canvas, Flow, Academic | Chart defaults, collision prevention, axis/grid/legend rules |
| Overflow Prevention | `typesetting/overflow.md` | Report, Fixed-Canvas, Flow, Academic | Bounding box system, text/image/table overflow prevention, fallback strategies |
| **Fill Engine (Anti-Void)** | `typesetting/fill-engine.md` | **Report, Fixed-Canvas, Academic** | **Anti-Void Engine V2.0: font floor enforcement, fill ratio calculation, paragraph inflation, component elevation, Y-axis golden-ratio anchoring** |
| Pagination & Flow Control | `typesetting/pagination.md` | Report, Fixed-Canvas, Flow | Cross-page integrity, orphan/widow control, CJK punctuation rules |
| Typography System | `typesetting/typography.md` | Report, Fixed-Canvas, Flow | Font size scale, line-height, spacing hierarchy |
| Geometric Anchors | `typesetting/geometry.md` | Creative + Report | Decorative geometric elements, anchor placement rules |
| Cover Backgrounds | `typesetting/cover-backgrounds.md` | **Report + Fixed-Canvas + Flow + Academic** | Cover background rendering, transparency constraints |
| Visual Framework | `configs/visual_framework.md` | Fixed-Canvas | Palette mode, color harmony, SVG background params |
| Components Library | `configs/components.md` | Fixed-Canvas | Non-grid composition components (floating cards, oversized text, etc.) |
| Font Stacks | `configs/fonts.md` | All pipelines | Font families per pipeline (Google Fonts, ReportLab, LaTeX) |

---

## Content Rules

- **Language**: Match user's query language. Chinese query → Chinese PDF.
- **Page/word count**: Respect explicit constraints (±20%). Unspecified → completeness over brevity.
- **Outline**: User-provided outlines are sacred. No reordering without asking.
- **Citations**: No fabrication. Chinese → GB/T 7714, English → APA. Search to verify.
- **Multi-part requests**: Generate ALL parts - never silently drop a component.

### Content Depth and Richness Standards (Anti-Shallow Writing)

**PROBLEM TO AVOID**: Shallow content with paragraphs containing only 1-2 sentences, or sections with minimal text under headings.

#### Minimum Content Standards

1. **Paragraph Depth**
   - Each paragraph MUST contain at least 3-5 sentences
   - Single-sentence paragraphs are FORBIDDEN (except for transitional statements)
   - Each paragraph should develop ONE complete idea with supporting details

2. **Section Completeness**
   - Each section heading MUST be followed by substantial content (minimum 150-200 words)
   - NEVER create a section with only 1-2 short sentences
   - If a section cannot meet minimum length, merge it with related sections

3. **Content Enrichment Techniques**
   - Include specific examples, data points, or case studies
   - Provide context and background information
   - Explain the "why" and "how", not just the "what"
   - Add comparisons, contrasts, or alternative perspectives where relevant
   - Include implications, consequences, or recommendations

#### Writing Quality Checklist

Before finalizing ANY written document, verify:
- [ ] No paragraph has fewer than 3 sentences
- [ ] No section has fewer than 150 words of body content
- [ ] Each main point is supported by examples or evidence
- [ ] Technical terms are explained when first introduced
- [ ] Transitions connect ideas between paragraphs and sections

#### Content Expansion Strategies

When writing feels thin, apply these techniques:

**For Analysis/Reports:**
- Add background context (history, current state, trends)
- Include multiple perspectives or stakeholder views
- Provide specific metrics, statistics, or quantitative data
- Discuss limitations, challenges, or counterarguments
- Offer actionable recommendations with rationale

**For Explanatory Content:**
- Use analogies to clarify complex concepts
- Provide step-by-step breakdowns where applicable
- Include real-world applications or use cases
- Address common questions or misconceptions
- Add visual descriptions or diagram explanations

**FORBIDDEN PATTERNS:**
- Section with heading followed by only 1-3 sentences
- Bullet lists without explanatory context
- Conclusions that merely restate the introduction
- Sections that say "as mentioned above" without adding new value

### Language Consistency Rule

Always use the same language as the user's input language for:
- The response and document content
- Any generated report, PDF, or plot/diagram
- **Cover page**: All text on the cover (title, subtitle, tags, author, footer) MUST match the user's prompt language. Chinese prompt → Chinese cover; English prompt → English cover. Mixing is forbidden.
- **Charts and figures**: Before generating any chart or figure, determine the user's language. Ensure that the title, legend, labels, and other textual elements are consistent with the user's language. If any element cannot use the user's language, explicitly explain the reason.

### HTML Image Source Path Rules

When embedding images in HTML documents (Creative pipeline, Playwright-rendered diagrams, or any HTML→PDF flow):

| Image location | `<img src>` value | Example |
|---|---|---|
| **Local file** | **Relative path** from the HTML file's directory | `<img src="images/chart.png">` or `<img src="./diagram.png">` |
| **Remote URL** | Full URL (no change needed) | `<img src="https://example.com/photo.jpg">` |

**Iron rules:**
1. **NEVER use absolute paths** for local files in HTML `<img>`, `<source>`, CSS `url()`, or any other asset reference (e.g. `/Users/alice/project/img.png`). Absolute paths break portability across machines and environments.
2. **Always use relative paths** anchored to the HTML file's own directory. If the image lives in a subdirectory, use `images/foo.png` or `./images/foo.png`.
3. **Remote URLs (`http://` / `https://`) are fine as-is** - do not convert them to local paths.
4. When generating HTML from a script or blueprint, ensure all referenced assets are either (a) in the same directory as the output HTML, or (b) in a clearly named subdirectory (e.g. `assets/`, `images/`), and referenced with relative paths.
5. If a build script needs to resolve paths programmatically, compute relative paths at generation time (e.g. `os.path.relpath(image_path, html_dir)`) rather than embedding absolute filesystem paths.

---

## Figure & Diagram Embedding (All Briefs)

### Iron Rule: Figures Are Block-Level

Figures, diagrams, and charts MUST be independent block elements occupying full width. **Never** float/wrap figures alongside body text - this causes the text-diagram overlap badcase.

| Brief | Correct embedding | Forbidden |
|-------|-------------------|-----------|
| Report (ReportLab) | `story.append(Image(...))` as standalone Flowable | Placing images inside Paragraph text, simulating float |
| Creative (Playwright) | `<figure style="display:block; width:100%; margin:2em auto">` | `float:right`, `display:flex` with text, `wrapfigure`-style CSS |
| Academic (LaTeX) | `\begin{figure}[t] ... \end{figure}` | Bare `\includegraphics` in text body (no figure env), bare `tikzpicture` in multi-column |

### Complex Diagram Strategy

When a diagram has **>12 nodes, >3 subgroups, or intricate connections**, do NOT try to render it as one giant figure. Instead:

1. **Table for details** - structured data (phases, components, specs) goes into a proper table
2. **Simplified overview diagram** - a stripped-down flowchart/Mermaid showing only the top-level flow (≤8 nodes)
3. **Cross-reference** - table caption + diagram caption reference each other

This "table + simple diagram" pattern prevents:
- Diagrams overflowing page boundaries
- Text becoming unreadably small to fit everything
- Layout engines mishandling oversized graphics

### Diagram Content Quality Rules (Cross-reference: charts)

The rules above handle **how** to embed diagrams in PDF. For **what the diagram itself looks like** (node layout, connector routing, color, readability), follow the `charts` skill rules:

**Before generating ANY flowchart/diagram for PDF embedding, check these:**

1. **Connectors must not pass through nodes** - If 3+ layers exist, connect adjacent layers only (top→mid, mid→bottom). Never draw top→bottom lines through middle nodes. Use detour paths if cross-layer links are needed.
2. **Multiple arrows into one node must not pile up** - Distribute entry points evenly along target edge, or use merge-then-enter pattern (sources converge to a vertical merge line, then single arrow to target).
3. **Low-saturation fills only** - Node backgrounds must be pale (`#EFF6FF`, `#F0FDF4`). High-saturation colors (`#3B82F6`, `#10B981`) only for borders or small accents. No children's-art color schemes.
4. **Phase titles vs sub-steps must be visually distinct** - Different background color, font size, and font weight. Never same-style boxes for both.
5. **Font sizes must be readable at final output size** - Sizes depend on the embedding context:
   | Output context | Node title min | Description min | Label min |
   |---------------|----------------|-----------------|-----------|
   | Standalone PNG (web/presentation, ≥1200px wide) | 14px | 12px | 11px |
   | Embedded in A4 PDF (ReportLab/LaTeX, ~450pt content width) | 10pt | 8pt | 7pt |
   | Embedded in slide deck (landscape, ~720pt wide) | 12pt | 10pt | 9pt |

   **Principle**: After embedding, the smallest text in the diagram must still be legible when the document is viewed at 100% zoom. If the diagram is scaled down to fit page width, recalculate: `effective_size = original_size × (display_width / canvas_width)`. If effective size drops below the minimum, either increase original font size or reduce diagram complexity.
6. **Legend/annotations must not overlap content** - Separate container, ≥ 40px gap from last node, fully within canvas bounds.

**For Playwright-rendered diagrams**: Use low-saturation fills (`#EFF6FF`, `#F0FDF4`), CSS flexbox/grid for node layout, SVG `<line>`/`<path>` for connectors, and verify no overlap at final render size.
**For ReportLab-drawn diagrams**: Same principles apply - use `Drawing()` with explicit coordinates, check node bounding boxes for overlap before finalizing.

### Diagram Generation Strategy (Per-Brief)

Diagram rendering depends on the target brief - **NOT** a one-size-fits-all TikZ pipeline.

| Target Brief | Diagram Method | Rationale |
|---|---|---|
| **Report** (ReportLab) | Playwright+CSS → PNG → `Image()` | No LaTeX compiler in this route; HTML/CSS handles any layout natively |
| **Creative** (Playwright) | Directly in HTML (CSS flexbox/grid + JS connectors) | Already in browser context |
| **Academic** (Tectonic) - simple (≤6 nodes) | TikZ native `tikzpicture` | Vector output, font consistency, LaTeX-native |
| **Academic** (Tectonic) - complex (>6 nodes) | Playwright+CSS → PNG @2× → `\includegraphics` | TikZ branch logic is error-prone for models; 300dpi PNG is publication-ready |

**Playwright+CSS diagram pipeline (Report & Academic-complex):**

```bash
# 1. Write diagram HTML (CSS grid/flexbox + connectors)
cat > diagram.html << 'EOF'
<!-- LLM generates: nodes as divs, arrows as SVG/CSS -->
EOF

# 2. Screenshot at 2× for print quality (300dpi equivalent)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" convert.blueprint diagram.html --device-scale-factor 2 --output diagram.png
# Or via Playwright directly:
# page.screenshot(path='diagram.png', scale='device', device_scale_factor=2)

# 3a. Embed in ReportLab (Report brief)
from reportlab.platypus import Image
img = Image('diagram.png', width=450)  # auto height via aspect ratio
story.append(img)

# 3b. Embed in LaTeX (Academic brief, complex diagrams only)
# \includegraphics[width=\columnwidth]{diagram.png}
```

**🚫 FORBIDDEN for Report/Creative briefs:** Do NOT use TikZ standalone → compile → pdftoppm → PNG pipeline. This route has no LaTeX compiler and the extra compilation steps are error-prone.

**TikZ remains valid ONLY for:**
- Academic brief with simple diagrams (≤6 nodes, linear/hierarchical)
- Direct `tikzpicture` embedding in LaTeX documents
- Math-annotated diagrams where LaTeX math rendering matters

See `briefs/academic.md` Scenario B for TikZ templates (simple diagrams only).

---

## Vector Rendering Iron Rule

**The final PDF MUST be generated via `page.pdf()` (Playwright) or ReportLab/LaTeX native output - NEVER via screenshot-to-PDF.**

| Scenario | Correct Method | Forbidden |
|----------|---------------|-----------|
| Creative pipeline (single/multi-page) | `page.pdf()` via `convert.blueprint` or `html2pdf-next.js` | `page.screenshot()` → image → wrap as PDF |
| Report cover (HTML/Playwright) | `page.pdf()` → merge via pypdf | Screenshot cover → embed as image |
| Academic cover | `page.pdf()` → merge via pypdf | Screenshot → `\includegraphics` for cover |
| Full-page posters/infographics | `html2poster.js` (auto overflow:hidden + height measurement + `page.pdf()`) | Any raster pipeline for the final output |

**Why:** `page.pdf()` produces vector text + vector shapes. Text remains selectable, sharp at any zoom, and file size is smaller. Screenshot-based PDFs are raster images - blurry when zoomed, unsearchable, and 3-5× larger.

**The ONLY place screenshot/PNG embedding is acceptable:**
- **Diagrams** embedded as sub-elements inside a larger document (e.g., flowcharts in a Report). These use `page.screenshot()` at 2× device scale factor for 300dpi print quality, then embed via `Image()` (ReportLab) or `\includegraphics` (LaTeX).
- **Chart images** generated by matplotlib/plotly saved as PNG, then embedded.

These are sub-elements, not the document itself. The document-level PDF output must always be vector.

**Quick test:** Open the generated PDF, zoom to 400%. If text is blurry, you used a screenshot pipeline. Fix it.

### HTML→PDF Engine Selection Rules

There are **two dedicated scripts** for HTML→PDF. Choose based on document type:

| Document type | Script | Reason |
|---------------|--------|--------|
| **Posters, infographics, long-image single-page designs** | `html2poster.js` | Auto overflow:hidden, auto height measurement, zero margin, single-page output |
| **Cover pages (Report/Academic route)** | `html2poster.js` | Covers are single-page fixed layouts with absolute positioning - same nature as posters. `html2pdf-next.js` would convert absolute→static and destroy the layout |
| **Multi-page documents, reports, academic papers, resumes** | `html2pdf-next.js` | Paged.js pagination, A4/custom size, pdf-lib metadata. `--nopaged` for Chromium native fallback |
| **Creative pipeline (Blueprint → HTML → PDF)** | `html2pdf-next.js` via `convert.blueprint` | Called internally by design_engine pipeline |

#### Poster / Single-Page Long-Image → `html2poster.js`

```bash
node "$PDF_SKILL_DIR/scripts/html2poster.js" poster.html --output poster.pdf --width 720px
```

`html2poster.js` automatically:
- Forces `overflow: hidden` on `.poster` / `.page` containers (clips decorative overflow)
- Injects `@page { margin: 0 }` (zero margins always)
- Syncs `html/body` background with poster background color
- Measures `.poster` scrollHeight and uses it as PDF height
- Generates a single-page vector PDF with exact content dimensions

**Use this for ANY fixed-width, dynamic-height, single-page design.**

#### Documents / Multi-Page → `html2pdf-next.js`

```bash
node "$PDF_SKILL_DIR/scripts/html2pdf-next.js" input.html --output output.pdf --width 210mm --height 297mm
# Or via pdf.py wrapper:
python3 "$PDF_SKILL_DIR/scripts/pdf.py" convert.html input.html --output output.pdf
```

Pre-render hooks auto-handle Mermaid/KaTeX rendering, overflow detection, and font loading. **Paged.js polyfill** is injected for pagination (break-inside/before/after, orphans/widows, named pages). Use `--nopaged` flag to fall back to Chromium native @page pagination if needed.

#### ⚠️ Iron Rule: No Hand-Written Playwright Scripts

Common issues with hand-written Python `page.pdf()` (the dedicated scripts handle these automatically):
1. **Missing `@page` rule** → browser default margin causes content overflow to second page or white edges
2. **Oversized elements not fixed** → large elements with `break-inside: avoid` block pagination, content gets truncated
3. **Rendering before fonts are loaded** → Chinese text displays as squares or falls back to wrong font
4. **No overflow detection** → content exceeds page boundary without awareness
5. **No metadata** → PDF title, author, and other info missing

**Iron rule: Posters and cover pages use `html2poster.js`, multi-page documents use `html2pdf-next.js`. Do not write hand-written Python Playwright scripts.**

> **⚠️ Cover page gotcha:** Cover HTML uses `position: absolute` for layout. Always use `html2poster.js` for cover pages — `html2pdf-next.js` + Paged.js would re-layout absolute-positioned elements into flow, destroying the cover design.

### No overflow:hidden on Fixed-Size Pages

**NEVER set `overflow: hidden` on `html`, `body`, `.page`, or the main container** in HTML intended for PDF conversion. Paged.js handles content chunking and pagination natively — it does not need overflow clipping.

> **Note:** This rule does NOT apply to posters rendered via `html2poster.js` - that script automatically adds `overflow: hidden` to `.poster`/`.page` containers to clip decorative overflow.

| Problem | Cause | Fix |
|---------|-------|-----|
| Content silently clipped at page boundaries | `overflow: hidden` on container hides content exceeding bounds | Remove `overflow: hidden`; Paged.js handles pagination |
| Decorative elements inflate scrollWidth | `width > 100%` or negative offsets on absolutely-positioned elements | Constrain within page bounds (see creative-fixed-canvas.md §0.75) |

**Always pair fixed-size pages with `@media screen` auto-scale** so the full page is visible in any browser window without scrolling. See `briefs/creative-fixed-canvas.md` § 0.5 for the CSS pattern.

### Full-Bleed Rule (No White Margins)

When generating HTML for Playwright `page.pdf()`, the content **MUST fill the entire page** with zero margins. White side margins = broken layout.

**Mandatory CSS for any HTML → PDF:**
```css
@page {
  size: <width> <height>;  /* e.g., 720px 960px, or A4 */
  margin: 0;
}
html, body {
  margin: 0;
  padding: 0;
}
```

**Common causes of white margins:**
1. Missing `@page { margin: 0 }` - browser default margins kick in (~1cm each side)
2. Content width doesn't match page width - e.g., canvas is 720px but page is A4 (794px)
3. Missing `@page { size }` declaration in the HTML
4. Content has explicit `max-width` that's narrower than the page

**For blueprint pipeline:** `design_engine.py` now injects `@page { size: var(--canvas-w) var(--canvas-h); margin: 0; }` automatically.
**For raw HTML:** YOU must include the `@page` rule. No exceptions.
**For direct Playwright:** Pass `margin: { top: 0, right: 0, bottom: 0, left: 0 }` to `page.pdf()`.

### Background Color Consistency (No Color Mismatch)

**`html` / `body` background color must match the content canvas background color.**

Playwright `page.pdf({ printBackground: true })` renders the body background color. If body is white while the content area is gray/colored, color-inconsistent borders/gaps will appear in the PDF.

#### Single-color documents (all pages same background)

```css
/* MANDATORY: body background = content background */
html, body {
  margin: 0;
  padding: 0;
  background: var(--c-bg);  /* Same color as content canvas */
}
```

#### Multi-page documents with mixed backgrounds (e.g. dark cover + white body pages)

**Root cause:** Playwright resolves `.page { width: 210mm }` and `@page { size: 210mm }` to slightly different sub-pixel values (e.g. 793.688px vs 793.701px). This creates a <1px gap at the right/bottom edge of each `.page` div where `body`'s background shows through. On dark pages, a white `body` background makes this gap visible as a white edge.

**Fix - set `body` background to the document's dominant dark color:**

```css
:root {
  --primary: #0f172a;  /* darkest page background */
}
html, body {
  margin: 0;
  padding: 0;
  width: 210mm;  /* match @page size */
  background: var(--primary);  /* fallback for sub-pixel gaps */
}
```

**Why this works and doesn't break white pages:**
- Dark pages: sub-pixel gap reveals dark `body` → gap invisible.
- White pages: `.page-white { background: #ffffff }` fully covers `body` → dark body never visible.
- The gap is <1px - even on white pages, the dark body at the extreme pixel edge is imperceptible after anti-aliasing.

**Rule: when generating multi-page HTML with mixed backgrounds, always set `html, body { background }` to the darkest page's background color.** If all pages are light/white, use the lightest content background (e.g. `#f8fafc`). Never leave `body` background unset (browser default = white = guaranteed white edges on dark pages).
```

### Content Centering (No Left/Right Drift)

**After HTML-to-PDF conversion, content must be centered, no left or right drift allowed.**

Common drift causes:
1. `@page { margin }` not 0 - browser default margin causes drift
2. `.safe-zone` or content container `inset` / `padding` left-right asymmetric
3. Content container has `max-width` but no `margin: 0 auto`
4. Grid components only occupy partial column width (e.g. `1/1 → X/7` only uses left half)
5. **Decorative elements overflow page boundary** - elements with `width > 100%` or negative offsets (e.g. glow circles, gradient overlays) inflate `scrollWidth` beyond page width. Playwright shrinks all content to fit, causing left-shift. **Fix: constrain decorative elements within page bounds** (`width` ≤ 100%, no negative `left`/`right` offsets). See `briefs/creative-fixed-canvas.md` §0.75 and `typesetting/overflow.md` §3.5 for details.

### Anti-Void Edges (No Large Blank Margins)

**Content should not have large meaningless whitespace at page edges, top, or bottom.**

- Content should make full use of page area; do not cram all content in the top half while leaving the bottom blank
- For multi-page documents, each page's fill rate should be ≥ 60% (see `pagination.md` last page ≥ 40% rule)
- For single-page posters/infographics, fill rate should be ≥ 70%

---

## Preflight (Quality Assurance)

Every PDF must pass preflight checks before delivery. Each brief specifies the exact commands.

### HTML Pre-Render Validation (MANDATORY for ALL HTML→PDF paths)

**Before** calling `html2pdf-next.js`, `html2poster.js`, `convert.blueprint`, or any Playwright `page.pdf()`, run:

```bash
python3 "$PDF_SKILL_DIR/scripts/poster_validate.py" check-html <your_file>.html
```

| Result | Action |
|--------|--------|
| **PASS** (no errors) | Proceed to PDF generation |
| **ERROR** items | Must fix before generating PDF. Use `--fix --output <file>.html` for auto-repair |
| **WARNING** items | Review; non-blocking but should be addressed |

**Key checks:**
- `OVERFLOW_HIDDEN_CONTAINER` (error): `overflow:hidden` on html/body/.page clips content and hides layout bugs. Paged.js handles pagination without needing overflow clipping
- `FIXED_SIZE_NO_SCREEN_ADAPT` (warning): fixed-size page without `@media screen` auto-scale - browser preview requires scrolling
- `SCREEN_ADAPT_NO_SCALE` (warning): `@media screen` exists but lacks scale/transform/zoom
- `FONT_NO_FALLBACK` (error): font-family without generic fallback
- `COLOR_CONTRAST` (warning): text/background contrast ratio < 3:1
- Plus: remote images, absolute paths, missing margin reset, tiny fonts, background mismatch, etc.

This applies to **all three HTML routes**: Creative blueprint pipeline, Report HTML covers, and bypass/custom HTML.

### Overflow Prevention System

**→ Full spec: `typesetting/overflow.md`** - read it for any document with tables, images, or multi-column layouts.

Core principles:
1. **Measure first, draw second** - never render content without pre-calculating its dimensions
2. **Bounding Box constraint** - every element's width ≤ its parent container's `Max_Width`
3. **Text: use font metrics**, not character count, for width calculation
4. **Images: proportional scaling** - never insert at original size
5. **Tables: weight-based column width** + `Paragraph()` wrapping (never plain strings)
6. **Fallback ladder**: wrap → shrink font (max -3pt) → reduce padding → split element → log warning
7. **Vertical: KeepTogether** for heading+body, chart+caption; `repeatRows=1` for long tables

### Table Overflow Prevention (ReportLab)
**Most common layout bug: table columns exceed page margins.**

Before building any ReportLab Table:
1. Calculate `available_width = page_width - left_margin - right_margin`
2. Use proportional colWidths (`[0.25, 0.40, 0.20, 0.15]` × available_width) or fixed+flex pattern
3. `sum(colWidths)` must be ≤ `available_width` - **verify this in code**
4. Long text columns must use `Paragraph()` wrapping, not plain strings (plain strings don't wrap)
5. CJK text is wider: budget ~12pt per character at 10pt font size

See `briefs/report.md` § "Table Width Management" for code patterns.

### Table Overflow Prevention (LaTeX/Academic)
**Most common bug in dual-column papers: wide tables overflow single-column width.**

Before writing any LaTeX table:
1. Count data columns - ≤ 4 fits single column; 5-6 needs `\small`; 7-8 needs `\resizebox`; ≥ 9 use `table*` (full width)
2. Use `tabular*{\columnwidth}` or `tabularx{\columnwidth}` instead of plain `tabular` for 5+ columns
3. Never use plain `tabular` with 8+ columns in twocolumn layout - guaranteed overflow
4. `\resizebox{\columnwidth}{!}` as last resort - verify smallest text ≥ 6pt after scaling

See `briefs/academic.md` § "Table width management" for LaTeX patterns.

### Playwright PDF CSS Blacklist
These CSS properties **silently break** in Playwright's PDF renderer:
- `backdrop-filter` / `-webkit-backdrop-filter` - **drops entire element content**. Use solid `rgba()` backgrounds.
- `overflow: hidden` on content containers - clips content. Only safe on small decorative elements (< 200px).

After generating any Playwright PDF, **verify every page has content** (pypdf text extraction, check non-empty).

### PDF Metadata (all briefs)
ALL PDFs must have: Title, Author (default "Z.ai"), Creator, Subject.

### Delivery Summary (all briefs)
Report to user: file path, size, page count. Academic adds word/image count. Creative adds per-page verification.

**HTML→PDF route deliverables (MANDATORY - applies to ALL briefs that use Playwright/HTML to generate PDF):**
Whenever the HTML→PDF pipeline is used (Creative route, Report cover bypass, Direct HTML Flow posters, or any Playwright `page.pdf()` path), you MUST deliver **both files** to the user:
1. **HTML** - the source HTML file, so the user can edit and reuse the design
2. **PDF** - the final vector PDF (`page.pdf()` output)

Optionally also provide:
3. **Image** - a full-page screenshot/preview image (PNG or JPG) for quick sharing on chat/social media

All file paths must be reported to the user. **Never deliver only the PDF without the HTML source.**

---

## Tooling Reference

### CLI: `python3 "$PDF_SKILL_DIR/scripts/pdf.py" <command>`

```bash
# Environment
env.check                    # Check deps
env.fix                      # Auto-install missing

# Quality
code.sanitize <script>       # Sanitize forbidden Unicode
content.sanitize <file> [--apply]  # Fix content issues (CJK, encoding)
meta.brand <pdf>             # Add Z.ai metadata
font.check <pdf>             # Scan for missing glyphs
toc.check <pdf>              # Validate TOC

# Conversion
convert.blueprint <llm_json_response.md> -o final.pdf  # CRITICAL FOR CREATIVE: Auto-extracts JSON, compiles, and renders PDF.
convert.html <html>          # HTML → PDF (Playwright)
convert.latex <tex>           # LaTeX → PDF (Tectonic). Bundled binary is macOS arm64 only; see academic.md for other-platform install.
convert.office <file>         # Office → PDF (LibreOffice)

# Processing
extract.text <pdf>            # Extract text
extract.table <pdf>           # Extract tables
extract.image <pdf>           # Extract images
pages.merge a.pdf b.pdf -o out.pdf
pages.split <pdf>
pages.clean <pdf>             # Remove blank pages
form.info <pdf>               # Inspect form fields
form.fill <pdf>               # Fill form
form.annotate <pdf>           # Fill via annotations
meta.get <pdf>
meta.set <pdf> -o out.pdf -d '{"Title": "..."}'
```

### Poster/HTML/LaTeX Validator: `python3 "$PDF_SKILL_DIR/scripts/poster_validate.py"`
```bash
check-html <html>                              # Pre-render validation (overflow:hidden, @media screen, fonts, contrast, etc.)
check-html <html> --fix --output <fixed.html>  # Auto-fix errors (remove overflow:hidden, add font fallback)
check-pdf <pdf> --source-html <html>           # Post-render validation
check-pdf <pdf> --poster                       # Poster mode: suppress ORPHAN_PAGE warning
check-tex <tex>                                # LaTeX source validation (table overflow, image width, etc.)
```

**check-html checks include:**
- `OVERFLOW_HIDDEN_CONTAINER` (error): overflow:hidden on html/body/.page/.poster - clips content
- `FIXED_SIZE_NO_SCREEN_ADAPT` (warning): fixed-size page without @media screen auto-scale
- `SCREEN_ADAPT_NO_SCALE` (warning): @media screen exists but lacks scale/transform/zoom
- `FONT_NO_FALLBACK` (error): font-family without generic fallback (sans-serif/serif)
- `COLOR_CONTRAST` (warning): text/background contrast ratio < 3:1
- `BG_COLOR_MISMATCH` (warning): body background differs from .canvas/.poster background
- `SCREEN_BG_MISMATCH` (warning): @media screen html background differs from body/canvas background
- `MULTIPAGE_BODY_BG_MISSING` (warning): multi-page document with dark `.page` backgrounds but no `html/body` background color. Sub-pixel gaps at page edges reveal white body, causing visible white edges on dark pages. Resolves `var()` references via `:root` variables.
- `SCREEN_NO_BG` (warning): fixed-size page's @media screen block lacks html background color
- `OVERFLOW_DECORATION` (warning): negative position values may cause black edges
- `NO_PAGE_SIZE` / `MISSING_MARGIN_RESET` / `WHITE_BACKGROUND` / `TINY_FONT` / etc.

**check-tex checks include:**
- `BARE_TABULAR_OVERFLOW` (error): `\begin{tabular}` with 5+ columns in two-column layout, not wrapped in resizebox/adjustbox/table*
- `RESIZEBOX_TEXTWIDTH` (error): `\resizebox{\textwidth}` used inside single-column float in two-column layout. `\textwidth` = full page width, but `table` float is one column. Fix: use `\resizebox{\columnwidth}` or `table*`
- `TABULAR_OVERFLOW_RISK` (warning): 4-column tabular in two-column layout without width constraint
- `TABULAR_WIDE` (warning): 7+ column tabular in single-column layout without width constraint
- `TABULAR_NO_FLOAT` (warning): tabular not inside table/table* float environment
- `TABULARX_NOT_LOADED` (warning): document has tabular but tabularx package not loaded
- `IMAGE_NO_WIDTH` (warning): `\includegraphics` without width/height/scale constraint
- `EQUATION_DUAL_ON_LINE` (warning): `equation` environment has 2+ equations joined by `\quad` without line breaks. Guaranteed overflow in dual-column
- `EQUATION_OVERFLOW_RISK` (warning): equation body has >80 math characters. Likely overflows single column
- `ALGORITHM_NO_SMALL_FONT` (warning): `algorithm` environment in dual-column without `\SetAlFnt{\small}`
- `ALGORITHM_LONG_IO` (warning): Algorithm Input/Output line >120 chars. Will overflow narrow column
- `CJK_ASCII_QUOTES` (error): ASCII `"` found adjacent to CJK characters. LaTeX interprets `"` as right double quote, so `"北漂"` renders incorrectly. Skips verbatim/lstlisting/minted environments and `\texttt{}`/`\url{}`/`\href{}{}`/`\verb||` inline commands.

### Design Engine: `python3 "$PDF_SKILL_DIR/scripts/design_engine.py"`
```bash
compile --blueprint <json_file> --output poster.html  # CRITICAL: Compile JSON blueprint to HTML
derive "document title or description"         # Auto-derive intent from content
palette --intent calm --mode dark               # Generate HSL-locked palette
palette-cascade --intent cold --mode minimal    # Generate role-based cascade palette (V2, preferred)
svg --intent flow --dimensions 720x960         # Generate SVG background
full --intent energy --mode dark --dimensions 720x960 --output-dir ./assets/
audit --palette-json palette.json              # Check palette constraints
```

### Palette Generator (for Report route): `python3 "$PDF_SKILL_DIR/scripts/pdf.py" palette.generate`
```bash
palette.generate --title "document title" --mode minimal   # Output: ready-to-paste ReportLab Python code
palette.generate --title "..." --format json               # Output: raw JSON
palette.generate --title "..." --format css                # Output: CSS custom properties
palette.generate --title "..." --mode dark --harmony complementary --seed 42
```

### Cascade Palette (V2 - Preferred): `python3 "$PDF_SKILL_DIR/scripts/pdf.py" palette.cascade`
```bash
palette.cascade --title "document title" --mode minimal    # Output: summary table with all 12 roles
palette.cascade --title "..." --format json                # Full structured JSON (roles + cover + body + charts + semantic)
palette.cascade --title "..." --format css                 # CSS custom properties by tier
palette.cascade --title "..." --format reportlab           # Ready-to-paste ReportLab Python code
```
**⚠️ Cascade palette is the preferred palette system.** It enforces area ∝ 1/saturation (larger areas = lower saturation) and outputs unified color subsets for cover, body, and charts from one base hue. Use `palette.cascade` instead of `palette.generate` for new documents.

**⚠️ Report route MUST call `palette.cascade` (or `palette.generate`) before writing any ReportLab code.** The output is copy-paste ready - no manual hex picking allowed.

> **Note**: `design_engine.py compile` produces **HTML** from a JSON blueprint. To get a **PDF**, use `pdf.py convert.blueprint` which internally calls `compile` → Playwright render → PDF output. In the Creative pipeline, always use `convert.blueprint` for the final PDF.

### Tech Stack per Brief

| Brief | Primary Tool | Secondary | Emoji Support | Custom Page Size |
|-------|-------------|-----------|---------------|-----------------|
| Report | ReportLab + pypdf | **Playwright (cover)** | ❌ (tofu □) | Manual pagination |
| Creative | Playwright | html2pdf-next.js (Paged.js + pdf-lib) | ✅ native | ✅ any size |
| Academic | Tectonic + pypdf | **Playwright (cover)** | ❌ (dropped) | Template-dependent |
| Process | pikepdf, pdfplumber | LibreOffice (soffice) | N/A | N/A |

> **Unified Cover System**: All routes generate covers via HTML/Playwright. Report uses Template 01, Academic uses Templates 03-04 (dark backgrounds, scholarly typography), Creative generates cover + body in one HTML document. Cover PDFs are merged with body PDFs via pypdf.
>
> **Fallback**: If Report brief content has emoji → reroute to Creative.

---

## File Map

```
SKILL.md                            ← You are here
briefs/
  report.md                         ← Report production: ReportLab workflow + API
  resume.md                         ← Resume/CV production: ATS-friendly single-column template
  creative-fixed-canvas.md              ← Fixed-canvas: posters, infographics, certificates (5-phase blueprint design)
  creative-flow.md                       ← Flowing documents: guides, handbooks, catalogs, introductions (content flows across pages)
  poster.md                          ← Poster scene rules: density, font sizing, fill constraints (overlay on creative-fixed-canvas.md)
  academic.md                       ← Academic production: LaTeX workflow + templates + resume(CV)
  process.md                        ← PDF processing: extract/merge/split/form/convert/reformat/encrypt/OCR/batch
configs/
  visual_framework.md               ← Palette mode, color harmony, SVG background params
  components.md                     ← Non-grid composition components (floating cards, etc.)
  fonts.md                          ← Font stacks per pipeline (Creative/Report/Academic)
typesetting/
  palette.md                        ← Color system + typography + anti-patterns + spacing
  cover.md                          ← Cover page layout system (7 layouts × 2-3 variants) + typography scale + color rules
  cover-backgrounds.md              ← Cover background rendering rules + transparency constraints
  charts.md                         ← Chart styling + anti-stacking rules + axis/grid/legend treatment
  overflow.md                       ← Bounding box system, text/image/table overflow prevention
  pagination.md                     ← Cross-page integrity, orphan/widow control, CJK punctuation
  typography.md                     ← Font size scale, line-height, spacing system
  geometry.md                       ← Geometric anchor system (decorative elements, lines, shapes)
  fill-engine.md                    ← Adaptive anti-void layout engine V2.0
scripts/
  pdf.py                            ← CLI tool (30 subcommands)
  pdf_qa.py                         ← PDF quality checker (metadata, fonts, overflow, margins, tables, formulas)
  design_engine.py                  ← Generative SVG + palette engine (palette/svg/compile/derive/audit)
  poster_validate.py                ← HTML/PDF validator
  toc_validate.py                   ← TOC validator
  html2pdf-next.js                  ← Playwright + Paged.js + pdf-lib HTML→PDF converter for documents
  html2poster.js                    ← Playwright HTML→PDF converter for posters/single-page (auto overflow:hidden, dynamic height)
  cover_validate.js                 ← Cover-ONLY overlap detection (text vs decorative lines). Do NOT run on posters or documents - only on cover HTML in Report/Academic pipelines.
references/
  resume-altacv.tex                 ← AltaCV dual-column resume template (creative/tech)
  resume-academic.tex               ← Academic CV template (PhD/academic)
```

### Loading Protocol

> **⚠️ DO NOT SKIP FILES. DO NOT SKIM.**
>
> Every rule in these files exists because a previous generation failed without it. "I already know how to make a PDF" is not a valid reason to skip reading. You don't — these files contain hundreds of engine-specific pitfalls (font registration order, overflow:hidden restrictions, cover rendering tools, page-break interactions) that you cannot guess correctly.

**Step 1 — ALWAYS read (every task):**
- This file (SKILL.md) — routing + iron rules
- `configs/fonts.md` — font stacks per pipeline (wrong font = garbled CJK)

**Step 2 — Read the matched brief (every task):**
- ONE brief file from `briefs/` based on routing
- Read it **completely, top to bottom** — do not stop at the first code example

**Step 3 — Read every file the brief references (MANDATORY, not optional):**
- When the brief says "see `typesetting/cover.md`" or "see `typesetting/overflow.md`" → you **MUST** open and read that file before writing any code
- When a typesetting file references another file → follow that link too
- **There is no "on demand" or "only if needed".** If the brief mentions a file, read it. Period.

**Step 4 — Cover page? Read these BEFORE generating cover HTML:**
- `typesetting/cover.md` — template system, layer architecture, anti-overflow rules
- Run `cover_validate.js` after generating cover HTML (before PDF conversion)
- Use `html2poster.js` for cover rendering — **NEVER write hand-written Playwright scripts**

**Checkpoint before writing code:** Can you name the exact rendering tool (html2poster.js vs html2pdf-next.js), font stack, cover template ID, and post-generation validators for this task? If not, you haven't read enough. Go back.

---

## 8. Quality Checklist (Mandatory after every PDF generation)

> ⚠️ **正文才是第一章。** 封面/目录/摘要不计入编号，正文编号永远从 1 开始。详见 `report.md` Step 3.5。

> The following checks come from the `typesetting/` spec files and are **mandatory** quality gates.

### Automated Detection (Must Run)

```bash
# 1. PDF quality check (all pipelines)
python3 "$PDF_SKILL_DIR/scripts/pdf_qa.py" <output.pdf>
python3 "$PDF_SKILL_DIR/scripts/pdf_qa.py" --poster <output.pdf>   # poster mode: skip content fill ratio, check all pages for full-bleed
python3 "$PDF_SKILL_DIR/scripts/pdf_qa.py" --skip-cover --formulas <output.pdf>   # academic mode: skip cover for margin check, enable formula overflow
python3 "$PDF_SKILL_DIR/scripts/pdf_qa.py" --no-tables <output.pdf>   # creative mode: skip table centering check

# 2. Cover overlap detection (Report/Academic with cover - MANDATORY)
#    Run on the cover HTML BEFORE rendering to PDF. Detects:
#    - Text vs decorative line overlap (minimum gap = 1U = 5% of page width)
#    - Layer 3 text vs text zone overflow (same-layer foreground text blocks overlapping)
#    Exit 0 = pass, Exit 1 = overlap found (must fix), Exit 2 = script error
node "$PDF_SKILL_DIR/scripts/cover_validate.js" cover.html
node "$PDF_SKILL_DIR/scripts/cover_validate.js" cover.html --min-gap 30   # custom min gap in px
```

> **Dependencies**: `pymupdf` (`pip install pymupdf`) for pdf_qa.py; `playwright` or `playwright-core` for cover_validate.js. If not installed, skip the respective check and use the manual checklist below.

Run `pdf_qa.py` after generating a PDF. It auto-detects: metadata completeness, page size consistency, blank pages, CJK punctuation placement, color count, font embedding status, content overflow, content fill ratio, cover full-bleed, margin symmetry, table centering, formula overflow.
- **`--poster` mode**: skips content fill ratio check (poster last page naturally has less content), checks ALL pages for full-bleed (not just cover)
- **`--skip-cover`**: skips page 1 when checking margin symmetry (for documents with separately-generated covers)
- **`--no-tables`**: disables table centering check (for creative/poster documents that rarely have traditional tables)
- **`--formulas`**: enables formula overflow detection (checks if formula-like content extends past right content margin)
- Result PASS → deliver directly
- Result WARN → evaluate whether fix is needed, non-blocking
- Result FAIL → **must fix and regenerate**

### Brief-Specific Quality Checklists

Detailed checklist items have been moved into each brief to reduce context size:

- **Report** → `briefs/report.md` § "Quality Checklist — Report-Specific Items" (pagination, overflow, color, cover, charts, exam rules, layout, design restraint)
- **Academic** → `briefs/academic.md` § "Quality Checklist — Academic-Specific Items" (pagination, LaTeX-specific)
- **Creative Fixed-Canvas** → `briefs/creative-fixed-canvas.md` § "Quality Checklist — Creative-Specific Items" (color, geometric anchors, layout, design restraint)
- **Creative Flow** → `briefs/creative-flow.md` § "Quality Checklist — Creative Flow" (layout & pagination, full-bleed, design quality)

After loading your brief, review its quality checklist before delivering.

### Output Cleanliness (All Pipelines)

- [ ] **No process artifacts in output**: NEVER include version numbers ("V3"), iteration markers, draft labels ("DRAFT"), "CONFIDENTIAL"/"机密" stamps, "Generated by AI"/"本文档由AI生成", or internal comments in the final PDF unless the user explicitly requested them
- [ ] **No auto-generated boilerplate labels**: Do not add ANY watermarks, generation notices, version numbers, timestamps, or tool names that the user didn't ask for
- [ ] **No debug output in content**: Console logs, file paths, generation timestamps, tool names, or error messages must never appear in the PDF body
- [ ] **Clean metadata only**: PDF metadata (author, title, subject) should reflect the document content, not the generation process
