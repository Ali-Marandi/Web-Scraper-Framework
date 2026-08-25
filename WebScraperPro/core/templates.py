"""
WebScraper Pro - Pre-built Scraping Templates
Ready-to-use configurations for common scraping scenarios.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class ScrapeTemplate:
    """A pre-built scraping configuration template."""
    name: str
    description: str
    urls: List[str]
    mode: str  # static, dynamic, auto
    extraction_rules: List[Dict]
    page_actions: List[Dict] = field(default_factory=list)
    options: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "urls": self.urls,
            "mode": self.mode,
            "extraction_rules": self.extraction_rules,
            "page_actions": self.page_actions,
            "options": self.options,
        }


TEMPLATES: List[ScrapeTemplate] = [
    ScrapeTemplate(
        name="Page Title & Meta",
        description="Extract page title, meta description, and all meta tags from any URL.",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "title", "method": "css_selector", "selector": "title", "attribute": None, "default": None, "is_list": False},
            {"name": "description", "method": "meta", "selector": "name=description", "attribute": None, "default": None, "is_list": False},
            {"name": "all_meta", "method": "meta", "selector": "", "attribute": None, "default": None, "is_list": True},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="All Links",
        description="Extract all hyperlinks from a page with their anchor text.",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "links", "method": "links", "selector": "a", "attribute": None, "default": None, "is_list": True},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="All Images",
        description="Extract all image URLs and alt text from a page.",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "images", "method": "images", "selector": "img", "attribute": None, "default": None, "is_list": True},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="Full Text Content",
        description="Extract all visible text content from a page (scripts and styles removed).",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "content", "method": "full_text", "selector": "", "attribute": None, "default": None, "is_list": False},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="HTML Tables",
        description="Extract data from all HTML tables on a page.",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "tables", "method": "table", "selector": "table", "attribute": None, "default": None, "is_list": True},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="Article Scraper",
        description="Extract article title, author, date, and body text from news/blog pages.",
        urls=["https://example.com/article"],
        mode="static",
        extraction_rules=[
            {"name": "title", "method": "css_selector", "selector": "h1", "attribute": None, "default": None, "is_list": False},
            {"name": "author", "method": "css_selector", "selector": "[rel='author'], .author, .byline", "attribute": None, "default": None, "is_list": False},
            {"name": "date", "method": "css_selector", "selector": "time, [datetime], .date, .published", "attribute": "datetime", "default": None, "is_list": False},
            {"name": "content", "method": "css_selector", "selector": "article, .article, .post-content, main", "attribute": None, "default": None, "is_list": False},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="Product Page",
        description="Extract product name, price, description, and image from e-commerce pages.",
        urls=["https://example.com/product"],
        mode="dynamic",
        extraction_rules=[
            {"name": "name", "method": "css_selector", "selector": "h1, .product-title, [data-product-name]", "attribute": None, "default": None, "is_list": False},
            {"name": "price", "method": "css_selector", "selector": ".price, [data-price], .product-price", "attribute": None, "default": None, "is_list": False},
            {"name": "description", "method": "css_selector", "selector": ".description, .product-description, #description", "attribute": None, "default": None, "is_list": False},
            {"name": "image", "method": "css_selector", "selector": ".product-image img, [data-product-image], .main-image img", "attribute": "src", "default": None, "is_list": False},
        ],
        page_actions=[
            {"action_type": "scroll", "selector": "", "value": "", "delay": 1.0},
        ],
        options={"auto_scroll": True, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="Contact Info",
        description="Extract email addresses, phone numbers, and social media links from a page.",
        urls=["https://example.com/contact"],
        mode="static",
        extraction_rules=[
            {"name": "emails", "method": "regex", "selector": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "attribute": None, "default": None, "is_list": True},
            {"name": "phones", "method": "regex", "selector": r"\+?[0-9][\d\-\s]{8,}", "attribute": None, "default": None, "is_list": True},
            {"name": "social_links", "method": "links", "selector": "a[href*='facebook'], a[href*='twitter'], a[href*='linkedin'], a[href*='instagram']", "attribute": None, "default": None, "is_list": True},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="SEO Analysis",
        description="Extract all SEO-relevant meta tags, headings structure, and link counts.",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "title", "method": "css_selector", "selector": "title", "attribute": None, "default": None, "is_list": False},
            {"name": "meta_description", "method": "meta", "selector": "name=description", "attribute": None, "default": None, "is_list": False},
            {"name": "meta_keywords", "method": "meta", "selector": "name=keywords", "attribute": None, "default": None, "is_list": False},
            {"name": "canonical", "method": "html_attr", "selector": "link[rel='canonical']", "attribute": "href", "default": None, "is_list": False},
            {"name": "headings", "method": "css_selector", "selector": "h1, h2, h3, h4, h5, h6", "attribute": None, "default": None, "is_list": True},
            {"name": "all_links", "method": "links", "selector": "a", "attribute": None, "default": None, "is_list": True},
            {"name": "all_images", "method": "images", "selector": "img", "attribute": None, "default": None, "is_list": True},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="API/JSON Extractor",
        description="Extract and parse JSON data embedded in script tags (useful for SPAs).",
        urls=["https://example.com"],
        mode="dynamic",
        extraction_rules=[
            {"name": "json_data", "method": "json_path", "selector": "data", "attribute": None, "default": None, "is_list": True},
        ],
        page_actions=[
            {"action_type": "wait", "selector": "", "value": "2", "delay": 2.0},
        ],
        options={"auto_scroll": False, "follow_links": False, "max_pages": 1},
    ),
    ScrapeTemplate(
        name="Directory Crawler",
        description="Crawl a website following internal links up to N pages.",
        urls=["https://example.com"],
        mode="static",
        extraction_rules=[
            {"name": "title", "method": "css_selector", "selector": "title", "attribute": None, "default": None, "is_list": False},
            {"name": "description", "method": "meta", "selector": "name=description", "attribute": None, "default": None, "is_list": False},
            {"name": "headings", "method": "css_selector", "selector": "h1, h2", "attribute": None, "default": None, "is_list": True},
            {"name": "content", "method": "full_text", "selector": "main, article", "attribute": None, "default": None, "is_list": False},
        ],
        options={"auto_scroll": False, "follow_links": True, "max_pages": 50},
    ),
]


def get_template_names() -> List[str]:
    return [t.name for t in TEMPLATES]


def get_template_by_name(name: str) -> ScrapeTemplate:
    for t in TEMPLATES:
        if t.name == name:
            return t
    return None
