# RPA Desktop Automation Module

Windows desktop application automation using pyautogui, pywinauto, and native Windows APIs.

## PyAutoGUI - Cross-Platform Desktop Automation

### Basic Operations

```python
#!/usr/bin/env python3
"""PyAutoGUI desktop automation - run with: uv run script.py"""

import pyautogui
import time
from dataclasses import dataclass
from typing import Optional, Tuple
from pathlib import Path


# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Pause between actions


@dataclass
class ScreenPosition:
    """Screen position."""
    x: int
    y: int
    
    def as_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)


class DesktopAutomation:
    """Desktop automation using PyAutoGUI."""
    
    def __init__(self, screenshots_dir: str = "./screenshots"):
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
    
    # Mouse Operations
    def click(self, x: int, y: int, clicks: int = 1, button: str = "left"):
        """Click at coordinates."""
        pyautogui.click(x, y, clicks=clicks, button=button)
    
    def double_click(self, x: int, y: int):
        """Double-click at coordinates."""
        pyautogui.doubleClick(x, y)
    
    def right_click(self, x: int, y: int):
        """Right-click at coordinates."""
        pyautogui.rightClick(x, y)
    
    def move_to(self, x: int, y: int, duration: float = 0.5):
        """Move mouse to coordinates."""
        pyautogui.moveTo(x, y, duration=duration)
    
    def drag_to(self, x: int, y: int, duration: float = 0.5, button: str = "left"):
        """Drag to coordinates."""
        pyautogui.dragTo(x, y, duration=duration, button=button)
    
    def scroll(self, amount: int, x: int = None, y: int = None):
        """Scroll wheel."""
        pyautogui.scroll(amount, x, y)
    
    # Keyboard Operations
    def type_text(self, text: str, interval: float = 0.05):
        """Type text."""
        pyautogui.typewrite(text, interval=interval)
    
    def write(self, text: str):
        """Write text (supports unicode)."""
        pyautogui.write(text)
    
    def press(self, key: str):
        """Press key."""
        pyautogui.press(key)
    
    def hotkey(self, *keys: str):
        """Press hotkey combination."""
        pyautogui.hotkey(*keys)
    
    def key_down(self, key: str):
        """Hold key down."""
        pyautogui.keyDown(key)
    
    def key_up(self, key: str):
        """Release key."""
        pyautogui.keyUp(key)
    
    # Screen Operations
    def screenshot(self, name: str = None, region: Tuple[int, int, int, int] = None) -> Path:
        """Take screenshot."""
        name = name or f"screenshot_{int(time.time())}"
        path = self.screenshots_dir / f"{name}.png"
        
        if region:
            pyautogui.screenshot(str(path), region=region)
        else:
            pyautogui.screenshot(str(path))
        
        return path
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        return pyautogui.size()
    
    def get_mouse_position(self) -> ScreenPosition:
        """Get current mouse position."""
        pos = pyautogui.position()
        return ScreenPosition(pos.x, pos.y)
    
    # Image Recognition
    def find_on_screen(
        self,
        image_path: str,
        confidence: float = 0.9,
        grayscale: bool = True
    ) -> Optional[ScreenPosition]:
        """Find image on screen."""
        try:
            location = pyautogui.locateOnScreen(
                image_path,
                confidence=confidence,
                grayscale=grayscale
            )
            if location:
                center = pyautogui.center(location)
                return ScreenPosition(center.x, center.y)
        except pyautogui.ImageNotFoundException:
            pass
        return None
    
    def find_all_on_screen(
        self,
        image_path: str,
        confidence: float = 0.9
    ) -> list[ScreenPosition]:
        """Find all occurrences of image."""
        positions = []
        try:
            for location in pyautogui.locateAllOnScreen(image_path, confidence=confidence):
                center = pyautogui.center(location)
                positions.append(ScreenPosition(center.x, center.y))
        except pyautogui.ImageNotFoundException:
            pass
        return positions
    
    def wait_for_image(
        self,
        image_path: str,
        timeout: int = 30,
        confidence: float = 0.9
    ) -> Optional[ScreenPosition]:
        """Wait for image to appear."""
        start = time.time()
        while time.time() - start < timeout:
            pos = self.find_on_screen(image_path, confidence)
            if pos:
                return pos
            time.sleep(0.5)
        return None
    
    def click_image(
        self,
        image_path: str,
        confidence: float = 0.9,
        timeout: int = 10
    ) -> bool:
        """Find and click on image."""
        pos = self.wait_for_image(image_path, timeout, confidence)
        if pos:
            self.click(pos.x, pos.y)
            return True
        return False
    
    # Window Operations
    def get_active_window_title(self) -> str:
        """Get active window title."""
        return pyautogui.getActiveWindowTitle()
    
    def get_all_windows(self) -> list[str]:
        """Get all window titles."""
        return pyautogui.getAllTitles()
    
    # Alerts and Dialogs
    def alert(self, text: str, title: str = "Alert"):
        """Show alert dialog."""
        pyautogui.alert(text, title)
    
    def confirm(self, text: str, title: str = "Confirm") -> bool:
        """Show confirmation dialog."""
        result = pyautogui.confirm(text, title)
        return result == "OK"
    
    def prompt(self, text: str, title: str = "Input", default: str = "") -> Optional[str]:
        """Show input dialog."""
        return pyautogui.prompt(text, title, default)


def example_pyautogui():
    """Example PyAutoGUI usage."""
    automation = DesktopAutomation()
    
    # Get screen info
    width, height = automation.get_screen_size()
    print(f"Screen: {width}x{height}")
    
    # Take screenshot
    screenshot = automation.screenshot("desktop")
    print(f"Screenshot: {screenshot}")
    
    # Find and click button (if template exists)
    # automation.click_image("templates/button.png")
    
    # Type text
    # automation.hotkey("win", "r")  # Open Run dialog
    # time.sleep(0.5)
    # automation.type_text("notepad")
    # automation.press("enter")


if __name__ == "__main__":
    example_pyautogui()
```

