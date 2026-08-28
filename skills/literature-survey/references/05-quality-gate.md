# Survey Quality Gate — Self-Check Before Delivery

## Why this exists

Even a thorough first pass produces a survey with one or two issues — citations that don't resolve, a figure that's too small, a section caption that's a fragment. This checklist runs **after** drafting and recompiling, **before** telling the user "it's done". If any item fails, return to the relevant reference.

The gate is bright-line. Do not soften the targets to ship.

## Hard gates (must pass)

### G1 · PDF compiles cleanly

```bash
cd output/literature-survey/<slug>/survey_paper
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
bibtex main >/dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1

test -s main.pdf || echo "FAIL: main.pdf missing or empty"
echo "undefined cites: $(grep -c 'Citation .* undefined' main.log) (must be 0)"
echo "undefined refs:  $(grep -c 'Reference .* undefined' main.log) (must be 0)"

# Overfull boxes = content spilling past the margin (the "elements run off the
# page / overlap" complaint). List the worst offenders with how far they overrun:
grep 'Overfull \\hbox' main.log | grep -oE '\([0-9.]+pt too wide\)' | sort -t'(' -k2 -rn | head
echo "overfull boxes:  $(grep -c 'Overfull \\hbox' main.log) (target 0)"
```

**Overfull is a remediation trigger, not a tolerated warning** (unattended runs have no human to eyeball the PDF). Any overfull box > ~2pt means something visibly crosses the margin — fix it, don't ship it:

- **Figure/table overrun** → it isn't wrapped per `02`/`04`. Wrap TikZ in `\resizebox{\linewidth}{!}{…}`; add `width=\linewidth` to the include; shrink/`tabularx` the table. This alone clears almost all overfull boxes.
- **A long unbreakable token** (URL, code, long math) → `\sloppy`, `\url{}`, or manual break.
- Recompile and re-grep until the count is 0 (a stray ≤ 1–2pt box from microtype is acceptable; anything larger is not).

### G2 · Bibliography size

```bash
grep -c "^@" bibliography.bib    # must be ≥ 60 (100+ recommended)
```

No fabricated entries:

```bash
# Every entry should have a url= field that the agent fetched in this session
grep -c "url = {" bibliography.bib   # should be close to total entry count
```

If many entries lack `url=`, you may have leaked memory-sourced entries; audit them.

### G2.5 · No orphan bib entries

A bib that contains entries never `\cite{}`-d in the prose is **padding**.
The common failure mode is reaching G2's count by appending famous papers
from adjacent fields (LLM, vision, foundational deep learning, …) that
the survey never uses. This gate detects orphans; **detection is not
termination — it triggers remediation**.

```bash
# every key listed in bibliography.bib must appear in at least one \cite,
# \citep, \citet, etc. in main.tex or sections/*.tex
bib_keys=$(grep -oE '^@[a-z]+\{[^,]+,' bibliography.bib \
           | sed -E 's/^@[a-z]+\{//; s/,$//' | sort -u)
cite_keys=$(grep -hoE '\\cite[a-z]*\{[^}]+\}' main.tex sections/*.tex 2>/dev/null \
            | grep -oE '\{[^}]+\}' | tr ',' '\n' | tr -d '{} \n' \
            | sort -u | sed '/^$/d')
orphans=$(comm -23 <(echo "$bib_keys") <(echo "$cite_keys"))
orphan_count=$(echo "$orphans" | grep -c .)
echo "orphan bib entries: $orphan_count (must be 0)"
test "$orphan_count" -eq 0 || {
  echo "ACTION REQUIRED · $orphan_count orphans (first 10):"
  echo "$orphans" | head -10
}
```

**This is a remediation trigger, not a task-failure signal.** If
`orphan_count > 0`, DO NOT exit the step or report failure. Loop on
remediation until orphans reach 0, in this priority order:

1. **Cite them in prose** (preferred). Most orphans are real on-topic
   papers you researched but skipped writing about. Go back to
   `03-survey-section-playbook.md` and add each to the appropriate
   section with a one-to-three-sentence treatment. A survey *is* the
   argument that every cited paper deserves citation. Re-run the gate.
2. **Prune + lower scope.** If after honest effort you cannot extend prose
   to cover the orphans, lower the target toward the 60 floor (100+ recommended)
   and prune the bib to entries you actually cite. Update the abstract
   to reflect the narrower scope. Re-run the gate.
3. **Prune + honest shortfall report.** If even the focused target
   cannot be honestly reached, prune to the cited entries and add a
   note to the introduction / abstract: "Scope limited to N entries
   due to limited on-topic literature; expanded coverage left to
   future work." Then re-run the gate. Never quietly pad — but a
   smaller, honest bib is acceptable output.

