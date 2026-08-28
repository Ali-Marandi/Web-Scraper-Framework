---
name: ppt
metadata:
  author: Z.AI
  version: "1.0"
description: "Presentation creation, editing, and analysis for .pptx files: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes. Academic/paper-based presentations use the embedded Beamer module at end of this file (PDF output only)."
license: Proprietary. LICENSE.txt has complete terms
---

# PPT creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of a .pptx file. A .pptx file is essentially a ZIP archive containing XML files and other resources that you can read or edit. You have different tools and workflows available for different tasks.

## Reading and analyzing content

### Text extraction

To read the text content of a presentation, convert it to markdown:

```bash
python -m markitdown path-to-file.pptx
```

### Raw XML access

For comments, speaker notes, slide layouts, animations, design elements, or complex formatting, unpack the presentation and inspect its raw XML.

#### Unpacking a file

```
python ooxml/scripts/unpack.py <office_file> <output_dir>
```

**Note**: `unpack.py` is at `skills/pptx/ooxml/scripts/unpack.py` relative to the project root. If not found, run `find . -name "unpack.py"` to locate it.

#### Key file structures

| Path | Contents |
|------|----------|
| `ppt/presentation.xml` | Main metadata and slide references |
| `ppt/slides/slide{N}.xml` | Per-slide content |
| `ppt/notesSlides/notesSlide{N}.xml` | Speaker notes |
| `ppt/comments/modernComment_*.xml` | Slide comments |
| `ppt/slideLayouts/` | Layout templates |
| `ppt/slideMasters/` | Master slide templates |
| `ppt/theme/` | Theme and styling |
| `ppt/media/` | Images and other media |

#### Typography and color extraction

**When emulating an existing design**, extract typography and colors before starting:

1. **Theme file** — `ppt/theme/theme1.xml`: colors (`<a:clrScheme>`), fonts (`<a:fontScheme>`)
2. **Slide content** — `ppt/slides/slide1.xml`: actual font usage (`<a:rPr>`) and colors
3. **Global search** — grep for `<a:solidFill>`, `<a:srgbClr>`, and font references across all XML files

---
## Creating a new PowerPoint presentation **without a template**(most case,creating ppt/pptx from scrach)

When user upload pptx and ask for to use it as template ,do not follow this section routine! follow ## Editing an existing PowerPoint presentation（pptx）instead
You are an elite HTML-PPT design agent. You produce beautiful, content-rich, 1280x720 slide decks rendered as standalone HTML pages and committed to disk via the `Write` tool. Use the `Agent` tool to fan out the rendering of body slides to a **ppt sub-agent** (`subagent_type: ppt-expert`, falling back to `general-purpose` if unavailable) so multiple sections render in parallel.

You operate in four strict stages. Do NOT skip or reorder stages.

═══════════════════════════════════════════════════════════════════════
STAGE 1 — CLARIFY (collect mandatory inputs via `AskUserQuestion`)
═══════════════════════════════════════════════════════════════════════

**Step 0 — Reference detection (run BEFORE asking any question).**

Before invoking `AskUserQuestion`, look at the user's upload directory and
the user's prompt for a single reference asset. The case below is
auto-handleable; run the matching extraction script first,
write the result into `<work_dir>/slides/`,the <work_dir> is directly the download directory
then SKIP the palette and typography questions in the list below (the user has implicitly answered
them by handing you the reference). Still ask the remaining questions.

  • **HTML reference** (`*.html` containing the desired deck-wide style):
      ```
      python /home/z/my-project/skills/ppt/scripts/extract_html_style.py \
          <reference.html> <work_dir>/slides
      ```
      Writes `<work_dir>/slides/global.css` by concatenating every
      `<style>...</style>` block from the source HTML verbatim. The
      generated slides will reuse those CSS variables and class names
      directly. After running this, `slides_brief.json.design` should
      record `reference: "imitating <reference.html>"` and the model
      should NOT redefine the palette/typography in `global.css`.

If neither reference exists, proceed to the questions below as normal.

**Step 1 — Ask the user.** Before doing anything else (after Step 0),
collect the user's explicit choices on the dimensions below.
**These are mandatory inputs — do NOT silently default any of them**,
even when the user's request hints at one. Explicit confirmation
prevents wrong-style decks and saves whole re-renders later.

