# Structured Extraction Reference

**⚠️ v3.5.0 API Update:** Code examples below may use the deprecated `.ocr()` method and `result[0]` access pattern. In v3.5.0, use `.predict()` and access results via `res.json[res]`. See [ocr-pipeline.md](ocr-pipeline.md) for the migration guide. Key changes:
- `ocr.ocr(img)` → `ocr.predict(img)`
- `result[0][i][1][0]` (text) → `res.json[res][rec_texts][i]`
- `result[0][i][1][1]` (score) → `res.json[res][rec_scores][i]`
- `result[0][i][0]` (bbox) → `res.json[res][rec_polys][i]`
- `for line in (result[0] or []): line[1][0]` → `for res in result: for text, score in zip(res.json[res][rec_texts], res.json[res][rec_scores])`

Covers: forms, key-value pairs, invoices, receipts, ID cards, passports, bank statements, payslips, insurance documents.

## Strategy Overview

```
Image → PaddleOCR → Raw Lines → Pattern Engine → Structured JSON
                              ↗                ↗
                  LLM Extraction       Regex Templates
                  (flexible, NL)       (fast, deterministic)
```

Use **regex templates** for known document formats (invoices, IDs).
Use **LLM extraction** for unknown/variable documents.

## Generic KV Extractor

```python
import re
from paddleocr import PaddleOCR

def extract_kv(image_path: str, patterns: dict) -> dict:
    """
    Extract key-value pairs using regex patterns.

    patterns = {
        'field_name': r'regex with one capture group',
        ...
    }
    """
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(image_path)
    full_text = '\n'.join(l[1][0] for l in (result[0] or []))

    extracted = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
        extracted[field] = match.group(1).strip() if match else None

    return extracted
```

## Invoice / Receipt Extraction

```python
INVOICE_PATTERNS = {
    'invoice_number':  r'(?:Invoice|Inv)[\s.#No:]*([A-Z0-9\-/]+)',
    'invoice_date':    r'(?:Invoice\s*)?Date[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'due_date':        r'(?:Due|Payment\s*Due)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'vendor_name':     r'^([A-Z][A-Za-z\s&.,]+(?:Ltd|LLC|Inc|Corp|PLC|Limited))',
    'customer_name':   r'(?:Bill\s*To|Sold\s*To|Client)[:\s]+([^\n]+)',
    'subtotal':        r'(?:Sub\s*[-]?\s*Total)[:\s$₦€£]*([\d,]+\.?\d*)',
    'tax':             r'(?:VAT|Tax|GST)[:\s%\d]*[:\s$₦€£]*([\d,]+\.?\d*)',
    'total_amount':    r'(?:Total|Grand\s*Total|Amount\s*Due)[:\s$₦€£]*([\d,]+\.?\d*)',
    'currency':        r'(USD|NGN|GBP|EUR|₦|\$|£|€)',
    'po_number':       r'(?:PO|Purchase\s*Order)\s*[#No:.]*\s*([A-Z0-9\-]+)',
    'payment_method':  r'(?:Payment\s*Method|Pay\s*Via)[:\s]+([^\n]+)',
}

def extract_invoice(image_path: str) -> dict:
    return extract_kv(image_path, INVOICE_PATTERNS)
```

## Receipt Extraction

```python
RECEIPT_PATTERNS = {
    'store_name':    r'^([A-Z][A-Za-z\s&]+(?:Store|Mart|Shop|Market|Restaurant)?)',
    'date':          r'(?:Date|Dt)[:\s]*([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'time':          r'(?:Time)[:\s]*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)',
    'receipt_no':    r'(?:Receipt|Rcpt|Trans|Transaction)\s*[#No:.]*\s*([A-Z0-9\-]+)',
    'cashier':       r'(?:Cashier|Served\s*By|Operator)[:\s]+([^\n]+)',
    'subtotal':      r'(?:Sub\s*Total)[:\s$₦€£]*([\d,]+\.?\d*)',
    'discount':      r'(?:Discount|Promo)[:\s\-$₦€£]*([\d,]+\.?\d*)',
    'total':         r'(?:TOTAL|Total)[:\s$₦€£]*([\d,]+\.?\d*)',
    'cash_tendered': r'(?:Cash|Tendered)[:\s$₦€£]*([\d,]+\.?\d*)',
    'change':        r'(?:Change|Balance)[:\s$₦€£]*([\d,]+\.?\d*)',
}

def extract_receipt(image_path: str) -> dict:
    result = extract_kv(image_path, RECEIPT_PATTERNS)
    # Also extract line items
    result['line_items'] = extract_receipt_line_items(image_path)
    return result

def extract_receipt_line_items(image_path: str) -> list[dict]:
    """Extract item name + price pairs from receipt."""
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(image_path)
    lines = [l[1][0] for l in (result[0] or [])]
    items = []
    item_pattern = re.compile(r'^(.+?)\s+([\d,]+\.?\d*)\s*$')
    for line in lines:
        m = item_pattern.match(line.strip())
        if m and not any(kw in line.upper()
                         for kw in ('TOTAL', 'TAX', 'SUBTOTAL', 'CASH', 'CHANGE')):
            items.append({'name': m.group(1).strip(), 'price': m.group(2)})
    return items
```

