# RPA Form Automation Module

Complete form automation patterns including text inputs, dropdowns, checkboxes, file uploads, date pickers, rich text editors, and CAPTCHA handling.

## Form Element Handling

### Text Inputs

```python
#!/usr/bin/env python3
"""Text input automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Optional
import time


class TextInputHandler:
    """Handle various text input types."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def fill_text(self, selector: str, value: str, clear_first: bool = True):
        """Fill text input."""
        if clear_first:
            self.page.fill(selector, "")
        self.page.fill(selector, value)
    
    def type_slowly(self, selector: str, value: str, delay_ms: int = 50):
        """Type with delay between keystrokes (more human-like)."""
        self.page.click(selector)
        self.page.keyboard.type(value, delay=delay_ms)
    
    def fill_with_validation(self, selector: str, value: str) -> bool:
        """Fill and verify value was entered."""
        self.page.fill(selector, value)
        actual = self.page.input_value(selector)
        return actual == value
    
    def clear_input(self, selector: str):
        """Clear input field."""
        self.page.fill(selector, "")
    
    def fill_masked_input(self, selector: str, value: str):
        """Handle masked inputs (phone, SSN, etc.)."""
        self.page.click(selector)
        
        # Type each character, allowing mask to process
        for char in value:
            self.page.keyboard.type(char)
            time.sleep(0.05)
    
    def fill_autocomplete(self, selector: str, value: str, suggestion_selector: str):
        """Handle autocomplete inputs."""
        self.page.fill(selector, value)
        self.page.wait_for_selector(suggestion_selector, state="visible")
        self.page.click(f"{suggestion_selector}:first-child")
    
    def fill_number_input(self, selector: str, value: float):
        """Fill number input with validation."""
        self.page.fill(selector, str(value))
    
    def fill_search_and_select(
        self,
        input_selector: str,
        search_term: str,
        results_selector: str,
        result_text: str
    ):
        """Search and select from results."""
        self.page.fill(input_selector, search_term)
        self.page.wait_for_selector(results_selector, state="visible")
        self.page.click(f"{results_selector}:has-text('{result_text}')")


def example_text_inputs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://the-internet.herokuapp.com/login")
        
        handler = TextInputHandler(page)
        
        handler.fill_text("#username", "tomsmith")
        handler.fill_text("#password", "SuperSecretPassword!")
        
        page.click("button[type=submit]")
        
        browser.close()


if __name__ == "__main__":
    example_text_inputs()
```

### Dropdown/Select Handling

```python
#!/usr/bin/env python3
"""Dropdown and select automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Optional, Union


class SelectHandler:
    """Handle dropdown and select elements."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def select_by_value(self, selector: str, value: str):
        """Select option by value attribute."""
        self.page.select_option(selector, value=value)
    
    def select_by_label(self, selector: str, label: str):
        """Select option by visible text."""
        self.page.select_option(selector, label=label)
    
    def select_by_index(self, selector: str, index: int):
        """Select option by index."""
        self.page.select_option(selector, index=index)
    
    def select_multiple(self, selector: str, values: list[str]):
        """Select multiple options (for multi-select)."""
        self.page.select_option(selector, value=values)
    
    def get_selected_value(self, selector: str) -> str:
        """Get currently selected value."""
        return self.page.input_value(selector)
    
    def get_all_options(self, selector: str) -> list[dict]:
        """Get all available options."""
        return self.page.evaluate(f"""
            () => {{
                const select = document.querySelector('{selector}');
                return Array.from(select.options).map(opt => ({{
                    value: opt.value,
                    text: opt.text,
                    selected: opt.selected
                }}));
            }}
        """)
    
    def select_custom_dropdown(
        self,
        trigger_selector: str,
        option_selector: str,
        option_text: str
    ):
        """Handle custom (non-native) dropdowns."""
        # Click to open dropdown
        self.page.click(trigger_selector)
        
        # Wait for options to appear
        self.page.wait_for_selector(option_selector, state="visible")
        
        # Click the desired option
        self.page.click(f"{option_selector}:has-text('{option_text}')")
    
    def select_searchable_dropdown(
        self,
        trigger_selector: str,
        search_input_selector: str,
        search_term: str,
        option_selector: str
    ):
        """Handle searchable dropdowns (Select2, Chosen, etc.)."""
        # Open dropdown
        self.page.click(trigger_selector)
        
        # Type in search
        self.page.fill(search_input_selector, search_term)
        
        # Wait and click result
        self.page.wait_for_selector(option_selector, state="visible")
        self.page.click(option_selector)
    
    def select_cascading(
        self,
        first_selector: str,
        first_value: str,
        second_selector: str,
        second_value: str
    ):
        """Handle cascading/dependent dropdowns."""
        # Select first dropdown
        self.page.select_option(first_selector, value=first_value)
        
        # Wait for second dropdown to update
        self.page.wait_for_function(f"""
            () => document.querySelector('{second_selector}').options.length > 1
        """)
        
        # Select second dropdown
        self.page.select_option(second_selector, value=second_value)


def example_dropdowns():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://the-internet.herokuapp.com/dropdown")
        
        handler = SelectHandler(page)
        
        # Native select
        handler.select_by_value("#dropdown", "1")
        
        # Get selected value
        selected = handler.get_selected_value("#dropdown")
        print(f"Selected: {selected}")
        
        # Get all options
        options = handler.get_all_options("#dropdown")
        print(f"Options: {options}")
        
        browser.close()


if __name__ == "__main__":
    example_dropdowns()
```

