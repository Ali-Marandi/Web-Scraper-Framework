# Bibliography Expansion for a Survey — 60+ Real Entries (100+ recommended) via WebFetch

## Why this exists

A survey paper is largely *defined* by its bibliography: the breadth of coverage, how recent the most-recent works are, and how foundational the oldest works are determine whether the survey is useful or junk. There is no Python-side fetching: the entire bibliography is built by the orchestrating agent using the **WebSearch** and **WebFetch** tools, in one continuous pass before drafting begins.

**Hard minimum:** **60 unique, real, properly-attributed entries** before drafting prose; **100+ recommended**. Aim for ~120 as headroom for organic citation needs.

## The non-negotiable rule

> **Every BibTeX entry must originate from a URL the agent fetched in this session.** No entries from training-data memory. No "I know this paper exists" shortcuts. If it's not backed by a fetched URL, it does not go in the bib.

For surveys this is especially important: a survey is judged on how completely and accurately it maps a field. A fabricated entry (wrong author, wrong year, hallucinated paper) ends the survey's usefulness instantly.

## Tools and when

| Tool | Use for | Output |
|---|---|---|
| **WebSearch** | Discovering papers per query angle | List of titles + URLs + snippets |
| **WebFetch** | Pulling canonical metadata from a discovered URL | Page content; you parse title/authors/year/venue |

Pattern: WebSearch first to find candidates, then WebFetch the most promising URLs.

Reliable URL templates:
- arXiv abstract: `https://arxiv.org/abs/<id>`
- arXiv API (bulk): `http://export.arxiv.org/api/query?search_query=...&max_results=N` (Atom XML)
- Semantic Scholar: `https://www.semanticscholar.org/paper/<slug>/<id>` and the `https://api.semanticscholar.org/graph/v1/paper/...` API (JSON)
- OpenReview: `https://openreview.net/forum?id=<id>`
- NeurIPS proceedings: `https://papers.nips.cc/paper_files/paper/<year>/...`

## Process

### 0. Read the topic's scope & temporal intent FIRST (adaptive search)

Before planning a single query, read the user's topic the way a librarian would and pick a **search posture**. This is the step that was missing when a topic like "OpenSource LLM **2026**" came back with zero 2026 papers — the year in the topic *is* an instruction, not decoration. There is no fixed rule here; you infer the posture from the signals, then let it shape every later query.

| Signal in the topic / request | Posture | What it means for search |
|---|---|---|
| Names a specific recent/current/future year ("… 2026"), or says "latest / recent / emerging / state of the art / this year / past 12 months" | **Recency-led** | The named timeframe is a **hard filter**. Most queries (≳ 70%) carry that year/range and lead with date-sorted sources (see §3.5). Canon/foundational works appear only as *supporting context* (≤ ~30%), explicitly framed as "prior to the surveyed window". **Do not draft until the bib actually contains real entries from the named window.** |
| Says "history / evolution / development / foundations / comprehensive / from X to Y" | **Timeline-spanning** | Span earliest seminal work → newest. The "cover the canon" guidance below applies in full. |
| No temporal signal at all | **Balanced (default)** | Mix foundational + recent, but always include the **most recent 12 months** so the survey isn't stale. |

Write the chosen posture and the parsed timeframe as the first line of `.bib_progress.txt`, e.g. `POSTURE: recency-led | window: 2025-09 .. now | canon cap: 30%`. Every later query-planning and gate decision refers back to it.

> **Why the old behaviour failed:** the model reaches for the famous papers it already knows (all 2–3 years old), and the "span the timeline / a bib that's all-2023+ is a snapshot" guidance below *reinforced* that pull. Under a recency-led posture that guidance is **suspended** — there, an all-old bib is the failure, not the goal.

### 1. Start with an empty bibliography

`$RUN/bibliography.bib` starts empty after Step 2 of the skill. Build it up to ≥ 60 entries (100+ recommended) below before drafting any prose. Optionally also maintain a `$RUN/papers.json` index alongside.

### 2. Plan a query expansion (12–20 angles)

