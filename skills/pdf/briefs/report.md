# Brief: Report Production

Structured documents via ReportLab: reports, proposals, contracts, white papers, financial analysis, data tables. Also covers ATS-friendly resumes.

---

> ###  EMOJI CHECK - STOP HERE IF CONTENT HAS EMOJI
>
> ReportLab renders emoji (📊🎯🔥💡 etc.) as **□ tofu squares**. This is unfixable.
>
> **If the user's content contains intentional emoji** → **STOP. Do NOT use this brief.**
> Route to `briefs/creative-fixed-canvas.md` instead (Playwright renders emoji natively).
>
> This applies even if the document is a "report" - emoji + ReportLab = broken output.

---

## Production Workflow

```
1. BRIEF    → Confirm document type, audience, page count, outline
2. DESIGN   → Run `pdf.py palette.cascade --title "..."` → copy-paste output into script
3. EDIT     → Content transformation (extract data, define typographic roles)
3.5 NUMBERING → ⚠️ Chapter Numbering Plan (see below) — MUST output mapping table before writing code
4. COVER    → ⚠️ MANDATORY READ: `typesetting/cover.md` — MUST read BEFORE writing any cover HTML
5. BUILD    → ⚠️ TOC GATE first (see below) → Write ReportLab code
6. PREFLIGHT → code.sanitize → execute → meta.brand → font.check → toc.check → pages.clean → pdf_qa.py
7. DELIVER  → Merge cover + body → final PDF
```

> **⚠️ Word (.docx) dual-delivery rule:** If the user also requests a Word version, you MUST generate it through the **docx skill** (load `docx/SKILL.md` → read `references/design-system.md` → use a validated cover recipe R1-R7). Do NOT hand-write a python-docx script with freehand cover code — freehand covers produce blank pages, wrong heights, and broken layouts in MS Office/WPS. The docx skill's cover system exists to prevent these exact problems.

**Typesetting assets** (load when you reach that step):
- `typesetting/palette.md` - color system, typography rules, anti-patterns
- `typesetting/cover.md` - 5 cover layouts with variants, typography scale, bounding box rules
- `typesetting/charts.md` - chart styling, anti-stacking rules, axis/grid/legend treatment

**Cover is DEFAULT ON for reports.** Skip cover only for: resumes, letters, memos, forms, checklists, or documents ≤ 2 pages.

---

### ⚠️ Step 4 COVER — MANDATORY Pre-Read Gate

**You MUST read `typesetting/cover.md` BEFORE writing any cover HTML.** Do NOT write cover HTML from memory or from pre-trained knowledge. The cover system has 5 specific templates with precise zone coordinates, layer structure, and bounding box rules that change over time.

```bash
# MANDATORY: Read cover.md first. Do NOT skip this.
cat "$PDF_SKILL_DIR/typesetting/cover.md"
```

After reading cover.md:
1. Select a template (01-07) based on document tone and type
2. Follow the template's HTML structure exactly
3. Run `poster_validate.py check-html` on the result
4. Run `cover_validate.js` on the result (checks text-text overlap + text-line overlap)
5. Only then render via `html2poster.js --width 794px`

**Common failure mode:** Model reads report.md, skips cover.md, writes freehand HTML → broken layout, missing zones, overflow issues, decorative elements outside page bounds. The cover templates exist to prevent these exact problems.

---

### ⚠️ Step 5 BUILD — MANDATORY TOC Gate

**Before writing ANY ReportLab code, answer this question:**

> **Does this document have a Table of Contents?**

| Answer | DocTemplate | Build Method | TOC Implementation |
|--------|-------------|--------------|--------------------|
| **YES** | `TocDocTemplate` | `doc.multiBuild(story)` | `TableOfContents()` + heading `bookmark_name/level/text/key` attributes |
| **NO** | `SimpleDocTemplate` | `doc.build(story)` | N/A |

**⚠️ If you answered YES, these are ALL mandatory — missing any one = broken TOC:**

```python
# 1. MUST define TocDocTemplate (NOT SimpleDocTemplate)
class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            self.notify('TOCEntry', (level, text, self.page, key))

# 2. MUST add TableOfContents to story
toc = TableOfContents()
toc.levelStyles = [toc_level0, toc_level1]  # define your styles
story.append(toc)
story.append(PageBreak())

# 3. MUST set bookmark attributes on every heading
def add_heading(text, style, level=0):
    key = f'h_{hashlib.md5(text.encode()).hexdigest()[:8]}'
    p = Paragraph(f'<a name="{key}"/>{text}', style)
    p.bookmark_name = key
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    return p

# 4. MUST use multiBuild (NOT build)
doc = TocDocTemplate(output_path, pagesize=A4, ...)
doc.multiBuild(story)
```

**🚫 FORBIDDEN patterns (these produce broken/fake TOC):**
```python
# ❌ Hard-coded TOC items with manual page numbers
toc_items = [('Chapter 1', '3'), ('Chapter 2', '5')]  # WRONG - not clickable, page numbers will be wrong

# ❌ SimpleDocTemplate + build() with TOC
doc = SimpleDocTemplate(...)  # WRONG if you have TOC
doc.build(story)              # WRONG - TOC entries won't populate

# ❌ TableOfContents without TocDocTemplate
toc = TableOfContents()
story.append(toc)
doc = SimpleDocTemplate(...)  # WRONG - no afterFlowable to feed TOC
```

---

## Step 2: DESIGN - Palette & Font Plan

**Before writing any ReportLab code, you MUST generate the color palette via the `palette.generate` command.** This is not optional. Do NOT hardcode hex colors. Do NOT pick colors by feel.

### 2a. Generate Palette (MANDATORY)

**Run this command FIRST. Copy-paste its output directly into your Python script:**

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" palette.cascade --title "<document title>" --mode minimal --format reportlab
```

> ⚠️ **Use `palette.cascade` (V2), NOT the old `palette.generate`.** Cascade palette outputs unified color roles for cover, body, charts, and tables from one base hue.

The command auto-derives the design intent from the document title, computes a mathematically harmonious palette, and outputs ready-to-paste ReportLab Python code:

```python
# ━━ Cascade Palette (auto-generated by design_engine.py palette-cascade) ━━
from reportlab.lib import colors

# XL tier: backgrounds (area > 50%, S ≤ 0.08)
PAGE_BG       = colors.HexColor('#f5f4f3')
SECTION_BG    = colors.HexColor('#f0efed')

# L tier: surfaces (area 20-50%, S ≤ 0.15)
CARD_BG       = colors.HexColor('#eae8e4')
TABLE_STRIPE  = colors.HexColor('#edebe8')

# M tier: structural fills (area 5-20%, S ≤ 0.30)
HEADER_FILL   = colors.HexColor('#3d5a6e')
COVER_BLOCK   = colors.HexColor('#4a6575')

# S tier: edges & icons (area 1-5%, S ≤ 0.50)
BORDER        = colors.HexColor('#b8c0c7')
ICON          = colors.HexColor('#4e6d7a')

# XS tier: emphasis (area < 1%, S ≤ 0.75)
ACCENT        = colors.HexColor('#2f97b9')
ACCENT_2      = colors.HexColor('#3a8a7d')

# Typography
TEXT_PRIMARY  = colors.HexColor('#252422')
TEXT_MUTED    = colors.HexColor('#8d8981')

# Table colors (derived from cascade tiers — NOT from ACCENT)
TABLE_HEADER_COLOR = HEADER_FILL          # M tier, low-sat — harmonious with body
TABLE_HEADER_TEXT  = colors.white          # White text on dark header
TABLE_ROW_EVEN     = colors.white          # Clean white
TABLE_ROW_ODD      = TABLE_STRIPE          # L tier, very subtle stripe
```

**Options:**
- `--mode minimal` (default, recommended for 50%+ of documents) | `dark` | `pastel` | `jewel` | `light`
- `--harmony auto` (default, recommended) | `complementary` | `split_complementary` | `analogous` | `triadic` | `monochrome`
- `--format reportlab` (recommended) | `json` | `css` | `summary`
- `--seed <int>` - for reproducible palettes across regenerations

**⚠️ FORBIDDEN:**
- ❌ Writing `colors.HexColor('#xxxxxx')` with any hex value you chose yourself
- ❌ Using `colors.red`, `colors.blue`, or any ReportLab named color for design elements
- ❌ Skipping this step and picking colors "that look good"
- ❌ Using different palettes for different sections of the same document
- ❌ Using `ACCENT` (XS tier, high saturation) for table headers — use `HEADER_FILL` (M tier)
- ❌ Using the old `palette.generate` — always use `palette.cascade`

**✅ The ONLY acceptable way to get colors:** Run `palette.cascade`, copy the output.

### 2b. Color Application Rules

| Element | Color Source | Tier | Notes |
|---------|-------------|------|-------|
| Table headers | `HEADER_FILL` (bg) + white (text) | M | Low-sat, harmonious with body |
| Table odd rows | `TABLE_STRIPE` | L | Very subtle same-hue stripe |
| Table even rows | `colors.white` | — | Clean white |
| Section titles | `HEADER_FILL` or `TEXT_PRIMARY` | M/text | Match heading hierarchy |
| Body text | `TEXT_PRIMARY` | text | Never use pure #000000 |
| Muted/meta text | `TEXT_MUTED` | text | Dates, captions, footnotes |
| Horizontal rules | `BORDER` at 30% opacity | S | Thin, unobtrusive |
| Chart colors | `ACCENT` → `ACCENT_2` → `HEADER_FILL` → `ICON` | XS/M/S | Series colors (see charts.md) |
| Badges / tags | `ACCENT` | XS | Small area, high sat OK |
| Card backgrounds | `CARD_BG` | L | Container fills |

### 2c. Forbidden

- ❌ Hardcoding hex colors like `#1F4E79`, `#555555`, `#888888` in code
- ❌ Using `colors.red`, `colors.blue` or any ReportLab named color for design elements
- ❌ Choosing colors by "feel" without running palette first
- ❌ Using different accent colors across tables/sections in the same document