## Nigerian / African Document Patterns

```python
# Nigerian formats
NG_INVOICE_PATTERNS = {
    **INVOICE_PATTERNS,
    'tin':         r'(?:TIN|Tax\s*ID)[:\s]+(\d{8,12})',
    'rc_number':   r'(?:RC|CAC)[:\s#]*(\d{5,8})',
    'vat_reg':     r'(?:VAT\s*Reg)[:\s]+([A-Z0-9\-]+)',
    'bank_name':   r'(?:Bank)[:\s]+([A-Za-z\s]+Bank)',
    'account_no':  r'(?:Account\s*No|Acct)[:\s]+(\d{10})',
    'sort_code':   r'(?:Sort\s*Code)[:\s]+([\d\-]+)',
}
```

## ID Card Extraction

```python
ID_PATTERNS = {
    'full_name':    r'(?:Name|Full\s*Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'id_number':    r'(?:ID\s*No|Card\s*No|Number)[:\s#]*([A-Z0-9\-]+)',
    'date_of_birth':r'(?:DOB|Date\s*of\s*Birth|Born)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'sex':          r'(?:Sex|Gender)[:\s]+(M(?:ale)?|F(?:emale)?)',
    'nationality':  r'(?:Nationality|Country)[:\s]+([A-Za-z\s]+)',
    'issue_date':   r'(?:Issued?|Issue\s*Date)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'expiry_date':  r'(?:Expir|Exp\.?\s*Date|Valid\s*Until)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'address':      r'(?:Address|Addr)[:\s]+([^\n]{10,})',
    'state_of_origin': r'(?:State\s*of\s*Origin|State)[:\s]+([A-Za-z\s]+)',
}

# MRZ (Machine Readable Zone) extraction for passports
MRZ_PATTERN = re.compile(r'([A-Z<]{2}[A-Z0-9<]{42,44})')

def extract_id_card(image_path: str) -> dict:
    result = extract_kv(image_path, ID_PATTERNS)
    result['is_expired'] = _check_expiry(result.get('expiry_date'))
    result['mrz'] = _extract_mrz(image_path)
    return result

def _check_expiry(expiry_str: str | None) -> bool | None:
    if not expiry_str:
        return None
    from datetime import datetime
    for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y'):
        try:
            expiry = datetime.strptime(expiry_str, fmt)
            return expiry < datetime.now()
        except ValueError:
            continue
    return None

def _extract_mrz(image_path: str) -> str | None:
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False, lang='en')
    result = ocr.predict(image_path)
    lines = [l[1][0] for l in (result[0] or [])]
    mrz_lines = [l for l in lines if MRZ_PATTERN.search(l)]
    return '\n'.join(mrz_lines) if mrz_lines else None
```

## Bank Statement Parsing

