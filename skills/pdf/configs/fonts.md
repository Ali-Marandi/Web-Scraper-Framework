# Font System

## Font Stacks (by pipeline)

### Creative Pipeline (Playwright / HTML)

Fonts are loaded via Google Fonts CDN in the HTML `<head>`:

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=Noto+Sans+SC:wght@300;400;500;700;900&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
```

#### Variable Font (for Tension Typesetting)

When `tension_score` is used on `Glass_Canvas`, the engine switches to **Inter Variable** for continuous weight interpolation (100–900):

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap" rel="stylesheet">
```

This enables `font-variation-settings: 'wght' <value>` for smooth, non-discrete weight transitions. The standard discrete-weight URL is still used when tension is not active.

| Variable | Stack | Usage |
|----------|-------|-------|
| `--font-sans` | Inter, Noto Sans SC, Liberation Sans, Noto Color Emoji, sans-serif | Body text, UI elements, stats |
| `--font-serif` | Playfair Display, Noto Serif SC, Cormorant Garamond, Noto Color Emoji, serif | Hero text, editorial headlines |
| `--font-mono` | Liberation Mono, DejaVu Sans Mono, Noto Color Emoji, monospace | Floating meta, timestamps, codes |

### Report Pipeline (ReportLab)

ReportLab requires registered fonts. Primary Chinese font is **Noto Serif SC** (思源宋体, serif with sharp elegant strokes):

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# Primary Chinese font — Noto Serif SC (serif, high quality, OFL licensed)
# FONT_DIR = '/usr/share/fonts' (Linux) or '~/.openclaw/workspace/fonts' (macOS)
pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')

# Fallback / legacy Chinese fonts (sans-serif, static weight)
pdfmetrics.registerFont(TTFont('Noto Sans SC', f'{FONT_DIR}/truetype/chinese/NotoSansSC-Regular.ttf'))  # sans-serif fallback
pdfmetrics.registerFont(TTFont('Noto Sans SC Bold', f'{FONT_DIR}/truetype/chinese/NotoSansSC-Bold.ttf'))
# Use 'NotoSerifSC' for body, 'NotoSerifSC-Bold' for headings
```

> **⚠️ ReportLab CANNOT render emoji.** If content has emoji, route to Creative pipeline.

### Academic Pipeline (Tectonic / LaTeX)

CJK support via `ctex` package:
```latex
\usepackage{ctex}  % Auto-selects appropriate CJK fonts
```

For manual font selection:
```latex
\setCJKmainfont{Noto Serif CJK SC}
\setCJKsansfont{Noto Sans CJK SC}
```

> **⚠️ LaTeX silently drops emoji characters.** If content has emoji, route to Creative pipeline.

## Emoji Font Fallback

All Creative pipeline font stacks include emoji fallback:
- **macOS**: `Noto Color Emoji` (cross-platform, full color emoji)
- **Windows**: `Noto Color Emoji`
- **Linux**: `Noto Color Emoji` (install: `apt install fonts-noto-color-emoji`)

Chromium (used by Playwright) on macOS renders emoji natively — no extra configuration needed.

## CJK Font Weight Guide

| Weight Value | Inter Equivalent | Noto Sans SC Name | Usage |
|-------------|------------------|-------------------|-------|
| 300 | Light | Light | Subtitles, captions, meta text |
| 400 | Regular | Regular | Body text |
| 500 | Medium | Medium | Semi-emphasis |
| 700 | Bold | Bold | Headlines, emphasis |
| 900 | Black | Black | Hero text, stat numbers |

> **Tip**: Noto Sans SC weights 300–900 cover most use cases. Always load at least 400 and 700 via Google Fonts.

## Font Size Scale

Recommended type scale (base: 16px body):

| Role | Size | Weight | Line-Height |
|------|------|--------|-------------|
| Page Ghost Number | 240px | 900 | 1.0 |
| Hero (large) | clamp(48px, 10vw, 110px) | 900 | 0.88 |
| Hero (serif thin) | clamp(48px, 10vw, 110px) | 100 | 0.88 |
| Stat Number | clamp(32px, 5vw, 56px) | 900 | 0.9 |
| Section Title | 24px | 800 | 1.2 |
| Subsection | 20px | 700 | 1.3 |
| Body | 16px | 400 | 1.6–1.7 |
| Caption | 14px | 400 | 1.5 |
| Floating Meta | 10px | 400 (mono) | 1.4 |
| Stat Label | 11px | 400 | 1.2 |