Only after `orphan_count == 0` may you proceed past this gate.

### G2.6 · Temporal coverage matches the stated intent

If the topic named a year or recency window (the §0 *recency-led* posture in `01-bibliography-expansion.md`), the bib must actually contain real entries from it. This is the gate that catches "asked for 2026, delivered all 2024".

```bash
# Histogram the bib by year — eyeball it against the recorded posture.
grep -oE 'year[[:space:]]*=[[:space:]]*[{"]?[[:space:]]*(19|20)[0-9]{2}' bibliography.bib \
  | grep -oE '(19|20)[0-9]{2}' | sort | uniq -c
```

There is **no universal threshold** — judge against the posture in `.bib_progress.txt`:

- **Recency-led** (topic named year Y / "latest"): the bulk of entries fall in the window, and there is a meaningful count *from Y itself*. Zero entries from the named year is an automatic fail; a handful is a warning — search harder before shipping.
- **Timeline-spanning / balanced**: the bib reaches the last ~6–12 months, not stopping 2 years short.

**Detection is a remediation trigger, not a stop.** If coverage doesn't match intent, loop:

1. **Search harder with date filters.** Re-run the §3.5 date-sorted arXiv queries with the explicit year; the newest papers are almost never in the model's prior knowledge, so relevance-ranked search alone keeps missing them. Add the real entries, recompile, re-check.
2. **Honest shortfall note** — only if, after genuine date-filtered searching, the literature in that window is truly thin: add one sentence to the introduction/abstract stating the actual coverage. Never silently substitute old papers for the requested recent ones.

### G3 · Page count

```bash
pdfinfo main.pdf | grep Pages    # must be ≥ 6 (8+ recommended)
```

A survey under 5 pages is a digest, not a survey. Re-scope or expand.

### G4 · Cite count across sections

```bash
total=0
for f in sections/*.tex; do
  c=$(grep -o "\\\\cite{" "$f" | wc -l)
  total=$((total + c))
done
echo "TOTAL \\cite{} markers: $total"   # must be ≥ 60
```

Per-section minimums:

| Section | Min `\cite{` count |
|---|---|
| abstract | 3 |
| introduction | 10 |
| background | 6 |
| methods | 25 |
| discussion | 6 |
| conclusion | 3 |
| related_work | 5 |

Methods carries most of the load — that is correct for a survey.

### G5 · Required figures present

```bash
grep -rh "begin{figure" sections/ | wc -l    # must be ≥ 6
```

Specifically, the survey must have:

- ≥ 1 taxonomy / classification diagram (TikZ-style figure tag in Background or Methods)
- ≥ 1 chronological timeline (matplotlib-style figure tag, typically in Introduction)
- ≥ 1 coverage / capability matrix (heatmap-style figure tag, typically in Discussion)

```bash
grep -l "fig:taxonomy" sections/*.tex     # must list the section that owns the taxonomy fig
grep -l "fig:timeline" sections/*.tex
grep -l "fig:capability\|fig:coverage" sections/*.tex
```

