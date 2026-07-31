# PaddleOCR-VL Multimodal Model Reference

**⚠️ v3.5.0 API Update:** Code examples below may use the deprecated `.ocr()` method and `result[0]` access pattern. In v3.5.0, use `.predict()` and access results via `res.json[res]`. See [ocr-pipeline.md](ocr-pipeline.md) for the migration guide. Key changes:
- `ocr.ocr(img)` → `ocr.predict(img)`
- `result[0][i][1][0]` (text) → `res.json[res][rec_texts][i]`
- `result[0][i][1][1]` (score) → `res.json[res][rec_scores][i]`
- `result[0][i][0]` (bbox) → `res.json[res][rec_polys][i]`
- `for line in (result[0] or []): line[1][0]` → `for res in result: for text, score in zip(res.json[res][rec_texts], res.json[res][rec_scores])`

Covers: when to use VL, installation, visual document QA, chart understanding, scene text reasoning, comparison with standard OCR.

## What Is PaddleOCR-VL?

PaddleOCR-VL-1.5 is a **multimodal vision-language model** — it processes both image pixels and text in one model pass. Unlike standard PaddleOCR which runs detection → recognition as separate steps, VL can:

- Answer open-ended questions about a document visually
- Understand charts, graphs, and infographics without numeric extraction
- Reason about spatial relationships ("what is above the signature?")
- Handle degraded, complex, or artistic text that defeats standard det+rec
- Perform document QA from raw image without intermediate text extraction
- Understand document context holistically (e.g., "is this a contract or a receipt?")

## When to Use VL vs Standard PaddleOCR

| Scenario | Use Standard OCR | Use VL |
|---|---|---|
| Extract all text from clean scan | ✅ | ❌ (overkill) |
| Parse known template (invoice, ID) | ✅ | ❌ |
| Table → CSV | ✅ | ❌ |
| Batch process 100+ pages | ✅ | ❌ (slow, large) |
| "What does this chart show?" | ❌ | ✅ |
| "Summarize the key risks in this doc" | ❌ | ✅ |
| Degraded, artistic, or curved text | ❌ | ✅ |
| Spatial reasoning ("what's next to X") | ❌ | ✅ |
| Unknown document type classification | ❌ | ✅ |
| Multi-language mixed in one document | ⚠️ | ✅ |

## Installation (Not Yet Installed on This Host)

```bash
# VL model requires additional dependencies
pip install paddleocr[vl]

# Or manually:
pip install paddlenlp>=3.0.0
pip install paddleocr>=3.5.0
```

**Note:** PaddleOCR-VL-1.5 requires ~4–8GB disk and ~8GB RAM minimum. On this host (macOS ARM64, CPU only), inference will be slow (~30–120s per image).

## Basic VL Usage

```python
from paddleocr import PaddleOCR

# Initialize in VL mode
ocr = PaddleOCR(
    use_vl_model=True,             # enable VL model
    vl_model_name='PP-VL-1.5',    # model variant
    
)

# Visual document QA
result = ocr.chat(
    image='financial_report.jpg',
    question='What is the total revenue reported in this document?'
)
print(result['answer'])

# Free-form description
result = ocr.chat(
    image='chart.png',
    question='Describe what this chart shows and identify any trends.'
)
```

## Chart & Graph Understanding

```python
def analyze_chart(image_path: str, client_type='vl') -> dict:
    """
    Analyze a chart image.
    client_type: 'vl' uses PaddleOCR-VL; 'llm' uses Claude vision API.
    """
    if client_type == 'llm':
        # Recommended: use Claude vision directly for charts (faster, better)
        import anthropic
        import base64
        from pathlib import Path

        client = anthropic.Anthropic()
        img_data = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        ext = Path(image_path).suffix.lstrip('.').replace('jpg', 'jpeg')

        response = client.messages.create(
            model='claude-opus-4-5',
            max_tokens=1024,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': f'image/{ext}', 'data': img_data}},
                    {'type': 'text', 'text': '''Analyze this chart/graph. Return JSON:
{
  "chart_type": "bar|line|pie|scatter|table|mixed",
  "title": "...",
  "x_axis": "...",
  "y_axis": "...",
  "data_series": [...],
  "key_findings": [...],
  "trend": "..."
}'''}
                ]
            }]
        )
        import json
        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {'raw': response.content[0].text}
```

