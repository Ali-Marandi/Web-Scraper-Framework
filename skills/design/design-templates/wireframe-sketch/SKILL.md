---
name: wireframe-sketch
description: Hand-drawn paper-wireframe template — white paper background, monochromatic ink palette, SVG turbulence "wobble" filters for pen-quiver authenticity, handwritten fonts (Caveat / Kalam / Ma Shan Zheng / Long Cang), wavy dividers, sketch-rect overlays, marginalia annotations. For PRD illustrations, IA flow docs, low-fidelity layout exploration, "draft / not final" stakeholder communication. Three skeletons (single-page editorial / app multi-screen flow / IA sitemap) — pick one up front based on the artifact, do NOT inherit only the brush strokes.
visibility: public
mode: template
carrier: web-page
scenario: lo-fi-mockup
pattern_source: foolscap-wireframe.html
source_priority: skill-first
triggers:
  - "做个手绘 wireframe"
  - "纸感线框图"
  - "IA 流程图"
  - "低保真草图"
  - "PRD 配图"
  - "draft / not final 风格"
---

# Wireframe Sketch Template

Hand-drawn lo-fi wireframes that look explicitly draft — to invite layout feedback, signal "not shippable", or document IA without committing to visual design.

## ⚠️ Pick the Skeleton FIRST

The biggest failure mode of this skill: model inherits the brush strokes (wobble, dashed, handwriting) but writes the **wrong document structure** — e.g. producing 3 isolated app screens when a multi-screen flow doc was needed, or stuffing a sitemap with editorial figures.

**Before you write a single line, declare in your reply which skeleton you're using and why.** Match user's words to one of:

| User says | Skeleton | Why |
|---|---|---|
| 报纸 / 杂志 / landing / 官网 / brochure / 单页 / 一篇 / 简报 / 海报式文档 / one-pager / editorial | **A. Single-Page Editorial** | One long page, sections stack, content-dense |
| App / 小程序 / 移动端 / 手机 / 桌面应用 / SaaS 流程 / 用户路径 / 注册流 / 下单流 / 多屏 / 多页 / 注册 / 登录 / 引导 / 设置 / Tab / 表单流 | **B. App Multi-Screen Flow** | Multiple screens, navigation, states, triggers |
| 信息架构 / IA / sitemap / 站点地图 / 流程图 / 关系图 / 节点图 / 数据流 / 状态机 / 权限矩阵 | **C. IA / Sitemap Diagram** | Nodes + edges, no actual screens |
| 不明 / 用户没说 / 都行 | **ask the user** before picking — don't default | — |

If the user gave a topic but no skeleton hint, **ask which one**. Picking wrong = doing the work twice.

---

## Skeleton A — Single-Page Editorial

`foolscap-wireframe.html` is the reference for this skeleton. Use when the artifact is a single scrollable page (newspaper, magazine spread, landing page wireframe, brochure, single-page PRD illustration).

Required sections (in order, can drop 1–2 but keep the rhythm):

1. **Masthead / banner** — title, issue/version, date
2. **Hero feature** — one big lead block with headline + intro + hand-drawn illustration placeholder
3. **3–5 content sections** — each with its own h2, mix of text figures and sketch illustrations
4. **Sidebar / brief / list block** — short items, dense type, breaks the rhythm
5. **CTA / signup / footer**

Density: aim for the foolscap reference's content-per-square-inch — sparse single-page wireframes feel like a stub, not a draft.

---

## Skeleton B — App Multi-Screen Flow ⛔ HARD MINIMUMS

`foolscap-wireframe.html` is **not the reference for this skeleton** — only borrow its SVG filters, font stack, and dashed-cell aesthetic. The document **structure** must be assembled from the checklist below.

### Required sections (MUST all be present — page is incomplete otherwise)