(These three are the *common* survey figures, not a mandatory trio — per `02`'s design process, let the topic decide. The bar is "every figure makes a claim visible", not "fill these slots".)

### G5.5 · No template leakage; Nature/Science look

The figures must be designed for this survey, not copied from the playbook's worked examples (a real run once shipped time-series leaves — `Informer`, `PatchTST` — inside an LLM survey).

```bash
# Sample/example tokens that must NOT appear unless the topic genuinely is time-series:
grep -rIE "Informer|Autoformer|FEDformer|PatchTST|iTransformer|Moirai|TimeGPT|Time-Series Forecasting" \
  sections/ figures/ *.tex 2>/dev/null | grep -v "%"   # expect empty for non-TS topics
# Figures should be sans-serif (Nature), not the default serif:
grep -rn 'font.family.*serif' figures/*.py 2>/dev/null   # expect empty (use the sans Nature preamble)
# Taxonomies must be forest-based (auto-spaced), not hand-tuned overlapping trees:
grep -rn 'sibling distance' sections/*.tex 2>/dev/null    # expect empty
```

If any fires: redraw the offending figure for *this* topic with the Nature language in `02` (sans-serif, Wong palette, despined, panel labels, finding-first caption). This is a remediation trigger — fix and re-run, don't ship a leaked or generic-looking figure.

### G6 · Comparison table present

```bash
grep -rh "begin{table" sections/ | wc -l    # must be ≥ 1
```

A survey should have at least one method-comparison table (often spanning the column with `\begin{table*}`).

### G7 · Disclosure footnote correct

The `\author{}` block in `main.tex` carries a `\thanks` footnote with the always-on human-review clause:

```bash
grep -E "Human review|human review" main.tex      # must match
```

Surveys do **not** include the simulated clause:

```bash
grep -i "simulated" main.tex sections/abstract.tex   # should be empty
```

If your survey somehow ended up with the simulated clause, remove it — surveys don't carry numerical experiments to simulate.

### G8 · Cross-reference integrity

```bash
grep -ohE '\\label\{[^}]+\}' sections/*.tex | sed 's/.*\\label{//;s/}.*//' | sort -u > /tmp/labels
grep -ohE '\\ref\{[^}]+\}'   sections/*.tex | sed 's/.*\\ref{//;s/}.*//'    | sort -u > /tmp/refs
diff <(comm -23 /tmp/labels /tmp/refs) <(echo)    # labels with no ref → bad
diff <(comm -13 /tmp/labels /tmp/refs) <(echo)    # refs with no label → bad
```

## Soft gates (should pass)

### S1 · Notation consistency

Skim all sections for the same concept under different symbols. Pick one and globally replace.

### S2 · Caption quality

Read each caption alone (cover the figure/table). If it doesn't convey what's shown, lengthen.

### S3 · Anti-pattern sweep

```bash
# Marketing prose
grep -E "comprehensive overview|extensive review|cutting-edge|state-of-the-art" sections/*.tex | head
# These are not always wrong, but if they're frequent the prose is fluffy.

grep -E "the authors|This paper presents|This survey provides" sections/*.tex   # should be empty / minimal

# Citation dumps (≥ 6 keys in one \cite{})
grep -oE '\\cite\{[^}]+\}' sections/*.tex | awk -F, '{print NF}' | sort -nr | head -3
# top number should be ≤ 5
```

### S4 · Prior surveys actually cited

```bash
# Open Related Work; check it cites at least 5 prior surveys by name
wc -l sections/related_work.tex
```

A survey that does not engage with prior surveys is rude (and incomplete).

### S5 · Figures look right

Unattended runs can't rely on a human opening the PDF, so this is now two layers:

**Machine check (always):** G1's overfull list above must be empty (or ≤ ~2pt). A figure that overruns the margin shows up there; a figure correctly wrapped in `\resizebox`/`width=\linewidth` cannot. If you have `pdftoppm`/ImageMagick, rasterize the figure pages (`pdftoppm -png -f <p> -l <p> main.pdf /tmp/chk`) and confirm no glyphs touch the page edge.

**Taste check (when a reviewer is available):** open `main.pdf` and verify:
- Taxonomy figure: leaves are readable (not shrunk to illegibility by `\resizebox` — if so, fold the tree); fits cleanly within the column.
- Timeline: lane structure visible; labels not overlapping.
- Coverage matrix: cell colors readable; legend explained.
- Architecture figures (if any): consistent style with the taxonomy.

## Final report format

When all gates pass:

```
Survey ready: output/literature-survey/<slug>/survey_paper/main.pdf

Stats:
  Pages:        9
  Bibliography: 112 entries (all url-backed)
  \cite{} total: 78 across 7 sections
  Figures:      8 (1 taxonomy, 1 timeline, 1 coverage matrix, 3 architecture, 2 trend)
  Tables:       2 (capability comparison, paradigm summary)
  Compile:      0 undefined citations, 0 undefined refs, 0 overfull boxes
  Coverage:     recency-led; 41/58 entries in 2026 window (posture honoured)

Quality gate: PASSED (G1–G8 hard incl. G2.6 temporal coverage, S1–S5 soft).
```

If you cannot pass G1–G4 without compromising honesty, **say so explicitly**:

> "Bibliography stalled at 52 entries — could not find more high-quality citations on this niche topic via WebFetch. Page count 5. The survey is delivery-quality at this scope; raising to 100 cites would require padding with low-relevance entries that hurt readability."

That's a legitimate stop. Fabricating entries to clear the gate is not.

## Quick checklist

- [ ] G1 compile clean; 0 overfull boxes (remediate, don't tolerate)
- [ ] G2 bibliography ≥ 60 (100+ recommended); every entry has `url=`
- [ ] G2.6 temporal coverage matches the §0 posture (recency-led topic → real entries from the named year)
- [ ] G3 PDF ≥ 6 pages
- [ ] G4 `\cite{}` total ≥ 60; per-section minimums hit
- [ ] G5 ≥ 6 figures; taxonomy + timeline + coverage matrix all present
- [ ] G6 ≥ 1 comparison table
- [ ] G7 `\thanks` carries human-review clause; no simulated clause
- [ ] G8 every label is referenced
- [ ] S1–S5 soft gates reviewed
- [ ] Visual sanity check on the rendered PDF
- [ ] Honest report — don't pad to clear gates
