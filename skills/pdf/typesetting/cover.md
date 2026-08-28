# Cover Design - Cover Layout Engine Specification

> The cover is the first impression. Either skip it, or build it like architecture.

---

## ⚠️ Critical Rules (Read First)

1. **Cover is OPTIONAL.** Do NOT force a cover on documents that don't need one. When in doubt, skip.
2. **Unified cover system.** All routes (Report, Creative, Academic) use the HTML/Playwright cover system. **Template 01** is general-purpose (also covers government/bidding scenarios); **Template 07 is Crystal Blue (dark cover + light-blue body)**; **Templates 03-04** are academic-specific (dark backgrounds, scholarly typography; 04 also covers Chinese journal/keyword scenarios); **Template 06 is institutional (white bg, black border frame, structured fields)**. All routes generate covers via Playwright and merge via pypdf.
3. **Single PDF output.** Never deliver a separate cover PDF.
   - **Creative route**: Cover is part of the same HTML document → single PDF output inherently.
   - **Report route**: Cover PDF (Playwright) + body PDF (ReportLab) → merged via pypdf into one final PDF.
   - **Academic route**: Cover PDF (Playwright) + body PDF (Tectonic) → merged via pypdf into one final PDF.
4. **Page isolation.** Cover content must NEVER share a page with TOC, body text, or any subsequent content. Report/Academic: isolation is inherent in the merge pipeline. Creative: CSS page-break enforces isolation. Cover + TOC on the same page = **critical bug**.

---

## When to Include a Cover

| Document Type | Cover Needed | Notes |
|---------------|-------------|-------|
| Formal report (annual, research, white paper) | ✅ Required | Conveys professionalism |
| Proposal / plan | ✅ Required | First impression is everything |
| Resume | ❌ Not needed | Content itself is the cover |
| Menu / flyer / card | ❌ Not needed | Single page or function-oriented |
| Invitation | ❌ Not needed | The front side IS the cover |
| Lab report / academic paper | ⚠️ Situational | Add when template requires it |
| Portfolio / lookbook | ✅ Required | Cover sets the tone |

---

# PART 0: GLOBAL ENGINE ARCHITECTURE (Mandatory)

These three architectural upgrades are **mandatory** for ALL cover rendering. They eliminate 90% of squished/misaligned/overflow bugs at the engine level.

---

## A0.0 - Global Base Parameters

**All templates MUST obey these.**

```
W = page total width
H = page total height
U = W * 0.05           # Base spacing unit (5% of page width)
                        # All spacing should be multiples of U
```

**Coordinate origin:** `(0, 0)` at top-left corner. Some PDF libraries (ReportLab) use bottom-left origin - invert Y axis accordingly: `y_pdf = H - y_spec`.

---

## A0.1 - Absolute Anchor Grid (Replaces Flow Layout)

**Old (DEPRECATED):** `Y = previous_element_Y + height + spacing` - if one element overflows, everything below shifts and gets crushed.

**New (MANDATORY):** Page height = 100%. Every element group gets an **absolute percentage Y-anchor**. Elements may only grow **within their own bounding box**. They NEVER push or compress other blocks.

### Implementation Rule

```
# WRONG - flow layout (banned)
y_cursor = PAGE_H - top_margin
y_cursor -= title_height
y_cursor -= gap
y_cursor -= subtitle_height   # ← if title wraps, subtitle gets crushed

# RIGHT - absolute anchor grid
ANCHOR_TITLE_Y  = H * 0.30
ANCHOR_SUMMARY_Y = H * 0.50
ANCHOR_META_Y   = H * 0.70
ANCHOR_FOOTER_Y = H * 0.90
# Each block renders at its anchor, independent of others
```

### Bounding Box Containment

Each block has a **maximum bounding box** defined by two consecutive anchors:
- Block can grow downward within `[own_anchor_Y, next_anchor_Y - min_gap]`
- If content exceeds its bounding box → trigger overflow protection (see Part 3)
- Blocks NEVER consume space belonging to adjacent blocks

---

## A0.2 - Typography Weight & Spacing System

Use **weight**, **letter-spacing**, and **opacity** to create hierarchy - not just font size.

### Mandatory Type Roles

| Role | Size | Weight | Letter-Spacing | Line-Height | Opacity | Purpose |
|------|------|--------|----------------|-------------|---------|---------|
| **Kicker / Footer** (decorative text) | 16pt | Regular | 3pt (very wide) | - | 60% | Wide spacing + transparency makes 16pt text feel delicate and recessive |
| **Summary / Description** (summary paragraph)  | 16-18pt | Regular | normal | **1.6** | 85% | **Fill visual space** - 2-4 lines of descriptive text that prevents empty covers |
| **Meta / Subtitle** (secondary text) | 20-22pt | Light / Regular | normal | 1.4 | 85% | Comfortable reading rhythm, clear secondary hierarchy |
| **Hero Title** (main title) | 32-65pt (CJK: 32-80pt) | Black / Heavy (extra bold) | normal-tight | **1.15** (multi-line) | 100% | Must create overwhelming scale contrast; visually dominates the page. CJK characters need +15-20% size to match Latin visual weight. **⚠️ For 3-line CJK titles with subtitle, max ~42pt (see S3.1 table).** |

###  Data-to-Drawer Binding Rule

> **Hero Title = Company/entity name. Kicker = Report type/subtitle. Never reverse.**

When users provide structured information (company name + report name/type), they must be bound to typography drawers by these rules:

| User Data Field | Bound to Typography Role | Notes |
|-------------|-------------|------|
| **Company/entity name** (e.g. "GREENTECH") | **Hero Title** (45-65pt Heavy) | Company name is the **absolute visual center**, largest font, heaviest weight |
| **Report type/subtitle** (e.g. "2025 Annual Report Summary") | **Kicker** (16pt, letter-spacing 3pt, opacity 60%) | Report name is decorative supplementary text, placed in small text position at top-left/above title |
| **Summary/description** | **Summary** (16-18pt) | Detailed description text |
| **Date/author/version** | **Meta** (20-22pt) | Auxiliary information |
| **Document number/org signature** | **Footer** (16pt, opacity 60%) | Bottom closing |

