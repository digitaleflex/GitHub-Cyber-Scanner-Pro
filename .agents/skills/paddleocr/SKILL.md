---
name: paddleocr
description: Comprehensive PaddleOCR document intelligence skill covering OCR text extraction, table detection and QA, layout analysis, document-level reasoning, structured extraction (forms, invoices, IDs, receipts), seal/stamp recognition, handwriting, formulas, multilingual OCR, and PaddleOCR-VL multimodal tasks. Use when extracting text from images or PDFs, parsing tables, understanding document structure, extracting key-value pairs, running document QA, processing financial documents, or doing any image-to-structured-data task.
---

# PaddleOCR Skill

**Installed:** PaddleOCR 3.5.0 · PaddlePaddle 3.3.1 · Python 3.12 · macOS ARM64
**Model cache:** `~/.paddlex/official_models/`
**Official docs:** https://www.paddleocr.ai/v3.5.0/en/quick_start.html

## Task → Tool Matrix

| Task | Primary Tool | CLI Subcommand | Reference |
|---|---|---|---|
| Plain text extraction | `PaddleOCR(lang='en')` | `paddleocr ocr` | [ocr-pipeline.md](references/ocr-pipeline.md) |
| Document structure (layout+tables+text) | `PPStructureV3` | `paddleocr pp_structurev3` | [document-reasoning.md](references/document-reasoning.md) |
| Table extraction (HTML/CSV) | `PPStructureV3` | `paddleocr table_recognition_v2` | [table-qa.md](references/table-qa.md) |
| Form / KV extraction | `PaddleOCR` + regex | — | [structured-extraction.md](references/structured-extraction.md) |
| Invoice / receipt parsing | `PaddleOCR` + template | — | [structured-extraction.md](references/structured-extraction.md) |
| Seal / stamp recognition | `PaddleOCR(use_seal_recognition=True)` | `paddleocr seal_recognition` | [advanced-tasks.md](references/advanced-tasks.md) |
| Formula / LaTeX extraction | `PaddleOCR` formula pipeline | `paddleocr formula_recognition_pipeline` | [advanced-tasks.md](references/advanced-tasks.md) |
| Multilingual OCR (80+ langs) | `PaddleOCR(lang='ch'/'fr'/'ar'...)` | — | [advanced-tasks.md](references/advanced-tasks.md) |
| Multimodal doc QA (VL) | `PaddleOCR-VL-1.5` (optional, separate install) | `paddleocr doc_vlm` | [vl-model.md](references/vl-model.md) |
| Document to Markdown | `PaddleOCR` doc pipeline | `paddleocr doc2md` | [ocr-pipeline.md](references/ocr-pipeline.md) |
| Chart/diagram parsing | `PaddleOCR` chart pipeline | `paddleocr chart_parsing` | [advanced-tasks.md](references/advanced-tasks.md) |
| Text detection only | `TextDetection` | `paddleocr text_detection` | [ocr-pipeline.md](references/ocr-pipeline.md) |
| Text recognition only | `TextRecognition` | `paddleocr text_recognition` | [ocr-pipeline.md](references/ocr-pipeline.md) |
| Layout detection only | `LayoutDetection` | `paddleocr layout_detection` | [document-reasoning.md](references/document-reasoning.md) |
| PDF batch processing | `pypdfium2` + `PaddleOCR` | — | [ocr-pipeline.md](references/ocr-pipeline.md) |

## Quick Start

### Python

```python
from paddleocr import PaddleOCR

# Initialize OCR pipeline (disable preprocessing for speed)
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang='en'
)

# Run inference — returns iterator of OCRResult objects
result = ocr.predict('document.jpg')
for res in result:
    data = res.json['res']
    texts  = data['rec_texts']      # list[str] — recognized text
    scores = data['rec_scores']      # list[float] — confidence per line
    polys  = data['rec_polys']       # list[list] — 4-point polygons (x,y)
    boxes  = data['rec_boxes']       # list[list] — bounding boxes [x,y,w,h]
    print(texts)

    # Save outputs
    res.save_to_img("output")       # annotated image
    res.save_to_json("output")       # JSON results
```

