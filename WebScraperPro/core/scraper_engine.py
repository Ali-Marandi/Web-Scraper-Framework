"""
WebScraper Pro - Main Scraper Engine
Orchestrates all scraping components: static/dynamic scrapers, proxy, rate limiting, parsing, export.
"""

import threading
import time
import json
import os
import uuid
import re
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from .static_scraper import StaticScraper, RequestConfig
from .dynamic_scraper import DynamicScraper, BrowserConfig, PageAction
from .proxy_manager import ProxyManager, ProxyConfig, ProxyType
from .rate_limiter import RateLimiter, LimitStrategy, DomainLimits
from .data_parser import DataParser, ExtractionRule, ExtractionMethod, ParseResult
from .data_exporter import DataExporter
from .scheduler import TaskScheduler, ScheduledTask, ScheduleType


class ScrapingMode(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    AUTO = "auto"


class EngineState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    success: bool
    url: str
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    records_count: int = 0
    elapsed_time: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    total_bytes: int = 0
    export_path: Optional[str] = None


@dataclass
class ScrapingProject:
    """A saved scraping project configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Untitled Project"
    urls: List[str] = field(default_factory=list)
    mode: ScrapingMode = ScrapingMode.STATIC
    extraction_rules: List[Dict] = field(default_factory=list)
    use_proxy: bool = False
    use_rate_limit: bool = True
    request_config: Dict = field(default_factory=dict)
    browser_config: Dict = field(default_factory=dict)
    page_actions: List[Dict] = field(default_factory=list)
    export_format: str = "json"
    export_path: str = ""
    auto_scroll: bool = False
    max_depth: int = 1
    follow_links: bool = False
    max_pages: int = 100
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    concurrent_workers: int = 1
    use_proxy: bool = False
    use_rate_limit: bool = True

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "urls": self.urls,
            "mode": self.mode.value, "extraction_rules": self.extraction_rules,
            "use_proxy": self.use_proxy, "use_rate_limit": self.use_rate_limit,
            "request_config": self.request_config, "browser_config": self.browser_config,
            "page_actions": self.page_actions, "export_format": self.export_format,
            "export_path": self.export_path, "auto_scroll": self.auto_scroll,
            "max_depth": self.max_depth, "follow_links": self.follow_links,
            "max_pages": self.max_pages, "concurrent_workers": self.concurrent_workers,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ScrapingProject":
        d = data.copy()
        d["mode"] = ScrapingMode(d.get("mode", "static"))
        rules = []
        for r in d.get("extraction_rules", []):
            rules.append(r)
        d["extraction_rules"] = rules
        return cls(**d)


class ScraperEngine:
    """
    Main scraping engine that orchestrates all components.
    
    This is the central controller that manages:
    - Static and dynamic scraping
    - Proxy management and rotation
    - Rate limiting per domain
    - Data extraction with configurable rules
    - Multi-format data export
    - Project management (save/load)
    - Task scheduling
    - Real-time progress reporting
    - Thread-safe operation
    """

    def __init__(self):
        self._state = EngineState.IDLE
        self._state_lock = threading.RLock()

        # Core components
        self._proxy_manager = ProxyManager()
        self._rate_limiter = RateLimiter(LimitStrategy.TOKEN_BUCKET)
        self._data_parser = DataParser()
        self._data_exporter = DataExporter()
        self._scheduler = TaskScheduler()

        # Scrapers (created on demand)
        self._static_scraper: Optional[StaticScraper] = None
        self._dynamic_scraper: Optional[DynamicScraper] = None

        # Projects
        self._projects: Dict[str, ScrapingProject] = {}
        self._current_project: Optional[ScrapingProject] = None

        # Results
        self._results: List[Dict[str, Any]] = []
        self._errors: List[Dict] = []

        # Progress
        self._progress_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None
        self._progress = {"current": 0, "total": 0, "status": "idle"}

        # Config
        self._projects_dir = "projects"
        os.makedirs(self._projects_dir, exist_ok=True)

        self._load_projects()

    @property
    def state(self) -> EngineState:
        return self._state

    @property
    def results(self) -> List[Dict]:
        return list(self._results)

    @property
    def result_count(self) -> int:
        return len(self._results)

    @property
    def errors(self) -> List[Dict]:
        return list(self._errors)

    @property
    def progress(self) -> Dict:
        return dict(self._progress)

    @property
    def proxy_manager(self) -> ProxyManager:
        return self._proxy_manager

    @property
    def rate_limiter(self) -> RateLimiter:
        return self._rate_limiter

    @property
    def data_parser(self) -> DataParser:
        return self._data_parser

    @property
    def data_exporter(self) -> DataExporter:
        return self._data_exporter

    @property
    def scheduler(self) -> TaskScheduler:
        return self._scheduler

    @property
    def projects(self) -> List[ScrapingProject]:
        return list(self._projects.values())

    @property
    def current_project(self) -> Optional[ScrapingProject]:
        return self._current_project

    def set_progress_callback(self, callback: Callable) -> None:
        self._progress_callback = callback

    def set_log_callback(self, callback: Callable) -> None:
        self._log_callback = callback

    def _log(self, message: str, level: str = "info") -> None:
        if self._log_callback:
            self._log_callback(message, level)

    def _update_progress(self, current: int, total: int, status: str = "") -> None:
        self._progress = {"current": current, "total": total, "status": status or self._progress["status"]}
        if self._progress_callback:
            self._progress_callback(self._progress)

    # ---- Project Management ----

    def create_project(self, name: str = "", **kwargs) -> ScrapingProject:
        project = ScrapingProject(name=name or "Untitled Project", **kwargs)
        project.updated_at = datetime.now().isoformat()
        self._projects[project.id] = project
        self._save_projects()
        self._log(f"Project created: {project.name} ({project.id})")
        return project

    def load_project(self, project_id: str) -> Optional[ScrapingProject]:
        project = self._projects.get(project_id)
        if project:
            self._current_project = project
            self._data_parser.clear_rules()
            for rule_dict in project.extraction_rules:
                rule = ExtractionRule(
                    name=rule_dict["name"],
                    method=ExtractionMethod(rule_dict["method"]),
                    selector=rule_dict["selector"],
                    attribute=rule_dict.get("attribute"),
                    default=rule_dict.get("default"),
                    prefix=rule_dict.get("prefix", ""),
                    suffix=rule_dict.get("suffix", ""),
                    is_list=rule_dict.get("is_list", False),
                    max_items=rule_dict.get("max_items", 0),
                )
                self._data_parser.add_rule(rule)
            self._log(f"Project loaded: {project.name}")
        return project

    def delete_project(self, project_id: str) -> bool:
        if project_id in self._projects:
            name = self._projects[project_id].name
            del self._projects[project_id]
            if self._current_project and self._current_project.id == project_id:
                self._current_project = None
            self._save_projects()
            self._log(f"Project deleted: {name}")
            return True
        return False

    def save_current_project(self) -> bool:
        if not self._current_project:
            return False
        self._current_project.updated_at = datetime.now().isoformat()
        self._current_project.extraction_rules = [
            {"name": r.name, "method": r.method.value, "selector": r.selector,
             "attribute": r.attribute, "default": r.default,
             "prefix": r.prefix, "suffix": r.suffix,
             "is_list": r.is_list, "max_items": r.max_items}
            for r in self._data_parser.rules
        ]
        self._projects[self._current_project.id] = self._current_project
        self._save_projects()
        self._log(f"Project saved: {self._current_project.name}")
        return True

    def _save_projects(self) -> None:
        try:
            data = {pid: p.to_dict() for pid, p in self._projects.items()}
            path = os.path.join(self._projects_dir, "projects.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"Failed to save projects: {e}", "error")

    def _load_projects(self) -> None:
        path = os.path.join(self._projects_dir, "projects.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for pid, pdata in data.items():
                self._projects[pid] = ScrapingProject.from_dict(pdata)
            self._log(f"Loaded {len(self._projects)} projects")
        except Exception as e:
            self._log(f"Failed to load projects: {e}", "error")

    # ---- Scraping ----

    def scrape_urls(self, urls: List[str], mode: ScrapingMode = ScrapingMode.STATIC,
                    callback: Optional[Callable] = None) -> ScrapingResult:
        """
        Scrape a list of URLs with configured extraction rules.
        Runs in a background thread.
        """
        result = ScrapingResult(success=False, url="", elapsed_time=0)
        thread = threading.Thread(
            target=self._scrape_urls_sync,
            args=(urls, mode, result, callback),
            daemon=True,
        )
        thread.start()
        return result

    def _scrape_single_url(self, url: str, static_scraper: Optional[StaticScraper],
                                dynamic_scraper: Optional[DynamicScraper],
                                mode: ScrapingMode, use_proxy: bool, use_rate_limit: bool,
                                auto_scroll: bool, page_actions: list) -> tuple:
        """Scrape a single URL. Returns (url, result_row, error_dict, metadata, new_links)."""
        if self._state == EngineState.STOPPING:
            return (url, None, None, {}, [])

        use_dynamic = (mode == ScrapingMode.DYNAMIC)
        html_content = None
        metadata = {}
        new_links = []

        try:
            if use_dynamic and dynamic_scraper:
                actions = [PageAction(**a) for a in page_actions]
                html_content, metadata = dynamic_scraper.scrape(url, actions=actions, auto_scroll=auto_scroll)
            elif static_scraper:
                html_content, metadata = static_scraper.fetch(url)

            if html_content:
                parse_result = self._data_parser.parse(html_content, url)
                row = None
                if parse_result.fields:
                    row = parse_result.to_dict()
                    row["_url"] = url
                    row["_scraped_at"] = datetime.now().isoformat()

                # Extract links for crawling
                if self._current_project and self._current_project.follow_links:
                    try:
                        soup = __import__("bs4", fromlist=["BeautifulSoup"]).BeautifulSoup(html_content, "lxml")
                        links = self._data_parser._extract_links(
                            soup, url, ExtractionRule(name="", method=ExtractionMethod.LINKS, selector="a")
                        )
                        base = urlparse(url)
                        for link in links:
                            parsed = urlparse(link)
                            if parsed.netloc == base.netloc:
                                new_links.append(link)
                    except Exception:
                        pass

                return (url, row, None, metadata, new_links)
            else:
                error_msg = metadata.get("error", "No content")
                return (url, None, {"url": url, "error": error_msg}, metadata, [])

        except Exception as e:
            return (url, None, {"url": url, "error": str(e)[:200]}, {}, [])

    def _scrape_urls_sync(self, urls: List[str], mode: ScrapingMode,
                           result: ScrapingResult, callback: Optional[Callable]) -> None:
        """Synchronous scraping implementation with concurrent worker support."""
        with self._state_lock:
            if self._state == EngineState.RUNNING:
                result.error = "Engine is already running"
                return
            self._state = EngineState.RUNNING

        self._results.clear()
        self._errors.clear()
        start_time = time.time()
        total = len(urls)

        # Determine workers
        workers = 1
        if mode == ScrapingMode.STATIC and self._current_project:
            workers = max(1, self._current_project.concurrent_workers or 1)
        elif mode == ScrapingMode.DYNAMIC:
            workers = 1  # Dynamic scraping is not thread-safe

        self._update_progress(0, total, "running")
        self._log(f"Starting scrape of {total} URLs in {mode.value} mode ({workers} worker(s))")

        static_scraper = None
        dynamic_scraper = None

        try:
            if mode in (ScrapingMode.STATIC, ScrapingMode.AUTO):
                req_config = RequestConfig(**self._current_project.request_config) if self._current_project else RequestConfig()
                static_scraper = StaticScraper(
                    config=req_config,
                    proxy_manager=self._proxy_manager if self._current_project and self._current_project.use_proxy else None,
                    rate_limiter=self._rate_limiter if self._current_project and self._current_project.use_rate_limit else None,
                )

            if mode in (ScrapingMode.DYNAMIC, ScrapingMode.AUTO):
                browser_cfg = BrowserConfig(**self._current_project.browser_config) if self._current_project else BrowserConfig()
                dynamic_scraper = DynamicScraper(config=browser_cfg)

            use_proxy = self._current_project.use_proxy if self._current_project else False
            use_rate_limit = self._current_project.use_rate_limit if self._current_project else True
            auto_scroll = self._current_project.auto_scroll if self._current_project else False
            page_actions = self._current_project.page_actions if self._current_project else []
            max_pages = (self._current_project.max_pages if self._current_project else 100)

            visited_urls = set()
            urls_to_scrape = list(urls)
            pages_scraped = 0
            results_lock = threading.Lock()
            errors_lock = threading.Lock()
            links_lock = threading.Lock()

            while urls_to_scrape and pages_scraped < max_pages:
                if self._state == EngineState.STOPPING:
                    break

                # Take a batch
                batch_size = min(len(urls_to_scrape), max_pages - pages_scraped)
                batch = []
                for _ in range(batch_size):
                    if not urls_to_scrape:
                        break
                    url = urls_to_scrape.pop(0)
                    if url not in visited_urls:
                        visited_urls.add(url)
                        batch.append(url)

                if not batch:
                    break

                if workers > 1 and len(batch) > 1:
                    # Concurrent scraping
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = {
                            executor.submit(
                                self._scrape_single_url, url, static_scraper, dynamic_scraper,
                                mode, use_proxy, use_rate_limit, auto_scroll, page_actions
                            ): url for url in batch
                        }
                        for future in as_completed(futures):
                            if self._state == EngineState.STOPPING:
                                break
                            url, row, error, metadata, new_links = future.result()

                            with results_lock:
                                if row:
                                    self._results.append(row)
                            with errors_lock:
                                if error:
                                    self._errors.append(error)

                            status = metadata.get("status_code", 0)
                            if status:
                                result.status_codes[status] = result.status_codes.get(status, 0) + 1
                            result.total_bytes += metadata.get("content_length", 0)

                            with links_lock:
                                for link in new_links:
                                    if link not in visited_urls:
                                        urls_to_scrape.append(link)

                            pages_scraped += 1
                            self._update_progress(pages_scraped, total, "running")
                            if callback:
                                callback(pages_scraped, total, len(self._results))
                else:
                    # Sequential scraping (dynamic mode or 1 worker)
                    for url in batch:
                        if self._state == EngineState.STOPPING:
                            break
                        url, row, error, metadata, new_links = self._scrape_single_url(
                            url, static_scraper, dynamic_scraper, mode,
                            use_proxy, use_rate_limit, auto_scroll, page_actions
                        )

                        if row:
                            self._results.append(row)
                        if error:
                            self._errors.append(error)

                        status = metadata.get("status_code", 0)
                        if status:
                            result.status_codes[status] = result.status_codes.get(status, 0) + 1
                        result.total_bytes += metadata.get("content_length", 0)

                        for link in new_links:
                            if link not in visited_urls:
                                urls_to_scrape.append(link)

                        pages_scraped += 1
                        self._update_progress(pages_scraped, total, "running")
                        if callback:
                            callback(pages_scraped, total, len(self._results))

        except Exception as e:
            result.error = str(e)[:200]
            self._log(f"Scraping error: {e}", "error")

        finally:
            if static_scraper:
                static_scraper.close()
            if dynamic_scraper:
                dynamic_scraper.close()

            elapsed = time.time() - start_time
            result.success = len(self._results) > 0
            result.data = list(self._results)
            result.records_count = len(self._results)
            result.elapsed_time = round(elapsed, 2)

            with self._state_lock:
                self._state = EngineState.IDLE
            self._update_progress(total, total, "completed")
            self._log(f"Scraping completed: {result.records_count} records in {elapsed:.1f}s")

            # Auto-export if configured
            if (result.success and self._current_project
                    and self._current_project.export_format
                    and self._current_project.export_path):
                try:
                    result.export_path = self._data_exporter.export(
                        self._results, self._current_project.export_format,
                        self._current_project.export_path,
                    )
                    self._log(f"Auto-exported to: {result.export_path}")
                except Exception as e:
                    self._log(f"Export failed: {e}", "error")

    def fetch_html_preview(self, url: str, mode: ScrapingMode = ScrapingMode.STATIC) -> tuple:
        """Fetch a URL and return (html_content, metadata) for preview. Thread-safe."""
        def _fetch():
            if mode == ScrapingMode.DYNAMIC:
                scraper = DynamicScraper()
                html, meta = scraper.scrape(url)
                scraper.close()
            else:
                scraper = StaticScraper()
                html, meta = scraper.fetch(url)
                scraper.close()
            return html, meta

        if threading.current_thread() is threading.main_thread():
            # Run in background to avoid blocking UI
            result_holder = [None]
            def _run():
                result_holder[0] = _fetch()
            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout=60)
            return result_holder[0] or (None, {"error": "Timeout"})
        return _fetch()

    def test_regex(self, pattern: str, text: str) -> list:
        """Test a regex pattern against text and return all matches."""
        try:
            return re.findall(pattern, text)
        except re.error as e:
            return [f"Regex error: {e}"]

    def stop(self) -> None:
        """Stop the current scraping operation."""
        with self._state_lock:
            if self._state == EngineState.RUNNING:
                self._state = EngineState.STOPPING
        self._update_progress(self._progress["current"], self._progress["total"], "stopping")
        self._log("Stopping scraping...")

    def export_results(self, format: str, filepath: str, **kwargs) -> str:
        """Export current results to a file."""
        return self._data_exporter.export(self._results, format, filepath, **kwargs)

    def clear_results(self) -> None:
        self._results.clear()
        self._errors.clear()
        self._update_progress(0, 0, "idle")

    def quick_scrape(self, url: str, mode: ScrapingMode = ScrapingMode.STATIC) -> ParseResult:
        """Quick scrape a single URL for preview/testing."""
        if mode == ScrapingMode.DYNAMIC:
            scraper = DynamicScraper()
            html, meta = scraper.scrape(url)
            scraper.close()
        else:
            scraper = StaticScraper()
            html, meta = scraper.fetch(url)
            scraper.close()

        if html is None:
            return ParseResult(url=url, error=meta.get("error", "Failed"))

        return self._data_parser.parse(html, url)

    def get_engine_stats(self) -> Dict:
        """Get comprehensive engine statistics."""
        stats = {
            "state": self._state.value,
            "total_results": len(self._results),
            "total_errors": len(self._errors),
            "projects_count": len(self._projects),
            "proxies": self._proxy_manager.get_summary(),
            "rate_limiter": self._rate_limiter.get_stats(),
            "scheduler": self._scheduler.get_summary(),
        }
        return stats