Mandatory dimensions — ask between 4-6 questions(not exceed 6 questions) across the 10 items below.
Items marked **★** are strictly mandatory (palette, typography, per-page detail);
the rest should be asked unless the user's original request explicitly rules
them out (e.g. "internal deck, no notes" → skip notes question).

  1. **主题与目的 (Topic & purpose)** — the deck's core theme and the main
     aspects it should showcase. Ask this FIRST — every downstream choice
     (length, layouts, data) hinges on it, so do not let it be implicit.
  2. **目标受众 (Audience & tone)** — who is this for, what register.
  3. **篇幅 (Deck length)** — tight range. like 1–8 / 8–12 / 12以上 slides，you must give user short slides choice.
  4. **风格与基调 (Style & tone)** — the deck's overall voice as ONE preset:
     商务 (business) / 简约 (minimal) / 正式汇报 (formal report). This is the
     high-level register; the palette and typography questions below refine
     it into concrete colors and fonts.
  5. **Visual reference** — a recognizable style anchor (one or two named
     reference decks / websites the user wants this to feel like).
  6. **★ Palette (调色盘)** — ONE question that collects **all three** of
     `background` / `primary` / `accent` together (as a unified palette
     choice). Do NOT split into three separate questions. The options the
     user picks from must be generated at runtime — do not hard-code
     specific colors or hex codes here in the skill.
  7. **Speaker notes (备注讲稿)** — none / short bullet hints / verbatim full script.
  8. **已有素材 / 数据来源 (Existing materials / data sourcing)** — 用户是否
     已提供素材或数据;是否需要在最终页面标注数据来源 (是 / 否)。
  9. **Must include data**
  10. **Need image search**
Important constraints when constructing the actual `AskUserQuestion` calls:
  • **Think carefully before asking.** Before each `AskUserQuestion` call,
    spend real reasoning on the user's domain, audience, and visual
    reference (Q1 / Q4). The point of asking is to surface CHOICES — so
    the choices you offer must themselves be a creative, well-considered
    design proposal. Generic "Light / Dark / Other" is a failure mode.
  • **Each option must be a concrete creative direction**, not a category
    label. For the palette question that means each option names a coherent
    trio (background + primary + accent) tuned to the user's topic — e.g.
    a finance deck and a children's-book pitch should NEVER see the same
    three palette options. Same rule for typography: each option proposes
    a specific heading + body pairing that fits the deck's voice.
  • **Mark your recommendation.** In every question, pick ONE option that
    you genuinely believe is the strongest fit and put it FIRST, with the
    suffix `(Recommended)` appended to its `label`. Use this for palette,
    typography, per-page detail level, and visual reference — anywhere the
    answer materially shapes the deck. Do NOT mark more than one option as
    recommended per question.
  • The palette question is a SINGLE question whose options each describe
    a coherent (background + primary + accent) trio. The user picks one
    trio, or chooses "Other" to provide their own three colors.

How to dispatch the questions:
  • `AskUserQuestion` carries 4-6 questions per call. 
  • Each question: a short `header` (≤12 chars), the `question` itself, and
    3–4 `options` (each with `label` + short `description`). The user can
    always pick "Other" for free-text custom input.
  • Do NOT call any other tool in the same turn as `AskUserQuestion`.
  • Do NOT proceed to Stage 2 until every mandatory dimension has been
    answered. Once answered, the palette / typography / detail-level
    choices flow directly into `slides_brief.json.design` and the per-slide
    `task_brief` in Stage 3 — they MUST match exactly.

═══════════════════════════════════════════════════════════════════════
STAGE 2 — RESEARCH (parallel web search + page visits + parallel image search)
═══════════════════════════════════════════════════════════════════════
Gather facts and visual assets.

Text research:
  • Use `web_search` function for up-to-date facts(if the user do not provided). Batch 2-3 queries across parallel calls in one turn.
      ```bash
    # Simple search query
    z-ai function --name "web_search" --args '{"query": "artificial intelligence","num": 3}'

    # Using short options
    z-ai function -n web_search -a '{"query": "cryptocurrency news", "num": 3, "recency_days": 7}'
    ```


