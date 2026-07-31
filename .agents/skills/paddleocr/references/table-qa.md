# Table Extraction & Question Answering

Covers: table detection, HTML/CSV export, multi-table documents, pandas QA, cross-table reasoning.

## Table Detection with PPStructure

```python
from paddleocr import PPStructureV3
import pandas as pd
from io import StringIO

engine = PPStructureV3(use_table_recognition=True, use_doc_orientation_classify=False, use_doc_unwarping=False)
result = engine('financial_report.jpg')

tables = [r for r in result if r['type'] == 'table']
print(f"Found {len(tables)} table(s)")
```

## HTML Table Output

```python
for i, table in enumerate(tables):
    html = table['res']['html']
    print(f"--- Table {i+1} ---")
    print(html)
```

## Table → Pandas DataFrame

```python
def table_to_df(table_region: dict) -> pd.DataFrame:
    """Convert a PPStructure table region to a pandas DataFrame."""
    html = table_region['res']['html']
    dfs = pd.read_html(StringIO(html))
    return dfs[0] if dfs else pd.DataFrame()

for i, table in enumerate(tables):
    df = table_to_df(table)
    print(f"\n--- Table {i+1} ({df.shape[0]}r × {df.shape[1]}c) ---")
    print(df.to_string())
```

## Table → CSV

```python
from pathlib import Path

def export_tables_to_csv(tables: list, output_dir: str):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, table in enumerate(tables):
        df = table_to_df(table)
        csv_path = out / f'table_{i+1}.csv'
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved: {csv_path}")
```

## Table → Excel (multi-sheet)

```python
def tables_to_excel(tables: list, output_path='tables.xlsx'):
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for i, table in enumerate(tables):
            df = table_to_df(table)
            df.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)
    print(f"✅ Excel saved: {output_path}")
```

## Table Question Answering (Pandas)

```python
def table_qa(df: pd.DataFrame, question: str) -> str:
    """
    Rule-based table QA for common financial/data questions.
    For advanced NL QA, pair with an LLM (see document-reasoning.md).
    """
    q = question.lower()

    # Max/Min queries
    if 'highest' in q or 'maximum' in q or 'largest' in q:
        col = _find_numeric_col(df, q)
        if col:
            idx = df[col].idxmax()
            return f"Row {idx}: {df.iloc[idx].to_dict()}"

    if 'lowest' in q or 'minimum' in q or 'smallest' in q:
        col = _find_numeric_col(df, q)
        if col:
            idx = df[col].idxmin()
            return f"Row {idx}: {df.iloc[idx].to_dict()}"

    # Sum/Total
    if 'total' in q or 'sum' in q:
        col = _find_numeric_col(df, q)
        if col:
            return f"Total {col}: {df[col].sum()}"

    # Average
    if 'average' in q or 'mean' in q:
        col = _find_numeric_col(df, q)
        if col:
            return f"Average {col}: {df[col].mean():.2f}"

    # Count
    if 'how many' in q or 'count' in q:
        return f"Row count: {len(df)}"

    return "Could not answer. Try LLM-based QA for complex questions."


def _find_numeric_col(df: pd.DataFrame, hint: str) -> str | None:
    """Find a numeric column name mentioned in hint text."""
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    for col in numeric_cols:
        if col.lower() in hint:
            return col
    return numeric_cols[0] if numeric_cols else None
```

## LLM-Augmented Table QA

Pair extracted table with an LLM for natural language answers:

```python
import anthropic
import json

def llm_table_qa(df: pd.DataFrame, question: str, client=None) -> str:
    """Send table + question to Claude for NL reasoning."""
    if client is None:
        client = anthropic.Anthropic()

    table_str = df.to_markdown(index=False)  # pip install tabulate
    prompt = f"""You are a data analyst. Answer the question based ONLY on the table below.

TABLE:
{table_str}

QUESTION: {question}

Answer concisely with the specific value or values from the table."""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=512,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text


# Usage
df = table_to_df(tables[0])
answer = llm_table_qa(df, "Which branch had the highest revenue in Q3?")
print(answer)
```

## Multi-Table Document Processing

```python
def extract_all_tables(image_or_pdf_path: str) -> list[pd.DataFrame]:
    """Extract all tables from a document as DataFrames."""
    engine = PPStructureV3(use_table_recognition=True, use_doc_orientation_classify=False, use_doc_unwarping=False)

    if image_or_pdf_path.endswith('.pdf'):
        import pypdfium2 as pdfium
        import numpy as np
        doc = pdfium.PdfDocument(image_or_pdf_path)
        all_dfs = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            bitmap = page.render(scale=200/72)
            img = np.array(bitmap.to_pil())
            result = engine(img)
            for r in result:
                if r['type'] == 'table':
                    all_dfs.append(table_to_df(r))
        return all_dfs
    else:
        result = engine(image_or_pdf_path)
        return [table_to_df(r) for r in result if r['type'] == 'table']
```

## Table Boundary Visualization

```python
import cv2
import numpy as np

def visualize_tables(img_path: str, tables: list, out_path='tables_annotated.jpg'):
    img = cv2.imread(img_path)
    for i, table in enumerate(tables):
        bbox = table['bbox']   # [x1, y1, x2, y2]
        cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 3)
        cv2.putText(img, f'Table {i+1}', (bbox[0], bbox[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imwrite(out_path, img)
```

## Cell-Level Extraction

```python
def extract_cells(table_region: dict) -> list[dict]:
    """Extract individual cells with their positions."""
    cells = []
    if 'cell_bbox' in table_region.get('res', {}):
        for cell in table_region['res']['cell_bbox']:
            cells.append({
                'row': cell.get('row_index'),
                'col': cell.get('col_index'),
                'text': cell.get('text', ''),
                'bbox': cell.get('bbox')
            })
    return cells
```

## Financial Table Patterns

### Balance Sheet / P&L parsing
```python
def parse_financial_table(df: pd.DataFrame) -> dict:
    """Parse a financial statement table into structured dict."""
    # Assume first column = line item names, remaining = period values
    df = df.dropna(how='all').reset_index(drop=True)

    # Clean numeric columns (remove $, ₦, commas)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(r'[^\d.\-]', '', regex=True),
            errors='coerce'
        )

    # Index by line item
    df = df.set_index(df.columns[0])
    return df.to_dict()


# Usage
result_dict = parse_financial_table(df)
revenue = result_dict.get('Revenue', {})
```

### Rate/Fee table lookup
```python
def lookup_rate(df: pd.DataFrame, product: str, tier: str) -> float | None:
    """Look up a rate from a product × tier table."""
    matches = df[df.iloc[:, 0].str.contains(product, case=False, na=False)]
    if matches.empty:
        return None
    cols = [c for c in df.columns if tier.lower() in str(c).lower()]
    if not cols:
        return None
    return matches[cols[0]].iloc[0]
```

## Table Cleaning Utilities

```python
def clean_table(df: pd.DataFrame) -> pd.DataFrame:
    """Standard table cleanup after OCR."""
    # Drop fully empty rows/cols
    df = df.dropna(how='all').dropna(axis=1, how='all')

    # Strip whitespace from string cells
    df = df.apply(lambda col: col.map(
        lambda x: x.strip() if isinstance(x, str) else x))

    # Promote first row to header if it looks like headers
    if df.iloc[0].apply(lambda x: isinstance(x, str)).all():
        df.columns = df.iloc[0].tolist()
        df = df[1:].reset_index(drop=True)

    return df
```