### Checkboxes and Radio Buttons

```python
#!/usr/bin/env python3
"""Checkbox and radio automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Optional


class CheckboxRadioHandler:
    """Handle checkboxes and radio buttons."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def check(self, selector: str):
        """Check a checkbox (idempotent)."""
        self.page.check(selector)
    
    def uncheck(self, selector: str):
        """Uncheck a checkbox (idempotent)."""
        self.page.uncheck(selector)
    
    def set_checked(self, selector: str, checked: bool):
        """Set checkbox to specific state."""
        if checked:
            self.page.check(selector)
        else:
            self.page.uncheck(selector)
    
    def toggle(self, selector: str):
        """Toggle checkbox state."""
        self.page.click(selector)
    
    def is_checked(self, selector: str) -> bool:
        """Check if checkbox is checked."""
        return self.page.is_checked(selector)
    
    def check_multiple(self, selectors: list[str]):
        """Check multiple checkboxes."""
        for selector in selectors:
            self.page.check(selector)
    
    def check_by_value(self, name: str, value: str):
        """Check checkbox by name and value."""
        self.page.check(f"input[name='{name}'][value='{value}']")
    
    def select_radio(self, selector: str):
        """Select radio button."""
        self.page.check(selector)
    
    def select_radio_by_value(self, name: str, value: str):
        """Select radio button by name and value."""
        self.page.check(f"input[name='{name}'][value='{value}']")
    
    def get_checked_radio(self, name: str) -> Optional[str]:
        """Get value of checked radio in group."""
        radio = self.page.locator(f"input[name='{name}']:checked")
        if radio.count() > 0:
            return radio.get_attribute("value")
        return None
    
    def get_all_checkboxes(self, container: str = "body") -> list[dict]:
        """Get all checkboxes in container with their states."""
        return self.page.evaluate(f"""
            () => {{
                const container = document.querySelector('{container}');
                return Array.from(container.querySelectorAll('input[type=checkbox]')).map(cb => ({{
                    name: cb.name,
                    value: cb.value,
                    checked: cb.checked,
                    id: cb.id,
                    label: cb.labels?.[0]?.textContent?.trim() || ''
                }}));
            }}
        """)


def example_checkboxes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://the-internet.herokuapp.com/checkboxes")
        
        handler = CheckboxRadioHandler(page)
        
        # Check both checkboxes
        handler.check("input[type=checkbox]:nth-child(1)")
        handler.check("input[type=checkbox]:nth-child(3)")
        
        # Get states
        checkboxes = handler.get_all_checkboxes()
        print(f"Checkboxes: {checkboxes}")
        
        browser.close()


if __name__ == "__main__":
    example_checkboxes()
```

---

## Date and Time Pickers

### Date Picker Automation

