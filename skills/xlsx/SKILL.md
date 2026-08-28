---
name: xlsx
metadata:
  author: Z.AI
  version: "1.0"
description: "Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file; create a new spreadsheet from scratch or from other data sources; analyze data and output results as an Excel file with charts; convert between tabular file formats (CSV/JSON/PDF → XLSX or vice versa); clean, merge, pivot, or transform tabular data. Trigger especially when the user references a spreadsheet file by name or path, says 'make a table/report/model', mentions Excel/CSV/数据分析/报表/汇总, or wants data visualization inside a spreadsheet."
license: Proprietary. LICENSE.txt has complete terms
---

# XLSX — Scene-Driven Spreadsheet Workbench

## Quick Setup

```bash
bash "$XLSX_SKILL_DIR/setup.sh"    # Interactive environment check + install
```
## Pre-Flight: Intent Gate

Before touching any code, confirm the user actually needs a spreadsheet:

- Report / analysis summary (述职, 调研报告) → **docx skill**
- Presentation (汇报, 演示, pitch deck) → **pptx skill**
- Formal print document (合同, 证书, "PDF") → **pdf skill**
- Charts only, no data table needed → **charts skill**
- User explicitly says a format → respect it

If confirmed xlsx → proceed to Scene Router below.

**Request Decomposition** (do this every time):
- **Explicit needs**: sheets, columns, formulas, metrics the user stated
- **Implicit needs**: business context, downstream use (filter? sort? input?)
- **Multi-part requests**: generate ALL parts — never silently drop a component

**Multi-Intent Detection** — some requests combine multiple scenes:

```
"Create a financial model with charts and export a PDF summary"
 → scenes/finance.md + engines/chart.md + (hand off PDF to pdf skill)

"Analyze this CSV, build a dashboard, and make it look professional"
 → scenes/analyze.md + engines/chart.md + engines/design.md

"Edit this budget file, add a new quarter column, and create a pivot"
 → scenes/edit.md + quality/pipeline.md (pivot command)

"Convert these 5 CSVs into one xlsx with a summary sheet"
 → scenes/convert.md + scenes/create.md (for summary)
```

When multiple intents detected, load all matching files and execute in logical order: data preparation → analysis → visualization → styling → QA.

---

## Complexity Gate (evaluate BEFORE Scene Router)

Determine task complexity to control file loading depth:

```
User Request
│
├─ LITE (single aggregation, simple chart, direct conversion, QA-only)
│  → Load: SKILL.md + ONE scene file (lean version)
│  → Skip: engine files (use built-in knowledge for basic styles)
│  → QA: audit + validate only
│  → Target: ≤ 400 lines total context
│
└─ FULL (multi-dimensional analysis, financial model, dashboard, KANO, etc.)
   → Load: SKILL.md + scene + engines (chart.md / design.md) as needed
   → For code patterns: load recipes/templates files ON DEMAND (not upfront)
   → QA: full pipeline (recalc → audit → scan → chart-verify → validate)
   → Target: load recipes/templates only when stuck on implementation
```

**LITE triggers**: single groupby, one chart, format conversion, inspect/audit/validate, simple pivot
**FULL triggers**: correlation matrix, multi-sheet dashboard, statistical analysis, financial model, KANO/funnel/cohort

---

## Scene Router

```
User Request
│
├─ Involves an existing file?
│  ├─ Yes → Modify content or structure?
│  │         ├─ Yes ──────────────────── → scenes/edit.md
│  │         └─ No (read/analyze only) ─ → scenes/analyze.md
│  │
│  └─ Format conversion (CSV↔XLSX, JSON, PDF tables)?
│     └─ Yes ────────────────────────── → scenes/convert.md
│
├─ Create from scratch?
│  ├─ Financial / budget / forecast / cost tracking?
│  │  ├─ Complex (DCF / LBO / three-statement linkage (三表联动) / sensitivity / IB model)?
│  │  │  └─ Yes ─────────────────────── → scenes/finance.md
│  │  └─ Simple (budget table (预算表) / expense report (费用报表) / revenue vs cost (收支对比) / project cost (项目成本) / personal finance (个人记账))?
│  │     └─ Yes ─────────────────────── → scenes/finance_lite.md
│  └─ General table / report / template
│     └─ ──────────────────────────── → scenes/create.md
│
├─ Batch processing / large files / protection / validation?
│  └─ Yes ───────────────────────────── → scenes/advanced.md
│
├─ VBA / macros / automation inside Excel?
│  └─ Yes ───────────────────────────── → scenes/vba.md + engines/vba-templates.md
│
├─ Needs charts or data visualization?
│  └─ Yes ───────────── append ────────→ engines/chart.md
│
└─ Needs styling / design system?
   └─ Yes ───────────── append ────────→ engines/design.md
```

**Mixed requests**: load all matching files. Engine files always **append** to a scene.

**Finance detection**:
- **finance.md** (complex): DCF, LBO, P&L, 利润表, 资产负债, valuation, 估值, IRR, 三表联动, sensitivity, scenario
- **finance_lite.md** (simple): 预算, budget, 费用, expense, 收支, 记账, 项目成本, cost tracking, 报销, ROI