**Mapping priority (when ambiguous):**
1. If user provides only one name → treat as company/entity name, bind to Hero Title
2. If user provides two names → shorter/more brand-like → Hero Title; longer/descriptive → Kicker or Summary
3. If user explicitly labels "title" and "subtitle" → title → Hero Title, subtitle → Kicker
4. **Never use report type names (e.g. "Annual Report", "White Paper") as Hero Title's largest text** - report type is always Kicker-level decorative text

### The Summary Block Rule (Anti-Void Iron Rule) 

> Every cover MUST include a Summary/Description text block. If the user provides no summary, the system MUST auto-generate one.

**Why:** A cover with only a title and date looks barren. The Summary block physically fills 2-4 lines of space, preventing the "empty field" aesthetic.

**Auto-generation rule:** When no summary/description is provided:
```python
# Generate a default summary
if not summary_text:
    summary_text = f"This report was generated by {org_name or 'the system'}, containing comprehensive data analysis and insights."
    # Or in English:
    # summary_text = f"This report presents comprehensive analysis and key insights prepared by {org_name or 'the organization'}."
```

**Constraints:**
- Width: template-specific (typically `W * 0.5` to `W * 0.6`)
- Lines: 2-4 lines (auto-wrap at width boundary)
- Never truncate summary - if too long, reduce to 4 lines max with `...`

### Font Weight Fallback

- If font family lacks Black/Heavy weight → use Bold + slightly larger size (+4pt)
- If font family lacks Light weight → use Regular + increased letter-spacing (+1pt)
- CJK fonts: Noto Serif SC for Regular/Light roles; for Heavy/Black → increase size by 15% to compensate for single-weight CJK fonts
- English kickers/footers: **FORCE UPPERCASE** via code (`text.upper()` / `toUpperCase()`)

---

## A0.3 - Z-Index Layer Management

All cover elements must be rendered in strict layer order. No exceptions.

| Layer | Z-Index | Contents | Rules |
|-------|---------|----------|-------|
| **Layer 0** (base) | 0 | Background fill (white / light gray) | Always rendered first; full page |
| **Layer 1** (background) | 1 | Grids, watermark letters, decorative blocks, large clipped graphics | **MUST enable clip-path** - background elements may extend beyond logical bounds but must be clipped to page physical bounds. Never let background elements inflate PDF page size. |
| **Layer 2** (structure) | 2 | Ultra-thin divider lines, sidebars, corner crop marks | Structural guides that define spatial zones |
| **Layer 3** (content) | 3 | All readable text content | Rendered last, always on top |

### Clip-Path Enforcement

```css
/* clip background overflow — ONLY on Layer 1 */
.cover-bg-layer {
  position: absolute;
  inset: 0;
  overflow: hidden;  /* MANDATORY */
  z-index: 1;
}
```

> ⚠️ **Clip scope = Layer 1 ONLY.** `overflow: hidden` must ONLY be on the Layer 1 background container. Layer 2 (lines) and Layer 3 (text) containers must NOT have `overflow: hidden`.

###  Anti-Clip Bug (Layer 3 Text Truncation Fix)

**Symptom:** Cover text is visible but truncated by an invisible boundary.

**Root cause:** `overflow: hidden` scope too broad, clipping text in Layer 3.

**Iron rule:**
```html
<!-- ✅ CORRECT - overflow:hidden only on Layer 1 -->
<div class="cover-layer-1" style="position:absolute; inset:0; overflow:hidden; z-index:1;">
  <!-- Background decorative elements -->
</div>
<div class="cover-layer-2" style="position:absolute; inset:0; z-index:2;">
  <!-- Structure lines, no overflow:hidden -->
</div>
<div class="cover-layer-3" style="position:absolute; inset:0; z-index:3;">
  <!-- Text content, no overflow:hidden -->
</div>

<!-- ❌ WRONG - global overflow:hidden clips text -->
<div class="cover-container" style="overflow:hidden;">
  <div class="layer-1">...</div>
  <div class="layer-2">...</div>
  <div class="layer-3">...</div>  <!-- Text gets clipped! -->
</div>
```

###  No Page Border/Frame

**Symptom:** A rectangular border appears around the entire cover page.

**Iron rule:**
```css
.cover-page {
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}
```

###  Minimum Spacing Between Decorative Lines and Text (Line-to-Text Spacing)

**Symptom:** Decorative lines on the cover (Layer 2 dividers, corner marks, sidebar edges) are flush against or overlapping with text.

**Iron rule:**
```
Minimum spacing between decorative lines and any text content = U (= W * 0.05)
i.e., at least 1 U of whitespace between line edges and text edges
```

| Line Type | Minimum Spacing | Notes |
|---------|---------|------|
| Horizontal divider | `U` above and below the line | Line must not be flush against title or body text |
| Vertical sidebar edge | `U` to the right of the line | Text inside sidebar must maintain spacing from the edge |
| Ultra-thick anchor line (Template 01) | `2 * U` to the right of the line | Thick line and title need ample breathing room |

---

# PART 1: 5 Cover Templates (Cover Rendering Specifications)

Coordinates use `W` (page width) and `H` (page height). `U = W * 0.05` (base spacing unit).

All templates inherit the A0.0-A0.3 architecture rules above.

**Each template now includes a mandatory Summary/Description drawer** to fill visual space.

---

## Template 01: HUD Data Terminal - Ultra-Thick Vertical Anchor Line

**Design intent:** A single bold vertical line on the left anchors all visual weight. The thick line eliminates left-side floating. Clean, data-driven, authoritative.

### Layer 1 - Background
- Full-page grid pattern: horizontal + vertical lines at ~50pt intervals
- Grid color: primary color at **2% opacity** (white background, nearly invisible)
- Grid line width: `0.5pt`

