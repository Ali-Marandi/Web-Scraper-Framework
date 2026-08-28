---
name: quality-gate
description: Final blocking delivery gate for generated or major-edited design artifacts. A short blocking core (must-pass every time) plus on-demand detail checks (only the relevant ones) and non-blocking polish. Run as a checklist, not a passive reference. Triggers on "质量检查", "交付检查", "delivery check", "design QA", "compliance check", or whenever an artifact is about to be handed off.
mode: quality-gate
platform: any
scenario: delivery-quality
preview:
  type: none
default_for:
  - quality gate
  - design QA
  - delivery check
  - compliance check
  - 交付检查
  - 质量检查
fidelity: system
---

# Quality Gate

Run **after** an artifact is generated or substantially edited, **before** delivery. This file only verifies that the right rules were actually applied and visible in the output — the rules themselves live in the artifact skills and `horizontal-craft/*.md`.

```text
Brief → Artifact Skill → Template / Design System / Craft → Artifact → [Quality Gate] → Delivery
```

If a check fails, fix the **smallest** failing issue. Do not redesign the whole artifact unless the user asked for one.

This gate has three tiers — run them in order:

1. **Blocking core** — a short must-pass list. Run **every** time, every delivery, every turn. If you do nothing else, do this.
2. **On-demand checks** — detailed checks that apply **only when the artifact has the relevant thing** (forms, charts, templates, motion…). Skip the ones that don't apply.
3. **Non-blocking polish** — note in the summary; never block on these.

---

## TIER 1 — Blocking core (must pass, every time)

These are交付事故级 failures: the artifact reaches the user broken, off-target, dishonest, or visibly cheap. Check all of them on every delivery — this list is short on purpose so it actually gets run.

```text
[ ] 1. Right artifact type / carrier — matches what the user asked for
       (a poster delivered as a scrollable page, or a product brief treated as a landing page, fails). [§A]
[ ] 2. Relevant to the brief — visibly solves the actual request, not a polished wrong answer. [§A]
[ ] 3. No dead links / no fake JS in a publish-ready artifact —
       no href="#" / javascript:void(0) unless visibly marked placeholder; no alert('todo'),
       TODO handler, or console-only "interaction"; every CTA has a real destination or visible pending state. [§B]
[ ] 4. Content truthfulness AND completeness —
       content comes from a real read of the source: it neither fabricates what isn't there
       (fake data, fake works/projects, fake logos/testimonials/awards/metrics/press),
       NOR omits or waters down what IS there (for source-grounded tasks, each real project/section's
       substance is actually extracted and shown — not left as vague filler or a thin placeholder).
       Depth over bulk: the test is "did it faithfully represent the source", not "is there more text". [§B]
[ ] 5. Chinese fonts actually load — for Chinese content, every named font is really loaded
       (<link> or @font-face) and font-family contains a CJK font; it must NOT fall straight through to system-ui. [§C]
[ ] 6. Interactive artifacts have real behavior — controls are clickable and do something real;
       relevant states (loading / empty / error / success / populated) exist; no placeholder-only interaction. [§D]
[ ] 7. Anti-AI-slop (whole section, blocking — this is what most affects visual quality) —
       no decorative emoji as icons/bullets; no default blue-purple gradient as the visual system;
       no fake proof (logos/testimonials/awards/rankings/press/metrics presented as real);
       no feature-card filler grid (vague 3-up/4-up); no generic "hero + three cards + CTA" with no
       content-specific idea; no stock-photo / floating-device / fake-mockup evidence; no Chinese AI-cliché
       copy; no decorative blobs/orbs to fill space; consistent icon family (no emoji/icon mix);
       no visualization or interaction added only to look advanced. [§E]
[ ] 8. Editability markers — sections / slides / screens / components / states are individually
       identifiable; stable structural anchors exist (semantic HTML, named sections, or selected-region
       comments); no opaque generated blobs that block local edits; placeholder content is labeled. [§F]
```

If any blocking item fails, fix it before delivery. Fix the specific failure — do not redesign by default.

---

## TIER 2 — On-demand checks (only when relevant)

Run a check below **only if the artifact actually contains that thing**. Don't run a forms check on a page with no forms. These deepen the blocking core; they are where you confirm craft was really applied.

### On-demand: which horizontal-craft to verify

For the craft that actually applies, open that file and confirm its rules are visibly applied. Don't load files that don't apply.

| Only if the artifact has… | Verify against |
|---|---|
| **(always, final pass)** the anti-slop core above | `horizontal-craft/anti-ai-slop.md` (full file, for the blocking §E check) |
| Substantial Chinese text / typography-led titles/covers | `horizontal-craft/chinese-typography.md` (+ `reference/fonts.md` when font choice matters) |
| Charts, diagrams, timelines, maps, explorable models | `horizontal-craft/visual-explanation.md` |
| UI icons / pictograms / icon buttons | `horizontal-craft/icon-system.md` |
| Forms / inputs / validation | `horizontal-craft/form-validation.md` |
| Interactive states / dashboards / tools / prototypes | `horizontal-craft/state-coverage.md` |
| Metrics / charts / tables / demo data / claims | `horizontal-craft/data-integrity.md` |
| CTAs / links / proof / citations / logos | `horizontal-craft/link-and-proof.md` |
| Unclear color direction / no design system | `horizontal-craft/color.md` |
| Motion / transitions / animated charts | `horizontal-craft/animation-discipline.md` |
| Pricing / onboarding / dashboards / H5 / conversion flows | `horizontal-craft/laws-of-ux.md` |
| Advanced effects beyond plain CSS/SVG | `horizontal-craft/technique-library.md` |

