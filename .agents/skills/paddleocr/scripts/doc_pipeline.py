#!/usr/bin/env python3
"""
doc_pipeline.py — Full document understanding pipeline.

Runs a complete analysis on any document image or PDF:
  1. Layout analysis (PPStructure)
  2. Text extraction with reading order
  3. Table extraction → DataFrames
  4. Structured field extraction (type-aware)
  5. LLM reasoning / summarization (optional)
  6. Anomaly/completeness check (optional)

Output: comprehensive JSON with all extracted information.

Usage:
    python3 doc_pipeline.py <input> [options]

Examples:
    python3 doc_pipeline.py annual_report.pdf --out result.json
    python3 doc_pipeline.py contract.jpg --summarize --anomaly-check
    python3 doc_pipeline.py invoice.png --type invoice --out invoice_data.json
    python3 doc_pipeline.py document.pdf --qa "What are the key risks?" --summarize

Options:
    --out PATH          Output JSON path (default: <input>_pipeline.json)
    --type TYPE         Document type hint: invoice|receipt|id|contract|report|auto
    --lang LANG         OCR language (default: en)
    --dpi INT           PDF render DPI (default: 200)
    --summarize         Generate document summary (requires ANTHROPIC_API_KEY)
    --qa QUESTION       Answer a specific question (requires ANTHROPIC_API_KEY)
    --anomaly-check     Detect document anomalies
    --no-tables         Skip table extraction (faster)
    --no-layout         Use plain OCR instead of PPStructure (much faster)
    --max-pages INT     Maximum PDF pages to process (default: all)
    --verbose           Print progress to stderr
"""

import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description='Full document understanding pipeline')
    p.add_argument('input', help='Image or PDF file')
    p.add_argument('--out', default=None)
    p.add_argument('--type', default='auto', help='Document type hint')
    p.add_argument('--lang', default='en')
    p.add_argument('--dpi', type=int, default=200)
    p.add_argument('--summarize', action='store_true')
    p.add_argument('--qa', default=None, help='Question to answer')
    p.add_argument('--anomaly-check', action='store_true', dest='anomaly_check')
    p.add_argument('--no-tables', action='store_true', dest='no_tables')
    p.add_argument('--no-layout', action='store_true', dest='no_layout')
    p.add_argument('--max-pages', type=int, default=None, dest='max_pages')
    p.add_argument('--verbose', action='store_true')
    return p.parse_args()


def log(msg, verbose=True):
    if verbose:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr)


# ─── Phase 1: Input normalization ────────────────────────────────────────────

def load_images(input_path: Path, dpi=200, max_pages=None, verbose=False):
    """Load image(s) from file. Returns list of (page_num, numpy_array)."""
    import numpy as np

    suffix = input_path.suffix.lower()
    images = []

    if suffix == '.pdf':
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(input_path))
        n = len(doc) if max_pages is None else min(len(doc), max_pages)
        log(f"PDF: {n} pages to process", verbose)
        for i in range(n):
            page = doc[i]
            bitmap = page.render(scale=dpi / 72)
            img = np.array(bitmap.to_pil())
            images.append((i + 1, img))
        doc.close()
    elif suffix in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'):
        import cv2
        img = cv2.imread(str(input_path))
        if img is None:
            raise ValueError(f"Cannot read image: {input_path}")
        images.append((1, img))
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return images


# ─── Phase 2: Layout analysis ────────────────────────────────────────────────

def analyze_layout(img, lang='en', include_tables=True):
    """Run PPStructure layout analysis on a single image."""
    from paddleocr import PPStructureV3
    engine = PPStructureV3(use_table_recognition=include_tables, use_doc_orientation_classify=False, use_doc_unwarping=False)
    result = engine(img)

    page_data = {
        'titles': [], 'paragraphs': [], 'lists': [],
        'tables': [], 'figures': [], 'formulas': [], 'seals': []
    }

    for block in result:
        btype = block['type']
        bbox = block.get('bbox', [])
        score = block.get('score', 1.0)

        if btype == 'title':
            page_data['titles'].append({'text': block['res'], 'bbox': bbox, 'score': score})
        elif btype == 'text':
            page_data['paragraphs'].append({'text': block['res'], 'bbox': bbox, 'score': score})
        elif btype == 'list':
            page_data['lists'].append({'text': block['res'], 'bbox': bbox, 'score': score})
        elif btype == 'table':
            from io import StringIO
            import pandas as pd
            html = block['res']['html']
            try:
                df = pd.read_html(StringIO(html))[0]
                page_data['tables'].append({
                    'html': html,
                    'shape': list(df.shape),
                    'columns': df.columns.tolist(),
                    'preview': df.head(3).to_dict(orient='records'),
                    'bbox': bbox,
                    'score': score
                })
            except Exception:
                page_data['tables'].append({'html': html, 'bbox': bbox, 'score': score})
        elif btype == 'figure':
            page_data['figures'].append({'bbox': bbox, 'score': score})
        elif btype == 'formula':
            page_data['formulas'].append({'text': block.get('res', ''), 'bbox': bbox})
        elif btype == 'seal':
            page_data['seals'].append({'text': block.get('res', ''), 'bbox': bbox})

    return page_data


