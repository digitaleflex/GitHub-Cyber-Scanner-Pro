# RPA Browser Automation Module

Advanced Playwright patterns for enterprise browser automation. This module covers multi-browser support, mobile emulation, stealth mode, parallel execution, and complex interaction patterns.

## Browser Configuration

### Multi-Browser Launch

```python
#!/usr/bin/env python3
"""Multi-browser automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@dataclass
class BrowserConfig:
    """Browser configuration options."""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    slow_mo: int = 0
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone: str = "America/New_York"
    geolocation: Optional[dict] = None
    permissions: list[str] = None
    proxy: Optional[dict] = None
    downloads_path: str = "./downloads"
    ignore_https_errors: bool = False
    java_script_enabled: bool = True
    
    def get_browser_args(self) -> list[str]:
        """Get browser-specific arguments."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        if self.headless:
            args.append("--disable-gpu")
        return args


class BrowserManager:
    """Manage browser instances and contexts."""
    
    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: list[BrowserContext] = []
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self._launch_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for ctx in self.contexts:
            ctx.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _launch_browser(self):
        """Launch browser based on config."""
        browser_launcher = getattr(self.playwright, self.config.browser_type.value)
        
        self.browser = browser_launcher.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
            args=self.config.get_browser_args(),
            downloads_path=self.config.downloads_path,
        )
    
    def new_context(self, **overrides) -> BrowserContext:
        """Create new browser context with config."""
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height
            },
            "locale": self.config.locale,
            "timezone_id": self.config.timezone,
            "ignore_https_errors": self.config.ignore_https_errors,
            "java_script_enabled": self.config.java_script_enabled,
        }
        
        if self.config.user_agent:
            context_options["user_agent"] = self.config.user_agent
        
        if self.config.geolocation:
            context_options["geolocation"] = self.config.geolocation
            context_options["permissions"] = ["geolocation"]
        
        if self.config.permissions:
            context_options["permissions"] = self.config.permissions
        
        if self.config.proxy:
            context_options["proxy"] = self.config.proxy
        
        context_options.update(overrides)
        
        context = self.browser.new_context(**context_options)
        self.contexts.append(context)
        return context
    
    def new_page(self, **context_overrides):
        """Create new page with fresh context."""
        context = self.new_context(**context_overrides)
        return context.new_page()


# Usage
if __name__ == "__main__":
    config = BrowserConfig(
        browser_type=BrowserType.CHROMIUM,
        headless=False,
        viewport_width=1440,
        viewport_height=900,
        locale="en-GB",
        timezone="Europe/London",
    )
    
    with BrowserManager(config) as manager:
        page = manager.new_page()
        page.goto("https://example.com")
        print(page.title())
```

### Mobile Device Emulation

```python
#!/usr/bin/env python3
"""Mobile device emulation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright


# Common device presets
DEVICES = {
    "iphone_14": {
        "viewport": {"width": 390, "height": 844},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "iphone_14_pro_max": {
        "viewport": {"width": 430, "height": 932},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 3,
        "is_mobile": True,
        "has_touch": True,
    },
    "pixel_7": {
        "viewport": {"width": 412, "height": 915},
        "user_agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36",
        "device_scale_factor": 2.625,
        "is_mobile": True,
        "has_touch": True,
    },
    "ipad_pro": {
        "viewport": {"width": 1024, "height": 1366},
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
    },
}


def emulate_device(device_name: str):
    """Emulate mobile device."""
    device = DEVICES.get(device_name)
    if not device:
        raise ValueError(f"Unknown device: {device_name}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**device)
        page = context.new_page()
        
        page.goto("https://example.com")
        
        # Mobile-specific interactions
        page.tap("#menu-button")  # Touch tap
        page.touchscreen.tap(100, 200)  # Coordinate tap
        
        # Swipe gesture
        page.mouse.move(200, 400)
        page.mouse.down()
        page.mouse.move(200, 100, steps=10)
        page.mouse.up()
        
        # Screenshot at device resolution
        page.screenshot(path=f"{device_name}.png")
        
        browser.close()


def use_playwright_devices():
    """Use built-in Playwright device descriptors."""
    with sync_playwright() as p:
        # Playwright has built-in device descriptors
        iphone = p.devices["iPhone 14 Pro Max"]
        
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(**iphone)
        page = context.new_page()
        
        page.goto("https://example.com")
        page.screenshot(path="iphone_14_pro_max.png")
        
        browser.close()


if __name__ == "__main__":
    emulate_device("iphone_14")
```

