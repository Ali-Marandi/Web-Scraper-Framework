---
name: literature-survey
description: Use when the user wants a comprehensive literature survey on a specific research topic. Outputs a complete PDF survey (6–20 pages, 60+ real citations, 100+ recommended) with LaTeX source, taxonomy figures, and a classified literature table. Single-stage, no Python runtime.
---

# Literature Survey

## Overview

End-to-end literature survey builder. **Single stage, full quality from the start.** The agent (Claude Code / Cursor / Aider / Codex / …) does the entire build using its own tools (WebFetch, WebSearch, Write, Bash). This SKILL is procedure + reference playbooks + LaTeX template — no Python runtime, no LLM SDK.

The substantive work is decomposed into reference playbooks under `references/`:

| Reference | Topic |
|---|---|
| `references/00-incremental-execution.md` | how to actually do this without losing work: batch sizes, persistence, resume — **read first** |
| `references/01-bibliography-expansion.md` | grow `bibliography.bib` to 60+ real entries (100+ recommended) via WebFetch (no memory) |
| `references/02-survey-figures.md` | taxonomy / timeline / coverage-matrix / area-map figures |
| `references/03-survey-section-playbook.md` | per-section structure for survey-shaped papers |
| `references/04-layout-discipline.md` | tables, figures, floats, cross-refs, author + disclosure footnote |
| `references/05-quality-gate.md` | self-check before delivery |

**Read the relevant reference _before_ writing, not after.** The full pass does not fit in a single turn — `references/00-incremental-execution.md` is the only execution mode that completes.

## When to Use

- User asks for a "survey" / "review" on a specific topic.
- User has a research topic and wants a structured map of the field with citations.
- User needs background reading curated for a thesis chapter or grant section.

## When NOT to Use

- User wants original research with experiments → `paper-writer`.
- User wants only an outline / topic exploration → `research-explorer`.
- User wants experiment code → `experiment-suite`.
- Topic is too broad (e.g., "all of AI") — narrow it before starting.

## Workflow

### Step 1 — Understand the topic and scope

Confirm with the user:

- **Topic** — specific research area (e.g., "federated learning in healthcare"). If too broad, narrow it first.
- **Scope** — broad survey of a field vs. focused review of a sub-area.
- **Citation budget** — minimum 60 unique entries; aim for 100+ (push higher for a broad survey).
- **Language** — default Chinese in conversation; the LaTeX paper is English unless requested otherwise.

Always tell the user that human review by a domain expert is recommended before publication or production use.

### Step 2 — Set up the run directory

```bash
TOPIC="<topic>"
SLUG=$(python3 -c "import re,hashlib,sys; t=sys.argv[1]; n=re.sub(r'[\\s_]+','-',re.sub(r'[^\\w\\s-]','',t.lower().strip())).strip('-')[:40].rstrip('-'); h=hashlib.sha1(t.encode()).hexdigest()[:8]; print(f'{n}-{h}')" "$TOPIC")
TS=$(date +%Y-%m-%d_%H%M%S)
RUN=output/literature-survey/$SLUG/$TS/survey_paper

mkdir -p "$RUN/sections" "$RUN/figures"
cp -r literature-survey/templates/survey/. "$RUN/"
ln -sfn "$TS" "output/literature-survey/$SLUG/latest"
```

In commands below `$RUN` = `output/literature-survey/<slug>/latest/survey_paper`.

### Step 3 — Build the survey (REQUIRED — this is the whole job)

Open `references/00-incremental-execution.md` first. Then carry out the five tracks below across many turns, persisting state to `$RUN/` after every batch.

#### 3.1 Bibliography — 60+ real entries (100+ recommended)

**Open:** `references/01-bibliography-expansion.md`.

**First (§0 of that reference): read the topic's temporal/scope intent and pick a search posture.** If the topic names a year or says "latest/recent" (e.g. "OpenSource LLM **2026**"), go *recency-led* — date-sorted arXiv queries carrying the explicit year, canon only as context. Otherwise span the timeline. This is what prevents "asked for 2026, got all 2024".