### CLI

```bash
# Full OCR (text detection + recognition)
paddleocr ocr -i ./document.png \
    --use_doc_orientation_classify False \
    --use_doc_unwarping False \
    --use_textline_orientation False \
    --save_path ./output \
    --device cpu

# Document structure analysis (layout + tables + text)
paddleocr pp_structurev3 -i ./report.png \
    --use_doc_orientation_classify False \
    --use_doc_unwarping False

# Individual modules
paddleocr text_detection -i ./image.png
paddleocr text_recognition -i ./cropped_text.png
paddleocr layout_detection -i ./document.png
paddleocr seal_recognition -i ./stamp.png
paddleocr table_recognition_v2 -i ./table.png
paddleocr formula_recognition_pipeline -i ./equation.png
paddleocr chart_parsing -i ./chart.png
paddleocr doc2md -i ./document.docx
paddleocr doc_vlm -i ./complex_doc.png   # requires PaddleOCR-VL install
```

## Core Patterns

### 1. Full OCR Pipeline (Detection → Recognition)

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,   # disable for speed
    use_doc_unwarping=False,              # disable for speed
    use_textline_orientation=False,       # disable for speed
    lang='en',
    # Model selection (defaults shown):
    # text_detection_model_name="PP-OCRv5_server_det",   # high accuracy
    # text_recognition_model_name="en_PP-OCRv5_mobile_rec",  # fast
    # device="cpu",            # "cpu" | "gpu" | "gpu:0" | "npu"
    # engine=None,             # None (legacy=paddle) | "paddle" | "transformers"
)

result = ocr.predict('document.jpg')
for res in result:
    data = res.json['res']
    texts  = data['rec_texts']       # list[str]
    scores = data['rec_scores']      # list[float]
    polys  = data['rec_polys']       # list[list] — polygon corners [[x,y],...]
    boxes  = data['rec_boxes']       # list[list] — [x, y, w, h]
    
    # Filter by confidence
    for text, score in zip(texts, scores):
        if score > 0.8:
            print(f"{text} ({score:.2f})")
    
    # Save results
    res.save_to_img("output")        # annotated visualization
    res.save_to_json("output")       # JSON with all data
```

### 2. Document Structure Analysis (Layout + Tables + Text + Formulas)

```python
from paddleocr import PPStructureV3

pipeline = PPStructureV3(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    # use_seal_recognition=True,       # enable seal/stamp detection
    # use_table_recognition=True,      # enable table extraction (default True)
    # use_formula_recognition=True,     # enable LaTeX formula extraction (default True)
    # use_chart_recognition=False,      # disable chart parsing (default False)
    # use_region_detection=True,        # detect regions of interest
)

output = pipeline.predict(input='./report.png')
for res in output:
    data = res.json['res']
    
    # Layout detection results
    layout = data['layout_det_res']
    for box in layout['boxes']:
        print(f"  {box['label']} (score={box['score']:.2f}) at {box['coordinate']}")
    # Labels: 'text', 'image', 'paragraph_title', 'doc_title', 'figure_title', etc.
    
    # Overall OCR text
    ocr_data = data['overall_ocr_res']
    texts = ocr_data['rec_texts']
    
    # Save as Markdown (document reconstruction)
    res.save_to_markdown("output")
    res.save_to_json("output")
```

**Note:** `PPStructureV3` requires extra dependencies. Install with:
```bash
pip install "paddleocr[all]"
# or specifically:
pip install "paddlex[ocr]"
```

### 3. Individual Module Usage

```python
# Text detection only (find text regions)
from paddleocr import TextDetection
det = TextDetection()
output = det.predict("document.png")
for res in output:
    polys = res.json['res']['dt_polys']    # detected polygon regions
    scores = res.json['res']['dt_scores']  # detection confidence
    res.save_to_img("./output/")
    res.save_to_json("./output/res.json")

