---
name: Prototype Skill
description: Design HTML-based product prototypes, product/feature demos (any "做一个 XX 的 demo" / interactive demo request), app flows, web app mockups, dashboards, and interactive product concepts. By default produces TWO separate files: a working interactive prototype (clickable, states complete) AND a standalone interaction flow diagram (core task wiring, key screens, main transitions).
mode: prototype
platform: responsive-web
scenario: product
preview:
  type: html
default_for:
  - prototype
  - product prototype
  - mockup
  - product flow
  - app screen
  - dashboard
  - admin interface
  - web app
  - mobile app
  - clickable demo
  - demo
  - product demo
  - feature demo
  - interactive demo
  - 产品 demo
  - 功能 demo
  - 做一个 demo
  - 演示
  - 功能演示
  - 可交互演示
  - UX proposal
  - product design proposal
  - interaction design
  - user flow
  - design process
  - design deliverables
  - page jump map
  - screen navigation map
fidelity: medium
---

# Prototype Skill

**Document map:** §1 Axes · §2 Non-negotiables · §3 Prototype · §4 Flow · §5 Workflow · §6 Validation · §7 References & handoff

---

## Default deliverables (two files, always together)

| File | Owns | Does NOT own |
|------|------|--------------|
| **`prototype.html`** | Clickable, end-to-end, states complete — running JS, happy path first, reachable states, feedback | — |
| **`flow.html`** | How main tasks connect — key screens, triggers, mini-screen showing result | Exhaustive state inventory; status tag clouds |

**Consistency:** flow canvas nodes/edges must match prototype screens/transitions. Screens not on canvas stay prototype-only. Separate flow node for loading/error only when needed to show task completion/failure; otherwise inline note.

Produce both by default. Only drop flow if user **explicitly** asks for a single screen.

---

## 1. Decide what to build (four axes)

| Axis | Values | Default |
|------|--------|---------|
| **Platform** | web app · mobile app · dashboard/admin · responsive web | infer; if unclear → responsive web |
| **Scope** | single screen · single flow · multi-flow product | single flow |
| **Fidelity** | wireframe · medium · high | medium |
| **Mode** | default · copy · patch | default |

- **default**: from scratch
- **copy**: replicate style from reference, keep unchanged
- **patch**: extract existing design system → insert new features → maintain consistency

### Do not use this skill when

portfolio → `portfolio.md` · deck → `deck.md` · reading page → `content-page.md` · landing page → `landing-page.md` · single-task tool → `web-tool.md`

---

## 2. Non-Negotiables

A prototype that fails any of these is not done.

### 2.1 Happy path first

The normal successful flow of each core task must work end-to-end BEFORE error/edge states.

- Core task = the primary reason a user opens this product.
- "Work" = user enters → main action → meaningful normal result/feedback.
- Do NOT wire core action directly to error/edge. Happy path built and tested first.
- Then add error, empty, loading, disabled as reachable branches.

### 2.2 Every interactive-looking element must respond

- **Core path**: real JS response (navigate, toggle, submit, feedback). Core-path elements MUST NOT use toast as a substitute for real implementation.
- **Off core path**: call `showToast('功能暂未开放')` (or contextual equivalent). A CSS class toggle alone (e.g. sidebar `.active` swap) with no visible content change does NOT count — pair it with a toast or a content area update.
- **Visually non-interactive**: reduced opacity + `cursor: default` + no hover effect. Only for elements clearly outside scope.
- **Forbidden**: dead controls that look active with no response.

### 2.3 Real JavaScript

Running JS mandatory. Screen navigation functional via product UI, not developer chrome.

### 2.4 No dead ends

Every screen has a return path (back/close/nav). User never gets stuck.

### 2.5 IA before polish

Define screen inventory, nav model, one main action per screen before visual work. Weak IA = fix structure first.

### 2.6 No fake proof

Never invent real-looking revenue, logos, counts, benchmarks, testimonials, or personal data.

### 2.7 No preview chrome

Floating screen switchers, debug sidebars, route selectors forbidden unless user asks.

---

## 3. The interactive prototype

### 3.1 Shell & viewport

```html
<main data-prototype="product-name" data-platform="mobile" data-viewport="390x844">
  <div class="phone-shell">
    <section data-screen="home" class="screen active">…</section>
    <section data-screen="success" class="screen" data-state="success">…</section>
  </div>
</main>
```

Mark components/states: `data-component="sidebar"`, `data-state="empty"`, etc.

Declare viewport per platform (`data-viewport="390x844"`).