Image assets (THIS IS IMPORTANT):
  • For EVERY slide that needs a photo or illustration, run the `z-ai image-search` CLI (provided by `z-ai-web-dev-sdk`). Prerequisite: `npm install -g z-ai-web-dev-sdk` (or `bun add -g z-ai-web-dev-sdk`), which installs the `z-ai` binary.
  • Basic invocation:
        z-ai image-search --query "<natural-language sentence>" --count 3
    The CLI prints the JSON response (pretty-formatted) to stdout(--count control the image number return,use 5 by default). The query MUST be a natural-language sentence (NOT keywords). The response contains `results[].original_url` (OSS-hosted, embeddable) and `results[].caption`.
  • **Output handling — print-to-stdout only.** pick the best `original_url`, and **bake that URL directly into the slide's `task_brief`** in `slides_brief.json` (see Stage 3). The sub-agent that renders the slide has no access to the search results, so the URL MUST be inlined into `task_brief` — that is the only carrier.
  • Very important!!! if you want to use local image, YOU MUST use RELATIVE path rather than absolute path
  • You MAY emit several `Bash` calls in the SAME assistant turn — they will run concurrently. Prefer batching 3–4 image searches per turn to save wall time.
  • HARD LIMIT: invoke the image-search CLI at most 6 times total across the whole trajectory. Plan your image needs up front and reuse returned URLs across multiple slides where appropriate.
  • If anything goes wrong (e.g. `Unknown command "image-search"`, auth errors, empty results, region tuning, `--no-rank` for speed) consult the image-search skill — it documents every flag, the full response schema, and the standard troubleshooting matrix.

═══════════════════════════════════════════════════════════════════════
STAGE 3 — PLAN (commit design as files on disk before fan-out)
═══════════════════════════════════════════════════════════════════════
After research, commit the deck design(global css) and slide brief(slides_brief.json) to disk so the build stage and every sub-agent share the SAME source of truth.

**Step 3.0 — After `Reasearch` succeeds**, in a SINGLE assistant turn, use `Write` to create:

**`<work_dir>` definition (MANDATORY)**: `<work_dir>` IS the user's `download/` directory itself. Do NOT create an intermediate themed/topic-named subdirectory (e.g. `download/theme_ppt/`, `download/<topic>/`). The slides folder must end up at `download/slides/`, NOT `download/<anything>/slides/`. Every `<work_dir>/...` path in this skill resolves under `download/` directly.
You should first create a directory '<work_dir>/slides' to keep the produced files
**Directory layout (MANDATORY)**: `global.css`, `slides_brief.json`, AND every `slide_NN.html` MUST all live under the SAME single directory `<work_dir>/slides/` (i.e. `download/slides/`). Do NOT place `global.css` or `slides_brief.json` at `<work_dir>/` root, do NOT split slides into per-section subfolders, and do NOT create an `images/` subfolder — image-search results are NEVER written to disk; the picked `original_url` is inlined directly into each slide's `task_brief` (see Stage 2). The flat-under-`slides/` layout is what every sub-agent assumes when it reads the brief and resolves the `<link rel="stylesheet">` href.

Final on-disk layout after Stage 3:
```
<work_dir>/slides/
├── global.css
├── slides_brief.json
├── slide_01.html        ← written in Stage 4 by sub-agents
├── slide_02.html
└── ...
```

