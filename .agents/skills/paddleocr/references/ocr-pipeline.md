# OCR Pipeline Reference

Covers: text detection, recognition, orientation classification, confidence filtering, PDF batch processing, and output formats.

**Updated for PaddleOCR 3.5.0 API** — uses `.predict()` instead of deprecated `.ocr()`.

## Pipeline Architecture

```
Input Image/PDF
      │
      ▼
┌─────────────────────┐
│  Document Unwarp    │  UVDoc model — correct perspective/curvature
│  (PP-LCNet_doc_ori) │  + PP-LCNet_x1_0_doc_ori (page orientation)
│  [optional]         │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Text Detection     │  PP-OCRv5_server_det — find text regions
│  (bounding boxes)   │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Textline Orient.   │  PP-LCNet_x1_0_textline_ori — rotate lines
│  (0/90/180/270°)    │  [optional]
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Text Recognition   │  en_PP-OCRv5_mobile_rec — text → string
│  + Confidence       │
└─────────────────────┘
      │
      ▼
   OCRResult objects: res.json['res']['rec_texts'], rec_scores, rec_polys
```

## Initialization

```python
from paddleocr import PaddleOCR

# Minimal (fastest) — disables all preprocessing
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang='en'
)

# Full pipeline — includes orientation + unwarping
ocr = PaddleOCR(
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True,
    lang='en'
)
```

## Model Variants

### Detection Models
```python
# Default (server-grade, high accuracy)
ocr = PaddleOCR(text_detection_model_name="PP-OCRv5_server_det", lang='en')

# Fast/mobile
ocr = PaddleOCR(text_detection_model_name="PP-OCRv5_mobile_det", lang='en')

# Scene text (photos, signs, natural images) — use CLI flags
# paddleocr ocr -i image.png --text_det_thresh 0.3 --text_det_box_thresh 0.5 --text_det_unclip_ratio 1.6
```

### Recognition Models
```python
# English (default)
ocr = PaddleOCR(lang='en')    # en_PP-OCRv5_mobile_rec (fast)

# Chinese + English
ocr = PaddleOCR(lang='ch')    # ch_PP-OCRv4_rec

# Server-grade English (highest accuracy, slower)
ocr = PaddleOCR(text_recognition_model_name="en_PP-OCRv5_server_rec", lang='en')
```

## Detection-Only Mode

```python
from paddleocr import TextDetection

det = TextDetection()
output = det.predict('image.jpg')
for res in output:
    polys = res.json['res']['dt_polys']    # list of polygon regions
    scores = res.json['res']['dt_scores']  # detection confidence
    res.save_to_img("./output/")
    res.save_to_json("./output/res.json")
```

## Recognition-Only Mode (pre-cropped text regions)

```python
from paddleocr import TextRecognition

rec = TextRecognition()
output = rec.predict(input='cropped_text.png')
for res in output:
    text = res.json['res']['rec_text']     # recognized string
    score = res.json['res']['rec_score']   # confidence float
```

## Orientation Classification

```python
# Enable at init time (not per-call)
ocr = PaddleOCR(use_textline_orientation=True, lang='en')
result = ocr.predict('rotated_scan.jpg')
for res in result:
    data = res.json['res']
    angles = data.get('textline_orientation_angles', [])  # per-line rotation
    texts = data['rec_texts']
```

## Confidence Thresholding

```python
def filter_by_confidence(result, min_conf=0.80):
    """Remove low-confidence detections from OCRResult."""
    data = result.json['res']
    filtered = []
    for text, score in zip(data['rec_texts'], data['rec_scores']):
        if score >= min_conf:
            filtered.append({'text': text, 'conf': score})
    return filtered

# Usage
result = ocr.predict('document.jpg')
for res in result:
    lines = filter_by_confidence(res, min_conf=0.90)
```

## Spatial Sorting (Reading Order)

```python
def sort_by_reading_order(result):
    """Sort OCR results top-to-bottom, left-to-right."""
    data = result.json['res']
    items = list(zip(data['rec_polys'], data['rec_texts'], data['rec_scores']))
    # Sort by y-center then x-center of polygon
    def sort_key(item):
        poly = item[0]
        y_center = sum(p[1] for p in poly) / len(poly)
        x_center = sum(p[0] for p in poly) / len(poly)
        return (y_center, x_center)
    return sorted(items, key=sort_key)

# Usage
result = ocr.predict('document.jpg')
for res in result:
    sorted_items = sort_by_reading_order(res)
    for poly, text, score in sorted_items:
        print(text)
```

## PDF Processing

### Method 1: pypdfium2 (fastest, already installed)

```python
import pypdfium2 as pdfium
from paddleocr import PaddleOCR

def ocr_pdf(pdf_path: str, lang='en', dpi=200) -> list[dict]:
    """OCR all pages of a PDF. Returns list of page results."""
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang=lang
    )
    doc = pdfium.PdfDocument(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        bitmap = page.render(scale=dpi / 72)
        pil_img = bitmap.to_pil()

        result = ocr.predict(pil_img)
        for res in result:
            texts = res.json['res']['rec_texts']
            text = '\n'.join(texts)
            pages.append({'page': page_num + 1, 'text': text})

    doc.close()
    return pages
```

### Method 2: Pillow (for scanned PDFs already as images)

```python
from PIL import Image
pil_img = Image.open('scan.tiff')
result = ocr.predict(pil_img)
for res in result:
    texts = res.json['res']['rec_texts']
```

## Result Object Structure (v3.5.0)

