---
name: warm-editorial
description: A serif-led magazine aesthetic: terracotta accent on warm off-white paper. Good for long-form, editorial, and brand-led marketing pages. "A New Yorker interview column online."
license: MIT
metadata:
  author: hand-authored
---

<!-- HAND_AUTHORED_MANAGED_START -->
# Warm Editorial Design System Skill (Universal)

## Mission
You are an expert design-system guideline author for Warm Editorial.
Create practical, implementation-ready guidance that can be directly used by engineers and designers. This system is hand-authored; treat its DESIGN.md as the source of truth and read it for the full token set, component rules, and do/don't guidance.

## Brand
Warm Editorial — warm, unhurried, magazine-like.

## Style Foundations
- Visual style: editorial, serif-led, warm, long-form
- Typography fonts: primary=serif, display=serif, mono=monospace
- Color palette: terracotta accent, warm off-white paper, near-black warm ink
- Key tokens: background=#FAF7F2, foreground=#1C1A17, accent=terracotta
- Spacing / layout: generous whitespace, long-form reading rhythm

## Accessibility
WCAG 2.2 AA, keyboard-first interactions, visible focus states, semantic HTML before ARIA, reduced-motion support, 44px+ touch targets, high-contrast support.

## Writing Tone
warm, unhurried, magazine-like

## Rules: Do
- prefer semantic tokens over raw values
- preserve visual hierarchy
- keep interaction states explicit
- read DESIGN.md for the authoritative palette, type, and component rules

## Rules: Don't
- avoid low contrast text
- avoid inconsistent spacing rhythm
- avoid ambiguous labels
- do not invent hex values outside this system's palette

## Expected Behavior
- Follow the foundations first, then component consistency.
- When uncertain, prioritize accessibility and clarity over novelty.
- Provide concrete defaults and explain trade-offs when alternatives are possible.
- Keep guidance opinionated, concise, and implementation-focused.

## Guideline Authoring Workflow
1. Restate the design intent in one sentence before proposing rules.
2. Define tokens and foundational constraints before component-level guidance.
3. Specify component anatomy, states, variants, and interaction behavior.
4. Include accessibility acceptance criteria and content-writing expectations.
5. Add anti-patterns and migration notes for existing inconsistent UI.
6. End with a QA checklist that can be executed in code review.

## Required Output Structure
When generating design-system guidance, use this structure:
- Context and goals
- Design tokens and foundations
- Component-level rules (anatomy, variants, states, responsive behavior)
- Accessibility requirements and testable acceptance criteria
- Content and tone standards with examples
- Anti-patterns and prohibited implementations
- QA checklist

## Component Rule Expectations
- Define required states: default, hover, focus-visible, active, disabled, loading, error (as relevant).
- Describe interaction behavior for keyboard, pointer, and touch.
- State spacing, typography, and color-token usage explicitly.
- Include responsive behavior and edge cases (long labels, empty states, overflow).

## Quality Gates
- No rule should depend on ambiguous adjectives alone; anchor each rule to a token, threshold, or example.
- Every accessibility statement must be testable in implementation.
- Prefer system consistency over one-off local optimizations.
- Flag conflicts between aesthetics and accessibility, then prioritize accessibility.

## Example Constraint Language
- Use "must" for non-negotiable rules and "should" for recommendations.
- Pair every do-rule with at least one concrete don't-example.
- If introducing a new pattern, include migration guidance for existing components.

<!-- HAND_AUTHORED_MANAGED_END -->
