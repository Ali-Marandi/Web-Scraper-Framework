---
name: data-integrity
description: Data marker, chart, table, metric, and demo-data integrity rules for editable design artifacts.
mode: reference
platform: web
scenario: horizontal-craft
preview:
  type: none
default_for:
  - data markers
  - charts
  - metrics
  - tables
  - dashboard data
  - demo data
  - editable artifact
fidelity: system
---

# Data Integrity

Use this file when an artifact contains data, metrics, charts, tables, proof-like numbers, or needs future editing.

Core rule:

```text
A design artifact may use demo data, but it must never disguise demo data as real evidence.
```

---

## Data markers

Data markers preserve editability and later comment targeting.

Use the artifact scaffold:

```text
portfolio        → data-portfolio / data-section / data-project / data-component
deck             → data-deck / data-slide / data-component
prototype        → data-prototype / data-screen / data-section / data-component / data-state
content-page     → data-content-page / data-mode / data-section / data-component
landing-page     → data-landing-page / data-section / data-component
web-tool         → data-web-tool / data-tool-type / data-screen / data-component / data-state
```

If a marker would be excessive for a tiny edit, preserve existing markers and add the minimum missing markers around edited regions.

---

## Metrics and demo data

Specific numbers must be one of:

```text
user-provided
sourced
demo-labeled
placeholder
```

Do not invent impressive proof to improve a design.

Never invent:

- revenue
- market size
- user counts
- growth rates
- conversion rates
- retention / churn
- satisfaction scores
- rankings
- uptime
- benchmark wins
- customer counts

If the number is illustrative, label it as demo.

Example:

```html
<span data-proof="demo">92% demo</span>
<p class="data-note">Demo data — replace with verified figures before publishing.</p>
```

---

## Charts

Charts must communicate a claim, not decorate a card.

Required:

- title or conclusion
- axes or labels when quantitative
- units
- source / demo label when data is not user-provided
- readable values
- contrast that survives small screens

Avoid:

- fake trend lines with no data meaning
- unlabeled sparkline decoration
- impossible precision
- random upward growth lines
- chart colors with no legend or state meaning

---

## Tables

Tables must optimize scanning.

Rules:

- numeric columns align consistently
- status labels use consistent vocabulary
- filters/search/sort appear when the table implies operations
- long text has wrap or truncation strategy
- empty and error states exist
- row actions are close to rows
- units appear in header or values, not randomly

---

## Data copy

Prefer honest labels:

- Demo data
- 示例数据
- 待填写
- Replace with verified figures
- Source pending

Avoid pretending:

- trusted by 10,000+ teams
- 99.9% uptime
- #1 platform
- industry-leading
- verified by experts

---

## Quality checks

```text
[ ] Required data markers are present.
[ ] Proof-like numbers have provenance.
[ ] Demo data is visibly labeled.
[ ] Charts have labels, units, and a conclusion.
[ ] Tables are aligned, scannable, and have states.
[ ] No invented impressive metric exists.
[ ] Fake customer logos, quotes, awards, and press claims are absent.
```