Decompose the topic into angles spanning multiple axes simultaneously. For a survey, breadth matters more than for a research paper.

Recommended angle types (pick 12–20 across these):

- **Foundational classics**: pre-2015 / pre-2010 papers that defined the field.
- **Method families**: each named architectural / technical family (one query per family).
- **Application domains**: each major domain (one query per domain).
- **Adjacent paradigms**: rival or sibling families (e.g., for a Transformer survey: linear models, MLP-only, state-space).
- **Empirical & benchmark studies**: dataset and benchmark papers, evaluation studies.
- **Theoretical analyses**: convergence, expressivity, identifiability, scaling laws.
- **Surveys**: prior surveys / reviews on the same or adjacent topics.
- **Recent advances**: queries carrying the **explicit year/window from §0** (not a placeholder) to capture the frontier. Under a *recency-led* posture this is the majority of your angles, not one of twenty.
- **Open problems / critiques**: papers that argue against received wisdom.
- **Tooling / libraries**: framework papers (when relevant to the field).

Track the plan in `.bib_progress.txt`.

### 3. Per query: WebSearch → triage → WebFetch → extract → append

For each query in the plan:

1. **WebSearch** with the query string. Result: list of links + titles + snippets.
2. **Triage** — for each candidate, decide whether to keep:
   - Keep peer-reviewed venue papers and authoritative arXiv preprints.
   - Skip blog posts, marketing pages, vendor pages, Medium articles, lecture slides.
   - Deduplicate against entries already in `bibliography.bib`.
3. **WebFetch** the abstract URL to obtain canonical metadata (title, full author list, year, venue).
4. **Append** the BibTeX entry to `bibliography.bib` immediately, and append the query to `.bib_progress.txt`.

For arXiv specifically, the export.arxiv.org Atom endpoint returns 10–30 entries from one fetch — preferred for bulk loading.

### 3.5. Date-filtered search (use whenever recency matters)

A plain WebSearch ranks by relevance/popularity, which skews toward *older, more-cited* papers — exactly why a "2026" topic returns 2023–2024 results. When the posture from §0 is **recency-led** (or balanced, for the recent-12-months slice), don't rely on the model's prior knowledge; **fetch a date-sorted feed and read what's actually new**:

- **arXiv, sorted by date (primary recency tool).** The Atom API takes `sortBy=submittedDate&sortOrder=descending` — the top results are the newest papers, regardless of citation count:

  ```
  https://export.arxiv.org/api/query?search_query=all:%22open%20source%20large%20language%20model%22&sortBy=submittedDate&sortOrder=descending&max_results=40
  ```

  WebFetch this URL (use **https** — the plain-`http` host can return empty through some proxies), then keep entries whose `<published>` year falls inside the §0 window. Repeat per sub-topic (architectures, alignment, evaluation, …) so each theme has fresh coverage. (Verified: a date-sorted query like this returns current-month arXiv papers, exactly the frontier a relevance-ranked search misses.)
- **WebSearch with the year embedded and time-scoped phrasing.** Put the explicit year in the query and add words that bias toward new work: `open source LLM 2026 release`, `... announced 2026`, `... arxiv 2026`. Avoid model-name lists (`Llama Mistral Qwen …`) under a recency-led posture — they pull the search back to the known canon.
- **Cross-check the frontier you can't know.** Your training data does not contain the newest papers. Treat any "I already know the key 2026 papers" impulse as a red flag: if it's not from a URL fetched this session via a date-sorted query, it isn't recent enough to trust.

Record in `.bib_progress.txt` which queries were date-sorted, so the §0 window is auditable.

### 4. BibTeX entry format

```bibtex
@inproceedings{lastname2023key,
  title={Exact title from the source page},
  author={Lastname, Firstname and Other, Author},
  booktitle={Venue Name},
  year={2023},
  url={https://arxiv.org/abs/2305.12345},
}

@article{lastname2024arxiv,
  title={Exact title from the source page},
  author={Lastname, Firstname},
  journal={arXiv preprint arXiv:2401.12345},
  year={2024},
  url={https://arxiv.org/abs/2401.12345},
}
```