---

## Stealth Mode

### Anti-Detection Patterns

```python
#!/usr/bin/env python3
"""Stealth browser automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
import random
import time


class StealthBrowser:
    """Browser with anti-detection measures."""
    
    # Realistic user agents
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]
    
    # Realistic viewports
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1536, "height": 864},
        {"width": 1440, "height": 900},
        {"width": 1366, "height": 768},
        {"width": 1280, "height": 720},
    ]
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self._launch_stealth_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _launch_stealth_browser(self):
        """Launch browser with stealth settings."""
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
            ]
        )
        
        self.context = self.browser.new_context(
            viewport=random.choice(self.VIEWPORTS),
            user_agent=random.choice(self.USER_AGENTS),
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"longitude": -73.935242, "latitude": 40.730610},
            color_scheme="light",
        )
        
        self.page = self.context.new_page()
        self._apply_stealth_scripts()
    
    def _apply_stealth_scripts(self):
        """Apply JavaScript patches to avoid detection."""
        
        # Remove webdriver property
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Mock plugins
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ]
            });
        """)
        
        # Mock languages
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        # Mock hardware concurrency
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
        """)
        
        # Mock device memory
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
        """)
        
        # Fix chrome runtime
        self.page.add_init_script("""
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)
        
        # Mock permissions API
        self.page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    def human_like_delay(self, min_ms: int = 100, max_ms: int = 500):
        """Add human-like random delay."""
        delay = random.randint(min_ms, max_ms) / 1000
        time.sleep(delay)
    
    def human_like_type(self, selector: str, text: str):
        """Type with human-like speed variation."""
        self.page.click(selector)
        for char in text:
            self.page.keyboard.type(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def human_like_scroll(self):
        """Scroll with human-like behavior."""
        # Random scroll amounts
        scroll_heights = [100, 200, 300, 400, 500]
        
        for _ in range(random.randint(2, 5)):
            scroll_amount = random.choice(scroll_heights)
            self.page.mouse.wheel(0, scroll_amount)
            self.human_like_delay(200, 800)
    
    def random_mouse_movement(self):
        """Move mouse randomly across page."""
        viewport = self.page.viewport_size
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, viewport["width"] - 100)
            y = random.randint(100, viewport["height"] - 100)
            self.page.mouse.move(x, y, steps=random.randint(5, 15))
            self.human_like_delay(100, 300)
    
    def navigate(self, url: str):
        """Navigate with human-like behavior."""
        self.page.goto(url, wait_until="domcontentloaded")
        self.human_like_delay(500, 1500)
        self.random_mouse_movement()
        self.human_like_scroll()


if __name__ == "__main__":
    with StealthBrowser() as browser:
        browser.navigate("https://bot.sannysoft.com/")
        browser.page.screenshot(path="stealth_test.png")
        print("Check stealth_test.png for bot detection results")
```

---

## Parallel Execution

### Concurrent Page Processing

```python
#!/usr/bin/env python3
"""Parallel browser automation - run with: uv run script.py"""

import asyncio
from playwright.async_api import async_playwright, Browser, Page
from dataclasses import dataclass
from typing import Any, Callable, Awaitable
import structlog

log = structlog.get_logger()


@dataclass
class TaskResult:
    """Result from parallel task."""
    url: str
    success: bool
    data: Any = None
    error: str = None


class ParallelBrowser:
    """Execute browser tasks in parallel."""
    
    def __init__(self, max_concurrent: int = 5, headless: bool = True):
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.playwright = None
        self.browser: Browser = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def process_url(
        self,
        url: str,
        task: Callable[[Page], Awaitable[Any]],
        semaphore: asyncio.Semaphore
    ) -> TaskResult:
        """Process single URL with task."""
        async with semaphore:
            context = await self.browser.new_context()
            page = await context.new_page()
            
            try:
                log.info("processing", url=url)
                await page.goto(url, wait_until="networkidle", timeout=30000)
                data = await task(page)
                return TaskResult(url=url, success=True, data=data)
            except Exception as e:
                log.error("failed", url=url, error=str(e))
                return TaskResult(url=url, success=False, error=str(e))
            finally:
                await context.close()
    
    async def process_urls(
        self,
        urls: list[str],
        task: Callable[[Page], Awaitable[Any]]
    ) -> list[TaskResult]:
        """Process multiple URLs in parallel."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        tasks = [
            self.process_url(url, task, semaphore)
            for url in urls
        ]
        
        return await asyncio.gather(*tasks)


async def extract_title(page: Page) -> dict:
    """Example task: extract page title and meta."""
    title = await page.title()
    description = await page.locator("meta[name='description']").get_attribute("content") \
        if await page.locator("meta[name='description']").count() > 0 else None
    
    return {
        "title": title,
        "description": description,
        "url": page.url
    }


async def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://quotes.toscrape.com",
        "https://books.toscrape.com",
        "https://scrapingclub.com/exercise/list_basic/",
    ]
    
    async with ParallelBrowser(max_concurrent=3, headless=True) as browser:
        results = await browser.process_urls(urls, extract_title)
        
        for result in results:
            if result.success:
                log.info("success", **result.data)
            else:
                log.error("failed", url=result.url, error=result.error)


if __name__ == "__main__":
    asyncio.run(main())
```

