---
name: Content Page Skill
description: Design publishing-ready HTML content pages for existing articles, reports, newsletters, guides, case studies, release notes, public-account articles, and editorial reading experiences.
mode: artifact
platform: responsive-web
scenario: content-page
preview:
  type: html
default_for:
  - article page
  - editorial page
  - newsletter
  - memo
  - WeChat article
  - public account article
  - long-form content page
  - report page
  - whitepaper
  - guide
  - tutorial article
  - case study
  - release note
  - changelog article
  - reading page
  - 内容页
  - 文章页
  - 长文页面
  - 公众号文章
  - 公众号长文
  - 报告页面
  - 白皮书页面
  - 案例拆解
  - 发布说明
fidelity: high
---

# Content Page Skill

Design an editorial reading page for content that already exists or is partially provided.

This skill is closer to **editorial layout / graphic design** than product UI. Its job is to turn existing content into a readable, publishable, well-paced HTML page through hierarchy, rhythm, typography, evidence treatment, and layout — not to invent the article.

## Route elsewhere if

- the primary goal is conversion / signup / sales → `landing-page.md`
- the user wants exploration, filters, animated data, or interactive explanation as the main experience → `info-interactive.md`
- the user wants a single-task calculator / generator / checker → `web-tool.md`
- the user wants a product interface, dashboard, or app flow → `prototype.md`
- the user wants a slide presentation → `deck.md`
- the final medium is social images, covers, long-image cards, or product brief images → `social-card.md`

If a content page also needs a social cover, route the reading page here and the cover/card to `social-card.md`; do not force both into one artifact.

---

## Core Principle: Content Is Source of Truth

Assume the user has content unless they explicitly ask for writing.

Do not invent claims, examples, statistics, quotes, sections, conclusions, sources, charts, or case details to make the page feel fuller.

The work is to transform available content into a designed publishing artifact:

- clarify hierarchy;
- group related material;
- surface key points;
- create reading rhythm;
- design evidence, figures, quotes, notes, and references;
- preserve factual meaning;
- mark missing material as placeholder instead of fabricating it.

If the content is too thin, design a clean structure and ask for the missing material. Do not pad with generic paragraphs.

---

## What Makes a Content Page Succeed

A content page succeeds when the reader can enter quickly, stay oriented, and finish with a clear takeaway.

The failure mode is not ugliness. The failure mode is a page that is technically readable but editorially flat: title, subtitle, blocks of text, a few cards, no rhythm, no reason to keep reading.

A strong content page has:

- **a clear reading promise** — why this is worth reading now;
- **a visible editorial structure** — the reader can tell where they are and what kind of section they are in;
- **controlled text measure** — body text never stretches across the screen;
- **rhythm** — fast scan zones, slow reading zones, evidence breaks, and pauses;
- **evidence treatment** — quotes, data, figures, sources, and examples are designed, not dumped;
- **a deliberate ending** — conclusion, implication, action, appendix, or related reading.

---

## Content Type Detection

Before designing, infer the content type from the provided material. Do not force every content page into the same article layout.

| Content type | Use when | Layout direction |
|---|---|---|
| Article / Essay | one argument, opinion, explanation, or reflection | strong title, readable body, section breaks, pull quotes |
| Editorial Feature | narrative, culture, brand story, interview, field notes | immersive opening, image/quote rhythm, slower pace |
| Report / Whitepaper | findings, research, industry analysis, structured sections | executive summary, section index, data cards, figures, source notes |
| Newsletter / Memo | update, briefing, internal/external note | compact hierarchy, skimmable blocks, clear next step |
| Release Note / Changelog Article | product updates, version announcement, feature summary | grouped updates, before/after, screenshots, migration/action notes |
| Guide / Resource | how-to, checklist, tutorial, reference material | steps, examples, callouts, warnings, checklist ending |
| Case Study | background, challenge, solution, result, reflection | case spine, evidence blocks, before/after, outcome caveats |
| Public Account / WeChat Article | mobile-first Chinese reading | single-column rhythm, strong title breaking, paragraph breathing, image captions |

If the content combines multiple types, choose the dominant one and borrow only the necessary secondary devices.

---

## Editorial Layout Principles

### 1. Start with the text block

Design the reading column before designing decoration.

