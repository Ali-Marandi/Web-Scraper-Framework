---
name: state-coverage
description: Required UI states for interactive, data-driven, form, tool, dashboard, and prototype surfaces. Prevents designs that only render the ideal populated state.
mode: reference
platform: web
scenario: horizontal-craft
preview:
  type: none
default_for:
  - state coverage
  - empty state
  - loading state
  - error state
  - forms
  - dashboard
  - interactive prototype
fidelity: system
sources:
  - adapted-from-open-design/craft/state-coverage.md
---

# State Coverage

The single most reliable AI-design failure is shipping only the populated state.

The active design system decides how states look. This file decides which states must exist and what they must contain.

---

## The five required states

Every surface that fetches, transforms, filters, searches, or accepts data must handle all five.

| State | Triggered when | Must contain |
|---|---|---|
| Loading | Data is in flight | skeleton, spinner, shell, or labelled progress |
| Empty | no records yet or query returned nothing | headline, explanation, primary next action |
| Error | fetch failed, server failure, validation rejection | plain cause, recovery action, preserved input |
| Populated | data present | the main designed state |
| Edge | extreme volume, long strings, missing fields, partial network | layout does not break |

Render-and-screenshot test: every list, table, card, form, and panel has these states.

---

## Edge matrix

| Surface | Edge scenario |
|---|---|
| Dashboard / table | 10,000+ rows, numeric columns, sort + filter active |
| Mobile card / list | 200-char title, missing avatar, missing secondary CTA |
| Form | optional fields empty, required fields at max length |
| Search results | one-character query, special-character query, 1,000+ results |
| Detail view | missing optional metadata, mixed Chinese / Latin / long words |
| Tool H5 | invalid input, user retries, result cannot be computed |

---

## Form-specific states

Forms add:

| State | Triggered when | Behavior |
|---|---|---|
| Untouched | field has not had focus | default styling; no validation message |
| Dirty valid | user typed and field passes validation | helper remains; avoid excessive success coloring |
| Submitted pending | submit clicked, waiting | button loading state; prevent duplicate submit |

Validation timing:

- validate on blur by default;
- for password / live fields, validate on keystroke only after first blur;
- remove error when input becomes valid;
- preserve input on server failure.

---

## Empty state composition

Empty is not absence. It has a job.

- **First-use empty:** illustration or simple mark + headline + value sentence + primary CTA.
- **No-results empty:** echo the query, suggest alternatives.
- **Cleared empty:** confirm completion, optional next action.
- **Error-as-empty:** forbidden. Error is its own state.

---

## Error state composition

Every error answers:

1. What happened.
2. Why, if knowable.
3. What the user can do.

Bad:

```text
Something went wrong.
```

Better:

```text
未能保存表单。网络连接中断，请检查后重试。
```

Severity tiers:

- field-level
- form-level
- section-level
- page-level
- app-level

Match severity to scope. A field error does not need a page-level error.

---

## Loading thresholds

| Duration | Indicator |
|---|---|
| 0–300ms | none |
| 300ms–2s | subtle spinner or skeleton |
| 2–10s | skeleton or labelled spinner |
| 10–30s | progress with cancel option when possible |
| 30s+ | explicit longer-than-expected message |
| 60s+ | stop indefinite animation; show error / retry / cancel |

Never leave a spinner running indefinitely.

---

## ARIA and focus rules

| Change | ARIA | Focus action |
|---|---|---|
| Inline error on submit | `role="alert"` | move focus to first error field |
| Toast confirmation | `role="status"` | do not move focus |
| Critical modal | `role="alertdialog"` | move focus to dialog |
| Loading begins | `role="status"` | do not focus spinner |
| User-triggered content appears | usually none | move focus only if it helps continuation |

---

## Common mistakes

- only populated state exists
- empty state says only “No data”
- error says only “Something went wrong”
- spinner has no timeout
- submit clears fields on failure
- validation fires on first keystroke
- full-page loading replaces chrome for a section-level fetch
- color alone conveys error state
- toast cannot be paused on hover/focus

---

## Quality checks

```text
[ ] Loading, empty, error, populated, and edge states exist where relevant.
[ ] Empty state has explanation and next action.
[ ] Error state has cause and recovery.
[ ] Forms preserve input after failure.
[ ] Long strings and missing optional fields do not break layout.
[ ] Loading does not spin forever.
[ ] State changes are announced where appropriate.
```
