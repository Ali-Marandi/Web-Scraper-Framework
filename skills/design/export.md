---
name: Export Skill
description: Package, transform, or hand off the current design artifact without silently redesigning it.
mode: export
platform: any
scenario: handoff
preview:
  type: file
default_for:
  - export
  - download
  - handoff
  - package
  - zip
  - pdf
  - pptx
  - image
  - standalone html
  - design spec
fidelity: delivery
---

# Export Skill

Use this skill when the user asks to export, download, package, hand off, or convert the current design artifact.

Export is not a redesign step. It should preserve the current approved artifact state.

---

## Trigger

Use this skill when the user asks for:

- export
- download
- save as
- package
- handoff
- generate files
- zip
- HTML file
- standalone HTML
- image export
- screenshot
- PDF
- PPTX
- Markdown
- JSON
- design spec
- generation trace
- comment history
- 导出
- 下载
- 打包
- 交付
- 生成文件
- 保存成 HTML / PDF / PPTX

Do not use this skill when:

- the user is only asking to generate the initial artifact
- the user is asking for a design revision
- the user is asking to change visual direction
- the user is asking to extract a DESIGN.md → use `design-system-generation.md`
- the user is asking to use a reference system → use `design-system-reference.md`

---

## Goal

The goal is to turn the current artifact into a usable deliverable.

Export should:

- preserve the current artifact state
- keep the artifact runnable or viewable
- keep edit structure when useful
- include required assets
- include metadata only when useful
- avoid silent visual changes
- flag missing assets or placeholder content

---

## Supported Export Targets

### 1. Standalone HTML

Use when the artifact is already HTML or can be represented as a single HTML file.

Rules:

- include required CSS and JS inline when practical
- preserve stable `data-section`, `data-slide`, and `data-component` markers
- preserve semantic structure
- keep the file runnable locally
- avoid external dependencies unless explicitly required
- if external assets are used, include them or document them

Default for:

- portfolio
- prototype
- deck
- landing page
- content page
- H5 tool

---

### 2. ZIP Package

Use when the artifact has multiple files or assets.

Possible structure:

```text
artifact/
├── index.html
├── assets/
├── DESIGN.md
├── README.md
└── metadata.json
```

Include only what is needed.

Do not package temporary files, cache files, system files, or unrelated source.

---

### 3. Image / Screenshot

Use when the user wants a preview image, cover image, social card, or static snapshot.

Rules:

- preserve current visual state
- choose the requested viewport or slide
- if no viewport is specified, use the artifact’s default viewport
- do not redesign for screenshot export unless requested

For deck exports, support:

- current slide
- all slides
- cover slide
- social preview cover

#### 截图技术规则（Playwright，现写脚本时照此做）

用 Playwright 无头浏览器渲染 HTML 再对元素截图。`file://` 协议下本地图片、字体会被 CORS 拦截，
Canvas 读不到像素、字体不加载。**正确解法是用 `page.route()` 把本地资源映射进去——不要改 HTML
（不要去掉 `crossorigin`、不要被迫把图片转 base64）。**

必做：

- **自动扫描页面引用的所有本地资源**（`<img>`、CSS `url()`、`@font-face` 的 woff2 等），逐个用
  `page.route()` 拦截并 `route.fulfill(path=本地文件)` 喂入。不要手写死单个路径——会漏图。
- 字体响应要带 `Content-Type: font/woff2`（otf 用 `font/otf`）。
- `goto` 之后留足渲染时间（等字体 + Canvas，通常 3–4 秒）再截图。
- 用**元素级截图** `element.screenshot()` 只截目标容器（如 `.frame`），不是整页。

Paste-ready 模板（把资源映射做成自动扫描，按实际目录改 base 路径）：

