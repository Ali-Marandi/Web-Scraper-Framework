# Brief: PDF Processing

Work with existing PDFs: extract, merge, split, fill forms, convert formats, or **reformat** with a new design. Usually a Light triage path — except reformat, which escalates to Standard.

---

## Decision Tree

```
User request
  ├─ "Extract text/tables/images"     → §Extract
  │     └─ No text extracted?         → §OCR Fallback
  ├─ "Merge/split/rotate/crop pages"  → §Pages
  ├─ "Fill a form"                    → §Forms (check fillable first)
  ├─ "Read/write metadata"            → §Metadata
  ├─ "Convert DOCX/PPTX/XLSX to PDF" → §Convert
  │     └─ DOCX with TOC?            → §DOCX Pipeline (5-step)
  ├─ "Redesign/reformat a document"   → §Reformat
  │     └─ With a reference template? → §Template-Guided Reformat
  ├─ "Decrypt/repair a PDF"           → §Encrypted / §Corrupted
  ├─ "Optimize file size"             → §Optimize
  └─ "Batch process many PDFs"        → §Batch Processing
```

---

## Environment Check

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" env.check
```

Reports availability but does **not** auto-install. 

Entry point: `python3 "$PDF_SKILL_DIR/scripts/pdf.py" <group>.<action> [options]`

All commands return JSON on stdout (`{"status": "success", "data": {...}}`) or stderr (`{"status": "error", ...}`).
Exit codes: 0 = success, 1 = bad args, 2 = file not found, 3 = parse error, 4 = operation failed.

---

## §Extract

### Basic Extraction (pdf.py)

```bash
# Text (full or page range)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.text report.pdf
python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.text report.pdf -p 1-3
python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.text report.pdf -p 1,4,7

# Tables — returns structured JSON
python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.table report.pdf

# Images — dumps embedded rasters to directory
python3 "$PDF_SKILL_DIR/scripts/pdf.py" extract.image report.pdf -o ./images/
```

### Precise Coordinates (pdfplumber)

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]

    # Characters with exact coordinates
    for char in page.chars[:10]:
        print(f"'{char['text']}' at x:{char['x0']:.1f} y:{char['y0']:.1f}")

    # Text within a bounding box (left, top, right, bottom)
    bbox_text = page.within_bbox((100, 100, 400, 200)).extract_text()

    # Advanced table extraction with custom settings
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "intersection_tolerance": 15
    }
    tables = page.extract_tables(table_settings)

    # Visual debugging
    img = page.to_image(resolution=150)
    img.save("debug_layout.png")
```

### Fast Rendering (pypdfium2)