1. **Cover** — app name + version + role/persona + 1-line scope ("MVP / 内测 / v0.3 / 仅记账,不含理财")
2. **Sitemap / nav diagram** — visual tree or grid showing all screens and their relationship. Not a list — an actual diagram with boxes + lines.
3. **6–8+ core screens** as `figure` blocks. For a 记账 app that's at minimum: 启动/欢迎 → 首页(概览) → 记一笔(金额→分类→备注→保存) → 账单详情 → 月度统计 → 分类管理 → 预算设置 → 我的/设置. **3 screens is not a wireframe doc, it's a sketch sample.**
4. **At least 1 flow arrow diagram** showing user path across screens (e.g. "首页 → 点'+' → 记一笔 → 保存 → toast → 回首页"). Don't just put a single `↓` between screens — write the trigger on the arrow.
5. **At least 1 state variant** for each screen that has state: empty / loading / error / success. Pick the screens where it matters (list page → empty state; form → error state).
6. **End matter** — open questions / TBD list / version log / next-step decisions to make

### Per-screen requirements

Every screen block must have:
- **Figure number** — `图 02` / `Fig. 03`, sequential, referenced from flow diagrams
- **One-line responsibility** — "记一笔 · 从主页点'+'进入,保存后弹 toast 并返回主页"
- **Trigger annotations** — what entry points lead here, what exits go where
- **Marginalia** — at least 1 hand-written side note per non-trivial screen (constraint, edge case, "TBD",未决问题)

### Layout

- **Vertical stack** of screens with explicit arrow + trigger label between each (not a passive `↓`)
- Or **horizontal flow strip** with screens in left-to-right order — works well for linear flows like onboarding/checkout
- **Don't** put screens in a grid with no flow indication — that's a screen gallery, not a flow doc

### Content density red lines

- < 5 screens → reject yourself, ask user for more flows or downgrade scope honestly
- No sitemap → reject yourself, the doc is unreadable without it
- No state variants → at least mark the empty/error spots even if you don't draw them ("空状态:见图 04a / TBD")
- No marginalia anywhere → you copied the brush but not the language; go back and annotate

---

## Skeleton C — IA / Sitemap Diagram

Pure structural document — no real screens, just node-edge diagrams of information architecture, navigation, data flow, or state machines.

Required sections:

1. **Title + legend** — what the boxes mean, what the line types mean (solid = direct nav, dashed = conditional, double = data binding)
2. **Main diagram** — the tree/graph itself, central, large
3. **Per-node mini-spec** — for non-obvious nodes, 1–3 lines of what lives there
4. **Permission / role matrix** if applicable
5. **Open questions** at the bottom

Wobble + handwriting still apply. Box-and-line layout, lots of whitespace, single accent color for the "current path" / "default" highlight.

---

## Marginalia Language (skeletons B & C must use; A optional)

Marginalia is what separates a real lo-fi wireframe from a "high-fi draft pretending to be lo-fi". Use these moves:

| Mark | When | How |
|---|---|---|
| Side note | Constraint or rationale | `<aside class="margin">` in handwritten font, accent color, pulled into the margin |
| Circle + arrow | Calling out a specific element | SVG `<circle>` + `<path>` with `filter:url(#wobble)`, accent stroke |
| TBD / ? | Unresolved decision | Handwritten "TBD" in accent color, sometimes inside a wobbly circle |
| Strikethrough | Old idea kept for context | `text-decoration:line-through` + slight rotation `transform:rotate(-1deg)` |
| Underline + ! | Important / must-discuss | Wavy underline SVG below the term |
| Numbered call-out | Reference into a legend table below | Circled digit in accent color, with `<ol>` legend at section end |

**Marginalia ink color** = the one accent (template uses bright blue). Body ink stays monochrome.

---

## Hand-drawn Marks

Lo-fi wireframes lean heavily on **drawn-in-place** marks, not real icons or photos. Build a small library at top of file:

- **X-out box** — image placeholder: `<rect>` + two crossing `<line>`, all under `filter:url(#wobble)`
- **Wavy-line text** — copy placeholder: 3–5 `<path>` of horizontal squiggles at decreasing widths
- **Stick icons** — nav icons as 8–16 px SVG paths (house, plus, chart, gear), 1.4 px stroke + wobble
- **Loading spinner** — wobbly circle with a gap, no animation needed for static deliverable
- **Avatar circle** — circle + initials in handwritten font
- **Chart bones** — wobbly bars / dots / lines, no axis labels beyond figure number