# Text recognition only (read cropped text lines)
from paddleocr import TextRecognition
rec = TextRecognition()
output = rec.predict(input="cropped_line.png")
for res in output:
    text = res.json['res']['rec_text']     # recognized string
    score = res.json['res']['rec_score']   # confidence float

# Layout detection only
from paddleocr import LayoutDetection
layout = LayoutDetection()
output = layout.predict("document.png")
```

### 4. Structured KV Extraction

```python
import re
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang='en'
)

def extract_kv(ocr_lines, patterns: dict) -> dict:
    full_text = '\n'.join(ocr_lines)
    return {k: re.search(p, full_text, re.I).group(1)
            for k, p in patterns.items()
            if re.search(p, full_text, re.I)}

result = ocr.predict('invoice.jpg')
for res in result:
    texts = res.json['res']['rec_texts']
    fields = extract_kv(texts, {
        'invoice_no': r'Invoice\s*No[.:\s]+([A-Z0-9\-]+)',
        'date':       r'Date[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
        'total':      r'Total\s*[\$₦€£]?\s*([\d,]+\.?\d*)',
    })
    print(fields)
```

### 5. Batch PDF Processing

```python
import pypdfium2 as pdfium
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang='en'
)

def pdf_to_images(pdf_path, dpi=200):
    doc = pdfium.PdfDocument(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        bitmap = page.render(scale=dpi/72)
        yield bitmap.to_pil()

for page_num, page_img in enumerate(pdf_to_images('report.pdf')):
    result = ocr.predict(page_img)
    for res in result:
        texts = res.json['res']['rec_texts']
        print(f"Page {page_num+1}: {len(texts)} lines")
```

### 6. Streaming Large Datasets with predict_iter()

```python
ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                use_textline_orientation=False, lang='en')

# predict_iter() returns a generator — lower memory for large batches
for res in ocr.predict_iter(large_image_list):
    texts = res.json['res']['rec_texts']
    process(texts)
```

## Result Object API (OCRResult)

The `predict()` method returns an iterator of `OCRResult` objects. Each has:

| Method / Attribute | Description |
|---|---|
| `res.json` | Dict with key `'res'` containing all results |
| `res.json['res']['rec_texts']` | `list[str]` — recognized text lines |
| `res.json['res']['rec_scores']` | `list[float]` — confidence per line |
| `res.json['res']['rec_polys']` | `list[list]` — 4-corner polygons `[[x,y],...]` |
| `res.json['res']['rec_boxes']` | `list[list]` — bounding boxes `[x, y, w, h]` |
| `res.json['res']['dt_polys']` | `list[list]` — raw detection polygons |
| `res.json['res']['input_path']` | Source file path |
| `res.json['res']['page_index']` | Page number (for PDFs) |
| `res.json['res']['model_settings']` | Dict of pipeline config used |
| `res.print()` | Print results to stdout |
| `res.save_to_img(path)` | Save annotated image |
| `res.save_to_json(path)` | Save JSON results |

For `PPStructureV3`, additional keys:

| Key | Description |
|---|---|
| `res.json['res']['layout_det_res']['boxes']` | Layout regions with `label`, `score`, `coordinate` |
| `res.json['res']['overall_ocr_res']['rec_texts']` | Full-page OCR text |
| `res.save_to_markdown(path)` | Save reconstructed Markdown document |

## CLI Subcommands (v3.5.0)

```bash
paddleocr <subcommand> -i <input> [options]