```python
result = ocr.predict('document.jpg')
for res in result:
    data = res.json['res']
    
    # Core data
    data['rec_texts']       # list[str] — recognized text lines
    data['rec_scores']      # list[float] — confidence per line
    data['rec_polys']       # list[list] — 4-point polygons [[x,y],...]
    data['rec_boxes']       # list[list] — bounding boxes [x, y, w, h]
    data['dt_polys']        # list[list] — raw detection polygons
    data['input_path']      # str — source file path
    data['page_index']      # int|None — page number for PDFs
    data['model_settings']  # dict — pipeline config used
    
    # Save methods
    res.print()                    # print results
    res.save_to_img("output")      # save annotated image
    res.save_to_json("output")      # save JSON results
```

## Output Formats

### Export to JSON
```python
import json

def ocr_to_json(result, output_path='output.json'):
    data = result.json['res']
    entries = [
        {'text': text, 'confidence': round(score, 4), 'polygon': poly, 'box': box}
        for text, score, poly, box in zip(
            data['rec_texts'], data['rec_scores'],
            data['rec_polys'], data['rec_boxes']
        )
    ]
    with open(output_path, 'w') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    return entries
```

### Export to plain text
```python
def ocr_to_text(result) -> str:
    data = result.json['res']
    return '\n'.join(data['rec_texts'])
```

### Export to TSV (bbox + text + confidence)
```python
def ocr_to_tsv(result, output_path='output.tsv'):
    data = result.json['res']
    rows = []
    for poly, text, score in zip(data['rec_polys'], data['rec_texts'], data['rec_scores']):
        if len(poly) >= 3:
            x = int(poly[0][0]); y = int(poly[0][1])
            w = int(poly[2][0] - poly[0][0]); h = int(poly[2][1] - poly[0][1])
        else:
            x = y = w = h = 0
        rows.append(f"{x}\t{y}\t{w}\t{h}\t{text}\t{score:.4f}")
    with open(output_path, 'w') as f:
        f.write('x\ty\tw\th\ttext\tconf\n' + '\n'.join(rows))
```

### Annotated image output
```python
# Use PaddleOCR's built-in save method
result = ocr.predict('document.jpg')
for res in result:
    res.save_to_img("output")  # saves annotated image to output/ directory
```

### Manual annotation with OpenCV
```python
import cv2
import numpy as np

def draw_ocr_results(img_path, result, output_path='annotated.jpg'):
    img = cv2.imread(img_path)
    data = result.json['res']
    for poly, text in zip(data['rec_polys'], data['rec_texts']):
        pts = np.array(poly, dtype=np.int32)
        cv2.polylines(img, [pts], True, (0, 255, 0), 2)
        x, y = pts[0]
        cv2.putText(img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 1)
    cv2.imwrite(output_path, img)
    return output_path
```

## Detection Hyperparameters

| Parameter | CLI Flag | Default | Effect |
|---|---|---|---|
| `text_det_thresh` | `--text_det_thresh` | 0.3 | Lower = detect more (inc. faint text) |
| `text_det_box_thresh` | `--text_det_box_thresh` | 0.6 | Lower = keep more boxes |
| `text_det_unclip_ratio` | `--text_det_unclip_ratio` | 1.5 | Higher = larger boxes (good for tight text) |
| `text_det_limit_side_len` | `--text_det_limit_side_len` | 960 | Max side length before downscaling |
| `text_det_limit_type` | `--text_det_limit_type` | 'max' | 'max' or 'min' |

## Batch Processing Pattern

```python
from pathlib import Path
from paddleocr import PaddleOCR

def batch_ocr(input_dir: str, output_dir: str, lang='en', exts=('.jpg','.png','.bmp','.tiff')):
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang=lang
    )
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for img_path in Path(input_dir).rglob('*'):
        if img_path.suffix.lower() not in exts:
            continue
        result = ocr.predict(str(img_path))
        for res in result:
            text = '\n'.join(res.json['res']['rec_texts'])
            (out / img_path.stem).with_suffix('.txt').write_text(text, encoding='utf-8')
        print(f"✅ {img_path.name}")
```

## CLI Quick Reference

```bash
# Full OCR
paddleocr ocr -i image.png \
    --use_doc_orientation_classify False \
    --use_doc_unwarping False \
    --use_textline_orientation False \
    --device cpu \
    --save_path ./output

# Detection only
paddleocr text_detection -i image.png

# Recognition only
paddleocr text_recognition -i cropped_line.png

# With custom thresholds
paddleocr ocr -i image.png \
    --text_det_thresh 0.2 \
    --text_det_box_thresh 0.5 \
    --text_det_unclip_ratio 1.8
```

## Migration from v2.x / early v3.x

| Old | New (v3.5.0) |
|---|---|
| `ocr.ocr(img, cls=True)` | `ocr.predict(img)` |
| `result[0][i][1][0]` (text) | `res.json['res']['rec_texts'][i]` |
| `result[0][i][1][1]` (score) | `res.json['res']['rec_scores'][i]` |
| `result[0][i][0]` (bbox) | `res.json['res']['rec_polys'][i]` |
| `PaddleOCR(show_log=False)` | `PaddleOCR(...)` — `show_log` removed |
| `PaddleOCR(use_gpu=False)` | `PaddleOCR(device="cpu")` |
| `ocr.ocr(img, rec=False)` | Use `TextDetection().predict(img)` |
| `ocr.ocr(img, det=False)` | Use `TextRecognition().predict(img)` |
