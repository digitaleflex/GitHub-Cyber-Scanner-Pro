# RPA Data Extraction Module

Comprehensive data extraction patterns for web scraping, parsing, and structured data collection. This module covers table extraction, pagination, infinite scroll, JSON/XML parsing, and export formats.

## Extraction Strategies

### Strategy Selection Guide

| Scenario | Best Approach |
|----------|---------------|
| Static HTML | BeautifulSoup + requests |
| JavaScript-rendered | Playwright |
| Hidden API available | curl + jq (fastest) |
| Infinite scroll | Playwright with scroll automation |
| Paginated data | Playwright or API pagination |
| Complex selectors | Playwright locators |
| High volume | Async Playwright + parallel |

---

## HTML Parsing with BeautifulSoup

### Basic Extraction

```python
#!/usr/bin/env python3
"""HTML parsing with BeautifulSoup - run with: uv run script.py"""

from bs4 import BeautifulSoup
import httpx
from typing import Optional
from pydantic import BaseModel


class Article(BaseModel):
    """Article data model."""
    title: str
    url: str
    author: Optional[str] = None
    date: Optional[str] = None
    summary: Optional[str] = None


def fetch_html(url: str) -> str:
    """Fetch HTML content."""
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_articles(html: str) -> list[Article]:
    """Parse articles from HTML."""
    soup = BeautifulSoup(html, "lxml")
    articles = []
    
    for article_elem in soup.select("article.post"):
        title_elem = article_elem.select_one("h2.title a")
        author_elem = article_elem.select_one(".author")
        date_elem = article_elem.select_one(".date")
        summary_elem = article_elem.select_one(".summary")
        
        if title_elem:
            article = Article(
                title=title_elem.get_text(strip=True),
                url=title_elem.get("href", ""),
                author=author_elem.get_text(strip=True) if author_elem else None,
                date=date_elem.get_text(strip=True) if date_elem else None,
                summary=summary_elem.get_text(strip=True) if summary_elem else None,
            )
            articles.append(article)
    
    return articles


def extract_all_links(html: str, base_url: str = "") -> list[dict]:
    """Extract all links from page."""
    from urllib.parse import urljoin
    
    soup = BeautifulSoup(html, "lxml")
    links = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href) if base_url else href
        
        links.append({
            "text": a.get_text(strip=True),
            "url": full_url,
            "title": a.get("title", ""),
        })
    
    return links


def extract_meta_tags(html: str) -> dict:
    """Extract meta tags from page."""
    soup = BeautifulSoup(html, "lxml")
    meta = {}
    
    # Title
    title = soup.find("title")
    meta["title"] = title.get_text(strip=True) if title else None
    
    # Meta tags
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        content = tag.get("content")
        if name and content:
            meta[name] = content
    
    return meta


if __name__ == "__main__":
    html = fetch_html("https://quotes.toscrape.com")
    
    soup = BeautifulSoup(html, "lxml")
    quotes = []
    
    for quote_elem in soup.select(".quote"):
        text = quote_elem.select_one(".text").get_text(strip=True)
        author = quote_elem.select_one(".author").get_text(strip=True)
        tags = [tag.get_text() for tag in quote_elem.select(".tag")]
        
        quotes.append({
            "text": text,
            "author": author,
            "tags": tags
        })
    
    for q in quotes[:3]:
        print(f"{q['author']}: {q['text'][:50]}...")
```

### Advanced CSS Selectors

