---
description: Enterprise-grade Robotic Process Automation framework for web automation without APIs - a UiPath alternative using Playwright, Python, mitmproxy, and open-source RPA tools for browser automation, data extraction, form filling, workflow orchestration, scheduled task execution, desktop automation, document processing, and enterprise observability
name: rpa
---

# RPA: Enterprise Robotic Process Automation Framework

> **Open-Source UiPath Alternative**  
> Enterprise-grade web automation for sites without APIs using Playwright + Python + mitmproxy + open-source RPA frameworks.

## What I Do

I am an enterprise-grade RPA framework that automates web-based business processes without requiring APIs. Unlike commercial tools like UiPath or Automation Anywhere, I leverage powerful open-source technologies:

- **Browser Automation**: Playwright for reliable cross-browser automation with auto-waiting
- **Traffic Analysis**: mitmproxy for understanding hidden APIs and network requests
- **Data Extraction**: BeautifulSoup, lxml, and Playwright for structured data scraping
- **Workflow Orchestration**: Multi-step process automation with state management
- **Visual Automation**: OCR and image recognition for legacy systems
- **Scheduling**: Cron-based and event-driven task execution
- **Error Recovery**: Intelligent retry mechanisms and failure handling

## When to Use Me

Use this skill when you need to:

- Automate repetitive web-based tasks (data entry, form filling, report generation)
- Extract data from websites without APIs
- Automate legacy web applications
- Build unattended automation bots
- Create scheduled data collection workflows
- Automate multi-step business processes across multiple websites
- Handle file uploads/downloads automatically
- Automate authentication flows (login, MFA, SSO)

## Core Stack Components

### 1. Playwright - Browser Automation Engine

**Purpose**: Reliable cross-browser automation with modern web support

**Why Playwright over Selenium**:
- Auto-waiting for elements (no explicit waits needed)
- Native support for shadow DOM, iframes, and web components
- Built-in screenshot, video, and trace recording
- Network interception and mocking
- Multi-browser support (Chromium, Firefox, WebKit)
- Mobile emulation
- Persistent contexts for session reuse

**Installation**:
```bash
# Install with uv
uv add playwright

# Install browsers
uv run playwright install chromium
uv run playwright install firefox  # Optional
uv run playwright install webkit   # Optional
```

### 2. mitmproxy - Traffic Analysis

**Purpose**: Discover hidden APIs and understand network behavior

**Use Cases**:
- Capture API endpoints the website uses internally
- Understand request/response patterns
- Replay captured requests with curl
- Identify authentication mechanisms

**Installation**:
```bash
uv tool install mitmproxy
```

### 3. Python Libraries

**Core Libraries**:
```bash
# Browser automation
uv add playwright

# Data extraction
uv add beautifulsoup4 lxml html5lib

# HTTP requests
uv add httpx aiohttp requests

# Data processing
uv add pandas openpyxl xlrd

# OCR and vision
uv add pytesseract pillow opencv-python

# Scheduling
uv add schedule apscheduler

# Workflow orchestration
uv add prefect  # or temporalio

# Configuration
uv add pydantic python-dotenv

# Logging
uv add structlog loguru
```

### 4. Additional RPA Frameworks

**RPA Framework (Robot Framework)**:
```bash
uv add rpaframework rpaframework-browser
```

**Botcity**:
```bash
uv add botcity-framework-core botcity-framework-web
```

---

## Core Automation Patterns

### Pattern 1: Basic Page Automation

```python
#!/usr/bin/env python3
"""Basic page automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page, Browser
from typing import Optional
import structlog

log = structlog.get_logger()


class PageAutomator:
    """Base class for page automation."""
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.page = self.browser.new_page()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def navigate(self, url: str, wait_until: str = "networkidle"):
        """Navigate to URL and wait for page load."""
        log.info("navigating", url=url)
        self.page.goto(url, wait_until=wait_until)
    
    def click(self, selector: str, timeout: int = 30000):
        """Click element with auto-wait."""
        log.info("clicking", selector=selector)
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str):
        """Fill input field."""
        log.info("filling", selector=selector)
        self.page.fill(selector, value)
    
    def get_text(self, selector: str) -> str:
        """Get text content of element."""
        return self.page.text_content(selector)
    
    def screenshot(self, path: str):
        """Take screenshot."""
        self.page.screenshot(path=path, full_page=True)
    
    def wait_for_selector(self, selector: str, timeout: int = 30000):
        """Wait for element to appear."""
        self.page.wait_for_selector(selector, timeout=timeout)


# Usage
if __name__ == "__main__":
    with PageAutomator(headless=False, slow_mo=100) as bot:
        bot.navigate("https://example.com")
        bot.screenshot("example.png")
```