### Browser Pool

```python
#!/usr/bin/env python3
"""Browser pool for high-throughput automation - run with: uv run script.py"""

import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext
from typing import Optional
from collections import deque
import structlog

log = structlog.get_logger()


class BrowserPool:
    """Pool of browser contexts for reuse."""
    
    def __init__(
        self,
        pool_size: int = 5,
        headless: bool = True,
        max_pages_per_context: int = 10
    ):
        self.pool_size = pool_size
        self.headless = headless
        self.max_pages_per_context = max_pages_per_context
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.available_contexts: deque[BrowserContext] = deque()
        self.context_page_counts: dict[BrowserContext, int] = {}
        self._lock = asyncio.Lock()
    
    async def start(self):
        """Initialize browser pool."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless
        )
        
        # Pre-create contexts
        for _ in range(self.pool_size):
            context = await self._create_context()
            self.available_contexts.append(context)
        
        log.info("pool_started", size=self.pool_size)
    
    async def stop(self):
        """Shutdown browser pool."""
        for context in list(self.available_contexts):
            await context.close()
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        log.info("pool_stopped")
    
    async def _create_context(self) -> BrowserContext:
        """Create new browser context."""
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.context_page_counts[context] = 0
        return context
    
    async def acquire(self) -> BrowserContext:
        """Get context from pool."""
        async with self._lock:
            while not self.available_contexts:
                # Wait for context to become available
                await asyncio.sleep(0.1)
            
            context = self.available_contexts.popleft()
            self.context_page_counts[context] += 1
            
            # Check if context should be recycled
            if self.context_page_counts[context] >= self.max_pages_per_context:
                await context.close()
                context = await self._create_context()
            
            return context
    
    async def release(self, context: BrowserContext):
        """Return context to pool."""
        async with self._lock:
            if context in self.context_page_counts:
                self.available_contexts.append(context)


class PooledAutomator:
    """Automator using browser pool."""
    
    def __init__(self, pool: BrowserPool):
        self.pool = pool
    
    async def process(self, url: str, task) -> dict:
        """Process URL using pooled context."""
        context = await self.pool.acquire()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle")
            result = await task(page)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            await page.close()
            await self.pool.release(context)


async def main():
    pool = BrowserPool(pool_size=3, headless=True)
    await pool.start()
    
    try:
        automator = PooledAutomator(pool)
        
        urls = [f"https://httpbin.org/delay/{i}" for i in range(1, 6)]
        
        async def get_response(page):
            return await page.content()
        
        tasks = [automator.process(url, get_response) for url in urls]
        results = await asyncio.gather(*tasks)
        
        for url, result in zip(urls, results):
            log.info("result", url=url, success=result["success"])
    
    finally:
        await pool.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Complex Interactions

### Drag and Drop

```python
#!/usr/bin/env python3
"""Complex interactions - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page


class InteractionHelper:
    """Helper for complex browser interactions."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def drag_and_drop(self, source: str, target: str):
        """Drag element from source to target."""
        self.page.drag_and_drop(source, target)
    
    def drag_and_drop_coordinates(
        self,
        source_x: int, source_y: int,
        target_x: int, target_y: int,
        steps: int = 10
    ):
        """Drag from source coordinates to target."""
        self.page.mouse.move(source_x, source_y)
        self.page.mouse.down()
        self.page.mouse.move(target_x, target_y, steps=steps)
        self.page.mouse.up()
    
    def hover_and_click(self, hover_selector: str, click_selector: str):
        """Hover over element then click another."""
        self.page.hover(hover_selector)
        self.page.wait_for_selector(click_selector, state="visible")
        self.page.click(click_selector)
    
    def double_click(self, selector: str):
        """Double-click element."""
        self.page.dblclick(selector)
    
    def right_click(self, selector: str):
        """Right-click (context menu)."""
        self.page.click(selector, button="right")
    
    def click_with_modifier(self, selector: str, modifier: str = "Control"):
        """Click with keyboard modifier (Ctrl+Click, Shift+Click)."""
        self.page.click(selector, modifiers=[modifier])
    
    def focus_and_blur(self, selector: str):
        """Focus element then blur."""
        self.page.focus(selector)
        self.page.evaluate(f"document.querySelector('{selector}').blur()")
    
    def scroll_to_element(self, selector: str):
        """Scroll element into view."""
        self.page.locator(selector).scroll_into_view_if_needed()
    
    def scroll_page(self, direction: str = "down", amount: int = 500):
        """Scroll page in direction."""
        if direction == "down":
            self.page.mouse.wheel(0, amount)
        elif direction == "up":
            self.page.mouse.wheel(0, -amount)
        elif direction == "right":
            self.page.mouse.wheel(amount, 0)
        elif direction == "left":
            self.page.mouse.wheel(-amount, 0)
    
    def resize_element(self, handle_selector: str, offset_x: int, offset_y: int):
        """Resize by dragging handle."""
        box = self.page.locator(handle_selector).bounding_box()
        if box:
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2
            self.drag_and_drop_coordinates(
                int(center_x), int(center_y),
                int(center_x + offset_x), int(center_y + offset_y)
            )
    
    def multi_select(self, selectors: list[str]):
        """Select multiple elements with Ctrl+Click."""
        for i, selector in enumerate(selectors):
            if i == 0:
                self.page.click(selector)
            else:
                self.page.click(selector, modifiers=["Control"])
    
    def range_select(self, first: str, last: str):
        """Select range with Shift+Click."""
        self.page.click(first)
        self.page.click(last, modifiers=["Shift"])