```python
#!/usr/bin/env python3
"""Advanced BeautifulSoup selectors - run with: uv run script.py"""

from bs4 import BeautifulSoup


def demonstrate_selectors(html: str):
    """Demonstrate various CSS selector patterns."""
    soup = BeautifulSoup(html, "lxml")
    
    # By ID
    element = soup.select_one("#main-content")
    
    # By class
    elements = soup.select(".article-card")
    
    # Multiple classes
    elements = soup.select(".card.featured")
    
    # Descendant
    elements = soup.select("div.container article.post")
    
    # Direct child
    elements = soup.select("ul.menu > li")
    
    # Attribute selectors
    elements = soup.select("[data-id]")  # Has attribute
    elements = soup.select("[data-type='featured']")  # Exact match
    elements = soup.select("[href^='https']")  # Starts with
    elements = soup.select("[href$='.pdf']")  # Ends with
    elements = soup.select("[class*='btn']")  # Contains
    
    # Pseudo-selectors
    elements = soup.select("li:first-child")
    elements = soup.select("li:last-child")
    elements = soup.select("li:nth-child(2)")
    elements = soup.select("li:nth-child(odd)")
    elements = soup.select("p:not(.intro)")
    
    # Combining selectors
    elements = soup.select("article h2, article h3")  # OR
    elements = soup.select("div.content > p:first-child")  # Chained
    
    # Adjacent sibling
    elements = soup.select("h2 + p")  # p immediately after h2
    
    # General sibling
    elements = soup.select("h2 ~ p")  # All p siblings after h2
    
    return elements


def extract_structured_data(html: str) -> dict:
    """Extract JSON-LD structured data."""
    import json
    
    soup = BeautifulSoup(html, "lxml")
    structured_data = []
    
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except json.JSONDecodeError:
            pass
    
    return structured_data
```

---

## Playwright-Based Extraction

### Dynamic Content Extraction

```python
#!/usr/bin/env python3
"""Playwright data extraction - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page, Locator
from typing import Any
import json


class PlaywrightExtractor:
    """Extract data from JavaScript-rendered pages."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def extract_text(self, selector: str) -> str:
        """Extract text content."""
        return self.page.locator(selector).text_content() or ""
    
    def extract_texts(self, selector: str) -> list[str]:
        """Extract text from multiple elements."""
        return self.page.locator(selector).all_text_contents()
    
    def extract_attribute(self, selector: str, attribute: str) -> str:
        """Extract element attribute."""
        return self.page.locator(selector).get_attribute(attribute) or ""
    
    def extract_attributes(self, selector: str, attribute: str) -> list[str]:
        """Extract attribute from multiple elements."""
        elements = self.page.locator(selector).all()
        return [el.get_attribute(attribute) or "" for el in elements]
    
    def extract_html(self, selector: str) -> str:
        """Extract inner HTML."""
        return self.page.locator(selector).inner_html()
    
    def extract_value(self, selector: str) -> str:
        """Extract input value."""
        return self.page.locator(selector).input_value()
    
    def count_elements(self, selector: str) -> int:
        """Count matching elements."""
        return self.page.locator(selector).count()
    
    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return self.page.locator(selector).is_visible()
    
    def extract_table(self, table_selector: str) -> list[dict]:
        """Extract table as list of dicts."""
        table = self.page.locator(table_selector)
        
        # Get headers
        headers = table.locator("thead th").all_text_contents()
        if not headers:
            headers = table.locator("tr:first-child th, tr:first-child td").all_text_contents()
        
        # Get rows
        rows = table.locator("tbody tr").all()
        data = []
        
        for row in rows:
            cells = row.locator("td").all_text_contents()
            if len(cells) == len(headers):
                data.append(dict(zip(headers, cells)))
        
        return data
    
    def extract_list_items(self, list_selector: str) -> list[str]:
        """Extract list items."""
        return self.page.locator(f"{list_selector} li").all_text_contents()
    
    def extract_form_data(self, form_selector: str) -> dict:
        """Extract current form values."""
        form = self.page.locator(form_selector)
        data = {}
        
        # Text inputs
        for input_el in form.locator("input[type=text], input[type=email], input[type=tel]").all():
            name = input_el.get_attribute("name")
            if name:
                data[name] = input_el.input_value()
        
        # Textareas
        for textarea in form.locator("textarea").all():
            name = textarea.get_attribute("name")
            if name:
                data[name] = textarea.input_value()
        
        # Selects
        for select in form.locator("select").all():
            name = select.get_attribute("name")
            if name:
                data[name] = select.input_value()
        
        # Checkboxes
        for checkbox in form.locator("input[type=checkbox]").all():
            name = checkbox.get_attribute("name")
            if name:
                data[name] = checkbox.is_checked()
        
        return data
    
    def extract_json_from_script(self, variable_name: str) -> Any:
        """Extract JavaScript variable value."""
        return self.page.evaluate(f"() => {variable_name}")
    
    def extract_computed_style(self, selector: str, property: str) -> str:
        """Extract computed CSS property."""
        return self.page.evaluate(f"""
            () => getComputedStyle(document.querySelector('{selector}')).{property}
        """)


def extract_dynamic_content():
    """Extract from JavaScript-rendered page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://quotes.toscrape.com/js/")
        
        # Wait for JavaScript to render
        page.wait_for_selector(".quote")
        
        extractor = PlaywrightExtractor(page)
        
        quotes = []
        quote_elements = page.locator(".quote").all()
        
        for quote_el in quote_elements:
            quotes.append({
                "text": quote_el.locator(".text").text_content(),
                "author": quote_el.locator(".author").text_content(),
                "tags": quote_el.locator(".tag").all_text_contents(),
            })
        
        print(json.dumps(quotes[:2], indent=2))
        browser.close()


if __name__ == "__main__":
    extract_dynamic_content()
```