```python
#!/usr/bin/env python3
"""Date picker automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from datetime import datetime, date
from typing import Optional


class DatePickerHandler:
    """Handle various date picker implementations."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def fill_native_date(self, selector: str, date_value: date):
        """Fill native HTML5 date input."""
        formatted = date_value.strftime("%Y-%m-%d")
        self.page.fill(selector, formatted)
    
    def fill_native_datetime(self, selector: str, datetime_value: datetime):
        """Fill native HTML5 datetime-local input."""
        formatted = datetime_value.strftime("%Y-%m-%dT%H:%M")
        self.page.fill(selector, formatted)
    
    def fill_native_time(self, selector: str, time_str: str):
        """Fill native HTML5 time input."""
        self.page.fill(selector, time_str)
    
    def fill_text_date(self, selector: str, date_value: date, format: str = "%m/%d/%Y"):
        """Fill text input with formatted date."""
        formatted = date_value.strftime(format)
        self.page.fill(selector, formatted)
    
    def select_calendar_date(
        self,
        input_selector: str,
        calendar_selector: str,
        target_date: date
    ):
        """Select date from popup calendar."""
        # Open calendar
        self.page.click(input_selector)
        self.page.wait_for_selector(calendar_selector, state="visible")
        
        # Navigate to correct month/year
        self._navigate_to_month(calendar_selector, target_date)
        
        # Click the day
        day = target_date.day
        self.page.click(f"{calendar_selector} [data-day='{day}']")
    
    def _navigate_to_month(self, calendar_selector: str, target_date: date):
        """Navigate calendar to target month."""
        max_iterations = 24  # 2 years max
        
        for _ in range(max_iterations):
            # Get current displayed month/year
            displayed = self.page.locator(f"{calendar_selector} .month-year").text_content()
            current_date = datetime.strptime(displayed, "%B %Y")
            
            if current_date.month == target_date.month and current_date.year == target_date.year:
                break
            
            # Click next or previous
            if current_date < datetime(target_date.year, target_date.month, 1):
                self.page.click(f"{calendar_selector} .next-month")
            else:
                self.page.click(f"{calendar_selector} .prev-month")
            
            self.page.wait_for_timeout(200)
    
    def select_datepicker_ui(
        self,
        input_selector: str,
        target_date: date,
        year_selector: str = ".ui-datepicker-year",
        month_selector: str = ".ui-datepicker-month",
        day_selector: str = "td a.ui-state-default"
    ):
        """Handle jQuery UI datepicker."""
        # Open datepicker
        self.page.click(input_selector)
        
        # Select year if dropdown exists
        year_dropdown = self.page.locator(year_selector)
        if year_dropdown.count() > 0:
            self.page.select_option(year_selector, str(target_date.year))
        
        # Select month if dropdown exists
        month_dropdown = self.page.locator(month_selector)
        if month_dropdown.count() > 0:
            self.page.select_option(month_selector, str(target_date.month - 1))
        
        # Click the day
        self.page.click(f"{day_selector}:has-text('{target_date.day}')")
    
    def select_date_range(
        self,
        start_selector: str,
        end_selector: str,
        start_date: date,
        end_date: date
    ):
        """Select date range."""
        self.fill_native_date(start_selector, start_date)
        self.fill_native_date(end_selector, end_date)
    
    def select_flatpickr(self, input_selector: str, target_date: date):
        """Handle Flatpickr date picker."""
        # Open picker
        self.page.click(input_selector)
        
        # Navigate months if needed
        current_month = self.page.locator(".flatpickr-current-month .cur-month").text_content()
        current_year = self.page.locator(".flatpickr-current-month .cur-year").input_value()
        
        target_month_name = target_date.strftime("%B")
        
        while current_month != target_month_name or int(current_year) != target_date.year:
            if datetime.strptime(f"{current_month} {current_year}", "%B %Y") < datetime(target_date.year, target_date.month, 1):
                self.page.click(".flatpickr-next-month")
            else:
                self.page.click(".flatpickr-prev-month")
            
            current_month = self.page.locator(".flatpickr-current-month .cur-month").text_content()
            current_year = self.page.locator(".flatpickr-current-month .cur-year").input_value()
        
        # Click day
        self.page.click(f".flatpickr-day:not(.prevMonthDay):not(.nextMonthDay):has-text('{target_date.day}')")


def example_date_picker():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Test native date input
        page.set_content("""
            <input type="date" id="date-input">
            <input type="datetime-local" id="datetime-input">
        """)
        
        handler = DatePickerHandler(page)
        
        handler.fill_native_date("#date-input", date(2024, 12, 25))
        handler.fill_native_datetime("#datetime-input", datetime(2024, 12, 25, 14, 30))
        
        page.screenshot(path="date_input.png")
        browser.close()


if __name__ == "__main__":
    example_date_picker()
```