### Pattern 2: Async Automation for Performance

```python
#!/usr/bin/env python3
"""Async automation for parallel tasks - run with: uv run script.py"""

import asyncio
from playwright.async_api import async_playwright, Page
from typing import Any
import structlog

log = structlog.get_logger()


class AsyncPageAutomator:
    """Async page automation for parallel processing."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.playwright = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def new_page(self) -> Page:
        """Create new page context."""
        context = await self.browser.new_context()
        return await context.new_page()
    
    async def process_url(self, url: str) -> dict[str, Any]:
        """Process a single URL."""
        page = await self.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            title = await page.title()
            content = await page.content()
            return {"url": url, "title": title, "content_length": len(content)}
        finally:
            await page.close()
    
    async def process_urls_parallel(self, urls: list[str], max_concurrent: int = 5) -> list[dict]:
        """Process multiple URLs in parallel."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_process(url: str):
            async with semaphore:
                return await self.process_url(url)
        
        tasks = [limited_process(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://quotes.toscrape.com",
    ]
    
    async with AsyncPageAutomator(headless=True) as bot:
        results = await bot.process_urls_parallel(urls)
        for result in results:
            if isinstance(result, dict):
                log.info("processed", **result)


if __name__ == "__main__":
    asyncio.run(main())
```

### Pattern 3: Session Persistence

```python
#!/usr/bin/env python3
"""Session persistence for login state - run with: uv run script.py"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import json


class SessionManager:
    """Manage browser sessions with persistence."""
    
    def __init__(self, storage_dir: str = "./sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    def save_session(self, page, session_name: str):
        """Save browser session (cookies + storage)."""
        context = page.context
        
        # Save storage state (cookies + localStorage)
        storage_path = self.storage_dir / f"{session_name}_storage.json"
        context.storage_state(path=str(storage_path))
        
        print(f"Session saved: {storage_path}")
    
    def load_session(self, browser, session_name: str):
        """Load browser session."""
        storage_path = self.storage_dir / f"{session_name}_storage.json"
        
        if storage_path.exists():
            context = browser.new_context(storage_state=str(storage_path))
            print(f"Session loaded: {storage_path}")
            return context.new_page()
        else:
            print("No saved session found, creating new context")
            return browser.new_page()
    
    def clear_session(self, session_name: str):
        """Clear saved session."""
        storage_path = self.storage_dir / f"{session_name}_storage.json"
        if storage_path.exists():
            storage_path.unlink()


def login_and_save_session():
    """Login once and save session for reuse."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        session_mgr = SessionManager()
        
        # Navigate to login page
        page.goto("https://example.com/login")
        
        # Perform login
        page.fill("#username", "your_username")
        page.fill("#password", "your_password")
        page.click("button[type=submit]")
        
        # Wait for login to complete
        page.wait_for_url("**/dashboard**")
        
        # Save session
        session_mgr.save_session(page, "my_account")
        
        browser.close()


def use_saved_session():
    """Use previously saved session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        session_mgr = SessionManager()
        
        # Load session - no login needed!
        page = session_mgr.load_session(browser, "my_account")
        
        # Navigate directly to protected page
        page.goto("https://example.com/dashboard")
        
        # You're already logged in
        print(page.title())
        
        browser.close()
```

### Pattern 4: Network Request Interception

