#!/usr/bin/env python3
"""
table_extract.py — Extract all tables from images or PDFs as CSV/Excel/HTML.

Usage:
    python3 table_extract.py <image_or_pdf> [options]

Examples:
    python3 table_extract.py report.pdf --out ./tables/
    python3 table_extract.py statement.jpg --format excel
    python3 table_extract.py document.png --format html --qa "What is the total?"

Options:
    --out DIR         Output directory (default: ./tables_output/)
    --format FORMAT   Output format: csv|excel|html|json (default: csv)
    --qa QUESTION     Ask a question about the extracted tables (requires ANTHROPIC_API_KEY)
    --dpi INT         DPI for PDF rendering (default: 200)
    --show            Print table contents to stdout
    --merge           Merge all tables into one file (Excel: sheets, CSV: concatenated)
"""

import sys
import json
import argparse
from pathlib import Path
from io import StringIO


def parse_args():
    p = argparse.ArgumentParser(description='Table extraction from documents')
    p.add_argument('input', help='Image or PDF file')
    p.add_argument('--out', default='./tables_output', help='Output directory')
    p.add_argument('--format', choices=['csv', 'excel', 'html', 'json'], default='csv')
    p.add_argument('--qa', default=None, help='Question to ask about the tables')
    p.add_argument('--dpi', type=int, default=200)
    p.add_argument('--show', action='store_true', help='Print tables to stdout')
    p.add_argument('--merge', action='store_true', help='Merge all tables into one file')
    return p.parse_args()


def extract_tables_from_image(img_input):
    """Run PPStructure on an image and return list of HTML table strings + bboxes."""
    from paddleocr import PPStructureV3
    engine = PPStructureV3(use_table_recognition=True, use_doc_orientation_classify=False, use_doc_unwarping=False)
    result = engine(img_input)
    tables = []
    for block in result:
        if block['type'] == 'table':
            tables.append({
                'html': block['res']['html'],
                'bbox': block.get('bbox', []),
                'score': block.get('score', 1.0)
            })
    return tables


def html_to_df(html: str):
    import pandas as pd
    dfs = pd.read_html(StringIO(html))
    return dfs[0] if dfs else None


def clean_df(df):
    import pandas as pd
    df = df.dropna(how='all').dropna(axis=1, how='all')
    # Promote first row to header if all strings
    if df.shape[0] > 1 and df.iloc[0].apply(lambda x: isinstance(x, str)).all():
        df.columns = df.iloc[0].tolist()
        df = df[1:].reset_index(drop=True)
    return df


def save_tables(tables, out_dir: Path, fmt: str, source_name: str, merge=False):
    import pandas as pd

    out_dir.mkdir(parents=True, exist_ok=True)
    dfs = []

    for i, tbl in enumerate(tables):
        df = html_to_df(tbl['html'])
        if df is None:
            print(f"  ⚠️  Table {i+1}: could not parse HTML", file=sys.stderr)
            continue
        df = clean_df(df)
        dfs.append(df)

        if not merge:
            out_base = out_dir / f"{source_name}_table_{i+1}"
            if fmt == 'csv':
                path = out_base.with_suffix('.csv')
                df.to_csv(path, index=False)
            elif fmt == 'excel':
                path = out_base.with_suffix('.xlsx')
                df.to_excel(path, index=False)
            elif fmt == 'html':
                path = out_base.with_suffix('.html')
                path.write_text(tbl['html'], encoding='utf-8')
            elif fmt == 'json':
                path = out_base.with_suffix('.json')
                path.write_text(df.to_json(orient='records', indent=2), encoding='utf-8')
            print(f"  ✅ Table {i+1} ({df.shape[0]}r×{df.shape[1]}c) → {path}")

    if merge and dfs:
        if fmt == 'excel':
            path = out_dir / f"{source_name}_all_tables.xlsx"
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                for j, df in enumerate(dfs):
                    df.to_excel(writer, sheet_name=f'Table_{j+1}', index=False)
            print(f"  ✅ Merged {len(dfs)} tables → {path}")
        elif fmt == 'csv':
            combined = pd.concat(dfs, ignore_index=True)
            path = out_dir / f"{source_name}_all_tables.csv"
            combined.to_csv(path, index=False)
            print(f"  ✅ Merged {len(dfs)} tables → {path}")
        elif fmt == 'json':
            all_data = [df.to_dict(orient='records') for df in dfs]
            path = out_dir / f"{source_name}_all_tables.json"
            path.write_text(json.dumps(all_data, indent=2), encoding='utf-8')
            print(f"  ✅ Merged {len(dfs)} tables → {path}")

    return dfs


def table_qa(dfs, question: str):
    """Answer a question about extracted tables using Claude."""
    import os
    import anthropic
    import pandas as pd

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set. Cannot run table QA.", file=sys.stderr)
        return

    client = anthropic.Anthropic(api_key=api_key)

    table_context = []
    for i, df in enumerate(dfs):
        try:
            md = df.to_markdown(index=False)
        except ImportError:
            md = df.to_string(index=False)
        table_context.append(f"TABLE {i+1}:\n{md}")

    context = '\n\n'.join(table_context)
    prompt = f"""You are a data analyst. Answer the question based ONLY on the tables below.

{context}

QUESTION: {question}

Give a precise answer referencing specific values from the tables."""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=512,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text


def main():
    args = parse_args()
    input_path = Path(args.input)
    out_dir = Path(args.out)

    if not input_path.exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    all_tables = []
    all_dfs = []
    source_name = input_path.stem

    if input_path.suffix.lower() == '.pdf':
        import pypdfium2 as pdfium
        import numpy as np
        doc = pdfium.PdfDocument(str(input_path))
        total_pages = len(doc)
        print(f"Processing PDF: {input_path} ({total_pages} pages)", file=sys.stderr)

        for page_num in range(total_pages):
            page = doc[page_num]
            bitmap = page.render(scale=args.dpi / 72)
            img = np.array(bitmap.to_pil())
            print(f"  Scanning page {page_num + 1}/{total_pages}...", file=sys.stderr)
            page_tables = extract_tables_from_image(img)
            all_tables.extend(page_tables)
            print(f"  → {len(page_tables)} table(s) found", file=sys.stderr)
        doc.close()
    else:
        print(f"Processing image: {input_path}", file=sys.stderr)
        all_tables = extract_tables_from_image(str(input_path))

    print(f"\nTotal tables found: {len(all_tables)}", file=sys.stderr)

    if not all_tables:
        print("No tables detected.", file=sys.stderr)
        sys.exit(0)

    if args.show:
        import pandas as pd
        for i, tbl in enumerate(all_tables):
            df = html_to_df(tbl['html'])
            if df is not None:
                print(f"\n{'='*60}\nTABLE {i+1} ({df.shape[0]}r×{df.shape[1]}c)\n{'='*60}")
                print(df.to_string())
        print()

    all_dfs = save_tables(all_tables, out_dir, args.format, source_name, args.merge)

    if args.qa and all_dfs:
        print(f"\n📊 QA: {args.qa}", file=sys.stderr)
        answer = table_qa(all_dfs, args.qa)
        if answer:
            print(f"\nAnswer: {answer}")


if __name__ == '__main__':
    main()
