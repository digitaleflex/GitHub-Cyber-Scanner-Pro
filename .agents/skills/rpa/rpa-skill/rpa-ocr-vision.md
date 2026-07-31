# RPA OCR and Visual Automation Module

Visual automation patterns including OCR (Optical Character Recognition), image recognition, screen capture, and visual element location for legacy systems.

## OCR with Tesseract

### Basic OCR

```python
#!/usr/bin/env python3
"""OCR with Tesseract - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from PIL import Image
import pytesseract
from pathlib import Path
import io


class OCRHandler:
    """Handle OCR operations."""
    
    def __init__(self, tesseract_cmd: str = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_text(self, image_path: str, lang: str = "eng") -> str:
        """Extract text from image."""
        image = Image.open(image_path)
        return pytesseract.image_to_string(image, lang=lang)
    
    def extract_from_bytes(self, image_bytes: bytes, lang: str = "eng") -> str:
        """Extract text from image bytes."""
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image, lang=lang)
    
    def extract_with_boxes(self, image_path: str, lang: str = "eng") -> list[dict]:
        """Extract text with bounding boxes."""
        image = Image.open(image_path)
        data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
        
        results = []
        for i in range(len(data["text"])):
            if data["text"][i].strip():
                results.append({
                    "text": data["text"][i],
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "confidence": data["conf"][i]
                })
        
        return results
    
    def extract_numbers(self, image_path: str) -> list[str]:
        """Extract only numbers from image."""
        image = Image.open(image_path)
        config = "--psm 6 -c tessedit_char_whitelist=0123456789.,-"
        text = pytesseract.image_to_string(image, config=config)
        
        import re
        numbers = re.findall(r"[\d.,]+", text)
        return numbers
    
    def extract_table(self, image_path: str) -> list[list[str]]:
        """Extract table from image."""
        image = Image.open(image_path)
        config = "--psm 6"
        text = pytesseract.image_to_string(image, config=config)
        
        lines = text.strip().split("\n")
        table = []
        for line in lines:
            row = [cell.strip() for cell in line.split() if cell.strip()]
            if row:
                table.append(row)
        
        return table
    
    def preprocess_image(self, image_path: str, output_path: str = None) -> Image.Image:
        """Preprocess image for better OCR."""
        from PIL import ImageFilter, ImageEnhance
        
        image = Image.open(image_path)
        
        # Convert to grayscale
        image = image.convert("L")
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply sharpening
        image = image.filter(ImageFilter.SHARPEN)
        
        if output_path:
            image.save(output_path)
        
        return image


class PageOCR:
    """OCR operations on browser pages."""
    
    def __init__(self, page: Page):
        self.page = page
        self.ocr = OCRHandler()
    
    def capture_and_ocr(self, selector: str = None, lang: str = "eng") -> str:
        """Capture element/page and perform OCR."""
        if selector:
            element = self.page.locator(selector)
            screenshot_bytes = element.screenshot()
        else:
            screenshot_bytes = self.page.screenshot()
        
        return self.ocr.extract_from_bytes(screenshot_bytes, lang)
    
    def find_text_position(self, target_text: str, selector: str = None) -> dict:
        """Find position of text using OCR."""
        if selector:
            element = self.page.locator(selector)
            screenshot_bytes = element.screenshot()
            box = element.bounding_box()
            offset_x, offset_y = box["x"], box["y"]
        else:
            screenshot_bytes = self.page.screenshot()
            offset_x, offset_y = 0, 0
        
        # Save temporarily for OCR with boxes
        temp_path = "/tmp/ocr_temp.png"
        with open(temp_path, "wb") as f:
            f.write(screenshot_bytes)
        
        boxes = self.ocr.extract_with_boxes(temp_path)
        
        for item in boxes:
            if target_text.lower() in item["text"].lower():
                return {
                    "x": item["x"] + offset_x + item["width"] / 2,
                    "y": item["y"] + offset_y + item["height"] / 2,
                    "text": item["text"],
                    "confidence": item["confidence"]
                }
        
        return None
    
    def click_by_text(self, text: str, selector: str = None):
        """Click on text found via OCR."""
        position = self.find_text_position(text, selector)
        
        if position:
            self.page.mouse.click(position["x"], position["y"])
            return True
        return False


def example_ocr():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://example.com")
        
        ocr = PageOCR(page)
        
        # Extract all text from page
        text = ocr.capture_and_ocr()
        print(f"Page text:\n{text[:500]}...")
        
        # Find and click text
        if ocr.click_by_text("More information"):
            print("Clicked on 'More information'")
        
        browser.close()


if __name__ == "__main__":
    example_ocr()
```

---

## Image Recognition

### Template Matching