```python
#!/usr/bin/env python3
"""Network interception for API discovery - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Route, Request
import json


class NetworkInterceptor:
    """Intercept and analyze network requests."""
    
    def __init__(self):
        self.captured_requests = []
        self.captured_responses = []
    
    def capture_request(self, route: Route, request: Request):
        """Capture request details."""
        self.captured_requests.append({
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
        })
        route.continue_()
    
    def capture_api_calls(self, page, url_pattern: str = "**/api/**"):
        """Set up API call interception."""
        page.route(url_pattern, self.capture_request)
    
    def block_resources(self, page, resource_types: list[str] = None):
        """Block specified resource types for faster loading."""
        if resource_types is None:
            resource_types = ["image", "stylesheet", "font", "media"]
        
        def block_handler(route: Route, request: Request):
            if request.resource_type in resource_types:
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", block_handler)
    
    def mock_api_response(self, page, url_pattern: str, mock_data: dict):
        """Mock API response for testing."""
        def mock_handler(route: Route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(mock_data)
            )
        
        page.route(url_pattern, mock_handler)
    
    def export_as_curl(self, request_data: dict) -> str:
        """Convert captured request to curl command."""
        cmd = f"curl -X {request_data['method']} '{request_data['url']}'"
        
        for key, value in request_data.get("headers", {}).items():
            if key.lower() not in ["host", "content-length"]:
                cmd += f" \\\n  -H '{key}: {value}'"
        
        if request_data.get("post_data"):
            cmd += f" \\\n  -d '{request_data['post_data']}'"
        
        return cmd


def discover_hidden_apis():
    """Discover hidden API endpoints used by a website."""
    interceptor = NetworkInterceptor()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture all API calls
        interceptor.capture_api_calls(page, "**/api/**")
        interceptor.capture_api_calls(page, "**/graphql**")
        
        # Navigate and interact
        page.goto("https://example.com")
        page.click("#load-more")  # Trigger API calls
        
        # Wait for network to settle
        page.wait_for_load_state("networkidle")
        
        # Export discovered APIs
        print("Discovered API Endpoints:")
        for req in interceptor.captured_requests:
            print(f"\n{req['method']} {req['url']}")
            print(interceptor.export_as_curl(req))
        
        browser.close()
```

---

## Selector Strategies

### Priority Order (Most Reliable First)

1. **Test IDs** (most stable):
   ```python
   page.click("[data-testid='submit-button']")
   page.click("[data-cy='login-form']")
   ```

2. **Accessible Roles**:
   ```python
   page.get_by_role("button", name="Submit")
   page.get_by_role("textbox", name="Email")
   page.get_by_role("link", name="Learn more")
   ```

3. **Labels and Text**:
   ```python
   page.get_by_label("Email address")
   page.get_by_text("Sign in")
   page.get_by_placeholder("Enter your email")
   ```

4. **CSS Selectors** (stable if well-structured):
   ```python
   page.click("#login-button")
   page.click(".btn-primary")
   page.click("form.login button[type=submit]")
   ```

5. **XPath** (use sparingly):
   ```python
   page.click("//button[contains(text(), 'Submit')]")
   page.click("//div[@class='container']//input[@name='email']")
   ```

### Selector Chaining

```python
# Scope selectors to parent elements
form = page.locator("form.login-form")
form.locator("input[name=email]").fill("user@example.com")
form.locator("input[name=password]").fill("password123")
form.locator("button[type=submit]").click()
```

### Waiting Strategies

```python
# Auto-wait (built-in)
page.click("#button")  # Waits automatically

# Explicit wait for element
page.wait_for_selector("#dynamic-content", state="visible")

# Wait for specific conditions
page.wait_for_function("document.querySelector('#status').innerText === 'Ready'")

# Wait for network
page.wait_for_load_state("networkidle")
page.wait_for_response("**/api/data")

# Wait for navigation
page.wait_for_url("**/success**")
```

---

## Data Extraction Patterns

### Table Extraction

```python
#!/usr/bin/env python3
"""Extract table data - run with: uv run script.py"""

from playwright.sync_api import sync_playwright
import pandas as pd


def extract_table(page, table_selector: str) -> pd.DataFrame:
    """Extract HTML table to DataFrame."""
    
    # Get headers
    headers = page.locator(f"{table_selector} thead th").all_text_contents()
    
    # Get rows
    rows = page.locator(f"{table_selector} tbody tr").all()
    data = []
    
    for row in rows:
        cells = row.locator("td").all_text_contents()
        data.append(cells)
    
    return pd.DataFrame(data, columns=headers)


def extract_table_with_pagination(page, table_selector: str, next_button: str) -> pd.DataFrame:
    """Extract table data across multiple pages."""
    all_data = []
    
    while True:
        # Extract current page
        df = extract_table(page, table_selector)
        all_data.append(df)
        
        # Check for next page
        next_btn = page.locator(next_button)
        if next_btn.is_visible() and next_btn.is_enabled():
            next_btn.click()
            page.wait_for_load_state("networkidle")
        else:
            break
    
    return pd.concat(all_data, ignore_index=True)
```