**Mobile** phone shell must fit the browser **and be centered**:

```css
body {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; margin: 0;
  background: #E8E8E4; /* HARDCODED canvas — NOT derived from prototype tokens.
                          Dark-theme prototypes keep this light background;
                          the contrast frames the phone shell. */
}
.phone-shell {
  width: 390px; height: 844px;
  max-height: calc(100vh - 40px);
  max-width: calc(100vw - 40px);
  overflow-x: hidden; /* prevent horizontal scroll inside frame */
}
/* Hide native scrollbars inside phone frame — mandatory */
.phone-shell * { scrollbar-width: none; }
.phone-shell *::-webkit-scrollbar { display: none; }

@media (max-height: 900px) {
  .phone-shell { width: auto; height: calc(100vh - 40px); aspect-ratio: 390/844; }
}
```

**Desktop**: `max-width: 100vw; max-height: 100vh; overflow: hidden` on shell.

Long content scrolls **inside** active screen (`overflow-y: auto`), not by stretching the shell.

### 3.2 Visual direction

Before drawing UI, select a visual direction that fits the product scenario:

1. **Analyze the product** — what type is it? (consumer app / tool / dashboard / social / finance / health / lifestyle / e-commerce / enterprise…)
2. **Select a style skill** — pick ONE from `design-systems/style-skills/` that best matches the scenario. Read its `DESIGN.md` (and `tokens.css` if available) before generating.

**Matching guide:**

| Product type | Recommended styles (pick one) |
|-------------|------------------------------|
| Consumer / lifestyle | `clean` · `friendly` · `warm-editorial` · `cafe` · `colorful` |
| Finance / data | `dashboard` · `trading-terminal` · `enterprise` · `professional` |
| Tool / productivity | `minimal` · `application` · `sleek` · `modern` |
| Social / community | `vibrant` · `bold` · `energetic` · `colorful` |
| Creative / portfolio | `editorial` · `artistic` · `expressive` · `paper` |
| Premium / luxury | `luxury` · `elegant` · `refined` · `premium` |
| Admin / B2B | `enterprise` · `corporate` · `ant` · `shadcn` |

3. **Apply the style** — load the selected style's `DESIGN.md`, extract its tokens (colors, typography, spacing, radius), and use them as `:root` variables. Adapt to the product context, don't blindly copy.
4. **When user specifies a style or brand**: that takes priority over the matching guide — load via `design-system-reference.md`.

**Anti-default (mandatory):** avoid purple gradients, equal-width feature cards, decorative blobs, emoji as icons, Inter/Roboto/Arial as display fonts. Load `anti-ai-slop.md` for full rules.

### 3.3 Structural floor

These structural minimums apply regardless of visual direction:

- **Phone frame packaging** (mobile): border-radius ≥40px, box-shadow, status bar with notch
- **Clear typography hierarchy**: title / body / meta must be visually distinguishable
- **Primary action prominence**: one main CTA per screen, visually dominant
- **Controlled density**: content should breathe, not crowd

### 3.4 Admin/B2B default component pack

When admin/dashboard/B2B without explicit scope: filter bar · data table with status · primary action (new/create) · pagination · create/edit modal with validation · status feedback components.

---

## 4. The interaction flow document (mandatory, separate file)

**CRITICAL — exact class names and structure below are LOCKED. Do NOT rename, abbreviate, or substitute:**
- `.flow-node` → `.flow-node__title` + `.flow-node-visual` + `.flow-node__note`
- `.flow-node__title` content = **page name** (e.g. "餐厅列表页"), NEVER "Screen A", "Step 1", or step numbers
- `.flow-node-visual` = mini-screen with phone chrome (status bar, content, tab bar), NOT desktop window dots
- `.flow-arrow` between every pair of adjacent nodes, with `.flow-arrow__label` describing the trigger — NEVER omit

### 4.1 Page hierarchy and layout

**FORBIDDEN**: all-SVG flow pages. Flow nodes MUST be HTML elements (`div.flow-node` → `div.flow-node-visual` → content), never SVG `<g>`/`<rect>`. SVG is ONLY for arrows (§4.8).

**Flow.html full structure:**