```python
BANK_STATEMENT_PATTERNS = {
    'account_name':   r'(?:Account\s*Name|Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'account_number': r'(?:Account\s*No|Account\s*Number)[:\s]+(\d{6,16})',
    'bank_name':      r'([A-Z][A-Za-z\s]+(?:Bank|Financial))',
    'statement_date': r'(?:Statement\s*Date|Period)[:\s]+([\w\s,]+\d{4})',
    'opening_balance':r'(?:Opening|O\/B|Brought\s*Forward)[:\s$₦€£]*([\d,]+\.?\d*)',
    'closing_balance':r'(?:Closing|C\/B|Carried\s*Forward)[:\s$₦€£]*([\d,]+\.?\d*)',
}

def extract_transactions(image_path: str) -> list[dict]:
    """Extract transaction rows from a bank statement image."""
    from paddleocr import PPStructureV3
    from io import StringIO
    import pandas as pd

    engine = PPStructureV3(table=True, ocr=True)
    result = engine(image_path)

    transactions = []
    for block in result:
        if block['type'] == 'table':
            df = pd.read_html(StringIO(block['res']['html']))[0]
            # Detect transaction columns
            cols = [c.lower() for c in df.columns]
            date_col   = next((c for c in df.columns if 'date' in c.lower()), None)
            desc_col   = next((c for c in df.columns if any(k in c.lower() for k in ('desc','narr','ref','particular'))), None)
            debit_col  = next((c for c in df.columns if 'debit' in c.lower() or 'dr' in c.lower()), None)
            credit_col = next((c for c in df.columns if 'credit' in c.lower() or 'cr' in c.lower()), None)
            bal_col    = next((c for c in df.columns if 'balance' in c.lower() or 'bal' in c.lower()), None)

            for _, row in df.iterrows():
                transactions.append({
                    'date':        row.get(date_col),
                    'description': row.get(desc_col),
                    'debit':       row.get(debit_col),
                    'credit':      row.get(credit_col),
                    'balance':     row.get(bal_col),
                })

    return transactions
```

## Payslip / Payroll Extraction

```python
PAYSLIP_PATTERNS = {
    'employee_name':  r'(?:Employee|Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'employee_id':    r'(?:Employee\s*ID|Staff\s*ID|No)[:\s]+([A-Z0-9\-]+)',
    'department':     r'(?:Department|Dept)[:\s]+([^\n]+)',
    'pay_period':     r'(?:Pay\s*Period|Period)[:\s]+([^\n]+)',
    'basic_salary':   r'(?:Basic\s*Salary|Basic\s*Pay)[:\s$₦€£]*([\d,]+\.?\d*)',
    'gross_salary':   r'(?:Gross\s*Pay|Gross\s*Salary)[:\s$₦€£]*([\d,]+\.?\d*)',
    'net_salary':     r'(?:Net\s*Pay|Net\s*Salary|Take\s*Home)[:\s$₦€£]*([\d,]+\.?\d*)',
    'tax':            r'(?:PAYE|Income\s*Tax|Tax)[:\s$₦€£]*([\d,]+\.?\d*)',
    'pension':        r'(?:Pension|Retirement)[:\s$₦€£]*([\d,]+\.?\d*)',
    'nhf':            r'(?:NHF)[:\s$₦€£]*([\d,]+\.?\d*)',
}
```

## LLM-Powered Flexible Extraction

Use when document format is unknown or irregular:

```python
import anthropic
import json

def llm_extract(image_path: str, fields: list[str], client=None) -> dict:
    """
    Use LLM to extract arbitrary fields from any document.
    More flexible than regex, works on irregular formats.
    """
    if client is None:
        client = anthropic.Anthropic()

    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang='en')
    result = ocr.predict(image_path)
    text = '\n'.join(l[1][0] for l in (result[0] or []))

    prompt = f"""Extract the following fields from this document text.
Return a JSON object. Use null for missing fields.

FIELDS TO EXTRACT: {json.dumps(fields)}

DOCUMENT TEXT:
{text}

Return only valid JSON."""

    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )

    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {'raw_response': response.content[0].text}


# Usage
result = llm_extract('insurance_policy.jpg', [
    'policy_number', 'insured_name', 'coverage_amount',
    'premium', 'start_date', 'end_date', 'beneficiaries'
])
```

## Insurance Document Extraction

```python
INSURANCE_PATTERNS = {
    'policy_number':   r'(?:Policy\s*No|Policy\s*Number)[:\s]+([A-Z0-9\-/]+)',
    'insured_name':    r'(?:Insured|Policy\s*Holder|Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'sum_insured':     r'(?:Sum\s*Insured|Coverage|Amount)[:\s$₦€£]*([\d,]+\.?\d*)',
    'premium':         r'(?:Premium|Annual\s*Premium)[:\s$₦€£]*([\d,]+\.?\d*)',
    'start_date':      r'(?:Inception|Start|Commencement)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'end_date':        r'(?:Expiry|Expiration|End\s*Date)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'insurer':         r'(?:Insurer|Insurance\s*Company)[:\s]+([A-Z][A-Za-z\s]+(?:Insurance|Assurance))',
}
```

## Output Schema

```python
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ExtractionResult:
    document_type: str
    confidence: float           # 0.0 – 1.0 overall extraction confidence
    fields: dict                # extracted key-value pairs
    missing_fields: list[str]   # fields not found
    raw_text: str               # full OCR text
    warnings: list[str]         # e.g., 'low image quality', 'expired ID'

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
```