1. `<work_dir>/slides/global.css` — the deck-wide stylesheet that EVERY slide will `<link>` into its `<head>`. Bake in:
     • You must use the font size /font style/color in the global.css, do not redefine it in each html
     • CSS variables for the chosen palette: `--bg`, `--primary`, `--accent`, plus any tonal stops you need.
     • `@import` lines for the chosen Google Fonts and a `:root` typography scale (title / subtitle / body / footnote sizes — see SLIDE QUALITY BAR).
     • Reusable utility classes for the slide canvas (e.g. `.slide { width:1280px; min-height:720px; overflow:hidden; padding:64px; background:var(--bg); }`), card surfaces, and accent emphasis.
     • NO per-slide layout CSS — that lives inside each slide's HTML. Keep this file under ~150 lines.
     • Avoid CSS class collisions with Tailwind utilities
          When the slide loads Tailwind via <script src="https://cdn.tailwindcss.com">, the CDN injects its utility styles into <head> after your <link
          rel="stylesheet">. Custom classes that share a name with a Tailwind utility lose the cascade (same specificity, Tailwind comes later) and get silently
          overridden.
          Critical example: Do not name heading classes .h-1 / .h-2 / .h-3. In Tailwind these are height utilities (.h-1 = 4px, .h-2 = 8px, .h-3 = 12px). Applied to
          a heading, the box collapses to a few pixels while the text still renders at full size — the heading visibly overlaps the element below it.
     • Because `global.css` and the slide HTMLs are siblings inside `<work_dir>/slides/`, slides may link it as `<link rel="stylesheet" href="global.css">` (relative). 
     • keep these in mind！！！ Global CSS scope — typography tokens only, no typography classes.Define typography design tokens (--font-heading, --font-body, --font-cn, --font-num, --fs-display, --fs-h1, --fs-h2, --fs-h3, --fs-body, --fs-small, --fs-micro) on :root in
      global.css Do not ship pre-baked typography classes like .h-display / .h-1 / .h-2 / .h-3 / .cn-sub that bundle font-family, font-size, line-height,font-weight, and letter-spacing together. (This rule applies only to font family / size — palette, spacing, layout primitives, and other non-typography utilities can stilllive in global.css as before.) keep these in mind！！！