---

## Table Extraction

### Complex Table Handling

```python
#!/usr/bin/env python3
"""Advanced table extraction - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
import pandas as pd
from typing import Optional
import json


class TableExtractor:
    """Extract data from HTML tables."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def simple_table(self, selector: str) -> pd.DataFrame:
        """Extract simple table to DataFrame."""
        headers = self.page.locator(f"{selector} thead th").all_text_contents()
        
        rows = []
        for row in self.page.locator(f"{selector} tbody tr").all():
            cells = row.locator("td").all_text_contents()
            rows.append(cells)
        
        return pd.DataFrame(rows, columns=headers if headers else None)
    
    def table_with_rowspan(self, selector: str) -> pd.DataFrame:
        """Handle tables with rowspan/colspan."""
        # Use JavaScript to properly parse complex tables
        data = self.page.evaluate(f"""
            () => {{
                const table = document.querySelector('{selector}');
                const rows = [];
                const spanTracker = {{}};
                
                for (const tr of table.querySelectorAll('tr')) {{
                    const row = [];
                    let colIndex = 0;
                    
                    for (const cell of tr.querySelectorAll('th, td')) {{
                        // Skip columns with active rowspan
                        while (spanTracker[colIndex] && spanTracker[colIndex].remaining > 0) {{
                            row.push(spanTracker[colIndex].value);
                            spanTracker[colIndex].remaining--;
                            colIndex++;
                        }}
                        
                        const colspan = parseInt(cell.getAttribute('colspan') || '1');
                        const rowspan = parseInt(cell.getAttribute('rowspan') || '1');
                        const value = cell.textContent.trim();
                        
                        // Add value for each colspan
                        for (let i = 0; i < colspan; i++) {{
                            row.push(value);
                            
                            if (rowspan > 1) {{
                                spanTracker[colIndex] = {{
                                    value: value,
                                    remaining: rowspan - 1
                                }};
                            }}
                            colIndex++;
                        }}
                    }}
                    
                    // Fill remaining spanned columns
                    while (spanTracker[colIndex] && spanTracker[colIndex].remaining > 0) {{
                        row.push(spanTracker[colIndex].value);
                        spanTracker[colIndex].remaining--;
                        colIndex++;
                    }}
                    
                    rows.push(row);
                }}
                
                return rows;
            }}
        """)
        
        if data and len(data) > 0:
            return pd.DataFrame(data[1:], columns=data[0])
        return pd.DataFrame()
    
    def nested_table(self, outer_selector: str, inner_selector: str) -> list[pd.DataFrame]:
        """Extract nested tables."""
        tables = []
        
        for outer_row in self.page.locator(f"{outer_selector} > tbody > tr").all():
            inner_table = outer_row.locator(inner_selector)
            if inner_table.count() > 0:
                headers = inner_table.locator("thead th").all_text_contents()
                rows = []
                for row in inner_table.locator("tbody tr").all():
                    cells = row.locator("td").all_text_contents()
                    rows.append(cells)
                tables.append(pd.DataFrame(rows, columns=headers if headers else None))
        
        return tables
    
    def table_with_links(self, selector: str) -> pd.DataFrame:
        """Extract table preserving link URLs."""
        rows = []
        
        for tr in self.page.locator(f"{selector} tbody tr").all():
            row_data = {}
            cells = tr.locator("td").all()
            headers = self.page.locator(f"{selector} thead th").all_text_contents()
            
            for i, cell in enumerate(cells):
                col_name = headers[i] if i < len(headers) else f"col_{i}"
                
                # Check for link
                link = cell.locator("a")
                if link.count() > 0:
                    row_data[col_name] = cell.text_content().strip()
                    row_data[f"{col_name}_url"] = link.get_attribute("href")
                else:
                    row_data[col_name] = cell.text_content().strip()
            
            rows.append(row_data)
        
        return pd.DataFrame(rows)
    
    def sortable_table(self, selector: str, sort_column: str, ascending: bool = True) -> pd.DataFrame:
        """Sort table by clicking header before extraction."""
        header_selector = f"{selector} thead th:has-text('{sort_column}')"
        
        self.page.click(header_selector)
        self.page.wait_for_timeout(500)
        
        if not ascending:
            self.page.click(header_selector)
            self.page.wait_for_timeout(500)
        
        return self.simple_table(selector)


def extract_tables():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://www.w3schools.com/html/html_tables.asp")
        
        extractor = TableExtractor(page)
        df = extractor.simple_table("#customers")
        
        print(df.to_string())
        df.to_csv("table_data.csv", index=False)
        
        browser.close()


if __name__ == "__main__":
    extract_tables()
```