### Structured Data Extraction

```python
#!/usr/bin/env python3
"""Extract structured data - run with: uv run script.py"""

from playwright.sync_api import sync_playwright
from pydantic import BaseModel
from typing import Optional
import json


class Product(BaseModel):
    """Product data model."""
    name: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None


def extract_products(page, container_selector: str) -> list[Product]:
    """Extract product data from page."""
    products = []
    
    items = page.locator(container_selector).all()
    
    for item in items:
        try:
            product = Product(
                name=item.locator(".product-name").text_content().strip(),
                price=float(item.locator(".price").text_content().replace("$", "").strip()),
                description=item.locator(".description").text_content().strip() 
                           if item.locator(".description").count() > 0 else None,
                image_url=item.locator("img").get_attribute("src"),
                rating=float(item.locator(".rating").get_attribute("data-rating"))
                       if item.locator(".rating").count() > 0 else None,
            )
            products.append(product)
        except Exception as e:
            print(f"Error extracting product: {e}")
    
    return products


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://example-shop.com/products")
        
        products = extract_products(page, ".product-card")
        
        # Export to JSON
        with open("products.json", "w") as f:
            json.dump([p.model_dump() for p in products], f, indent=2)
        
        browser.close()


if __name__ == "__main__":
    main()
```

---

## Form Automation

### Complete Form Filling

```python
#!/usr/bin/env python3
"""Form automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from pydantic import BaseModel
from typing import Optional
from pathlib import Path


class FormData(BaseModel):
    """Form data model."""
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    country: str = "United States"
    agree_terms: bool = True
    newsletter: bool = False
    file_upload: Optional[str] = None


class FormAutomator:
    """Automate form filling."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def fill_text_field(self, selector: str, value: str):
        """Fill text input field."""
        self.page.fill(selector, value)
    
    def select_dropdown(self, selector: str, value: str):
        """Select dropdown option by value or label."""
        self.page.select_option(selector, value)
    
    def check_checkbox(self, selector: str, checked: bool = True):
        """Check or uncheck checkbox."""
        if checked:
            self.page.check(selector)
        else:
            self.page.uncheck(selector)
    
    def select_radio(self, selector: str):
        """Select radio button."""
        self.page.check(selector)
    
    def upload_file(self, selector: str, file_path: str):
        """Upload file."""
        self.page.set_input_files(selector, file_path)
    
    def fill_form(self, form_data: FormData, field_mapping: dict[str, str]):
        """Fill entire form from data model."""
        data = form_data.model_dump()
        
        for field_name, selector in field_mapping.items():
            if field_name not in data or data[field_name] is None:
                continue
            
            value = data[field_name]
            element = self.page.locator(selector)
            
            # Determine field type and fill accordingly
            tag = element.evaluate("el => el.tagName.toLowerCase()")
            input_type = element.get_attribute("type") or "text"
            
            if tag == "select":
                self.select_dropdown(selector, value)
            elif tag == "textarea":
                self.fill_text_field(selector, value)
            elif input_type == "checkbox":
                self.check_checkbox(selector, bool(value))
            elif input_type == "radio":
                if value:
                    self.select_radio(selector)
            elif input_type == "file":
                if value and Path(value).exists():
                    self.upload_file(selector, value)
            else:
                self.fill_text_field(selector, str(value))
    
    def submit_form(self, submit_selector: str = "button[type=submit]"):
        """Submit form."""
        self.page.click(submit_selector)


def automate_registration():
    """Example: Automate registration form."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://example.com/register")
        
        form = FormAutomator(page)
        
        form_data = FormData(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1-555-123-4567",
            company="Acme Inc",
            country="United States",
            agree_terms=True,
            newsletter=False,
        )
        
        field_mapping = {
            "first_name": "#firstName",
            "last_name": "#lastName",
            "email": "#email",
            "phone": "#phone",
            "company": "#company",
            "country": "select[name=country]",
            "agree_terms": "#agreeTerms",
            "newsletter": "#newsletter",
        }
        
        form.fill_form(form_data, field_mapping)
        form.submit_form()
        
        # Wait for success
        page.wait_for_url("**/success**")
        print("Registration completed!")
        
        browser.close()


if __name__ == "__main__":
    automate_registration()
```

