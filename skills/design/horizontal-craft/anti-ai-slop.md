---
name: anti-ai-slop
description: Anti-AI-default design craft rules. Use during generation and again as a quality-gate check to avoid generic model output, fake proof, decorative emoji, template layouts, and unearned visual effects.
mode: reference
platform: any
scenario: horizontal-craft
preview:
  type: none
default_for:
  - anti AI slop
  - AI味
  - 反AI味
  - generic design
  - template-looking design
  - design polish
fidelity: system
sources:
  - adapted-from-open-design/craft/anti-ai-slop.md
  - extracted-from-previous-quality-gate.md
---

# Anti-AI Slop

This file is a generation-time craft reference. It defines what **not** to do by default.

`quality-gate.md` should reference this file, not duplicate it.

Core test:

```text
Did this design choice come from the brief, scenario skill, design system, content, or user request?
If not, it is probably model autopilot.
```

A slop item is not always forbidden. It is forbidden when used as an unearned default.

---

## P0 hard failures

Fix these before delivery.

1. **Default indigo / purple AI accent**
   - Avoid `#6366f1`, `#4f46e5`, `#4338ca`, `#3730a3`, `#8b5cf6`, `#7c3aed`, `#a855f7` as generic accent colors.
   - Use the active design system token or a content-driven palette.

2. **Generic blue-purple hero gradient**
   - Avoid purple→blue, blue→cyan, indigo→pink hero gradients unless the brand or brief explicitly earns it.

3. **Emoji as UI icons**
   - Do not use `✨`, `🚀`, `🎯`, `⚡`, `🔥`, `💡` as feature icons, section markers, button decoration, status labels, or deck bullets.
   - Use inline SVG, typographic numbers, CSS shapes, or no icon.

4. **Invented proof**
   - Do not invent “10× faster”, “99.9% uptime”, “3× productivity”, fake customer logos, fake testimonials, fake awards, fake press quotes, fake benchmarks, or fake market data.
   - Use `horizontal-craft/link-and-proof.md`.

5. **Filler content**
   - No `lorem ipsum`, “feature one / two / three”, “placeholder text”, fake console handlers, TODO comments, or empty demo logic.

6. **Rounded-card dashboard default**
   - Avoid the reflexive pattern: rounded white card + 1px border + subtle shadow + colored left border.
   - Use hierarchy, spacing, typography, and state semantics instead.

7. **Unlabeled placeholders**
   - If content is demo or missing, label it visibly. Do not disguise it as real proof.

---

## Color and palette failures

Avoid as defaults:

- purple / blue two-stop gradients as hero, button fill, text gradient, progress bar, or accent
- generic AI dark mode: near-black background + indigo / purple glow
- mesh gradients without a strong reason
- pastel pink / lavender / peach as automatic “soft polish”
- black + gold / muddy bronze as automatic “premium”
- dirty earth tones on dark backgrounds
- Tailwind / Vercel tutorial defaults: indigo, slate, gray ramp, emerald accent, tutorial-blue
- low-contrast muted text, especially opacity `0.4–0.6`

Prefer:

- a nameable color territory
- product- or content-driven palettes
- solid color fields when conviction matters
- material metaphors: paper, ink, cinnabar, brick, forest, phosphor, steel, terminal amber
- explicit CSS tokens instead of scattered magic hex values

---

## Typography failures

Avoid as defaults:

- Inter, Roboto, Open Sans, Arial, `system-ui`, PingFang SC, HarmonyOS Sans, Microsoft YaHei as the visible display identity
- Space Grotesk / Fraunces / Playfair / Instrument Serif as automatic taste markers without reason
- italic serif accent word inside a sans h1 as a reflex move
- gradient text inside h1
- tracked all-caps section labels everywhere
- Chinese body text that is too light on dark backgrounds
- Chinese display text without an intentional display font or accepted fallback

Allowed:

- common fonts as fallback stack positions
- system fonts when the design system explicitly chooses a neutral product voice
- expressive fonts when loaded and tied to the visual direction

---

## Layout failures

Avoid:

- generic Hero → Features → Pricing → FAQ → CTA sequence with no variation
- three equal feature cards with icon / title / description as filler
- bento grid unless the information is genuinely modular
- centered `max-width: 800px; margin: auto; text-align: center` across all sections
- card grids where every card has the same size and rhythm
- fake macOS window chrome with traffic-light dots
- top nav default: monogram left + four links right + hairline rule
- floating phone / device mockups with reflection as default