---

## PyWinAuto - Windows Application Automation

### Application Control

```python
#!/usr/bin/env python3
"""PyWinAuto Windows automation - run with: uv run script.py"""

from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.keyboard import send_keys
from dataclasses import dataclass
from typing import Optional, Union
import time


@dataclass
class WindowInfo:
    """Window information."""
    title: str
    class_name: str
    handle: int
    rect: tuple
    visible: bool


class WindowsAutomation:
    """Windows desktop automation using PyWinAuto."""
    
    def __init__(self):
        self.desktop = Desktop(backend="uia")
        self.app: Optional[Application] = None
        self.main_window = None
    
    # Application Management
    def start_application(
        self,
        path: str,
        backend: str = "uia",
        timeout: int = 30
    ) -> bool:
        """Start application."""
        self.app = Application(backend=backend).start(path, timeout=timeout)
        return True
    
    def connect_to_application(
        self,
        title: str = None,
        process: int = None,
        path: str = None,
        backend: str = "uia"
    ) -> bool:
        """Connect to running application."""
        connect_args = {"backend": backend}
        
        if title:
            connect_args["title"] = title
        elif process:
            connect_args["process"] = process
        elif path:
            connect_args["path"] = path
        
        self.app = Application(**connect_args).connect(**{k: v for k, v in connect_args.items() if k != "backend"})
        return True
    
    def close_application(self):
        """Close application."""
        if self.app:
            self.app.kill()
    
    # Window Operations
    def get_window(self, title: str = None, class_name: str = None):
        """Get window by title or class."""
        if title:
            return self.app.window(title=title)
        elif class_name:
            return self.app.window(class_name=class_name)
        return self.app.top_window()
    
    def list_windows(self) -> list[WindowInfo]:
        """List all windows."""
        windows = []
        for win in self.desktop.windows():
            try:
                windows.append(WindowInfo(
                    title=win.window_text(),
                    class_name=win.class_name(),
                    handle=win.handle,
                    rect=win.rectangle().mid_point(),
                    visible=win.is_visible()
                ))
            except:
                pass
        return windows
    
    def focus_window(self, title: str):
        """Bring window to foreground."""
        window = self.get_window(title=title)
        window.set_focus()
    
    def minimize_window(self, title: str = None):
        """Minimize window."""
        window = self.get_window(title=title) if title else self.app.top_window()
        window.minimize()
    
    def maximize_window(self, title: str = None):
        """Maximize window."""
        window = self.get_window(title=title) if title else self.app.top_window()
        window.maximize()
    
    def restore_window(self, title: str = None):
        """Restore window."""
        window = self.get_window(title=title) if title else self.app.top_window()
        window.restore()
    
    # Control Operations
    def find_control(
        self,
        window_title: str = None,
        control_type: str = None,
        auto_id: str = None,
        name: str = None,
        class_name: str = None
    ):
        """Find control in window."""
        window = self.get_window(title=window_title) if window_title else self.app.top_window()
        
        criteria = {}
        if control_type:
            criteria["control_type"] = control_type
        if auto_id:
            criteria["auto_id"] = auto_id
        if name:
            criteria["title"] = name
        if class_name:
            criteria["class_name"] = class_name
        
        return window.child_window(**criteria)
    
    def click_control(
        self,
        window_title: str = None,
        auto_id: str = None,
        name: str = None
    ):
        """Click on control."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            name=name
        )
        control.click()
    
    def set_text(
        self,
        text: str,
        window_title: str = None,
        auto_id: str = None,
        name: str = None
    ):
        """Set text in control."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            name=name
        )
        control.set_text(text)
    
    def get_text(
        self,
        window_title: str = None,
        auto_id: str = None,
        name: str = None
    ) -> str:
        """Get text from control."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            name=name
        )
        return control.texts()[0] if control.texts() else ""
    
    def select_menu(self, *menu_path: str):
        """Select menu item."""
        window = self.app.top_window()
        window.menu_select("->".join(menu_path))
    
    def select_listbox_item(
        self,
        item: str,
        window_title: str = None,
        auto_id: str = None
    ):
        """Select item in listbox."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            control_type="List"
        )
        control.select(item)
    
    def check_checkbox(
        self,
        window_title: str = None,
        auto_id: str = None,
        name: str = None,
        check: bool = True
    ):
        """Check or uncheck checkbox."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            name=name,
            control_type="CheckBox"
        )
        if check:
            control.check()
        else:
            control.uncheck()
    
    def select_radio(
        self,
        window_title: str = None,
        auto_id: str = None,
        name: str = None
    ):
        """Select radio button."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            name=name,
            control_type="RadioButton"
        )
        control.select()
    
    def select_combobox(
        self,
        item: str,
        window_title: str = None,
        auto_id: str = None
    ):
        """Select item in combobox."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            control_type="ComboBox"
        )
        control.select(item)
    
    def get_table_data(
        self,
        window_title: str = None,
        auto_id: str = None
    ) -> list[list[str]]:
        """Get data from table/grid."""
        control = self.find_control(
            window_title=window_title,
            auto_id=auto_id,
            control_type="DataGrid"
        )
        
        data = []
        for row in control.children():
            row_data = []
            for cell in row.children():
                row_data.append(cell.texts()[0] if cell.texts() else "")
            data.append(row_data)
        
        return data
    
    # Keyboard Operations
    def send_keys(self, keys: str):
        """Send keys to active window."""
        send_keys(keys)
    
    def type_text(self, text: str):
        """Type text."""
        send_keys(text, with_spaces=True)
    
    # Wait Operations
    def wait_for_window(self, title: str, timeout: int = 30) -> bool:
        """Wait for window to appear."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                window = self.desktop.window(title=title)
                if window.exists():
                    return True
            except ElementNotFoundError:
                pass
            time.sleep(0.5)
        return False
    
    def wait_for_control(
        self,
        window_title: str,
        auto_id: str = None,
        name: str = None,
        timeout: int = 30
    ) -> bool:
        """Wait for control to appear."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                control = self.find_control(
                    window_title=window_title,
                    auto_id=auto_id,
                    name=name
                )
                if control.exists():
                    return True
            except ElementNotFoundError:
                pass
            time.sleep(0.5)
        return False
    
    # Debug/Inspect
    def print_control_identifiers(self, window_title: str = None):
        """Print all control identifiers (for debugging)."""
        window = self.get_window(title=window_title) if window_title else self.app.top_window()
        window.print_control_identifiers()


def example_notepad():
    """Example: Automate Notepad."""
    automation = WindowsAutomation()
    
    # Start Notepad
    automation.start_application("notepad.exe")
    time.sleep(1)
    
    # Wait for window
    automation.wait_for_window("Untitled - Notepad")
    
    # Type text
    automation.type_text("Hello from RPA automation!")
    
    # Save file
    automation.send_keys("^s")  # Ctrl+S
    time.sleep(1)
    
    automation.wait_for_window("Save As")
    automation.type_text("test_file.txt")
    automation.send_keys("{ENTER}")
    
    time.sleep(1)
    automation.close_application()


if __name__ == "__main__":
    example_notepad()
```