> **Exception**: Semantic colors for data visualization (green for positive, red for negative) are acceptable but should be muted variants derived from the palette when possible.

---

## Step 3: EDIT - Content Transformation

**Before writing any code, restructure raw text into visual roles.** This is the most impactful quality step - skipping it produces "Word document with a PDF extension".

### 3a. Typographic Role Extraction

Parse raw text and categorize content into visual roles:

| Role | ReportLab Mapping | Description |
|------|------------------|-------------|
| **Hero / Display** | Cover title (36-42pt) or section opener | 1-5 words, the emotional hook |
| **Kicker / Eyebrow** | Subtitle or section intro (10-12pt, muted) | Tiny context line above main heading |
| **Data Sculpture** | CalloutBox or bold stat block | Extract impactful numbers (97%, $4.2M, -45ms) |
| **Pull Quote** | BlockQuote (italic + left indent 24pt + accent border) | Most provocative sentence, standalone |
| **Body** | Standard paragraph | Everything else |

**Rule**: Before writing any body paragraph, scan for numbers with units. Every metric like "revenue grew by 12%" or "latency dropped to 45ms" MUST be extracted into a CalloutBox or metrics table - never buried in paragraph prose. See §Data-to-Ink Ratio Rules below.

### 3b. Section Pacing

- If any H1 section has **>400 words** of continuous body text without visual breaks, split into H2 subsections or insert a visual break (table, chart, callout)
- Aim for at least 1 visual element (table/chart/callout) per 2-3 pages of body text
- Dense text walls are the #1 sign of poor report design

### 3c. Content Sanitization for External Sources (MANDATORY when source is PDF/OCR/web)

When content is extracted from an external PDF, OCR output, or web scrape, it may contain invisible garbage characters that cause garbled rendering. **You MUST sanitize the text content before writing it into any `Paragraph()` or `canvas.drawString()`.**

This is different from `code.sanitize` (which cleans Python source code). Content sanitization cleans the **text data itself**.

```python
import re

def content_sanitize(text: str) -> str:
    """Strip invisible/control chars from externally-sourced text."""
    # Remove control chars (except \n \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Remove zero-width chars
    text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060\ufeff]', '', text)
    # Remove replacement char (upstream encoding error)
    text = text.replace('\ufffd', '')
    # Remove variation selectors
    text = re.sub(r'[\ufe00-\ufe0f]', '', text)
    # Remove private use area chars
    text = re.sub(r'[\ue000-\uf8ff]', '', text)
    return text
```

**When to use:**
| Source | Must sanitize? |
|--------|---------------|
| User typed text in prompt | No (usually clean) |
| Extracted from PDF via `pdf.py extract.text` | **YES** |
| OCR output | **YES** |
| Web scrape / HTML strip | **YES** |
| LLM-generated content | No (usually clean) |

⚠️ **Do NOT confuse** `code.sanitize` (Step 6, cleans Python code) with `content_sanitize()` (Step 3, cleans text data). They solve different problems.

---

## Step 3.5: NUMBERING — 正文才是第一章 (MANDATORY)

> ⚠️ **封面、目录、摘要、前言都不是章节。正文第一节 = 第一章/Chapter 1，永远。** Outline 的 `index` 是排序序号，不是章节号。混淆两者会导致文档从“第三章”或“第四章”开始。

**写代码前必须输出编号映射表：**

```
| Outline Index | Type    | Chapter # | Title            |
|---------------|---------|-----------|------------------|
| 1             | cover   | —         | 封面               |
| 2             | toc     | —         | 目录               |
| 3             | content | 第一章    | 概要               |
| 4             | content | 第二章    | 引言               |
| ...           | ...     | ...       | ...              |
```

**铁律：**
- cover/toc/back_cover/摘要/前言 → 无编号
- 第一个 content 节点 = 第一章，永远从 1 开始
- `page_title()` 必须用此表的章节号，不是 Outline `index`

---

---

## Character Safety Rule (MANDATORY)

Three rules for safe character handling in ReportLab PDFs:

**a) Superscripts and subscripts**: Use `<super>`/`<sub>` tags, never raw Unicode superscript/subscript characters (e.g., `\u00b2`, `\u2082`).

**b) Emoji**: ReportLab cannot render emoji. If content contains emoji, use Creative brief (HTML + Playwright).

**c) Font fallback for mixed CJK/Latin text (MANDATORY)**: After registering fonts, you **MUST** call `install_font_fallback()` once. This automatically wraps missing-glyph characters in `<font>` tags inside every `Paragraph()`. No manual `<font name="...">` wrapping needed for mixed Chinese-English text. **Skipping this call is the #1 cause of Helvetica garbled text in CJK documents.**

**d) canvas.drawString / drawRightString CJK font rule (MANDATORY)**: `install_font_fallback()` only works on `Paragraph()` objects. It does NOT affect `canvas.drawString()` / `canvas.drawRightString()` / `canvas.drawCentredString()`. If the text passed to any `canvas.draw*String()` call contains CJK characters (Chinese/Japanese/Korean), you **MUST** call `canvas.setFont('NotoSerifSC', size)` (or another registered CJK font) before drawing. Using FreeSerif / Helvetica / Times for CJK canvas text = garbled output.

```python
# ❌ WRONG — FreeSerif has no CJK glyphs, '科大讯飞' will be garbled
canvas.setFont('FreeSerif-Italic', 8)
canvas.drawRightString(x, y, 'SZSE: 002230  ·  科大讯飞')

# ✅ CORRECT — use CJK font for mixed text
canvas.setFont('NotoSerifSC', 8)
canvas.drawRightString(x, y, 'SZSE: 002230  ·  科大讯飞')

# ✅ ALSO CORRECT — pure English text can use FreeSerif
canvas.setFont('FreeSerif-Italic', 8)
canvas.drawString(x, y, 'Prepared by Strategy Advisory Team')
```

Mathematical/relational operators (×, ÷, ±, ≤, √, ∑, ≅, ∫, π, ∠, Δ, etc.) are safe to use as literal characters in `Paragraph()` - both Noto Sans SC and FreeSerif have these glyphs.

| Need | Correct Method | Correct Example |
|------|---------------|---------|
| Superscript | `<super>` tag in `Paragraph()` | `Paragraph('10<super>2</super> × 10<super>3</super> = 10<super>5</super>', style)` |
| Subscript | `<sub>` tag in `Paragraph()` | `Paragraph('H<sub>2</sub>O', style)` |
| Bold | `<b>` tag in `Paragraph()` | `Paragraph('<b>Title</b>', style)` |
| Math operators | Literal char in `Paragraph()` | `Paragraph('AB ⊥ AC, ∠A = 90°, and ΔABC ≅ ΔDCF', style)` |
| Scientific notation | Combined tags in `Paragraph()` | `Paragraph('1.2 × 10<super>8</super> kg/m<super>3</super>', style)` |

```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

body_style = ParagraphStyle(
    name="ENBodyStyle",
    fontName="FreeSerif",
    fontSize=10.5,
    leading=18,
    alignment=TA_JUSTIFY,
)

# CJK Body (Chinese documents)
cn_body_style = ParagraphStyle(
    name="CNBodyStyle",
    fontName="NotoSerifSC", fontSize=10.5, leading=18,
    alignment=TA_LEFT,      # ← NEVER TA_JUSTIFY for CJK
    wordWrap='CJK',         # ← MANDATORY for CJK
    firstLineIndent=2*4.5*mm,
)

# Superscript: area unit
Paragraph('Total area: 500 m<super>2</super>', body_style)

# Subscript: chemical formula
Paragraph('The reaction produces CO<sub>2</sub> and H<sub>2</sub>O', body_style)

# Scientific notation
Paragraph('Speed of light: 3.0 × 10<super>8</super> m/s', body_style)

# Combined
Paragraph('E<sub>k</sub> = mv<super>2</super>/2', body_style)

# Bold heading
Paragraph('<b>Chapter 1: Introduction</b>', header_style)

# Math symbols
Paragraph('When ∠ A = 90°, AB ⊥ AC and ΔABC ≅ ΔDEF', body_style)
```

**Pre-generation check - before writing ANY string, ask:**
> "Does this string contain a character outside basic CJK or Mathematical/relational operators?"
> If YES → it MUST be inside a `Paragraph()` with the appropriate tag.
> If it is a superscript/subscript digit in raw unicode escape form → REPLACE with `<super>`/`<sub>` tag.

**NEVER rely on post-generation scanning. Prevent at the point of writing.**

**Encoding safety - before writing ANY content text:**
> "Does this string contain Japanese kana (の, が, は etc.) or rare Unicode symbols?"
> If YES → REPLACE with safe plain Chinese equivalents. Japanese kana (Hiragana U+3040-U+309F, Katakana U+30A0-U+30FF) frequently corrupt to U+FFFD (�) when code passes through LLM output, heredoc, or terminal encoding layers.
> Common safe replacements: `活の真鲷`→`活缔真鲷`, `盐烤の鲭鱼`→`盐烤鲭鱼`, `烤の鸡串`→`炭烤鸡串`.
> If the character is genuinely needed, verify it survives a full write→read round-trip with `open(file, encoding='utf-8')`.