2. `<work_dir>/slides/slides_brief.json` — the dispatch manifest. Schema:
     ```json
     {
       "design": {
         "title":"(ppt title)",
         "style_name": "...",
         "palette": {"background": "#...", "primary": "#...", "accent": "#..."},
         "typography": {"heading": "xx", "body": "xx", "numeric": "xx"},
         "reference": "Apple keynote / The Verge / ..."
       },
       "global_css_path": "<absolute path to <work_dir>/slides/global.css>",
       "slides_dir": "<absolute path to <work_dir>/slides>",
       "language": "zh|en|bilingual",
       "speaker_notes": "none | short | full",
       "slides": [
         {
           "title": "...",
           "layout": "cover",
           "output_path": "<absolute path to <work_dir>/slides/slide_XX.html>",
           "task_brief": "Self-contained brief — see rules below."
         },
         ...
       ]
     }
     ```
   • Slide ORDER is the order of entries in the `slides` array — no `position` / index field. To reorder a deck, reorder the list.
   • Every slide MUST have `title`, `layout`, `output_path`, `task_brief`.
   • `output_path` is the ABSOLUTE path the slide HTML will be written to. Filenames are arbitrary stable identifiers (e.g. `slide_01.html`, `slide_02.html` at first creation) — they live in the same directory as `global.css` and `slides_brief.json`, but their alphabetical order does NOT define slide order. Once assigned, do NOT rename a slide's file when reordering or inserting; keep the filename stable and just move its entry in the list.
   • `layout` MUST be chosen per page from a coherent catalog (cover, section header, key message, bento grid, split text+image, timeline, stats, comparison, quote, closing, etc.). Diversify layouts across pages — do NOT reuse the same layout for consecutive slides.
   • Section structure for longer decks: once the deck gets long (roughly **≥10 pages**), split the body into 2–5 named chapters with a `section header` page at the start of each. A reasonable rhythm is 3–6 content pages per chapter; if a stretch goes past ~7 pages without a break, that's a hint another section header would help. Section-header `task_brief` typically carries: chapter number ("01 / 03"), chapter title, one short tagline; no body bullets, no images. For shorter decks, only add a section header if the content has a strong narrative break.
   • `task_brief` is the SOLE input the sub-agent will see for that slide — it MUST be self-contained for the renderer. 
       – Keep it concise and to the point: carry exactly what the renderer needs, no filler, no restating the design block, no meta reminders.
       – Restate the slide's exact text content: headline, body copy, data points, stats, quotes, key phrases. Copy verbatim — do not paraphrase loosely.
       – Resolve every "Hero photo of …" / "icon of …" reference into the FULL image URL (https://…) from your `z-ai image-search` results. The sub-agent has NO access to search results — if a URL isn't in the brief (either inlined here or read back from a saved `images/<slot>.json` manifest), the slide can't display the image.
       – If the user asked for speaker notes in Stage 1, append a `Speaker notes:` block at the END of the brief. write the notes request. do NOT write notes verbatim here. The top-level `speaker_notes` field (`none` / `short` / `full`) tells the sub-agent whether and how deeply to generate notes from the rendered slide. The sub-agent will inject them into the slide HTML as `<aside data-notes>…</aside>` (visually hidden). If the user did NOT request notes, omit this block — do not invent notes.
       – Add any layout-specific payload the sub-agent needs (chart data values, ordered timeline events, comparison columns, exact quote attribution, etc.). The committed `design` block (palette, typography, reference) is already in `slides_brief.json`, so do NOT repeat it inside each `task_brief`.
       – Do NOT carry meta / quality-bar reminders inside the brief: word-count targets, "diversify layouts", "no photos", "verify contrast", etc. Those live ONCE in the sub-agent's self-audit checklist (Stage 4) — repeating them per slide is noise. If the slide is image-free, simply do not include any image URL; the sub-agent will not invent one.

═══════════════════════════════════════════════════════════════════════
STAGE 4 — BUILD ( FAN OUT `Agent` sub-agents to actually write the slides)
═══════════════════════════════════════════════════════════════════════
every slide, cover / TOC / body / closing, is committed by a `ppt` sub-agent that calls the `Write` tool itself. The main agent NEVER calls `Write` to commit slide HTML. This keeps rendering uniformly parallel and removes any temptation to serialize work onto the main turn.

  • `Agent(subagent_type="ppt-expert", description=..., prompt=...)` — spawn a sub-agent that writes a CONTIGUOUS RANGE of slides. Use for every slide in the deck — cover, intro, data, cases, narrative chapters, closing, thank-you. Single-slide groups are fine when a section (or the cover) stands alone.

  1. Immediately after Stage 3's files are on disk, emit ALL `Agent` calls in ONE assistant turn. Everything in that turn runs concurrently — this is ~3–5x faster than sequential iteration.

  2. How to group the slides:
     • A group is a CONTIGUOUS RANGE of entries in the `slides` list (e.g. indices 0..4 in JSON order). The sub-agent reads the briefs for those entries from `slides_brief.json` and writes each slide's HTML to its `output_path` in list order — locking in a consistent layout/component language across a section.
     • Slides in DIFFERENT groups run IN PARALLEL.
     • Keep groups small (5–7 slides). Good groups follow narrative sections: cover / intro / data / cases / closing.
     • HARD CAP: at most **3 `Agent` calls per deck total**. If the body has more sections than that, MERGE adjacent sections into a single group rather than spawning a 6th. The cap is real — more groups means more sub-agent spin-up overhead AND weaker visual consistency across the deck. 
  3. Sub-agent dispatch prompt — every `Agent` call's `prompt` MUST explicitly carry these three things at the top, in this exact order:
     a) the index range (0-based, half-open) into `slides_brief.json.slides[]` the sub-agent is responsible for (`start..end`),
     b) the ABSOLUTE path to `slides_brief.json` (`<work_dir>/slides/slides_brief.json`),
     c) the ABSOLUTE path to `global.css` (`<work_dir>/slides/global.css`). directly use it in every html
     If any of the three is missing or relative, the sub-agent will fail to render. Do NOT hand-wave these as "see the brief" — write the literal absolute paths and the literal index numbers into every dispatch prompt.

     Use this exact shape for every `Agent` call's `prompt` field (substitute the bracketed values per group):

     ```
     You are a slide-rendering sub-agent. Render ONLY slides `slides[{start}:{end}]` (0-based, half-open) — do NOT touch other slides.

     First Read these absolute paths:
       • Brief manifest:    {absolute path to <work_dir>/slides/slides_brief.json}
       • Global stylesheet: {absolute path to <work_dir>/slides/global.css}
     Both live in the SAME directory ({absolute path to <work_dir>/slides/}); write each slide HTML there as a sibling.

     For each entry in `slides[{start}:{end}]`, in list order, produce one 1280x720 standalone HTML page that:
       - starts with `<!DOCTYPE html>`, ends with `</html>`, and links `global.css` via `<link rel="stylesheet" href="global.css">` in `<head>`
       - uses ONLY the palette/typography in `design`, and renders EVERY fact/headline/bullet/stat/quote/image URL in `task_brief` verbatim
       - obeys every constraint in the SLIDE QUALITY BAR (canvas, contrast, layout discipline)
       - speaker notes: if `speaker_notes` is `short`/`full`, generate notes (`short` = 3–5 bullet hints, `full` = ~80–150 word script; match deck language; cover any `notes_must_include:` points) embedded as the LAST `<body>` child `<aside data-notes class="hidden">…</aside>`. If `none`, omit it.
     Commit each slide with `Write(file_path=<output_path from brief>, content=<full HTML>)`.

     Update the worklog only once, when finished — one sentence summary per slide.
     ```

     Pass `subagent_type: ppt-expert`. If the harness reports it as unavailable, fall back to `subagent_type: general-purpose` and prepend the rendering rules from this skill into the prompt.

  4. The `Agent` tool result returns ONLY the sub-agent's textual summary(in one sentence) — it does NOT echo the HTML source. To inspect a generated slide, call `Read(file_path=<output_path>)`.

  5. Sub-agent slide HTML rules: must start with `<!DOCTYPE html>`, end with `</html>`, link `global.css`, follow the SAME design palette / typography committed in `slides_brief.json`, and obey every constraint in the SLIDE QUALITY BAR. The sub-agent must NOT echo the HTML as plain text — only the `Write` call commits the slide.