---

## Windows UI Automation (UIA)

```python
#!/usr/bin/env python3
"""Windows UI Automation - run with: uv run script.py"""

from pywinauto.uia_defines import IUIA
from pywinauto import Desktop
from pywinauto.controls.uia_controls import UIAWrapper
from dataclasses import dataclass
from typing import Optional, List
import time


@dataclass
class UIElement:
    """UI element information."""
    name: str
    control_type: str
    automation_id: str
    class_name: str
    is_enabled: bool
    is_visible: bool
    rect: tuple


class UIAutomation:
    """Windows UI Automation wrapper."""
    
    def __init__(self):
        self.desktop = Desktop(backend="uia")
    
    def get_focused_element(self) -> Optional[UIElement]:
        """Get currently focused element."""
        try:
            element = self.desktop.get_focus()
            return self._element_to_info(element)
        except:
            return None
    
    def get_element_at(self, x: int, y: int) -> Optional[UIElement]:
        """Get element at coordinates."""
        try:
            element = self.desktop.from_point(x, y)
            return self._element_to_info(element)
        except:
            return None
    
    def find_elements(
        self,
        control_type: str = None,
        name: str = None,
        automation_id: str = None,
        parent_window: str = None
    ) -> List[UIElement]:
        """Find UI elements."""
        if parent_window:
            parent = self.desktop.window(title=parent_window)
        else:
            parent = self.desktop
        
        criteria = {}
        if control_type:
            criteria["control_type"] = control_type
        if name:
            criteria["title"] = name
        if automation_id:
            criteria["auto_id"] = automation_id
        
        elements = []
        try:
            for child in parent.descendants(**criteria):
                elements.append(self._element_to_info(child))
        except:
            pass
        
        return elements
    
    def _element_to_info(self, element) -> UIElement:
        """Convert element to info dataclass."""
        rect = element.rectangle()
        return UIElement(
            name=element.window_text(),
            control_type=element.element_info.control_type,
            automation_id=element.element_info.automation_id,
            class_name=element.element_info.class_name,
            is_enabled=element.is_enabled(),
            is_visible=element.is_visible(),
            rect=(rect.left, rect.top, rect.right, rect.bottom)
        )
    
    def invoke_element(self, automation_id: str, parent_window: str = None):
        """Invoke (click) element."""
        if parent_window:
            parent = self.desktop.window(title=parent_window)
        else:
            parent = self.desktop
        
        element = parent.child_window(auto_id=automation_id)
        element.invoke()
    
    def expand_element(self, automation_id: str, parent_window: str = None):
        """Expand collapsible element."""
        if parent_window:
            parent = self.desktop.window(title=parent_window)
        else:
            parent = self.desktop
        
        element = parent.child_window(auto_id=automation_id)
        element.expand()
    
    def collapse_element(self, automation_id: str, parent_window: str = None):
        """Collapse element."""
        if parent_window:
            parent = self.desktop.window(title=parent_window)
        else:
            parent = self.desktop
        
        element = parent.child_window(auto_id=automation_id)
        element.collapse()
    
    def scroll_element(
        self,
        automation_id: str,
        direction: str = "down",
        amount: int = 1,
        parent_window: str = None
    ):
        """Scroll element."""
        if parent_window:
            parent = self.desktop.window(title=parent_window)
        else:
            parent = self.desktop
        
        element = parent.child_window(auto_id=automation_id)
        
        if direction == "down":
            element.scroll("down", "page", amount)
        elif direction == "up":
            element.scroll("up", "page", amount)


def inspect_ui():
    """Inspect UI elements under mouse."""
    automation = UIAutomation()
    
    print("Move mouse to inspect elements. Ctrl+C to stop.")
    
    import pyautogui
    
    try:
        while True:
            x, y = pyautogui.position()
            element = automation.get_element_at(x, y)
            
            if element:
                print(f"\rElement: {element.name[:30]:30} | Type: {element.control_type:20} | ID: {element.automation_id[:20]:20}", end="")
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nDone")


if __name__ == "__main__":
    inspect_ui()
```