---

## Error Handling and Recovery

### Retry Pattern

```python
#!/usr/bin/env python3
"""Error handling with retry - run with: uv run script.py"""

import asyncio
from functools import wraps
from typing import Callable, Any
import structlog

log = structlog.get_logger()


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    log.warning(
                        "attempt_failed",
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error=str(e)
                    )
                    if attempt < max_attempts:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            import time
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    log.warning(
                        "attempt_failed",
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error=str(e)
                    )
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RobustAutomator:
    """Automator with built-in error recovery."""
    
    def __init__(self, page):
        self.page = page
    
    @retry(max_attempts=3, delay=1.0, exceptions=(Exception,))
    def safe_click(self, selector: str):
        """Click with retry on failure."""
        self.page.click(selector, timeout=10000)
    
    @retry(max_attempts=3, delay=1.0)
    def safe_fill(self, selector: str, value: str):
        """Fill with retry on failure."""
        self.page.fill(selector, value, timeout=10000)
    
    def click_with_fallback(self, selectors: list[str]):
        """Try multiple selectors until one works."""
        for selector in selectors:
            try:
                if self.page.locator(selector).is_visible():
                    self.page.click(selector)
                    return True
            except Exception:
                continue
        raise Exception(f"None of the selectors worked: {selectors}")
    
    def handle_popup(self):
        """Dismiss common popups."""
        popup_selectors = [
            "[aria-label='Close']",
            ".popup-close",
            "#cookie-accept",
            ".modal-close",
            "button:has-text('Accept')",
            "button:has-text('Close')",
        ]
        
        for selector in popup_selectors:
            try:
                if self.page.locator(selector).is_visible():
                    self.page.click(selector)
                    log.info("popup_dismissed", selector=selector)
            except Exception:
                pass
    
    def wait_and_retry(self, action: Callable, timeout: int = 30):
        """Wait for page stability then perform action."""
        self.page.wait_for_load_state("networkidle")
        self.handle_popup()
        return action()
```

---

## Workflow Orchestration

### Multi-Step Workflow