---

## Pagination Handling

### Click-Based Pagination

```python
#!/usr/bin/env python3
"""Pagination handling - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Generator, Any
import json


class PaginatedExtractor:
    """Extract data from paginated pages."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def extract_page_data(self, item_selector: str, extract_func) -> list[Any]:
        """Extract data from current page."""
        items = self.page.locator(item_selector).all()
        return [extract_func(item) for item in items]
    
    def click_pagination(
        self,
        item_selector: str,
        next_button: str,
        extract_func,
        max_pages: int = None
    ) -> Generator[list[Any], None, None]:
        """Iterate through click-based pagination."""
        page_num = 0
        
        while True:
            page_num += 1
            
            # Extract current page
            data = self.extract_page_data(item_selector, extract_func)
            yield data
            
            # Check page limit
            if max_pages and page_num >= max_pages:
                break
            
            # Check for next button
            next_btn = self.page.locator(next_button)
            if not next_btn.is_visible() or next_btn.is_disabled():
                break
            
            # Click next
            next_btn.click()
            self.page.wait_for_load_state("networkidle")
    
    def url_pagination(
        self,
        base_url: str,
        item_selector: str,
        extract_func,
        start_page: int = 1,
        max_pages: int = None,
        page_param: str = "page"
    ) -> Generator[list[Any], None, None]:
        """Iterate through URL-based pagination."""
        page_num = start_page
        
        while True:
            url = f"{base_url}?{page_param}={page_num}"
            self.page.goto(url, wait_until="networkidle")
            
            # Check if items exist
            if self.page.locator(item_selector).count() == 0:
                break
            
            data = self.extract_page_data(item_selector, extract_func)
            yield data
            
            page_num += 1
            
            if max_pages and (page_num - start_page) >= max_pages:
                break
    
    def numbered_pagination(
        self,
        item_selector: str,
        page_links_selector: str,
        extract_func,
        max_pages: int = None
    ) -> Generator[list[Any], None, None]:
        """Click through numbered page links."""
        visited_pages = set()
        
        while True:
            # Get current page number
            current_url = self.page.url
            if current_url in visited_pages:
                break
            visited_pages.add(current_url)
            
            # Extract current page
            data = self.extract_page_data(item_selector, extract_func)
            yield data
            
            if max_pages and len(visited_pages) >= max_pages:
                break
            
            # Find next unvisited page link
            page_links = self.page.locator(page_links_selector).all()
            found_next = False
            
            for link in page_links:
                href = link.get_attribute("href")
                if href and href not in visited_pages:
                    link.click()
                    self.page.wait_for_load_state("networkidle")
                    found_next = True
                    break
            
            if not found_next:
                break


def extract_with_pagination():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://quotes.toscrape.com")
        
        extractor = PaginatedExtractor(page)
        
        def extract_quote(element):
            return {
                "text": element.locator(".text").text_content(),
                "author": element.locator(".author").text_content(),
            }
        
        all_quotes = []
        for page_data in extractor.click_pagination(
            item_selector=".quote",
            next_button=".next > a",
            extract_func=extract_quote,
            max_pages=3
        ):
            all_quotes.extend(page_data)
            print(f"Collected {len(all_quotes)} quotes")
        
        print(f"Total: {len(all_quotes)} quotes")
        browser.close()


if __name__ == "__main__":
    extract_with_pagination()
```