- Body text must have a controlled measure — but bounded on *both* sides. Target roughly **30–45 Chinese characters / 60–75 Latin characters per line**, i.e. a reading column around **wide: clamp(0, ~42em, ~760px)**. Don't run full-width across a desktop viewport, and equally don't over-narrow it into a cramped ~480px ribbon with huge empty margins. If the layout has no side rail/figures, the column can sit toward the upper end (~46em); a too-narrow column is as much a failure as a full-width one.
- Long-form text should have generous line-height and stable paragraph rhythm.
- Margins should frame and pace the reading, not just center a thin column in a sea of white.
- Do not use the whole viewport width just because HTML allows it — but the fix is a *bounded* measure, not an arbitrarily narrow one.

### 2. Hierarchy is not only font size

Build hierarchy through a system:

- title, deck/subtitle, metadata, intro, section heading, subheading, body, quote, note, caption, source;
- section spacing and white space;
- rules, dividers, labels, side notes, figure captions, callout blocks;
- contrast between scan areas and slow-reading areas.

Avoid the generic hierarchy of “large H1 + medium H2 + plain paragraphs” with no editorial devices.

A page that is only title + paragraphs + a few cards is the flat failure mode, even if it reads fine. Commit to visible rhythm: alternate dense reading zones with lighter pause zones (quote, figure, data insert, divider), and pick at least one editorial device below so the page has a memory point — don't ship an even, paragraph-after-paragraph wall. For Chinese content specifically, actively use the **表现力手法** in `horizontal-craft/chinese-typography.md` (oversized title contrast, weight contrast, drop-cap/opening ritual, vertical-in-horizontal title/quote, pulled-out 金句 blocks) so the typography itself carries character — not just correct, but expressive. Keep it in service of reading, not decoration.

### 3. Choose one editorial device

Use one primary device to give the page memory. Do not use all devices at once.

Good devices:

- pull quote;
- side note / margin note;
- evidence card;
- source appendix;
- timeline;
- figure strip;
- glossary;
- case card;
- data insert;
- chapter index;
- key-takeaway rail.

The device must come from the content. Do not add a timeline if there is no sequence; do not add a data card if there is no real data.

### 4. Figures and images must carry meaning

Images, charts, diagrams, and screenshots are not filler.

- Every figure needs a reason and usually a caption.
- Screenshots should be legible and framed deliberately.
- Data visualizations need title, unit, label, and source/placeholder status.
- Avoid generic stock imagery that does not add evidence, atmosphere, or context.

### 5. Ending is part of the design

Do not finish every page with a generic CTA.

Choose the ending based on content:

- conclusion;
- implication;
- next action;
- open question;
- checklist;
- source appendix;
- related reading;
- author note;
- changelog / version note.

---

## Reading Rhythm

Design where the reader speeds up and where they slow down.

A good content page usually contains:

1. **Entry** — title, subtitle/deck, metadata, and reading promise.
2. **Orientation** — summary, table of contents, key finding, or context block.
3. **Body rhythm** — sections with varied density, not one long wall of text.
4. **Pause points** — quote, figure, note, data insert, example, or divider.
5. **Evidence zones** — sources, charts, examples, screenshots, case blocks.
6. **Transition cues** — section breaks that tell the reader what changed.
7. **Ending beat** — final takeaway, implication, or appendix.

Opening moves should be extracted from the content, not invented:

- thesis first;
- scene first;
- data first;
- question first;
- quote first;
- object/screenshot first;
- context first.

If no strong opening is evident, use a clear thesis/context opening rather than fabricating drama.

---

## Layout Models

Choose one model and commit.

### Classic Reading Page

Use for essays, explanations, opinion pieces, and public-account style articles.

- single strong text column;
- restrained metadata;
- clear section headings;
- occasional pull quote or figure;
- calm ending.

### Editorial Feature

Use for narrative, culture, brand story, interview, or field notes.

- stronger opening treatment;
- image / quote / text rhythm;
- more atmospheric spacing;
- slower reading pace.

### Report / Dossier

Use for structured analysis, whitepapers, industry reports, or research summaries.

- executive summary;
- section index;
- data cards / figure blocks;
- source notes;
- appendix or methodology area when relevant.

### Newsletter / Brief

Use for updates, memos, weekly notes, and product briefings that are meant to be scanned.

- compact intro;
- labeled sections;
- clear “what changed / why it matters / next step” structure;
- lighter visuals.

### Guide / Resource

Use for tutorials, how-tos, references, checklists, or resource pages.

- step blocks;
- examples;
- warnings / tips;
- final checklist;
- stable navigation if long.

### Public Account / Mobile Article

Use for Chinese mobile reading and WeChat-like publishing.

- single-column mobile-first body;
- strong title line breaks;
- short paragraph rhythm;
- image captions and section dividers;
- avoid dense desktop-style sidebars.

---

## Typography And Grid

For Chinese content, apply `horizontal-craft/chinese-typography.md`.

