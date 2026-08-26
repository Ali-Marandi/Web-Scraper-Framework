"""
WebScraper Pro - Data Parser
Extracts data from HTML/pages using CSS selectors, XPath, regex, JSON paths, and structured extraction.
"""

import re
import json
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from bs4 import BeautifulSoup, Tag, NavigableString
from lxml import etree, html


class ExtractionMethod(Enum):
    CSS_SELECTOR = "css_selector"
    XPATH = "xpath"
    REGEX = "regex"
    JSON_PATH = "json_path"
    TABLE = "table"
    LINKS = "links"
    IMAGES = "images"
    FULL_TEXT = "full_text"
    HTML_ATTR = "html_attr"
    META = "meta"


@dataclass
class TransformRule:
    """Defines a data transformation to apply after extraction."""
    operation: str  # trim, uppercase, lowercase, strip_html, normalize_spaces, remove_numbers, remove_urls, replace
    pattern: str = ""  # For 'replace' operation: the pattern to find
    replacement: str = ""  # For 'replace' operation: the replacement string
    
    TRANSFORM_OPERATIONS = [
        "trim", "uppercase", "lowercase", "title_case",
        "strip_html", "normalize_spaces", "remove_numbers",
        "remove_urls", "remove_emails", "replace", "prefix", "suffix",
        "to_int", "to_float", "reverse",
    ]


def apply_transform(value: str, transform: TransformRule) -> str:
    """Apply a single transform to a value."""
    if not value:
        return value
    
    op = transform.operation
    
    if op == "trim":
        return value.strip()
    elif op == "uppercase":
        return value.upper()
    elif op == "lowercase":
        return value.lower()
    elif op == "title_case":
        return value.title()
    elif op == "strip_html":
        return re.sub(r'<[^>]+>', '', value)
    elif op == "normalize_spaces":
        return re.sub(r'\s+', ' ', value).strip()
    elif op == "remove_numbers":
        return re.sub(r'\d+', '', value)
    elif op == "remove_urls":
        return re.sub(r'https?://\S+', '', value)
    elif op == "remove_emails":
        return re.sub(r'\S+@\S+\.\S+', '', value)
    elif op == "replace":
        if transform.pattern:
            return re.sub(transform.pattern, transform.replacement, value)
        return value
    elif op == "prefix":
        return transform.replacement + value
    elif op == "suffix":
        return value + transform.replacement
    elif op == "reverse":
        return value[::-1]
    elif op == "to_int":
        match = re.search(r'-?\d+', value)
        return str(int(match.group())) if match else value
    elif op == "to_float":
        match = re.search(r'-?\d+\.?\d*', value)
        return str(float(match.group())) if match else value
    return value


def apply_transform_chain(value: str, transforms: list) -> str:
    """Apply a chain of transforms to a value."""
    for t in transforms:
        if isinstance(t, dict):
            t = TransformRule(**t)
        if isinstance(t, TransformRule):
            value = apply_transform(value, t)
    return value


@dataclass
class ExtractionRule:
    """Defines a single data extraction rule."""
    name: str  # Field name for output
    method: ExtractionMethod
    selector: str  # CSS selector, XPath, regex pattern, etc.
    attribute: Optional[str] = None  # For extracting specific attributes (href, src, etc.)
    default: Optional[str] = None  # Default value if not found
    prefix: str = ""  # Prefix to add to extracted value
    suffix: str = ""  # Suffix to add to extracted value
    regex_replace: Optional[Dict[str, str]] = None  # {pattern: replacement}
    transforms: List = field(default_factory=list)  # List of TransformRule dicts
    is_list: bool = False  # Extract multiple items
    max_items: int = 0  # Max items to extract (0 = unlimited)


@dataclass
class ExtractedField:
    """Represents a single extracted data field."""
    name: str
    value: Union[str, List[str]]
    method: str
    selector: str