### Layer 2 - Structure
- **Left anchor line:** Start `(0.12*W, 0.1*H)`, End `(0.12*W, 0.9*H)`. Line width = **6pt**, primary color.


### Layer 3 - Content

**Content left edge: `X_content = 0.12*W + 30pt`** (offset from the thick line)

| Drawer | Y-Anchor | Content | Constraints |
|--------|----------|---------|-------------|
| **A - Kicker** | `0.15 * H` | Report type / subtitle (e.g. "2025 Annual Report Summary") | 16pt, Regular, letter-spacing 3pt, opacity 60%, uppercase |
| **B - Hero Title** | `0.30 * H` | **Company/entity name** (e.g. "GREENTECH") | 45-65pt (CJK: 50-80pt), Heavy. Company name is the visual center |
| **C - Summary**  | `0.50 * H` | 2-3 lines descriptive text about the report | 16-18pt, Regular, line-height 1.6, opacity 85%. **Width limit: `W * 0.6`**, auto-wrap. This drawer fills the mid-page void |
| **D - Meta/Date** | `0.75 * H` | Author, org, date | 16-20pt, Regular |

### Best For
Technology reports, data analysis, dashboard summaries, technical white papers

---

---

# PART 2: TEMPLATE SELECTION GUIDE

Template selection uses a two-dimensional matrix: **Intent** (from `visual_framework.md` 5-intent system) × **Document Type**. This replaces the old "Document Tone" classification and aligns with the Intent Mapping Table in `creative-fixed-canvas.md`.

| Intent | Document Type | Recommended Templates | Default |
|--------|---------------|----------------------|---------|
| **Calm** | Healthcare / Wellness / Minimalist | 07 Crystal Blue, 01 HUD | **07** |
| **Calm** | Academic / Research | 07 Crystal Blue, 04 Academic Symmetric | **07** |
| **Tension** | Crisis / Alert / Disruption | 01 HUD, 04 Academic Symmetric | **01** |
| **Energy** | Marketing / Creative / Design | 07 Crystal Blue, 04 Academic Symmetric | **07** |
| **Energy** | Technology / Data | 01 HUD, **07 Crystal Blue** | **07** |
| **Authority** | Formal / Corporate / Financial | 07 Crystal Blue, 04 Academic Symmetric | **04** |
| **Authority** | Government / Bidding | 01 HUD, 04 Academic Symmetric, **06 Institutional** | **01** |
| **Authority** | Thesis proposal / Dissertation cover | **06 Institutional** | **06** |
| **Authority** | Luxury / Editorial | 04 Academic Symmetric, 07 Crystal Blue | **04** |
| **Warmth** | Food / Lifestyle / Home | 07 Crystal Blue, 01 HUD | **07** |

> **Legacy mapping:** "Formal/Corporate" tone → Authority intent, "Minimalist" tone → Calm intent, "Luxurious/Editorial" tone → Authority intent.

**⚠️ No Global Default.** When no specific style is explicitly requested, the LLM MUST analyze the document's content, tone, and audience to autonomously select the most fitting template. Cross-reference the Intent (derived from content via `design_engine.py derive` or manual judgment) with the Document Type to find the best match. Every cover selection must be a deliberate design decision.

---

# PART 3: CODE-LEVEL SAFETY MEASURES (Pre-Render Safeguards)

These checks run BEFORE final rendering. They are **mandatory** - not optional optimizations.

---

## S3.0 - Cover Overlap Validation (MANDATORY)

**After generating the cover HTML and before rendering to PDF, run:**

```bash
node "$PDF_SKILL_DIR/scripts/cover_validate.js" cover.html
```

This detects text-vs-decorative-line overlaps by rendering the HTML and measuring actual bounding boxes. Exit code 1 = overlap found, must fix before generating the PDF.

The minimum gap between any text element and any decorative line is **1U (= 5% of page width ≈ 40px on A4)**. This catches the exact bug shown in the "text overlapping decorative lines" screenshots.

**If the check fails:**
1. Adjust the decorative line's Y position to maintain ≥ 1U gap from the nearest text
2. Or adjust the text block's position/size to avoid the overlap
3. Re-run `cover_validate.js` until it passes (exit code 0)

---

## S3.1 - Hero Title Overflow Protection (Title Line-Wrapping)

**Rule:** Hero title must NEVER exceed its template's width boundary.

1. If rendered width > max_width → word-wrap (CJK: any character; Latin: space/hyphen)
2. Multi-line hero titles: **lock line-height to 1.15**
3. Maximum lines: **3** — if 4+ lines needed, reduce font size by 4pt increments
4. Minimum font size floor: **32pt** (below this, truncate with `...`)

### Title Size vs Lines Quick-Reference (Template 01, zone B→C ≈ 225px)

| Lines | With subtitle | Without subtitle |
|-------|--------------|------------------|
| 1 | ≤ 80pt | ≤ 80pt |
| 2 | ≤ 55pt | ≤ 70pt |
| 3 | ≤ 42pt | ≤ 48pt |

**⚠️ CJK 3-line titles must reduce to ~42pt.** Do NOT use 50-80pt for 3-line CJK titles — it WILL overlap the Summary zone.

---

## S3.2 - Zone Collision Detection

After placing each text block, check if its bottom edge penetrates the next zone's top:

1. **Reposition first:** Push the collided zone down by `overlap + 20px` gap. All downstream zones shift together.
2. **Font reduction (if reposition insufficient):** Decrease title by 2pt increments. Floor: **32pt** for titles, 14pt for meta/summary.
3. **Truncation (last resort):** If font reduction hits floor and still collides, truncate with `...`

---

## S3.3 - Uppercase Lock

**Force-uppercase when content is English/Latin:**
- Kicker (category label / lead-in text)
- Footer (closing date / document number)
- Background watermark text
- Any Layer 1 decorative text

CJK text is exempt. Mixed CJK+Latin strings: uppercase only the Latin portions. Use `text-transform: uppercase` in CSS or `.upper()` in code.

---

## S3.4 - Hard Width Boundary Enforcement 