```python
#!/usr/bin/env python3
"""Image recognition with OpenCV - run with: uv run script.py"""

import cv2
import numpy as np
from playwright.sync_api import sync_playwright, Page
from pathlib import Path
from typing import Optional, Tuple
import io


class ImageRecognition:
    """Image recognition using template matching."""
    
    def find_template(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.8
    ) -> Optional[Tuple[int, int, int, int]]:
        """Find template in screenshot."""
        # Convert to grayscale
        gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Template matching
        result = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            h, w = gray_template.shape
            return (max_loc[0], max_loc[1], w, h)
        
        return None
    
    def find_all_templates(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.8
    ) -> list[Tuple[int, int, int, int]]:
        """Find all occurrences of template."""
        gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        
        h, w = gray_template.shape
        matches = []
        
        for pt in zip(*locations[::-1]):
            matches.append((pt[0], pt[1], w, h))
        
        # Remove overlapping matches
        return self._remove_overlaps(matches)
    
    def _remove_overlaps(
        self,
        matches: list[Tuple[int, int, int, int]],
        overlap_thresh: float = 0.5
    ) -> list[Tuple[int, int, int, int]]:
        """Remove overlapping matches using NMS."""
        if not matches:
            return []
        
        boxes = np.array([[x, y, x + w, y + h] for x, y, w, h in matches])
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        indices = np.argsort(areas)[::-1]
        
        keep = []
        while len(indices) > 0:
            i = indices[0]
            keep.append(i)
            
            xx1 = np.maximum(x1[i], x1[indices[1:]])
            yy1 = np.maximum(y1[i], y1[indices[1:]])
            xx2 = np.minimum(x2[i], x2[indices[1:]])
            yy2 = np.minimum(y2[i], y2[indices[1:]])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            overlap = (w * h) / areas[indices[1:]]
            indices = indices[1:][overlap < overlap_thresh]
        
        return [matches[i] for i in keep]
    
    def compare_images(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compare two images and return similarity score."""
        # Resize to same size
        h, w = img1.shape[:2]
        img2 = cv2.resize(img2, (w, h))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Compute SSIM
        from skimage.metrics import structural_similarity
        score, _ = structural_similarity(gray1, gray2, full=True)
        
        return score


class VisualAutomation:
    """Visual automation using image recognition."""
    
    def __init__(self, page: Page, templates_dir: str = "./templates"):
        self.page = page
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.recognizer = ImageRecognition()
    
    def _screenshot_to_cv2(self) -> np.ndarray:
        """Capture page as OpenCV image."""
        screenshot_bytes = self.page.screenshot()
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    def save_template(self, selector: str, name: str):
        """Save element as template."""
        element = self.page.locator(selector)
        screenshot_bytes = element.screenshot()
        
        template_path = self.templates_dir / f"{name}.png"
        with open(template_path, "wb") as f:
            f.write(screenshot_bytes)
        
        print(f"Template saved: {template_path}")
    
    def find_element(self, template_name: str, threshold: float = 0.8) -> Optional[dict]:
        """Find element by template."""
        template_path = self.templates_dir / f"{template_name}.png"
        template = cv2.imread(str(template_path))
        
        screenshot = self._screenshot_to_cv2()
        match = self.recognizer.find_template(screenshot, template, threshold)
        
        if match:
            x, y, w, h = match
            return {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "center_x": x + w / 2,
                "center_y": y + h / 2
            }
        
        return None
    
    def click_image(self, template_name: str, threshold: float = 0.8) -> bool:
        """Click on element found by image."""
        element = self.find_element(template_name, threshold)
        
        if element:
            self.page.mouse.click(element["center_x"], element["center_y"])
            return True
        
        return False
    
    def wait_for_image(
        self,
        template_name: str,
        timeout: int = 30,
        threshold: float = 0.8
    ) -> bool:
        """Wait for image to appear."""
        import time
        
        start = time.time()
        while time.time() - start < timeout:
            if self.find_element(template_name, threshold):
                return True
            time.sleep(0.5)
        
        return False
    
    def drag_image_to(
        self,
        source_template: str,
        target_template: str,
        threshold: float = 0.8
    ) -> bool:
        """Drag from source image to target image."""
        source = self.find_element(source_template, threshold)
        target = self.find_element(target_template, threshold)
        
        if source and target:
            self.page.mouse.move(source["center_x"], source["center_y"])
            self.page.mouse.down()
            self.page.mouse.move(target["center_x"], target["center_y"])
            self.page.mouse.up()
            return True
        
        return False


def example_visual():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto("https://example.com")
        
        visual = VisualAutomation(page)
        
        # Save template of button
        visual.save_template("a", "more_info_link")
        
        # Later, click by image
        if visual.click_image("more_info_link"):
            print("Clicked using image recognition!")
        
        browser.close()


if __name__ == "__main__":
    example_visual()
```

