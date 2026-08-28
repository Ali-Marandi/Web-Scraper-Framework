---
name: accessibility
description: Accessibility baseline for generated HTML artifacts. Covers contrast, focus, keyboard behavior, labels, touch targets, motion safety, semantics, and common failure patterns.
mode: reference
platform: web
scenario: horizontal-craft
preview:
  type: none
default_for:
  - accessibility
  - a11y
  - WCAG
  - focus visible
  - keyboard
  - form labels
fidelity: system
sources:
  - adapted-from-open-design/craft/accessibility-baseline.md
---

# Accessibility

This file defines the accessibility baseline for generated design artifacts. The active design system decides how it looks; this file decides what cannot be broken.

Target **WCAG 2.2 AA** as the practical working baseline unless the user specifies another compliance target.

---

## Contrast

Minimums:

| Pair | Minimum |
|---|---:|
| Normal text | 4.5:1 |
| Large text | 3:1 |
| Non-text UI and graphical objects | 3:1 |
| Focus indicator vs adjacent state | 3:1 |

Do not round up. `2.99:1` fails a `3:1` check.

Avoid low-contrast muted text, especially opacity-based text on dark or colored backgrounds.

---

## Focus visibility

- Every interactive element must have visible `:focus-visible` styling.
- Never remove focus outline without an accessible replacement.
- Focus indicator should be visible by shape, outline, underline, or offset — not color alone.
- Modals must trap focus while open and return focus to the opener when closed.

---

## Keyboard behavior

- Native `<button>` for actions.
- Native `<a href="...">` for navigation.
- Do not use `<a>` without `href` as a button.
- Do not use `<div role="button">` unless keyboard handlers, focus, and pressed state are implemented.
- Escape should close dismissible modals, popovers, and drawers.

---

## Labels and names

- Every form input needs a visible `<label>` or an accessible name.
- Placeholder text is not a label.
- Icon-only buttons require `aria-label`.
- Decorative icons use `aria-hidden="true" focusable="false"`.
- Meaningful status changes use live regions when needed.

Recommended field pattern:

```html
<label for="email">Email</label>
<input id="email" type="email" required aria-describedby="email-hint email-error" aria-invalid="true">
<span id="email-hint">Used for receipts only.</span>
<span id="email-error" role="alert">Email must include @ and a domain.</span>
```

---

## Touch targets

- Minimum practical target: `24×24 CSS px`.
- Preferred mobile target: `44×44 pt` / `48×48 dp` equivalent.
- Adjacent tiny targets need enough spacing.
- Primary mobile actions should be thumb-reachable.

---

## Semantics

- Use one logical `<h1>` per document / screen when possible.
- Heading levels should not skip randomly.
- Use lists for lists, tables for tabular data, buttons for actions, links for navigation.
- Avoid ARIA when native HTML does the job.
- Do not use positive `tabindex`; fix DOM order.

---

## Motion safety

- Add `prefers-reduced-motion` fallback when using animation, transform, transition-heavy interaction, smooth scroll, or scripted motion.
- Do not flash more than three times per second.
- Do not block input with decorative animation.
- Auto-playing motion longer than 5 seconds needs pause/stop/hide controls.

---

## Forms and errors

- Validate on blur by default, not on first keystroke.
- Preserve user input after errors.
- Move focus to the first invalid field after submit.
- Provide a summary for multi-field forms.
- Error copy must say what happened and how to fix it.

---

## Quality checks

```text
[ ] Color contrast passes for body, labels, captions, buttons, focus rings.
[ ] :focus-visible exists and is visible.
[ ] Keyboard can reach and operate all controls.
[ ] Inputs have labels.
[ ] Icon-only buttons have accessible names.
[ ] Decorative icons are aria-hidden.
[ ] Reduced-motion fallback exists when motion exists.
[ ] No href-less fake links are used as controls.
[ ] Semantics match behavior.
```
