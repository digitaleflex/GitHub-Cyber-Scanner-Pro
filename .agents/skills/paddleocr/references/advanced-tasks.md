# Advanced OCR Tasks Reference

**⚠️ v3.5.0 API Update:** Code examples below may use the deprecated `.ocr()` method and `result[0]` access pattern. In v3.5.0, use `.predict()` and access results via `res.json[res]`. See [ocr-pipeline.md](ocr-pipeline.md) for the migration guide. Key changes:
- `ocr.ocr(img)` → `ocr.predict(img)`
- `result[0][i][1][0]` (text) → `res.json[res][rec_texts][i]`
- `result[0][i][1][1]` (score) → `res.json[res][rec_scores][i]`
- `result[0][i][0]` (bbox) → `res.json[res][rec_polys][i]`
- `for line in (result[0] or []): line[1][0]` → `for res in result: for text, score in zip(res.json[res][rec_texts], res.json[res][rec_scores])`

Covers: seal/stamp recognition, handwriting, mathematical formulas, multilingual OCR (80+ languages), scene text, low-quality images, rotated/curved text, document verification.

## Seal & Stamp Recognition

Seals (circular stamps) require special detection:

```python
from paddleocr import PaddleOCR

# Enable seal detection
ocr = PaddleOCR(
    use_seal_recognition=True,        # dedicated seal detector
    lang='ch',                # seals are often Chinese characters
    
)

result = ocr.predict('document_with_seal.jpg')

# Seal text appears in result like regular text
# but with circular/rotated bounding boxes
for line in (result[0] or []):
    print(f"Text: {line[1][0]}  Conf: {line[1][1]:.2f}  BBox: {line[0]}")
```

### Detect seal presence
```python
import cv2
import numpy as np

def detect_seal_region(image_path: str) -> list[tuple]:
    """
    Find circular seal regions using Hough Circle Transform.
    Returns list of (x, y, radius) tuples.
    """
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    blurred = cv2.GaussianBlur(img, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=50,
        param2=30,
        minRadius=30,
        maxRadius=200
    )
    if circles is None:
        return []
    return [(int(c[0]), int(c[1]), int(c[2])) for c in circles[0]]

def crop_and_ocr_seal(image_path: str) -> list[str]:
    """Crop seal regions and OCR them individually."""
    img = cv2.imread(image_path)
    seals = detect_seal_region(image_path)
    results = []
    ocr = PaddleOCR(use_seal_recognition=True, lang='ch')
    for x, y, r in seals:
        pad = int(r * 0.2)
        x1, y1 = max(0, x - r - pad), max(0, y - r - pad)
        x2, y2 = min(img.shape[1], x + r + pad), min(img.shape[0], y + r + pad)
        crop = img[y1:y2, x1:x2]
        res = ocr.predict(crop)
        text = ' '.join(l[1][0] for l in (res[0] or []))
        results.append(text)
    return results
```

## Handwriting Recognition

```python
# Standard PaddleOCR handles printed handwriting reasonably well
# For dedicated handwriting models, use PP-OCRv3 with hw-tuned rec:

ocr = PaddleOCR(
    det_model_dir=None,   # standard detection
    rec_model_dir=None,   # upgrade to server_rec for better hw support
    lang='en',
    use_textline_orientation=True,
    
)

# For cursive/flowing handwriting, preprocess first:
def preprocess_handwriting(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Adaptive thresholding (better than global for uneven lighting)
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    # Morphological closing to connect broken strokes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return cleaned

def ocr_handwriting(image_path: str) -> str:
    preprocessed = preprocess_handwriting(image_path)
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(preprocessed)
    return '\n'.join(l[1][0] for l in (result[0] or []))
```

## Mathematical Formula Extraction

PaddleOCR detects formula regions; use LaTeX-OCR for conversion:

```python
from paddleocr import PPStructureV3

engine = PPStructureV3(layout=True)
result = engine('math_paper.jpg')

formula_regions = [r for r in result if r['type'] == 'formula']
print(f"Found {len(formula_regions)} formula region(s)")

# For LaTeX conversion, use pix2tex (LaTeX-OCR):
# pip install pix2tex
def formula_to_latex(crop_image) -> str:
    try:
        from pix2tex.cli import LatexOCR
        model = LatexOCR()
        from PIL import Image
        if isinstance(crop_image, str):
            img = Image.open(crop_image)
        else:
            img = Image.fromarray(crop_image)
        return model(img)
    except ImportError:
        return "[pix2tex not installed: pip install pix2tex]"

# Crop formula regions and convert
import cv2
img = cv2.imread('math_paper.jpg')
for i, region in enumerate(formula_regions):
    bbox = region['bbox']
    crop = img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
    latex = formula_to_latex(crop)
    print(f"Formula {i+1}: {latex}")
```

## Multilingual OCR

PaddleOCR supports 80+ languages:

```python
# Language codes
LANG_CODES = {
    'English':    'en',
    'Chinese':    'ch',
    'Chinese Trad': 'chinese_cht',
    'Japanese':   'japan',
    'Korean':     'korean',
    'French':     'fr',
    'German':     'german',
    'Arabic':     'arabic',
    'Hindi':      'hi',
    'Urdu':       'ur',
    'Russian':    'ru',
    'Spanish':    'es',
    'Portuguese': 'pt',
    'Italian':    'it',
    'Yoruba':     'en',      # use en; Yoruba not natively supported → fallback
    'Hausa':      'en',      # same fallback
    'Igbo':       'en',
    'Latin':      'latin',
    'Cyrillic':   'cyrillic',
    'Devanagari': 'devanagari',  # Hindi/Nepali/Marathi
    'Tamil':      'ta',
    'Telugu':     'te',
    'Kannada':    'ka',
}

def auto_detect_language_and_ocr(image_path: str) -> dict:
    """
    Attempt OCR with multiple languages and return best result.
    Heuristic: highest average confidence wins.
    """
    candidates = ['en', 'ch', 'fr', 'arabic', 'hi']
    best = {'lang': 'en', 'text': '', 'avg_conf': 0.0}

    for lang in candidates:
        ocr = PaddleOCR(lang=lang)
        result = ocr.predict(image_path)
        lines = result[0] or []
        if not lines:
            continue
        avg_conf = sum(l[1][1] for l in lines) / len(lines)
        if avg_conf > best['avg_conf']:
            best = {
                'lang': lang,
                'text': '\n'.join(l[1][0] for l in lines),
                'avg_conf': avg_conf
            }

    return best
```

### Mixed-language document
```python
def ocr_mixed_language(image_path: str, primary_lang='ch') -> str:
    """
    Handle documents with mixed languages (e.g., Chinese + English).
    PaddleOCR's 'ch' model handles Chinese+English well by default.
    """
    ocr = PaddleOCR(lang=primary_lang, use_textline_orientation=True)
    result = ocr.predict(image_path)
    return '\n'.join(l[1][0] for l in (result[0] or []))
```

## Scene Text (Photos, Signs, Natural Images)

```python
def ocr_scene_text(image_path: str) -> list[dict]:
    """
    OCR text in natural scene photos (signs, storefronts, whiteboards).
    Uses looser detection thresholds for irregular text placement.
    """
    ocr = PaddleOCR(
        det_db_thresh=0.2,          # lower = detect more (faint/small text)
        det_db_box_thresh=0.4,
        det_db_unclip_ratio=2.0,    # higher = larger boxes (scene text needs this)
        use_textline_orientation=True,
        lang='en',
        
    )
    result = ocr.predict(image_path)
    return [{'text': l[1][0], 'conf': l[1][1], 'bbox': l[0]}
            for l in (result[0] or []) if l[1][1] > 0.5]
```

## Low-Quality / Degraded Document Recovery

```python
def restore_and_ocr(image_path: str) -> str:
    """Pipeline for degraded/low-quality scans."""
    img = cv2.imread(image_path)

    # Step 1: Upscale if small
    h, w = img.shape[:2]
    if max(h, w) < 1000:
        scale = 1000 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # Step 2: Deskew
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    coords = np.column_stack(np.where(gray < 200))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:
            M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
            img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)

    # Step 3: CLAHE contrast enhancement
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    # Step 4: Denoise
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    # Step 5: Binarize for very poor quality
    gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(binary)
    return '\n'.join(l[1][0] for l in (result[0] or []))
```

## Rotated and Curved Text

```python
def ocr_rotated_document(image_path: str, angle: float = None) -> str:
    """
    OCR a document that is rotated by a known or auto-detected angle.
    If angle=None, auto-detects using document orientation model.
    """
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    if angle is not None:
        M = cv2.getRotationMatrix2D((w//2, h//2), -angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)

    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(img)
    return '\n'.join(l[1][0] for l in (result[0] or []))
```

## Watermark Text Extraction

```python
def extract_under_watermark(image_path: str) -> str:
    """
    Attempt to extract text beneath a watermark using color channel separation.
    Works best when watermark is a single color (e.g., red diagonal text).
    """
    img = cv2.imread(image_path)
    # Split channels; use the channel where watermark has least contrast
    b, g, r = cv2.split(img)
    # For red watermarks, use blue channel (watermark appears faded)
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(b)   # try blue channel
    return '\n'.join(l[1][0] for l in (result[0] or []))
```

## Document Verification

```python
def verify_document_completeness(image_path: str, doc_type: str, required_fields: list[str]) -> dict:
    """
    Check that all required fields are present in a document.
    Returns: {field: found/missing, overall: pass/fail}
    """
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(image_path)
    full_text = '\n'.join(l[1][0] for l in (result[0] or [])).lower()

    field_status = {}
    for field in required_fields:
        field_status[field] = field.lower() in full_text

    return {
        'doc_type': doc_type,
        'fields': field_status,
        'missing': [f for f, found in field_status.items() if not found],
        'overall': 'PASS' if all(field_status.values()) else 'FAIL'
    }


# Example: verify invoice
status = verify_document_completeness(
    'invoice.jpg',
    'invoice',
    ['invoice', 'date', 'total', 'vat', 'company']
)
```

## Performance Benchmarks (This Host — CPU ARM64)

| Task | Approx. Time per Page |
|---|---|
| Standard English OCR (A4) | ~1–2s |
| PPStructure layout + OCR | ~3–6s |
| Table extraction (single table) | ~2–4s |
| Seal detection | ~2–3s |
| PDF page (200 DPI render + OCR) | ~2–4s |
| Multi-language (ch model) | ~2–3s |
| VL model inference | ~60–120s (not installed) |