---

## Font Setup (Guaranteed Success Method)

### CRITICAL: Allowed Fonts Only
**You MUST ONLY use the following registered fonts. Using ANY other font is STRICTLY FORBIDDEN.**

| Font Name | Usage | Path |
|-----------|-------|------|
| `NotoSerifSC` | **Chinese body text (primary)** |  `/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf` |
| `NotoSerifSC-Bold` | **Chinese headings (primary)** |  `/usr/share/fonts/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf` |
| `Noto Sans SC` | Chinese fallback / sans-serif | `/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf` |
| `Noto Sans SC Bold` | Chinese headings (sans-serif) | `/usr/share/fonts/truetype/chinese/NotoSansSC-Bold.ttf` |
| `SarasaMonoSC` | Chinese code blocks | `/usr/share/fonts/truetype/chinese/SarasaMonoSC-Regular.ttf` |
| `FreeSerif` | English text, numbers, tables | `freefont/FreeSerif.ttf` |
| `DejaVuSans` | Formulas, symbols, code | `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf` |

**FORBIDDEN fonts (DO NOT USE):**
- ❌ Arial, Arial-Bold, Arial-Italic
- ❌ Helvetica, Helvetica-Bold, Helvetica-Oblique
- ❌ Courier, Courier-Bold
- ❌ Any font not listed in the table above

> **Font file locations note:** On macOS, font paths may be under `~/.openclaw/workspace/fonts/` or `~/Library/Fonts/` instead of `/usr/share/fonts/`. The registration code below uses a single `FONT_DIR` variable — set it to the correct base path for your system. All font sub-paths (e.g. `truetype/noto-serif-sc/NotoSerifSC-Regular.ttf`) are appended to `FONT_DIR`.

### Font Registration Template
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

import platform
_IS_MAC = platform.system() == 'Darwin'
if _IS_MAC:
    FONT_DIR = os.path.expanduser('~/.openclaw/workspace/fonts')
else:  # Linux
    FONT_DIR = '/usr/share/fonts'

# Chinese fonts — Noto Serif SC (primary, serif, high quality)
pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
# Chinese fonts — fallback / sans-serif (static weight files, NOT variable font)
pdfmetrics.registerFont(TTFont('Noto Sans SC', f'{FONT_DIR}/truetype/chinese/NotoSansSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Noto Sans SC Bold', f'{FONT_DIR}/truetype/chinese/NotoSansSC-Bold.ttf'))
pdfmetrics.registerFont(TTFont('SarasaMonoSC', f'{FONT_DIR}/truetype/chinese/SarasaMonoSC-Regular.ttf'))

# English fonts — FreeSerif (4 weights)
pdfmetrics.registerFont(TTFont('FreeSerif', f'{FONT_DIR}/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Bold', f'{FONT_DIR}/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Italic', f'{FONT_DIR}/truetype/freefont/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-BoldItalic', f'{FONT_DIR}/truetype/freefont/FreeSerifBoldItalic.ttf'))

# Symbol/Formula font
pdfmetrics.registerFont(TTFont('DejaVuSans', f'{FONT_DIR}/truetype/dejavu/DejaVuSansMono.ttf'))

# CRITICAL: Register font families to enable <b>, <i>, <super>, <sub> tags
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')
registerFontFamily('Noto Sans SC', normal='Noto Sans SC', bold='Noto Sans SC Bold')
registerFontFamily('FreeSerif', normal='FreeSerif', bold='FreeSerif-Bold', italic='FreeSerif-Italic', boldItalic='FreeSerif-BoldItalic')
registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans')
```

### Font Configuration by Document Type

**For Chinese PDFs:**
- Body text: `NotoSerifSC` (primary) — serif font with sharp, elegant strokes
- Headings: `NotoSerifSC-Bold` (MUST use for Chinese headings) — same family, bolder weight for clear hierarchy
- Code blocks: `SarasaMonoSC`
- Formulas/symbols: `DejaVuSans`
- **In tables: ALL Chinese content MUST use `NotoSerifSC`, numbers use `FreeSerif`**
- Fallback: `Noto Sans SC` (if NotoSerifSC unavailable)

**For English PDFs:**
- Body text: `FreeSerif`
- Headings: `FreeSerif` (MUST use for English headings)
- Code blocks: `DejaVuSans`
- **In tables: ALL English content and numbers MUST use `FreeSerif`**

**For Mixed Chinese-English PDFs:**
- Call `install_font_fallback()` once after registering fonts - it automatically wraps characters in `<font>` tags so you don't need to do it manually.
- If you still want manual control, you can use `<font name='...'>` tags, but the automatic fallback handles most cases.

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from pdf import install_font_fallback

# 1. Register fonts (as above)
# 2. Install fallback - one line, handles all mixed-language text
install_font_fallback()

# 3. Just write naturally - no manual <font> wrapping needed!
en_style = ParagraphStyle(name="EN", fontName="FreeSerif", fontSize=10.5, leading=18)
cn_style = ParagraphStyle(name="CN", fontName="NotoSerifSC", fontSize=10.5, leading=18, wordWrap='CJK')

Paragraph('MySQL、PostgreSQL、Redis', en_style)           # ✅ CJK comma auto-fallback to NotoSerifSC
Paragraph('Beijing (北京) has 21M people', en_style)       # ✅ CJK chars auto-fallback
Paragraph('价格:¥2,200~5,800/月', en_style)               # ✅ all CJK chars handled
Paragraph('《巴黎协定》签署于2015年', en_style)               # ✅ CJK book title marks handled
```

**How it works:** `install_font_fallback()` monkey-patches `Paragraph.__init__` to scan each character against the font's `charToGlyph` table. Characters missing from the base font are automatically wrapped in `<font name="FallbackFont">`. The fallback chain is: English fonts → NotoSerifSC (primary) or Noto Sans SC (legacy), Chinese fonts → FreeSerif. For aesthetic optimization, Cyrillic text in NotoSerifSC/Noto Sans SC is automatically routed to FreeSerif (serif looks better for Cyrillic).

### Chinese Plot PNG Method
```python
import matplotlib
import matplotlib.pyplot as plt
matplotlib.font_manager.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
matplotlib.font_manager.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
# Noto Sans SC for Chinese, DejaVu Sans catches symbols Noto Sans SC lacks (²³♠ etc.)
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

### Available Font Paths
Run `fc-list` to get more fonts. Font files are typically located under:
- `/usr/share/fonts/truetype/chinese/`
- `/usr/share/fonts/truetype/english/`
- `/usr/share/fonts/`

---

## Layout & Spacing Control

### Page Breaks

Follow the document type strategy defined in SOUL.md Rule 1.

**Structural breaks (always - MANDATORY):**
- Between cover page and TOC - **cover must NEVER share a page with anything else**
- Between TOC and main content
- Between main content and back cover

**Content breaks (by document type):**
- **Default (all document types)**: ❗ **Absolutely NEVER force page breaks before H1/H2** — content flows naturally, do not insert `PageBreak()` before section headings. This is an iron rule.
- Resume / contract / letter → No content page breaks
- Short article → No content page breaks
- **Exception 1**: Academic papers / textbooks / teaching plans → `PageBreak()` before each H1 is acceptable (only if user explicitly requests academic formatting)
- **Exception 2**: User explicitly requests page breaks between chapters

**Anti-tear (mandatory — but with height limit):**
```python
from reportlab.platypus import KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# Maximum height for KeepTogether blocks: 40% of page height
# Blocks taller than this should NOT be kept together — they cause
# the preceding page to be mostly empty when the block gets pushed down.
MAX_KEEP_HEIGHT = A4[1] * 0.4  # ~336pt ≈ 12cm

def safe_keep_together(elements):
    """Wrap elements in KeepTogether only if their total height is reasonable.
    If too tall, keep only the FIRST TWO elements together (e.g. title + table/image header)
    to prevent title-content separation, while letting the rest paginate naturally.
    """
    total_h = 0
    for el in elements:
        w, h = el.wrap(A4[0] - 2*inch, A4[1])
        total_h += h
    if total_h <= MAX_KEEP_HEIGHT:
        return [KeepTogether(elements)]
    elif len(elements) >= 2:
        # Keep at least title + first element together to prevent title orphaning
        return [KeepTogether(elements[:2])] + list(elements[2:])
    else:
        return list(elements)

# Heading stays with first paragraph
story.extend(safe_keep_together([
    heading_paragraph,
    first_body_paragraph,
]))

# Image + caption: keep together ONLY if image is small
story.extend(safe_keep_together([image, caption_paragraph]))

# Table title + table: keep together ONLY if table is short
if len(table_data) <= 15:
    story.extend(safe_keep_together([table_title, table]))
else:
    # Long table: just keep title with the table start
    story.extend(safe_keep_together([table_title]))
    story.append(table)
