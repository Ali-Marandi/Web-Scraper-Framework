# WebScraper Pro

<div align="center">

**Commercial-Grade Web Scraping Application for Windows**

A professional, feature-rich desktop application for extracting data from websites.
Built with Python, CustomTkinter, Playwright, and BeautifulSoup.

[![Build Windows](https://github.com/Ali-Marandi/Web-Scraper-Framework/actions/workflows/build-release.yml/badge.svg)](https://github.com/Ali-Marandi/Web-Scraper-Framework/actions/workflows/build-release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)

[Download Latest Release](../../releases/latest)

</div>

---

## Screenshot

> Modern dark-themed UI with sidebar navigation, real-time progress tracking, and comprehensive data extraction tools.

## Features

### Dual Scraping Engines
| Feature | Static Engine | Dynamic Engine |
|---------|:------------:|:-------------:|
| Speed | Very Fast | Moderate |
| JavaScript | No | Full Support |
| Stealth | N/A | Anti-Detection |
| Resources | Minimal | Browser Required |

### Data Extraction Methods
- **CSS Selectors** - Standard CSS selector syntax
- **XPath** - Full XPath 1.0 support
- **Regular Expressions** - Pattern matching with groups
- **JSON Path** - Extract from embedded JSON/API responses
- **Table Extraction** - Auto-detect and extract HTML tables
- **Link/Image Extraction** - Bulk URL and image harvesting
- **Full Text** - Complete page text content
- **HTML Attributes** - Extract any element attribute
- **Meta Tags** - Page metadata extraction

### Export Formats
| Format | Description |
|--------|-------------|
| CSV | Excel-compatible with UTF-8 BOM |
| JSON | Pretty-printed, structured |
| Excel (XLSX) | Formatted with filters and frozen headers |
| XML | Structured with proper nesting |
| HTML | Styled, responsive table |
| SQLite | Queryable database |

### Proxy Management
- HTTP, HTTPS, SOCKS4, SOCKS5 support
- Multiple rotation strategies (random, round-robin, least-used, fastest)
- Automatic health monitoring and failover
- Concurrent proxy testing
- Import from file
- Authentication support

### Rate Limiting
- **Token Bucket** - Burst-friendly rate control
- **Sliding Window** - Precise request counting
- **Fixed Delay** - Simple time-based throttling
- **Adaptive** - Auto-adjusts based on response times
- Per-domain configuration
- Global request rate control

### Task Scheduler
- One-time, interval, daily, weekly, monthly schedules
- Auto-export on completion
- Execution history tracking

## Project Structure

```
WebScraperPro/
+-- main.py                    # Application entry point
+-- requirements.txt           # Python dependencies
+-- WebScraperPro.spec         # PyInstaller build config
+-- core/                      # Scraping engine
|   +-- scraper_engine.py      # Main orchestrator
|   +-- static_scraper.py      # HTTP-based scraper
|   +-- dynamic_scraper.py     # Browser-based scraper
|   +-- proxy_manager.py       # Proxy rotation & health
|   +-- rate_limiter.py        # Rate limiting algorithms
|   +-- data_parser.py         # Data extraction engine
|   +-- data_exporter.py       # Multi-format export
|   +-- scheduler.py           # Task scheduling
+-- ui/                        # User interface
|   +-- main_window.py         # Main application window
|   +-- styles.py              # Design system & theme
|   +-- panels/                # UI panels
|       +-- dashboard_panel.py # Main scraper panel
|       +-- proxy_panel.py     # Proxy management
|       +-- scheduler_panel.py # Task scheduler
|       +-- settings_panel.py  # Settings
+-- assets/                    # Icons and themes
+-- .github/workflows/        # CI/CD for Windows build
```

## Quick Start

### Download (Windows)
1. Go to [Releases](../../releases/latest)
2. Download `WebScraperPro-Windows-x64.zip`
3. Extract and run `WebScraperPro.exe`

### From Source
```bash
git clone https://github.com/Ali-Marandi/Web-Scraper-Framework.git
cd Web-Scraper-Framework
pip install -r requirements.txt
playwright install chromium
python main.py
```

### Build Windows EXE
```bash
pip install pyinstaller
pyinstaller WebScraperPro.spec
```
The executable will be in `dist/WebScraperPro/`.

## Requirements

- Python 3.10+
- Windows 10/11 (for the EXE)
- Dependencies listed in `requirements.txt`

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with Python | CustomTkinter | Playwright | BeautifulSoup
</div>