---

## Infinite Scroll

### Scroll-Based Loading

```python
#!/usr/bin/env python3
"""Infinite scroll handling - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Callable, Any
import time


class InfiniteScrollExtractor:
    """Handle infinite scroll pages."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def scroll_and_extract(
        self,
        item_selector: str,
        extract_func: Callable,
        max_items: int = None,
        max_scrolls: int = 50,
        scroll_delay: float = 1.0,
        no_new_items_threshold: int = 3
    ) -> list[Any]:
        """Scroll and extract items until limit or end."""
        extracted_items = []
        seen_count = 0
        no_new_items_count = 0
        
        for scroll_num in range(max_scrolls):
            # Get current items
            items = self.page.locator(item_selector).all()
            current_count = len(items)
            
            # Extract new items
            for item in items[seen_count:]:
                try:
                    data = extract_func(item)
                    extracted_items.append(data)
                    
                    if max_items and len(extracted_items) >= max_items:
                        return extracted_items
                except Exception as e:
                    print(f"Extraction error: {e}")
            
            # Check for new items
            if current_count == seen_count:
                no_new_items_count += 1
                if no_new_items_count >= no_new_items_threshold:
                    print("No new items, stopping")
                    break
            else:
                no_new_items_count = 0
            
            seen_count = current_count
            
            # Scroll down
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(scroll_delay)
            
            # Wait for new content
            self.page.wait_for_load_state("networkidle", timeout=5000)
        
        return extracted_items
    
    def scroll_to_element(self, selector: str) -> bool:
        """Scroll until element is visible."""
        max_scrolls = 20
        
        for _ in range(max_scrolls):
            if self.page.locator(selector).is_visible():
                return True
            
            self.page.evaluate("window.scrollBy(0, window.innerHeight)")
            time.sleep(0.5)
        
        return False
    
    def scroll_within_container(
        self,
        container_selector: str,
        item_selector: str,
        extract_func: Callable,
        max_items: int = None
    ) -> list[Any]:
        """Scroll within a scrollable container."""
        extracted_items = []
        seen_count = 0
        
        container = self.page.locator(container_selector)
        
        for _ in range(50):
            items = container.locator(item_selector).all()
            current_count = len(items)
            
            for item in items[seen_count:]:
                try:
                    data = extract_func(item)
                    extracted_items.append(data)
                    
                    if max_items and len(extracted_items) >= max_items:
                        return extracted_items
                except Exception:
                    pass
            
            if current_count == seen_count:
                break
            
            seen_count = current_count
            
            # Scroll container
            self.page.evaluate(f"""
                const container = document.querySelector('{container_selector}');
                container.scrollTop = container.scrollHeight;
            """)
            time.sleep(0.5)
        
        return extracted_items
    
    def lazy_load_images(self):
        """Trigger lazy-loaded images."""
        # Scroll through page to trigger lazy loading
        viewport_height = self.page.viewport_size["height"]
        page_height = self.page.evaluate("document.body.scrollHeight")
        
        current_position = 0
        while current_position < page_height:
            self.page.evaluate(f"window.scrollTo(0, {current_position})")
            time.sleep(0.3)
            current_position += viewport_height // 2
        
        # Scroll back to top
        self.page.evaluate("window.scrollTo(0, 0)")


def extract_infinite_scroll():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Example: Reddit-style infinite scroll
        page.goto("https://scrapingclub.com/exercise/list_infinite_scroll/")
        
        extractor = InfiniteScrollExtractor(page)
        
        def extract_product(element):
            return {
                "name": element.locator(".post-title").text_content(),
                "price": element.locator(".post-price").text_content(),
            }
        
        products = extractor.scroll_and_extract(
            item_selector=".post",
            extract_func=extract_product,
            max_items=30,
            scroll_delay=0.5
        )
        
        print(f"Extracted {len(products)} products")
        browser.close()


if __name__ == "__main__":
    extract_infinite_scroll()
```