### On-demand: Template adaptation — only if a template/seed was used

```text
[ ] markdown / SKILL.md instructions were treated as primary over pattern.html
[ ] pattern.html was not copied wholesale; output isn't a shallow text/color reskin
[ ] placeholder copy / fake assets are replaced or labeled; unused sections removed, not filled with fake content
[ ] template structure serves the current artifact skill and the user's goal
```

### On-demand: Design-system / visual consistency — only if a system/reference applies or visual coherence is at risk

```text
[ ] typography, color, spacing, radius, shadows, components share one visual language
[ ] accent color has a role and isn't overused; no unrelated style systems mixed by accident
[ ] system constraints don't override usability or carrier fit
```

### On-demand: Interaction & state detail — only for interactive artifacts (beyond blocking #6)

```text
[ ] form validation preserves input and explains recovery
[ ] dangerous actions have confirm / undo / clear prevention
[ ] keyboard and focus behavior are usable
```
Reference: `horizontal-craft/state-coverage.md`, `horizontal-craft/form-validation.md`.

### On-demand: Visual explanation — only if charts / diagrams / timelines / maps / explorable models exist

```text
[ ] representation matches the information shape; has a clear comprehension goal
[ ] interaction changes what the user can understand/compare/filter/decide (no decorative-only controls or fake filters)
[ ] charts have readable labels, units, scales, conclusions; diagrams have legible nodes, clear arrows, labeled branches
[ ] labels stay readable at target viewport / export scale
[ ] it explains MORE than a clear paragraph or table would (if not, simplify)
```
Reference: `horizontal-craft/visual-explanation.md`.

### On-demand: Accessibility — verify when it matters; NOT blocking for marketing/display artifacts

Design artifacts are mostly marketing/display, so accessibility is **not** a blocking gate here. Apply it when the artifact is a real interactive tool, a form, or when the user/brand requires compliance. Even then, only two items rise toward "really should fix": **severe contrast that hurts readability**, and **icon-only controls with no accessible name** (these affect actual usability). The rest below are good practice, noted not blocked.

```text
[ ] text + non-text contrast sufficient
[ ] focus-visible exists; interactive elements keyboard reachable
[ ] buttons/links use correct semantics; inputs have labels; icon-only controls have accessible names
[ ] decorative icons aria-hidden; chart info not conveyed by color alone
[ ] reduced-motion fallback when motion exists
```
Reference: `horizontal-craft/accessibility.md`.

---

## TIER 3 — Non-blocking polish

Note in the delivery summary; do not block unless severe. Do not over-polish by adding decoration — fix structure, hierarchy, content, proof, interaction, and representation first.

```text
[ ] visual rhythm could be more distinctive
[ ] one section feels generic
[ ] motion could be more purposeful
[ ] a chart could be simplified further
[ ] the design system could be made more explicit
```

---

## Section references (for the blocking core)

The blocking items above point to these short clarifications:

- **§A Brief & carrier** — artifact type matches request; audience/use case visible; language matches; output surface matches platform; major constraints respected; the carrier behaves like its kind (landing = single-subject conversion; portfolio = work/identity hierarchy + project detail; prototype = reachable states + real interaction; content-page = linear reading; info-interactive = explorable info, not a product demo; web-tool = input→logic→result; social-card = fixed canvas, one role; deck = one idea per slide).
- **§B Truthfulness & completeness** — verifiable honesty (links, data, demo labels) AND faithful, complete representation of real source content. Don't invent; don't omit. Demo/sample data labeled; numbers sourced or softened.
- **§C Chinese typography** — named fonts really loaded; CJK font in the stack; never fall through to an uncontrolled fallback. (Full rules: `chinese-typography.md`.)
- **§D Interaction** — real behavior, no placeholder JS, relevant states present. (Full rules: `state-coverage.md`.)
- **§E Anti-AI-slop** — the whole anti-slop list is blocking because it is what most affects visual quality. (Full rules: `anti-ai-slop.md`.)
- **§F Editability** — identifiable sections/components, stable anchors, no opaque blobs, labeled placeholders — so the user can locally edit and iterate.

---

## 交付（门禁内部跑，不向用户念清单）

质量门禁是**内部动作**——跑它，但**不要把检查清单逐条汇报给用户**（不要输出 pass/fail 表、不要列「①产物类型 pass ②相关 pass…」）。这和输出纪律一致：用户要的是做好的产物，不是质检过程。

- 默认：检查通过就**直接交付产物**，不附任何门禁清单 / 汇总表。
- 仅当确实**修复了**某个问题、或有**用户该知道的非阻塞提示**（如「项目图用了占位，建议你发真实图替换」）时，用**一句自然的话**说明，而不是念清单。
- 绝不在产物里嵌入 compliance 注释块。
