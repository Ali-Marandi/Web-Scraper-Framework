# Horizontal Craft

Horizontal craft files are cross-cutting design constraints. They are not artifact skills, templates, or scenario principles.

Use them after a lightweight design understanding step has determined what the artifact needs. Do not read every file by default.

```yaml
skill_bundle:
  horizontal_craft:
    # Always for Chinese artifacts
    - horizontal-craft/chinese-typography.md

    # Generative craft, loaded when needed
    - horizontal-craft/color.md
    - horizontal-craft/icon-system.md
    - horizontal-craft/animation-discipline.md
    - horizontal-craft/laws-of-ux.md
    - horizontal-craft/technique-library.md

    # Guardrail craft, usually applied during review or when triggered
    - horizontal-craft/anti-ai-slop.md
    - horizontal-craft/accessibility.md
    - horizontal-craft/state-coverage.md
    - horizontal-craft/form-validation.md
    - horizontal-craft/data-integrity.md
    - horizontal-craft/link-and-proof.md
```

`quality-gate.md` verifies whether the relevant horizontal craft checks passed. It should not duplicate the full rulebooks.

## Loading Priority

Do not read every horizontal craft file by default. Load only what the task needs.

### Baseline for Chinese visual design

- Read `chinese-typography.md` whenever the artifact contains meaningful Chinese text.
- Read `reference/fonts.md` when font choice materially affects the visual direction: font-related user requests, typography-led covers/posters/cards/deck covers, official documents, classical/literary content, academic/report tone, industrial/technology display type, or when title/body font attitudes must differ.
- Do not read `reference/fonts.md` for every Chinese task; for ordinary Web/App/Dashboard output without font intent, use a safe system font stack.
- Read other deep files in `reference/` only when their trigger conditions apply.

### Generative craft

Read these before or during drafting when their trigger applies:

- `color.md` — read when no strong design system is provided, when color direction is vague, when semantic colors/status colors are used, or when the artifact risks default blue-purple gradient styling.
- `chinese-typography.md` — read for all Chinese-language artifacts.
  It provides principles and diagnostics, not a universal type-scale preset; concrete sizes should come from the artifact skill, template, design system, or canvas/device registry.
- `icon-system.md` — read when the artifact uses icons, pictograms, status marks, or icon-like decoration.
- `animation-discipline.md` — read when motion, transitions, scroll reveal, microinteractions, or animated H5 behavior are requested or implied.
- `laws-of-ux.md` — read for decision-heavy or interaction-heavy surfaces such as pricing pages, onboarding, dashboards, forms, H5 tools, and product flows.
- `technique-library.md` — read only for advanced front-end effects such as GSAP, Three.js, shaders, rich motion, or data visualization technique selection.

### Guardrail craft

Usually apply these during review, or earlier only when the task clearly triggers them:

- `anti-ai-slop.md` — use as an anti-default check, not as the primary creative direction.
- `accessibility.md` — apply as a final baseline check for web artifacts.
- `state-coverage.md` — read for interactive, data-driven, form, tool, dashboard, or prototype surfaces.
- `form-validation.md` — read for signup, login, checkout, calculators, input-heavy H5, settings, admin forms, or any artifact with validation/error messaging.
- `data-integrity.md` — read when charts, metrics, benchmarks, forecasts, calculations, or proof-like numbers appear.
- `link-and-proof.md` — read when links, CTAs, customer proof, testimonials, logos, awards, or external claims appear.

### Removed boundary

There is no standalone `chinese-copy.md`. Copywriting is not a core design craft. Only short copy-related failure smells that visibly affect design quality remain in `anti-ai-slop.md`.

## Boundary with Scenario Principles and Templates

Templates live outside horizontal craft in `templates/`. They provide optional concrete structure seeds.

Scenario principles decide business priorities. Horizontal craft decides cross-cutting execution quality.

Horizontal craft files are universal constraints that can apply to any scenario or template. `technique-library.md` is here because advanced front-end technique selection is a cross-cutting implementation rule, not an artifact skill.

## Reference Loading Rule

Deep reference files are not passive appendices. When a selected horizontal craft file contains a clear trigger condition, add the matching reference file to `required_reference_files_to_read`. Do not rely on the summary file alone for typography-heavy, publication, report, fixed-image, or punctuation-sensitive work.

For normal UI work, read only the top-level craft file. For typography-heavy work, read 1–3 relevant files from `horizontal-craft/reference/`.

## Deep Reference Files

`reference/` lives inside `horizontal-craft/` because these files are deep typography and layout references used primarily by `chinese-typography.md`. Keep them here instead of the design root.

- `reference/directions.md`
- `reference/title-and-breaking.md`
- `reference/punctuation.md`
- `reference/grid-system.md`
- `reference/text-detail.md`
- `reference/fonts.md`
