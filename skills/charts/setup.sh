#!/usr/bin/env bash
# ---
# name: charts-setup
# author: Z.AI
# version: "1.0"
# description: Environment setup for the Charts skill. Checks and installs all required dependencies.
# ---
#
# Installs only dependencies required by the Charts skill.
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok() { echo -e "  ${GREEN}✓${NC} $1"; }
fail() { echo -e "  ${RED}✗${NC} $1"; }
warn() { echo -e "  ${YELLOW}○${NC} $1"; }
info() { echo -e "  ${BLUE}→${NC} $1"; }

echo "============================================"
echo "  Charts Skill — Environment Setup"
echo "============================================"
echo ""

OS="$(uname -s)"
ARCH="$(uname -m)"
echo "Platform: $OS $ARCH"
echo ""

# ── 0. macOS: Homebrew ──
if [ "$OS" = "Darwin" ]; then
    echo "--- Homebrew (macOS package manager) ---"
    if command -v brew &>/dev/null; then
        BREW_VER=$(brew --version 2>/dev/null | head -1)
        ok "brew ($BREW_VER)"
    else
        fail "brew not found — most dependencies below need Homebrew on macOS"
        info "Install: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    fi
    echo ""
fi

# ── 1. Python 3 ──
echo "--- Python ---"
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    ok "python3 ($PY_VER)"
    if [ "$OS" = "Darwin" ]; then
        PY_PATH=$(which python3 2>/dev/null)
        if [[ "$PY_PATH" == "/usr/bin/python3" ]]; then
            warn "Using macOS system Python (limited). Recommend: brew install python3"
        fi
    fi
else
    fail "python3 not found"
    case "$OS" in
        Darwin) info "Install: brew install python3" ;;
        Linux)  info "Install: sudo apt install python3 python3-pip  (Debian/Ubuntu)"
                info "         sudo dnf install python3 python3-pip  (Fedora/RHEL)" ;;
        *)      info "Install: https://www.python.org/downloads/" ;;
    esac
fi

# ── 2. pip ──
echo ""
echo "--- pip ---"
if python3 -m pip --version &>/dev/null 2>&1; then
    PIP_VER=$(python3 -m pip --version 2>/dev/null | head -1)
    ok "pip ($PIP_VER)"
else
    fail "pip not found"
    case "$OS" in
        Darwin) info "Install: python3 -m ensurepip --upgrade"
                info "     or: brew install python3 (includes pip)" ;;
        Linux)  info "Install: sudo apt install python3-pip  (Debian/Ubuntu)" ;;
        *)      info "Install: python3 -m ensurepip --upgrade" ;;
    esac
fi

# ── 3. Python packages (matplotlib / seaborn for data charts) ──
echo ""
echo "--- Python Packages (Data Charts) ---"
PY_PKGS=(
    "matplotlib:matplotlib"
    "seaborn:seaborn"
    "numpy:numpy"
    "adjustText:adjustText"
)

MISSING_PY=()
for entry in "${PY_PKGS[@]}"; do
    mod="${entry%%:*}"
    pkg="${entry##*:}"
    if python3 -c "import $mod" 2>/dev/null; then
        ver=$(python3 -c "import $mod; print(getattr($mod, '__version__', 'installed'))" 2>/dev/null)
        ok "$pkg ($ver)"
    else
        fail "$pkg not installed"
        MISSING_PY+=("$pkg")
    fi
done

if [ ${#MISSING_PY[@]} -gt 0 ]; then
    echo ""
    if [ -t 0 ]; then
        read -p "  Install missing Python packages? [Y/n] " -n 1 -r REPLY
        echo ""
        REPLY=${REPLY:-Y}
    else
        warn "Non-interactive mode — skipping auto-install. Run interactively or install manually."
        REPLY=N
    fi
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        python3 -m pip install -q "${MISSING_PY[@]}" 2>/dev/null \
            || python3 -m pip install -q --user "${MISSING_PY[@]}" 2>/dev/null \
            || python3 -m pip install -q --break-system-packages "${MISSING_PY[@]}" 2>/dev/null \
            || { fail "pip install failed. Try manually: pip install ${MISSING_PY[*]}"; }
        ok "Installed: ${MISSING_PY[*]}"
    fi
fi

# ── 4. Node.js ──
echo ""
echo "--- Node.js (Interactive Charts & Diagrams) ---"
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    ok "node ($NODE_VER)"
else
    fail "node not found"
    case "$OS" in
        Darwin) info "Install: brew install node" ;;
        Linux)  info "Install: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
                info "         sudo apt install -y nodejs" ;;
        *)      info "Install: https://nodejs.org/" ;;
    esac