```python
import re, pathlib
from playwright.async_api import async_playwright

async def capture(html_path, target_selector, out_path, assets_dir):
    html = pathlib.Path(html_path).read_text(encoding="utf-8")
    # 扫描页面里所有本地资源引用（img src / url() / woff2 等）
    refs = set(re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html)) \
         | set(re.findall(r'url\(["\']?([^"\')]+)["\']?\)', html))
    locals_ = [r for r in refs if not r.startswith(("http://", "https://", "data:"))]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1400, "height": 1800})

        # 为每个本地资源建立 route 映射，绕过 file:// CORS
        for ref in locals_:
            fname = ref.split("/")[-1]
            fpath = pathlib.Path(assets_dir) / fname
            if not fpath.exists():
                continue
            ct = ("font/woff2" if fname.endswith(".woff2")
                  else "font/otf" if fname.endswith(".otf") else None)
            headers = {"Content-Type": ct} if ct else {}
            page.route(f"**/{fname}",
                       lambda route, fp=str(fpath), h=headers: route.fulfill(path=fp, headers=h))

        await page.goto(f"file://{pathlib.Path(html_path).resolve()}")
        await page.wait_for_timeout(4000)  # 等字体 + Canvas 渲染
        el = await page.query_selector(target_selector)
        await el.screenshot(path=out_path)
        await browser.close()
```

如果某个本地资源在磁盘上找不到（route 没命中），截图会缺图——交付前确认所有引用都映射成功，
缺失的要报给用户，不要假装截图完整。

---

### 4. PDF

Use when the user wants a printable or shareable static document.

Rules:

- preserve layout
- avoid relying on hover-only content
- ensure page breaks are sane
- for decks, one slide per page unless requested otherwise
- for long pages, use print-friendly layout if available

---

### 5. PPTX

Use when the user wants PowerPoint-style editing or sharing.

Rules:

- preserve slide order and narrative
- preserve text editability when possible
- avoid rasterizing everything unless there is no other option
- if exact fidelity is impossible, say what may change
- for complex HTML decks, export fidelity may be lower than HTML/PDF

Do not promise perfect PPTX fidelity from arbitrary HTML.

---

### 6. JSON / Metadata

Use when the product needs structured handoff.

Possible fields:

```json
{
  "artifactType": "deck",
  "version": "1.0",
  "sourceSkill": "deck.md",
  "references": [],
  "sections": [],
  "slides": [],
  "parameters": {},
  "assumptions": [],
  "placeholders": []
}
```

Use JSON to preserve:

- sections
- slides
- comments
- parameters
- generation trace
- selected template
- selected design system
- assumptions
- placeholder warnings

---

### 7. Design Spec / Handoff Notes

Use when handing off to design, product, or engineering.

Include:

- artifact summary
- structure
- design system reference
- major components
- interaction states
- responsive behavior
- known placeholders
- open questions
- implementation notes

Do not turn the handoff into a long essay. Keep it operational.

---

## Export Workflow

### 1. Identify source artifact

Determine what is being exported:

- portfolio
- deck
- prototype
- content page
- landing page
- H5 tool
- DESIGN.md
- template
- design system package

If there is no current artifact, ask one concise clarification or produce the closest requested file from available context.

---

### 2. Identify target format

Infer the target format from the request.

If the user says only “export”, default to the most natural format:

- HTML artifact → standalone HTML
- deck → standalone HTML deck
- DESIGN.md → Markdown
- multi-file asset → ZIP

Ask only if multiple export formats would materially change the result.

---

### 3. Preserve current state

Do not silently:

- redesign
- rewrite content
- change layout
- change colors
- change component structure
- add missing proof
- remove placeholders

Only make technical packaging changes required for export.

---

### 4. Include assets and metadata

When useful, include:

- local images
- CSS
- JS
- fonts only if legally available and already provided
- README
- metadata.json
- DESIGN.md
- third-party notices

Never include font files from the environment unless the user provided them and license allows it.

---

### 5. Validate output

Before delivery, check:

- file opens or package structure is coherent
- required assets are included
- links are not accidentally broken
- placeholder content is still clearly marked
- export target matches request
- no unrelated files are included
- third-party license notices are preserved when vendored assets are included
- for Playwright screenshot exports: every local image/font the page references was mapped via `page.route()` and actually rendered (no missing-image or fallback-font in the output)

---

## Deck Export Rules

For deck artifacts:

- preserve slide order
- preserve `data-slide` markers
- preserve speaker notes if present and requested
- preserve keyboard navigation for HTML deck
- for PDF, one slide per page by default
- for images, export either selected slide or all slides based on user request
- for PPTX, preserve text editability where possible

If a deck uses preset templates, include relevant notices and assets.

---

## Prototype Export Rules

For prototype artifacts:

- preserve interactive states
- preserve component and screen markers
- preserve navigation links and step flow
- include any data or fixture files needed for the prototype
- do not collapse a flow into one static image unless the user asks

---

## DESIGN.md Export Rules

For design system exports:

- output Markdown by default
- include lightweight tokens when available
- include assumptions and source notes when useful
- if packaged with artifacts, place it at the package root as `DESIGN.md`

---

## License and Third-Party Notices

When exporting vendored templates or assets:

- preserve upstream license files
- include `THIRD_PARTY_NOTICES.md` when available
- do not remove copyright notices
- note whether assets were modified or reorganized

If generated output includes public brand-inspired style, do not claim it is an official brand system.

---

## Output Expectations

At completion, provide:

- exported file or package
- brief note about format
- important caveats only

Do not include a long recap unless the user asks.



## Chinese Typography Reference

Use `horizontal-craft/chinese-typography.md` when the artifact contains substantial Chinese / Chinese / CJK text, Chinese editorial layout, public-account formatting, Xiaohongshu content, Chinese deck typography, Chinese UI labels, or print-design-inspired HTML.

Translate print-design methods into HTML structure: 版心, 网格, 留白, 标题组, 图版, 边注, 章节 rhythm, and proper punctuation.


## Icon System Reference

Use `horizontal-craft/icon-system.md` when the artifact includes UI icons, navigation icons, status icons, feature icons, pictograms, or icon-like visual marks.

Use one coherent icon family or one custom inline SVG style. Do not use emoji as icon substitutes. Do not use unknown low-quality open-source icon packs.


## Canvas / Device / Export Size Reference

Use `canvas-and-device.md` when the artifact includes fixed canvases, device previews, phone frames, dashboard frames, deck canvases, social cards, long images, or image-export surfaces.

Do not stretch device previews or export surfaces into arbitrary generic cards. Preserve the target viewport, aspect ratio, and export size.



## Source Quality Handling

Export should not silently redesign the source artifact.

If the user asks only to export, preserve the current artifact state.

If the user asks to QA, clean up, polish, or prepare for delivery before export, apply `quality-gate.md` first and report or fix gate failures before packaging.

If the source artifact contains fake proof, decorative emoji, dead links, missing data markers, or accessibility failures, do not pretend export fixed them.




When substantial Chinese text is present, use `horizontal-craft/chinese-typography.md` Mandatory Runtime Baseline. Read deeper typography references only for typography-heavy tasks such as 版心、网格、模数、出版感、诊断 or formal report layout.

## Mandatory Final Gate

Before delivery, run `quality-gate.md` as a blocking checklist, not as a passive reference.

The artifact must include or satisfy:

- visible `:focus-visible` handling for interactive controls
- reduced-motion handling when motion exists
- scenario-specific `data-*` markers
- no decorative emoji as icons
- no `href="#"`
- no fake proof without provenance
- no placeholder logic or empty handlers
- non-visible Design Compliance block matching the actual code

If the task contains substantial Chinese text, also apply `horizontal-craft/chinese-typography.md` and its required reference-loading matrix.

## Quality Gate

Before delivering this scenario, apply `quality-gate.md`.

This scenario may add stricter checks, but it must not weaken the shared gate.