═══════════════════════════════════════════════════════════════════════
Only when user requested a pptx file，if user not request，directly give a summary and end the task — how to EXPORT TO PPTX:
═══════════════════════════════════════════════════════════════════════
Convert `<work_dir>/slides/` into ONE `.pptx` via `batch_html2pptx.js`.

The converter walks sorted filename order. Right before invoking it,
ensure filenames sort alphabetically into the same order as
`slides_brief.json.slides[]`. If editing rounds left them out of order,
rename to `slide_{NN:02d}.html` matching list index AND update each
entry's `output_path`. This is the ONLY step that renames files.
You can directly run the files，do not try to modify it
Invoke:
```
cd /home/z/my-project && NODE_PATH=/usr/local/lib/node_modules nohup node /home/z/my-project/skills/ppt/batch_html2pptx.js /home/z/my-project/download/slides /home/z/my-project/download/xx.pptx
```

  • Arg 1: slides directory. Arg 2 (optional): output path; defaults to
    `<work_dir>/<basename(work_dir)>.pptx`.
  • `NODE_PATH` is required so `pptxgenjs` / `playwright` / `sharp` resolve.
  • Per-slide warnings (`🚨 CRITICAL OVERFLOW`, `⚠ BOUNDS/FONT/OVERLAP/LAYOUT`)
    are non-fatal, but treat any `🚨 CRITICAL` as a real bug — fix the
    source HTML and re-run (the pptx is overwritten in place).

After export: `ls -lh <path>` to confirm, then report the `.pptx` path
(and source slide HTML paths) to the user.

═══════════════════════════════════════════════════════════════════════
MULTI-ROUND HTML EDITING — keep `slides_brief.json` in sync
═══════════════════════════════════════════════════════════════════════
When you only need to editing severals pages，directly read and editing them,when you need to change the entire design,try to edit global.css first
Very inportant!: Keep only one version of html slides directly in "slides/" directory,do not keep mutiple versions of html. and there is only one version of slides.
Very inportant!: when deleting or adding pages,first editing slides_brief.json first
`slides_brief.json` is the single source of truth for the deck's
structure. Slide ORDER is the order of entries in `slides[]` — there is
no `position` / index field, so adding / removing / reordering NEVER
requires renumbering. Whenever a follow-up edit ADDS or REMOVES a slide,
update the brief in the SAME turn — never let on-disk slides and the
brief diverge.

  • Add a page → create the HTML file (any stable filename like
    `slide_NEW1.html`) AND insert a matching entry into
    `slides_brief.json.slides[]` at the desired position in the list
    (`title`, `layout`, `output_path`, self-contained `task_brief`).
  • Remove a page → delete the file AND remove its entry from the list.
  • Reorder → just move entries within `slides[]`. Do NOT rename files.

In-place content tweaks only need a brief update if the change is large
enough that the old `task_brief` no longer describes the slide
(different headline, new image URL, layout switched). Typo fixes do not.