---

## File Upload

### File Upload Automation

```python
#!/usr/bin/env python3
"""File upload automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from pathlib import Path
from typing import Union
import base64


class FileUploadHandler:
    """Handle various file upload scenarios."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def upload_single_file(self, selector: str, file_path: Union[str, Path]):
        """Upload single file to input."""
        self.page.set_input_files(selector, str(file_path))
    
    def upload_multiple_files(self, selector: str, file_paths: list[Union[str, Path]]):
        """Upload multiple files."""
        paths = [str(p) for p in file_paths]
        self.page.set_input_files(selector, paths)
    
    def upload_via_drag_drop(self, drop_zone_selector: str, file_path: Union[str, Path]):
        """Simulate drag and drop file upload."""
        path = Path(file_path)
        
        # Read file and create DataTransfer
        with open(path, "rb") as f:
            content = f.read()
        
        # Create file in browser and dispatch drop event
        self.page.evaluate(f"""
            async (path, content) => {{
                const dataTransfer = new DataTransfer();
                const blob = new Blob([new Uint8Array(content)]);
                const file = new File([blob], '{path.name}', {{ type: 'application/octet-stream' }});
                dataTransfer.items.add(file);
                
                const dropZone = document.querySelector('{drop_zone_selector}');
                const dropEvent = new DragEvent('drop', {{
                    dataTransfer: dataTransfer,
                    bubbles: true
                }});
                dropZone.dispatchEvent(dropEvent);
            }}
        """, [str(path), list(content)])
    
    def upload_with_dialog(self, trigger_selector: str, file_path: Union[str, Path]):
        """Handle file dialog triggered by button click."""
        with self.page.expect_file_chooser() as fc_info:
            self.page.click(trigger_selector)
        
        file_chooser = fc_info.value
        file_chooser.set_files(str(file_path))
    
    def clear_file_input(self, selector: str):
        """Clear file input."""
        self.page.set_input_files(selector, [])
    
    def upload_from_buffer(self, selector: str, filename: str, content: bytes, mime_type: str = "application/octet-stream"):
        """Upload from memory buffer."""
        self.page.set_input_files(selector, [{
            "name": filename,
            "mimeType": mime_type,
            "buffer": content
        }])
    
    def upload_from_base64(self, selector: str, filename: str, base64_content: str, mime_type: str = "application/octet-stream"):
        """Upload from base64 encoded content."""
        content = base64.b64decode(base64_content)
        self.upload_from_buffer(selector, filename, content, mime_type)
    
    def wait_for_upload_complete(self, progress_selector: str = None, timeout: int = 60000):
        """Wait for upload to complete."""
        if progress_selector:
            # Wait for progress bar to reach 100% or disappear
            self.page.wait_for_function(f"""
                () => {{
                    const progress = document.querySelector('{progress_selector}');
                    return !progress || progress.value === 100 || progress.value === '100%';
                }}
            """, timeout=timeout)
        else:
            # Wait for network idle
            self.page.wait_for_load_state("networkidle", timeout=timeout)
    
    def get_uploaded_filename(self, selector: str) -> str:
        """Get filename from file input."""
        return self.page.evaluate(f"""
            () => {{
                const input = document.querySelector('{selector}');
                return input.files?.[0]?.name || '';
            }}
        """)


def example_file_upload():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://the-internet.herokuapp.com/upload")
        
        handler = FileUploadHandler(page)
        
        # Create test file
        test_file = Path("test_upload.txt")
        test_file.write_text("Hello, upload test!")
        
        try:
            # Upload file
            handler.upload_single_file("#file-upload", test_file)
            
            # Submit
            page.click("#file-submit")
            
            # Verify
            page.wait_for_selector("#uploaded-files")
            print(f"Uploaded: {page.text_content('#uploaded-files')}")
        finally:
            test_file.unlink()
        
        browser.close()


if __name__ == "__main__":
    example_file_upload()
```

---

## Rich Text Editors

### WYSIWYG Editor Automation