---

## File Dialog Automation

```python
#!/usr/bin/env python3
"""File dialog automation - run with: uv run script.py"""

from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from pathlib import Path
import time


class FileDialogAutomation:
    """Automate file dialogs."""
    
    def __init__(self):
        self.desktop = Desktop(backend="uia")
    
    def handle_open_dialog(
        self,
        file_path: str,
        dialog_title: str = "Open",
        timeout: int = 10
    ) -> bool:
        """Handle Open file dialog."""
        try:
            dialog = self.desktop.window(title=dialog_title, timeout=timeout)
            
            # Enter file path
            edit = dialog.child_window(control_type="Edit", found_index=0)
            edit.set_text(str(file_path))
            
            # Click Open button
            open_button = dialog.child_window(title="Open", control_type="Button")
            open_button.click()
            
            return True
        except Exception as e:
            print(f"Error handling Open dialog: {e}")
            return False
    
    def handle_save_dialog(
        self,
        file_path: str,
        dialog_title: str = "Save As",
        timeout: int = 10
    ) -> bool:
        """Handle Save As dialog."""
        try:
            dialog = self.desktop.window(title=dialog_title, timeout=timeout)
            
            # Enter file path
            edit = dialog.child_window(control_type="Edit", found_index=0)
            edit.set_text(str(file_path))
            
            # Click Save button
            save_button = dialog.child_window(title="Save", control_type="Button")
            save_button.click()
            
            # Handle overwrite confirmation if exists
            time.sleep(0.5)
            try:
                confirm = self.desktop.window(title="Confirm Save As", timeout=2)
                yes_button = confirm.child_window(title="Yes", control_type="Button")
                yes_button.click()
            except:
                pass
            
            return True
        except Exception as e:
            print(f"Error handling Save dialog: {e}")
            return False
    
    def handle_folder_dialog(
        self,
        folder_path: str,
        dialog_title: str = "Select Folder",
        timeout: int = 10
    ) -> bool:
        """Handle folder selection dialog."""
        try:
            dialog = self.desktop.window(title_re=".*Select.*Folder.*", timeout=timeout)
            
            # Enter folder path
            send_keys(str(folder_path))
            time.sleep(0.3)
            send_keys("{ENTER}")
            
            # Click Select Folder button
            try:
                select_button = dialog.child_window(title="Select Folder", control_type="Button")
                select_button.click()
            except:
                send_keys("{ENTER}")
            
            return True
        except Exception as e:
            print(f"Error handling folder dialog: {e}")
            return False
    
    def handle_print_dialog(
        self,
        printer_name: str = None,
        copies: int = 1
    ) -> bool:
        """Handle print dialog."""
        try:
            dialog = self.desktop.window(title="Print", timeout=10)
            
            # Select printer if specified
            if printer_name:
                printer_combo = dialog.child_window(control_type="ComboBox", found_index=0)
                printer_combo.select(printer_name)
            
            # Set copies
            if copies > 1:
                copies_edit = dialog.child_window(auto_id="1154")
                copies_edit.set_text(str(copies))
            
            # Click Print
            print_button = dialog.child_window(title="Print", control_type="Button")
            print_button.click()
            
            return True
        except Exception as e:
            print(f"Error handling print dialog: {e}")
            return False


def example_file_dialogs():
    """Example file dialog handling."""
    automation = FileDialogAutomation()
    
    # Wait for dialog and handle it
    # automation.handle_save_dialog(r"C:\Users\User\Documents\output.txt")
    
    print("File dialog automation ready")


if __name__ == "__main__":
    example_file_dialogs()
```

