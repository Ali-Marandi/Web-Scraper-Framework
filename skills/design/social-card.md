---
name: social-card
description: |
  Create fixed-canvas social-distribution visual artifacts delivered as HTML-to-image outputs: Xiaohongshu/Rednote covers and carousel cards, WeChat official account cover pairs, Douyin/video covers, social posters, product brief cards, product update images, launch/feature announcement graphics, report summary cards, knowledge cards, screenshot explainers, quote cards, data cards, hiring/event posters, and mobile-first long images.
type: artifact-skill
output_target: html-to-image
primary_when:
  - social card
  - 小红书封面
  - 小红书图文
  - 小红书卡片
  - Rednote carousel
  - 微信公众号封面
  - 视频号封面
  - 抖音封面
  - 社媒海报
  - 知识卡片
  - 长图
  - 截图讲解卡
  - quote card
  - product brief card
  - product update card
  - product launch card
  - feature announcement card
  - release note image
  - company update card
  - event announcement image
  - hiring poster
  - report summary card
  - data summary card
  - 社媒产品简报
  - 产品更新图
  - 功能发布图
  - 版本说明图
  - 产品发布图
  - 活动预告图
  - 招聘海报
  - 公司动态图
  - 报告摘要图
  - 数据摘要图
avoid_when:
  - full slide deck / PPT / presentation
  - long-form webpage meant for scrolling and reading in-browser
  - pure photo editing with no layout or information design
  - dashboard / web app / operational prototype
---

# Social Card Artifact Skill

Use this skill for **fixed-canvas social-distribution visuals** that are usually authored in HTML/CSS and exported as images.

The routing signal is not only the platform name. Use this skill when the final medium is a social-ready image or image sequence, even if the content is a product brief, product update, report summary, launch announcement, recruiting card, or event notice.

This skill replaces the narrower `xiaohongshu-card.md`. Xiaohongshu is now one platform preset inside a broader social-card artifact skill.

## Core Principle

A social card is a fixed-canvas communication artifact for social distribution. It may be a cover, carousel, announcement, product brief, report summary, screenshot explainer, data card, recruiting poster, event notice, quote card, or long image. The final medium is image, even when authored as HTML.

A social card is not a mini article and not a poster filled with text.

Each card must have one clear job:

- make the viewer stop;
- explain one point;
- show one piece of evidence;
- compare two things;
- guide one step;
- summarize one conclusion.

Do not squeeze the full article into images. The card set is a **visual argument outline**. Nuance belongs in caption/body text, not in every card.

## Internal Brief Before Design

Before choosing layouts, silently resolve:

```yaml
social_card_brief:
  platform: xiaohongshu | wechat | douyin | generic-social | unknown
  output_target: html-to-image
  canvas_preset: from canvas-and-device.md
  card_count: single | cover-plus-pages | cover-pair | long-image
  audience:
  content_goal: stop | explain | persuade | teach | summarize | compare | prove | announce | update | brief | recruit | share
  visual_intent:
    mode:
    density:
    title_attitude:
    imagery_strategy:
  assets:
    photos:
    screenshots:
    logos:
    data:
  constraints:
```

Do not show this YAML to the user unless they ask for routing/debug details.

Ask at most one clarification question, and only when the missing answer changes platform, canvas size, or whether image assets are required.

## References (load only when triggered)

This is the artifact-specific reference contract for social-card work. It should be read after the primary route selects `social-card.md` and before generation.

Always read:

- `canvas-and-device.md` for platform sizes, fixed-canvas presets, safe areas, and export intent.
- `horizontal-craft/chinese-typography.md` when the output contains Chinese.

Read conditionally:

- `horizontal-craft/reference/title-and-breaking.md` for covers, large titles, posters, or cards where title breaking is visually dominant.
- `horizontal-craft/reference/fonts.md` when font choice materially affects the visual direction: poster title, brand card, editorial report card, classical/literary card, public-document style, industrial/tech title, or typography-led design.
- `horizontal-craft/color.md` when no design system is provided or the color direction is vague.
- `horizontal-craft/icon-system.md` when functional icons, badges, status marks, or repeated symbolic markers are used.
- `horizontal-craft/data-integrity.md` for numbers, charts, rankings, market size, ROI, benchmark, dashboard screenshots, or KPI cards.
- `horizontal-craft/link-and-proof.md` for customer logos, citations, source claims, awards, press mentions, or external proof.
- `horizontal-craft/anti-ai-slop.md` before final review, not as the primary creative director.