```
flow.html
├── h1.flow-page-title（左对齐）—— "产品名 · 核心任务流程"
│
├── section.flow-task（每条任务流）
│   ├── h2.flow-task-title（左对齐）—— "任务1：申请换班和审批"
│   ├── p.flow-task-subtitle（左对齐，灰色）—— "发起换班 → 被换人确认 → 老板审批 → 排班更新"
│   │
│   └── div.flow-row（节点横向排列，不换行）
│       ├── div.flow-node
│       │   ├── p.flow-node__title —— 页面名称（如"换班申请页"，不是步骤序号）
│       │   ├── div.flow-node-visual —— mini-screen（固定尺寸，设备边框）
│       │   └── p.flow-node__note —— 操作引起的关键变化（2-3行，可分点）
│       │
│       ├── [箭头 + label]
│       └── div.flow-node（下一个节点）
```

**Layout rules:**
- **Canvas**: CSS Grid with explicit columns or absolute positioning. **`flex-wrap` is strictly forbidden** — nodes must stay in one row per task, with horizontal scroll if needed (`overflow-x: auto` on flow-row).
- **All text elements** (page title, task title, task subtitle, node title, node note) are **left-aligned**.
- **flow-node** width = flow-node-visual width (per platform size table §4.6).
- **flow-node internal elements** (title, visual, note) are left-aligned and same width.

### 4.2 Flow concepts

| Concept | Definition | Example |
|---------|------------|---------|
| **Jump Map** | Screen navigation topology | `Home → Chat` |
| **Interaction Flow** | User actions and state changes | `Send → typing indicator → reply` |
| **State Flow** | Entity lifecycle when it defines the task | `Draft → Submitting → Done` |

**Arrangement patterns:**

- Single-branch: linear horizontal (left → right)
  ```
  [Node 1] →label→ [Node 2] →label→ [Node 3] →label→ [Node 4]
  ```

- Multi-branch: tree-like expansion (main horizontal, branches up/down)
  ```
                ↗ [Branch A-1] → [Branch A-2]
  [Start] → [Decision]
                ↘ [Branch B-1] → [Branch B-2]
  ```

### 4.3 Content policy

**Default: only main task flows.** Do NOT add: requirement background, design system summary, IA table, exception appendix, status tag clouds.

### 4.4 Chrome style

Flow canvas is **completely independent** from prototype visual style.

- **Mandatory canvas colors**: `background: #F6F6F6`, `color: #1A1A1A`. These are hardcoded — do NOT derive flow canvas background from prototype tokens.
- **Forbidden**: dark flow pages, prototype-themed flow pages, prototype accent/primary color as flow canvas background. The prototype's color palette must NOT leak into the flow canvas.
- Prototype tokens/colors appear **inside mini-screens only**, never on the canvas itself.

### 4.5 Node naming rules

| Element | Content | Example |
|---------|---------|---------|
| **flow-task-title** | 任务名称 | "任务1：快速分账" |
| **flow-task-subtitle** | 步骤流程串联 | "添加成员 → 拍票录入 → 勾选分摊 → 一键清算" |
| **flow-node__title** | 该节点对应的**页面名称** | "团队创建页"、"排班总览"、"换班申请页" |
| **flow-node__note** | 操作引起的页面关键变化，2-3行 | "选择要换的班次和目标同事；填写原因；点击'提交申请'进入待确认状态" |

- **flow-node__title 是页面名称**，不是步骤编号（不要写"1. 创建团队"，而是"团队创建页"）
- **flow-node__note 要具体**：描述用户做什么操作 → 页面怎么变化（如出现弹窗、展开面板、跳转新页），可以用分号或换行分点

### 4.6 Node sizing (fixed per platform)

| Platform | Viewport | Node size (w × h) |
|----------|----------|-------------------|
| Mobile app / 小程序 | 390×844 | **220 × 476 px** |
| Mobile small | 375×812 | **210 × 454 px** |
| Desktop web | 1440×900 | **640 × 400 px** |
| Dashboard | 1440×1024 | **640 × 456 px** |

> Escape: if ≤ 3 nodes AND page content is simple (single form / single illustration), Desktop/Dashboard may use half size (320 × 200 / 320 × 228).

- All nodes in one task: same outer size, enforced via CSS `width` + `height`.
- flow-node width = flow-node-visual width.
- Internal elements: percentage-based or `cqi`-based sizing to maintain relative position proportional to prototype.

```css
/* Example for mobile 390x844 */
.flow-node { width: 220px; }
.flow-node-visual {
  width: 220px; height: 476px;
  border: 1px solid var(--border, #e5e5e5);
  border-radius: 12px;
  overflow: hidden;
  container-type: inline-size;
  font-size: clamp(5px, 2cqi, 8px);
}
```

### 4.7 Mini-screen reconstruction

