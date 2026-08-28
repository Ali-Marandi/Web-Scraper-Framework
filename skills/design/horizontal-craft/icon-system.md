---
name: Icon System
description: Shared icon sourcing, consistency, accessibility, and quality rules for design artifacts.
mode: reference
platform: any
type: horizontal-craft
preview:
  type: none
default_for:
  - icons
  - icon system
  - icon family
  - icon set
  - SVG icons
  - UI icons
  - 图标
  - 图标库
  - 成套图标
fidelity: system
---

# Icon System

Use this shared reference whenever a design artifact uses UI icons, feature icons, navigation icons, status icons, pictograms, or icon-like visual marks.

The goal is not to add more icons. The goal is to use icons as a coherent functional language.

Bad icons make the artifact look more AI-generated than no icons.

---

## Core Rule

```text
One artifact → one icon family → one visual logic.
```

Do not mix line icons, solid icons, emoji, 3D stickers, random SVGs, and different stroke widths in one artifact.

If a coherent icon family is not available, draw a small set of custom inline SVG icons in one consistent style.

---

## Icon Source Priority

Choose icons from one coherent source.

Priority:

1. User-provided icon set
2. Icons included in the selected design system
3. Product-bundled icon library
4. Approved icon libraries only
5. Licensed / free Streamline assets, only when license and attribution requirements are satisfied
6. Custom inline SVG fallback

Do not use unknown icon libraries just because they are open-source.

Do not claim an icon came from a third-party library unless the asset is actually available and permitted.

---

## Approved Icon Libraries

Use only these approved external libraries unless the user provides another set or the selected design system requires another set.

Approved by default:

- Lucide
- Heroicons
- Material Symbols
- Phosphor Icons
- Radix Icons
- Tabler Icons
- Streamline, only when user-provided, free, licensed, or otherwise permitted

Do not mix multiple approved libraries in one artifact unless there is a specific reason and the visual style is manually normalized.

---

## Streamline Rules

Streamline is a high-quality source because it provides large coherent icon families and sets.

Use Streamline only when:

- the user provides Streamline assets
- the environment includes licensed Streamline assets
- the selected Streamline set is free or open-source for the intended use
- attribution requirements can be satisfied

Do not assume all Streamline assets are free to use.

Do not scrape, hotlink, or invent Streamline assets.

If Streamline assets are unavailable, create custom inline SVG icons in a consistent style inspired by the selected icon direction, but do not label them as Streamline icons.

---

## Scenario Defaults

### Prototype / Dashboard

Recommended default:

- Lucide or Heroicons
- 20–24px grid
- 1.5–2px stroke
- rounded caps / joins
- `currentColor`
- restrained usage

Use icons for:

- navigation
- actions
- status
- empty states
- affordance clarification

Avoid:

- icon-heavy cards
- random feature icons
- decorative icon wallpaper

---

### Tool H5

Recommended default:

- Phosphor, Tabler, or custom inline SVG
- larger optical size
- playful but consistent
- fewer icons
- stronger result-area pictogram when useful

Use icons for:

- input affordance
- result card
- retry/share actions
- physical metaphor when the tool needs one

Avoid:

- sticker-like 3D icons
- emoji substitutes
- mixed cute + serious icon styles

---

### Landing Page

Recommended default:

- minimal functional icons only
- avoid icon feature grids by default
- prefer product screenshots, diagrams, numerals, or type-led plates over icon rows

Use icons only when they clarify:

- feature categories
- integrations
- navigation
- product mechanism

Avoid:

- three equal cards each with an icon, title, and description
- icon rows used as filler
- fake integration logos

---

### Deck

Recommended default:

- use icons sparingly
- prefer diagrams, pictograms, numerals, arrows, and simple SVG marks
- keep icon style consistent across slides

Use icons for:

- navigation keys
- simple concept markers
- diagrams
- status legends

Avoid:

- decorative emoji
- slide titles with emoji
- random icon bullets
- icon-heavy feature slides

---

### Content Page

Recommended default:

- usually no icons
- use typography, pull quotes, dividers, and illustrations instead
- icons only for callout type, step labels, or compact metadata

Avoid random icons in long-form reading content.

---

## Visual Consistency Rules

If icons are used, define the icon style before generating the artifact.

Specify:

```text
icon family
style: line / solid / duo / filled / custom SVG
grid size
stroke width
corner style
cap / join style
optical size
color behavior
```

Default custom line icon style:

```text
viewBox: 0 0 24 24
stroke: currentColor
stroke-width: 1.75 or 2
stroke-linecap: round
stroke-linejoin: round
fill: none
```

Rules:

- Keep all icons on the same optical grid.
- Keep stroke widths consistent.
- Do not mix outline and filled icons unless the difference encodes state.
- Do not mix flat icons with 3D icons.
- Do not mix icon libraries.
- Do not use emoji as UI icons.
- Do not use logos as icons unless the user provides them or usage is clearly permitted.
- Do not use icons where a short text label is clearer.

---

## Implementation Rules

Prefer inline SVG for HTML artifacts.

Inline SVG requirements:

```html
<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
  <path d="..." />
</svg>
```

Decorative icons:

```html
<svg aria-hidden="true" focusable="false">...</svg>
```

Meaningful icons:

```html
<button aria-label="Open settings">
  <svg aria-hidden="true" focusable="false">...</svg>
</button>
```

Rules:

- Use `currentColor` so icons inherit text color.
- Do not hardcode random icon colors.
- Ensure icon-only buttons have accessible labels.
- Do not leave inline SVG paths unlabeled if the icon carries unique meaning outside a labeled control.
- Keep icon markup small; do not paste huge unoptimized SVG blobs.

---

## Quality Gate Checks

Before delivery, verify:

- Are icons necessary?
- Is there exactly one coherent icon family or custom SVG style?
- Are emoji absent as UI icons?
- Are stroke widths / fill styles consistent?
- Are icon-only controls labeled?
- Are decorative icons `aria-hidden="true"`?
- Are third-party license / attribution requirements satisfied?
- Are there no unknown low-quality open-source icon packs?
- Are icons not being used as filler?

If the answer is no, remove the icons or replace them with custom inline SVG in one consistent style.

---

## Fallback: Custom Inline SVG

Use this when no approved icon set is available.

Rules:

- Draw only the icons needed.
- Use simple geometry.
- Use a shared 24×24 viewBox.
- Use one stroke width.
- Use `currentColor`.
- Keep forms minimal and readable.
- Avoid clever decorative shapes.

Recommended fallback style:

```html
<svg class="icon" aria-hidden="true" focusable="false" viewBox="0 0 24 24">
  <path d="M5 12h14" />
  <path d="M13 6l6 6-6 6" />
</svg>
```

```css
.icon {
  width: 1.25em;
  height: 1.25em;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
  fill: none;
}
```

Do not call fallback icons Streamline, Lucide, Heroicons, or any other named library.