Always include `url=` so a reviewer can audit. Use `@inproceedings` with `booktitle={...}` for conferences, `@article` with `journal={...}` for journals. arXiv preprints are `@article` with `journal={arXiv preprint arXiv:<id>}`.

**bib_key convention:** `<firstauthorlastname><year><firstmeaningfulword>`, lowercase, alphanumeric. Disambiguate collisions with a single suffix letter.

**Acronyms in titles**: wrap with `{}` to preserve case — `{T}ransformers`, `{FED}former`, `{N-BEATS}`. Escape `&`, `%`, `$`, `_`, `#`.

### 5. Sync to `papers.json` (recommended)

Append a JSON record per BibTeX entry to `papers.json` so the manifest stays consistent. Minimum fields: `title`, `authors`, `year`, `bib_key`, `url`, `dimension` (which query angle discovered it).

The `dimension` field powers the literature table later: papers grouped by sub-area become a classified inventory the survey reader can use as a starting point.

### 6. Validate before drafting

```bash
cd output/literature-survey/<slug>/survey_paper
grep -c "^@" bibliography.bib    # should be ≥ 60 (100+ recommended)
```

Run a `pdflatex + bibtex + pdflatex × 2` pass on the template `main.tex` with the new bib. If `main.bbl` doesn't list everything you expect, the bib has a syntax problem; fix before drafting prose.

### 7. As you draft, audit cite resolution

After every section, recompile and grep `main.log` for `Citation .* undefined`. Each undefined citation is either a typo or a missing bib entry. Fix immediately.

## Survey-specific bib quality

A survey bibliography should also satisfy (read these **through the §0 posture** — the timeline rule below is for *timeline-spanning / balanced* surveys; a *recency-led* survey deliberately concentrates in its window):

- **Span the timeline** *(timeline-spanning / balanced postures)*. Papers should range from the earliest seminal work to the last 6 months. A bib that's all 2023+ is a snapshot, not a survey. **Under a recency-led posture this is inverted:** the bib should concentrate in the named window, with older works cited only as the lineage that leads up to it.
- **Cover the canon.** Every named technique in your taxonomy should be cited via its primary source — the paper that introduced it.
- **Include critiques.** If the field has a debate (e.g., "are X effective?"), cite both sides; a one-sided survey is a position paper.
- **Cite prior surveys.** Every prior survey on the same / adjacent topic must be cited, and its scope contrasted with yours in the introduction.

## Anti-patterns

- **Memory-sourced entries.** Forbidden. WebFetch first or omit.
- **Fabricated entries.** Catastrophic. Real or weaker claim, never fake reference.
- **One paper, 30 cites.** Each `\cite{}` should advance the argument. Density comes from prose density, not paper repetition.
- **Citation dump.** `\cite{a, b, c, d, e, f, g, h}` covering 8 papers at once means you didn't read them. Group thematically and cite 2–4 per claim with prose distinguishing them.
- **Stopping at the 60 floor.** 60 is the minimum, not the target — aim for 100+.
- **Skipping `url=`.** Without the URL the entry is unverifiable.

## Quick checklist

- [ ] Picked a search posture from §0 (recency-led / timeline-spanning / balanced) and wrote it + the parsed window to `.bib_progress.txt`
- [ ] If recency matters: ran date-sorted arXiv queries (§3.5), not just relevance-ranked WebSearch
- [ ] Planned query angles spanning timeline / family / domain / paradigm / theory / surveys / recent / critiques — weighted by the posture
- [ ] Each entry backed by a URL fetched in this session (not from memory)
- [ ] `grep -c "^@" bibliography.bib` ≥ 60 (100+ recommended)
- [ ] Every entry has `title`, `author`, `year`, venue, `url`
- [ ] `papers.json` records `dimension` per entry for the classified table
- [ ] `.bib_progress.txt` records executed queries
- [ ] First test compile shows zero "Citation undefined" warnings against the template