```

**⚠️ KEY INSIGHT:** `KeepTogether` is the #1 cause of “empty page with chart on next page”.
When a `KeepTogether` block is taller than the remaining space on the current page,
ReportLab pushes the **entire block** to the next page, leaving the current page mostly empty.
**Always use `safe_keep_together()` to cap the maximum block height.**

**⚠️ Note:** Do NOT use `KeepWithNext` - it is unreliable in ReportLab 4.x.

### Vertical Spacing Standards
* Before tables: `Spacer(1, 18)` after preceding text
* After tables: `Spacer(1, 6)` before table caption
* After table captions: `Spacer(1, 18)` before next content
* Between paragraphs: `Spacer(1, 12)` (~1 line)
* Between H3 subsections: `Spacer(1, 12)`
* Between H2 sections: `Spacer(1, 18)` (~1.5 lines)
* Between H1 sections: `Spacer(1, 24)` (~2 lines)
* NEVER use `Spacer(1, X)` where X > 24, except for H1 major breaks or cover page elements

### Cover Page: HTML/Playwright Unified Cover System

**⚠️ Report route covers are ALWAYS generated via HTML/Playwright**, using the same 5-template system defined in `typesetting/cover.md`. This ensures visual consistency across all routes (Report, Creative, Academic) and avoids the limitations of ReportLab for complex cover layouts.

**Pipeline (Report route):**
1. Generate **body PDF** via ReportLab (start with TOC or content - **no cover in story[]**)  
2. Generate **cover HTML** following `typesetting/cover.md` 5-template system  
3. **Run `poster_validate.py check-html` on cover HTML** — fix any ERRORs before rendering (overflow:hidden, font fallback, etc.)  
4. **Run `cover_validate.js` on cover HTML** — detects text-vs-decorative-line overlaps. Non-zero exit = must fix before proceeding.
   ```bash
   node "$PDF_SKILL_DIR/scripts/cover_validate.js" cover.html
   ```
5. Render cover HTML → single-page PDF via Playwright (`html2poster.js`) — **NOT `html2pdf-next.js`** (which converts absolute→static and destroys cover layout). **⚠️ MUST pass `--width 794px` for A4 documents** (A4 = 210mm = 794px @96dpi). Without this, `html2poster.js` defaults to 720px (=540pt), which is narrower than A4 (595pt) and causes page size mismatch after merging with the body PDF.  
6. **Merge: insert cover as page 0** of body PDF using pypdf → output single final PDF

> **Why not ReportLab covers?** ReportLab is excellent for structured content (tables, paragraphs, flowables) but painful for visual design (geometric accents, precise absolute positioning, web fonts). HTML/CSS handles these natively. One cover system, one visual standard, zero inconsistency.

**⚠️ Cover page is DEFAULT ON for all Report-route documents ≥ 3 pages.**

The Report route handles formal, structured documents. Readers expect a professional cover. **Always generate a cover unless the document type is explicitly excluded below.**

**ALWAYS add a cover page (default behavior):**
- Research reports, experiment reports, lab reports, analysis reports
- White papers, industry analysis, market research
- Business proposals, project plans, feasibility studies
- Technical documentation, product manuals, user guides
- Annual reports, financial summaries, quarterly reviews
- Any formal document ≥ 3 pages that will be shared externally or submitted

**NEVER add a cover page (explicit exclusions only):**
- **Resumes / CVs** - recruiters want content immediately
- **Letters / memos** - single-page or short-form
- **Forms / checklists / invoices** - functional documents
- **Internal notes / meeting minutes** - brevity over presentation
- **Documents ≤ 2 pages** - cover would be disproportionate
- **User explicitly said "no cover"**

**Rule of thumb:** If it's a report, analysis, proposal, or any formal document ≥ 3 pages → **add a cover**. When in doubt, add the cover. It's easier to remove a cover the user didn't want than to miss one they expected.

#### Step 1: Generate Body PDF (ReportLab, no cover)

Build the ReportLab document starting directly with TOC or first section. **Do NOT include any cover page in the `story[]` list.**

```python
# Body PDF - starts with TOC or first section, NO cover
story = []

# ⚠️ If document has TOC: use TocDocTemplate + multiBuild (see TOC Gate above)
# If no TOC: use SimpleDocTemplate + build

# WITH TOC (most reports):
# doc = TocDocTemplate(output, pagesize=A4, ...)
# story.append(toc)
# story.append(PageBreak())
# story.append(first_section_content)
# doc.multiBuild(story)

# WITHOUT TOC:
# doc = SimpleDocTemplate(output, pagesize=A4, ...)
# story.append(first_section_content)
# doc.build(story)
```

#### Step 2: Generate Cover PDF via html2poster.js

```bash
# ALWAYS use html2poster.js for cover rendering (NOT html2pdf-next.js)
# Cover pages use position:absolute layout — html2pdf-next.js pre-render hooks
# convert absolute→static and destroy the layout. html2poster.js preserves it.
node "$PDF_SKILL_DIR/scripts/html2poster.js" cover.html --output cover.pdf --width 794px
```

Or from Python:
```python
import subprocess, os

def render_cover(html_path, pdf_path):
    """Render HTML cover to PDF via html2poster.js.
    
    ⚠️ ALWAYS use html2poster.js for covers (NOT html2pdf-next.js).
    Cover HTML uses position:absolute for layout. html2pdf-next.js pre-render
    hooks convert absolute→static to prevent multi-page overlap, which
    destroys cover layouts. html2poster.js preserves absolute positioning.
    """
    scripts_dir = os.path.expanduser('~/.openclaw/workspace/skills/pdf/scripts')
    subprocess.run([
        'node', os.path.join(scripts_dir, 'html2poster.js'),
        html_path, '--output', pdf_path,
        '--width', '794px',
    ], check=True)
```

**Insertion script (single output PDF):**
```python
from pypdf import PdfReader, PdfWriter

A4_W, A4_H = 595.28, 841.89  # A4 in points

def normalize_page_to_a4(page):
    """Scale a page to A4 if its dimensions don't match."""
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    if abs(w - A4_W) > 2 or abs(h - A4_H) > 2:
        page.scale_to(A4_W, A4_H)
    return page

def insert_cover(cover_pdf, body_pdf, output_pdf):
    """Insert cover as first page of body PDF → single output file."""
    writer = PdfWriter()
    # Cover as page 1
    cover_page = PdfReader(cover_pdf).pages[0]
    writer.add_page(normalize_page_to_a4(cover_page))
    # Body pages follow
    for page in PdfReader(body_pdf).pages:
        writer.add_page(normalize_page_to_a4(page))
    writer.add_metadata({'/Title': 'Report Title', '/Author': 'Z.ai', '/Creator': 'Z.ai'})
    with open(output_pdf, 'wb') as f:
        writer.write(f)
```

> **⚠️ Size pitfall:** Playwright `page.pdf(width='794px', height='1123px')` output PDF dimensions may differ from A4 (595.28×841.89pt) by 1-2pt. **Do not use PIL Image.save('x.pdf')** for PNG→PDF conversion — DPI mapping causes severe size errors. You must call `normalize_page_to_a4()` to unify dimensions before insertion.

**Cover HTML template reference**: See `typesetting/cover.md` for the complete 5-Layout System with variants, typography scale, and bounding box rules.

**→ MUST READ: `typesetting/cover.md`** — read the complete 5-Layout System with variants, typography scale, and bounding box rules before writing any cover HTML.

**Cover design rules (summary - see cover.md for details):**
- Page size: `width: 794px; height: 1123px` (A4 at 96dpi)
- `body { margin: 0; padding: 0; overflow: hidden; }` - REQUIRED to avoid white borders
- Load Google Fonts via `<link href="..." rel="stylesheet">` in `<head>` (NOT `@import url(...)` in CSS — `@import` must be first rule or is silently ignored) — Playwright fetches them at render time
- **Background must be white or very light** (`#fff` / `#fafafa` / `#f5f8fb`), no dark solid backgrounds or gradient backgrounds
- Primary color used only for text, lines, geometric accents - never as large-area background
- Sophistication = whitespace + typography + restrained geometric accents

**Cover Constitution (5-Layout System):**
- **Pick a layout (01/03/04/06/07)** from `typesetting/cover.md` that matches the document tone. No global default - every selection must be a deliberate design decision.
- **Maximum 4 components** on any cover. Typical recipe: Title + subtitle + 1 geometric accent + metadata.
- **Typography Scale**: Title ≈ 45pt, Subtitle ≈ 25pt, Meta ≥ 18pt (never below 14pt). Tiny text = FAIL.
- **Background layer (optional)**: See `typesetting/cover-backgrounds.md` for 3 recipes (A=极简弧线, B=工程十字轴+立柱, C=锐角切割+出血文字). Background renders BELOW all foreground content at 2-5% opacity.
- **Mandatory `<br>` chunking**: Title MUST break every 2-4 words (CJK) or 3-5 words (English). Single-line title = FAIL.
- **Bounding Box spatial dispersion**: Group elements into 2-3 bounding boxes at opposite regions (e.g., top-left + bottom-right). Never cluster everything into middle 40%.
- **Safe Zone**: 12% top/bottom, 14% left/right padding on cover pages.
- **No body text on cover**: Cover = title + subtitle + date + optional geometric decoration. All content goes to page 2+.
- **Cover page isolation**: Cover NEVER shares a page with TOC or body content. In Report route this is inherent (separate PDFs merged via pypdf). If output shows cover + TOC on same page = **critical bug**, regenerate immediately.

### Alignment and Typography
- **CJK body**: Use `TA_LEFT` + 2-char indent. Headings: no indent.
- **Font sizes**: Body 11pt, subheadings 14pt, headings 18-20pt
- **Line height**: 1.5-1.6 (leading at **1.4x font size minimum**, recommended 1.5x for CJK)
  - CJK characters are taller than Latin - 1.2x causes cramped lines
  - Quick reference: 10pt→14pt min/18pt rec; 14pt→20pt min/22pt rec; 36pt→50pt min/54pt rec
