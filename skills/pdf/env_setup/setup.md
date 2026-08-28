# PDF Skill — Environment Setup Guide

This document contains full platform-specific instructions for setting up the PDF skill environment.
The model should read this file when first-time setup is needed.

---

## Step 1: Platform Detection

Detect the OS and set core variables:

### macOS / Linux (bash/zsh)

```bash
OS="$(uname -s)"   # Darwin = macOS, Linux = Linux
ARCH="$(uname -m)" # x86_64 or arm64

PDF_SKILL_DIR="<skill_directory>"
export PDF_SKILL_DIR
```

### Windows (PowerShell, Win10/Win11)

```powershell
$WinVer = [System.Environment]::OSVersion.Version
$Arch   = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture

$env:PDF_SKILL_DIR = "<skill_directory>"
```

---

## Step 2: Dependency Check & Install

Run the platform-appropriate setup script:

| Platform | Command |
|----------|---------|
| macOS / Linux | `bash "$PDF_SKILL_DIR/env_setup/setup_mac_linux.sh"` |
| Windows | `powershell -ExecutionPolicy Bypass -File "$env:PDF_SKILL_DIR\env_setup\setup_windows.ps1"` |

### Required Dependencies

| Category | Package | Purpose |
|----------|---------|---------|
| Runtime | Python 3 + pip | PDF generation and processing |
| Runtime | Node.js + npm | Playwright for Creative pipeline |
| Python pkg | pikepdf | PDF manipulation (merge/split/encrypt) |
| Python pkg | pdfplumber | Text/table extraction |
| Python pkg | pypdf | PDF reading/writing |
| Python pkg | reportlab | Report pipeline PDF generation |
| Python pkg | PyMuPDF (fitz) | Fast PDF rendering and extraction |
| npm pkg | playwright | HTML-to-PDF for Creative pipeline |
| Browser | Chromium (via Playwright) | Headless rendering |
| Optional | tectonic | LaTeX/Academic PDF compilation |
| Optional | LibreOffice | Office-to-PDF conversion |
| Font | CJK fonts (from CDN) | Chinese text in PDFs |

### Manual Install by Platform

#### macOS

```bash
brew install python3 node
python3 -m pip install pikepdf pdfplumber pypdf reportlab PyMuPDF
npm install -g playwright@1.50.0 && npx playwright install chromium
# Pinned to 1.50.0 — npmmirror has Chromium rev 1155 for this version
brew install tectonic                 # optional: LaTeX
brew install --cask libreoffice       # optional: Office-to-PDF
```

#### Linux (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip nodejs npm
python3 -m pip install pikepdf pdfplumber pypdf reportlab PyMuPDF
npm install -g playwright@1.50.0 && npx playwright install chromium && npx playwright install-deps
# Pinned to 1.50.0 — npmmirror has Chromium rev 1155 for this version
# optional:
conda install -c conda-forge tectonic   # use Tsinghua mirror: conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
sudo apt install libreoffice-core                      # LibreOffice
```

#### Windows (PowerShell)

```powershell
winget install Python.Python.3.11
winget install OpenJS.NodeJS.LTS
python -m pip install pikepdf pdfplumber pypdf reportlab PyMuPDF
npm install -g playwright@1.50.0
# Pinned to 1.50.0 — npmmirror has Chromium rev 1155 for this version
npx playwright install chromium
# optional:
scoop install tectonic                           # LaTeX
winget install TheDocumentFoundation.LibreOffice  # Office-to-PDF
```

Alternative Windows package managers:
- `choco install python3 nodejs-lts`
- `scoop install python nodejs-lts`

---

## Step 3: Font Installation

Fonts are downloaded individually from CDN on first setup.

- **CDN base**: `https://z-cdn.chatglm.cn/office-skill/fonts/`
- **Font list**: `env_setup/font_list.txt` (78 fonts, one relative path per line)
- **Marker file**: `.office-skill-fonts-installed` in the user font directory prevents re-download
- Special characters in filenames (e.g., `[`, `]`) are URL-encoded automatically by the setup script