Escalate to deep references when needed:

- `horizontal-craft/reference/text-detail.md` — body size, line-height, paragraph rhythm, long-form readability.
- `horizontal-craft/reference/title-and-breaking.md` — headlines, decks, section titles, Chinese line breaks.
- `horizontal-craft/reference/punctuation.md` — punctuation-heavy Chinese, quotations, lists, notes, captions.
- `horizontal-craft/reference/grid-system.md` — report, dossier, multi-column, long image, or complex editorial layout.
- `horizontal-craft/reference/fonts.md` — only when font choice materially affects the editorial tone, e.g. literary, academic, public-document, magazine, poster-like title, or brand-specific typography.

Do not read `fonts.md` for every Chinese article. Most web content can use a safe system font stack unless the typography itself is part of the visual direction.

---

## HTML Structure

Keep the page editable and semantically clear.

Recommended markers:

```html
<main data-content-page="topic-name" data-content-type="report">
  <header data-content-section="entry">…</header>
  <section data-content-section="summary">…</section>
  <section data-content-section="chapter" id="chapter-1">…</section>
  <aside data-editorial-device="pull-quote">…</aside>
  <figure data-figure="chart" data-source-status="provided|placeholder">…</figure>
  <section data-content-section="appendix">…</section>
</main>
```

Rules:

- preserve real content structure;
- keep headings semantic;
- mark placeholder areas clearly;
- keep figures, captions, notes, sources, and callouts identifiable;
- avoid opaque generated blobs that make selected-region edits impossible.

---

## References, Load Only When Triggered

Core reading/layout references:

- `horizontal-craft/chinese-typography.md` → substantial Chinese text.
- `horizontal-craft/reference/text-detail.md` → long-form reading, dense body copy, report/article rhythm.
- `horizontal-craft/reference/title-and-breaking.md` → strong title, Chinese headline, public-account title, editorial section headings.
- `horizontal-craft/reference/punctuation.md` → punctuation-heavy Chinese, quotes, citations, notes.
- `horizontal-craft/reference/grid-system.md` → report/dossier/multi-column/long-image layout.
- `horizontal-craft/reference/fonts.md` → font choice materially affects tone.

Supporting references:

- `horizontal-craft/color.md` → no design system or color direction is vague.
- `horizontal-craft/data-integrity.md` → data, charts, metrics, rankings, percentages, research claims.
- `horizontal-craft/link-and-proof.md` → citations, links, client names, testimonials, sources, proof claims.
- `horizontal-craft/visual-explanation.md` → diagrams, timelines, maps, process figures, comparison graphics, explanatory charts.
- `horizontal-craft/icon-system.md` → icons, pictograms, labels, repeated symbolic marks.
- `design-system-reference.md` → brand/style/template/DESIGN.md reference exists.

Normally avoid:

- `state-coverage.md` unless the page contains meaningful interactive states.
- `form-validation.md` unless there are forms.
- `animation-discipline.md` unless motion is requested or used.
- `technique-library.md` unless advanced visualization or interaction is truly necessary.

---

## Decision Sequence

1. Inventory the provided content: title, sections, claims, evidence, figures, sources, missing parts.
2. Extract the editorial stance from the content: explainer, report, memo, guide, case, release note, essay, public-account article, etc.
3. Choose the reading promise: what should the reader understand or take away?
4. Select one layout model and one editorial device.
5. Design the text block, hierarchy, rhythm, figures, and ending.
6. Build the HTML while preserving content truth and marking placeholders.
7. Run the final gate.

---

## Final Gate

Run `quality-gate.md` as the shared blocking check. This skill adds content-page-specific checks:

- content meaning preserved; no invented claims, examples, quotes, data, or conclusions;
- placeholder material clearly marked;
- body text measure and line-height support real reading;
- hierarchy uses more than font size alone;
- long pages have visible section rhythm and orientation;
- figures/images/charts have a reason, caption, and source/placeholder status where relevant;
- links, citations, and proof claims are real or clearly marked;
- Chinese text applies `horizontal-craft/chinese-typography.md` when substantial;
- the page does not look like a landing page, slide deck, or social card unless explicitly hybrid;
- the ending matches the content instead of defaulting to a generic CTA.

---

## Handoff

Use the standard Design Skill delivery, export, and version-management flow.

If requested, define named export targets for:

- PDF / print-style article;
- WeChat/public-account publishing package;
- long image export;
- source appendix;
- downloadable report assets.

If the user also needs a social cover, carousel, or summary image, route that output to `social-card.md` rather than forcing it into the reading page.
