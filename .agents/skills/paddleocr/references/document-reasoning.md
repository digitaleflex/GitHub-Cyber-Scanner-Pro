# Document-Level Reasoning & Layout Analysis

Covers: layout analysis, reading order, block classification, LLM reasoning chains, multi-page document understanding, contract analysis, report summarization.

## Layout Analysis with PPStructure

PPStructure classifies document regions into semantic blocks before OCR:

```python
from paddleocr import PPStructureV3
from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes

engine = PPStructureV3(use_table_recognition=True, use_doc_orientation_classify=False, use_doc_unwarping=False)
result = engine('annual_report.jpg')

# Region types: text | title | figure | table | list | formula | seal
for block in result:
    btype = block['type']
    bbox  = block['bbox']        # [x1, y1, x2, y2]
    score = block.get('score', 1.0)
    print(f"[{btype}] @{bbox}  conf={score:.2f}")
    if btype in ('text', 'title', 'list'):
        print(f"  → {block['res']}")
    elif btype == 'table':
        print(f"  → {len(block['res']['html'])} chars of HTML")
```

## Reading-Order Recovery

```python
def recover_reading_order(result: list, page_height: int) -> list:
    """
    Sort layout blocks into natural reading order (columns-aware).
    Uses sorted_layout_boxes from PaddleOCR recovery module.
    """
    from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes
    sorted_blocks = sorted_layout_boxes(result, page_height)
    return sorted_blocks
```

## Document Reconstruction (Markdown)

```python
def reconstruct_document(result: list) -> str:
    """Reconstruct document content as Markdown-like text preserving structure."""
    parts = []
    for block in result:
        btype = block['type']
        if btype == 'title':
            parts.append(f"\n## {block['res']}\n")
        elif btype == 'text':
            parts.append(block['res'])
        elif btype == 'list':
            items = block['res'].split('\n')
            parts.extend(f"- {item}" for item in items if item.strip())
        elif btype == 'table':
            parts.append('\n[TABLE]\n' + block['res']['html'] + '\n[/TABLE]\n')
        elif btype == 'figure':
            parts.append(f'\n[FIGURE @ {block["bbox"]}]\n')
        elif btype == 'formula':
            parts.append(f'\n[FORMULA: {block.get("res", "")}]\n')
    return '\n'.join(parts)
```

## LLM Document Reasoning Chain

### Step 1: Extract full document content
```python
def extract_document_content(image_path: str) -> dict:
    """Full structured extraction from a single-page document."""
    engine = PPStructureV3(use_table_recognition=True, use_doc_orientation_classify=False, use_doc_unwarping=False)
    result = engine(image_path)

    content = {
        'titles': [],
        'paragraphs': [],
        'tables': [],
        'lists': [],
        'figures': [],
        'formulas': [],
        'seals': [],
    }

    for block in result:
        btype = block['type']
        if btype == 'title':
            content['titles'].append(block['res'])
        elif btype == 'text':
            content['paragraphs'].append(block['res'])
        elif btype == 'table':
            content['tables'].append(block['res']['html'])
        elif btype == 'list':
            content['lists'].append(block['res'])
        elif btype == 'formula':
            content['formulas'].append(block.get('res', ''))
        elif btype == 'seal':
            content['seals'].append(block.get('res', ''))

    return content
```

### Step 2: Send to LLM for reasoning
```python
import anthropic
import json

def document_reasoning(content: dict, question: str, client=None) -> str:
    """Ask an LLM to reason over extracted document content."""
    if client is None:
        client = anthropic.Anthropic()

    # Build context string
    ctx_parts = []
    if content['titles']:
        ctx_parts.append("TITLES:\n" + '\n'.join(content['titles']))
    if content['paragraphs']:
        ctx_parts.append("PARAGRAPHS:\n" + '\n\n'.join(content['paragraphs']))
    if content['tables']:
        for i, tbl in enumerate(content['tables']):
            ctx_parts.append(f"TABLE {i+1}:\n{tbl}")
    if content['lists']:
        ctx_parts.append("LISTS:\n" + '\n'.join(content['lists']))

    context = '\n\n---\n\n'.join(ctx_parts)

    prompt = f"""You are an expert document analyst. Analyze the document content below and answer the question.

DOCUMENT CONTENT:
{context}

QUESTION: {question}

Provide a precise, well-reasoned answer based only on the document content above."""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text
```

### Step 3: One-shot document QA
```python
def ask_document(image_path: str, question: str) -> str:
    """End-to-end: image → OCR → LLM → answer."""
    content = extract_document_content(image_path)
    return document_reasoning(content, question)

# Examples
answer = ask_document('contract.jpg', 'What is the payment due date?')
answer = ask_document('report.jpg', 'What was the total revenue in Q4?')
answer = ask_document('form.jpg', 'Who signed this document?')
```

## Contract Analysis