**VBA detection**: 宏, macro, VBA, 自动化, automation, .xlsm, 按钮, button, auto-run, 批量处理脚本

---

## Design Principles

### 1. Live Formula Guarantee
Every derived value SHOULD be an Excel formula so the spreadsheet stays dynamic.

**Exception — Programmatic Verification**: When the output file will be verified by Python (not opened in Excel), TOTAL/SUM rows should write **computed values** instead of formulas, because openpyxl cannot evaluate formulas and `data_only=True` returns `None` for newly-written formulas. Optionally add the formula as a cell comment for reference.

### 2. Zero Error Tolerance
Deliverables must have zero formula errors. All divisions wrapped with `IFERROR` or `IF(denom=0,...)`. Absolute references (`$C$42`) for shared denominators.

### 3. Compatibility First
No dynamic array functions (`FILTER`, `UNIQUE`, `XLOOKUP`, `SORT`, `SORTBY`, `XMATCH`, `SEQUENCE`, `LET`, `LAMBDA`, `RANDARRAY`). No implicit array formulas — use `SUMPRODUCT` alternatives.

### 4. Preserve & Match
When editing existing files: study and exactly match format, style, conventions. Existing patterns always override defaults. Text starting with `=` must be prefixed with `'`.

### 5. Language Mirror
Output language (sheet names, headers, labels) matches user's input language.

### 6. Data Consistency Over Instructions
When user instructions conflict with the actual data patterns in the existing file:
- **First priority**: match the existing data pattern (e.g., if existing data uses `0` for empty, don't switch to `-`)
- **Second priority**: follow user instructions literally
- Always flag the conflict to the user

Example: User says "show hyphen for zero" but existing data and answer key use numeric `0` → Use `0` and notify user of the discrepancy.

---

## Toolchain

### Script Path Setup (MANDATORY before any script call)

All CLI tools live relative to this skill's directory. Before calling any script, resolve the absolute path once:

```bash
XLSX_SKILL_DIR="<skill_directory>"   # ← parent directory of this SKILL.md

# Then all commands use absolute paths:
python3 "$XLSX_SKILL_DIR/xlsx.py" inspect data.xlsx --pretty
python3 "$XLSX_SKILL_DIR/xlsx.py" pivot data.xlsx output.xlsx --rows Region --values Revenue
python3 "$XLSX_SKILL_DIR/xlsx.py" validate output.xlsx
```

**For Python imports** (when generation code needs to import skill modules):

```python
import sys, os
XLSX_SKILL_DIR = "<skill_directory>"
for sub in [XLSX_SKILL_DIR, os.path.join(XLSX_SKILL_DIR, "templates")]:
    if sub not in sys.path:
        sys.path.insert(0, sub)
```

**⚠️ NEVER use bare `python3 xlsx.py ...`** — it only works if cwd happens to be the skill directory. Always use the absolute path.

### Tool Reference

| Tool | Use |
|------|-----|
| **openpyxl** | Formulas, formatting, charts, cell-level control |
| **pandas** | Data analysis, bulk operations, CSV/TSV |
| `load_workbook(read_only=True)` | Large file reads |
| `Workbook(write_only=True)` | Large file writes |
| **templates/base.py** | Design tokens, font resolution, style factories, utilities (single source of truth) |
| **xlsx.py** | QA commands (see `quality/pipeline.md`) |

Workbook metadata: `wb.properties.creator = "Z.ai"`

> **All code must import from `templates/base.py`** for colors, fonts, and style helpers. Never hardcode hex values or font names.

---

## Quality Gate

Every deliverable must pass the full integrity pipeline before delivery.

→ **Load `quality/pipeline.md` for the role-based integrity workflow.**

Quick reference:
```
Blueprint → Build & Self-check (per-sheet) → Inspect → Pivot (if needed) → Release
```

---

## Capability Matrix

| Capability | Supported | Scene/Engine |
|-----------|-----------|-------------|
| Create from scratch | ✅ | scenes/create |
| Edit existing file | ✅ | scenes/edit |
| Data analysis & EDA | ✅ | scenes/analyze |
| Format conversion | ✅ | scenes/convert |
| Financial models (DCF/LBO/P&L) | ✅ | scenes/finance |
| Simple budgets & expenses | ✅ | scenes/finance_lite |
| VBA macros & automation | ✅ | scenes/vba + engines/vba-templates |
| Batch processing | ✅ | scenes/advanced |
| Embedded charts | ✅ | engines/chart |
| Smart chart recommendation | ✅ | engines/chart |
| Design system & styling | ✅ | engines/design |
| PivotTable creation | ✅ | quality/pipeline (pivot cmd) |
| Formula validation | ✅ | quality/pipeline |
| Structural validation | ✅ | quality/pipeline |
| Data provenance tracking | ✅ | scenes/analyze |
| Large file handling | ✅ | scenes/advanced |
| Data protection & locking | ✅ | scenes/advanced |