fi

# ── 5. npm ──
echo ""
echo "--- npm ---"
if command -v npm &>/dev/null; then
    NPM_VER=$(npm --version 2>/dev/null)
    ok "npm ($NPM_VER)"
else
    fail "npm not found"
    case "$OS" in
        Darwin) info "Install: brew install node (includes npm)" ;;
        Linux)  info "Install: comes with nodejs" ;;
        *)      info "Install: https://nodejs.org/" ;;
    esac
fi

# ── 6. Playwright + Chromium (for HTML→PNG/PDF rendering) ──
echo ""
echo "--- Playwright (Structural Diagrams & HTML Charts) ---"
if node -e "require('playwright')" 2>/dev/null; then
    PW_VER=$(node -e "console.log(require('playwright/package.json').version)" 2>/dev/null)
    ok "playwright ($PW_VER)"
else
    fail "playwright not installed"
    info "Install: npm install -g playwright"
fi

if [ "$OS" = "Darwin" ]; then
    PW_CACHE="$HOME/Library/Caches/ms-playwright"
else
    PW_CACHE="$HOME/.cache/ms-playwright"
fi
if ls "$PW_CACHE"/chromium-* &>/dev/null 2>&1; then
    CR_DIR=$(ls -d "$PW_CACHE"/chromium-* 2>/dev/null | tail -1)
    ok "chromium ($(basename "$CR_DIR"))"
else
    fail "chromium not installed"
    info "Install: npx playwright install chromium"
    if [ "$OS" = "Linux" ]; then
        info "         npx playwright install-deps  (system libs, needs sudo)"
    fi
fi

# ── 7. CJK Fonts (for Chinese chart labels) ──
echo ""
echo "--- CJK Fonts (Chinese text in charts) ---"
CJK_FOUND=false

# Check matplotlib registered fonts
if python3 -c "
import matplotlib.font_manager as fm
fonts = [f.name for f in fm.fontManager.ttflist]
if 'SimHei' in fonts or 'Heiti SC' in fonts or 'Noto Sans CJK' in fonts or 'PingFang SC' in fonts:
    print('ok')
else:
    print('missing')
" 2>/dev/null | grep -q "ok"; then
    ok "CJK font registered in matplotlib (SimHei/Heiti SC/Noto Sans CJK/PingFang SC)"
    CJK_FOUND=true
fi

# Check system CJK fonts
if [ "$OS" = "Darwin" ]; then
    if ls /System/Library/Fonts/PingFang.ttc &>/dev/null 2>&1 \
       || ls /System/Library/Fonts/STHeiti*.ttc &>/dev/null 2>&1; then
        ok "macOS CJK system fonts available (PingFang/STHeiti)"
        CJK_FOUND=true
    fi
elif [ "$OS" = "Linux" ]; then
    if fc-list :lang=zh 2>/dev/null | head -1 | grep -q .; then
        ok "system CJK fonts available (fc-list)"
        CJK_FOUND=true
    fi
fi

if [ "$CJK_FOUND" = false ]; then
    warn "No CJK font detected — Chinese labels may show as □"
    info "The skill configures font fallback via rcParams at runtime."
    info "Ensure a CJK font file exists (e.g., SimHei.ttf) and is registered."
    if [ "$OS" = "Darwin" ]; then
        info "macOS ships with PingFang — try: plt.rcParams['font.sans-serif'] = ['PingFang SC', 'DejaVu Sans']"
    elif [ "$OS" = "Linux" ]; then
        info "Install: sudo apt install fonts-noto-cjk"
    fi
fi

# ── Summary ──
echo ""
echo "============================================"
echo "  Setup complete."
echo "  Data charts: matplotlib + seaborn"
echo "  Structural diagrams: Playwright + CSS"
echo "  Interactive charts: ECharts / D3.js via Node.js"
echo "============================================"