def plain_ocr(img, lang='en'):
    """Fallback plain OCR when PPStructure is not needed."""
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang=lang)
    result = ocr.predict(img)
    lines = []
    for res in result:
        data = res.json['res']
        for text, score, poly in zip(data.get('rec_texts', []), data.get('rec_scores', []), data.get('rec_polys', [])):
            lines.append({'text': text, 'confidence': round(score, 4), 'bbox': poly})
    text = '\n'.join(l['text'] for l in lines)
    return {'lines': lines, 'text': text}


# ─── Phase 3: Full-document aggregation ──────────────────────────────────────

def aggregate_pages(pages: list) -> dict:
    """Merge per-page results into one document-level structure."""
    doc = {
        'full_text': '',
        'all_titles': [],
        'all_paragraphs': [],
        'all_tables': [],
        'all_lists': [],
        'all_figures': [],
        'all_formulas': [],
        'all_seals': [],
    }
    text_parts = []
    for page in pages:
        pnum = page['page']
        data = page.get('layout') or {}

        for t in data.get('titles', []):
            doc['all_titles'].append({'page': pnum, **t})
            text_parts.append(t['text'])
        for p in data.get('paragraphs', []):
            doc['all_paragraphs'].append({'page': pnum, **p})
            text_parts.append(p['text'])
        for l in data.get('lists', []):
            doc['all_lists'].append({'page': pnum, **l})
            text_parts.append(l['text'])
        for tbl in data.get('tables', []):
            doc['all_tables'].append({'page': pnum, **tbl})
        doc['all_figures'].extend({'page': pnum, **f} for f in data.get('figures', []))
        doc['all_formulas'].extend({'page': pnum, **f} for f in data.get('formulas', []))
        doc['all_seals'].extend({'page': pnum, **s} for s in data.get('seals', []))

        if 'plain' in page:
            text_parts.append(page['plain'].get('text', ''))

    doc['full_text'] = '\n'.join(text_parts)
    return doc


# ─── Phase 4: LLM reasoning ──────────────────────────────────────────────────

def llm_summarize(full_text: str, doc_type='document') -> str:
    import os, anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content':
            f"Provide a concise executive summary of this {doc_type}. "
            f"Highlight key findings, important values, dates, and parties involved.\n\n"
            f"DOCUMENT:\n{full_text[:8000]}"}]
    )
    return response.content[0].text


def llm_answer(full_text: str, question: str) -> str:
    import os, anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content':
            f"Answer this question based only on the document content below.\n\n"
            f"QUESTION: {question}\n\n"
            f"DOCUMENT:\n{full_text[:8000]}"}]
    )
    return response.content[0].text


def llm_detect_type(full_text: str) -> str:
    import os, anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=30,
        messages=[{'role': 'user', 'content':
            f"What type of document is this? Respond with ONE of: "
            f"invoice, receipt, id, passport, contract, bank_statement, payslip, "
            f"insurance, annual_report, policy, letter, form, certificate, other\n\n"
            f"TEXT:\n{full_text[:500]}"}]
    )
    return response.content[0].text.strip().lower()


def llm_check_anomalies(full_text: str, doc_type: str) -> list[str]:
    import os, anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=512,
        messages=[{'role': 'user', 'content':
            f"Review this {doc_type} for anomalies, errors, missing fields, or inconsistencies. "
            f"List each issue as a bullet point. If clean, say 'No anomalies detected.'\n\n"
            f"DOCUMENT:\n{full_text[:5000]}"}]
    )
    return [l.lstrip('•-– ').strip()
            for l in response.content[0].text.split('\n') if l.strip()]