**Every drawer/zone has a maximum width. Text MUST respect this width exactly.** Use CSS `max-width` on text containers.

Vertical growth (more lines) is acceptable. Horizontal overflow is a **critical bug**.

---

## S3.5 - Mandatory Summary Auto-Generation 

**If the user provides only a title and no description/summary, auto-generate a 2-4 line placeholder.** A title-only cover looks barren. The Summary drawer physically fills mid-page void.

---

## S3.6 - Background Watermark Full-Display Enforcement 

**All watermark text in Layer 1 must be 100% within the visible page area. Cropping is strictly forbidden.**

**Applicable scope:**
- `cover-backgrounds.md` Recipe 2.1 giant sidebar pillar
- `cover-backgrounds.md` Recipe 2.2 bottom full-size text
- Any other decorative text in the background layer

**Rules:**
1. Horizontal text: rendered width must not exceed `W * 0.90` (5% safety margin each side)
2. Vertical/rotated text: rendered height must not exceed `H * 0.85` (7.5% safety margin top/bottom)
3. If exceeded, scale down font size proportionally — never truncate
4. Anchor coordinates must never exceed page boundaries

---

## S3.7 - Line-Length Alignment (Line Must Match Text Span)

**Decorative lines must be sized relative to the text they serve:**

- **Vertical lines:** height = text block height (± 1U padding above/below first/last element)
- **Horizontal lines:** width ≥ widest text element in its zone (up to 120%, NEVER shorter)

```css
.vline {
  position: absolute;
  top: var(--content-top);     /* align with first text element */
  bottom: var(--content-bottom); /* align with last text element */
}
.hline {
  width: max(100%, 200px);     /* at least as wide as parent text container */
}
```

**Checklist:**
- [ ] Every vertical line’s height matches its adjacent text block span
- [ ] Every horizontal line’s width ≥ widest text element in its zone
- [ ] No decorative line is shorter than the text it accompanies

---

## S3.8 - Vertical Balance (Anti-Top-Heavy Layout)

**Problem:** Content clusters at top of page, bottom 40%+ is dead whitespace.

**Rule:** When total content height < 50% of page height, switch to centered distribution (flexbox `justify-content: center`). Otherwise use anchor grid:

| Content Volume | Title Anchor | Summary Anchor | Meta Anchor |
|---------------|-------------|----------------|-------------|
| **Sparse** (fill < 50%) | Centered mode | Centered mode | Centered mode |
| **Normal** (fill 50-80%) | `H * 0.30` | `H * 0.48` | `H * 0.70` |
| **Dense** (fill > 80%) | `H * 0.20` | `H * 0.40` | `H * 0.65` |

**CJK Title Size Compensation:** CJK characters appear smaller at same pt size. Increase by 15-20%:
- CJK Hero Title: 50-80pt (Latin: 45-65pt)
- CJK Kicker: 11-12pt (Latin: 9pt)
- CJK Summary: 17-20pt (Latin: 16-18pt)

**Checklist:**
- [ ] No cover has >40% dead whitespace at the bottom
- [ ] CJK titles are 15-20% larger than equivalent Latin titles
- [ ] Sparse-content covers use centered distribution

---

## S3.9 - Percentage Positioning Requires Known-Size Container

**Problem:** `top: XX%` resolves against containing block’s height. If height is undefined (all children absolutely positioned), percentages collapse and elements stack.

**Iron rule:** Container with `top: XX%` children MUST have deterministic height (`height: 100%`, `inset: 0`, or `top` + `bottom` pair).

```css
/* ✅ Safest: flat structure with px values */
.cover { position: relative; width: 794px; height: 1123px; }
.kicker { position: absolute; top: 225px; left: 95px; }
.title  { position: absolute; top: 292px; left: 95px; }

/* ✅ OK: wrapper with inset:0 gives it known height */
.content-left { position: absolute; inset: 0; width: 55%; }
.title { position: absolute; top: 26%; }  /* 26% of 1123px ✓ */

/* ❌ BANNED: wrapper without height, percentage is undefined */
.content-left { position: absolute; left: 12%; top: 0; width: 55%; }
.title { position: absolute; top: 26%; }  /* 26% of WHAT? → overlap */
```

---

# PART 4: COVER COLOR RULES

> Cover colors must be consistent with the body color system - they cannot exist independently.
> **The cascade palette CSS output includes `--c-*` aliases** that map directly to cover template variables. Paste the CSS output into cover HTML's `:root` block — template 01 works without any manual color translation.

```
Cover primary    = Body theme color
Cover secondary  = Primary lightness variant (±20% lightness)
Cover background = Pure white / very light gray / primary at 5-8% opacity
```

### Absolutely Forbidden

- ❌ Dark large-area solid backgrounds (dark blue, dark green, black filling the page)
- ❌ Gradient backgrounds (any `linear-gradient` / `radial-gradient` as large-area fill)
- ❌ High-saturation color schemes
- ❌ Rainbow / multi-color gradients
- ❌ Dense textures or patterns
- ❌ Piling on decorative elements - restraint > clutter
- ❌ More than 2 typefaces on a cover
- ❌ Centered text + gradient/solid background (PowerPoint aesthetic)

### Safe Cover Color Schemes (Reference Only)

> ⚠️ These are **examples for reference**. In normal workflow, run `palette.cascade --title "<title>" --mode minimal --format css` to generate the actual cover colors. Do NOT copy these hex values directly.

> ✅ **Cascade CSS output includes `--c-*` aliases.** The `--format css` output automatically appends cover-compatible aliases (`--c-bg`, `--c-accent`, `--c-text`, `--c-muted`, `--c-mid`, `--c-surface`) mapped from cascade roles. Template 01 can consume the CSS output directly — no manual variable translation needed.
>
> | Cover alias | Cascade source | Tier | Purpose |
> |------------|---------------|------|---------|
> | `--c-bg` | `--page-bg` | XL | Cover background |
> | `--c-accent` | `--accent` | XS | Decorative lines, labels |
> | `--c-text` | `--text-primary` | text | Title text |
> | `--c-muted` | `--text-muted` | text | Subtitle, footer |
> | `--c-mid` | `--header-fill` | M | Structural fills |
> | `--c-surface` | `--card-bg` | L | Card/container bg |

