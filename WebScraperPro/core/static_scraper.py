"""
WebScraper Pro - Static Scraper
Handles static page scraping using requests + BeautifulSoup.
Supports sessions, custom headers, cookies, and retry logic.
"""

import time
import requests
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from .proxy_manager import ProxyManager, ProxyConfig
from .rate_limiter import RateLimiter
from .data_parser import DataParser, ParseResult
from .captcha_detector import detect_captcha, get_captcha_info_for_log


@dataclass
class RequestConfig:
    """Configuration for HTTP requests."""
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 2.0
    verify_ssl: bool = True
    follow_redirects: bool = True
    max_redirects: int = 10
    encoding: Optional[str] = None  # Force specific encoding
    headers: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    cookies: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Tuple[str, str]] = None  # (username, password)
    referrer: Optional[str] = None


class StaticScraper:
    """
    Static web page scraper.
    
    Features:
    - Session management with cookie persistence
    - Custom headers and authentication
    - Automatic retry with exponential backoff
    - Proxy support
    - Rate limiting integration
    - Encoding detection and handling
    - Response time tracking
    """

    def __init__(self, config: Optional[RequestConfig] = None,
                 proxy_manager: Optional[ProxyManager] = None,
                 rate_limiter: Optional[RateLimiter] = None):
        self._config = config or RequestConfig()
        self._proxy_manager = proxy_manager
        self._rate_limiter = rate_limiter
        self._session = requests.Session()
        self._session.headers.update(self._config.headers)
        if self._config.cookies:
            self._session.cookies.update(self._config.cookies)
        self._total_requests = 0
        self._total_bytes = 0
        self._errors = 0

    @property
    def config(self) -> RequestConfig:
        return self._config

    @config.setter
    def config(self, value: RequestConfig):
        self._config = value
        self._session.headers.update(value.headers)

    def update_headers(self, headers: Dict[str, str]) -> None:
        """Update or add request headers."""
        self._session.headers.update(headers)
        self._config.headers.update(headers)

    def update_cookies(self, cookies: Dict[str, str]) -> None:
        """Update session cookies."""
        self._session.cookies.update(cookies)
        self._config.cookies.update(cookies)

    def set_proxy_manager(self, manager: ProxyManager) -> None:
        self._proxy_manager = manager

    def set_rate_limiter(self, limiter: RateLimiter) -> None:
        self._rate_limiter = limiter

    def fetch(self, url: str, method: str = "GET",
              data: Optional[Dict] = None,
              json_data: Optional[Dict] = None,
              params: Optional[Dict] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Fetch a URL and return (html_content, metadata).
        """
        metadata = {
            "url": url,
            "method": method,
            "status_code": 0,
            "response_time": 0.0,
            "content_length": 0,
            "encoding": "",
            "content_type": "",
            "final_url": url,
            "error": None,
            "retries": 0,
        }

        # Rate limiting
        if self._rate_limiter:
            domain = urlparse(url).netloc
            if not self._rate_limiter.acquire(domain, timeout=30.0):
                metadata["error"] = "Rate limit timeout"
                return None, metadata

        proxy_config = None
        proxies = None
        if self._proxy_manager:
            proxy_config = self._proxy_manager.get_proxy()
            if proxy_config:
                proxies = proxy_config.requests_proxy

        html_content = None
        last_error = None

        for attempt in range(self._config.max_retries + 1):
            try:
                if self._config.referrer:
                    self._session.headers["Referer"] = self._config.referrer

                start = time.time()
                response = self._session.request(
                    method=method,
                    url=url,
                    data=data,
                    json=json_data,
                    params=params,
                    proxies=proxies,
                    timeout=self._config.timeout,
                    verify=self._config.verify_ssl,
                    allow_redirects=self._config.follow_redirects,
                )
                elapsed = time.time() - start

                metadata["status_code"] = response.status_code
                metadata["response_time"] = round(elapsed, 3)
                metadata["content_length"] = len(response.content)
                metadata["encoding"] = response.encoding or "unknown"
                metadata["content_type"] = response.headers.get("Content-Type", "")
                metadata["final_url"] = response.url
                metadata["retries"] = attempt

                response.raise_for_status()

                # Handle encoding
                if self._config.encoding:
                    response.encoding = self._config.encoding

                html_content = response.text
                self._total_bytes += len(response.content)

                # Captcha detection
                captcha = detect_captcha(html_content)
                if captcha.detected:
                    metadata["captcha_detected"] = True
                    metadata["captcha_type"] = captcha.captcha_type
                    metadata["captcha_info"] = captcha.description

                # Report success to proxy and rate limiter
                if proxy_config:
                    self._proxy_manager.report_success(proxy_config, elapsed)
                if self._rate_limiter:
                    domain = urlparse(url).netloc
                    self._rate_limiter.report_success(domain)
                    self._rate_limiter.report_response_time(domain, elapsed)

                break

            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP {e.response.status_code}"
                metadata["status_code"] = e.response.status_code
                if e.response.status_code in (403, 404, 410):
                    break  # Don't retry client errors (except 429)
            except requests.exceptions.Timeout:
                last_error = "Timeout"
            except requests.exceptions.ConnectionError:
                last_error = "Connection error"
            except requests.exceptions.TooManyRedirects:
                last_error = "Too many redirects"
                break
            except Exception as e:
                last_error = str(e)[:100]

            if proxy_config:
                self._proxy_manager.report_failure(proxy_config)
            if self._rate_limiter:
                domain = urlparse(url).netloc
                self._rate_limiter.report_error(domain)

            if attempt < self._config.max_retries:
                delay = self._config.retry_delay * (2 ** attempt)
                time.sleep(delay)

        if html_content is None:
            metadata["error"] = last_error
            self._errors += 1

        self._total_requests += 1
        return html_content, metadata

    def fetch_and_parse(self, url: str, parser: DataParser) -> ParseResult:
        """Fetch a URL and parse it with the given parser."""
        html, meta = self.fetch(url)
        if html is None:
            return ParseResult(url=url, error=meta.get("error", "Failed to fetch"))
        result = parser.parse(html, url)
        result.raw_data = meta
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            "total_requests": self._total_requests,
            "total_bytes": self._total_bytes,
            "errors": self._errors,
            "error_rate": round(self._errors / self._total_requests * 100, 1) if self._total_requests > 0 else 0,
        }

    def close(self) -> None:
        """Close the session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
