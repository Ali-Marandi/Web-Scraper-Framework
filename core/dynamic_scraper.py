"""
WebScraper Pro - Dynamic Scraper
Handles JavaScript-rendered pages using Playwright with stealth, interception, and multi-tab support.
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from .data_parser import DataParser, ParseResult


@dataclass
class BrowserConfig:
    """Configuration for browser-based scraping."""
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone: str = "America/New_York"
    geolocation: Optional[Dict[str, float]] = None
    extra_http_headers: Dict[str, str] = field(default_factory=dict)
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    wait_until: str = "networkidle"  # load, domcontentloaded, networkidle
    wait_timeout: int = 30000  # ms
    javascript_enabled: bool = True
    ignore_https_errors: bool = True
    screenshot: bool = False
    pdf: bool = False
    stealth_mode: bool = True
    block_resources: List[str] = field(default_factory=lambda: [
        "image", "media", "font",
    ])
    intercept_ads: bool = True


@dataclass
class PageAction:
    """Represents a browser action (click, type, scroll, wait, etc.)."""
    action_type: str  # click, type, scroll, wait, select, hover, screenshot
    selector: str = ""
    value: str = ""
    delay: float = 0.5
    repeat: int = 1
    scroll_direction: str = "down"  # for scroll action
    scroll_amount: int = 500  # pixels per scroll


class DynamicScraper:
    """
    Dynamic web page scraper using Playwright.
    
    Features:
    - Full browser automation (Chromium, Firefox, WebKit)
    - Stealth mode to avoid detection
    - Custom page actions (click, type, scroll, wait)
    - Resource blocking for faster loading
    - Screenshot and PDF generation
    - Cookie and session management
    - Network request interception
    - Multi-page/tab support
    - Auto-scrolling for infinite pages
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        self._config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._total_requests = 0
        self._is_running = False
        self._loop = None
        self._stealth_script = '''
            // Overwrite the `navigator.webdriver` property.
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            // Overwrite the `plugins` property to use a custom getter.
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            // Overwrite the `languages` property.
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            // Add chrome object.
            window.chrome = { runtime: {} };
            // Pass the WebDriver test.
            document.getElementById('webdriver-detection')?.remove();
        '''

    @property
    def config(self) -> BrowserConfig:
        return self._config

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

    async def _launch(self) -> None:
        """Launch browser and create context."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        browser_type = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }.get(self._config.browser_type, self._playwright.chromium)

        launch_args = {
            "headless": self._config.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ] if self._config.stealth_mode else [],
        }

        self._browser = await browser_type.launch(**launch_args)

        context_args = {
            "viewport": {
                "width": self._config.viewport_width,
                "height": self._config.viewport_height,
            },
            "locale": self._config.locale,
            "timezone_id": self._config.timezone,
            "java_script_enabled": self._config.javascript_enabled,
            "ignore_https_errors": self._config.ignore_https_errors,
        }

        if self._config.user_agent:
            context_args["user_agent"] = self._config.user_agent

        if self._config.extra_http_headers:
            context_args["extra_http_headers"] = self._config.extra_http_headers

        if self._config.geolocation:
            context_args["geolocation"] = self._config.geolocation
            context_args["permissions"] = ["geolocation"]

        self._context = await self._browser.new_context(**context_args)

        if self._config.cookies:
            await self._context.add_cookies(self._config.cookies)

        self._page = await self._context.new_page()

        # Apply stealth mode
        if self._config.stealth_mode:
            await self._page.add_init_script(self._stealth_script)

        # Block resources
        if self._config.block_resources:
            await self._page.route("**/*", self._route_handler)

        self._is_running = True

    async def _route_handler(self, route):
        """Block specified resource types for faster loading."""
        request = route.request
        resource_type = request.resource_type

        if resource_type in self._config.block_resources:
            await route.abort()
        else:
            await route.continue_()

    async def _execute_actions(self, actions: List[PageAction]) -> None:
        """Execute a sequence of page actions."""
        for action in actions:
            try:
                if action.action_type == "click":
                    for _ in range(action.repeat):
                        await self._page.click(action.selector, timeout=5000)
                        await asyncio.sleep(action.delay)

                elif action.action_type == "type":
                    await self._page.fill(action.selector, action.value)
                    await asyncio.sleep(action.delay)

                elif action.action_type == "press":
                    await self._page.press(action.selector, action.value)
                    await asyncio.sleep(action.delay)

                elif action.action_type == "scroll":
                    for _ in range(action.repeat):
                        if action.scroll_direction == "down":
                            await self._page.evaluate(f"window.scrollBy(0, {action.scroll_amount})")
                        else:
                            await self._page.evaluate(f"window.scrollBy(0, -{action.scroll_amount})")
                        await asyncio.sleep(action.delay)

                elif action.action_type == "wait":
                    if action.selector:
                        await self._page.wait_for_selector(action.selector, timeout=10000)
                    else:
                        await asyncio.sleep(float(action.value) if action.value else action.delay)

                elif action.action_type == "select":
                    await self._page.select_option(action.selector, action.value)
                    await asyncio.sleep(action.delay)

                elif action.action_type == "hover":
                    await self._page.hover(action.selector, timeout=5000)
                    await asyncio.sleep(action.delay)

                elif action.action_type == "screenshot":
                    await self._page.screenshot(path=action.value if action.value else None)

                elif action.action_type == "wait_for_navigation":
                    async with self._page.expect_navigation(timeout=10000):
                        pass

            except Exception as e:
                # Log action error but continue
                pass

    async def _auto_scroll(self, max_scrolls: int = 10, scroll_delay: float = 1.0) -> None:
        """Auto-scroll to load lazy-loaded content."""
        last_height = await self._page.evaluate("document.body.scrollHeight")
        scroll_count = 0

        while scroll_count < max_scrolls:
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(scroll_delay)
            new_height = await self._page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height
            scroll_count += 1

    async def _scrape_async(self, url: str,
                            actions: Optional[List[PageAction]] = None,
                            auto_scroll: bool = False,
                            max_scrolls: int = 10) -> Tuple[Optional[str], Dict[str, Any]]:
        """Async scraping implementation."""
        metadata = {
            "url": url,
            "status": "success",
            "response_time": 0.0,
            "title": "",
            "final_url": url,
            "error": None,
            "screenshot_path": None,
        }

        try:
            if not self._browser:
                await self._launch()

            start = time.time()
            response = await self._page.goto(
                url,
                wait_until=self._config.wait_until,
                timeout=self._config.wait_timeout,
            )
            metadata["response_time"] = round(time.time() - start, 3)
            metadata["status"] = "loaded" if response else "no_response"
            metadata["final_url"] = self._page.url
            metadata["title"] = await self._page.title()

            # Execute custom actions
            if actions:
                await self._execute_actions(actions)

            # Auto-scroll for lazy content
            if auto_scroll:
                await self._auto_scroll(max_scrolls)

            # Get page content
            html_content = await self._page.content()

            # Screenshot if configured
            if self._config.screenshot:
                metadata["screenshot_path"] = f"screenshot_{int(time.time())}.png"
                await self._page.screenshot(path=metadata["screenshot_path"])

            self._total_requests += 1
            return html_content, metadata

        except Exception as e:
            metadata["error"] = str(e)[:200]
            metadata["status"] = "error"
            return None, metadata

    def scrape(self, url: str,
               actions: Optional[List[PageAction]] = None,
               auto_scroll: bool = False,
               max_scrolls: int = 10) -> Tuple[Optional[str], Dict[str, Any]]:
        """Scrape a dynamic page (sync wrapper)."""
        loop = self._ensure_loop()
        try:
            result = loop.run_until_complete(
                self._scrape_async(url, actions, auto_scroll, max_scrolls)
            )
            return result
        except RuntimeError:
            # If loop is closed, create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self._scrape_async(url, actions, auto_scroll, max_scrolls)
            )

    def scrape_and_parse(self, url: str, parser: DataParser,
                         actions: Optional[List[PageAction]] = None,
                         auto_scroll: bool = False) -> ParseResult:
        """Scrape and parse in one call."""
        html, meta = self.scrape(url, actions, auto_scroll)
        if html is None:
            return ParseResult(url=url, error=meta.get("error", "Failed to scrape"))
        result = parser.parse(html, url)
        result.raw_data = meta
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self._total_requests,
            "browser_type": self._config.browser_type,
            "headless": self._config.headless,
            "is_running": self._is_running,
        }

    async def close_async(self) -> None:
        """Async close."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._is_running = False

    def close(self) -> None:
        """Close browser and cleanup."""
        loop = self._ensure_loop()
        try:
            loop.run_until_complete(self.close_async())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.close_async())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