```python
#!/usr/bin/env python3
"""Workflow orchestration - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional
import json
from datetime import datetime
import structlog

log = structlog.get_logger()


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Workflow step definition."""
    name: str
    action: Callable[[Page], Any]
    depends_on: list[str] = field(default_factory=list)
    retry_count: int = 3
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None


@dataclass
class WorkflowContext:
    """Shared context between workflow steps."""
    data: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)


class Workflow:
    """Multi-step workflow orchestrator."""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: list[WorkflowStep] = []
        self.context = WorkflowContext()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def add_step(
        self,
        name: str,
        action: Callable[[Page], Any],
        depends_on: list[str] = None,
        retry_count: int = 3
    ):
        """Add step to workflow."""
        step = WorkflowStep(
            name=name,
            action=action,
            depends_on=depends_on or [],
            retry_count=retry_count
        )
        self.steps.append(step)
        return self
    
    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Get step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None
    
    def can_run_step(self, step: WorkflowStep) -> bool:
        """Check if step dependencies are met."""
        for dep_name in step.depends_on:
            dep_step = self.get_step(dep_name)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        return True
    
    def run_step(self, step: WorkflowStep, page: Page) -> bool:
        """Run a single step with retry."""
        step.status = StepStatus.RUNNING
        
        for attempt in range(1, step.retry_count + 1):
            try:
                log.info("step_running", step=step.name, attempt=attempt)
                step.result = step.action(page)
                step.status = StepStatus.COMPLETED
                log.info("step_completed", step=step.name)
                return True
            except Exception as e:
                log.warning("step_failed", step=step.name, attempt=attempt, error=str(e))
                step.error = str(e)
                if attempt == step.retry_count:
                    step.status = StepStatus.FAILED
                    return False
        
        return False
    
    def run(self, page: Page) -> bool:
        """Execute workflow."""
        self.start_time = datetime.now()
        log.info("workflow_started", name=self.name)
        
        pending_steps = list(self.steps)
        max_iterations = len(self.steps) * 2
        iteration = 0
        
        while pending_steps and iteration < max_iterations:
            iteration += 1
            made_progress = False
            
            for step in list(pending_steps):
                if step.status == StepStatus.PENDING and self.can_run_step(step):
                    success = self.run_step(step, page)
                    pending_steps.remove(step)
                    made_progress = True
                    
                    if not success:
                        # Skip dependent steps
                        for other in pending_steps:
                            if step.name in other.depends_on:
                                other.status = StepStatus.SKIPPED
                                pending_steps.remove(other)
            
            if not made_progress:
                break
        
        self.end_time = datetime.now()
        
        # Check final status
        failed_steps = [s for s in self.steps if s.status == StepStatus.FAILED]
        if failed_steps:
            log.error("workflow_failed", failed_steps=[s.name for s in failed_steps])
            return False
        
        log.info("workflow_completed", name=self.name, duration=str(self.end_time - self.start_time))
        return True
    
    def get_report(self) -> dict:
        """Generate workflow execution report."""
        return {
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": str(self.end_time - self.start_time) if self.end_time and self.start_time else None,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "error": s.error,
                }
                for s in self.steps
            ]
        }


# Example workflow
def create_data_extraction_workflow():
    """Create a data extraction workflow."""
    
    def login(page: Page):
        page.goto("https://example.com/login")
        page.fill("#username", "user")
        page.fill("#password", "pass")
        page.click("button[type=submit]")
        page.wait_for_url("**/dashboard**")
        return True
    
    def navigate_to_reports(page: Page):
        page.click("a[href='/reports']")
        page.wait_for_selector(".reports-table")
        return True
    
    def download_report(page: Page):
        page.click("#download-csv")
        # Wait for download
        with page.expect_download() as download_info:
            page.click("#confirm-download")
        download = download_info.value
        download.save_as("./report.csv")
        return download.path()
    
    def logout(page: Page):
        page.click("#logout")
        page.wait_for_url("**/login**")
        return True
    
    workflow = Workflow("Daily Report Download")
    workflow.add_step("login", login)
    workflow.add_step("navigate", navigate_to_reports, depends_on=["login"])
    workflow.add_step("download", download_report, depends_on=["navigate"])
    workflow.add_step("logout", logout, depends_on=["download"])
    
    return workflow


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        workflow = create_data_extraction_workflow()
        success = workflow.run(page)
        
        report = workflow.get_report()
        print(json.dumps(report, indent=2))
        
        browser.close()
```

---

## Scheduling

### Cron-Based Scheduling

```python
#!/usr/bin/env python3
"""Scheduled automation - run with: uv run scheduler.py"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from playwright.sync_api import sync_playwright
import structlog
from datetime import datetime

log = structlog.get_logger()


def run_daily_report():
    """Run daily report automation."""
    log.info("job_started", job="daily_report", time=datetime.now().isoformat())
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("https://example.com/reports")
            # ... automation logic
            log.info("job_completed", job="daily_report")
        except Exception as e:
            log.error("job_failed", job="daily_report", error=str(e))
        finally:
            browser.close()


def run_hourly_check():
    """Run hourly status check."""
    log.info("job_started", job="hourly_check", time=datetime.now().isoformat())
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("https://example.com/status")
            status = page.locator("#system-status").text_content()
            log.info("status_check", status=status)
        except Exception as e:
            log.error("job_failed", job="hourly_check", error=str(e))
        finally:
            browser.close()


def main():
    scheduler = BlockingScheduler()
    
    # Daily at 6 AM
    scheduler.add_job(
        run_daily_report,
        CronTrigger(hour=6, minute=0),
        id="daily_report",
        name="Daily Report Download"
    )
    
    # Every hour
    scheduler.add_job(
        run_hourly_check,
        CronTrigger(minute=0),
        id="hourly_check",
        name="Hourly Status Check"
    )
    
    # Every weekday at 9 AM
    scheduler.add_job(
        lambda: log.info("weekday_job"),
        CronTrigger(day_of_week="mon-fri", hour=9),
        id="weekday_job"
    )
    
    log.info("scheduler_started", jobs=len(scheduler.get_jobs()))
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("scheduler_stopped")


if __name__ == "__main__":
    main()
```

---

## Module Reference

