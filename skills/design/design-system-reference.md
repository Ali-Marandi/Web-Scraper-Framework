---
name: Design System Reference Skill
description: Select and apply provided style skills, brand inspiration references, open-source component systems, preset HTML templates, or user-owned visual systems to guide design generation and edits.
mode: reference
platform: any
scenario: design-system-reference
preview:
  type: none
default_for:
  - style reference
  - brand inspiration
  - design system reference
  - preset template
  - open-source component system
  - user-owned design system
  - DESIGN.md reference
fidelity: system
---

# Design System Reference Skill

Use this skill when a design task should follow an existing reference instead of inventing a new visual language.

This skill is not a artifact skill. It does not decide whether the artifact is a portfolio, landing page, prototype, content page, or H5 tool.

It works together with artifact skills by providing visual, structural, component, template, and style constraints.

Examples:

- `portfolio.md` + `design-system-reference.md`
- `deck.md` + `design-system-reference.md`
- `prototype.md` + `design-system-reference.md`
- `landing-page.md` + `design-system-reference.md`
- `web-tool.md` + `design-system-reference.md`

---

## Trigger

Use this skill when:

- the user explicitly selects a design system, style, brand reference, or preset HTML template
- the user asks to use a known style skill
- the user asks to use a known open-source component system
- the user mentions a public brand or product style as inspiration
- the user uploads or provides a design system, style guide, screenshot, codebase, tokens, or component library
- the user asks to keep the new artifact consistent with an existing artifact
- the user says to follow a previous version, selected template, UI kit, component style, or visual language

Examples:

- “用 Ant Design 做”
- “用 shadcn/ui”
- “做成 editorial 风格”
- “更 minimal”
- “像 Apple 一点”
- “参考 Linear”
- “小红书风格”
- “按这个截图的风格”
- “沿用上次那个页面的风格”
- “这是我们的设计规范，按这个来”
- “按这个 HTML 模板改”

Do not use this skill when:

- the task has no visual, system, style, or template reference
- the user only wants pure writing, research, or coding
- the user asks for a new visual direction without any reference
- the reference would require copying proprietary assets, logos, distinctive commercial layouts, or private UI patterns

---

## Goal

The goal is to improve design quality and consistency by grounding output in the right reference.

This skill should help the agent:

- avoid generic visual taste
- select only the relevant reference
- use existing systems when available
- distinguish reusable style skills from public brand inspiration
- distinguish open-source component systems from proprietary brand UI
- prevent unauthorized brand copying
- preserve consistency across generated artifacts
- reuse templates, tokens, components, and visual patterns responsibly

The goal is not to force every design into a design system.

If no relevant reference exists, proceed with scenario-specific defaults from `skills/design/SKILL.md`.

---

## Available Reference Libraries

During testing, the system may provide two reference libraries.

Look up known references in:

`skills/design/design-systems/INDEX.md`

Do not load every reference by default. Select only the most relevant reference.

---

### 1. Style Skills

Path:

`skills/design/design-systems/style-skills/`

These are reusable design style skills. Each style may contain:

- `SKILL.md`
- `DESIGN.md`
- `components.html`, optional
- `tokens.css`, optional

Use these when the user explicitly requests a visual style, UI style, design mood, or implementation style.

Examples:

- minimal
- luxury
- editorial
- paper
- retro
- dashboard
- shadcn
- ant
- glassmorphism
- neobrutalism
- professional
- expressive

Behavior:

- Treat these as reusable design recipes.
- Read the selected style's `SKILL.md` and `DESIGN.md` before generating when available.
- Apply only the relevant style guidance to the current artifact.
- Do not load all style skills.
- Do not combine many style skills unless the user explicitly asks.
- If multiple style skills match, choose the most specific one.
- If the style skill conflicts with the user's content or selected template, preserve the user's goal first.

Example:

```text
“做一个 editorial 风格的个人作品集”
→ `portfolio.md`
→ `design-system-reference.md`
→ `design-systems/style-skills/editorial/`
```

---

### 2. Brand Inspiration

Path:

`skills/design/design-systems/brand-inspiration/`

These are public brand-inspired `DESIGN.md` references.

Use these when the user mentions a known public brand or product style.

Examples:

- Apple
- Stripe
- Notion
- Airbnb
- Vercel
- Figma
- Nike
- Tesla
- Shopify
- Spotify

Behavior:

- Treat these as inspiration only.
- Read the selected brand's `DESIGN.md` when available.
- Extract high-level qualities such as mood, hierarchy, density, typography direction, spacing rhythm, color restraint, and interaction feel.
- Create an original design.
- Do not copy logos, layouts, assets, proprietary screens, branded UI, or distinctive commercial patterns.
- Do not claim the output uses the official design system.

Example:

```text
“做一个 Apple 风格的作品集”
→ `portfolio.md`
→ `design-system-reference.md`
→ `design-systems/brand-inspiration/apple/`
```