```python
#!/usr/bin/env python3
"""Rich text editor automation - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page


class RichTextHandler:
    """Handle WYSIWYG editors (TinyMCE, CKEditor, Quill, etc.)."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def fill_tinymce(self, editor_id: str, content: str, html: bool = False):
        """Fill TinyMCE editor."""
        if html:
            self.page.evaluate(f"""
                () => tinymce.get('{editor_id}').setContent(`{content}`)
            """)
        else:
            # Clear and type
            self.page.evaluate(f"""
                () => tinymce.get('{editor_id}').setContent('')
            """)
            
            # Focus and type
            frame = self.page.frame_locator(f"#{editor_id}_ifr")
            frame.locator("body").click()
            self.page.keyboard.type(content)
    
    def fill_tinymce_iframe(self, iframe_selector: str, content: str):
        """Fill TinyMCE via iframe."""
        frame = self.page.frame_locator(iframe_selector)
        body = frame.locator("body")
        body.click()
        self.page.keyboard.press("Control+a")
        self.page.keyboard.type(content)
    
    def fill_ckeditor(self, editor_name: str, content: str, html: bool = False):
        """Fill CKEditor."""
        if html:
            self.page.evaluate(f"""
                () => CKEDITOR.instances['{editor_name}'].setData(`{content}`)
            """)
        else:
            self.page.evaluate(f"""
                () => CKEDITOR.instances['{editor_name}'].setData('')
            """)
            
            # Focus editable area
            self.page.click(f".cke_editable")
            self.page.keyboard.type(content)
    
    def fill_quill(self, container_selector: str, content: str, html: bool = False):
        """Fill Quill editor."""
        if html:
            self.page.evaluate(f"""
                () => {{
                    const editor = Quill.find(document.querySelector('{container_selector}'));
                    editor.root.innerHTML = `{content}`;
                }}
            """)
        else:
            editor = self.page.locator(f"{container_selector} .ql-editor")
            editor.click()
            self.page.keyboard.press("Control+a")
            self.page.keyboard.type(content)
    
    def fill_contenteditable(self, selector: str, content: str):
        """Fill contenteditable element."""
        self.page.click(selector)
        self.page.keyboard.press("Control+a")
        self.page.keyboard.type(content)
    
    def insert_html_contenteditable(self, selector: str, html: str):
        """Insert HTML into contenteditable."""
        self.page.evaluate(f"""
            () => {{
                const el = document.querySelector('{selector}');
                el.innerHTML = `{html}`;
            }}
        """)
    
    def apply_formatting(self, format_type: str):
        """Apply formatting to selected text."""
        shortcuts = {
            "bold": "Control+b",
            "italic": "Control+i",
            "underline": "Control+u",
            "strikethrough": "Control+Shift+s",
        }
        
        if format_type in shortcuts:
            self.page.keyboard.press(shortcuts[format_type])
    
    def get_editor_content(self, editor_type: str, identifier: str) -> str:
        """Get content from editor."""
        if editor_type == "tinymce":
            return self.page.evaluate(f"() => tinymce.get('{identifier}').getContent()")
        elif editor_type == "ckeditor":
            return self.page.evaluate(f"() => CKEDITOR.instances['{identifier}'].getData()")
        elif editor_type == "quill":
            return self.page.evaluate(f"""
                () => Quill.find(document.querySelector('{identifier}')).root.innerHTML
            """)
        elif editor_type == "contenteditable":
            return self.page.locator(identifier).inner_html()
        
        return ""


def example_rich_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://the-internet.herokuapp.com/tinymce")
        
        handler = RichTextHandler(page)
        
        # Fill TinyMCE
        handler.fill_tinymce_iframe("#mce_0_ifr", "Hello from automation!")
        
        page.screenshot(path="rich_text.png")
        browser.close()


if __name__ == "__main__":
    example_rich_text()
```

---

## CAPTCHA Handling

### CAPTCHA Strategies