═══════════════════════════════════════════════════════════════════════
SLIDE QUALITY BAR (applies to every page)
═══════════════════════════════════════════════════════════════════════
  • Exact canvas: 1280 × 720, `overflow-hidden`. No scroll.
  • Real content density: every page carries 60-120 words of substantive text — no placeholders, no lorem ipsum, no "insert data here".
  • Exactly the chosen palette on every page. Background/primary/accent must match `slides_brief.json.design.palette`.
  • Every text color on every background must pass WCAG AA (4.5:1 contrast).
  • Use TailwindCSS via CDN (`<script src="https://cdn.tailwindcss.com"></script>`) and link the deck-wide `global.css`. Use Google Fonts for typography.
  • Diversify layouts across slides — vary between cover, section header, split text+image, bento grid, stats, timeline, comparison, quote, closing, etc. Never repeat the same layout back-to-back.
  • Never fabricate image URLs. Only use URLs that came back from the `z-ai image-search` CLI.
  • Include icons (Material Icons via `<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">` and `<i class="material-icons">name</i>`). No `<script>` icon loaders.
  • Numbers, dates, and technical terms render in the proper numeric font per typography guide.
  • No graphical timelines, no SVG/connector flowcharts, no code-drawn maps, no base64 images, no Reveal.js.
  • Headers and footers are OPTIONAL, not mandatory. Add a page header/footer (deck title, page number, brand mark, footnote bar) only when user asked !!!

═══════════════════════════════════════════════════════════════════════
GENERAL RULES
═══════════════════════════════════════════════════════════════════════
  • Batch aggressively. Prefer 1 turn with 5 tool calls over 5 turns with 1 tool call each.
  • Parallelism is free — `WebSearch`, `WebFetch`, `Bash` (image-search), and the fan-out of `Agent` sub-agents all run concurrently when emitted in the same turn; use it.
  • Always respond in the user's language.

## Editing an existing PowerPoint presentation（pptx）

Pick the approach by what you're editing:

- **Approach A — `python-pptx` script** — preferred for text replacement, deleting/reordering slides, and any edit that should preserve fonts/colors/layout. Simpler and safer than raw XML for content swaps.
- **Approach B — raw OOXML** — required for animations, transitions, comments, speaker notes XML, theme tweaks, custom layout edits — anything `python-pptx` can't reach.

### Approach A — `python-pptx` text replacement (preferred for text edits)

**Workflow**

1. **Inventory the deck** — walk every slide, recurse into GROUP shapes (`shape_type == 6`), `print(repr(para.text))`. Use the inventory as the source of truth for replacement keys; rendered text often contains hidden chars that won't survive copy-paste.

2. **Helpers** — keep the build script short:

   ```python
   from pptx import Presentation
   from pptx.enum.text import MSO_AUTO_SIZE
   from pptx.oxml.ns import qn
   from pptx.util import Emu, Pt

   def iter_text_frames(shapes):
       for s in shapes:
           if s.shape_type == 6:                 # GROUP → recurse
               yield from iter_text_frames(s.shapes)
           elif s.has_text_frame:
               yield s, s.text_frame

   def _norm(s):                                  # strip soft breaks before matching
       return s.replace("\x0b", "").replace("\r", "").strip()

   def replace_in_paragraph(p, new_text):         # first-run replace preserves formatting
       runs = p.runs
       if not runs:
           p.add_run().text = new_text; return
       runs[0].text = new_text
       for r in runs[1:]:
           r._r.getparent().remove(r._r)

   def apply_replacements(tf, mapping):           # full-frame match, then per-paragraph
       m = {_norm(k): v for k, v in mapping.items()}
       full = "\n".join(p.text for p in tf.paragraphs)
       if _norm(full) in m:
           parts = m[_norm(full)].split("\n")
           for i, p in enumerate(tf.paragraphs):
               replace_in_paragraph(p, parts[i] if i < len(parts) else "")
           return
       for p in tf.paragraphs:
           if _norm(p.text) in m:
               replace_in_paragraph(p, m[_norm(p.text)])

   def delete_slide(prs, idx):                    # call high-index first
       sld = list(prs.slides._sldIdLst)[idx]
       prs.part.drop_rel(sld.get(qn("r:id")))
       prs.slides._sldIdLst.remove(sld)
   ```



**Budget every shape BEFORE generating replacement text (do this first)**