## Claude Vision as VL Alternative (Recommended)

On this host, use Claude's vision API directly instead of installing the heavy VL model. Faster, more capable, no extra install:

```python
import anthropic
import base64
from pathlib import Path


def visual_document_qa(image_path: str, question: str) -> str:
    """
    Answer questions about a document image using Claude vision.
    Use this when PaddleOCR-VL is not installed.
    """
    client = anthropic.Anthropic()
    img_bytes = Path(image_path).read_bytes()
    img_b64 = base64.standard_b64encode(img_bytes).decode()

    ext = Path(image_path).suffix.lower().lstrip('.')
    media_type_map = {'jpg': 'jpeg', 'jpeg': 'jpeg', 'png': 'png', 'gif': 'gif', 'webp': 'webp'}
    media_type = f"image/{media_type_map.get(ext, 'jpeg')}"

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {'type': 'base64', 'media_type': media_type, 'data': img_b64}
                },
                {'type': 'text', 'text': question}
            ]
        }]
    )
    return response.content[0].text


def classify_document(image_path: str) -> str:
    """Identify what type of document an image is."""
    return visual_document_qa(image_path,
        'What type of document is this? (e.g., invoice, receipt, ID card, contract, bank statement, payslip, report, form, letter). Respond with the document type and a 1-sentence reason.')


def extract_all_fields_visually(image_path: str) -> dict:
    """Extract all meaningful fields from any document image using vision."""
    import json
    client = anthropic.Anthropic()
    img_b64 = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
    ext = Path(image_path).suffix.lower().lstrip('.')
    media_type = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=2048,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': img_b64}},
                {'type': 'text', 'text': '''Extract ALL meaningful information from this document.
Return a JSON object with appropriate keys for every field visible.
Include names, dates, amounts, IDs, addresses, terms, signatures present (yes/no), etc.
Use null for illegible fields. Return only valid JSON.'''}
            ]
        }]
    )
    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {'raw': response.content[0].text}
```

## Hybrid Pipeline: OCR + VL/Vision

Best of both worlds — use OCR for text accuracy, vision for reasoning:

```python
def hybrid_document_understanding(image_path: str, question: str) -> dict:
    """
    Phase 1: Extract precise text with PaddleOCR
    Phase 2: Reason about the document with Claude vision
    """
    import anthropic, base64, json
    from pathlib import Path
    from paddleocr import PaddleOCR

    # Phase 1: Precise text extraction
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    ocr_result = ocr.predict(image_path)
    extracted_text = '\n'.join(l[1][0] for l in (ocr_result[0] or []))

    # Phase 2: Vision + text reasoning
    client = anthropic.Anthropic()
    img_b64 = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
    ext = Path(image_path).suffix.lower().lstrip('.')
    media_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': img_b64}},
                {'type': 'text', 'text': f"""I have extracted the following text from this document via OCR:

--- OCR TEXT ---
{extracted_text}
--- END OCR TEXT ---

Using both the image and the OCR text above, answer this question:
{question}

Prefer OCR text for specific values (numbers, dates, names) and the image for layout/structure understanding."""}
            ]
        }]
    )

    return {
        'answer': response.content[0].text,
        'ocr_text': extracted_text,
        'image_path': image_path
    }
```

## VL Use Case Examples

```python
# Document type classification
doc_type = visual_document_qa('unknown.jpg',
    'What type of document is this? Return one of: invoice, receipt, contract, ID, passport, bank_statement, payslip, report, form, letter, unknown')

# Signature detection
has_sig = visual_document_qa('contract.jpg',
    'Does this document contain any signatures? Reply yes or no, and describe their location.')

# Damage / quality assessment
quality = visual_document_qa('old_scan.jpg',
    'Assess the quality of this scanned document. Are there tears, stains, folds, or low contrast areas that might affect OCR accuracy?')

# Chart data extraction
chart_data = visual_document_qa('monthly_sales.png',
    'Extract all data points from this chart as a JSON array of {label, value} objects.')

# Infographic understanding
info = visual_document_qa('process_diagram.jpg',
    'Describe the process or workflow shown in this diagram step by step.')

# Cross-reference check
check = visual_document_qa('invoice.jpg',
    'Does the amount in words match the numeric amount on this invoice?')
```