# Available subcommands:
ocr                             # Full OCR pipeline (detection + recognition)
text_detection                  # Text region detection only
text_recognition                # Text recognition only (cropped lines)
pp_structurev3                  # Document structure (layout + tables + OCR + formulas)
layout_detection                # Layout region detection only
seal_recognition                # Seal/stamp text extraction
table_recognition_v2            # Table structure → HTML
formula_recognition_pipeline    # Formula → LaTeX
chart_parsing                   # Chart/diagram → structured data
doc_preprocessor                # Image preprocessing (orientation + unwarping)
doc_understanding                # Document understanding pipeline
doc_vlm                         # PaddleOCR-VL multimodal (requires extra install)
pp_chatocrv4_doc                # Chat-based OCR QA
pp_doctranslation               # Document translation
doc2md                          # Office docs → Markdown
doc_img_orientation_classification  # Image orientation only
doc_parser                      # Full document parsing
seal_text_detection             # Seal region detection
text_image_unwarping            # Dewarp document images
textline_orientation_classification  # Text line angle only
table_cells_detection           # Table cell detection
table_classification            # Table type classification
table_structure_recognition     # Table structure only
formula_recognition             # Formula detection + recognition
```

Common CLI options:
```bash
-i, --input PATH              # Input image/PDF path or URL (required)
--save_path PATH              # Output directory
--device DEVICE               # "cpu" | "gpu" | "gpu:0" | "npu" (default: auto)
--lang LANG                   # Language code (default: en)
--use_doc_orientation_classify BOOL   # Enable orientation classification
--use_doc_unwarping BOOL             # Enable image dewarping
--use_textline_orientation BOOL      # Enable textline orientation
--ocr_version VERSION         # "PP-OCRv3" | "PP-OCRv4" | "PP-OCRv5"
--engine ENGINE               # None | "paddle" | "paddle_static" | "paddle_dynamic" | "transformers"
--cpu_threads INT             # CPU thread count
--enable_mkldnn BOOL          # Enable MKL-DNN acceleration
```

## Model Selection Guide

| Use Case | Detection Model | Recognition Model | Speed | Accuracy |
|---|---|---|---|---|
| Standard printed text | `PP-OCRv5_server_det` (default) | `en_PP-OCRv5_mobile_rec` (default) | Medium | High |
| Fast/mobile use | `PP-OCRv5_mobile_det` | `en_PP-OCRv5_mobile_rec` | Fast | Good |
| Highest accuracy | `PP-OCRv5_server_det` | `en_PP-OCRv5_server_rec` | Slow | Highest |
| Chinese documents | `PP-OCRv5_server_det` | `ch_PP-OCRv4_rec` | Medium | High |
| Scene text (photos) | `PP-OCRv5_server_det` | `en_PP-OCRv5_server_rec` | Slow | Highest |

Switch models at init:
```python
ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="en_PP-OCRv5_server_rec",
    lang='en'
)
```

## Installation Notes

### Base install (OCR only)
```bash
pip install paddlepaddle paddleocr
```

### Full install (all pipelines including PPStructureV3)
```bash
pip install "paddleocr[all]"
# or: pip install paddlepaddle "paddlex[ocr]"
```

### Specific extras
```bash
pip install "paddleocr[doc-parser]"   # document parsing
pip install "paddleocr[ie]"           # information extraction
pip install "paddleocr[doc2md]"       # Office docs → Markdown (works on Python 3.8+)
pip install "paddleocr[all]"          # everything (requires Python 3.9+)
```

## Important Notes

- **API changed in v3.5.0:** `.ocr()` → `.predict()`. The old `.ocr(img, cls=True)` method is deprecated and `cls` kwarg is removed. Use `.predict(img)` instead.
- **`show_log` removed:** Not a valid parameter in v3.5.0. Remove all `show_log=False` calls.
- **`use_angle_cls` removed:** Use `use_textline_orientation=True` at init time.
- **`use_gpu` renamed:** Use `device="cpu"` or `device="gpu"` parameter.
- **CLI restructured:** Now requires subcommand (`paddleocr ocr -i file.png` instead of `paddleocr --image_dir file.png`).
- **`--image_dir` → `-i`:** CLI input flag changed.
- **Result format changed:** Returns `OCRResult` objects (use `.json['res']`) instead of nested lists.
- **`PPStructure` → `PPStructureV3`:** The old class is replaced. Import from `paddleocr import PPStructureV3`.
- First run downloads models to `~/.paddlex/official_models/` (~200MB total for defaults)
- GPU disabled by default on this host — CPU inference only. Use `device="gpu"` if GPU available.
- `PaddleOCR-VL-1.5` is a **separate** large model (not installed); needed only for multimodal document QA — see [vl-model.md](references/vl-model.md)
- For high-accuracy table extraction, prefer `PPStructureV3` over plain `PaddleOCR`
- **Not suitable for network diagrams or visual layouts** — PaddleOCR extracts text labels only, not shapes/connections/topology. Use a vision/multimodal LLM for diagram analysis.
- **CPU inference can be slow** on large images. Downsample to ~150 DPI for faster results when full resolution isn't needed.

## Migration from v2.x / early v3.x

| Old (v2.x / early v3.x) | New (v3.5.0) | Notes |
|---|---|---|
| `ocr.ocr(img, cls=True)` | `ocr.predict(img)` | `.ocr()` deprecated, `cls` removed |
| `result[0][i][1][0]` (text) | `res.json['res']['rec_texts'][i]` | List access instead of nested tuples |
| `result[0][i][1][1]` (score) | `res.json['res']['rec_scores'][i]` | Direct list access |
| `result[0][i][0]` (bbox) | `res.json['res']['rec_polys'][i]` | Polygon as list of [x,y] points |
| `PaddleOCR(show_log=False)` | `PaddleOCR(...)` | `show_log` removed entirely |
| `PaddleOCR(use_gpu=False)` | `PaddleOCR(device="cpu")` | Renamed parameter |
| `PaddleOCR(use_angle_cls=True)` | `PaddleOCR(use_textline_orientation=True)` | Renamed parameter |
| `PPStructure(show_log=False)` | `PPStructureV3(...)` | Class renamed, `show_log` removed |
| `PPStructure(table=True, ocr=True)` | `PPStructureV3(use_table_recognition=True)` | Param names changed |
| `paddleocr --image_dir ./dir --use_gpu False` | `paddleocr ocr -i ./dir --device cpu` | CLI restructured |
| `region['res']['html']` (table) | `res.save_to_json()` / `res.save_to_markdown()` | Use save methods |

## Scripts

Ready-to-run scripts in `scripts/`:

| Script | Purpose |
|---|---|
| [`scripts/ocr_quick.py`](scripts/ocr_quick.py) | CLI: extract text from any image/PDF |
| [`scripts/table_extract.py`](scripts/table_extract.py) | Extract all tables → CSV files |
| [`scripts/structured_extract.py`](scripts/structured_extract.py) | Invoice / ID / form KV extraction |
| [`scripts/doc_pipeline.py`](scripts/doc_pipeline.py) | Full document understanding pipeline → JSON |

```bash
# Usage examples (use system Python where paddleocr is installed)
python3 scripts/ocr_quick.py document.jpg
python3 scripts/table_extract.py report.pdf --out ./tables/
python3 scripts/structured_extract.py invoice.jpg --type invoice
python3 scripts/doc_pipeline.py contract.pdf --out result.json
```

## References

- [references/quick-start.md](references/quick-start.md) — Installation, first run, common errors
- [references/ocr-pipeline.md](references/ocr-pipeline.md) — Text detection, recognition, orientation, PDF batch
- [references/table-qa.md](references/table-qa.md) — Table detection, HTML export, CSV, pandas QA
- [references/document-reasoning.md](references/document-reasoning.md) — Layout analysis, reading order, LLM reasoning chains
- [references/structured-extraction.md](references/structured-extraction.md) — Forms, invoices, receipts, ID cards, KV pairs
- [references/vl-model.md](references/vl-model.md) — PaddleOCR-VL multimodal QA (installation + usage)
- [references/advanced-tasks.md](references/advanced-tasks.md) — Seals, handwriting, formulas, multilingual, scene text