def example_drag_drop():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Test on drag-drop demo page
        page.goto("https://the-internet.herokuapp.com/drag_and_drop")
        
        helper = InteractionHelper(page)
        
        # Drag column A to column B position
        helper.drag_and_drop("#column-a", "#column-b")
        
        page.screenshot(path="drag_drop_result.png")
        browser.close()


if __name__ == "__main__":
    example_drag_drop()
```

### Keyboard Shortcuts

```python
#!/usr/bin/env python3
"""Keyboard automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page


class KeyboardHelper:
    """Helper for keyboard interactions."""
    
    # Common shortcuts
    SHORTCUTS = {
        "copy": "Control+c",
        "paste": "Control+v",
        "cut": "Control+x",
        "undo": "Control+z",
        "redo": "Control+y",
        "select_all": "Control+a",
        "save": "Control+s",
        "find": "Control+f",
        "new_tab": "Control+t",
        "close_tab": "Control+w",
        "refresh": "F5",
        "hard_refresh": "Control+Shift+r",
    }
    
    def __init__(self, page: Page):
        self.page = page
    
    def press_shortcut(self, name: str):
        """Press named shortcut."""
        if name in self.SHORTCUTS:
            self.page.keyboard.press(self.SHORTCUTS[name])
        else:
            raise ValueError(f"Unknown shortcut: {name}")
    
    def press_keys(self, *keys: str):
        """Press multiple keys as chord."""
        chord = "+".join(keys)
        self.page.keyboard.press(chord)
    
    def type_text(self, text: str, delay: int = 50):
        """Type text with delay between keystrokes."""
        self.page.keyboard.type(text, delay=delay)
    
    def press_and_hold(self, key: str, action: callable):
        """Hold key while performing action."""
        self.page.keyboard.down(key)
        action()
        self.page.keyboard.up(key)
    
    def tab_navigation(self, count: int = 1, reverse: bool = False):
        """Navigate using Tab key."""
        key = "Shift+Tab" if reverse else "Tab"
        for _ in range(count):
            self.page.keyboard.press(key)
    
    def arrow_navigation(self, direction: str, count: int = 1):
        """Navigate using arrow keys."""
        key_map = {
            "up": "ArrowUp",
            "down": "ArrowDown",
            "left": "ArrowLeft",
            "right": "ArrowRight",
        }
        key = key_map.get(direction, "ArrowDown")
        for _ in range(count):
            self.page.keyboard.press(key)
    
    def clear_input(self, selector: str):
        """Clear input field."""
        self.page.click(selector)
        self.page.keyboard.press("Control+a")
        self.page.keyboard.press("Backspace")
    
    def replace_text(self, selector: str, new_text: str):
        """Select all and replace text."""
        self.page.click(selector)
        self.page.keyboard.press("Control+a")
        self.page.keyboard.type(new_text)


def example_keyboard():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://example.com")
        
        kb = KeyboardHelper(page)
        
        # Open find dialog
        kb.press_shortcut("find")
        
        # Type search term
        kb.type_text("example")
        
        # Close dialog
        page.keyboard.press("Escape")
        
        browser.close()


if __name__ == "__main__":
    example_keyboard()
```

---

## Frame and Shadow DOM

### iframe Handling

```python
#!/usr/bin/env python3
"""iframe and frame handling - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page, Frame


