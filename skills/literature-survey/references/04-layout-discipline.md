# Layout Discipline — Tables, Figures, Floats, Cross-references

## Why this exists

A first draft is usually layout-naive: tables are bare `\begin{tabular}` blocks, figures use `[h]`, and the author block has no disclosure footnote. These choices break in journal/conference templates and look amateurish even where they don't break.

## Tables

### Always wrap in a `table` float

A bare `\begin{tabular}` in body text gets wrong placement, no caption, no label, and may break across pages. Always wrap:

```latex
\begin{table}[!t]
  \centering
  \small
  \setlength{\tabcolsep}{4pt}
  \caption{Comparison of Transformer-based time-series forecasters across capability dimensions. \checkmark = supported; \cmark[half] = partial; blank = not supported.}
  \label{tab:capability}
  \begin{tabular}{l c c c c c c}
    \toprule
    Method & Long horizon & Multivariate & Probabilistic & Zero-shot & Efficient & Interp. \\
    \midrule
    DLinear~\cite{zeng2023dlinear}              & \checkmark & --         & --         & --         & \checkmark & --         \\
    Informer~\cite{zhou2021informer}            & \checkmark & \checkmark & --         & --         & \checkmark & --         \\
    Autoformer~\cite{wu2021autoformer}          & \checkmark & \checkmark & --         & --         & \checkmark & --         \\
    PatchTST~\cite{nie2023patchtst}             & \checkmark & \checkmark & --         & --         & \checkmark & --         \\
    iTransformer~\cite{liu2024itransformer}     & \checkmark & \checkmark & --         & --         & \checkmark & --         \\
    Moirai~\cite{woo2024moirai}                 & \checkmark & \checkmark & \checkmark & \checkmark & --         & --         \\
    \bottomrule
  \end{tabular}
\end{table}
```

### Float placement

- `[!t]` — top of page. Default for tables and figures.
- `[!ht]` — top, otherwise here.
- Avoid `[h]` and `[h!]` — they cause floats to land in the middle of paragraphs.
- For a wide method-comparison table that overruns the text width, **do not** reach for `table*` (no second column to span here). Instead shrink to fit: `\small`/`\footnotesize`, tighten `\tabcolsep`, drop vertical padding, or wrap the `tabular` in `\resizebox{\linewidth}{!}{…}`; use `tabularx` with an `X` column when one text column should absorb the slack.

### Style

- **Always use `booktabs`**: `\toprule`, `\midrule`, `\bottomrule`. Never `\hline`.
- **No vertical rules** (`|` in column spec).
- **Numbers right-aligned** when comparing magnitudes.
- **Bold the cell that wins per row** if applicable. For survey capability tables, prefer `\checkmark` / `--` / partial markers over numerical scores.
- **Caption above** the tabular (scientific convention for tables).

### Caption rule

Captions must let a reader who reads only the caption + table understand what's shown. "Comparison." is not a caption; aim for 1–3 sentences naming the axis of comparison and the legend.

## Figures

### Float wrapper

```latex
\begin{figure}[!t]
  \centering
  \includegraphics[width=0.95\linewidth]{figures/fig_02_timeline.pdf}
  \caption{Chronology of representative works on Transformer-based time-series forecasting. Lanes correspond to the taxonomy branches in Fig~\ref{fig:taxonomy}.}
  \label{fig:timeline}
\end{figure}
```

### Width

- This template is **single-column** `article` → there is no second column to span. `figure*` behaves exactly like `figure` here, so it buys no width. Don't use it to "make room".
- Includes: `width=0.85\linewidth` to `width=\linewidth` — never a bare `\includegraphics{file}`.
- TikZ figures (taxonomy, timeline, architecture): wrap in `\resizebox{\linewidth}{!}{…}` so they fit the column whatever their natural size (see `02-survey-figures.md` § *Fitting & overflow*). If shrinking makes a tree unreadable, fold it into sub-figures rather than spilling past the margin.

### Path

