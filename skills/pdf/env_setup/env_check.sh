#!/usr/bin/env bash
# Lightweight environment check for PDF skill.
# Exit 0 = all OK, exit 1 = missing dependencies.
# Also resolves and exports PDF_SKILL_DIR and FONT_DIR.
# Usage: source env_check.sh  (preferred, exports vars to caller)
#    or: bash env_check.sh [--quiet]
QUIET=false; [ "${1:-}" = "--quiet" ] && QUIET=true
FAIL=0
check() { local desc="$1"; shift; if ! "$@" &>/dev/null; then $QUIET || echo "MISSING: $desc"; FAIL=1; fi; }

# ── Resolve PDF_SKILL_DIR & FONT_DIR ──
_ENV_CHECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PDF_SKILL_DIR="$(cd "$_ENV_CHECK_DIR/.." && pwd)"
export PDF_SKILL_DIR

if [ "$(uname -s)" = "Darwin" ]; then
    FONT_DIR="${HOME}/Library/Fonts"
else
    FONT_DIR="/usr/share/fonts"
fi
export FONT_DIR

check "python3"    command -v python3
check "node"       command -v node
check "pikepdf"    python3 -c "import pikepdf"
check "pdfplumber" python3 -c "import pdfplumber"
check "pypdf"      python3 -c "import pypdf"
check "reportlab"  python3 -c "import reportlab"
check "PyMuPDF"    python3 -c "import fitz"
check "playwright" node -e "require('playwright')"

# LaTeX engine (tectonic) — needed for Academic pipeline
if [ -x "$PDF_SKILL_DIR/scripts/tectonic" ]; then
    : # bundled binary OK
elif command -v tectonic &>/dev/null; then
    : # system tectonic OK
else
    $QUIET || echo "MISSING: tectonic (needed for LaTeX/Academic PDFs)"
    FAIL=1
fi

# Font check: verify CJK fonts are available
if command -v fc-list &>/dev/null; then
    fc-list :lang=zh 2>/dev/null | grep -qi "noto\|simhei\|wenquanyi" || { $QUIET || echo "MISSING: CJK fonts"; FAIL=1; }
fi

$QUIET || echo "PDF_SKILL_DIR=$PDF_SKILL_DIR"
$QUIET || echo "FONT_DIR=$FONT_DIR"
return $FAIL 2>/dev/null || exit $FAIL