---

## Screen Capture and Recording

```python
#!/usr/bin/env python3
"""Screen capture and recording - run with: uv run script.py"""

from playwright.sync_api import sync_playwright, Page
from pathlib import Path
from datetime import datetime
from typing import Optional
import base64
import json


class ScreenCapture:
    """Screen capture utilities."""
    
    def __init__(self, page: Page, output_dir: str = "./captures"):
        self.page = page
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def capture_full_page(self, name: str = None) -> Path:
        """Capture full page screenshot."""
        name = name or f"page_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = self.output_dir / f"{name}.png"
        
        self.page.screenshot(path=str(path), full_page=True)
        return path
    
    def capture_viewport(self, name: str = None) -> Path:
        """Capture visible viewport only."""
        name = name or f"viewport_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = self.output_dir / f"{name}.png"
        
        self.page.screenshot(path=str(path), full_page=False)
        return path
    
    def capture_element(self, selector: str, name: str = None) -> Path:
        """Capture specific element."""
        name = name or f"element_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = self.output_dir / f"{name}.png"
        
        self.page.locator(selector).screenshot(path=str(path))
        return path
    
    def capture_as_base64(self) -> str:
        """Capture page as base64 string."""
        screenshot_bytes = self.page.screenshot()
        return base64.b64encode(screenshot_bytes).decode()
    
    def capture_with_annotations(
        self,
        annotations: list[dict],
        name: str = None
    ) -> Path:
        """Capture page with visual annotations."""
        import cv2
        import numpy as np
        
        screenshot_bytes = self.page.screenshot(full_page=True)
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        for ann in annotations:
            if ann["type"] == "rectangle":
                cv2.rectangle(
                    img,
                    (ann["x"], ann["y"]),
                    (ann["x"] + ann["width"], ann["y"] + ann["height"]),
                    (0, 0, 255),
                    2
                )
            elif ann["type"] == "circle":
                cv2.circle(
                    img,
                    (ann["x"], ann["y"]),
                    ann["radius"],
                    (0, 255, 0),
                    2
                )
            elif ann["type"] == "text":
                cv2.putText(
                    img,
                    ann["text"],
                    (ann["x"], ann["y"]),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    2
                )
        
        name = name or f"annotated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path = self.output_dir / f"{name}.png"
        cv2.imwrite(str(path), img)
        
        return path
    
    def compare_screenshots(self, path1: str, path2: str) -> dict:
        """Compare two screenshots."""
        import cv2
        
        img1 = cv2.imread(path1)
        img2 = cv2.imread(path2)
        
        # Resize if needed
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # Compute difference
        diff = cv2.absdiff(img1, img2)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        differences = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 5:
                differences.append({"x": x, "y": y, "width": w, "height": h})
        
        return {
            "identical": len(differences) == 0,
            "difference_count": len(differences),
            "differences": differences
        }


class ScreenRecorder:
    """Record browser session."""
    
    def __init__(self, output_dir: str = "./recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def start_recording(self, browser, name: str = None) -> "BrowserContext":
        """Start recording browser context."""
        name = name or f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        video_dir = self.output_dir / name
        video_dir.mkdir(exist_ok=True)
        
        context = browser.new_context(
            record_video_dir=str(video_dir),
            record_video_size={"width": 1280, "height": 720}
        )
        
        return context
    
    def stop_recording(self, context) -> list[Path]:
        """Stop recording and return video paths."""
        videos = []
        
        for page in context.pages:
            video = page.video
            if video:
                videos.append(Path(video.path()))
        
        context.close()
        return videos


def example_capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://example.com")
        
        capture = ScreenCapture(page)
        
        # Full page screenshot
        full = capture.capture_full_page("example_full")
        print(f"Full page: {full}")
        
        # Element screenshot
        elem = capture.capture_element("h1", "example_heading")
        print(f"Element: {elem}")
        
        # Annotated screenshot
        annotations = [
            {"type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 50},
            {"type": "text", "text": "Click here", "x": 120, "y": 90}
        ]
        annotated = capture.capture_with_annotations(annotations, "example_annotated")
        print(f"Annotated: {annotated}")
        
        browser.close()


if __name__ == "__main__":
    example_capture()
```

---

## Best Practices

1. **Preprocess images** - Improve OCR accuracy with grayscale, contrast, sharpening
2. **Use appropriate thresholds** - Tune template matching for reliability
3. **Handle variations** - Images may have slight differences
4. **Fallback to selectors** - Use visual only when necessary
5. **Cache templates** - Store frequently used templates
6. **Log visual matches** - Save screenshots for debugging

---

**Next Module:** See **rpa-error-handling.md** for retry and recovery patterns.