- ** Prohibited: fixed `rowHeights` in Table()**. Use `TOPPADDING` / `BOTTOMPADDING` to control row spacing. Fixed rowHeights cause content overflow clipping - the text renders but gets invisibly cut off.
- **CRITICAL: Alignment Selection Rule**:
  - Use `TA_JUSTIFY` only when ALL of:
    * Text is predominantly English (≥ 90%)
    * Column width is sufficiently wide (A4 single-column body)
    * Font: Western fonts (FreeSerif)
    * Chinese content: None or negligible
  - Otherwise, always default to `TA_LEFT`
  - For Chinese text, always add `wordWrap='CJK'` to ParagraphStyle

### Style Configuration
* Normal paragraph: `spaceBefore=0`, `spaceAfter=6-12`
* Headings: `spaceBefore=12-18`, `spaceAfter=6-12`
* **Headings must be bold**: Use `<b></b>` tags in Paragraph
* Table captions: `spaceBefore=3`, `spaceAfter=6`, `alignment=TA_CENTER`
* **CRITICAL**: For Chinese text, always add `wordWrap='CJK'` to ParagraphStyle

---

## Table Formatting

### Standard Table Color Scheme (MUST USE for ALL tables)

> **Colors MUST come from the `palette.cascade` output (Step 2).** The values below are variable names - they are populated by the cascade palette, never hardcoded.

```python
# Colors from palette.cascade (Step 2) — NEVER hardcode hex values
# Table header uses HEADER_FILL (M tier, S ≤ 0.30) — NOT ACCENT (XS tier, too vivid)
TABLE_HEADER_COLOR = HEADER_FILL          # M tier — low-sat, blends with document body
TABLE_HEADER_TEXT  = colors.white          # White text for header (fixed)
TABLE_ROW_EVEN     = colors.white          # White for even rows
TABLE_ROW_ODD      = TABLE_STRIPE          # L tier — very subtle same-hue stripe
```

> **⚠️ Why NOT `ACCENT` for table headers?** `ACCENT` is XS tier (S = 0.50-0.75), designed for tiny elements like badges and tags. Table headers occupy 5-20% of visual area (M tier). Using high-saturation `ACCENT` on table headers creates jarring color blocks that clash with the low-saturation body. `HEADER_FILL` (S ≤ 0.30) is specifically designed for this area ratio.

### Table Rules
- Caption must be centered, added immediately after the table
- Entire table must be centered on the page
- **Header Row**: Dark background (from palette `HEADER_FILL`, M tier), white bold text
- **Cell Margins**: Left/Right at least 120-200 twips
- **Alignment**: Each body element within the same table must be aligned the same method
- **Color consistency**: All tables in one PDF must use the same `HEADER_FILL` + `TABLE_STRIPE` scheme
- **Spacing**: `Spacer(1, 18)` → Table → `Spacer(1, 6)` → Caption → `Spacer(1, 18)`

### Table Centering Enforcement (MANDATORY)

**Every table MUST be horizontally centered on the page. No exceptions.**

```python
# ReportLab: ALWAYS set hAlign='CENTER'
table = Table(data, colWidths=col_widths, hAlign='CENTER')

# Width rule: table total width should be 85-100% of available content width
available_width = doc.width  # or page_width - left_margin - right_margin
table_width = sum(col_widths)
if table_width < available_width * 0.85:
    # Scale up columns proportionally to fill space
    scale = (available_width * 0.90) / table_width
    col_widths = [w * scale for w in col_widths]

# ❌ WRONG — no hAlign (defaults to LEFT, table drifts left)
table = Table(data, colWidths=[100, 200, 150])

# ✅ RIGHT — explicit centering
table = Table(data, colWidths=[100, 200, 150], hAlign='CENTER')
```

**LaTeX equivalent:**
```latex
\begin{table}[htbp]
  \centering  % MANDATORY
  \begin{tabular}{...}
  ...
  \end{tabular}
\end{table}
```

### Table Cell Content Rule (MANDATORY - NON-NEGOTIABLE)

**ALL text content in table cells MUST be wrapped in `Paragraph()`. NO EXCEPTIONS.**

❌ **PROHIBITED** - Plain strings:
```python
data = [
    ['<b>Header</b>', 'Value'],           # Bold won't render!
    ['Pressure', '1.01 × 10<super>5</super>'],  # Superscript won't work!
]
```

✅ **REQUIRED** - All text in Paragraph:
```python
data = [
    [Paragraph('<b>Header</b>', header_style), Paragraph('Value', header_style)],
    [Paragraph('Pressure', cell_style), Paragraph('1.01 × 10<super>5</super>', cell_style)],
]
```

**The ONLY exception**: `Image()` objects can be placed directly in table cells.

### Units with Exponents (CRITICAL)
- PROHIBITED: `W/m2`, `kg/m3`, `m/s2` (plain text exponents)
- RIGHT: `Paragraph('W/m<super>2</super>', style)`, `Paragraph('kg/m<super>3</super>', style)`

### Numeric Values in Tables (CRITICAL)
- Large numbers MUST use scientific notation: `Paragraph('-1.246 × 10<super>8</super>', style)` not `-124600000`
- Small decimals MUST use scientific notation: `Paragraph('2.5 × 10<super>-3</super>', style)` not `0.0025`
- Threshold: Use scientific notation when |value| ≥ 10000 or |value| ≤ 0.001

### Complete Table Example
```python
from reportlab.platypus import Table, TableStyle, Paragraph, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

header_style = ParagraphStyle(
    name='TableHeader', fontName='FreeSerif', fontSize=11,
    textColor=colors.white, alignment=TA_CENTER
)
cell_style = ParagraphStyle(
    name='TableCell', fontName='FreeSerif', fontSize=10,
    textColor=colors.black, alignment=TA_CENTER
)

data = [
    [Paragraph('<b>Parameter</b>', header_style),
     Paragraph('<b>Unit</b>', header_style),
     Paragraph('<b>Value</b>', header_style)],
    [Paragraph('Temperature', cell_style),
     Paragraph('°C', cell_style),
     Paragraph('25.5', cell_style)],
    [Paragraph('Pressure', cell_style),
     Paragraph('Pa', cell_style),
     Paragraph('1.01 × 10<super>5</super>', cell_style)],
    [Paragraph('Density', cell_style),
     Paragraph('kg/m<super>3</super>', cell_style),
     Paragraph('1.225', cell_style)],
]

table = Table(data, colWidths=[120, 80, 100])
# ⚠️ Above uses hardcoded widths - OK for this 3-col example (120+80+100=300 < available ~460pt).
# For real tables, ALWAYS calculate from available_width. See "Table Width Management" below.
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT),           # Header: palette accent
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 1), (-1, 1), colors.white),
    ('BACKGROUND', (0, 2), (-1, 2), BG_SURFACE),       # Odd row: palette surface
    ('BACKGROUND', (0, 3), (-1, 3), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, TEXT_MUTED),       # Grid: palette muted
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
```

### Table Width Management (⚠️ Prevent Table Overflow)

**Most common table bug: columns overflow the right page margin because colWidths are hardcoded without checking available space.**

**Iron Rule: The sum of all colWidths MUST NOT exceed `available_width`.**

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

page_width = A4[0]  # 595.28pt
left_margin = 1.0 * inch   # 72pt (adjust to your doc's actual margins)
right_margin = 1.0 * inch  # 72pt
available_width = page_width - left_margin - right_margin  # ≈ 451pt

# ─── Method 1: Proportional widths (RECOMMENDED) ───
# Define column ratios, auto-scale to fit available_width
col_ratios = [0.25, 0.40, 0.20, 0.15]  # must sum to 1.0
col_widths = [r * available_width for r in col_ratios]
table = Table(data, colWidths=col_widths)

# ─── Method 2: Fixed + flex columns ───
# Some columns have fixed width (numbers, dates), rest fills remaining space
fixed_cols = {0: 80, 3: 60}  # col 0 = 80pt, col 3 = 60pt
fixed_total = sum(fixed_cols.values())
flex_count = 4 - len(fixed_cols)  # total columns minus fixed
flex_width = (available_width - fixed_total) / flex_count
col_widths = []
for i in range(4):
    col_widths.append(fixed_cols.get(i, flex_width))
table = Table(data, colWidths=col_widths)

# ─── Method 3: Let ReportLab auto-calculate (simplest, less control) ───
# Pass colWidths=None - ReportLab auto-sizes based on content
# ⚠️ Risk: may still overflow if content is too wide
table = Table(data)  # no colWidths
```

**Checklist before adding any table:**
1. Calculate `available_width` from your actual page size and margins
2. Sum all colWidths - must be ≤ `available_width`
3. For CJK text: characters are wider than Latin - budget ~12pt per CJK char at 10pt font
4. If a column has long text (descriptions, policies), use Paragraph() wrapping inside cells (not plain strings) - plain strings don't wrap and will overflow
5. Test with the longest expected content in each column

**Common mistake - plain strings don't wrap:**
```python
# ❌ Plain string: will overflow if text is long
data = [['Policy Name', 'Very long description that keeps going and going']]
# ✅ Paragraph: wraps within column width
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
styles = getSampleStyleSheet()
cell_style = styles['Normal']
data = [[Paragraph('Policy Name', cell_style),
         Paragraph('Very long description that keeps going and going', cell_style)]]