**Full-structure**: every major structural region of the prototype screen (status bar, header, content area, tab bar, floating actions) MUST be present. No region may be omitted.

| Target | Rule |
|--------|------|
| Structural regions | 100% present |
| Flow-critical details | 100% accurate — labels, position, visual weight of CTAs/tabs/fields. **Buttons/CTAs must show real text** (e.g. "提交申请", "保存"), not blank colored blocks |
| Non-critical details | Simplified (fewer items, placeholder blocks, abbreviated text) |

**Forbidden**: text-only cards, gray-bar-only placeholders, abstract boxes, pure text nodes with no visual reconstruction.

**Reconstruction method**: use **CSS-only shapes** (divs with background/border-radius) to represent layout regions. But **any interactive element tied to the task flow (buttons, tabs, key inputs) must include its real text label** — do not leave them as blank shape blocks.

**Text scaling rule — proportion over readability:**

| Prototype text | Mini-screen equivalent | Role |
|---------------|----------------------|------|
| 18-22px title | 10-12px | Section/page titles |
| 13-15px body | 7-8px | Main content |
| 11-12px meta | 6-7px | Captions, timestamps |

- Prioritize proportional sizing over readability.
- If too dense → reduce content items, do NOT enlarge font size.
- Flow-critical labels (CTA text, tab names) may use upper range but must not exceed prototype's visual weight ratio.

**Node HTML pattern:**

```html
<div class="flow-node" data-flow-node="screen-name">
  <p class="flow-node__title">换班申请页</p>
  <div class="flow-node-visual">
    <div class="mini-status-bar"><span>9:41</span><span>···</span></div>
    <div class="mini-header"><span class="mini-page-title">申请换班</span></div>
    <div class="mini-content">
      <div class="mini-form-field"></div>
      <div class="mini-form-field"></div>
      <div class="mini-button">提交申请</div>
    </div>
    <div class="mini-tab-bar">
      <span class="active">排班</span><span>消息</span><span>我的</span>
    </div>
  </div>
  <p class="flow-node__note">选择要换的班次和目标同事；填写换班原因；点击'提交申请'后进入待确认状态</p>
</div>
```

```css
/* Mini-screen shapes */
.mini-status-bar {
  height: 6%; display: flex; align-items: center; justify-content: space-between;
  padding: 0 8px; font-size: 6px; font-weight: 600;
}
.mini-header { padding: 4px 8px; }
.mini-page-title { font-size: 9px; font-weight: 700; }
.mini-content { padding: 6px 8px; flex: 1; }
.mini-card {
  height: 40px; border-radius: 6px;
  background: var(--surface-2, #f0f0f0); margin-bottom: 6px;
}
.mini-button {
  height: 24px; border-radius: 12px;
  background: var(--accent, #333); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 7px; font-weight: 600;  /* MUST have text label */
}
.mini-form-field {
  height: 16px; background: var(--surface-2, #f0f0f0);
  border-radius: 4px; margin-bottom: 4px;
}
.mini-list-row {
  height: 12px; width: 80%; background: var(--surface-2, #eee);
  border-radius: 3px; margin-bottom: 4px;
}
.mini-tab-bar {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 7%; display: flex; justify-content: space-around;
  align-items: center; font-size: 6px;
  border-top: 1px solid var(--border, #e5e5e5);
}
```

**Rules:**
- `.flow-node`: no border/shadow/background (invisible wrapper, width = visual width)
- `.flow-node-visual`: the only bordered element (device chrome, border-radius 12px). **Must have `position: relative`** so pinned children can anchor to it.
- **Buttons and CTAs inside mini-screen MUST contain their text label** — never a blank color block
- Non-critical content (list rows, cards without key actions) may use blank shape blocks
- All elements' relative position must match the prototype screen
- **Pinned elements**: any element that uses `position: fixed / sticky / absolute; bottom: 0` in the prototype (tab bars, cart bars, checkout footers, FABs) → use `position: absolute; bottom: 0; left: 0; right: 0;` inside `flow-node-visual`. Same logic for top-pinned elements (`top: 0`). They must NOT appear in normal document flow below scrollable content.

### 4.8 Arrows (labels mandatory)

**Default implementation — arrow as flex item between nodes** (robust, no coordinate math):

```html
<div class="flow-row">
  <div class="flow-node">…</div>

  <!-- Arrow between nodes: flex item, self-aligns via height -->
  <div class="flow-arrow">
    <div class="flow-arrow__label">点击'提交申请'</div>
    <svg width="48" height="16" viewBox="0 0 48 16">
      <path d="M0 8 L38 8" stroke="#999" stroke-width="1.5" fill="none"/>
      <path d="M36 4 L42 8 L36 12" stroke="#999" stroke-width="1.5" fill="none"/>
    </svg>
  </div>

  <div class="flow-node">…</div>
</div>
```