| Name | Primary | Secondary | Background | Use Case |
|------|---------|-----------|------------|----------|
| Ink Stone | `#1a1a2e` | `#4a4a5e` | `#fafafa` | Business, formal |
| Indigo | `#1e3a5f` | `#2d5f8a` | `#f5f8fb` | Technology, reports |
| Warm Chestnut | `#5c3d2e` | `#8a6b5a` | `#faf6f3` | Culture, branding |
| Moss Green | `#2d4a3e` | `#4a7a6a` | `#f5f8f6` | Nature, health |
| Deep Crimson | `#6b2d3e` | `#9a4a5e` | `#faf5f6` | Traditional, elegant |

---

# PART 4.5: ACADEMIC COVER TEMPLATES (Templates 03-04)

> **Academic covers are exempt from PART 4 color rules.** Academic papers, theses, and research reports traditionally use dark backgrounds with light text - this is the established scholarly visual language. Templates 03-04 follow LaTeX title page conventions translated to HTML/CSS.

**All 2 templates share these rules:**
- Page size: `width: 794px; height: 1123px` (A4 at 96dpi)
- Full-bleed dark background (edge-to-edge, no margins)
- Serif font for titles (Playfair Display / Noto Serif SC), sans-serif for metadata
- Generated as HTML → Playwright `page.pdf()` → pypdf merge (same pipeline as Report covers)
- `<link>` tag for Google Fonts (NOT `@import`)

**Content slots (all templates):**
| Slot | Required | Example |
|------|----------|---------|
| `label` | Optional | `RESEARCH PAPER`, `博士论文` |
| `title` | **Required** | Paper title (auto-wrap, max 3 lines) |
| `subtitle` | Optional | Subtitle or abstract excerpt |
| `authors` | **Required** | Author name(s) |
| `institution` | Optional | University / lab / affiliation |
| `keywords` | Optional | Keyword list |
| `footer_left` | Optional | Journal name, DOI |
| `footer_right` | Optional | Date, version |

---

## Template 03: Academic Vertical Anchor - Dark bg + Left vertical line + Left-aligned

**Design intent:** Emulates the classic arXiv/preprint cover. A bold vertical accent line anchors the left edge, all text left-aligned with generous vertical rhythm. Serious, no-frills.

```
┌─────────────────────────────┐
│ ┃                           │
│ ┃  LABEL (9pt, accent)      │  ← y = H - 3.5cm
│ ┃                           │
│ ┃  Title (32pt Bold)        │  ← y = H - 6cm, line-height 42pt
│ ┃  Title line 2             │
│ ┃                           │
│ ┃  Subtitle (12pt)          │  ← y = H - 14cm
│ ┃                           │
│ ┃  Authors (12pt, white)    │  ← y = H - 18cm
│ ┃  Institution (10pt)       │
│ ┃                           │
│ ┃  Footer L       Footer R  │
└─────────────────────────────┘
┃ = vertical accent line at x=1.5cm, 2.5pt width
```

**Best for:** Research papers, technical reports, arXiv preprints

**HTML structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Noto+Serif+SC:wght@400;700;900&family=Inter:wght@300;400;500&family=Noto+Sans+SC:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    @page { size: 794px 1123px; margin: 0; }
    :root {
      --c-bg: #162032;
      --c-accent: #8B7E5A;
      --c-text: #FFFFFF;
      --c-muted: #8898A8;
      --c-footer: #607080;
    }
    html, body { margin: 0; padding: 0; width: 794px; height: 1123px; background: var(--c-bg); color: var(--c-text); font-family: 'Inter', 'Noto Sans SC', sans-serif; }
    @media screen {
      html { height: auto; display: flex; justify-content: center; min-height: 100vh; background: var(--c-bg); }
      body { transform-origin: top center; scale: min(1, calc(100vw / 794), calc(100vh / 1123)); margin: 0 auto; box-shadow: 0 0 60px rgba(0,0,0,0.3); }
    }
    .cover { width: 794px; height: 1123px; position: relative; box-sizing: border-box; }
    .vline { position: absolute; left: 57px; top: 76px; bottom: 76px; width: 2.5px; background: var(--c-accent); }
    .content { position: absolute; left: 83px; right: 76px; top: 0; bottom: 0; }
    .label { position: absolute; top: 132px; font-size: 9pt; color: var(--c-accent); letter-spacing: 3px; text-transform: uppercase; font-family: 'Inter', 'Noto Sans SC', sans-serif; }
    .title { position: absolute; top: 228px; font-size: 32pt; font-weight: 700; line-height: 1.3; font-family: 'Playfair Display', 'Noto Serif SC', serif; color: var(--c-text); max-width: 580px; }
    .subtitle { position: absolute; top: 530px; font-size: 12pt; line-height: 1.5; color: var(--c-muted); max-width: 500px; }
    .authors { position: absolute; top: 680px; font-size: 12pt; color: var(--c-text); }
    .institution { position: absolute; top: 740px; font-size: 10pt; color: var(--c-muted); line-height: 1.4; }
    .footer { position: absolute; bottom: 76px; left: 0; right: 0; display: flex; justify-content: space-between; font-size: 9pt; color: var(--c-footer); }
  </style>
</head>
<body>
  <div class="cover">
    <div class="vline"></div>
    <div class="content">
      <div class="label"><!-- LABEL --></div>
      <div class="title"><!-- TITLE --></div>
      <div class="subtitle"><!-- SUBTITLE --></div>
      <div class="authors"><!-- AUTHORS --></div>
      <div class="institution"><!-- INSTITUTION --></div>
      <div class="footer">
        <span><!-- FOOTER_LEFT --></span>
        <span><!-- FOOTER_RIGHT --></span>
      </div>
    </div>
  </div>
