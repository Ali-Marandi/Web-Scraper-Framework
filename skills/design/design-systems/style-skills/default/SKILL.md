---
name: default
description: A clean, product-oriented default. Use when the brief doesn't call for a specific mood — good for B2B tools, dashboards, and utility pages. Content-first, chrome-second.
license: MIT
metadata:
  author: hand-authored
---

<!-- HAND_AUTHORED_MANAGED_START -->
# Neutral Modern Design System Skill (Universal)

## Mission
You are an expert design-system guideline author for Neutral Modern.
Create practical, implementation-ready guidance that can be directly used by engineers and designers. This system is hand-authored; treat its DESIGN.md as the source of truth and read it for the full token set, component rules, and do/don't guidance.

## Brand
Neutral Modern — calm, functional, neutral.

## Style Foundations
- Visual style: minimal, functional, quietly confident
- Typography fonts: primary=Inter, display=Inter, mono=JetBrains Mono
- Color palette: background, foreground, accent, muted, border, surface
- Key tokens: background=#FAFAFA, foreground=#111111, accent=#2F6FEB, muted=#6B6B6B, border=#E5E5E5, surface=#FFFFFF, success=#17A34A, warning=#EAB308, danger=#DC2626
- Spacing / layout: 12-column grid, 1200px max-width, 24px gutters; 80/48/32px section spacing

## Accessibility
WCAG 2.2 AA, keyboard-first interactions, visible focus states, semantic HTML before ARIA, reduced-motion support, 44px+ touch targets, high-contrast support.

## Writing Tone
calm, functional, neutral

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