`\includegraphics{figures/<basename>}` — never absolute paths.

### Caption

Same standalone-readable rule as tables. Caption goes **below** the figure.

### Multi-panel

Use `\begin{subfigure}` (the `subcaption` package is already loaded). For surveys, sub-figures are common when comparing canonical architectures across a family.

## Cross-references

### Every label must be referenced

If you `\label{eq:x}`, refer to it later with `Eq.~\ref{eq:x}`. Same for `\label{tab:...}`, `\label{fig:...}`, `\label{sec:...}`.

```bash
grep -oE '\\label\{[^}]+\}' sections/*.tex | sort -u > /tmp/labels.txt
grep -oE '\\ref\{[^}]+\}'   sections/*.tex | sort -u > /tmp/refs.txt
diff <(comm -23 /tmp/labels.txt /tmp/refs.txt) <(echo)
```

### Non-breaking spaces

Use `~` not regular space:
- `Section~\ref{sec:methods}`
- `Table~\ref{tab:capability}`
- `Figure~\ref{fig:taxonomy}` (or `Fig.~\ref{...}`)
- `\cite{key}` is preceded by `~`: "as shown in PatchTST~\cite{nie2023patchtst}"

## Author and disclosure footnote

**Author:** the default template uses `\author{AI4S Agent}`. Keep this unless the user has provided a specific author block.

**Disclosure:** every survey produced by this skill must carry a `\thanks` footnote on the author block recommending human review. Surveys do not present numerical experimental results, so the simulated clause from `paper-writer`'s template is **not** included.

```latex
\author{AI4S Agent\thanks{This survey was generated by the AI4S Agent. \textbf{Human review by a domain expert is strongly recommended} before any scientific publication or production use.}}
```

Do **not** put `\input{simulated}` inside `\title{}`.

## Common compile errors

### `Citation X undefined`

- bib_key in `\cite{X}` does not appear in `bibliography.bib`. Check spelling.
- Forgot to run `bibtex main` between `pdflatex` passes. Compile sequence: `pdflatex` → `bibtex` → `pdflatex` → `pdflatex`.

### `Missing $ inserted`

- Math symbol used outside math mode. Wrap with `$...$`.
- Underscore in non-math text: escape with `\_`.

### `Overfull \hbox`

- A line is wider than the column. Caused by long unbreakable strings (URLs, long bib-key clusters, equations).
- Fix by breaking the line, using `\sloppy`, or shortening.

### Float too large for page

- Reduce `width=`, or wrap the content in `\resizebox{\linewidth}{!}{…}` (TikZ/tabular). `figure*`/`table*` do not help in this single-column template.

## Verification commands

After any compile:

```bash
cd output/literature-survey/<slug>/survey_paper
grep -E "Citation .* undefined" main.log    # must be empty
grep -E "Reference .* undefined" main.log   # must be empty
grep -E "Overfull|Underfull" main.log | head # should be near-empty
ls main.pdf                                  # must exist
pdfinfo main.pdf | grep Pages                # must be ≥ target
```

## Quick checklist

- [ ] Every table wrapped in `\begin{table}[!t]` with caption + label, using `booktabs`; wide tables fit via `\small`/`\resizebox`/`tabularx`, not `table*`
- [ ] Every figure wrapped in `\begin{figure}[!t]` with caption + label; TikZ in `\resizebox{\linewidth}{!}{…}`, includes with `width=…\linewidth`
- [ ] Captions are standalone-readable (1–3 sentences)
- [ ] Cross-refs use non-breaking space (`~`)
- [ ] No vertical rules in tables; no `\hline` inside `\toprule`/`\midrule`/`\bottomrule`
- [ ] Author = `AI4S Agent`; `\thanks` footnote present with human-review clause
- [ ] No simulated clause in the `\thanks` (surveys don't claim numerical results)
- [ ] Final compile log: 0 undefined citations, 0 undefined references, 0 overfull boxes (remediate, don't tolerate)