pypdfium2 is a Python binding for PDFium (Chromium's PDF library) — fast rendering and text extraction.

```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("document.pdf")

# Render single page
bitmap = pdf[0].render(scale=2.0)
bitmap.to_pil().save("page_1.png", "PNG")

# Batch render all pages
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.5)
    bitmap.to_pil().save(f"page_{i+1}.jpg", "JPEG", quality=90)

# Extract text
for i, page in enumerate(pdf):
    print(f"Page {i+1}: {len(page.get_text())} chars")
```

### CLI Rendering & Extraction (poppler-utils)

```bash
# High-resolution PNG rendering
pdftoppm -png -r 300 document.pdf output_prefix
pdftoppm -png -r 600 -f 1 -l 3 document.pdf high_res   # specific pages

# Text with bounding box coordinates
pdftotext -bbox-layout document.pdf output.xml

# Extract embedded images (faster than full-page rendering)
pdfimages -all document.pdf images/img
pdfimages -list document.pdf
```

### §OCR Fallback (Scanned PDFs)

When `pdfplumber` extracts 0 characters, the PDF is likely a scanned image:

```python
import pytesseract
from pdf2image import convert_from_path

def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    return "".join(pytesseract.image_to_string(img) for img in images)
```

Prerequisites: `pip install pdf2image pytesseract` + install Tesseract OCR and poppler.

---

## §Pages

### Basic Operations (pdf.py)

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.merge a.pdf b.pdf -o combined.pdf
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.split book.pdf -o ./chapters/
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.rotate doc.pdf 90 -o rotated.pdf
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.rotate doc.pdf 180 -o rotated.pdf -p 1-3
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.crop doc.pdf 50,50,550,750 -o trimmed.pdf
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.clean doc.pdf -o cleaned.pdf
```

### Complex Page Manipulation (qpdf)

```bash
# Split into groups of N pages
qpdf --split-pages=3 input.pdf output_group_%02d.pdf

# Extract complex page ranges
qpdf input.pdf --pages input.pdf 1,3-5,8,10-end -- extracted.pdf

# Merge specific pages from multiple PDFs
qpdf --empty --pages doc1.pdf 1-3 doc2.pdf 5-7 doc3.pdf 2,4 -- combined.pdf
```

---

## §Metadata

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" meta.get doc.pdf
python3 "$PDF_SKILL_DIR/scripts/pdf.py" meta.set doc.pdf -o out.pdf -d '{"Title": "Report", "Author": "Jane"}'
python3 "$PDF_SKILL_DIR/scripts/pdf.py" meta.brand doc.pdf -o branded.pdf
```

Recognised keys: `Title`, `Author`, `Subject`, `Keywords`, `Creator`, `Producer`.

---

## §Forms

### Step 1 — Check if fillable

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.info input.pdf
```

If `has_fields: true` → **Fillable workflow**. If `false` → **Non-fillable workflow**.

### Fillable Workflow

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.fill input.pdf -o filled.pdf \
  -d '{"name": "John", "agree": "true", "country": "US"}'
```

| Type | Value | Example |
|------|-------|---------|
| text | Free string | `"name": "Jane Doe"` |
| checkbox | `"true"` / `"false"` | `"agree": "true"` |
| radio | One of `radio_options[].value` | `"gender": "/Choice1"` |
| dropdown | One of `choice_options[].value` | `"country": "US"` |

For complex forms: `form.detail input.pdf -o fields.json` (full field info) and `form.render input.pdf -o ./pages/` (visual check).

### Non-Fillable Workflow (Annotation-Based)

For PDFs without interactive fields (scanned forms, image-based). All four steps are mandatory.

**Step 1 — Render pages as PNG**:
```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.render input.pdf -o ./pages/
```

**Step 2 — Create `fields.json`** with annotation regions. Determine bbox coordinates by inspecting the rendered PNG (use PIL to get pixel dimensions, then estimate [left, top, right, bottom] for each field). `dims` must match PNG dimensions exactly.

```json
{
  "sheet": [{
    "pg": 1, "dims": [1000, 1400],
    "regions": [{
      "id": "last_name", "hint": "Last name field",
      "label": {"tag": "Last name", "bbox": [30, 125, 95, 142]},
      "target": {"bbox": [100, 125, 280, 142]},
      "ink": {"value": "Simpson", "size": 14, "color": "000000"}
    }]
  }]
}
```

**Step 3 — Validate**:
```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.check-bbox fields.json
python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.validate 1 fields.json page1.png validation.png
```

**Step 4 — Fill**:
```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" form.annotate input.pdf fields.json -o filled.pdf
```

---

## §Encrypted

```bash
# Check encryption status
qpdf --show-encryption encrypted.pdf

# Decrypt with password
qpdf --password=secret123 --decrypt encrypted.pdf decrypted.pdf

# Encrypt a PDF
qpdf --encrypt user_pass owner_pass 256 --print=none --modify=none -- input.pdf encrypted.pdf
```

Python alternative:
```python
from pypdf import PdfReader
reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("password")
```

---

## §Corrupted

```bash
qpdf --check corrupted.pdf
qpdf --replace-input corrupted.pdf   # in-place repair
```

---

## §Optimize

```bash
qpdf --linearize input.pdf optimized.pdf           # web-optimized (fast first-page load)
qpdf --optimize-level=all input.pdf compressed.pdf  # maximum compression
```

---

## §Reformat

Take an existing document and rebuild it with a new visual design. Content is preserved; layout is rebuilt.

```
1. EXTRACT   → Extract content from source
2. STRUCTURE → Organize into sections (headings, body, tables, lists)
3. DELEGATE  → Route to appropriate brief:
                 Structured → briefs/report.md (ReportLab)
                 Visual     → briefs/creative-fixed-canvas.md (Playwright)
4. BUILD     → Follow the delegated brief's full workflow
5. DELIVER   → New PDF, same content, new design
```

### §Template-Guided Reformat

When user provides a reference PDF to match:

```
1. ANALYZE  → Extract design DNA from template:
               - meta.get (page size), extract.image (color samples),
                 extract.text (structure), pdftoppm (visual reference)
2. DOCUMENT → Record: page size, margins, colors, fonts, layout, header/footer
3. DELEGATE → Route to brief WITH design constraints (not defaults)
4. BUILD    → Follow brief workflow, constrained to template DNA
5. COMPARE  → pdftoppm both, visually compare side-by-side
```

**Key principles:** Match the spirit, not the pixels. Prefer source files over PDF when available. Declare font substitutions upfront.

---

## §Convert

### Office → PDF (LibreOffice)

```bash
python3 "$PDF_SKILL_DIR/scripts/pdf.py" convert.office input.docx -o output.pdf
# Or directly:
soffice --headless --convert-to pdf --outdir ./output input.docx
```

**Supported**: `.docx`, `.doc`, `.odt`, `.rtf`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.ods`, `.csv`, `.html`

**macOS path**: `/Applications/LibreOffice.app/Contents/MacOS/soffice`

**Gotchas:**
- soffice allows only one instance at a time; use `--env:UserInstallation=file:///tmp/libreoffice_tmp` if needed
- Missing Chinese fonts → squares. Ensure Noto Sans SC/Noto Serif SC are installed
- Large files (>50MB) may take 1-2 min; set reasonable timeout

**Priority**: Always prefer soffice for Office→PDF. Fall back to python-pptx/python-docx + HTML + Playwright only if soffice is unavailable.

### Spreadsheet → PDF (without LibreOffice)

Use openpyxl + HTML + Playwright. Columns ≤ 6 → portrait; > 6 → landscape. Scale font inversely with column count.

### §DOCX Pipeline (5-Step with TOC)

For DOCX files that need TOC generation/correction (LibreOffice `--headless` does not recalculate PAGEREF fields).

**When to use**: DOCX has 3+ headings, or mentions "table of contents" / "TOC", or already contains a TOC section. When in doubt, run `toc_validate.py fix-docx` — if it returns `no_toc_needed`, simple conversion is fine.

```bash
# Step 1: Convert to PDF (pass1)
python3 "$PDF_SKILL_DIR/scripts/pdf.py" convert.office input.docx -o pass1.pdf

# Step 2: Clean blank pages
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.clean pass1.pdf -o pass1_clean.pdf

# Step 3: Fix TOC (adds HYPERLINK + PAGEREF + bookmarks)
python3 "$PDF_SKILL_DIR/scripts/toc_validate.py" fix-docx input.docx -o fixed.docx

# Step 4: Correct TOC page numbers using pass1 as reference
python3 "$PDF_SKILL_DIR/scripts/toc_validate.py" fix-pages fixed.docx pass1_clean.pdf -o final.docx

# Step 5: Final convert + clean
python3 "$PDF_SKILL_DIR/scripts/pdf.py" convert.office final.docx -o output.pdf
python3 "$PDF_SKILL_DIR/scripts/pdf.py" pages.clean output.pdf -o output_clean.pdf
```

Check `fix-docx` output `action`: `fixed` → use fixed.docx, `skipped` → use original, `no_toc_needed` → skip to Step 5.

Optional post-validation: `toc_validate.py check-conversion final.docx output_clean.pdf`

---

## §Batch Processing

```python
import os, glob, logging
from pypdf import PdfReader, PdfWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_process(input_dir, operation='merge'):
    pdf_files = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    if operation == 'merge':
        writer = PdfWriter()
        for f in pdf_files:
            try:
                for page in PdfReader(f).pages:
                    writer.add_page(page)
                logger.info(f"Processed: {f}")
            except Exception as e:
                logger.error(f"Failed: {f}: {e}")
        with open("merged.pdf", "wb") as out:
            writer.write(out)
    elif operation == 'extract_text':
        for f in pdf_files:
            try:
                text = "".join(p.extract_text() for p in PdfReader(f).pages)
                with open(f.replace('.pdf', '.txt'), 'w') as out:
                    out.write(text)
            except Exception as e:
                logger.error(f"Failed: {f}: {e}")
```

---

## Caveats & Performance

| Topic | Detail |
|-------|--------|
| < 50 MB | Instant |
| 50–200 MB | 1–2 minutes |
| > 200 MB | Split first, or extend timeout |
| Memory | ~2-3× input file size |
| Text extraction speed | `pdftotext -bbox-layout` fastest; pdfplumber for structured data |
| Image extraction | `pdfimages` faster than full-page rendering |
| Large PDFs | Process in chunks to manage memory |

## Tooling Inventory

| Library / Tool | Role | Licence |
|----------------|------|---------|
| pikepdf | Low-level PDF manipulation (forms, pages, metadata) | MPL-2.0 |
| pdfplumber | Content extraction (text, tables) | MIT |
| pypdfium2 | Fast rendering, text extraction (PyMuPDF alternative) | Apache/BSD |
| pypdf | Merge, split, crop, metadata, encryption | BSD |
| poppler-utils | CLI text/image extraction, rendering | GPL-2 |
| qpdf | Page manipulation, optimization, encryption, repair | Apache |
| pytesseract | OCR for scanned PDFs | Apache |
| pdf2image | PDF-to-image conversion via poppler | MIT |
| LibreOffice | Office format conversion engine | MPL-2.0 |