```

```
Do you need auto-TOC?
├─ YES → Use TocDocTemplate + doc.multiBuild(story)
└─ NO → Use SimpleDocTemplate + doc.build(story)
```

| Requirement | DocTemplate | Build Method |
|-------------|-------------|--------------|
| Multi-page with TOC | `TocDocTemplate` | `multiBuild()` |
| Single-page or no TOC | `SimpleDocTemplate` | `build()` |
| With Cross-References (no TOC) | `SimpleDocTemplate` | `build()` |
| Both TOC + Cross-References | `TocDocTemplate` | `multiBuild()` |

**⚠️ CRITICAL**:
- `multiBuild()` is ONLY needed when using `TableOfContents`
- Using `build()` with `TocDocTemplate` = TOC won't work
- Using `multiBuild()` without `TocDocTemplate` = unnecessary overhead

---

## Rich Text Formatting

### Prerequisites
To use `<b>`, `<super>`, `<sub>` tags, you **must**:
1. Register fonts via `registerFont()`
2. Call `registerFontFamily()` to link normal/bold/italic variants
3. Wrap all tagged text in `Paragraph()` objects

**CRITICAL**: These tags ONLY work inside `Paragraph()` objects. Plain strings will NOT render them.

### Preventing Unwanted Line Breaks

```python
# Use non-breaking space to prevent breaking
text = Paragraph("Professors (K.G.\u00A0Palepu) proposed...", style)

# Use wordWrap='CJK' for proper Chinese typography
styles.add(ParagraphStyle(name='BodyStyle', fontName='Noto Sans SC', fontSize=10.5,
    leading=18, alignment=TA_LEFT, wordWrap='CJK'))

# Use <br/> for intentional line breaks (NOT \n)
text = Paragraph("Line 1<br/>Line 2<br/>Line 3", style)
```

---

## Auto-Generated Table of Contents

### ❌ FORBIDDEN: Manual Table of Contents
**NEVER manually create TOC with hardcoded page numbers.**

### ⚠️ MANDATORY: TOC requires a cover page
**Unless the user explicitly requests no cover, if a document has a Table of Contents, it MUST have a cover page.** Structure: Cover (page 1) → TOC (page 2) → Content (page 3+). Do not generate a TOC without a preceding cover page.

### ✅ ALWAYS use auto-generated TOC:

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.utils import simpleSplit
import hashlib

class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            # MUST pass key as 4th element - without it, TOC entries won't have clickable links
            self.notify('TOCEntry', (level, text, self.page, key))

doc = TocDocTemplate("document.pdf", pagesize=letter)
story = []

toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle(name='TOCHeading1', fontSize=14, leftIndent=20, fontName='FreeSerif'),
    ParagraphStyle(name='TOCHeading2', fontSize=12, leftIndent=40, fontName='FreeSerif'),
]
story.append(Paragraph("<b>Table of Contents</b>", styles['Title']))
story.append(toc)
story.append(PageBreak())

def add_heading(text, style, level=0):
    # Generate a unique bookmark key for this heading
    key = 'h_%s' % hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph('<a name="%s"/>%s' % (key, text), style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key  # This key enables clickable TOC links
    return p

# ⚠️ Orphan Heading Prevention (NOT a page break rule)
# If an H1 heading would appear in the bottom 15% of the page with no room
# for at least a few lines of content, push it to the next page.
# This is NOT "every H1 starts a new page" — it only triggers when the heading
# would be orphaned at the very bottom.
available_height = A4[1] - top_margin - bottom_margin
H1_ORPHAN_THRESHOLD = available_height * 0.15  # ~100pt ≈ 3.5cm — enough for heading + 2 lines

def add_major_section(text, style):
    """Add an H1-level heading with orphan prevention (NOT forced page break)."""
    return [
        CondPageBreak(H1_ORPHAN_THRESHOLD),  # Only break if heading would be orphaned at page bottom
        add_heading(text, style, level=0),
    ]

story.extend(add_major_section("Chapter 1: Introduction", styles['Heading1']))
# ... content ...

doc.multiBuild(story)  # MUST use multiBuild for TOC
```

**⚠️ CRITICAL TOC LINK RULES:**
1. `afterFlowable` MUST pass `key` as the 4th element in the notify tuple - without it, TOC entries have no clickable links
2. `add_heading` MUST set `bookmark_key` AND embed `<a name="key"/>` in the Paragraph text - this creates the link destination
3. The key must be unique per heading - use a hash of the heading text

### TOC with Leader Dots (Copy-Paste Ready)

**⚠️ WARNING**: This manual approach creates a visual-only TOC. It has **NO clickable links** and **NO auto-updated page numbers**. Use the auto-generated TOC above (TocDocTemplate + multiBuild) whenever possible. Only use this leader-dots approach if you need very specific visual styling that the auto TOC cannot provide - and even then, prefer the auto approach.

For a professional TOC with leader dots connecting titles to page numbers:

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Setup
doc = SimpleDocTemplate("report.pdf", pagesize=A4,
                       leftMargin=0.75*inch, rightMargin=0.75*inch)
styles = getSampleStyleSheet()
styles['Heading1'].fontName = 'FreeSerif'
styles['Heading1'].textColor = colors.black

story = []

# Calculate dimensions
page_width = A4[0]
available_width = page_width - 1.5*inch
page_num_width = 50  # Fixed width for page numbers
dots_column_width = available_width - 200 - page_num_width
optimal_dot_count = int(dots_column_width / 4.5)  # ~4.5pt per dot at 7pt font

# Define styles
toc_style = ParagraphStyle('TOCEntry', parent=styles['Normal'],
                          fontName='FreeSerif', fontSize=11, leading=16)
dots_style = ParagraphStyle('LeaderDots', parent=styles['Normal'],
                           fontName='FreeSerif', fontSize=7, leading=16)

# Build TOC
toc_data = [
    [Paragraph('<b>Table of Contents</b>', styles['Heading1']), '', ''],
    ['', '', ''],
]

entries = [('Section 1', '5'), ('Section 2', '10')]
for title, page in entries:
    toc_data.append([
        Paragraph(title, toc_style),
        Paragraph('.' * optimal_dot_count, dots_style),
        Paragraph(page, toc_style)
    ])

toc_table = Table(toc_data, colWidths=[None, dots_column_width, page_num_width])
toc_table.setStyle(TableStyle([
    ('GRID', (0, 0), (-1, -1), 0, colors.white),
    ('LINEBELOW', (0, 0), (0, 0), 1.5, colors.black),
    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ('TOPPADDING', (0, 2), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 2), (-1, -1), 3),
    ('TEXTCOLOR', (1, 2), (1, -1), TEXT_MUTED),  # From palette --c-muted
]))

story.append(toc_table)
story.append(PageBreak())
doc.build(story)
```

**MANDATORY Leader Dots Rules:**

| Rule | Requirement |
|------|-------------|
| Column widths | ✅ MUST use fixed values. Percentage-based widths are **STRICTLY FORBIDDEN**. |
| Dot count | ✅ MUST calculate dynamically: `int(dots_column_width / 4.5)`. Hard-coded counts are **STRICTLY FORBIDDEN**. |
| Page number column | ✅ MUST be at least 40pt wide. |
| Dot font size | ✅ MUST NOT exceed 8pt. |
| Dot alignment | ✅ MUST be LEFT-aligned (visual flow from title). |
| Padding | ✅ MUST be exactly 0 between columns. |
| Bold text | ✅ MUST use `Paragraph('<b>Text</b>', style)`. Plain strings like `'<b>Text</b>'` are **STRICTLY FORBIDDEN**. |
| Indentation | Use leading spaces for hierarchy (e.g., `"    1.1 Subsection"`). |

### TOC Post-Generation Validation (MANDATORY)

After generating any PDF with a Table of Contents, run:

```bash
python3 "$PDF_SKILL_DIR/scripts/toc_validate.py" check-pdf output.pdf
```

If any errors are returned, fix the code and regenerate. Common issues:
- `TOC_ALL_SAME_PAGE` → You used `build()` instead of `multiBuild()`, so all page numbers are stuck at 1.
- `TOC_NO_ENTRIES` → Headings are missing `bookmark_name`/`bookmark_level` attributes.
- `TOC_PAGES_INVALID` → A TOC entry references a page beyond the document's total page count.

---

## Cross-References (Figures, Tables, Bibliography)

Pre-register all figures, tables, and references BEFORE using them in text.

```python
class CrossReferenceDocument:
    def __init__(self):
        self.figures = {}
        self.tables = {}
        self.refs = {}
        self.figure_counter = 0
        self.table_counter = 0
        self.ref_counter = 0

    def add_figure(self, name):
        if name not in self.figures:
            self.figure_counter += 1
            self.figures[name] = self.figure_counter
        return self.figures[name]

    def add_table(self, name):
        if name not in self.tables:
            self.table_counter += 1
            self.tables[name] = self.table_counter
        return self.tables[name]

    def add_reference(self, name):
        if name not in self.refs:
            self.ref_counter += 1
            self.refs[name] = self.ref_counter
        return self.refs[name]