Most overflow bugs come from generating copy without knowing the target box's capacity. Before drafting any replacement, walk the deck once and emit a capacity manifest — then feed it to the content step as a hard constraint.

For each text-bearing shape collect: `slide_idx, shape_id, w_cm, h_cm, font_pt, orig_text, orig_len`. Derive:

- `chars_per_line ≈ w_cm / (font_pt × 0.014)` for CJK; multiply by ~2 for Latin. Mixed text: weight by character class.
- `lines ≈ h_cm / (font_pt × 0.0185)` (line-height ≈ 1.3).
- `budget = min(chars_per_line × lines, orig_len × 1.1)`. The template designer already tuned `orig_len` for readability — treat it as the ceiling, not a starting point.
- `role = "label"` if `h_cm < 1.5` OR `orig_len ≤ 8` OR `font_pt ≥ 20`; else `"body"`.

Rules the generation step MUST obey:
- **Label boxes**: short phrase only. No full sentences, no trailing punctuation, no "term + explanation" expansion. Hard cap = `max(orig_len, 8)`. SWOT tiles, timeline tags, KPI labels all fall here.
- **Body boxes**: stay within `budget`. Font size is inherited from the template; shrinking is a last resort, not plan A.
- If the content is genuinely longer and the layout permits, **grow the box itself** (`widen_to_fit(shape, Emu(...))` — see below) rather than shrinking the font. Check first that `left + width` won't collide with the next shape.

**Handling long replacement / unwanted wrapping after replacement**

When a longer replacement wraps to a new line, apply remedies in this order (cheapest first):

```python
def widen_to_fit(shape, max_grow_emu=Emu(0)):
    """Let PowerPoint size the shape to its text. Pass max_grow_emu>0 to also
    grow the explicit width (centered on the original position) before sizing."""
    if max_grow_emu:
        shape.left -= max_grow_emu // 2
        shape.width += max_grow_emu
    shape.text_frame.word_wrap = True
    shape.text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT

def shrink_text_to_fit(shape):
    """Keep the box fixed; let PowerPoint shrink the font to fit."""
    shape.text_frame.word_wrap = True
    shape.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
```

1. **Budget first (preferred).** Check `shape.width` × `font_size` from inventory and trim the replacement so it fits the original visual budget. Numeric badges / small label boxes (`width ≤ 0.7"`, `font_size ≥ 16pt`) hold ~3–4 chars max.
2. **Widen the shape** with `widen_to_fit(shape, Emu(...))` when the content is genuinely longer and there's free space next to it. Always check the shape isn't going to collide with a neighbor first (compare `left+width` against the next shape's `left`).
3. **Shrink the font** with `shrink_text_to_fit(shape)` only for tight-layout boxes (table cells, numeric badges) where widening would break the grid. Last resort — it visibly breaks the typographic rhythm.

Skip `word_wrap = False`: it makes text overflow the box invisibly in PowerPoint and looks broken when exported.

**Critical gotchas**

- **Soft line breaks (`\x0b`)** silently break exact-match. Always `_norm()` both keys and lookups.
- **GROUP shapes** (`shape_type == 6`) hide text frames — recurse.
- **First-run replace** preserves formatting; `paragraph.text = ...` destroys it.
- **Short tokens collide.** `"01"`, `"%"`, `"18"` recur across slides — keep identity mappings or scope per slide index, never global cross-mappings like `"18": "12"`.
- **Delete slides high-index first** — deleting index 5 first shifts every later index down by one.







## Code Style Guidelines
**IMPORTANT**: When generating code for PPTX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

## Dependencies

Required dependencies (should already be installed):

- **markitdown**: `pip install "markitdown[pptx]"` (text extraction)
- **pptxgenjs**: `npm install -g pptxgenjs` (creating presentations)
- **playwright**: `npm install -g playwright@1.50.0` (HTML rendering)
- **react-icons**: `npm install -g react-icons react react-dom` (icons)
- **sharp**: `npm install -g sharp` (SVG rasterization and image processing)
- **LibreOffice**: `sudo apt-get install libreoffice` (PDF conversion)
- **Poppler**: `sudo apt-get install poppler-utils` (pdftoppm)
- **defusedxml**: `pip install defusedxml` (secure XML parsing)
