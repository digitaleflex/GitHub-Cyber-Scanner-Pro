# RPA - Robotic Process Automation Framework

> **Version 2.0 - Enterprise Edition**

Enterprise-grade web automation for sites without APIs. A complete UiPath alternative using open-source tools.

## Stack

```
playwright + python + mitmproxy + uv + pyautogui + pywinauto
```

## Quick Start

### Installation

```bash
# Create project
mkdir my-rpa-bot && cd my-rpa-bot

# Initialize with uv
uv init

# Add dependencies
uv add playwright beautifulsoup4 pandas httpx pydantic structlog

# Install browsers
uv run playwright install chromium
```

### First Bot

```python
#!/usr/bin/env python3
"""my_bot.py - run with: uv run my_bot.py"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Navigate
    page.goto("https://example.com")
    
    # Fill form
    page.fill("#username", "user")
    page.fill("#password", "pass")
    page.click("button[type=submit]")
    
    # Extract data
    title = page.title()
    print(f"Page title: {title}")
    
    browser.close()
```

Run:
```bash
uv run my_bot.py
```

## Module Reference

### Core Modules
| Module | Description |
|--------|-------------|
| `SKILL.md` | Core patterns and complete reference |
| `rpa-browser-automation.md` | Multi-browser, mobile emulation, stealth mode |
| `rpa-data-extraction.md` | Scraping, tables, pagination, infinite scroll |
| `rpa-form-automation.md` | Forms, dropdowns, file uploads, CAPTCHA |
| `rpa-workflows.md` | Multi-step orchestration, state machines |
| `rpa-authentication.md` | Login, OAuth, MFA, session management |
| `rpa-scheduling.md` | Cron jobs, APScheduler, task queues |
| `rpa-ocr-vision.md` | OCR, image recognition, visual automation |
| `rpa-error-handling.md` | Retry, circuit breaker, recovery |

### Enterprise Modules (v2.0)
| Module | Description |
|--------|-------------|
| `rpa-credentials.md` | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault |
| `rpa-cicd.md` | GitHub Actions, GitLab CI, Docker, Kubernetes |
| `rpa-observability.md` | Structlog, Prometheus, OpenTelemetry, Grafana |
| `rpa-desktop.md` | Windows/macOS desktop automation (pyautogui, pywinauto) |
| `rpa-documents.md` | Excel, PDF, Word, Email, CSV automation |

## Common Patterns

### Data Extraction

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto("https://quotes.toscrape.com")
    
    quotes = []
    for quote in page.locator(".quote").all():
        quotes.append({
            "text": quote.locator(".text").text_content(),
            "author": quote.locator(".author").text_content(),
        })
    
    print(f"Extracted {len(quotes)} quotes")
    browser.close()
```

### Form Automation

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    page.goto("https://example.com/form")
    
    # Text inputs
    page.fill("#name", "John Doe")
    page.fill("#email", "john@example.com")
    
    # Dropdown
    page.select_option("#country", "US")
    
    # Checkbox
    page.check("#agree_terms")
    
    # File upload
    page.set_input_files("#resume", "resume.pdf")
    
    # Submit
    page.click("button[type=submit]")
    
    browser.close()
```

### Session Persistence

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

SESSION_FILE = "session.json"

with sync_playwright() as p:
    browser = p.chromium.launch()
    
    # Load or create session
    if Path(SESSION_FILE).exists():
        context = browser.new_context(storage_state=SESSION_FILE)
    else:
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto("https://example.com/login")
        page.fill("#username", "user")
        page.fill("#password", "pass")
        page.click("button[type=submit]")
        
        # Save session
        context.storage_state(path=SESSION_FILE)
    
    page = context.new_page()
    page.goto("https://example.com/dashboard")
    print(page.title())
    
    browser.close()
```

### Parallel Execution

```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_url(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        title = await page.title()
        await browser.close()
        return {"url": url, "title": title}

async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://quotes.toscrape.com",
    ]
    
    results = await asyncio.gather(*[scrape_url(url) for url in urls])
    for r in results:
        print(f"{r['url']}: {r['title']}")

asyncio.run(main())
```

### Scheduled Tasks

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from playwright.sync_api import sync_playwright

def daily_report():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com/reports")
        # ... extract data
        browser.close()

scheduler = BlockingScheduler()
scheduler.add_job(daily_report, 'cron', hour=6, minute=0)
scheduler.start()
```

## Best Practices

1. **Use `uv`** - Always manage Python with uv (never pip)
2. **Prefer selectors** - data-testid > role > CSS > XPath
3. **Auto-wait** - Playwright handles waiting automatically
4. **Session caching** - Avoid repeated logins
5. **Error recovery** - Implement retry with backoff
6. **Screenshots on failure** - Capture state for debugging
7. **Headless by default** - Use headless=True for production
8. **Secrets management** - Use Vault/Secrets Manager, never hardcode
9. **Observability** - Structured logging + metrics for production
10. **CI/CD** - Containerize bots for consistent deployment

## Enterprise Quick Start

```bash
# Full enterprise installation
uv add playwright beautifulsoup4 pandas httpx pydantic structlog
uv add openpyxl pypdf reportlab python-docx  # Documents
uv add aiosmtplib aioimaplib                  # Email
uv add hvac boto3                             # Secrets
uv add prometheus-client opentelemetry-sdk   # Observability
uv add pyautogui                              # Desktop (cross-platform)
uv add pywinauto                              # Desktop (Windows)

# Install browsers
uv run playwright install chromium
```

## Requirements

- Python 3.11+
- Playwright
- uv package manager

## Platform Support

| Platform | Web Automation | Desktop Automation |
|----------|----------------|-------------------|
| macOS | Full support | pyautogui + pyobjc |
| Linux | Full support | pyautogui |
| Windows | Full support | pyautogui + pywinauto |

## Version History

| Version | Features |
|---------|----------|
| 1.0 | Core browser automation, data extraction, workflows |
| 2.0 | Enterprise: credentials, CI/CD, observability, desktop, documents |

## License

MIT
