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

## What's New in v1.3.0

- **URL Explorer** - New panel that crawls pages and categorizes all links (internal, external, images, documents, videos, emails, social, feeds) with tree view and filters
- **Link Validation** - Validate extracted links with HTTP status codes, detect broken links, measure response times
- **CSS Selector Tester** - New tool tab: test CSS selectors against HTML with attribute extraction
- **XPath Tester** - New tool tab: test XPath expressions against HTML pages
- **JSON Path Tester** - New tool tab: test JSON path queries against JSON data with slice support
- **Response Inspector** - New tool tab: inspect HTTP responses with formatted headers, body, and raw request/response details
- **Enhanced Proxy Panel** - JSON file import, export proxy list, auto-remove dead proxies after testing, detailed test results with IP and timing
- **9 Navigation Panels** - Added Explorer panel (Scraper, Explorer, Proxies, Tools, Headers, History, Logs, Scheduler, Settings)

---

## What's New in v1.2.0

- **Scrape History** - Full session history with stats, search, detail view, and re-export
- **Data Transform Pipeline** - 15 post-extraction operations (trim, uppercase, strip HTML, remove URLs, regex replace, type conversion, etc.)
- **Captcha Detection** - Automatic detection of reCAPTCHA, hCaptcha, Cloudflare challenges with warning logs
- **Bug Fixes** - Fixed dashboard options bar reference error, removed duplicate dataclass fields
- **8 Navigation Panels** - Scraper, Proxies, Tools, Headers, History, Logs, Scheduler, Settings

---

## What's New in v1.1.0

- **Real-time Log Viewer** - Color-coded log panel with level filtering, auto-scroll, and copy-all
- **Sortable Data Table** - Professional results display with clickable column headers for sorting
- **Results Search & Filter** - Instantly filter results by typing in the search bar
- **Project Management UI** - Save, load, and manage scraping projects from the dashboard
- **Import/Export Rules** - Share extraction rules as JSON files
- **Crawl Depth Control** - Configure link-following depth from the UI
- **Custom User-Agent** - Set custom User-Agent string in settings
- **Application Icon** - Professional multi-resolution Windows icon
- **11 Pre-built Templates** - Page Title, Links, Images, Tables, Articles, Products, Contact Info, SEO, API/JSON, Directory Crawler, and Full Text
- **UI Polish** - Fixed duplicate imports, improved layout, SQLite export button added

---

## Screenshot

> Modern dark/light-themed UI with sidebar navigation, real-time log viewer, sortable data table, and comprehensive data extraction tools.

## Features

### Dual Scraping Engines
| Feature | Static Engine | Dynamic Engine |
|---------|:------------:|:-------------:|
| Speed | Very Fast | Moderate |
| JavaScript | No | Full Support |
| Stealth | N/A | Anti-Detection |
| Resources | Minimal | Browser Required |

### Data Extraction Methods (9 methods)
- **CSS Selectors** - Standard CSS selector syntax
- **XPath** - Full XPath 1.0 support
- **Regular Expressions** - Pattern matching with groups
- **JSON Path** - Extract from embedded JSON/API responses
- **Table Extraction** - Auto-detect and extract HTML tables
- **Link/Image Extraction** - Bulk URL and image harvesting
- **Full Text** - Complete page text content
- **HTML Attributes** - Extract any element attribute
- **Meta Tags** - Page metadata extraction

### Export Formats (6 formats)
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

### Rate Limiting (4 strategies)
- **Token Bucket** - Burst-friendly rate control
- **Sliding Window** - Precise request counting
- **Fixed Delay** - Simple time-based throttling
- **Adaptive** - Auto-adjusts based on response times
- Per-domain configuration
- Global request rate control

### Task Scheduler (5 types)
- One-time, interval, daily, weekly, monthly schedules
- Auto-export on completion
- Execution history tracking

### Project Management
- Save and load project configurations
- Import/export extraction rules as JSON
- 11 pre-built templates for common scenarios
- Persistent storage across sessions

### UI Features
- Dark and light theme support
- Real-time log viewer with filtering
- Sortable data table with search
- Sidebar navigation
- Progress tracking
- Professional icon and branding

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
|   +-- templates.py           # 11 pre-built templates
|   +-- history.py             # Scrape session history
|   +-- captcha_detector.py    # Captcha detection
+-- ui/                        # User interface
|   +-- main_window.py         # Main application window
|   +-- styles.py              # Design system & theme
|   +-- components/            # Reusable UI components
|   |   +-- table_widget.py    # Sortable data table
|   +-- panels/                # UI panels
|       +-- dashboard_panel.py # Main scraper panel
|       +-- proxy_panel.py     # Proxy management
|       +-- tools_panel.py     # Regex tester & HTML preview
|       +-- headers_panel.py   # Headers & cookies management
|       +-- scheduler_panel.py # Task scheduler
|       +-- settings_panel.py  # Settings
|       +-- log_panel.py       # Real-time log viewer
|       +-- history_panel.py   # Scrape session history
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