class FrameHelper:
    """Helper for iframe interactions."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def list_frames(self) -> list[dict]:
        """List all frames on page."""
        frames = []
        for frame in self.page.frames:
            frames.append({
                "name": frame.name,
                "url": frame.url,
                "is_detached": frame.is_detached(),
            })
        return frames
    
    def get_frame_by_name(self, name: str) -> Frame:
        """Get frame by name attribute."""
        return self.page.frame(name=name)
    
    def get_frame_by_url(self, url_pattern: str) -> Frame:
        """Get frame by URL pattern."""
        return self.page.frame(url=url_pattern)
    
    def get_frame_by_selector(self, selector: str) -> Frame:
        """Get frame by iframe selector."""
        frame_element = self.page.locator(selector)
        return frame_element.content_frame()
    
    def click_in_frame(self, frame_selector: str, element_selector: str):
        """Click element inside iframe."""
        frame = self.get_frame_by_selector(frame_selector)
        frame.click(element_selector)
    
    def fill_in_frame(self, frame_selector: str, element_selector: str, value: str):
        """Fill input inside iframe."""
        frame = self.get_frame_by_selector(frame_selector)
        frame.fill(element_selector, value)
    
    def get_text_in_frame(self, frame_selector: str, element_selector: str) -> str:
        """Get text from element inside iframe."""
        frame = self.get_frame_by_selector(frame_selector)
        return frame.text_content(element_selector)
    
    def wait_for_frame(self, frame_selector: str, timeout: int = 30000):
        """Wait for iframe to load."""
        self.page.wait_for_selector(frame_selector, timeout=timeout)
        frame_element = self.page.locator(frame_selector)
        frame = frame_element.content_frame()
        frame.wait_for_load_state("domcontentloaded")
        return frame
    
    def nested_frame(self, *frame_selectors: str) -> Frame:
        """Access nested iframes."""
        current = self.page
        for selector in frame_selectors:
            frame_element = current.locator(selector)
            current = frame_element.content_frame()
        return current


def example_iframe():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Page with iframe
        page.goto("https://the-internet.herokuapp.com/iframe")
        
        helper = FrameHelper(page)
        
        # List all frames
        frames = helper.list_frames()
        print(f"Found {len(frames)} frames")
        
        # Interact with iframe content
        frame = helper.get_frame_by_selector("#mce_0_ifr")
        
        # Clear and type in rich text editor
        frame.click("#tinymce")
        frame.keyboard.press("Control+a")
        frame.keyboard.type("Hello from automation!")
        
        browser.close()


if __name__ == "__main__":
    example_iframe()
```

### Shadow DOM

```python
#!/usr/bin/env python3
"""Shadow DOM handling - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page, Locator


