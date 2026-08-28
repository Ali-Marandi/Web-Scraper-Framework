# Survey Section-by-Section Playbook

## Why this exists

A survey paper is not a longer research paper. The sections look superficially similar but carry different load. A research paper has a contribution (Method) and evidence (Experiment / Results); a survey has organisation (Taxonomy / themed reviews) and judgment (Discussion / Open challenges). This reference gives the per-section playbook for surveys specifically.

## Universal rules

- Every section starts with `\section{Title}\label{sec:slug}`.
- Cross-references between sections use `Section~\ref{sec:slug}` (non-breaking space).
- Inline citations: `~\cite{key}` for textual flow. With `[numbers,sort&compress]`, this produces `[3, 7]`-style refs.
- Figures: see `04-layout-discipline.md`. Survey figures are organisational; cite them often.
- One topic per paragraph.
- Use first-person plural ("we") consistently.

## Abstract — `sections/abstract.tex`

**Length:** 200–300 words. **Citations:** 4–8.

**Structure (one paragraph):**
1. **Domain & importance** (1 sentence).
2. **Why a survey now** (1 sentence): why is this the moment, what was missed by prior surveys.
3. **Scope** (1–2 sentences): what's in, what's out.
4. **Approach to the survey** (1 sentence): your taxonomy / lens.
5. **Headline findings** (2–3 sentences): the most useful generalisations the reader can take away.
6. **What's next** (1 sentence): open challenges teaser.

**Anti-patterns:**
- Marketing prose ("This survey provides a comprehensive overview…").
- No quantitative anchor (number of papers covered, time span).
- Spillover into Related Work.

## Introduction — `sections/introduction.tex`

**Length:** 4–5 paragraphs (~900–1300 words). **Citations:** 12–20.

**Structure:**

**¶1 — Problem frame.** Why is this field important? Use 2–3 application motivations and a quantitative anchor (market size, scale, dataset count). Cite foundational references.

**¶2 — Trajectory of the field.** A compressed history: dominant approaches over time. Reference the taxonomy figure (Section~\ref{sec:taxonomy}) and timeline figure (Fig~\ref{fig:timeline}). 5–10 citations grouped chronologically.

**¶3 — Why now / why this survey.** What changed recently that motivates a new survey. Cite prior surveys explicitly and contrast scope: what they covered, what they missed, why a new lens is needed. 3–6 citations.

**¶4 — Survey structure (the lens).** Name your taxonomy axes, state your scope (in / out), and forecast the section structure. End with a contributions-style list:

```latex
\emph{First}, we ...
\emph{Second}, we ...
\emph{Third}, we ...
```

For a survey, "contributions" become "what this survey does" — namely, the taxonomy, the time-series of progress, and the synthesis of open challenges.

**¶5 — Reading order.** Brief paragraph telling readers how to traverse the paper.

**Anti-patterns:**
- "Many works have addressed this~\cite{a, b, c, d}" — prose without distinction.
- Not citing prior surveys.
- Promising sub-areas not delivered later.

## Background — `sections/background.tex`

**Length:** 3–4 `\paragraph{}` subsections (~600–1200 words). **Citations:** 8–15.

This section is the survey's pedagogical foundation. Define notation, recall the prerequisites, give the canonical formulation of the problem, and present the canonical baseline / first solution.

**Subsections to consider:**
- Problem definition with notation
- Canonical baseline formulation (e.g., recurrent / linear / classical)
- Evaluation conventions in the field
- Unifying mathematical framework if one exists

End the section by referencing the taxonomy figure: "In the rest of the survey, we organise the literature according to Figure~\ref{fig:taxonomy}."

**Anti-patterns:**
- Skipping background under the assumption the reader knows the field — surveys are read by people new to it.
- Notation that doesn't match later sections.

## Methods — `sections/methods.tex`

**Length:** 1200–2200 words. **Citations:** 35–60 here alone.

This is the survey's central section. Each branch of the taxonomy gets a `\paragraph{}` (or even a `\subsection{}` when it's large enough), in roughly the order shown in Figure~\ref{fig:taxonomy}.