# ─── Main pipeline ────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    t0 = time.time()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out) if args.out else input_path.parent / f"{input_path.stem}_pipeline.json"
    v = args.verbose

    pipeline_result = {
        'source': str(input_path),
        'processed_at': datetime.now().isoformat(),
        'pipeline_version': '1.0',
        'document_type': args.type,
        'pages': [],
    }

    # Phase 1: Load
    log(f"Loading: {input_path}", v)
    images = load_images(input_path, dpi=args.dpi, max_pages=args.max_pages, verbose=v)
    log(f"Loaded {len(images)} page(s)", v)

    # Phase 2: Per-page analysis
    for page_num, img in images:
        log(f"Analyzing page {page_num}...", v)
        page_data = {'page': page_num}

        if args.no_layout:
            plain = plain_ocr(img, lang=args.lang)
            page_data['plain'] = plain
            log(f"  Plain OCR: {len(plain['lines'])} lines", v)
        else:
            layout = analyze_layout(img, lang=args.lang, include_tables=not args.no_tables)
            page_data['layout'] = layout
            log(f"  Layout: {len(layout['titles'])} titles, "
                f"{len(layout['paragraphs'])} paragraphs, "
                f"{len(layout['tables'])} tables, "
                f"{len(layout['seals'])} seals", v)

        pipeline_result['pages'].append(page_data)

    # Phase 3: Aggregate
    log("Aggregating document...", v)
    doc = aggregate_pages(pipeline_result['pages'])
    pipeline_result['document'] = doc
    pipeline_result['stats'] = {
        'total_pages': len(images),
        'total_tables': len(doc['all_tables']),
        'total_titles': len(doc['all_titles']),
        'total_paragraphs': len(doc['all_paragraphs']),
        'full_text_length': len(doc['full_text']),
        'seals_found': len(doc['all_seals']),
        'formulas_found': len(doc['all_formulas']),
    }
    log(f"Stats: {pipeline_result['stats']}", v)

    # Phase 4: LLM reasoning (optional)
    import os
    has_api_key = bool(os.environ.get('ANTHROPIC_API_KEY'))

    if args.type == 'auto' and has_api_key:
        log("Auto-detecting document type...", v)
        pipeline_result['document_type'] = llm_detect_type(doc['full_text'])
        log(f"Detected type: {pipeline_result['document_type']}", v)

    if args.summarize:
        if not has_api_key:
            log("⚠️  --summarize requires ANTHROPIC_API_KEY", v)
        else:
            log("Generating summary...", v)
            pipeline_result['summary'] = llm_summarize(
                doc['full_text'], pipeline_result['document_type'])
            log("Summary complete", v)

    if args.qa:
        if not has_api_key:
            log("⚠️  --qa requires ANTHROPIC_API_KEY", v)
        else:
            log(f"Answering: {args.qa[:60]}...", v)
            pipeline_result['qa_answer'] = {
                'question': args.qa,
                'answer': llm_answer(doc['full_text'], args.qa)
            }
            log("QA complete", v)

    if args.anomaly_check:
        if not has_api_key:
            log("⚠️  --anomaly-check requires ANTHROPIC_API_KEY", v)
        else:
            log("Checking for anomalies...", v)
            pipeline_result['anomalies'] = llm_check_anomalies(
                doc['full_text'], pipeline_result['document_type'])
            log(f"Anomaly check: {len(pipeline_result['anomalies'])} item(s)", v)

    # Phase 5: Save output
    pipeline_result['elapsed_seconds'] = round(time.time() - t0, 2)
    result_json = json.dumps(pipeline_result, indent=2, ensure_ascii=False, default=str)
    out_path.write_text(result_json, encoding='utf-8')

    log(f"✅ Done in {pipeline_result['elapsed_seconds']}s → {out_path}", v)

    # Print summary to stdout
    print(f"✅ Pipeline complete: {out_path}")
    print(f"   Pages: {pipeline_result['stats']['total_pages']}")
    print(f"   Tables: {pipeline_result['stats']['total_tables']}")
    print(f"   Text length: {pipeline_result['stats']['full_text_length']} chars")
    print(f"   Document type: {pipeline_result['document_type']}")
    if 'summary' in pipeline_result:
        print(f"\n📋 Summary:\n{pipeline_result['summary']}")
    if 'qa_answer' in pipeline_result:
        print(f"\n❓ Q: {pipeline_result['qa_answer']['question']}")
        print(f"💡 A: {pipeline_result['qa_answer']['answer']}")
    if 'anomalies' in pipeline_result:
        print(f"\n⚠️  Anomalies ({len(pipeline_result['anomalies'])}):")
        for a in pipeline_result['anomalies']:
            print(f"   • {a}")


if __name__ == '__main__':
    main()