Do not read every reference by default. Read only what the card task needs.

## Platform Presets

Platform determines canvas and safe-area behavior. It does not determine the visual style by itself.

### Xiaohongshu / Rednote

Use for:

- cover image;
- carousel card set;
- knowledge card sequence;
- recommendation / review / tutorial / checklist;
- screenshot explainer.

Rules:

- Prefer 3:4 portrait unless the user asks for square or a known alternative.
- Cover must communicate the value within one glance.
- Use one idea per page.
- Avoid tiny body copy; cards are read on phones.
- Use 4–8 pages for most carousel posts when the user asks for a set.
- End with a summary, checklist, key takeaway, or share/save reason when useful.

### WeChat Official Account Cover Pair

Use when the user asks for 微信公众号封面, 公众号首图, article cover pair, or both main + square cover.

Rules:

- Generate a coordinated pair: one wide main cover and one square cover.
- The wide cover can carry the longer title, subtitle, and visual relation.
- The square cover must use a compressed short title. Do not squeeze the full title into the square.
- Build both covers as related but separately composed designs, not as blind crops.

### Douyin / Video / Video Account Cover

Use when the user asks for 抖音封面, 视频号封面, short-video cover, or vertical video thumbnail.

Rules:

- Title must survive thumbnail scale.
- Keep important text away from interface overlay zones where applicable.
- Use stronger focal contrast than article cards.
- Avoid long subtitles.

### Generic Social Poster / Card

Use when platform is not fixed.

Rules:

- Infer a canvas preset from the output target, but avoid pretending it is platform-specific.
- If the platform changes later, recompute composition rather than mechanically resizing.

## Route Boundaries

Route by final medium, not topic keyword alone.

- If the user wants a full web landing page, use `landing-page.md`.
- If the user wants a slide presentation, use `deck.md`.
- If the user wants a product interface prototype, use `prototype.md`.
- If the user wants a social-distribution image, image sequence, cover, poster, product brief image, update card, or long image, use `social-card.md`.
- If the user says “产品简报 / 周报 / 报告摘要 / 发布图” without specifying slides or webpage, prefer `social-card.md` when the deliverable is clearly image-first.

## Content Role Planning

Plan pages by role before designing. Repetition is the main failure mode.

Common roles:

- **Hook Cover** — stop the viewer with a sharp title and one dominant visual.
- **Problem Scene** — show the pain, mistake, or tension.
- **Misconception vs Reality** — contrast what people think with what is true.
- **Checklist** — scannable criteria or action list.
- **Comparison** — before/after, A/B, old/new, tool/tool, plan/plan.
- **Step Flow** — a process, workflow, route, or sequence.
- **Screenshot Evidence** — product/UI/code screenshot with clear framing and annotation.
- **Data/KPI Card** — one metric family, trend, or ranking.
- **Product Brief** — one product/update/message compressed into a visual brief.
- **Feature Announcement** — one feature, one benefit, one proof point, screenshot, or CTA.
- **Release Note** — version/update summary with clear hierarchy.
- **Event / Campaign** — time, offer, action, and visual hook.
- **Hiring / Recruiting** — role, reason to join, requirements, and CTA.
- **Report Summary** — one finding or section from a longer report.
- **Company Update** — milestone, partnership, launch, funding, community, or announcement.
- **Quote / Thesis** — one large sentence as the page subject.
- **Image-Led Cover** — strong photo first, restrained title.
- **Map / Spatial Card** — route, places, district, store map, walking guide.
- **Summary Card** — final takeaway, three-point recap, or save/share reason.

Hard rule: **one card = one role**. If a card tries to be cover + explanation + proof + CTA, split it.

## Style Mode Selection

Pick one visual mode per card set. Do not mix unrelated systems inside the same package.

### Editorial Card

Use when the content should feel:

