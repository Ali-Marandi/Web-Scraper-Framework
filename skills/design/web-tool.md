---
name: Web Tool Skill
description: Design single-task interactive web tools — calculators, generators, converters, checkers, pickers, quizzes, tests, decision tools, and lightweight utilities for desktop or mobile web.
mode: artifact
platform: responsive-web
scenario: web-tool
preview:
  type: html
default_for:
  - web tool
  - H5 tool
  - mini tool
  - calculator
  - generator
  - converter
  - checker
  - picker
  - quiz
  - test
  - countdown
  - timer
  - QR generator
  - decision tool
  - 小工具
  - Web 小工具
  - H5 小工具
  - 计算器
  - 生成器
  - 转换器
  - 测试
  - 答题
  - 抽签
  - 抽奖
  - 决策器
  - 占卜
  - 运势
fidelity: high
---

# Web Tool Skill

Design a **single-task interactive web tool**. The user comes to do one thing — calculate, generate, convert, check, pick, decide, answer, or get a result — and leaves with a useful output.

`H5` is only one output form. This skill covers desktop web, responsive web, mobile web, and H5 sharing experiences.

Use the global Design Skill flow, quality gate, delivery, export, and version-management rules.

## Route elsewhere if

- it is a multi-screen product/app flow, dashboard, admin UI, or product prototype → `prototype.md`.
- it is a marketing/conversion page where the tool is only a CTA support → `landing-page.md`.
- it expresses information through exploration rather than performing a task → `info-interactive.md`.
- the final artifact is primarily a social image/result card/long-image sequence → `social-card.md`.
- it is a slide presentation or report deck → `deck.md`.

A landing page with an embedded calculator can use `landing-page.md` as primary and borrow this skill's tool logic. A standalone calculator/generator/checker routes here.

## Output target selection

Choose output target by usage context:

- `responsive-html` — default for desktop or general web tools, internal tools, tools with tables, broad forms, or mixed desktop/mobile usage.
- `mobile-html` — when the user says H5, mobile-first, WeChat/mobile sharing, QR entry, or phone-only experience.

## What makes a web tool succeed

The tool must actually work. A beautiful form with fake results is a failed artifact.

- **Real function** — real computation, generation, conversion, validation, or selection logic.
- **One obvious path** — input → action → result is clear on first glance.
- **Result is the hero** — the output is large, useful, copyable/shareable when helpful.
- **Error recovery** — invalid and edge inputs explain what happened and how to fix it.
- **Appropriate surface** — desktop tools can use more width and tables; H5 tools need thumb-friendly controls and no fragile viewport assumptions.

## Logical completeness

Cover the states a real tool hits:

- initial / empty;
- valid input;
- invalid input with specific recovery text;
- edge values such as zero, negative, max, overflow, unsupported format;
- loading / processing when relevant;
- result;
- reset / retry;
- share/save/copy when included.

Do not silently fail on the second-most-obvious input.

## The few decisions that matter

- **Tool type and interaction model** — field, slider, picker, dropdown, stepper, upload, paste box, toggle, quiz, or multi-input form.
- **Result model** — number, verdict, score, generated text, file, QR, chart, comparison, plan, or share card.
- **Validation model** — inline, on-submit, progressive, or step-based; error messages must be specific and recoverable.
- **Visual world** — match the subject. A tax calculator, fortune tool, ROI estimator, and QR generator should not all look like the same grey form.
- **Platform ergonomics** — desktop can show dense controls; mobile/H5 prioritizes thumb reach, 44px+ targets, and stable result layout.

## Non-negotiables

- Core function works with real JS.
- No fake computation, fake generated result, or empty handler.
- One primary action.
- Result gets visual priority.
- Input validation is real and recoverable.
- Placeholder/demo data is clearly marked.
- No decorative emoji as icons; use SVG/icon system when needed.
- No dead `href="#"` in publish-ready output.

## Avoiding AI slop

The detailed catalog lives in `quality-gate.md`. For tools, the reflex to avoid is a centered grey form with a blue button and a fake result block. Give the tool a visual identity only after the task logic is right.

## Decision Sequence

1. State the single task, inputs, output, and required states.
2. Choose the interaction model and result model.
3. Choose output target: responsive web or mobile/H5.
4. Build real working logic and validation.
5. Make the result moment visually dominant.
6. Test normal, invalid, and edge inputs before delivery.
7. Run the global quality gate.

## References, load only when triggered

- `horizontal-craft/state-coverage.md` — tool states, result states, loading/error/success/reset/share.
- `horizontal-craft/form-validation.md` — input fields, forms, upload, required fields, invalid values, helper text.
- `horizontal-craft/data-integrity.md` — formulas, scores, ROI, financial outputs, benchmarks, charts, estimates, or claims.
- `horizontal-craft/chinese-typography.md` — substantial Chinese text.
- `horizontal-craft/color.md` — no design system is provided, or the tool needs a distinct visual world.
- `horizontal-craft/icon-system.md` — icons, status symbols, QR/action marks, repeated symbolic markers.
- `horizontal-craft/animation-discipline.md` — result reveal, transitions, or feedback motion.
- `horizontal-craft/technique-library.md` — advanced interaction, data visualization, 3D, or complex motion genuinely improves the tool.
- `canvas-and-device.md` — mobile/H5 viewport, responsive breakpoints, device frame, shareable result card, or export size.
- `design-system-reference.md` — brand/style/template/DESIGN.md reference exists.

Do not load every reference by default. Start with state/form/data only when the tool needs them.

## Creative Context

For open-ended requests, use `SKILL.md` Creative Context Completion before generating. The scenario rules define function; creative context defines the tool's visual and interaction character.

## Final Gate

Run `quality-gate.md` as the blocking global checklist. Web-tool-specific failures:

- computation/generation/checking logic does not run;
- invalid or edge inputs fail silently;
- error messages are vague or unrecoverable;
- result is visually secondary or hard to copy/use;
- share/save/export affordance is promised but not implemented;
- formulas, assumptions, or demo data are not disclosed;
- the tool is actually a product flow, landing page, or information page and should have routed elsewhere.

## Handoff

Use the standard Design Skill delivery, export, and version-management flow.

If the tool produces a shareable result card, downloadable image, QR code, CSV/JSON, copied text, or generated artifact, keep that output as a named export target and route conversion/package work through `export.md`.

If the user asks for H5/mobile sharing, optimize for `mobile-html`; otherwise use a responsive web layout that works on desktop and mobile.
