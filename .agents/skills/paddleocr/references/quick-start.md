# Quick Start Reference

## Installation

### Base install (OCR pipeline only)
```bash
pip install paddlepaddle paddleocr
```

### Full install (all pipelines including PPStructureV3)
```bash
pip install "paddleocr[all]"
```

### Specific extras
```bash
pip install "paddleocr[doc2md]"       # Office docs → Markdown (Python 3.8+)
pip install "paddleocr[doc-parser]"   # Document parsing (Python 3.9+)
pip install "paddleocr[ie]"          # Information extraction (Python 3.9+)
pip install "paddleocr[all]"         # Everything (Python 3.9+)
```

### PaddlePaddle
```bash
# CPU
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# GPU (CUDA 11.8 example)
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
```

**PaddleOCR 3.x requires PaddlePaddle 3.0+**

## First Run

### Python
```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    lang='en'
)

result = ocr.predict('./document.png')
for res in result:
    res.print()
    res.save_to_img("output")
    res.save_to_json("output")
```

First run downloads models to `~/.paddlex/official_models/` (~200MB).

### CLI
```bash
# Full OCR
paddleocr ocr -i ./document.png \
    --use_doc_orientation_classify False \
    --use_doc_unwarping False \
    --use_textline_orientation False

# Document structure
paddleocr pp_structurev3 -i ./report.png \
    --use_doc_orientation_classify False \
    --use_doc_unwarping False

# Individual modules
paddleocr text_detection -i ./image.png
paddleocr text_recognition -i ./cropped_text.png
```

## Common Errors

### `ValueError: Unknown argument: show_log`
PaddleOCR v3.5.0 removed `show_log`. Remove it from your PaddleOCR() call.

### `TypeError: PaddleOCR.predict() got an unexpected keyword argument 'cls'`
The `cls` parameter was removed in v3.5.0. Use `use_textline_orientation=True` at init instead.

### `ValueError: Unknown argument: use_angle_cls`
Renamed to `use_textline_orientation`. Replace all occurrences.

### `ValueError: Unknown argument: use_gpu`
Renamed to `device`. Use `device="cpu"` or `device="gpu"`.

### `DeprecationWarning: Please use 'predict' instead`
The `.ocr()` method is deprecated. Switch to `.predict()`.

### `AttributeError: 'list' object has no attribute ...`
The result format changed. Use `res.json['res']` to access data instead of `result[0][i][1][0]`.

### `DependencyError: PP-StructureV3 requires additional dependencies`
Install extras: `pip install "paddleocr[all]"` or `pip install "paddlex[ocr]"`

### `paddleocr: error: argument subcommand: invalid choice`
CLI now requires a subcommand. Use `paddleocr ocr -i file.png` instead of `paddleocr --image_dir file.png`.

### Slow inference on large images
CPU inference can be slow on high-res images. Options:
- Downsample: render PDFs at 150 DPI instead of 300
- Use `--text_det_limit_side_len 736` to limit detection resolution
- Use mobile models: `text_detection_model_name="PP-OCRv5_mobile_det"`