- magazine-like;
- literary / reflective;
- lifestyle / travel / culture;
- slow, considered, tactile;
- quote-led or image-led.

Typical signals:

- paper or ink atmosphere;
- serif/Songti/Mingcho title attitude;
- large photo well;
- marginal notes;
- pull quote;
- restrained palette;
- subtle texture.

Do not use it for high-density tool dashboards, KPI-heavy posts, or sharp product release cards unless the user asks for editorial contrast.

### Swiss Card

Use when the content should feel:

- structured;
- systemized;
- data-led;
- product/release focused;
- workplace / AI tools / methods / comparison;
- engineered and decisive.

Typical signals:

- strong grid;
- numbered statements;
- one accent color;
- hairline rules;
- KPI blocks;
- table/matrix structure;
- left alignment;
- high contrast.

Do not make Swiss cards heavy and bold by default. Swiss display titles can be large, but the system should remain precise.

### Product Brief / Product Update

Use when the content is a product brief, feature launch, release note, company update, report summary, campaign card, or recruiting/social announcement.

Default treatment:

- For feature updates, release notes, tool explainers, and product briefs, start from Swiss Card or Screenshot Explainer logic.
- For data-backed updates or report summaries, start from Data/KPI Card logic.
- For brand story, founder note, community update, lifestyle campaign, or culture/recruiting story, Editorial Card may be stronger.
- Product cards should clarify one message first, then support it with screenshot, proof, metric, date, or action.
- Do not make product announcements look like full landing pages compressed into one image.

### Image-Led Card

Use when the user supplies a strong photo, product image, or scene image that should carry emotion.

Rules:

- Let one image dominate.
- Use title placement based on safe zones.
- Do not place text over faces, hands, product UI, or key objects.
- Do not rely on a full-canvas black gradient to rescue a bad image.

### Screenshot Explainer

Use for:

- app / web / code / dashboard screenshots;
- AI tool tutorials;
- product update posts;
- workflow explanation.

Rules:

- Do not paste screenshots naked.
- Use a frame, browser/device chrome, stage, zoom, callout, crop, or annotation.
- Screenshot readability beats decorative layout.
- If screenshot text matters, enlarge the screenshot and reduce surrounding copy.

### Data / KPI Card

Use when numbers are the story.

Rules:

- One metric family per card.
- Explain the metric context; do not show fake precision.
- Mark demo/placeholder data clearly.
- Avoid decorative charts with no readable axis, label, or conclusion.

### Map / Travel Card

Use only when spatial relationships matter: route, neighborhood, stores, walking plan, location comparison.

Rules:

- Use a real static map when real geography matters.
- Use schematic map only for conceptual relations.
- Do not use a live JS map inside the exported image.

## Layout Recipe Selection

Use layout recipes as grammar, not as templates to copy.

Map content intent to layout family:

| Intent | Good layout family |
|---|---|
| Strong cover hook | Issue cover, hero title, image-led cover, hero question |
| One big thesis | Pull quote, statement page, manifesto card |
| Many criteria | Checklist, ledger, matrix |
| Step-by-step | Vertical pipeline, numbered flow, process cards |
| A/B comparison | Two-column comparison, before/after split, difference table |
| Product/UI proof | Screenshot frame, browser/device mock, zoom annotation |
| Product brief / update | Feature brief, release note stack, screenshot + benefit, announcement card |
| Event / hiring / campaign | Poster hierarchy, date-role-action block, campaign hero |
| Report summary | Finding card, executive brief, KPI + takeaway, insight stack |
| Data summary | KPI tower, bar comparison, ranking list, single-chart card |
| Travel/spatial | Map block, route list, field-note photo |
| Lifestyle/photos | Image-led cover, photo well, field-note page |
| Closing | Summary, remember-three, final quote, save card |

Do not reuse the same layout family across every page. A good carousel has rhythm.

## Cover Title Compression

Covers need short, visual titles.

Rules:

- Prefer 4–14 Chinese characters when possible.
- Preserve the core object and strongest action.
- Remove explanations, long modifiers, background clauses, and vague hype.
- Split into 2–3 intentional lines when needed.
- Do not force a full article title into a cover.
- If the title is long, create hierarchy: main hook + small clarifier, not one giant sentence.