class ShadowDOMHelper:
    """Helper for Shadow DOM interactions."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def pierce_shadow(self, css_selector: str) -> Locator:
        """
        Select element piercing through shadow DOM.
        Playwright's default selectors pierce shadow DOM automatically.
        """
        return self.page.locator(css_selector)
    
    def get_shadow_root(self, host_selector: str):
        """Get shadow root of element."""
        return self.page.evaluate(f"""
            document.querySelector('{host_selector}').shadowRoot
        """)
    
    def query_shadow(self, host_selector: str, inner_selector: str) -> Locator:
        """Query element inside shadow DOM."""
        # Playwright pierces shadow DOM by default
        return self.page.locator(f"{host_selector} >> {inner_selector}")
    
    def click_in_shadow(self, host_selector: str, inner_selector: str):
        """Click element inside shadow DOM."""
        self.page.locator(f"{host_selector} >> {inner_selector}").click()
    
    def fill_in_shadow(self, host_selector: str, inner_selector: str, value: str):
        """Fill input inside shadow DOM."""
        self.page.locator(f"{host_selector} >> {inner_selector}").fill(value)
    
    def get_shadow_text(self, host_selector: str, inner_selector: str) -> str:
        """Get text from element inside shadow DOM."""
        return self.page.locator(f"{host_selector} >> {inner_selector}").text_content()
    
    def deep_shadow_query(self, *selectors: str) -> Locator:
        """Query through multiple shadow boundaries."""
        selector_chain = " >> ".join(selectors)
        return self.page.locator(selector_chain)


def example_shadow_dom():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Create test page with shadow DOM
        page.set_content("""
            <div id="host"></div>
            <script>
                const host = document.getElementById('host');
                const shadow = host.attachShadow({mode: 'open'});
                shadow.innerHTML = `
                    <style>
                        button { padding: 10px; background: blue; color: white; }
                    </style>
                    <button id="shadow-button">Click me</button>
                    <input id="shadow-input" type="text" placeholder="Shadow input">
                `;
            </script>
        """)
        
        helper = ShadowDOMHelper(page)
        
        # Interact with shadow DOM elements
        helper.click_in_shadow("#host", "#shadow-button")
        helper.fill_in_shadow("#host", "#shadow-input", "Hello Shadow DOM!")
        
        page.screenshot(path="shadow_dom.png")
        browser.close()


if __name__ == "__main__":
    example_shadow_dom()
```

---

## Recording and Debugging

### Trace Recording

```python
#!/usr/bin/env python3
"""Trace recording for debugging - run with: uv run script.py"""

from playwright.sync_api import sync_playwright
from pathlib import Path
from datetime import datetime


def run_with_trace(task, trace_name: str = None):
    """Run automation with trace recording."""
    trace_dir = Path("./traces")
    trace_dir.mkdir(exist_ok=True)
    
    trace_name = trace_name or f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    trace_path = trace_dir / f"{trace_name}.zip"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Start tracing
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )
        
        page = context.new_page()
        
        try:
            # Run the automation task
            result = task(page)
            
            # Stop tracing and save
            context.tracing.stop(path=str(trace_path))
            
            print(f"Trace saved: {trace_path}")
            print(f"View with: npx playwright show-trace {trace_path}")
            
            return result
        except Exception as e:
            # Save trace on failure for debugging
            context.tracing.stop(path=str(trace_path))
            print(f"Error trace saved: {trace_path}")
            raise
        finally:
            browser.close()


def example_task(page):
    """Example task to trace."""
    page.goto("https://example.com")
    page.click("a")
    return page.title()


if __name__ == "__main__":
    result = run_with_trace(example_task, "example_trace")
    print(f"Result: {result}")
```

### Video Recording

```python
#!/usr/bin/env python3
"""Video recording - run with: uv run script.py"""

from playwright.sync_api import sync_playwright
from pathlib import Path


def run_with_video(task, video_dir: str = "./videos"):
    """Run automation with video recording."""
    Path(video_dir).mkdir(exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Create context with video recording
        context = browser.new_context(
            record_video_dir=video_dir,
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = context.new_page()
        
        try:
            result = task(page)
            return result
        finally:
            # Must close context to save video
            context.close()
            
            # Get video path
            video_path = page.video.path()
            print(f"Video saved: {video_path}")
            
            browser.close()


def example_task(page):
    page.goto("https://example.com")
    page.wait_for_timeout(2000)
    return page.title()


if __name__ == "__main__":
    run_with_video(example_task)
```

---

## Best Practices

1. **Always close contexts and browsers** - Use context managers
2. **Prefer auto-waiting** - Don't add unnecessary explicit waits
3. **Use unique selectors** - data-testid > role > CSS > XPath
4. **Handle errors gracefully** - Implement retry mechanisms
5. **Record traces for debugging** - Especially for CI/CD failures
6. **Use stealth mode** - When automation detection is a concern
7. **Pool contexts** - Reuse for high-throughput scenarios

---

**Next Module:** See **rpa-data-extraction.md** for scraping and parsing patterns.