```python
#!/usr/bin/env python3
"""CAPTCHA handling strategies - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from typing import Optional
import httpx
import time
import os


class CaptchaHandler:
    """Handle various CAPTCHA types."""
    
    def __init__(self, page: Page, solver_api_key: str = None):
        self.page = page
        self.solver_api_key = solver_api_key or os.getenv("CAPTCHA_API_KEY")
    
    def wait_for_manual_solve(self, captcha_selector: str, timeout: int = 300):
        """Wait for user to manually solve CAPTCHA."""
        print(f"Please solve the CAPTCHA manually. Timeout: {timeout}s")
        
        # Wait for CAPTCHA to be solved (element disappears or form becomes submittable)
        start = time.time()
        while time.time() - start < timeout:
            if not self.page.locator(captcha_selector).is_visible():
                print("CAPTCHA solved!")
                return True
            time.sleep(1)
        
        raise TimeoutError("CAPTCHA was not solved in time")
    
    def solve_recaptcha_v2(self, site_key: str = None) -> Optional[str]:
        """Solve reCAPTCHA v2 using 2captcha API."""
        if not self.solver_api_key:
            raise ValueError("CAPTCHA solver API key required")
        
        # Get site key from page if not provided
        if not site_key:
            site_key = self.page.evaluate("""
                () => document.querySelector('.g-recaptcha')?.dataset?.sitekey
            """)
        
        if not site_key:
            raise ValueError("Could not find reCAPTCHA site key")
        
        page_url = self.page.url
        
        # Submit to 2captcha
        response = httpx.post(
            "http://2captcha.com/in.php",
            data={
                "key": self.solver_api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1
            }
        ).json()
        
        if response.get("status") != 1:
            raise Exception(f"2captcha error: {response.get('request')}")
        
        captcha_id = response["request"]
        
        # Poll for result
        for _ in range(60):
            time.sleep(5)
            
            result = httpx.get(
                f"http://2captcha.com/res.php",
                params={
                    "key": self.solver_api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
            ).json()
            
            if result.get("status") == 1:
                token = result["request"]
                
                # Inject token into page
                self.page.evaluate(f"""
                    () => {{
                        document.querySelector('#g-recaptcha-response').value = '{token}';
                        document.querySelector('[name=g-recaptcha-response]').value = '{token}';
                    }}
                """)
                
                return token
            
            if result.get("request") != "CAPCHA_NOT_READY":
                raise Exception(f"2captcha error: {result.get('request')}")
        
        raise TimeoutError("CAPTCHA solving timed out")
    
    def solve_hcaptcha(self, site_key: str = None) -> Optional[str]:
        """Solve hCaptcha using 2captcha API."""
        if not self.solver_api_key:
            raise ValueError("CAPTCHA solver API key required")
        
        if not site_key:
            site_key = self.page.evaluate("""
                () => document.querySelector('[data-sitekey]')?.dataset?.sitekey
            """)
        
        page_url = self.page.url
        
        response = httpx.post(
            "http://2captcha.com/in.php",
            data={
                "key": self.solver_api_key,
                "method": "hcaptcha",
                "sitekey": site_key,
                "pageurl": page_url,
                "json": 1
            }
        ).json()
        
        if response.get("status") != 1:
            raise Exception(f"2captcha error: {response.get('request')}")
        
        captcha_id = response["request"]
        
        for _ in range(60):
            time.sleep(5)
            
            result = httpx.get(
                f"http://2captcha.com/res.php",
                params={
                    "key": self.solver_api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
            ).json()
            
            if result.get("status") == 1:
                token = result["request"]
                
                self.page.evaluate(f"""
                    () => {{
                        document.querySelector('[name=h-captcha-response]').value = '{token}';
                        document.querySelector('[name=g-recaptcha-response]').value = '{token}';
                    }}
                """)
                
                return token
        
        raise TimeoutError("hCaptcha solving timed out")
    
    def solve_simple_image_captcha(self, image_selector: str, input_selector: str) -> str:
        """Solve simple image CAPTCHA using 2captcha."""
        if not self.solver_api_key:
            raise ValueError("CAPTCHA solver API key required")
        
        # Get captcha image as base64
        image_base64 = self.page.evaluate(f"""
            async () => {{
                const img = document.querySelector('{image_selector}');
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/png').split(',')[1];
            }}
        """)
        
        # Submit to 2captcha
        response = httpx.post(
            "http://2captcha.com/in.php",
            data={
                "key": self.solver_api_key,
                "method": "base64",
                "body": image_base64,
                "json": 1
            }
        ).json()
        
        captcha_id = response["request"]
        
        for _ in range(30):
            time.sleep(5)
            
            result = httpx.get(
                f"http://2captcha.com/res.php",
                params={
                    "key": self.solver_api_key,
                    "action": "get",
                    "id": captcha_id,
                    "json": 1
                }
            ).json()
            
            if result.get("status") == 1:
                captcha_text = result["request"]
                self.page.fill(input_selector, captcha_text)
                return captcha_text
        
        raise TimeoutError("Image CAPTCHA solving timed out")
    
    def bypass_with_cookies(self, cookies_file: str):
        """Bypass CAPTCHA by loading pre-authenticated cookies."""
        import json
        
        with open(cookies_file) as f:
            cookies = json.load(f)
        
        self.page.context.add_cookies(cookies)
    
    def check_for_captcha(self) -> Optional[str]:
        """Detect if CAPTCHA is present."""
        captcha_indicators = {
            "recaptcha": ".g-recaptcha, #recaptcha",
            "hcaptcha": ".h-captcha, [data-hcaptcha-sitekey]",
            "cloudflare": "#cf-turnstile, .cf-challenge",
            "simple": "img[src*='captcha'], #captcha-image",
        }
        
        for captcha_type, selector in captcha_indicators.items():
            if self.page.locator(selector).count() > 0:
                return captcha_type
        
        return None


def example_captcha():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to page with CAPTCHA
        page.goto("https://www.google.com/recaptcha/api2/demo")
        
        handler = CaptchaHandler(page)
        
        captcha_type = handler.check_for_captcha()
        print(f"Detected CAPTCHA type: {captcha_type}")
        
        # For demo, wait for manual solve
        if captcha_type:
            handler.wait_for_manual_solve(".g-recaptcha", timeout=120)
        
        browser.close()


if __name__ == "__main__":
    example_captcha()
```