```css
.flow-arrow {
  flex-shrink: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  width: 64px;
  /* height must match flow-node-visual so arrow centers at visual midpoint */
  height: 476px; /* mobile — match §4.6 node-visual height */
  padding-top: 24px; /* offset for flow-node__title above visual */
}
.flow-arrow__label {
  font-size: 11px; color: #666;
  margin-bottom: 6px; white-space: nowrap;
}
```

**Height rule:** `.flow-arrow { height }` = flow-node-visual height from §4.6 size table. Add `padding-top` equal to the space taken by `flow-node__title` above the visual, so the arrow SVG vertically centers on the mini-screen.

- **Arrow labels are mandatory** — every arrow must have a `.flow-arrow__label` describing what user action or event triggers the transition (e.g. "点击'提交'", "审批通过", "系统检测冲突").
- Bezier curves for branching; straight lines for single-branch.
- Line style: solid = happy path; dashed = alternate/return.
- **Arrows scroll with nodes** — they are flex children of flow-row, so they scroll together naturally.

### 4.9 Scope

4–8 nodes per task. All other states in prototype only. Edge cases as inline notes on nodes/edges, not separate nodes.

---

## 5. Workflow

1. **Infer context** — product type, user, platform, primary task, scope, fidelity
2. **Lock axes** — §1 + confirm dual output
3. **Map IA** — screen inventory, nav model, one main action/screen, states list
4. **Build prototype** — visual direction (§3.2) → shell (§3.1) → screens → JS. Happy path first per §2.1, then states.
5. **Build flow** — core-path screens → fixed-size nodes (§4.6) → mini-screen reconstruction (§4.7) → SVG arrows (§4.8) → labels
6. **Validate** — pass ALL checks in §6 before delivery

---

## 6. Validation checklist (BLOCKING)

**Prototype:**
- [ ] Each core task happy path works end-to-end (entry → action → normal result)
- [ ] Every interactive-looking element responds per §2.2
- [ ] No dead-end screens
- [ ] Phone frame fits browser without page scrolling
- [ ] No horizontal scroll inside phone frame (unless explicitly carousel/banner)
- [ ] body background is `#E8E8E4` (not derived from prototype tokens)
- [ ] No visible native scrollbars inside phone-shell
- [ ] Every off-path interactive element has toast or visible feedback (not just CSS class toggle)

**Flow:**
- [ ] Mini-screens contain all structural regions of corresponding prototype screen
- [ ] All nodes same outer size per §4.6; flow-node width = flow-node-visual width
- [ ] Every button/CTA inside mini-screen has real text label (not blank block)
- [ ] Every arrow has a `.flow-arrow__label` describing the triggering action
- [ ] Arrows are flex children between nodes in flow-row (scroll with nodes)
- [ ] Arrows vertically centered on node-visual (flow-arrow height = node-visual height)
- [ ] flow-node__title = page name (not step number)
- [ ] flow-node__note = 2-3 lines describing what changes
- [ ] Pinned elements (tab bar, cart bar, FAB) use absolute positioning inside flow-node-visual, not in document flow

**Consistency:**
- [ ] Every flow node → reachable prototype screen
- [ ] Every flow edge → working prototype transition

---

## 7. References, editing & handoff

**Load by default:**
- `horizontal-craft/state-coverage.md` — state completeness in prototype
- `horizontal-craft/anti-ai-slop.md` — anti-generic visual

**Load when relevant:**
- `design-system-reference.md` · `horizontal-craft/chinese-typography.md` · `export.md` · `version-management/SKILL.md`

Before generation, use `SKILL.md` Creative Context Completion (creative_positioning, first_impression, anti_default).

**Selected-region edits**: treat selection as primary target; preserve unrelated screens.

**Sync rule**: any prototype edit affecting core-path flow → update corresponding flow node/edge/mini-screen.

**Parameters**: platform · fidelity · device · density · visualTone · colorMode · motionLevel

### Final gate

Run `quality-gate.md` (blocking). Then declare:

- [ ] Mode: `copy | patch | default`
- [ ] Baseline/style source
- [ ] Prototype + flow file paths
- [ ] Validation checklist (§6) passed

**Handoff:** Follow `SKILL.md` § Handoff for export, version management, or selected-region edits.