---

## Reference Types

There are five reference types.

Use the strongest applicable type. Do not load all reference types by default.

---

### 1. User-Owned Design System

Use this when the user provides or owns the design system.

Examples:

- uploaded brand guideline
- uploaded tokens
- uploaded UI kit
- uploaded component library
- existing project codebase
- existing product screenshots
- user-provided Figma file or future Figma MCP reference
- previous artifact created in the same workspace

Priority:

Highest.

Behavior:

- Treat as authoritative.
- Read the provided source before generating.
- Prefer exact tokens, colors, typography, spacing, radius, shadows, components, and patterns.
- Match the existing visual vocabulary before adding new elements.
- Do not invent new visual rules unless the user asks for a new direction.
- If the design system is incomplete, fill gaps conservatively and record assumptions.

Use when the user says:

- “按我们的设计规范”
- “沿用这个项目的风格”
- “参考这个页面”
- “基于这个截图”
- “用这个组件库”
- “跟之前那个版本保持一致”

---

### 2. Style Skill Reference

Use this when the user asks for a general visual style, design mood, or UI style that exists in `style-skills/`.

Examples:

- minimal
- luxury
- editorial
- paper
- retro
- dashboard
- shadcn
- ant
- glassmorphism
- neobrutalism
- professional
- expressive

Priority:

High when explicitly requested.

Behavior:

- Treat as a reusable design recipe.
- Read the selected style's `SKILL.md` and `DESIGN.md` when available.
- Apply the selected style to the current scenario, not the other way around.
- Do not let a style skill override the user's core artifact goal.
- Do not combine many style skills by default.

---

### 3. Open-Source Component System

Use this when the user explicitly asks for a public/open-source design system or component library.

Examples:

- Ant Design
- Material UI / MUI
- Chakra UI
- Radix UI
- shadcn/ui
- Bootstrap
- Tailwind UI, when license/access permits

Priority:

High when explicitly requested.

Behavior:

- Use the system directly according to public documentation and license.
- Prefer official components, tokens, layout patterns, and usage guidance.
- Generate implementation using real component APIs when relevant.
- Respect attribution or license requirements when relevant.
- Do not confuse the open-source system with the company’s private brand assets or internal product UI.

Use when the user says:

- “用 Ant Design 组件”
- “用 antd”
- “用 Material UI”
- “用 shadcn/ui”
- “用 Bootstrap”
- “做成 MUI 风格”

Important:

“Use Ant Design” means use Ant Design’s public component system. It does not mean copying Ant Group’s proprietary products, brand assets, internal dashboards, or non-public patterns.

---

### 4. Public Brand Inspiration

Use this when the user mentions a well-known brand or product style, but does not provide official assets or authorization.

Examples:

- Apple style
- Linear style
- Notion style
- Stripe style
- Airbnb style
- Nike style
- 小红书风格
- magazine style
- premium style

Priority:

Medium.

Behavior:

- Treat as high-level inspiration only.
- Extract abstract qualities, not proprietary expression.
- Create an original design.
- Do not copy logos, brand assets, distinctive layouts, exact page structures, proprietary UI patterns, or internal product patterns.
- Do not claim the output uses an official design system.

Allowed to extract:

- mood
- restraint
- density
- typography direction
- spacing rhythm
- content structure
- interaction feel
- motion temperament
- visual temperature
- hierarchy style

Not allowed:

- copying branded layouts
- using logos or trademarks as design assets
- recreating proprietary product screens
- mimicking distinctive commercial UI too closely
- claiming official system usage

Example:

“Apple style” means Apple-inspired qualities such as restraint, premium spacing, strong typography, product focus, and polished motion.

It does not mean copying apple.com, using Apple assets, or recreating Apple proprietary UI.

---

### 5. Preset HTML Template

Use this only when the user explicitly selects a preset HTML template.

Priority:

High when selected.

Behavior:

- Treat the selected template as a structured starting point.
- Preserve useful layout, responsive behavior, section structure, and interaction patterns.
- Replace placeholder content with user-provided or clearly inferred content.
- Remove sections that do not serve the user’s goal.
- Do not fill unused template slots with fake content.
- Adapt visual style, copy, density, and parameters to the user’s request.
- Preserve editable structure for comment edits, parameter edits, and future export.
- Avoid rewriting the whole template when a local edit is enough.

Do not apply a preset template by default if the user did not select one.

Use when the user says:

- “用这个模板”
- “基于这个 HTML 模板改”
- “我选这个模板”
- “按这个模板生成”
- “从这个模板开始”

---

### 6. Prior Artifact Reference

Use this when the user asks to continue, match, reuse, or modify a previous artifact.

Examples:

- “沿用刚才那个风格”
- “保持上一版的感觉”
- “这个页面也用同样的布局”
- “把这个模板复用到另一个页面”
- “只改文案，视觉不要动”