Then plan **12–20** query angles, weighted by the posture. For each angle, use **AMiner academic search first, web search as supplement**:

- **AMiner `search_papers`** — Use this FIRST for every query angle. It returns
  papers with structured metadata (title, authors, year, venue, DOI, citations,
  abstract) that is far more reliable than web-scraped results. Example:
  `search_papers(query="federated learning survey", max_results=20, sort_by_citation=true)`.
- **AMiner `get_paper_details`** — For key papers, fetch full details (abstract,
  citations, references) by their AMiner IDs.
- **`web_search`** — Use when AMiner returns insufficient results, or for
  non-academic sources (blogs, benchmarks, datasets, tool documentation).

For each kept candidate: extract canonical title/authors/year/venue/url/citations
from the AMiner response directly. For web-search-only results, WebFetch the
abstract URL to extract metadata. Append a BibTeX entry to
`$RUN/bibliography.bib`. **Every entry must originate from a URL fetched in this
session or from an AMiner search result.** Memory entries forbidden.

**Hard stop:** do not draft prose until `grep -c "^@" $RUN/bibliography.bib` ≥ 60 (aim for 100+).

#### 3.2 Figures — 6–10 survey-shaped

**Open:** `references/02-survey-figures.md`.

A survey is defined by how well it organises a field; figures carry that organisation:

- 1 taxonomy / classification diagram (TikZ hierarchy)
- 1 chronological timeline of major works
- 1 area / capability matrix (coverage heatmap)
- 1–2 representative architecture / mechanism diagrams
- 1–2 quantitative trend plots (matplotlib publication style)
- Optional: citation network, paradigm comparison

Save each into `$RUN/figures/` with reproducible source alongside.

#### 3.3 Sections — survey-shaped prose

**Open:** `references/03-survey-section-playbook.md`.

Survey sections differ in shape from research-paper sections. Order: introduction → background → methods (themed survey) → discussion → conclusion → related work → **abstract last**.

#### 3.4 Layout discipline

**Open:** `references/04-layout-discipline.md`.

Wrap every table in `\begin{table}[!t]` with booktabs; every figure in `\begin{figure}[!t]`. Use `~\cite{}` and `~\ref{}`. Set `\author{AI4S Agent}` with a `\thanks` footnote that **always** recommends human review. Surveys carry no simulated numerical experiments, so do **not** include a simulated clause.

#### 3.5 Compile + quality gate

```bash
cd "$RUN"
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

**Open:** `references/05-quality-gate.md`. Survey-specific targets: ≥ 60 bib entries (100+ recommended), ≥ 6 pages, ≥ 1 taxonomy figure, ≥ 1 timeline.

If a gate cannot honestly be met (e.g., the field is genuinely small), say so explicitly. Do not pad.

### Step 4 — Deliver

Report:

1. `output/literature-survey/<slug>/latest/survey_paper/main.pdf`
2. `output/literature-survey/<slug>/latest/survey_paper/` — complete LaTeX project (reproducible)
3. `output/literature-survey/<slug>/latest/literature_table.md` — classified literature table (write this alongside the bib build)
4. Stats per the report format in `references/05-quality-gate.md`.

## Cross-skill data flow (path convention)

A downstream skill (e.g., `paper-writer`) computing the same slug for the same topic will look here:

- `output/literature-survey/<slug>/latest/survey_paper/bibliography.bib` — bib starting point.

## Important rules

- **No LLM SDK in this skill.** No `import anthropic` / `import openai`. The skill is SKILL.md + references + LaTeX template only.
- **No fabricated citations.** Every BibTeX entry must trace back to a URL fetched this session. Real or weaker claim — never fake reference.
- **Honest stop > padding.** If the field is too small for 60 real citations, say so to the user instead of inventing entries.
- **Survey scope** is 6–20 pages with 60–150 references (100+ recommended). For longer or shorter formats, adjust scope explicitly with the user up front.