**Per-branch structure:**
1. **Premise** (1 sentence): the architectural / theoretical commitment that defines this branch.
2. **Canonical works** (3–5 papers cited individually with prose distinguishing them).
3. **Refinements / extensions** (3–8 follow-up papers grouped 2–3 per claim).
4. **Limitations** (1–2 sentences acknowledging the open critique within this branch).

End with a comparison paragraph that ties the branch back to the taxonomy and the timeline.

**Subsections:** for a large branch (10+ key papers), use `\subsection{}` and split into smaller paragraphs.

**Tables:** in this section a "method × property" comparison table (see `04-layout-discipline.md`) is often valuable.

**Anti-patterns:**
- Chronological dump within a branch ("In 2019, X… In 2020, Y…").
- Branches that don't connect back to the taxonomy.
- Branches with no critique — every architectural commitment has trade-offs; surveys should name them.

## Discussion — `sections/discussion.tex`

**Length:** 3–5 `\paragraph{}` subsections (~800–1500 words). **Citations:** 10–18.

Discussion is the survey's *judgment*. It synthesises across the methods covered.

**Subsections to consider:**
- **Cross-cutting trends.** Patterns visible across branches (e.g., "all of patching, inversion, and decomposition are forms of inductive bias re-injection").
- **Empirical maturity.** What has been measured well, what hasn't.
- **Coverage matrix.** Reference Fig~\ref{fig:capability_matrix}; what does the matrix tell us?
- **Where the field is converging or diverging.**
- **Engineering vs. science gaps.**

**Anti-patterns:**
- Restating Methods without adding judgment.
- Avoiding controversy (e.g., refusing to acknowledge a debate that exists).

## Conclusion — `sections/conclusion.tex`

**Length:** 2–3 paragraphs (~400–700 words). **Citations:** 4–8.

**Structure:**

**¶1 — What the survey did.** In 4–5 sentences, summarise the taxonomy and the most important findings.

**¶2 — Open challenges.** 4–6 concrete unresolved questions, each named and accompanied by 1–3 citations of work that points toward them.

**¶3 — Outlook.** Where the field is likely heading. This is forecast, not fact — write it as such (using "may" / "is likely to" rather than "will").

**Anti-patterns:**
- Repeating the abstract.
- Vague open challenges ("future work will explore extensions").
- Predictions stated as facts.

## Related Work — `sections/related_work.tex`

**Length:** 1–2 paragraphs (~400–700 words). **Citations:** 5–12.

In a survey, "Related Work" specifically means **other surveys** on the same or adjacent topics. This is short and deliberate.

**Structure:**
- Cite each prior survey by name (`Wen et al.~\cite{wen2023survey}`), with prose stating its scope and how yours differs.
- 5–10 prior surveys.
- 1 paragraph at the end discussing tutorials, blog series, and book chapters that complement the surveys.

**Anti-patterns:**
- Confusing "Related Work" with the methodology survey (Methods).
- Including every paper instead of just other surveys.

## Cross-section discipline

A survey's promises are made in the Introduction:
- "We organise the field according to Figure~\ref{fig:taxonomy}" → Methods must follow that taxonomy exactly.
- "We argue X" → Discussion must argue X explicitly.
- "We identify N open challenges" → Conclusion must list N.

Notation introduced in Background must reappear in Methods. Figures cited in Introduction must be referenced again later. The timeline cited in Introduction should be referenced again in Discussion when discussing trends.

## Quick checklist

- [ ] Every section has `\section{}\label{sec:...}` and is referenced from at least one other section.
- [ ] Abstract: 4–8 cites; one paragraph; quantitative anchor (papers covered, time span).
- [ ] Introduction: 12–20 cites; 4–5 paragraphs; explicit "First / Second / Third" what-this-survey-does.
- [ ] Background: 8–15 cites; notation + canonical baseline + evaluation conventions.
- [ ] Methods: 35–60 cites; structured per taxonomy branch; per-branch premise / canon / extensions / limitations.
- [ ] Discussion: 10–18 cites; cross-cutting trends and judgment.
- [ ] Conclusion: 4–8 cites; summary / open challenges / outlook.
- [ ] Related Work: 5–12 cites; **other surveys**, not the methodology body.
- [ ] Notation consistent across sections.
- [ ] First-person plural ("we") throughout.