Priority:

Very high for follow-up work.

Behavior:

- Treat the current or previous artifact as the active design system.
- Preserve approved visual direction.
- Preserve layout, rhythm, typography, components, and parameters unless the user asks to change them.
- Make local edits when possible.
- Do not restart from a new style unless the user explicitly requests it.

---

## Selection Rules

When selecting a design system reference:

1. Prefer explicit user choice over inferred style.
2. Prefer user-owned systems over public systems.
3. Prefer a selected HTML template over generic scenario patterns.
4. Prefer style skills for general style requests.
5. Prefer open-source component systems when implementation depends on components.
6. Prefer brand inspiration only for mood and visual direction.
7. Prefer the current artifact when editing or continuing existing work.
8. Do not load multiple design systems unless the user asks to combine them.
9. If multiple references conflict, prioritize the one closest to the user’s actual artifact or explicit request.

Examples:

```text
“用 Ant Design 做一个后台原型”
→ `prototype.md` + `design-system-reference.md`
→ `design-systems/style-skills/ant/` or an open-source Ant Design reference

“Apple 风格的个人作品集”
→ `portfolio.md` + `design-system-reference.md`
→ `design-systems/brand-inspiration/apple/`

“editorial 风格的作品集”
→ `portfolio.md` + `design-system-reference.md`
→ `design-systems/style-skills/editorial/`

“按这个 HTML 模板做产品落地页”
→ `landing-page.md` + `design-system-reference.md`
→ selected preset HTML template

“沿用上一版风格，改成 H5 工具”
→ `web-tool.md` + `design-system-reference.md`
→ prior artifact reference
```

---

## Conflict Rules

When references conflict:

### User content beats template slots

If a template has sections the user did not ask for, remove them instead of inventing content.

### User-selected template beats generic scenario pattern

Preserve the selected template’s useful structure unless it conflicts with the user’s goal.

### User-owned design system beats public inspiration

If the user provides a brand guideline, use it over “Apple style” or other public inspiration.

### Style skill beats vague mood

If the user explicitly asks for `editorial`, use the selected style skill instead of loosely guessing what editorial means.

### Open-source component API beats visual imitation

If the user asks to use Ant Design, use Ant Design components correctly instead of merely imitating their appearance.

### Current artifact beats new direction during edits

If the user asks for a small edit, preserve the current artifact unless they explicitly request a style change.

---

## Usage Rules

When applying a design reference:

- Do not blindly copy the reference.
- Extract what is relevant to the current scenario.
- Preserve the user’s content and goal.
- Keep the artifact editable.
- Avoid unnecessary redesign.
- Avoid mixing unrelated systems.
- Do not introduce visual rules from a lower-priority reference when a higher-priority reference already provides guidance.

When adapting a reference:

- remove irrelevant sections
- simplify when the reference is too complex
- preserve useful responsive behavior
- preserve useful interaction patterns
- keep component naming and structure clear
- record assumptions when useful

---

## IP and Brand Safety

Do not recreate copyrighted or proprietary designs.

Refuse or redirect if the user asks to:

- copy a company’s distinctive UI
- recreate a proprietary product screen
- use logos or brand assets without authorization
- mimic a proprietary command structure
- clone a branded website or app too closely

Instead, create an original design inspired by high-level qualities.

Safe phrasing:

```text
I can create an original design with similar high-level qualities, such as restrained typography, premium spacing, and product-focused composition, but I should not copy the exact Apple layout or assets.
```

---

## Output Expectations

After applying this skill, the design should show:

- clearer visual direction
- better consistency
- reduced generic styling
- better fit to the user’s stated reference
- appropriate use of templates, components, style skills, or inspiration
- no unauthorized copying
- preserved editability

When useful, record:

- reference type
- selected design system, style skill, brand inspiration, or template
- files consulted
- assumptions made
- sections kept or removed
- parameters changed
- license or attribution concerns

---



## Chinese Typography Reference

Use `horizontal-craft/chinese-typography.md` when the artifact contains substantial Chinese / Chinese / CJK text, Chinese editorial layout, public-account formatting, Xiaohongshu content, Chinese deck typography, Chinese UI labels, or print-design-inspired HTML.

Translate print-design methods into HTML structure: 版心, 网格, 留白, 标题组, 图版, 边注, 章节 rhythm, and proper punctuation.


## Quality Gate

Before delivering this scenario, apply `quality-gate.md`.

This scenario may add stricter checks, but it must not weaken the shared gate.

## Handoff

After selecting and applying the reference, return to the primary artifact skill.

Examples:

- selected `apple` brand inspiration → return to `portfolio.md`
- selected `ant` or `shadcn` style skill → return to the relevant artifact skill
- selected HTML template → return to the relevant artifact skill
- selected previous artifact → return to the relevant artifact skill

This skill guides visual and system constraints. The artifact skill still owns artifact structure and user goal.
