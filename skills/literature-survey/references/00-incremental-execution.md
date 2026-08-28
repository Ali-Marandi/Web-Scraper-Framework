# Incremental Execution — How a Survey Actually Gets Built

## Why this exists

A survey with 100+ references and 7 multi-paragraph sections does not fit into a single LLM tool call. WebSearch returns ~10 useful candidates per query, not 100. A single message can write one solid section, not seven. If you treat the build as "do it all in one shot", you will hit context limits, fail mid-task, and have nothing to recover.

This reference defines the only execution mode that works: **incremental, file-persisted, resumable**. Every other reference (`01`–`05`) describes *what* to produce; this one describes *how* to produce it without losing work.

## The three invariants

### Invariant 1 — Filesystem is the source of truth

Every intermediate result is written to disk **immediately**. A new BibTeX entry is appended to `bibliography.bib` the moment it is extracted from a WebFetch result, not after the batch finishes. A rewritten section is Written to `sections/<name>.tex` the moment it is drafted, not after all seven are drafted. A generated figure is committed to `figures/fig_NN_<name>.pdf` and the matching script is saved alongside.

If the conversation context fills, the agent crashes, or the user pivots, **the files survive**. Resumption reads the files and continues.

### Invariant 2 — Progress is observable via filesystem, not memory

```bash
cd output/literature-survey/<slug>/survey_paper
grep -c "^@" bibliography.bib                                # bib entries so far
ls figures/*.pdf | wc -l                                     # figures so far
for f in sections/*.tex; do
  echo "$(basename "$f"): $(wc -w < "$f") words"
done                                                          # per-section drafted size
```

If the count does not match the target, do another batch. Don't rely on remembering what you did.

### Invariant 3 — Each batch is small enough to succeed, atomic enough to retry

A "batch" is one WebSearch+WebFetch cycle, or one section's prose, or one figure's script+render. Failure → redo just that batch. Success → write to disk and move on.

## Batch sizes that work

| Operation | Batch size per turn | Total batches | Persistence |
|---|---|---|---|
| Bibliography expansion | 1 WebSearch query → triage → ~5–15 WebFetch'd entries | 10–15 batches to reach 100+ | Append to `bibliography.bib` after each |
| Section drafting | 1 section per turn | 7 batches total | Write each `sections/<name>.tex` immediately |
| Figure generation | 1 figure per turn (TikZ inline or matplotlib script + render) | 6–10 batches | Save script + render alongside |
| Compile + check | 1 cycle after major artefact | Several | `main.log` + grep |

A turn that tries to do 5 sections produces shallow prose and probably truncates. A turn that tries to "WebSearch all 15 queries at once" hits tool budgets. One per turn is the rhythm.

## Bibliography expansion — incremental loop

```
read existing bibliography.bib
n_entries = grep -c "^@" bibliography.bib
target = 110                                # aim above the 100 recommended floor (hard gate 60)

query_plan = [...]                          # 12–20 angles from 01-bibliography-expansion.md
already_run = read_state(.bib_progress)     # set of executed query strings
seen_urls   = extract_urls_from_bib()       # already-cited URLs

for q in query_plan:
    if q in already_run: continue
    candidates = WebSearch(q)               # ~5–15 hits
    for c in triage(candidates):            # filter by venue, dedup
        if c.url in seen_urls: continue
        meta = WebFetch(c.url)              # canonical title/authors/year/venue
        if meta is bad: continue
        append_bibtex(meta, bibliography.bib)
        seen_urls.add(c.url)
    append(.bib_progress, q)                # persist that query was run
    if grep -c "^@" bibliography.bib >= target: break
```

In Claude Code execution this is **one WebSearch + one or more WebFetch + Edit/Write per turn** for ~15 turns. If turn 7 fails, turn 8 reads the progress file, sees queries 1–6 are done, restarts from 7. **No work lost.**

## Section drafting — one section per turn

Order: introduction → background → methods (themed survey) → discussion → conclusion → related work → abstract.

For each section:

1. Read `references/03-survey-section-playbook.md` rules for that section (open it fresh — don't trust cached recollection).
2. Read `bibliography.bib` and pick relevant keys for this section.
3. Draft the section in one go (one section is 600–1500 words for a survey; a single LLM turn can comfortably produce that).
4. **Immediately** Write the result to `sections/<name>.tex`.
5. Compile (`pdflatex` once + `bibtex` + `pdflatex` ×2). Check `main.log` for new undefined citations.
6. Fix errors before moving to the next section.

### "Abstract last" rule

The abstract names the field's structure as you have organised it. Until you have actually organised it (in Background through Discussion), you can't write a good abstract. Drafting it last takes 5 minutes; drafting it first wastes 30.

## Figure generation — one figure per turn

For each figure (6–10 total):

1. Open `references/02-survey-figures.md` for the family that fits this figure (taxonomy / timeline / matrix / architecture / quantitative).
2. Decide what the figure *answers* in the survey. That answer becomes the caption.
3. Write the figure (TikZ inline in the relevant `sections/*.tex`, or a `figures/make_fig_NN_*.py` script).
4. Render (TikZ compiles via main.tex; matplotlib via `cd figures && python make_fig_NN_*.py`).
5. Verify the PDF exists and is non-trivial.
6. Reference it from the appropriate section with a caption.
7. Recompile and check.

## Recovery — what to do when a session resumes mid-task

```bash
cd output/literature-survey/<slug>/survey_paper

grep -c "^@" bibliography.bib                       # bib progress
cat .bib_progress.txt 2>/dev/null | wc -l           # queries executed
for f in sections/*.tex; do
  echo "$(basename "$f"): $(wc -w < "$f") words"
done                                                 # which sections drafted
ls figures/*.pdf 2>/dev/null
ls -la main.pdf
grep -c "Citation .* undefined" main.log
```

Resume the sub-step that's incomplete. **Never** redo work that's already on disk; only fill in what's missing.

## Checkpoint files

Three small bookkeeping files in the survey paper directory:

- `.bib_progress.txt` — one line per executed query string
- `.section_progress.txt` — one line per drafted section
- `.figure_progress.txt` — one line per generated figure id

```bash
echo "transformer time series Informer Autoformer" >> .bib_progress.txt
```

## Atomic write rule

Use Write/Edit tools (atomic). Never stream partial content via `python -c "open(...).write(...)"`. Don't parallelize bib appends — they must serialise.

## Sanity check before delivery

```bash
ls -la sections/                                  # all 7 .tex files non-trivial?
ls -la figures/*.pdf                              # 6+ figure PDFs present?
test -s main.pdf
grep -c "^@" bibliography.bib                     # ≥ 60 (100+ recommended)
total=0; for f in sections/*.tex; do
  total=$((total + $(grep -o "\\\\cite{" "$f" | wc -l)))
done
echo "TOTAL cites: $total"                         # ≥ 60 across all sections
```

## Quick checklist

- [ ] Bibliography assembled in **12+ small WebSearch+WebFetch batches**, one query per turn
- [ ] Sections written **one per turn**, abstract last
- [ ] Figures generated **one per turn**
- [ ] Three checkpoint files maintained
- [ ] Compile+verify after each major artefact
- [ ] Never tried to "do it all in one turn"