```

---

## Image Handling

### Diagram Embedding Rules (MANDATORY)

**Figures are block-level Flowables.** Every image/diagram in ReportLab MUST be appended to `story` as a standalone `Image()` or wrapped in `KeepTogether([image, caption])`. Never simulate floating layouts by placing images inside Paragraph text or multi-column Table cells alongside body text.

**Complex diagrams (>12 nodes)**: Decompose into a ReportLab Table (details) + a simplified diagram image (overview). The diagram gives the big picture; the table carries precision. See SKILL.md "Complex Diagram Strategy".

**Diagram quality**: When generating flowcharts/diagrams for PDF embedding (via Playwright screenshot or ReportLab Drawing), follow the diagram content quality rules in SKILL.md § "Diagram Content Quality Rules". Key points: connectors must not pass through nodes, no high-saturation large fills, multi-arrow convergence must use merge pattern, font sizes must be legible at final embedded size (see context-specific minimums in SKILL.md).

**Cross-brief diagram pipeline**: For flowcharts/architecture diagrams, generate via **Playwright+CSS** (HTML nodes + CSS layout + SVG connectors), screenshot at 2× device scale factor for 300dpi print quality, then embed with `Image()`. See SKILL.md § "Diagram Generation Strategy" for the full pipeline.

**🚫 FORBIDDEN: TikZ standalone → PNG pipeline in Report brief.** Report uses ReportLab, not LaTeX. Going through TikZ requires a LaTeX compiler, adds compilation steps, and models frequently produce broken TikZ code. Use Playwright+CSS instead - it's native to the existing cover rendering engine.

```python
# Playwright+CSS diagram → PNG → ReportLab embedding
# 1. LLM generates diagram.html (CSS grid/flexbox nodes + SVG arrows)
# 2. Playwright screenshots at 2× scale (300dpi equivalent)
# 3. Embed:
from reportlab.platypus import Image
img = Image('diagram.png', width=450)  # auto height via aspect ratio
story.append(img)                       # block-level Flowable
```

**⚠️ CRITICAL: Preserve aspect ratio - NEVER hardcode both width and height without reading actual image dimensions.**

**⚠️ CRITICAL: Always constrain to available space - NEVER insert at original size if it exceeds container width/height.**

Pie charts become ellipses, radar charts become diamonds, photos get stretched if you set arbitrary width/height.

**→ MUST READ: `typesetting/overflow.md`** — read the complete bounding box system before writing layout code.

```python
from PIL import Image as PILImage
from reportlab.platypus import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

def embed_image(path: str, max_width: float = None, max_height: float = None) -> Image:
    """Embed image with preserved aspect ratio, constrained to container.

    ALWAYS use this pattern. Never hardcode both width and height.
    If max_width is None, defaults to available_width (page - margins).
    """
    if max_width is None:
        max_width = A4[0] - 2.0 * inch  # Default: A4 width minus 1" margins each side
    if max_height is None:
        max_height = A4[1] * 0.35  # ~294pt ≈ 10cm — leaves room for caption + surrounding text on same page

    pil_img = PILImage.open(path)
    orig_w, orig_h = pil_img.size

    # Scale to fit within BOTH max_width and max_height
    ratio_w = max_width / orig_w if orig_w > max_width else 1.0
    ratio_h = max_height / orig_h if orig_h > max_height else 1.0
    ratio = min(ratio_w, ratio_h)

    return Image(path, width=orig_w * ratio, height=orig_h * ratio)

# Usage:
available_width = A4[0] - left_margin - right_margin
img = embed_image('chart.png', max_width=available_width, max_height=300)
story.append(img)
```

```python
# ❌ NEVER do this - distorts the image:
img = Image('chart.png', width=400, height=250)  # arbitrary height breaks aspect ratio
```

---

## PDF Metadata

```python
doc = SimpleDocTemplate(
    pdf_filename,
    pagesize=letter,
    title=os.path.splitext(pdf_filename)[0],
    author='Z.ai',
    creator='Z.ai',
    subject='Document purpose description'
)
```

### ⚠️ MANDATORY: Post-Generation Metadata

After `doc.build(story)` completes:
```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" meta.brand output.pdf
```

### ⚠️ MANDATORY: Post-Generation Blank Page Cleanup

After metadata branding, remove any accidental blank pages:
```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.clean output.pdf -o output_clean.pdf
```
If blank pages were found, rename `output_clean.pdf` → `output.pdf`.

---

## MANDATORY: Post-Generation Code Sanitization

**After writing PDF generation code and BEFORE executing it**, sanitize using:

```bash
# Step 0: Set skill root path (see SKILL.md § Script Path Setup)
PDF_SKILL_DIR="<skill_directory>"

# Step 1: Write code to .py file
cat > generate_pdf.py << 'PYEOF'
# ... your PDF generation code ...
PYEOF

# Step 2: Sanitize (MUST run before execution)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" code.sanitize generate_pdf.py

# Step 3: Execute
python3 generate_pdf.py

# Step 4: Add metadata (MUST run after PDF creation)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" meta.brand output.pdf

# Step 5: Check for missing glyphs (RECOMMENDED)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" font.check output.pdf

# Step 6: Check TOC quality (if document has TOC)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" toc.check output.pdf

# Step 7: PDF quality assurance scan (MUST run after all other checks)
python3 "$PDF_SKILL_DIR/scripts/pdf_qa.py" output.pdf
```

**FORBIDDEN patterns:**
```bash
# ❌ PROHIBITED: python -c with inline code
python -c "from reportlab... doc.build(story)"

# ❌ PROHIBITED: heredoc without saving to file first
python3 << 'EOF'
from reportlab...
EOF

# ❌ PROHIBITED: executing .py without sanitizing
python generate_pdf.py  # Missing sanitization!
```

---

## Debug Tips for Layout Issues

**→ MUST READ: `typesetting/overflow.md`** — read the complete bounding box system, two-pass rendering, fallback strategies, and all three route implementations.

```python
from reportlab.platypus import HRFlowable
from reportlab.lib.colors import red

# Visualize spacing during development - insert between elements
story.append(table)
story.append(HRFlowable(width="100%", color=red, thickness=0.5, spaceBefore=0, spaceAfter=0))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", color=red, thickness=0.5, spaceBefore=0, spaceAfter=0))
story.append(caption)
# Red lines create visual markers to see actual spacing - remove before final build
```

---

## Resume / CV

Resume/CV content has been moved to a dedicated brief: **`briefs/resume.md`**

This brief is automatically loaded when the triage routes to Resume. For ATS-friendly single-column resumes, see that file.

---

## Component Reference

### Block types:
| Type | Description | Notes |
|------|-------------|-------|
| h1 | 22pt + accent underline rule | KeepTogether with rule |
| h2 | 15pt, dark | No rule, no accent |
| h3 | 11.5pt bold | No accent |
| body | 10.5pt justified, 17pt leading | Supports `<b>` `<i>` `<font>` |
| bullet | Body size with `•` prefix | Unordered list |
| numbered | Body size with N. prefix | Counter auto-resets |
| callout | Accent left border 4px + light tint bg | Max one per section |
| table | Accent header + alternating rows + outer box only | Supports fractional col_widths |
| code | Courier 8.5pt + accent left border | Optional language label |
| divider | Accent 1.2pt rule | Use sparingly |
| caption | 8.5pt muted, centered | Below images/tables |
| chart | matplotlib figure saved as PNG → `Image()` flowable | Generate chart in-script, `fig.savefig()` → embed. Set `plt.rcParams['font.sans-serif']=['Noto Sans SC', 'DejaVu Sans']` for CJK + symbol fallback. Always `tight_layout()`. **Must follow `typesetting/charts.md` rules**: delete top/right spines, dashed grid 20% opacity, donut default for pie, anti-stacking labels. |
| quote | Body italic + left indent 24pt + muted accent left border 2px | For blockquotes / testimonials |
| bibliography | Hanging indent (firstLineIndent=-24pt, leftIndent=24pt) | GB/T 7714 or APA format per language |
| math | Rendered via `<super>` `<sub>` tags in Paragraph | For inline math; complex equations → use academic brief instead |

### Header / footer:
- Header: document title (left, 7.5pt, muted) + accent rule (1.5pt, full width)
- Footer: author (left, 7.5pt, muted) + page number (right, 7.5pt, muted) + light rule above

### Custom flowables (preferred over Table hacks):
- **CalloutBox**: accent 4px left border + light tint background - cleaner than Table simulation
- **BibliographyItem**: hanging indent reference entry

---

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Create PDF (ReportLab) | reportlab | Canvas or Platypus |
| Fill PDF forms | Process brief | `python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.fill` or annotation workflow |
| Merge PDFs | Process brief | `python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.merge` |
| Extract text | Process brief | `python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.text` |
| Extract tables | Process brief | `python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.table` |

---

## Document-Type Quick Reference

### 📋 Invoice / Receipt

Key elements:
- Company logo/name at top
- Invoice number + date (right-aligned)
- Seller/buyer info block (2-column layout)
- Line items table: Item, Quantity, Unit Price, Amount
- Total row with bold font
- Tax info + payment terms at bottom
- Stamp/seal placeholder (empty circle or rect with "Seal Here" text)

```python
# Invoice table pattern
data = [['Item', 'Qty', 'Unit Price', 'Amount']]
data += [[item['name'], item['qty'], item['price'], item['total']] for item in items]
data.append(['', '', 'Total:', f'¥{total}'])
```

### 📝 Contract / Legal Document

Key elements:
- Title centered, bold, 18pt
- Numbered clauses with auto-increment
- Signature block at bottom: Party A / Party B with date line
- Page numbers mandatory

```python
# Signature block pattern
sig_data = [
    ['Party A (Seal): ________________', 'Party B (Seal): ________________'],
    ['Date: ____/____/________', 'Date: ____/____/________'],
]
sig_table = Table(sig_data, colWidths=[250, 250])
```

### 📊 Book / Long Document

For documents with 10+ pages:
1. Generate TOC with `TableOfContents()` from reportlab.platypus
2. Use `CondPageBreak(H1_ORPHAN_THRESHOLD)` before H1 headings (NOT `PageBreak()` — never force page breaks between chapters)
3. Add running headers/footers with chapter title + page number
4. Run `python3 "$PDF_SKILL_DIR/scripts/toc_validate.py" output.pdf` to verify TOC links
5. Consider using `bookmarks=True` for PDF outline navigation

---

### 📝 Exam / Quiz / Test Paper / Worksheet

**Exam papers have unique layout requirements. These rules are MANDATORY when generating any test/quiz/exam document.**

#### Numbering & Structure
```
一、选择题（每小题 3 分，共 30 分）          ← Section header (宋体/黑体 14pt Bold)