Prefer:

- asymmetric grids
- meaningful density variation
- editorial rhythm
- one strong signature surface
- exact-ratio frames for key screens
- visual choices based on actual content hierarchy

---

## Component failures

Avoid:

- decorative emoji as icons or UI ornament
- pill chip with colored dot as the universal badge
- gradient primary button + outline ghost button with equal weight
- colored rounded status pills for every state
- fully rounded plastic CTA buttons with shadow
- fake avatars, fake quote cards, fake testimonial blocks
- icon grids that add no information

Use instead:

- inline SVG icons
- typographic numbers
- CSS shapes
- hairline labels
- text links for secondary actions
- real component states
- no icon when text is clearer

---

## Imagery failures

Avoid:

- stock photos used as fake product evidence
- Unsplash desks, sticky notes, laptops-with-coffee, moodboards, gears, Pantone flatlays
- fake product screenshots with fake proof
- screenshots without captions or real source context
- three-quarter floating device mockups as default

If real imagery is missing:

- use type-only hero
- use honest product UI with demo-labeled content
- use SVG diagrams
- use typographic plates
- use honest placeholders

---

## Chinese copy smells that affect design quality

This is not a copywriting rulebook. Only fix copy when it makes the artifact feel generic, breaks hierarchy, or weakens CTA clarity.

Common visual-quality smells:

- 赋能、打造、匠心、极致、丝滑、惊艳、震撼、颠覆、革新、引爆、解锁、加持、沉浸、深度、全方位、一站式
- 闭环、抓手、心智、链路、生态、矩阵、势能、心智占位
- 全新升级、隆重推出、强势来袭、火热进行中
- 「X，让 Y 更 Z」
- 「不止 X，更是 Y」
- 「重新定义 X」
- 「X，从未如此 Y」
- 「为 X 而生」

Prefer concrete verbs:

- 查、算、生成、对比、导出、预约、上传、筛选、复盘、发送

---

## Motion failures

Avoid:

- fade-in on every section as the only motion idea
- parallax by default
- bouncing hover curves everywhere
- decorative background motion unrelated to the task
- animations that delay input or obscure results

Use:

- one purposeful signature motion
- tactile button feedback
- result reveal for tools
- view transitions for multi-view artifacts
- reduced-motion fallback

---

## Background and texture failures

Avoid:

- full-page repeating grid / dot / line patterns behind text
- high-contrast patterns behind body or display text
- multiple noise layers
- blobs, orbs, gradient spheres, floating rings
- background decoration used only to fill empty space

Allowed:

- one subtle material texture on an isolated surface
- edge hairlines
- paper grain at low opacity when the visual world calls for it
- no texture when solid color is stronger

---

## Over-addition decision table

| Tempted to add… | Default decision |
|---|---|
| gradient | probably not; use solid field or grounded palette |
| emoji | no; use inline SVG, type, or nothing |
| rounded card + left-border accent | no; use hierarchy or divider |
| blob / hand-drawn hero illustration | no unless the visual direction needs it |
| testimonial quote | only with real user-provided quote |
| icon feature row | only if icons clarify information |
| bento grid | only if information is genuinely modular |
| hero + 3 cards + CTA | redesign from actual content |
| scroll reveal on everything | no; use one choreographed motion if any |

Rule of thumb: if you are unsure whether to add it, do not add it.

---

## Emoji scan

Before delivery, scan visible text and labels for emoji characters.

Forbidden emoji usage:

- feature icons
- slide icons
- section headers
- navigation icons
- status labels
- CTA decoration
- fake excitement or “friendly” ornament

Allowed emoji usage:

- user-provided content contains emoji
- product/content is emoji-based
- chat/social content uses emoji as actual content
- user explicitly requests emoji-led style

Replacement priority:

1. inline SVG
2. CSS shape
3. typographic number
4. text label
5. no icon

Mandatory scan ranges:

```text
U+1F300–U+1F6FF
U+1F900–U+1F9FF
U+1FA70–U+1FAFF
U+2600–U+26FF
U+2700–U+27BF
U+2300–U+23FF
U+FE0F
U+200D
```