</body>
</html>
```

**Default palette (override via `palette.cascade --intent <intent> --mode dark --format css`):**
| Name | `--c-bg` | `--c-accent` | `--c-muted` | Use case |
|------|----------|------------|----------|----------|
| Deep Sea | `#162032` | `#8B7E5A` | `#8898A8` | General academic |
| Indigo | `#1e3a5f` | `#2d5f8a` | `#7A90A5` | Technical |
| Ink Stone | `#1a1a2e` | `#4a4a5e` | `#8080A0` | Formal occasions |

> ⚠️ These are **fallback defaults** when the palette system is unavailable. In normal workflow, run `palette.cascade` to generate mathematically harmonious colors and inject them into the `:root` variables.

---

## Template 04: Academic Symmetric - Dark bg + Top/bottom lines + Centered

**Design intent:** Emulates the classic IEEE/ACM Transactions title page. Perfect bilateral symmetry, thick horizontal rules frame the content zone. Formal and authoritative.

```
┌─────────────────────────────┐
│                             │
│   ══════════════════════    │  ← Top rule y=H-3cm, 2pt
│                             │
│        LABEL (centered)     │
│                             │
│     Title (28-30pt Bold)    │
│                             │
│        Subtitle             │
│                             │
│          Authors              │
│       Institution           │
│                             │
│   ══════════════════════    │  ← Bottom rule y=3cm, 2pt
│      Journal · Date         │
└─────────────────────────────┘
```

**Best for:** Top journal submissions, IEEE/ACM papers, theses