@dataclass
class ParseResult:
    """Result of parsing a page."""
    url: str
    fields: List[ExtractedField] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    parse_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = {"url": self.url}
        for f in self.fields:
            result[f.name] = f.value
        if self.raw_data:
            result["_raw"] = self.raw_data
        if self.error:
            result["_error"] = self.error
        return result

    def to_row(self, field_names: List[str]) -> List[str]:
        """Convert to a flat list for CSV/Excel rows."""
        row = []
        for name in field_names:
            found = [f.value for f in self.fields if f.name == name]
            if found:
                val = found[0]
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val)
                row.append(str(val))
            else:
                row.append("")
        return row


class DataParser:
    """
    Advanced data extraction engine.
    
    Features:
    - CSS Selector extraction
    - XPath support
    - Regex pattern matching
    - JSON path extraction
    - Table data extraction
    - Link and image extraction
    - Meta tag extraction
    - Custom attribute extraction
    - Data cleaning and transformation
    - Multiple extraction rules per page
    """

    def __init__(self):
        self._rules: List[ExtractionRule] = []
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    @property
    def rules(self) -> List[ExtractionRule]:
        return list(self._rules)

    def add_rule(self, rule: ExtractionRule) -> None:
        """Add an extraction rule."""
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        for i, r in enumerate(self._rules):
            if r.name == name:
                self._rules.pop(i)
                return True
        return False

    def clear_rules(self) -> None:
        """Remove all rules."""
        self._rules.clear()

    def parse(self, html_content: str, url: str = "") -> ParseResult:
        """Parse HTML content using all configured rules."""
        import time
        start = time.time()
        result = ParseResult(url=url)

        try:
            soup = BeautifulSoup(html_content, "lxml")
            for rule in self._rules:
                try:
                    values = self._extract(soup, rule, html_content, url)
                    if values:
                        value = values if rule.is_list else values[0]
                        result.fields.append(ExtractedField(
                            name=rule.name,
                            value=value,
                            method=rule.method.value,
                            selector=rule.selector,
                        ))
                    elif rule.default is not None:
                        result.fields.append(ExtractedField(
                            name=rule.name,
                            value=rule.default,
                            method=rule.method.value,
                            selector=rule.selector,
                        ))
                except Exception as e:
                    result.fields.append(ExtractedField(
                        name=rule.name,
                        value=rule.default or "",
                        method=rule.method.value,
                        selector=rule.selector,
                    ))
        except Exception as e:
            result.error = str(e)

        result.parse_time = time.time() - start
        return result

    def _extract(self, soup: BeautifulSoup, rule: ExtractionRule,
                 raw_html: str, url: str) -> List[str]:
        """Extract data based on rule method."""
        method = rule.method

        if method == ExtractionMethod.CSS_SELECTOR:
            return self._extract_css(soup, rule)
        elif method == ExtractionMethod.XPATH:
            return self._extract_xpath(raw_html, rule)
        elif method == ExtractionMethod.REGEX:
            return self._extract_regex(raw_html, rule)
        elif method == ExtractionMethod.JSON_PATH:
            return self._extract_json(raw_html, rule)
        elif method == ExtractionMethod.TABLE:
            return self._extract_tables(soup, rule)
        elif method == ExtractionMethod.LINKS:
            return self._extract_links(soup, url, rule)
        elif method == ExtractionMethod.IMAGES:
            return self._extract_images(soup, url, rule)
        elif method == ExtractionMethod.FULL_TEXT:
            return self._extract_text(soup, rule)
        elif method == ExtractionMethod.HTML_ATTR:
            return self._extract_attr(soup, rule)
        elif method == ExtractionMethod.META:
            return self._extract_meta(soup, rule)
        return []

    def _apply_transforms(self, values: List[str], rule: ExtractionRule) -> List[str]:
        """Apply prefix, suffix, regex replacements, and transform chain."""
        result = []
        for val in values:
            val = str(val).strip()
            if rule.regex_replace:
                for pattern, replacement in rule.regex_replace.items():
                    val = re.sub(pattern, replacement, val)
            val = rule.prefix + val + rule.suffix
            # Apply transform chain
            if rule.transforms:
                val = apply_transform_chain(val, rule.transforms)
            result.append(val)

        if rule.max_items > 0:
            result = result[:rule.max_items]
        return result

    def _extract_css(self, soup: BeautifulSoup, rule: ExtractionRule) -> List[str]:
        """Extract using CSS selectors."""
        elements = soup.select(rule.selector)
        values = []
        for el in elements:
            if rule.attribute:
                val = el.get(rule.attribute, "")
            else:
                val = el.get_text(strip=True)
            values.append(str(val))
        return self._apply_transforms(values, rule)

    def _extract_xpath(self, raw_html: str, rule: ExtractionRule) -> List[str]:
        """Extract using XPath."""
        try:
            tree = html.fromstring(raw_html)
            elements = tree.xpath(rule.selector)
            values = []
            for el in elements:
                if isinstance(el, (html.HtmlElement, etree._Element)):
                    if rule.attribute:
                        val = el.get(rule.attribute, "")
                    else:
                        val = " ".join(el.itertext()).strip()
                else:
                    val = str(el)
                values.append(val.strip())
            return self._apply_transforms(values, rule)
        except Exception as e:
            return []

    def _extract_regex(self, raw_html: str, rule: ExtractionRule) -> List[str]:
        """Extract using regex patterns."""
        matches = re.findall(rule.selector, raw_html, re.DOTALL)
        values = []
        for match in matches:
            if isinstance(match, tuple):
                match = " ".join(str(m) for m in match if m)
            values.append(str(match).strip())
        return self._apply_transforms(values, rule)

    def _extract_json(self, raw_html: str, rule: ExtractionRule) -> List[str]:
        """Extract from embedded JSON (e.g., script tags)."""
        values = []
        json_matches = re.findall(r'<script[^>]*type\s*=\s*["\']application/json["\'][^>]*>(.*?)</script>',
                                   raw_html, re.DOTALL)
        if not json_matches:
            json_matches = re.findall(r'<script[^>]*>(.*?)</script>', raw_html, re.DOTALL)

        for json_str in json_matches:
            try:
                data = json.loads(json_str)
                value = self._resolve_json_path(data, rule.selector)
                if value is not None:
                    if isinstance(value, list):
                        values.extend(str(v) for v in value)
                    else:
                        values.append(str(value))
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
                continue

        return self._apply_transforms(values, rule)

    def _resolve_json_path(self, data: Any, path: str) -> Any:
        """Resolve a simple JSON path like 'key.nested.array[0]'"""
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]
        current = data
        for part in parts:
            if not part:
                continue
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current

    def _extract_tables(self, soup: BeautifulSoup, rule: ExtractionRule) -> List[str]:
        """Extract table data."""
        tables = soup.select(rule.selector if rule.selector else "table")
        values = []
        for table in tables:
            rows = []
            for tr in table.select("tr"):
                cells = [td.get_text(strip=True) for td in tr.select("th, td")]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                values.append("\n".join(rows))
        return self._apply_transforms(values, rule)

    def _extract_links(self, soup: BeautifulSoup, base_url: str, rule: ExtractionRule) -> List[str]:
        """Extract all links from the page."""
        from urllib.parse import urljoin
        anchors = soup.select(rule.selector if rule.selector else "a")
        values = []
        for a in anchors:
            href = a.get("href", "")
            if href:
                if rule.attribute == "text":
                    values.append(a.get_text(strip=True))
                else:
                    full_url = urljoin(base_url, href)
                    values.append(full_url)
        return self._apply_transforms(values, rule)

    def _extract_images(self, soup: BeautifulSoup, base_url: str, rule: ExtractionRule) -> List[str]:
        """Extract all images from the page."""
        from urllib.parse import urljoin
        imgs = soup.select(rule.selector if rule.selector else "img")
        values = []
        for img in imgs:
            src = img.get("src", "") or img.get("data-src", "")
            if src:
                full_url = urljoin(base_url, src)
                if rule.attribute == "alt":
                    values.append(img.get("alt", ""))
                else:
                    values.append(full_url)
        return self._apply_transforms(values, rule)

    def _extract_text(self, soup: BeautifulSoup, rule: ExtractionRule) -> List[str]:
        """Extract full text content."""
        if rule.selector:
            elements = soup.select(rule.selector)
            text = "\n".join(el.get_text(strip=True) for el in elements)
        else:
            # Remove script and style elements
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        return self._apply_transforms([text], rule)

    def _extract_attr(self, soup: BeautifulSoup, rule: ExtractionRule) -> List[str]:
        """Extract specific HTML attributes."""
        elements = soup.select(rule.selector)
        attr = rule.attribute or "href"
        values = []
        for el in elements:
            val = el.get(attr, "")
            if val:
                values.append(str(val))
        return self._apply_transforms(values, rule)

    def _extract_meta(self, soup: BeautifulSoup, rule: ExtractionRule) -> List[str]:
        """Extract meta tag content."""
        values = []
        if rule.selector:
            metas = soup.select(f"meta[{rule.selector}]")
            for meta in metas:
                content = meta.get("content", "")
                if content:
                    values.append(content)
        else:
            for meta in soup.select("meta"):
                name = meta.get("name", "") or meta.get("property", "")
                content = meta.get("content", "")
                if name and content:
                    values.append(f"{name}: {content}")
        return self._apply_transforms(values, rule)

    def auto_detect_fields(self, html_content: str) -> List[Dict]:
        """
        Auto-detect common extractable fields from a page.
        Returns suggested extraction rules.
        """
        suggestions = []
        soup = BeautifulSoup(html_content, "lxml")

        # Title
        title = soup.find("title")
        if title and title.get_text(strip=True):
            suggestions.append({
                "name": "title",
                "method": "css_selector",
                "selector": "title",
                "sample": title.get_text(strip=True)[:100],
            })

        # Meta description
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            suggestions.append({
                "name": "description",
                "method": "meta",
                "selector": "name=description",
                "sample": desc["content"][:100],
            })

        # H1
        h1 = soup.find("h1")
        if h1:
            suggestions.append({
                "name": "heading",
                "method": "css_selector",
                "selector": "h1",
                "sample": h1.get_text(strip=True)[:100],
            })

        # Main content
        main = soup.find("main") or soup.find("article") or soup.find(
            "div", class_=re.compile(r"content|main|article", re.I))
        if main:
            suggestions.append({
                "name": "content",
                "method": "css_selector",
                "selector": "main, article",
                "sample": main.get_text(strip=True)[:100] + "...",
            })

        # Links count
        links = soup.find_all("a", href=True)
        if links:
            suggestions.append({
                "name": "links",
                "method": "links",
                "selector": "a",
                "sample": f"{len(links)} links found",
            })

        # Images count
        imgs = soup.find_all("img", src=True)
        if imgs:
            suggestions.append({
                "name": "images",
                "method": "images",
                "selector": "img",
                "sample": f"{len(imgs)} images found",
            })

        # Tables
        tables = soup.find_all("table")
        if tables:
            suggestions.append({
                "name": "tables",
                "method": "table",
                "selector": "table",
                "sample": f"{len(tables)} tables found",
            })

        return suggestions

    def extract_page_metadata(self, html_content: str) -> Dict[str, str]:
        """Extract common page metadata."""
        soup = BeautifulSoup(html_content, "lxml")
        metadata = {}

        title = soup.find("title")
        if title:
            metadata["title"] = title.get_text(strip=True)

        for meta in soup.find_all("meta"):
            name = meta.get("name", "") or meta.get("property", "")
            content = meta.get("content", "")
            if name and content:
                metadata[name] = content

        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            metadata["canonical_url"] = canonical["href"]

        return metadata
