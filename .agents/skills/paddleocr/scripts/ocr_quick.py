#!/usr/bin/env python3
"""
ocr_quick.py — Fast text extraction from any image or PDF (PaddleOCR 3.5.0+).

Usage:
    python3 ocr_quick.py <image_or_pdf> [options]

Examples:
    python3 ocr_quick.py document.jpg
    python3 ocr_quick.py report.pdf --lang en --out output.txt
    python3 ocr_quick.py scan.png --format json --min-conf 0.85
    python3 ocr_quick.py ./docs/ --batch --out ./results/

Options:
    --lang LANG         Language code (default: en)
    --out PATH          Output file path (default: stdout)
    --format FORMAT     Output format: text|json|tsv (default: text)
    --min-conf FLOAT    Minimum confidence threshold 0.0–1.0 (default: 0.0)
    --batch             Process all images in a directory
    --dpi INT           DPI for PDF rendering (default: 200)
    --no-orient         Disable textline orientation correction
    --annotate          Save annotated image with bounding boxes
"""

import sys
import json
import argparse
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description='Quick OCR extraction')
    p.add_argument('input', help='Image file, PDF, or directory (with --batch)')
    p.add_argument('--lang', default='en', help='Language code (default: en)')
    p.add_argument('--out', default=None, help='Output file path')
    p.add_argument('--format', choices=['text', 'json', 'tsv'], default='text')
    p.add_argument('--min-conf', type=float, default=0.0, dest='min_conf')
    p.add_argument('--batch', action='store_true', help='Process entire directory')
    p.add_argument('--dpi', type=int, default=200, help='PDF render DPI')
    p.add_argument('--no-orient', action='store_true', dest='no_orient')
    p.add_argument('--annotate', action='store_true', help='Save annotated image')
    return p.parse_args()


def init_ocr(lang='en', orient=True):
    from paddleocr import PaddleOCR
    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=orient,
        lang=lang
    )


def ocr_image(ocr, image_input, min_conf=0.0):
    """Run OCR on an image path or PIL Image. Returns list of dicts."""
    result = ocr.predict(image_input)
    lines = []
    for res in result:
        data = res.json['res']
        texts = data.get('rec_texts', [])
        scores = data.get('rec_scores', [])
        polys = data.get('rec_polys', [])
        boxes = data.get('rec_boxes', [])
        for i, (text, score) in enumerate(zip(texts, scores)):
            if score >= min_conf:
                line = {
                    'text': text,
                    'confidence': round(score, 4),
                    'bbox': polys[i] if i < len(polys) else [],
                    'box': boxes[i] if i < len(boxes) else []
                }
                lines.append(line)
    return lines


def ocr_pdf(ocr, pdf_path, dpi=200, min_conf=0.0):
    """OCR all pages of a PDF. Returns list of page results."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        bitmap = page.render(scale=dpi / 72)
        img = bitmap.to_pil()
        lines = ocr_image(ocr, img, min_conf)
        pages.append({'page': page_num + 1, 'lines': lines})
        print(f"  Page {page_num + 1}/{len(doc)}: {len(lines)} lines", file=sys.stderr)
    doc.close()
    return pages


def format_results(results, fmt='text'):
    if fmt == 'json':
        return json.dumps(results, indent=2, ensure_ascii=False)
    elif fmt == 'tsv':
        rows = ['x\ty\tw\th\ttext\tconf']
        for item in (results if isinstance(results, list) else []):
            if 'lines' in item:  # PDF page
                for line in item['lines']:
                    rows.append(_line_to_tsv(line))
            elif 'text' in item:
                rows.append(_line_to_tsv(item))
        return '\n'.join(rows)
    else:  # text
        if isinstance(results, list) and results and 'lines' in results[0]:
            # PDF multi-page
            parts = []
            for page in results:
                parts.append(f'=== PAGE {page["page"]} ===')
                parts.extend(l['text'] for l in page['lines'])
            return '\n'.join(parts)
        elif isinstance(results, list):
            return '\n'.join(r['text'] for r in results)
        return str(results)


def _line_to_tsv(line):
    bbox = line.get('bbox', [[0,0],[0,0],[0,0],[0,0]])
    if len(bbox) >= 2:
        x = int(bbox[0][0]); y = int(bbox[0][1])
        w = int(bbox[2][0] - bbox[0][0]) if len(bbox) > 2 else 0
        h = int(bbox[2][1] - bbox[0][1]) if len(bbox) > 2 else 0
    else:
        x = y = w = h = 0
    return f"{x}\t{y}\t{w}\t{h}\t{line['text']}\t{line['confidence']}"


def save_annotated(image_path, results, ocr_instance):
    """Use PaddleOCR's built-in save_to_img for annotated output."""
    import tempfile, os
    result = ocr_instance.predict(image_path)
    for res in result:
        out = Path(image_path).stem + '_annotated.jpg'
        res.save_to_img(str(Path.cwd()))
        # PaddleOCR saves to output/ directory by default
        print(f"✅ Annotated image saved", file=sys.stderr)


def main():
    args = parse_args()
    ocr = init_ocr(lang=args.lang, orient=not args.no_orient)

    input_path = Path(args.input)
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

    if args.batch:
        if not input_path.is_dir():
            print(f"❌ --batch requires a directory, got: {input_path}", file=sys.stderr)
            sys.exit(1)
        out_dir = Path(args.out) if args.out else input_path / 'ocr_results'
        out_dir.mkdir(parents=True, exist_ok=True)
        files = [f for f in input_path.rglob('*') if f.suffix.lower() in IMAGE_EXTS]
        print(f"Processing {len(files)} files...", file=sys.stderr)
        for f in files:
            results = ocr_image(ocr, str(f), args.min_conf)
            output = format_results(results, args.format)
            ext = '.json' if args.format == 'json' else '.tsv' if args.format == 'tsv' else '.txt'
            (out_dir / f.stem).with_suffix(ext).write_text(output, encoding='utf-8')
            print(f"✅ {f.name} → {len(results)} lines", file=sys.stderr)
        return

    # Single file
    if not input_path.exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing: {input_path}", file=sys.stderr)

    if input_path.suffix.lower() == '.pdf':
        results = ocr_pdf(ocr, str(input_path), dpi=args.dpi, min_conf=args.min_conf)
    elif input_path.suffix.lower() in IMAGE_EXTS:
        results = ocr_image(ocr, str(input_path), args.min_conf)
        if args.annotate:
            save_annotated(str(input_path), results, ocr)
    else:
        print(f"❌ Unsupported file type: {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    output = format_results(results, args.format)

    if args.out:
        Path(args.out).write_text(output, encoding='utf-8')
        print(f"✅ Output saved: {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