The setup scripts read `font_list.txt`, check which fonts are already installed, and download only the missing ones. Each font is saved flat (filename only) to the user font directory.

### CDN Directory Structure (78 fonts)

| Directory | Count | Description |
|-----------|-------|-------------|
| `truetype/lxgw-wenkai/` | 6 | LXGW WenKai — Chinese handwriting style |
| `truetype/noto-serif-sc/` | 9 | Noto Serif SC — Chinese serif (variable + 8 static weights) |
| `chinese/` | 14 | Noto Sans SC, Sarasa Mono SC, Liberation fallbacks |
| `dejavu/` | 8 | DejaVu Sans/Serif/Mono — Latin/symbol fallback |
| `emoji/` | 1 | Noto Color Emoji |
| `english/` | 12 | Tinos, Carlito, Calibri |
| `freefont/` | 12 | FreeSans/FreeSerif/FreeMono — open-source fallback |
| `liberation/` | 12 | Liberation Sans/Serif/Mono — MS-metric-compatible |
| `libreoffice/` | 1 | OpenSymbol |
| `noto/` | 1 | Noto Color Emoji (duplicate) |
| `wqy/` | 1 | WenQuanYi Zen Hei — CJK fallback |
| *(root)* | 1 | Japanese Gothic |

### Install Targets by Platform

| Platform | User Font Directory |
|----------|-------------------|
| macOS | `~/Library/Fonts/` |
| Linux | `~/.local/share/fonts/` (then run `fc-cache -f`) |
| Windows | `%LOCALAPPDATA%\Microsoft\Windows\Fonts` (per-user, no admin) |

### Manual Font Installation

If CDN is unreachable, download fonts manually. Example:

```bash
# Download a single font (use static-weight files, NOT variable fonts)
curl -fSLO "https://z-cdn.chatglm.cn/office-skill/fonts/chinese/NotoSansSC-Regular.ttf"
# Copy to user font dir
cp "NotoSansSC-Regular.ttf" ~/Library/Fonts/   # macOS
```

Or download all fonts listed in `font_list.txt`:

```bash
while read f; do
    encoded=$(echo "$f" | sed 's/\[/%5B/g; s/\]/%5D/g')
    curl -fSLO "https://z-cdn.chatglm.cn/office-skill/fonts/$encoded"
done < env_setup/font_list.txt
```

### Post-Install Variable

After font installation, `FONT_DIR` points to the user font directory:

| Platform | FONT_DIR |
|----------|---------------|
| macOS | `~/Library/Fonts` |
| Linux | `~/.local/share/fonts` |
| Windows | `%LOCALAPPDATA%\Microsoft\Windows\Fonts` |

---

## China Network Fallback

If default sources are unreachable, use China mirrors:

### pip (Tsinghua mirror)

```bash
python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
  --trusted-host pypi.tuna.tsinghua.edu.cn \
  pikepdf pdfplumber pypdf reportlab PyMuPDF
```

### npm (npmmirror)

```bash
npm install -g playwright@1.50.0 --registry https://registry.npmmirror.com
# Pinned to 1.50.0 — npmmirror has Chromium rev 1155 for this version
```

### Playwright browser download (npmmirror)

```bash
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ npx playwright install chromium
```

### Windows (PowerShell) China mirrors

```powershell
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn pikepdf pdfplumber pypdf reportlab PyMuPDF
npm install -g playwright@1.50.0 --registry https://registry.npmmirror.com
# Pinned to 1.50.0 — npmmirror has Chromium rev 1155 for this version
$env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright/"
npx playwright install chromium
```

### Installer downloads (China)

| Software | China Mirror |
|----------|-------------|
| Node.js | https://npmmirror.com/mirrors/node/ |
| Python | https://npmmirror.com/mirrors/python/ |