---

## Complete Form Automation

### Form Automation Framework

```python
#!/usr/bin/env python3
"""Complete form automation framework - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from pydantic import BaseModel, Field
from typing import Any, Optional, Callable
from enum import Enum
from datetime import date, datetime
from pathlib import Path
import json


class FieldType(Enum):
    TEXT = "text"
    PASSWORD = "password"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    DATETIME = "datetime"
    FILE = "file"
    HIDDEN = "hidden"
    CUSTOM = "custom"


class FormField(BaseModel):
    """Form field definition."""
    name: str
    selector: str
    field_type: FieldType
    value: Any = None
    required: bool = False
    validation: Optional[str] = None
    custom_handler: Optional[str] = None  # Name of custom handler method


class FormDefinition(BaseModel):
    """Complete form definition."""
    name: str
    url: Optional[str] = None
    form_selector: str = "form"
    submit_selector: str = "button[type=submit]"
    success_indicator: Optional[str] = None
    fields: list[FormField] = Field(default_factory=list)


class FormAutomator:
    """Universal form automation."""
    
    def __init__(self, page: Page):
        self.page = page
        self.custom_handlers: dict[str, Callable] = {}
    
    def register_handler(self, name: str, handler: Callable):
        """Register custom field handler."""
        self.custom_handlers[name] = handler
    
    def fill_field(self, field: FormField):
        """Fill a single form field based on type."""
        if field.value is None:
            return
        
        selector = field.selector
        value = field.value
        
        match field.field_type:
            case FieldType.TEXT | FieldType.PASSWORD | FieldType.EMAIL | FieldType.PHONE | FieldType.NUMBER:
                self.page.fill(selector, str(value))
            
            case FieldType.TEXTAREA:
                self.page.fill(selector, str(value))
            
            case FieldType.SELECT:
                self.page.select_option(selector, value)
            
            case FieldType.CHECKBOX:
                if value:
                    self.page.check(selector)
                else:
                    self.page.uncheck(selector)
            
            case FieldType.RADIO:
                self.page.check(f"{selector}[value='{value}']")
            
            case FieldType.DATE:
                if isinstance(value, date):
                    value = value.strftime("%Y-%m-%d")
                self.page.fill(selector, value)
            
            case FieldType.DATETIME:
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%dT%H:%M")
                self.page.fill(selector, value)
            
            case FieldType.FILE:
                self.page.set_input_files(selector, value)
            
            case FieldType.HIDDEN:
                self.page.evaluate(f"""
                    document.querySelector('{selector}').value = '{value}'
                """)
            
            case FieldType.CUSTOM:
                if field.custom_handler and field.custom_handler in self.custom_handlers:
                    self.custom_handlers[field.custom_handler](self.page, selector, value)
    
    def fill_form(self, form_def: FormDefinition, data: dict[str, Any] = None):
        """Fill entire form from definition."""
        # Navigate if URL provided
        if form_def.url:
            self.page.goto(form_def.url)
        
        # Wait for form
        self.page.wait_for_selector(form_def.form_selector)
        
        # Fill each field
        for field in form_def.fields:
            # Override with provided data
            if data and field.name in data:
                field.value = data[field.name]
            
            try:
                self.fill_field(field)
            except Exception as e:
                if field.required:
                    raise
                print(f"Warning: Could not fill {field.name}: {e}")
    
    def submit_form(self, form_def: FormDefinition) -> bool:
        """Submit form and verify success."""
        self.page.click(form_def.submit_selector)
        
        if form_def.success_indicator:
            try:
                self.page.wait_for_selector(form_def.success_indicator, timeout=10000)
                return True
            except:
                return False
        else:
            self.page.wait_for_load_state("networkidle")
            return True
    
    def automate_form(self, form_def: FormDefinition, data: dict[str, Any] = None) -> bool:
        """Complete form automation: fill and submit."""
        self.fill_form(form_def, data)
        return self.submit_form(form_def)
    
    def validate_form(self, form_def: FormDefinition) -> list[str]:
        """Validate form fields have correct values."""
        errors = []
        
        for field in form_def.fields:
            if field.value is None:
                continue
            
            actual = None
            
            match field.field_type:
                case FieldType.TEXT | FieldType.PASSWORD | FieldType.EMAIL | FieldType.PHONE | FieldType.NUMBER | FieldType.DATE | FieldType.DATETIME | FieldType.TEXTAREA:
                    actual = self.page.input_value(field.selector)
                
                case FieldType.SELECT:
                    actual = self.page.input_value(field.selector)
                
                case FieldType.CHECKBOX:
                    actual = self.page.is_checked(field.selector)
            
            if actual is not None and str(actual) != str(field.value):
                errors.append(f"{field.name}: expected '{field.value}', got '{actual}'")
        
        return errors
    
    def save_form_definition(self, form_def: FormDefinition, filepath: str):
        """Save form definition to JSON."""
        with open(filepath, "w") as f:
            json.dump(form_def.model_dump(), f, indent=2, default=str)
    
    def load_form_definition(self, filepath: str) -> FormDefinition:
        """Load form definition from JSON."""
        with open(filepath) as f:
            data = json.load(f)
        return FormDefinition(**data)


def example_form_automation():
    # Define form
    registration_form = FormDefinition(
        name="User Registration",
        url="https://example.com/register",
        form_selector="form#registration",
        submit_selector="button[type=submit]",
        success_indicator=".success-message",
        fields=[
            FormField(name="first_name", selector="#firstName", field_type=FieldType.TEXT, required=True),
            FormField(name="last_name", selector="#lastName", field_type=FieldType.TEXT, required=True),
            FormField(name="email", selector="#email", field_type=FieldType.EMAIL, required=True),
            FormField(name="password", selector="#password", field_type=FieldType.PASSWORD, required=True),
            FormField(name="country", selector="#country", field_type=FieldType.SELECT),
            FormField(name="birthdate", selector="#birthdate", field_type=FieldType.DATE),
            FormField(name="agree_terms", selector="#agreeTerms", field_type=FieldType.CHECKBOX, required=True),
            FormField(name="newsletter", selector="#newsletter", field_type=FieldType.CHECKBOX),
        ]
    )
    
    # Form data
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "SecurePass123!",
        "country": "US",
        "birthdate": date(1990, 1, 15),
        "agree_terms": True,
        "newsletter": False,
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        automator = FormAutomator(page)
        success = automator.automate_form(registration_form, data)
        
        print(f"Form submitted: {success}")
        
        browser.close()


if __name__ == "__main__":
    example_form_automation()
```

---

## Best Practices

1. **Wait for elements** - Always ensure elements are visible before interaction
2. **Clear before fill** - Clear existing values before entering new ones
3. **Verify after fill** - Confirm values were entered correctly
4. **Handle dynamic forms** - Wait for dependent fields to update
5. **Save progress** - For long forms, save state periodically
6. **Screenshot on error** - Capture state for debugging
7. **Use data models** - Pydantic for validation and structure

---

**Next Module:** See **rpa-workflows.md** for multi-step orchestration.
