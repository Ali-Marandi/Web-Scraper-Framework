from bs4 import BeautifulSoup, SoupStrainer
from lxml import html as lhtml
from urllib.parse import urlparse, urljoin, urlunparse
import re
import threading
import time
from typing import Optional, List, Dict, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class LinkCategory(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    EMAIL = "email"
    SOCIAL = "social"
    FEED = "feed"
    OTHER = "other"


DOCUMENT_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".txt", ".csv", ".rtf", ".odt", ".ods", ".epub"}
VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}
AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff"}
FEED_EXTS = {".rss", ".atom", ".xml"}
SOCIAL_DOMAINS = {"facebook.com", "twitter.com", "x.com", "linkedin.com", "instagram.com",
                 "youtube.com", "tiktok.com", "reddit.com", "pinterest.com", "tumblr.com",
                 "telegram.org", "t.me", "whatsapp.com", "discord.com", "github.com",
                 "gitlab.com", "stackoverflow.com"}


@dataclass
class LinkInfo:
    url: str
    text: str = ""
    category: LinkCategory = LinkCategory.OTHER
    status_code: int = 0
    response_time: float = 0.0
    content_type: str = ""
    depth: int = 0
    source_url: str = ""
    validated: bool = False
    is_broken: bool = False

    @property
    def status_text(self) -> str:
        if not self.validated:
            return "Not checked"
        if self.status_code == 0:
            return "Failed"
        return str(self.status_code)

    @property
    def status_color(self) -> str:
        if not self.validated:
            return "muted"
        if self.is_broken or self.status_code >= 400:
            return "error"
        if self.status_code >= 300:
            return "warning"
        return "success"


@dataclass
class ExplorerResult:
    base_url: str = ""
    total_links: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    links: List[LinkInfo] = field(default_factory=list)
    pages_crawled: int = 0
    max_depth_reached: int = 0
    elapsed_time: float = 0.0
    broken_count: int = 0

    def get_by_category(self, cat: LinkCategory) -> List[LinkInfo]:
        return [l for l in self.links if l.category == cat]

    def get_categorized_dict(self) -> Dict[str, List[LinkInfo]]:
        result = {}
        for link in self.links:
            cat = link.category.value
            if cat not in result:
                result[cat] = []
            result[cat].append(link)
        return result