**HTML structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Noto+Serif+SC:wght@400;700;900&family=Inter:wght@300;400;500&family=Noto+Sans+SC:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    @page { size: 794px 1123px; margin: 0; }
    :root {
      --c-bg: #162032;
      --c-accent: #4A90C4;
      --c-text: #FFFFFF;
      --c-muted: #90A8C0;
    }
    html, body { margin: 0; padding: 0; width: 794px; height: 1123px; background: var(--c-bg); color: var(--c-text); font-family: 'Inter', 'Noto Sans SC', sans-serif; }
    @media screen {
      html { height: auto; display: flex; justify-content: center; min-height: 100vh; background: var(--c-bg); }
      body { transform-origin: top center; scale: min(1, calc(100vw / 794), calc(100vh / 1123)); margin: 0 auto; box-shadow: 0 0 60px rgba(0,0,0,0.3); }
    }
    .cover { width: 794px; height: 1123px; position: relative; display: flex; flex-direction: column; align-items: center; box-sizing: border-box; }
    .rule-top, .rule-bottom { position: absolute; left: 114px; right: 114px; height: 2px; background: var(--c-accent); }
    .rule-top { top: 114px; }
    .rule-bottom { bottom: 114px; }
    .center-block { position: absolute; top: 0; bottom: 0; left: 114px; right: 114px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
    .label { font-size: 9pt; color: var(--c-accent); letter-spacing: 3px; text-transform: uppercase; margin-bottom: 40px; font-family: 'Inter', 'Noto Sans SC', sans-serif; }
    .title { font-size: 30pt; font-weight: 700; line-height: 1.3; font-family: 'Playfair Display', 'Noto Serif SC', serif; margin-bottom: 24px; max-width: 500px; }
    .subtitle { font-size: 14pt; color: var(--c-muted); margin-bottom: 40px; max-width: 450px; line-height: 1.5; }
    .authors { font-size: 12pt; margin-bottom: 12px; }
    .institution { font-size: 10pt; color: var(--c-muted); line-height: 1.4; }
    .footer { position: absolute; bottom: 57px; left: 114px; right: 114px; text-align: center; font-size: 9pt; color: var(--c-muted); }
  </style>
</head>
<body>
  <div class="cover">
    <div class="rule-top"></div>
    <div class="rule-bottom"></div>
    <div class="center-block">
      <div class="label"><!-- LABEL --></div>
      <div class="title"><!-- TITLE --></div>
      <div class="subtitle"><!-- SUBTITLE --></div>
      <div class="authors"><!-- AUTHORS --></div>
      <div class="institution"><!-- INSTITUTION --></div>
    </div>
    <div class="footer"><!-- FOOTER --></div>
  </div>
</body>
</html>
```

**Default palette (override via `palette.cascade --intent <intent> --mode dark --format css`):**
| Name | `--c-bg` | `--c-accent` | `--c-muted` | Use case |
|------|----------|------------|----------|----------|
| Midnight Blue | `#162032` | `#4A90C4` | `#90A8C0` | Math/theoretical |
| Ink Blue | `#0D1B2A` | `#3D5A80` | `#8898A8` | Formal reports |
| Deep Navy | `#0a1628` | `#5B8DB8` | `#7A9AB5` | Engineering |

> ⚠️ These are **fallback defaults**. In normal workflow, run `palette.cascade` to generate colors and inject into `:root`.

---

---

## Template 06: Institutional - White bg + Black border frame + Structured field slots

**Design intent:** The universal institutional cover. White background with a thick black border frame, all content centered, structured field slots with underline placeholders. Matches the style required by most universities worldwide for thesis proposals, dissertations, and formal institutional documents. Also suitable for government reports and official submissions. Zero decorative elements - the formality IS the design.

**⚠️ This template is exempt from PART 4 Academic Cover Color Rules (dark backgrounds).** It uses a white/light background by design, aligning with institutional formatting requirements.

```
┌─────────────────────────────────┐
│  ┌─────────────────────────────┐  │
│  │                             │  │
│  │   INSTITUTION NAME           │  │  ← y = 12%, serif 28-34pt Bold
│  │   (校名/机构名)                │  │
│  │                             │  │
│  │   ━━━━━━━━━━━━━━━━━━━━  │  │  ← thick divider (2pt)
│  │                             │  │
│  │   DOCUMENT TYPE              │  │  ← y = 30%, 20-24pt
│  │   (开题报告/毕业论文/申报书)    │  │
│  │                             │  │
│  │   TITLE                     │  │  ← y = 40%, serif 26-30pt Bold
│  │   (论文题目)                   │  │    max 3 lines, centered
│  │                             │  │
│  │   Field: _______________    │  │  ← y = 58-78%, structured fields
│  │   Field: _______________    │  │    left-label + underline value
│  │   Field: _______________    │  │    e.g. 姓名、学号、导师、院系、日期
│  │   Field: _______________    │  │
│  │   Field: _______________    │  │
│  │                             │  │
│  │   DATE                      │  │  ← y = 88%, centered, 14pt
│  │                             │  │
│  └─────────────────────────────┘  │
└─────────────────────────────────┘
││ = 2.5pt black border, inset 5% from page edge
```

**Best for:** Thesis proposals (开题报告), dissertations, institutional reports, government documents, any formal submission with structured metadata fields

**Content slots:**
| Slot | Required | Example |
|------|----------|---------|
| `institution` | **Required** | "北京大学", "Massachusetts Institute of Technology" |
| `doc_type` | Optional | "开题报告", "Thesis Proposal", "毕业设计" |
| `title` | **Required** | Paper/document title (auto-wrap, max 3 lines) |
| `fields` | Optional | Array of `{label, value}` pairs. Common: 姓名/Name, 学号/ID, 导师/Advisor, 院系/Department, 专业/Major |
| `date` | Optional | "2026年4月", "April 2026" |

**HTML structure:**
```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@300;400;500;700&family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    @page { size: 794px 1123px; margin: 0; }
    :root {
      --c-bg: #ffffff;
      --c-text: #1a1a1a;
      --c-accent: #1a1a1a;
      --c-muted: #4a4a4a;
      --c-line: #333333;
    }
    html, body { margin: 0; padding: 0; width: 794px; height: 1123px; background: var(--c-bg); color: var(--c-text); font-family: 'Noto Sans SC', 'Inter', sans-serif; }
    @media screen {
      html { height: auto; display: flex; justify-content: center; min-height: 100vh; background: #e8e8e8; }
      body { transform-origin: top center; scale: min(1, calc(100vw / 794), calc(100vh / 1123)); margin: 0 auto; box-shadow: 0 0 60px rgba(0,0,0,0.15); }
    }
    .cover {
      width: 794px; height: 1123px; position: relative; box-sizing: border-box;
    }
    /* Black border frame - inset 5% from page edge */
    .border-frame {
      position: absolute;
      top: 56px; left: 40px; right: 40px; bottom: 56px;
      border: 2.5px solid var(--c-accent);
      pointer-events: none;
    }
    /* Content area inside frame */
    .content {
      position: absolute;
      top: 56px; left: 40px; right: 40px; bottom: 56px;
      display: flex; flex-direction: column; align-items: center;
      padding: 60px 50px;
      box-sizing: border-box;
    }
    .institution {
      font-size: 30pt; font-weight: 700; letter-spacing: 6px;
      font-family: 'Noto Serif SC', 'Playfair Display', serif;
      text-align: center; margin-bottom: 30px;
      max-width: 580px;
    }
    .thick-divider {
      width: 70%; height: 2px; background: var(--c-accent);
      margin-bottom: 40px;
    }
    .doc-type {
      font-size: 22pt; font-weight: 400; letter-spacing: 4px;
      text-align: center; margin-bottom: 50px;
      color: var(--c-text);
    }
    .title {
      font-size: 26pt; font-weight: 700; line-height: 1.4;
      font-family: 'Noto Serif SC', 'Playfair Display', serif;
      text-align: center; margin-bottom: 60px;
      max-width: 520px;
    }
    .fields-block {
      width: 400px; margin-bottom: auto;
    }
    .field-row {
      display: flex; align-items: baseline;
      margin-bottom: 28px; font-size: 14pt;
    }
    .field-label {
      white-space: nowrap; margin-right: 12px;
      color: var(--c-text); font-weight: 400;
      letter-spacing: 2px;
    }
    .field-value {
      flex: 1; text-align: center;
      border-bottom: 1px solid var(--c-line);
      padding-bottom: 4px; min-height: 24px;
      font-family: 'Noto Sans SC', 'Inter', sans-serif;
    }
    .date-block {
      font-size: 14pt; color: var(--c-muted);
      text-align: center; letter-spacing: 2px;
      margin-top: auto; padding-top: 30px;
    }
  </style>
</head>
<body>
  <div class="cover">
    <div class="border-frame"></div>
    <div class="content">
      <div class="institution"><!-- INSTITUTION --></div>
      <div class="thick-divider"></div>
      <div class="doc-type"><!-- DOC_TYPE --></div>
      <div class="title"><!-- TITLE --></div>
      <div class="fields-block">
        <div class="field-row">
          <span class="field-label"><!-- LABEL_1 --></span>
          <span class="field-value"><!-- VALUE_1 --></span>
        </div>
        <div class="field-row">
          <span class="field-label"><!-- LABEL_2 --></span>
          <span class="field-value"><!-- VALUE_2 --></span>
        </div>
        <div class="field-row">
          <span class="field-label"><!-- LABEL_3 --></span>
          <span class="field-value"><!-- VALUE_3 --></span>
        </div>
        <div class="field-row">
          <span class="field-label"><!-- LABEL_4 --></span>
          <span class="field-value"><!-- VALUE_4 --></span>
        </div>
        <div class="field-row">
          <span class="field-label"><!-- LABEL_5 --></span>
          <span class="field-value"><!-- VALUE_5 --></span>
        </div>
      </div>
      <div class="date-block"><!-- DATE --></div>
    </div>
  </div>
</body>
</html>
```

**Layout rules:**
1. **Border frame**: 2.5pt solid black, inset ~5% from all page edges (40px left/right, 56px top/bottom on A4 at 96dpi). This is the defining visual element.
2. **Institution name**: Centered, serif, 28-34pt Bold, letter-spacing 4-6px. For CJK names, use wider letter-spacing (6px). For Latin names, use standard (3px).
3. **Thick divider**: 2pt solid line, 70% width, separates institution from content below.
4. **Document type**: 20-24pt, lighter weight than institution name, letter-spacing 3-4px. This slot differentiates document categories (e.g. "开题报告" / "Thesis Proposal" / "毕业论文" / "Graduation Design").
5. **Title**: Serif, 26-30pt Bold, max 3 lines, centered. Auto-wrap at 520px width.
6. **Structured fields**: Left-aligned label + centered underline value. Label width fixed by longest label in the set. 3-7 field rows supported. Common fields: Name/姓名, Student ID/学号, Advisor/导师, Department/院系, Major/专业.
7. **Date**: Centered at bottom, 14pt, letter-spacing 2px.

**Field auto-detection:**
When the user provides structured metadata (name, student ID, advisor, etc.), auto-populate the fields block. When no fields are provided, omit the fields-block entirely and let the title expand vertically into the freed space.

**Variant 06B - Double border:**
For extra formality (government documents, official submissions), replace the single border with a double border (outer 2.5pt + inner 1pt, 6px gap):
```css
.border-frame {
  border: 2.5px solid var(--c-accent);
  outline: 1px solid var(--c-accent);
  outline-offset: 6px;
}
```

**This template has NO background decoration layer, NO watermarks, NO gradients.** The black frame + white space IS the design.

---

## Template 07: Crystal Blue - Deep Blue Night Sky with Luminous Accents

**Design intent:** Crystalline, translucent deep blue with glowing accents. Dark cover transitions to light-blue body. The entire document lives in one blue hue family (~215°). Subtle radial glow hints create glass-like depth without being flashy.

### Color System

**Cover (dark):**
| Role | Hex | Description |
|------|-----|-------------|
| Background | `#0a1628` | Deep blue night sky |
| Accent line/label | `#4da8da` | Luminous bright blue |
| Title text | `#e8f0f8` | Cool white with blue tint |
| Muted text | `#7a9bb8` | Blue-gray |
| Glow/sidebar | `#2d7ab3` | Mid-blue (gradient source) |

**Body (light) — same hue family:**
| Role | Cascade Tier | Hex | Usage |
|------|-------------|-----|-------|
| Page background | XL | `#f5f8fc` | Ultra-light blue-white |
| Section background | XL | `#edf2f9` | Light blue-gray |
| Card background | L | `#e4ecf5` | Soft blue card |
| Table stripe | L | `#eef3fa` | Subtle blue row |
| Table header | M | `#1a4a7a` | Deep blue (bridges to cover) |
| Border | S | `#c0d0e2` | Blue-gray lines |
| Accent | XS | `#2d7ab3` | = cover glow color |
| Text primary | text | `#142840` | Deep blue-black (not pure black) |
| Text muted | text | `#5a7a96` | Blue-gray secondary |

### Layer 2 - Structure
- **Rectangular frame:** A single continuous rectangular border, inset 60px from all edges (top/bottom = 80px). Stroke = **2px**, color = `#4da8da` (accent). This forms a clean luminous blue frame around the entire cover content area.
  - Top edge: `Y = 80px`, from `X = 60px` to `X = W - 60px`
  - Bottom edge: `Y = H - 80px`, from `X = 60px` to `X = W - 60px`
  - Left edge: `X = 60px`, from `Y = 80px` to `Y = H - 80px`
  - Right edge: `X = W - 60px`, from `Y = 80px` to `Y = H - 80px`
- **Background glow (optional):** Two subtle `radial-gradient` circles (6-8% opacity) positioned at upper-left and lower-right. Creates depth without visible shapes.

### Layer 3 - Content

| Element | Position | Constraints |
|---------|----------|-------------|
| Kicker | `X = 90px`, `Y = 0.12*H` | 11pt, accent color (#4da8da), letter-spacing 5px, uppercase, font-weight 300 |
| Hero Title | `X = 90px`, `Y = 0.21*H` | 50pt (CJK 55pt), weight 900, Noto Serif SC, cool white (#e8f0f8), subtle text-shadow with blue glow |
| Summary | `X = 90px`, `Y = 0.45*H` | 15pt, line-height 1.7, muted (#7a9bb8), max-width 520px |
| Organization | `X = 90px`, `Y = 0.64*H` | 18pt, cool white |
| Date | `X = 90px`, `Y = H - 80px` | 10pt, muted, letter-spacing 3px |

### Recommended Palette Generation

```bash
# For documents using this template, the palette is fixed (not auto-generated).
# Copy the body palette values directly from the table above.
# Cover colors are hardcoded in the template HTML.
```

### Best For
Technology reports, data analysis, AI/ML research, fintech, SaaS product reports, anything that benefits from a modern, polished, slightly premium blue aesthetic.

---

### Academic Template Selection Guide

| Scenario | Template | Rationale |
|----------|----------|-----------|
| arXiv preprint, technical report | **03** (Vertical Anchor) | Left-aligned, data-dense feel |
| IEEE/ACM paper, English thesis | **04** (Symmetric) | Classic bilateral symmetry |
| Chinese thesis, journal with keywords | **04** (Symmetric) | Classic symmetry + keyword support via subtitle/summary slots |
| **Thesis proposal, institutional cover, government doc** | **06** (Institutional) | **White bg, black border frame, structured field slots** |
| Light/formal academic (white bg) | **01** (HUD) | Use standard cover system |


Covers support a **background decoration layer** rendered behind all foreground content (Layer 1). This layer adds subtle depth through supergraphics, typographic watermarks, and blueprint hairlines.

See → `typesetting/cover-backgrounds.md` - complete specification with modules, recipes, and constraint matrix.

**Quick reference:**
- **Recipe A (Minimalist Modern)**: Deep-space arc only - safest, max whitespace
- **Recipe B (Engineering Academic)**: Coordinate cross + vertical spine text - precision, engineering feel
- **Recipe C (Stable & Authoritative)**: Angle slash + bottom bleed text - heavy, authoritative

**Background layer is OPTIONAL.** Not every cover needs one. Template 01 already defines its own Layer 1 background - use the recipes only when a template's built-in background is insufficient.

