
---

## CJK Typography Supplement

> See `pagination.md` Section 3 for detailed rules.

### Scope: Creative Flow pipeline (html2pdf-next.js) ONLY

These CSS rules apply to **multi-page HTML documents** rendered via `html2pdf-next.js` (Creative Flow brief). In this pipeline, Chromium's `text-align: justify` + `line-break: strict` produces proper CJK typesetting with correct punctuation handling.

**Do NOT apply these rules to:**
- **Poster pipeline** (html2poster.js) — short lines + fixed containers make justify stretch CJK character spacing. Use `text-align: left` instead. See `briefs/poster.md` §7.1.
- **Report pipeline** (ReportLab) — use `TA_LEFT` for CJK body text. ReportLab’s justify algorithm handles CJK poorly. See `briefs/report.md` §CJK alignment.

```css
/* CJK punctuation placement rules — Creative Flow pipeline only */
body {
  line-break: strict;
  word-break: normal;
  overflow-wrap: break-word;
}

p, td, li {
  line-break: strict;
  text-align: justify;  /* Only for Creative Flow; poster/report use left */
}
```