class URLExplorer:
    """
    Advanced URL/link explorer that crawls pages and categorizes all found links.
    
    Features:
    - Extracts all links (anchors, images, documents, emails, etc.)
    - Categorizes links (internal, external, documents, social, etc.)
    - Validates links with HTTP status codes
    - Multi-depth crawling with configurable limits
    - Thread-safe with cancellation support
    - Real-time progress reporting
    """

    def __init__(self):
        self._stop_flag = False
        self._lock = threading.RLock()
        self._visited: Set[str] = set()
        self._progress_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable) -> None:
        self._progress_callback = callback

    def set_log_callback(self, callback: Callable) -> None:
        self._log_callback = callback

    def stop(self) -> None:
        self._stop_flag = True

    def _log(self, msg: str, level: str = "info") -> None:
        if self._log_callback:
            self._log_callback(msg, level)

    def _report_progress(self, current: int, total: int, status: str = "") -> None:
        if self._progress_callback:
            self._progress_callback({"current": current, "total": total, "status": status})

    def _categorize_url(self, url: str, base_parsed: urlparse) -> LinkCategory:
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        if "." in path_lower:
            ext = path_lower.rsplit(".", 1)[-1].lower()
            if f".{ext}" in DOCUMENT_EXTS:
                return LinkCategory.DOCUMENT
            if f".{ext}" in VIDEO_EXTS:
                return LinkCategory.VIDEO
            if f".{ext}" in AUDIO_EXTS:
                return LinkCategory.AUDIO
            if f".{ext}" in IMAGE_EXTS:
                return LinkCategory.IMAGE
            if f".{ext}" in FEED_EXTS:
                return LinkCategory.FEED

        if url.startswith("mailto:"):
            return LinkCategory.EMAIL

        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain in SOCIAL_DOMAINS or any(domain.endswith(f".{sd}") for sd in SOCIAL_DOMAINS):
            return LinkCategory.SOCIAL

        base_domain = base_parsed.netloc.lower()
        if base_domain.startswith("www."):
            base_domain = base_domain[4:]
        if domain == base_domain:
            return LinkCategory.INTERNAL
        else:
            return LinkCategory.EXTERNAL

    def _normalize_url(self, url: str, base_url: str) -> Optional[str]:
        try:
            full = urljoin(base_url, url)
            parsed = urlparse(full)
            if parsed.scheme not in ("http", "https"):
                return None
            if not parsed.netloc:
                return None
            cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                                   parsed.params, parsed.query, ""))
            return cleaned
        except Exception:
            return None

    def extract_links_from_html(self, html_content: str, base_url: str,
                                  depth: int = 0, source_url: str = "") -> List[LinkInfo]:
        """Extract and categorize all links from an HTML page."""
        links = []
        base_parsed = urlparse(base_url)
        seen = set()

        try:
            soup = BeautifulSoup(html_content, "lxml")
        except Exception:
            return links

        # Anchor links
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("#", "javascript:", "data:", "void", "tel:")):
                continue
            if href.startswith("mailto:"):
                email_addr = href[7:].strip()
                link = LinkInfo(
                    url=href, text=email_addr or a.get_text(strip=True),
                    category=LinkCategory.EMAIL, depth=depth, source_url=source_url or base_url,
                )
                if href not in seen:
                    seen.add(href)
                    links.append(link)
                continue

            normalized = self._normalize_url(href, base_url)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)

            cat = self._categorize_url(normalized, base_parsed)
            link = LinkInfo(
                url=normalized, text=a.get_text(strip=True)[:200],
                category=cat, depth=depth, source_url=source_url or base_url,
            )
            links.append(link)

        # Image links
        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            normalized = self._normalize_url(src, base_url)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            links.append(LinkInfo(
                url=normalized, text=img.get("alt", ""),
                category=LinkCategory.IMAGE, depth=depth, source_url=source_url or base_url,
            ))

        # Source links (video, audio)
        for tag_name in ("source", "video", "audio", "embed", "iframe"):
            for src_attr in ("src", "data-src", "href"):
                for el in soup.find_all(tag_name, {src_attr: True}):
                    src = el[src_attr].strip()
                    normalized = self._normalize_url(src, base_url)
                    if not normalized or normalized in seen:
                        continue
                    seen.add(normalized)
                    cat = self._categorize_url(normalized, base_parsed)
                    if cat == LinkCategory.OTHER:
                        if tag_name in ("video", "source"):
                            cat = LinkCategory.VIDEO
                        elif tag_name == "audio":
                            cat = LinkCategory.AUDIO
                    links.append(LinkInfo(
                        url=normalized, text=el.get_text(strip=True)[:100],
                        category=cat, depth=depth, source_url=source_url or base_url,
                    ))

        # Link tags (feeds, stylesheets, etc.)
        for link_el in soup.find_all("link", href=True):
            href = link_el["href"].strip()
            rel = link_el.get("rel", [""])
            if "stylesheet" in rel or "icon" in rel:
                continue
            normalized = self._normalize_url(href, base_url)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            cat = self._categorize_url(normalized, base_parsed)
            if cat == LinkCategory.OTHER and "alternate" in rel:
                cat = LinkCategory.FEED
            links.append(LinkInfo(
                url=normalized, text=str(rel),
                category=cat, depth=depth, source_url=source_url or base_url,
            ))

        return links

    def validate_links(self, links: List[LinkInfo], max_workers: int = 20,
                       timeout: float = 10.0, callback: Optional[Callable] = None) -> List[LinkInfo]:
        """Validate links by making HEAD requests to check status codes."""
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed

        validatable = [l for l in links if not l.url.startswith("mailto:")]
        total = len(validatable)
        completed = [0]
        lock = threading.Lock()

        def _check(link: LinkInfo):
            if self._stop_flag:
                return link
            try:
                start = time.time()
                resp = requests.head(link.url, timeout=timeout, allow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"})
                elapsed = time.time() - start
                link.status_code = resp.status_code
                link.response_time = round(elapsed, 3)
                link.content_type = resp.headers.get("Content-Type", "")
                link.validated = True
                link.is_broken = resp.status_code >= 400
            except requests.exceptions.Timeout:
                link.validated = True
                link.is_broken = True
                link.status_code = 0
            except requests.exceptions.ConnectionError:
                link.validated = True
                link.is_broken = True
                link.status_code = 0
            except Exception:
                link.validated = True
                link.is_broken = True
                link.status_code = 0

            with lock:
                completed[0] += 1
                if callback:
                    callback(completed[0], total, link)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_check, l): l for l in validatable}
            for f in as_completed(futures):
                if self._stop_flag:
                    break

        return links

    def explore(self, start_url: str, max_depth: int = 1, max_pages: int = 50,
                validate: bool = False, callback: Optional[Callable] = None) -> ExplorerResult:
        """
        Explore a URL and extract/categorize/validate all links.
        Returns an ExplorerResult with all discovered links.
        """
        import requests

        self._stop_flag = False
        self._visited.clear()
        start_time = time.time()

        result = ExplorerResult(base_url=start_url)
        base_parsed = urlparse(start_url)

        queue = [(start_url, 0)]
        pages_crawled = 0

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        while queue and pages_crawled < max_pages and not self._stop_flag:
            url, depth = queue.pop(0)

            normalized = self._normalize_url(url, start_url)
            if not normalized or normalized in self._visited:
                continue
            self._visited.add(normalized)

            if depth > max_depth:
                continue

            self._log(f"Crawling: {normalized[:80]} (depth {depth})")
            self._report_progress(pages_crawled, max_pages, "exploring")

            try:
                resp = session.get(normalized, timeout=15, verify=False, allow_redirects=True)
                if "text/html" not in resp.headers.get("Content-Type", ""):
                    continue
            except Exception as e:
                self._log(f"Failed to fetch {normalized[:60]}: {str(e)[:60]}", "warning")
                continue

            page_links = self.extract_links_from_html(
                resp.text, normalized, depth=depth, source_url=normalized,
            )
            result.links.extend(page_links)
            pages_crawled += 1

            if depth < max_depth:
                for link in page_links:
                    if link.category in (LinkCategory.INTERNAL, LinkCategory.EXTERNAL):
                        if link.url not in self._visited and link.depth <= max_depth:
                            if link.category == LinkCategory.INTERNAL:
                                queue.append((link.url, depth + 1))

            if callback:
                callback(pages_crawled, len(result.links))

        session.close()

        if self._stop_flag:
            self._log("Exploration stopped by user", "warning")

        if validate and not self._stop_flag:
            self._log(f"Validating {len(result.links)} links...")
            result.links = self.validate_links(result.links, callback=callback)

        result.pages_crawled = pages_crawled
        result.total_links = len(result.links)
        result.max_depth_reached = max((l.depth for l in result.links), default=0)
        result.elapsed_time = round(time.time() - start_time, 2)
        result.broken_count = sum(1 for l in result.links if l.is_broken)

        for link in result.links:
            cat = link.category.value
            result.categories[cat] = result.categories.get(cat, 0) + 1

        self._report_progress(pages_crawled, pages_crawled, "completed")
        self._log(f"Exploration done: {result.total_links} links from {result.pages_crawled} pages in {result.elapsed_time}s")

        return result

    def quick_explore(self, html_content: str, url: str) -> ExplorerResult:
        """Quick explore a single page's HTML without fetching."""
        start_time = time.time()
        links = self.extract_links_from_html(html_content, url, depth=0)

        result = ExplorerResult(base_url=url, links=links, pages_crawled=1)
        result.total_links = len(links)
        result.max_depth_reached = 0
        result.elapsed_time = round(time.time() - start_time, 2)
        result.broken_count = 0

        for link in links:
            cat = link.category.value
            result.categories[cat] = result.categories.get(cat, 0) + 1

        return result