Examples of compression direction:

- `开源了一个 Skill，让 AI 接管你屏幕边那张便签纸` → `AI 接管便签纸`
- `普通人如何理解 AI Agent 和聊天机器人的区别` → `Agent 不只是聊天`
- `为什么你做的 AI 产品总是没人愿意第二次打开` → `为什么没人再打开`

This is layout adaptation, not copywriting polish. Do not invent claims the content does not support.

## Image And Screenshot Treatment

### Photo / Image Overlay

Before placing text on an image:

1. Identify the subject and quiet zones.
2. Keep title away from faces, hands, product features, UI text, and important objects.
3. Try composition first; use localized tint only when needed.
4. Avoid default full-canvas dark overlays.
5. Set image crop deliberately. Do not rely on `object-position:center` for every image.

If the photo cannot support text, use a split layout or framed image instead of forcing overlay.

### Screenshot Handling

- Preserve UI content unless the user asks for redesign.
- Use `object-fit: contain` for screenshots with text, code, dense UI, tables, or app windows.
- Use `object-fit: cover` only when cropping is safe.
- Add frame, shadow, stage, browser/device chrome, or inset background.
- Prefer one strong screenshot per card over several unreadable tiny screenshots.
- Make callouts spatially close to the UI area they explain.

## Portrait Fill Rules

For 3:4 portrait cards, avoid under-filled vertical space.

A card fails if it has a large empty vertical band with no visual reason.

Use one of these fixes:

- enlarge the focal image;
- increase title scale;
- add a quote column;
- add a ledger/list block;
- add evidence image or screenshot;
- add a secondary annotation zone;
- switch to a more suitable layout;
- reduce card count and combine thin pages.

Do not fix under-filled cards by adding random blobs, stickers, gradients, or decorative noise.

## Multi-Card Sequence Rhythm

For card sets, vary roles and density.

Recommended rhythm:

```text
01 Cover / hook
02 Problem or context
03–05 Explanation, comparison, checklist, proof, screenshot, data
06–08 Application, examples, workflow, mistakes
Last Summary / save reason / final thesis
```

Rules:

- Do not make every page title + bullets.
- Do not put two full-bleed image covers back to back unless the user explicitly wants a photo essay.
- After an image-heavy cover, use a more structured text/data card to let the eye settle.
- If the user asks for one card only, make it self-contained: hook + focal visual + 1–3 supporting fragments.

## Template Relationship

If a social-card template exists:

- Read the template `SKILL.md` / `.md` first.
- Do not read `pattern.html` by default.
- Read `pattern.html` only when the markdown lacks layout/interaction detail or the card requires a complex layout reference.
- When reading `pattern.html`, extract only layout relationships, section rhythm, component relationships, and responsive/canvas behavior.
- Do not copy DOM structure, class names, CSS tokens, placeholder content, or visual styling wholesale.

Templates are starting points. This skill decides whether the card needs editorial, Swiss, image-led, screenshot, data, or map treatment.

## HTML-To-Image Implementation Contract

File structure is decided by `card_count`:

- `single` → one **self-contained** HTML file. Inline all styles. No shared assets.
- multi-card carousel, cover-plus-pages, or WeChat cover pair → **one HTML file per card**, plus a shared design-token stylesheet and a preview page.

### Per-card file rules (multi-card sets)

- Each card is its own HTML file. The `<body>` **is** the canvas: set explicit `width`/`height` from `canvas-and-device.md`, no outer wrapper page, no scrolling.
- All cards in one package link the same `shared/tokens.css`. It is the single source of truth for colors, fonts, spacing scale, and the canvas reset (margin resets for `body`, `figure`, `h1`, `p`, `ul`, etc.).
- Card files may add card-private layout CSS, but must not override global tokens locally. Hardcoded colors/fonts that duplicate or contradict tokens are a defect.
- Mixed canvas sizes in one task (e.g. WeChat 21:9 + 1:1 pair) are handled naturally: each file declares its own body dimensions; never share one body size across different presets.
- Generate `preview.html` that embeds every card via `<iframe>` in reading order, scaled to fit. It exists for sequence-rhythm review only and is not a deliverable.
- Editing or regenerating one card must touch only that card's file (and never `shared/tokens.css` unless the change is intentionally package-wide).