1. 以下哪个不是 Python 内置数据类型？     ← Question stem (12pt)
   A. int                                   ← Options: indented 24pt (2em)
   B. float                                 ← Each option on new line or 2×2 grid
   C. array
   D. str

2. 以下表达式的值为？                     ← Next question
   A. True    B. False                      ← Short options: inline 2×2 grid OK
   C. None    D. Error
```

#### Option Indentation (MANDATORY)
```python
# ReportLab styles for exam papers
question_style = ParagraphStyle(
    'Question', fontSize=12, leading=16,
    leftIndent=0, firstLineIndent=0,
    spaceBefore=12, spaceAfter=4,
)
option_style = ParagraphStyle(
    'Option', fontSize=12, leading=16,
    leftIndent=24,   # ← MANDATORY: 24pt indent from question stem
    firstLineIndent=0,
    spaceBefore=2, spaceAfter=2,
)
```

#### Option Layout Decision
```python
def format_options(options):
    """
    Decide option layout based on content length.
    Short options (≤4 chars each, ≤4 options) → 2×2 grid table
    Long options or >4 options → vertical list, one per line
    """
    max_len = max(len(opt) for opt in options)
    if len(options) <= 4 and max_len <= 6:  # CJK: 4 chars; Latin: 6 chars
        # 2×2 grid using Table
        grid = Table(
            [[options[0], options[1]], [options[2], options[3]]],
            colWidths=[200, 200], hAlign='LEFT'
        )
        grid.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 24),  # Match option indent
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        return grid
    else:
        # Vertical list
        return [Paragraph(f'{opt}', option_style) for opt in options]
```

#### Answer Space Reservation (MANDATORY)

**Every question MUST have adequate answer space. No exceptions.**

| Question Type | Minimum Space | Implementation |
|--------------|---------------|----------------|
| Multiple choice | 0 extra (options are the answer) | Just question + options |
| Fill-in-the-blank | Inline underline, min 80pt width | `<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>` or ReportLab `HRFlowable` |
| Short answer | 40-60pt (2-3 lines) | `Spacer(1, 50)` |
| Calculation / math work | 120-200pt (6-10 lines) | `Spacer(1, 160)` with light guide lines |
| Essay / long answer | 200-400pt (10-20 lines) | `Spacer(1, 300)` with light guide lines |
| Proof / derivation | 160-250pt (8-12 lines) | `Spacer(1, 200)` |

```python
# Answer line helper — light dashed lines for handwriting
def add_answer_lines(story, num_lines=8, line_spacing=20):
    """Add light guide lines for handwritten answers."""
    for i in range(num_lines):
        story.append(Spacer(1, line_spacing))
        story.append(HRFlowable(
            width='90%', thickness=0.3,
            color=colors.Color(0.8, 0.8, 0.8),  # Light gray
            dash=[4, 4],  # Dashed
            spaceAfter=0, spaceBefore=0
        ))
```

#### Page Density
- `spaceBefore=12pt` between questions minimum
- `spaceBefore=24pt` before section headers (一、二、三)
- Score indicator after question number: `1. (分值: 5分)` or `1. [5 pts]`
- Page header: exam title + time limit + total score
- No cover page unless explicitly requested

---

## Data-to-Ink Ratio Rules (MANDATORY for Reports)

**CRITICAL: Do NOT write long paragraphs to describe data trends.** You MUST extract metrics and trends into structured visual elements.

### Pattern Detection Table

Before writing ANY body paragraph, scan the text. If you find any of these patterns, extract them:

| Raw text pattern | ❌ FORBIDDEN | ✅ REQUIRED visual form |
|-----------------|-------------|----------------------|
| "revenue grew 12% to $4.2M" | Bury in paragraph prose | CalloutBox with bold `+12%` + `$4.2M` |
| "latency dropped from 120ms to 75ms" | Long explanatory sentence | CalloutBox or metrics table row |
| "Q1→Q2→Q3: 10%→25%→40%" | Inline numbers in text | Chart (matplotlib PNG → `Image()`) |
| "first...second...third..." steps | Paragraph with ordinal words | Numbered Table or process list |
| "compared to last year / vs Q2" | Nested comparisons in prose | Side-by-side comparison table |
| "accounted for 60% of total" | Percentage in paragraph | Pie chart or stacked bar chart |

### ReportLab CalloutBox Template

Use this pattern for extracted metrics - it's visually clean and takes only 5 lines:

```python
stat_style = ParagraphStyle(
    name='StatBig', fontName='FreeSerif', fontSize=22,
    leading=26, textColor=ACCENT, alignment=TA_CENTER  # From palette
)
label_style = ParagraphStyle(
    name='StatLabel', fontName='FreeSerif', fontSize=9,
    leading=12, textColor=TEXT_MUTED, alignment=TA_CENTER  # From palette
)

callout = Table(
    [[Paragraph('<b>+12%</b>', stat_style)],
     [Paragraph('Revenue Growth vs Q2', label_style)]],
    colWidths=[160]
)
callout.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,-1), BG_SURFACE),      # From palette --c-mid
    ('BOX', (0,0), (-1,-1), 1, ACCENT),               # From palette --c-accent
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(KeepTogether(callout))
```

---

## Final Checklist (Mandatory before delivery)

### Code & Build

- [ ] **Font restriction**: Only 6 registered fonts used
- [ ] **Font family registered**: `registerFontFamily()` called for all used fonts
- [ ] **⚠️ MANDATORY font fallback**: `install_font_fallback()` called after font registration — **#1 cause of Helvetica garbled text (乱码)**
- [ ] **Rich text tags**: Only inside `Paragraph()` objects
- [ ] **Table cells**: ALL text wrapped in `Paragraph()` — no plain strings
- [ ] **Scientific notation**: Large/small numbers use `<super>` tags
- [ ] **Chinese text**: `wordWrap='CJK'` in ParagraphStyle
- [ ] **Line breaks**: Using `<br/>` not `\n`
- [ ] **Headings**: Bold with `<b>` tags
- [ ] **Sanitization**: Code sanitized before execution

### Pagination & Overflow

- [ ] **Last page fill ratio ≥ 40%**: No large blank areas on final page
- [ ] **Major section 3/4 threshold**: H1 headings must NOT start in bottom 25% of page. Use `CondPageBreak(available_height * 0.25)`
- [ ] **Tables don't split**: Small tables `break-inside: avoid`. Large tables `thead { display: table-header-group }`
- [ ] **No orphan headings**: Use `break-after: avoid` / KeepTogether
- [ ] **sum(colWidths) ≤ available_width**: Verified in code
- [ ] **Images/charts scaled**: Always `fit_image()` or `max-width: 100%`
- [ ] **Long tables repeatRows=1**
- [ ] **CJK wordWrap='CJK'**
- [ ] **URLs word-break**: `overflow-wrap: break-word`

### Color & Design

- [ ] **Entire document ≤ 5 colors**: Primary + secondary + accent + neutral + background
- [ ] **All colors from palette**: Secondary/accent derived via lightness/saturation shift
- [ ] **Table headers use `HEADER_FILL`** (M tier, S ≤ 0.30) — NOT `ACCENT`
- [ ] **Table stripes use `TABLE_STRIPE`** (L tier, S ≤ 0.15)
- [ ] **Decorative elements ≤ 3 per page** (cover exempt)
- [ ] **No rainbow/multi-color schemes**: Single-family palette only
- [ ] **No decorative borders/textures on body pages**
- [ ] **2-typeface maximum**
- [ ] **🚫 NO stock images / clipart / AI decorations**

### Cover

- [ ] **正文编号从 1 开始**: 封面/目录不是章节，Step 3.5 映射表已输出
- [ ] **Cover default ON** for reports/proposals/analysis ≥ 3 pages
- [ ] **Single PDF output**: Cover merged as page 0 via pypdf
- [ ] **Page isolation**: Cover never shares page with TOC/body
- [ ] **🚫 NEVER use ReportLab for covers** — HTML/Playwright only
- [ ] **Z-Index Layers**: Layer 0 (bg) → 1 (decorative, CLIPPED) → 2 (lines) → 3 (text)
- [ ] **No dark/gradient backgrounds**
- [ ] **Cover whitespace ≥ 60%**
- [ ] **Cover colors from palette.cascade** `:root` CSS variables

### Tables

- [ ] **ALL tables horizontally centered** (`hAlign='CENTER'`)
- [ ] **Table width 85-100%** of content area
- [ ] **Table headers**: White bold text on `HEADER_FILL`

### Charts

- [ ] **No text overlap**: Labels, values, legends collision-free
- [ ] **Chart-to-text separation**: 24pt above/below, 8pt to caption
- [ ] **Legend outside chart area**: `bbox_to_anchor`
- [ ] **Pie → Donut** by default (hole_ratio 60-70%)
- [ ] **Axis cleanup**: Top/right spines deleted

### Layout

- [ ] **Margin symmetry**: `left_margin == right_margin`
- [ ] **Full-bleed (Playwright)**: `@page { margin: 0 }`
- [ ] **Content centering**: No left/right drift
- [ ] **Anti-void edges**: Content fills ≥ 60%

### Post-Build

- [ ] **Metadata**: `pdf.py meta.brand` — Title matches filename, Author/Creator = "Z.ai"
- [ ] **Blank page cleanup**: `pdf.py pages.clean`
- [ ] **Glyph check**: `pdf.py font.check`
- [ ] **TOC check**: `pdf.py toc.check` (if document has TOC)
- [ ] **PDF QA scan**: `pdf_qa.py`