---

## Process Management

```python
#!/usr/bin/env python3
"""Process management - run with: uv run script.py"""

import subprocess
import psutil
from dataclasses import dataclass
from typing import Optional, List
import time


@dataclass
class ProcessInfo:
    """Process information."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_mb: float
    cmdline: List[str]


class ProcessManager:
    """Manage Windows processes."""
    
    def start_process(
        self,
        executable: str,
        args: List[str] = None,
        working_dir: str = None,
        wait: bool = False
    ) -> int:
        """Start process."""
        cmd = [executable] + (args or [])
        
        process = subprocess.Popen(
            cmd,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if wait:
            process.wait()
        
        return process.pid
    
    def kill_process(self, pid: int = None, name: str = None) -> bool:
        """Kill process by PID or name."""
        try:
            if pid:
                process = psutil.Process(pid)
                process.terminate()
                return True
            elif name:
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() == name.lower():
                        proc.terminate()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False
    
    def kill_all_by_name(self, name: str) -> int:
        """Kill all processes with name."""
        killed = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == name.lower():
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed
    
    def find_process(self, name: str) -> Optional[ProcessInfo]:
        """Find process by name."""
        for proc in psutil.process_iter(['name', 'status', 'cpu_percent', 'memory_info', 'cmdline']):
            try:
                if proc.info['name'].lower() == name.lower():
                    return ProcessInfo(
                        pid=proc.pid,
                        name=proc.info['name'],
                        status=proc.info['status'],
                        cpu_percent=proc.info['cpu_percent'] or 0,
                        memory_mb=(proc.info['memory_info'].rss / 1024 / 1024) if proc.info['memory_info'] else 0,
                        cmdline=proc.info['cmdline'] or []
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None
    
    def list_processes(self, name_filter: str = None) -> List[ProcessInfo]:
        """List all processes."""
        processes = []
        for proc in psutil.process_iter(['name', 'status', 'cpu_percent', 'memory_info', 'cmdline']):
            try:
                if name_filter and name_filter.lower() not in proc.info['name'].lower():
                    continue
                
                processes.append(ProcessInfo(
                    pid=proc.pid,
                    name=proc.info['name'],
                    status=proc.info['status'],
                    cpu_percent=proc.info['cpu_percent'] or 0,
                    memory_mb=(proc.info['memory_info'].rss / 1024 / 1024) if proc.info['memory_info'] else 0,
                    cmdline=proc.info['cmdline'] or []
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return processes
    
    def wait_for_process(self, name: str, timeout: int = 30) -> bool:
        """Wait for process to start."""
        start = time.time()
        while time.time() - start < timeout:
            if self.find_process(name):
                return True
            time.sleep(0.5)
        return False
    
    def wait_for_process_end(self, pid: int, timeout: int = 60) -> bool:
        """Wait for process to end."""
        try:
            process = psutil.Process(pid)
            process.wait(timeout=timeout)
            return True
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            return False


if __name__ == "__main__":
    manager = ProcessManager()
    
    # List all notepad processes
    processes = manager.list_processes("notepad")
    for p in processes:
        print(f"{p.pid}: {p.name} - {p.memory_mb:.1f} MB")
```

---

## Best Practices

1. **Use UIA backend** - More reliable than Win32 for modern apps
2. **Add delays** - Allow UI to update between actions
3. **Use automation IDs** - More stable than names
4. **Handle dialogs** - Expect and handle popup dialogs
5. **Implement waits** - Wait for elements before interacting
6. **Take screenshots on failure** - For debugging
7. **Use process management** - Ensure clean app state

---

**Next Module:** See **rpa-documents.md** for Excel/PDF/Email automation.