**Don't** import an icon font, lucide, heroicons, etc. Real icons fight the wobble and instantly break the lo-fi register.

---

## Required Reading

Read this `SKILL.md` first, end to end. **Don't** open `foolscap-wireframe.html` until you've picked a skeleton.

Then:
- **Skeleton A** → read foolscap fully, both for structure and brush vocabulary
- **Skeleton B** → open foolscap ONLY to copy: the `<filter>` SVG turbulence values, the dotted background pattern, the dashed/wavy divider paths, the handwritten font stack. **Do not copy** the masthead/hero/long-reads structure — wrong skeleton.
- **Skeleton C** → same as B, brush-only extraction

Never copy foolscap's placeholder editorial copy, figure captions, or class names wholesale.

---

## Design Strategy

Lock the **scope of fidelity** at the top:

- **pure structure** (boxes + labels only, no real type beyond field names) → maximum wobble, sparsest content
- **structure + sample content** (placeholder headlines, real labels, fake numbers like ¥3,280) → moderate wobble, more density
- **structure + annotations** (arrows, marginalia, "TBD", trigger labels) → wobble + marginalia + accent-color callouts

Pick one and hold the line across the whole doc — mixing fidelities reads as inconsistent. Skeleton B almost always wants tier 3.

---

## Layout Bias

Prefer:

- pure white paper background — no yellow legal-pad pretense
- monochrome ink (black + 2–3 grays), at most one accent (bright blue or red) for marginalia and "current/default" highlight
- one handwritten CJK font (Ma Shan Zheng / Long Cang) + one handwritten Latin font (Caveat / Kalam)
- mono stack (uppercase, tight letterspacing) for "labels" / "figure numbers" / "callouts"
- dashed or wavy dividers between sections — never solid clean rules
- consistent wobble intensity — don't dial it up and down per element; one global filter + maybe one "stronger" for tiny shapes
- numbered figures ("图 01", "Fig. 02") for everything referenced from elsewhere in the doc
- generous side margins to make room for marginalia

Avoid:

- real production icons or polished SVG illustrations (they fight the sketch frame)
- color photos (use sketch placeholders — X-out boxes or wavy-line text)
- emoji
- mixing wireframe with high-fidelity components on the same page
- forcing the wobble filter on every element until the page becomes noisy — wobble is a seasoning, not a wash
- 单一 `↓` 当作 flow 注释 — write the trigger on the arrow
- 在 App 场景里只画 3 个孤立屏并交付 — that's a screen sample, not a wireframe doc

---

## Anti-patterns (self-check before delivering)

- [ ] App 场景但没 sitemap → reject, add one
- [ ] App 场景但 < 5 屏 → reject, expand or downgrade scope honestly
- [ ] 屏与屏只用 `↓` 连接没 trigger label → annotate every arrow
- [ ] 通篇没有任何 marginalia / TBD / 圈划 → 你只继承了笔触没继承语言,补
- [ ] 用了 lucide/heroicons/emoji/真实 icon font → 拆掉换 SVG path 简笔
- [ ] wobble 强度乱跳 → 统一到 1–2 个 filter id
- [ ] 没有 figure 编号但流程图里要引用 → 加编号
- [ ] 文案太"成品"(完整营销 copy / 准确产品文案) → 退回到 placeholder ("功能 A 的一句话说明")
- [ ] 用了亮黄色 legal-pad 底 → 改回纯白纸
- [ ] 配色超过 1 个 accent → 砍

---

## Platform / Size

Renders as a web page, typically captured as a long screenshot for embedding in PRDs / Notion / Confluence / 飞书 docs. Not designed for runtime interaction — it's a static deliverable that looks hand-drawn.

For Skeleton B, page width 720–960 px works well (matches reading width in doc tools). For Skeleton A, 960–1100 px (editorial format). For Skeleton C, often wider (1200+) to fit sitemaps.