### Shared rules (all cases)

- Use explicit canvas dimensions from `canvas-and-device.md`.
- Keep safe areas and platform UI overlays in mind.
- Make text selectable in source HTML but visually composed as an image.
- Export = set viewport to the card's canvas dimensions and take a full-page screenshot of `body`. Do not use element/node clipping; it is fragile with transforms, shadows, and devicePixelRatio.
- Export images in stable order and with stable names, matching their source files.

Suggested structure and naming:

```text
output/
  shared/tokens.css
  card-01-cover.html
  card-02-<topic>.html
  preview.html
  social-01-cover.png
  social-02-<topic>.png
```

For WeChat cover pairs:

```text
output/
  shared/tokens.css
  wechat-21x9-cover.html
  wechat-1x1-cover.html
  preview.html
  wechat-21x9-cover.png
  wechat-1x1-cover.png
  wechat-cover-pair-preview.png
```

## Handoff

Social cards are authored as HTML but normally delivered as images.

Default handoff:

- Save the editable HTML source as the source of truth: one self-contained file for single cards; per-card files plus `shared/tokens.css` for sets.
- Export the final card or card sequence as PNG unless the user asks for JPG/PDF/ZIP.
- Preserve the selected canvas preset from `canvas-and-device.md`.
- For multi-card sequences, export one image per card file and keep ordering stable; card files and exported images can be generated and exported in parallel.
- If the user later asks to revise one card, regenerate only that card's HTML file and re-export only that image.
- For WeChat cover pairs, deliver both the main wide cover and the square cover.
- Do not deliver only a scrollable webpage when the user asked for a social card, cover, poster, carousel, or long image.
- If image export is not available in the current step, still structure the HTML so it can be captured cleanly later and state that export remains pending.

Use the standard `export.md` flow for actual image/PDF/ZIP packaging. Use the standard Design Skill version-management flow only when an editable HTML entry file is delivered as a web project.

## Quality Checks

Run `quality-gate.md` as the shared blocking check first. On top of it, this skill adds social-card-specific checks before delivery:

- correct platform size and ratio;
- title readable at phone thumbnail size;
- no text overflow;
- no accidental edge touching;
- one focal point per card;
- product/update/report cards have one clear message, not a compressed landing page;
- Chinese title breaks intentionally;
- screenshots remain readable;
- images are not distorted;
- no important face/object/UI cropped accidentally;
- no fake data, invented customer logos, or unsupported claims;
- card set does not repeat the same layout page after page;
- 3:4 portrait cards do not have unjustified empty lower space;
- style mode stays consistent across a package;
- in multi-card sets, every card file links the same `shared/tokens.css`, with no local hardcoded colors/fonts that duplicate or contradict tokens;
- every card file's body dimensions match its declared canvas preset;
- no random decorative blobs, stickers, gradients, or emoji icons unless required by the chosen visual language.

## Common Failure Cases

Avoid:

- treating a social card as a compressed article, landing page, or slide deck;
- turning a product brief into a tiny website screenshot full of sections;
- every page using the same title-plus-bullet structure;
- putting long subtitles on covers;
- using tiny Chinese text on mobile images;
- hiding screenshot evidence behind decoration;
- using stock/photo/generative images as filler rather than evidence;
- mixing editorial serif paper style with Swiss KPI grid without intent;
- making every social image look like a Xiaohongshu template when the platform is WeChat, Douyin, or generic;
- copying `pattern.html` instead of adapting the pattern;
- adding visual noise to solve empty composition;
- letting per-card files drift stylistically because tokens were redefined locally instead of read from `shared/tokens.css`;
- rebuilding the entire card set when the user asked to change one card.

## Scope Pushback

Be honest when the request is mostly photography, not card design.

Push back or ask for assets when the user wants:

- outfit/body-shot OOTD images;
- food-plating photography showcase;
- pure aesthetic/dreamcore mood images;
- celebrity/person-specific imagery without supplied assets;
- product photo results where the product image is the entire deliverable.

Offer a layout direction using user-supplied photos/screenshots, sourced images, or generated images only if appropriate.