---

## API Discovery and Extraction

### Network Request Capture

```python
#!/usr/bin/env python3
"""API discovery via network capture - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page, Response
import json
from typing import Callable
from urllib.parse import urlparse


class APIDiscovery:
    """Discover and extract from hidden APIs."""
    
    def __init__(self, page: Page):
        self.page = page
        self.captured_requests = []
        self.captured_responses = []
    
    def capture_responses(self, url_pattern: str = "**/*"):
        """Set up response capture."""
        def handle_response(response: Response):
            if "application/json" in response.headers.get("content-type", ""):
                try:
                    self.captured_responses.append({
                        "url": response.url,
                        "status": response.status,
                        "data": response.json()
                    })
                except Exception:
                    pass
        
        self.page.on("response", handle_response)
    
    def get_api_endpoints(self) -> list[dict]:
        """Get discovered API endpoints."""
        endpoints = []
        
        for resp in self.captured_responses:
            parsed = urlparse(resp["url"])
            endpoints.append({
                "path": parsed.path,
                "query": parsed.query,
                "full_url": resp["url"],
                "method": "GET",  # From response only
                "status": resp["status"],
            })
        
        return endpoints
    
    def extract_from_api(self, url: str, headers: dict = None) -> dict:
        """Direct API call using captured session."""
        response = self.page.request.get(url, headers=headers)
        return response.json()
    
    def generate_curl(self, endpoint: dict, cookies: bool = True) -> str:
        """Generate curl command for endpoint."""
        cmd = f"curl -s '{endpoint['full_url']}'"
        
        if cookies:
            page_cookies = self.page.context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in page_cookies])
            cmd += f" \\\n  -H 'Cookie: {cookie_str}'"
        
        cmd += " | jq"
        return cmd


def discover_apis():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        discovery = APIDiscovery(page)
        discovery.capture_responses()
        
        # Navigate and interact to trigger API calls
        page.goto("https://example.com")
        page.click("#load-data")  # Trigger API call
        page.wait_for_load_state("networkidle")
        
        # Analyze discovered endpoints
        endpoints = discovery.get_api_endpoints()
        
        for ep in endpoints:
            print(f"\nDiscovered API: {ep['path']}")
            print(discovery.generate_curl(ep))
        
        browser.close()


if __name__ == "__main__":
    discover_apis()
```

---

## Data Export

### Multiple Format Export