```python
CONTRACT_FIELDS = [
    'parties', 'effective_date', 'expiry_date', 'payment_terms',
    'governing_law', 'termination_clause', 'penalties', 'signatures'
]

def analyze_contract(image_path: str, client=None) -> dict:
    """Extract key contract fields."""
    if client is None:
        client = anthropic.Anthropic()

    content = extract_document_content(image_path)
    full_text = '\n'.join(content['paragraphs'])

    prompt = f"""Extract the following fields from this contract text.
Return a JSON object with these keys: {CONTRACT_FIELDS}
Use null for any field not found.

CONTRACT TEXT:
{full_text}

Return only valid JSON, no explanation."""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )

    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {'raw': response.content[0].text}
```

## Multi-Page Document Reasoning

```python
import pypdfium2 as pdfium
import numpy as np

def reason_over_pdf(pdf_path: str, question: str, client=None) -> str:
    """Reason over an entire multi-page PDF document."""
    if client is None:
        client = anthropic.Anthropic()

    engine = PPStructureV3(use_table_recognition=True, use_doc_orientation_classify=False, use_doc_unwarping=False)
    doc = pdfium.PdfDocument(pdf_path)
    all_content = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        bitmap = page.render(scale=200/72)
        img = np.array(bitmap.to_pil())
        result = engine(img)

        page_text = []
        for block in result:
            if block['type'] in ('text', 'title', 'list'):
                page_text.append(block['res'])
            elif block['type'] == 'table':
                page_text.append(f"[TABLE]\n{block['res']['html']}")
        all_content.append(f"=== PAGE {page_num + 1} ===\n" + '\n'.join(page_text))

    doc.close()
    full_document = '\n\n'.join(all_content)

    # Truncate to avoid token limits (keep first + last sections)
    if len(full_document) > 80000:
        half = 40000
        full_document = full_document[:half] + '\n\n[... truncated ...]\n\n' + full_document[-half:]

    prompt = f"""Analyze this multi-page document and answer the question.

DOCUMENT:
{full_document}

QUESTION: {question}"""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=2048,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text
```

## Report Summarization

```python
def summarize_document(image_path_or_pdf: str, style='executive', client=None) -> str:
    """
    Summarize a document.
    style: 'executive' | 'technical' | 'bullet' | 'one-liner'
    """
    if client is None:
        client = anthropic.Anthropic()

    style_prompts = {
        'executive': 'Write a 3-paragraph executive summary for a C-suite audience.',
        'technical': 'Write a detailed technical summary covering all key findings, methods, and results.',
        'bullet':    'Summarize as a structured bullet-point list with main sections and key points.',
        'one-liner': 'Summarize in one sentence (max 30 words).',
    }

    content = extract_document_content(image_path_or_pdf)
    full_text = '\n\n'.join(content['paragraphs'])

    prompt = f"""{style_prompts.get(style, style_prompts['executive'])}

DOCUMENT CONTENT:
{full_text}"""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text
```

## Comparison Across Multiple Documents

```python
def compare_documents(image_paths: list[str], aspect: str, client=None) -> str:
    """Compare a specific aspect across multiple documents."""
    if client is None:
        client = anthropic.Anthropic()

    excerpts = []
    for i, path in enumerate(image_paths):
        content = extract_document_content(path)
        text = '\n'.join(content['paragraphs'][:10])  # first 10 paragraphs
        excerpts.append(f"DOCUMENT {i+1} ({path}):\n{text}")

    all_docs = '\n\n---\n\n'.join(excerpts)

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': f"""Compare the following documents regarding: {aspect}

{all_docs}

Provide a structured comparison table or analysis."""}]
    )
    return response.content[0].text
```

## Anomaly / Inconsistency Detection

```python
def detect_document_anomalies(image_path: str, doc_type='financial', client=None) -> list[str]:
    """Detect inconsistencies, missing fields, or anomalies in a document."""
    if client is None:
        client = anthropic.Anthropic()

    content = extract_document_content(image_path)
    full_text = '\n\n'.join(content['paragraphs'] + content['lists'])

    prompts = {
        'financial': 'Check for: math errors, missing totals, inconsistent dates, unsigned sections, unusual amounts.',
        'contract':  'Check for: missing signatures, blank clauses, contradictory terms, missing dates.',
        'form':      'Check for: empty required fields, invalid formats, inconsistent entries.',
        'id':        'Check for: expiry, photo match indicators, security features mentioned.',
    }

    prompt = f"""Review this {doc_type} document for anomalies, errors, and inconsistencies.
{prompts.get(doc_type, '')}

DOCUMENT:
{full_text}

List each anomaly found as a bullet point. If none found, say "No anomalies detected." """

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=512,
        messages=[{'role': 'user', 'content': prompt}]
    )
    lines = response.content[0].text.strip().split('\n')
    return [l.lstrip('•- ').strip() for l in lines if l.strip()]
```
