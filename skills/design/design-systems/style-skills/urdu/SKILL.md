---
name: urdu
description: Urdu-first digital experiences with native RTL support, Nastaliq typography, and bilingual Urdu/Latin harmony. For editorial, personal, and publication layouts.
license: MIT
metadata:
  author: hand-authored
---

<!-- HAND_AUTHORED_MANAGED_START -->
# Urdu Modern (Indus Script System) Design System Skill (Universal)

## Mission
You are an expert design-system guideline author for Urdu Modern (Indus Script System).
Create practical, implementation-ready guidance that can be directly used by engineers and designers. This system is hand-authored; treat its DESIGN.md as the source of truth and read it for the full token set, component rules, and do/don't guidance.

## Brand
Urdu Modern (Indus Script System) — literary, considered, bilingual.

## Style Foundations
- Visual style: editorial, RTL-native, bilingual, publication
- Typography fonts: primary=Noto Nastaliq Urdu, display=Noto Nastaliq Urdu, mono=monospace, latin=Inter
- Color palette: warm publication neutrals with restrained accent
- Key tokens: see DESIGN.md — full RTL type-area, Nastaliq line metrics, and bilingual pairing tokens
- Spacing / layout: RTL type area; Nastaliq-aware line height and measure

## Accessibility
WCAG 2.2 AA, keyboard-first interactions, visible focus states, semantic HTML before ARIA, reduced-motion support, 44px+ touch targets, high-contrast support.

## Writing Tone
literary, considered, bilingual

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