```python
#!/usr/bin/env python3
"""Data export utilities - run with: uv run script.py"""

import json
import csv
from pathlib import Path
from typing import Any
from datetime import datetime
import pandas as pd


class DataExporter:
    """Export extracted data to various formats."""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def _generate_filename(self, prefix: str, extension: str) -> Path:
        """Generate timestamped filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.output_dir / f"{prefix}_{timestamp}.{extension}"
    
    def to_json(self, data: Any, filename: str = None, pretty: bool = True) -> Path:
        """Export to JSON."""
        filepath = Path(filename) if filename else self._generate_filename("export", "json")
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2 if pretty else None, ensure_ascii=False, default=str)
        
        return filepath
    
    def to_jsonl(self, data: list[dict], filename: str = None) -> Path:
        """Export to JSON Lines (one JSON object per line)."""
        filepath = Path(filename) if filename else self._generate_filename("export", "jsonl")
        
        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
        
        return filepath
    
    def to_csv(self, data: list[dict], filename: str = None) -> Path:
        """Export to CSV."""
        filepath = Path(filename) if filename else self._generate_filename("export", "csv")
        
        if not data:
            return filepath
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        
        return filepath
    
    def to_excel(self, data: list[dict], filename: str = None, sheet_name: str = "Data") -> Path:
        """Export to Excel."""
        filepath = Path(filename) if filename else self._generate_filename("export", "xlsx")
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, sheet_name=sheet_name)
        
        return filepath
    
    def to_excel_multi_sheet(self, sheets: dict[str, list[dict]], filename: str = None) -> Path:
        """Export multiple datasets to Excel sheets."""
        filepath = Path(filename) if filename else self._generate_filename("export", "xlsx")
        
        with pd.ExcelWriter(filepath) as writer:
            for sheet_name, data in sheets.items():
                df = pd.DataFrame(data)
                df.to_excel(writer, index=False, sheet_name=sheet_name[:31])  # Excel limit
        
        return filepath
    
    def to_markdown_table(self, data: list[dict], filename: str = None) -> Path:
        """Export to Markdown table."""
        filepath = Path(filename) if filename else self._generate_filename("export", "md")
        
        if not data:
            return filepath
        
        df = pd.DataFrame(data)
        markdown = df.to_markdown(index=False)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return filepath
    
    def to_html_table(self, data: list[dict], filename: str = None, title: str = "Data Export") -> Path:
        """Export to HTML table."""
        filepath = Path(filename) if filename else self._generate_filename("export", "html")
        
        df = pd.DataFrame(data)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #ddd; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Generated: {datetime.now().isoformat()}</p>
    {df.to_html(index=False, classes='data-table')}
</body>
</html>
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        return filepath
    
    def append_to_csv(self, data: list[dict], filepath: str) -> Path:
        """Append data to existing CSV."""
        path = Path(filepath)
        file_exists = path.exists()
        
        df = pd.DataFrame(data)
        df.to_csv(path, mode="a", header=not file_exists, index=False)
        
        return path


def example_export():
    data = [
        {"name": "Product A", "price": 29.99, "stock": 100},
        {"name": "Product B", "price": 49.99, "stock": 50},
        {"name": "Product C", "price": 19.99, "stock": 200},
    ]
    
    exporter = DataExporter("./exports")
    
    json_path = exporter.to_json(data)
    csv_path = exporter.to_csv(data)
    excel_path = exporter.to_excel(data)
    
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    print(f"Excel: {excel_path}")


if __name__ == "__main__":
    example_export()
```

---

## Best Practices

1. **Choose the right tool** - Use requests/curl for static, Playwright for dynamic
2. **Respect rate limits** - Add delays between requests
3. **Handle errors gracefully** - Empty elements, missing data
4. **Validate extracted data** - Use Pydantic models
5. **Export incrementally** - Don't wait until the end
6. **Use caching** - Cache API responses when possible
7. **Monitor memory** - Large extractions can use significant memory

---

**Next Module:** See **rpa-form-automation.md** for form filling patterns.