### Core Modules
- **rpa-browser-automation.md** - Advanced Playwright patterns, multi-browser, mobile emulation, stealth mode
- **rpa-data-extraction.md** - Scraping, parsing, structured data extraction, tables, infinite scroll
- **rpa-form-automation.md** - Form filling, dropdowns, file uploads, CAPTCHA handling

### Workflow Modules
- **rpa-workflows.md** - Multi-step orchestration, state machines, checkpoints, Prefect/Temporal
- **rpa-scheduling.md** - Cron jobs, APScheduler, event-driven triggers, queue-based processing

### Advanced Modules
- **rpa-authentication.md** - Login automation, MFA/TOTP, OAuth, SSO, session management
- **rpa-error-handling.md** - Retry patterns, circuit breaker, recovery, monitoring, alerting
- **rpa-ocr-vision.md** - Visual automation, OCR with Tesseract, image recognition

### Enterprise Modules (v2.0)
- **rpa-credentials.md** - HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, encrypted local storage
- **rpa-cicd.md** - GitHub Actions, GitLab CI, Docker containers, Kubernetes deployment
- **rpa-observability.md** - Structlog logging, Prometheus metrics, OpenTelemetry, Grafana dashboards
- **rpa-desktop.md** - Windows/macOS desktop automation with pyautogui and pywinauto
- **rpa-documents.md** - Excel (openpyxl), PDF (pypdf/reportlab), Word (python-docx), Email (IMAP/SMTP)

---

## Best Practices

### 1. Selector Stability
- Prefer data-testid over CSS classes
- Use role-based selectors when possible
- Avoid XPath unless necessary
- Create selector constants/enums

### 2. Performance
- Block unnecessary resources (images, fonts, CSS)
- Use parallel processing for multiple pages
- Implement connection pooling
- Cache session state

### 3. Reliability
- Always use explicit waits
- Implement retry mechanisms
- Handle popups and overlays
- Save screenshots on failure

### 4. Maintainability
- Use Page Object Model pattern
- Separate selectors from logic
- Create reusable automation components
- Document automation workflows

### 5. Security
- Never hardcode credentials
- Use environment variables or secret managers
- Encrypt session storage
- Audit automation access

---

## Installation Quick Start

```bash
# Create project
mkdir my-rpa-bot && cd my-rpa-bot

# Initialize with uv
uv init

# Add core dependencies
uv add playwright beautifulsoup4 pandas httpx pydantic structlog

# Install browsers
uv run playwright install chromium

# Create first bot
cat > bot.py << 'EOF'
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
EOF

# Run
uv run bot.py
```

---

---

## Enterprise Edition (v2.0) Features

### Credentials & Secrets Management
```bash
# See rpa-credentials.md for full details
uv add hvac boto3 azure-identity azure-keyvault-secrets cryptography
```
- HashiCorp Vault integration
- AWS Secrets Manager
- Azure Key Vault
- Encrypted local storage with Fernet

### CI/CD Integration
```bash
# See rpa-cicd.md for full details
# Docker, GitHub Actions, GitLab CI, Kubernetes
```
- Containerized bot deployment
- GitHub Actions workflows
- GitLab CI pipelines
- Kubernetes CronJobs and Deployments

### Observability
```bash
# See rpa-observability.md for full details
uv add structlog prometheus-client opentelemetry-api opentelemetry-sdk
```
- Structured logging with structlog
- Prometheus metrics collection
- OpenTelemetry tracing
- Grafana dashboard templates
- PagerDuty/Slack alerting

### Desktop Automation
```bash
# See rpa-desktop.md for full details
uv add pyautogui pywinauto  # Windows
uv add pyautogui pyobjc     # macOS
```
- Windows UI automation with pywinauto
- Cross-platform mouse/keyboard with pyautogui
- Screen capture and image matching
- Application launching and control

### Document Automation
```bash
# See rpa-documents.md for full details
uv add openpyxl pandas pypdf reportlab python-docx aiosmtplib aioimaplib
```
- Excel: openpyxl for reading/writing, pandas integration, charts
- PDF: Reading with pypdf, generation with reportlab, watermarks
- Word: python-docx for document generation and templates
- Email: IMAP reading, SMTP sending, batch mail merge
- CSV: Streaming, transformation, validation

---

**Next Module:** See **rpa-browser-automation.md** for advanced Playwright patterns.
