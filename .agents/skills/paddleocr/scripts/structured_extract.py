#!/usr/bin/env python3
"""
structured_extract.py — Extract structured fields from typed documents.

Usage:
    python3 structured_extract.py <image> --type <doc_type> [options]

Examples:
    python3 structured_extract.py invoice.jpg --type invoice
    python3 structured_extract.py id_card.png --type id
    python3 structured_extract.py receipt.jpg --type receipt
    python3 structured_extract.py statement.jpg --type bank_statement
    python3 structured_extract.py payslip.jpg --type payslip
    python3 structured_extract.py contract.pdf --type contract --llm
    python3 structured_extract.py unknown.jpg --type auto --llm

Document types:
    invoice, receipt, id, passport, bank_statement, payslip,
    insurance, contract, auto (auto-detect with --llm)

Options:
    --type TYPE       Document type (required)
    --out PATH        Output JSON file (default: stdout)
    --lang LANG       OCR language (default: en)
    --llm             Use LLM (Claude) for flexible/unknown extraction
    --fields f1,f2    Custom fields to extract (used with --llm)
    --verify          Check for missing/expired fields and anomalies
"""

import sys
import re
import json
import argparse
from pathlib import Path


# ─── Regex pattern libraries ─────────────────────────────────────────────────

INVOICE_PATTERNS = {
    'invoice_number':  r'(?:Invoice|Inv)[\s.#No:]*([A-Z0-9\-/]+)',
    'invoice_date':    r'(?:Invoice\s*)?Date[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'due_date':        r'(?:Due|Payment\s*Due)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'vendor_name':     r'^([A-Z][A-Za-z\s&.,]+(?:Ltd|LLC|Inc|Corp|PLC|Limited|Group))',
    'customer_name':   r'(?:Bill\s*To|Sold\s*To|Client|Customer)[:\s]+([^\n]+)',
    'subtotal':        r'(?:Sub\s*[-]?\s*Total)[:\s$₦€£]*([\d,]+\.?\d*)',
    'tax_vat':         r'(?:VAT|Tax|GST)[:\s%\d]*[:\s$₦€£]*([\d,]+\.?\d*)',
    'total_amount':    r'(?:TOTAL|Total|Grand\s*Total|Amount\s*Due)[:\s$₦€£]*([\d,]+\.?\d*)',
    'currency':        r'\b(USD|NGN|GBP|EUR|KES|GHS|ZAR)\b',
    'po_number':       r'(?:PO|Purchase\s*Order)\s*[#No:.]*\s*([A-Z0-9\-]+)',
    'tin':             r'(?:TIN|Tax\s*ID|FIRS)[:\s]+(\d{8,12})',
    'rc_number':       r'(?:RC|CAC)\s*[#No:.]*\s*(\d{5,8})',
    'bank_name':       r'(?:Bank)[:\s]+([A-Za-z\s]+Bank)',
    'account_number':  r'(?:Account\s*No|Acct)[:\s]+(\d{8,12})',
}

RECEIPT_PATTERNS = {
    'store_name':    r'^([A-Z][A-Za-z\s&]+)',
    'date':          r'(?:Date|Dt)[:\s]*([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'time':          r'(?:Time)[:\s]*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)',
    'receipt_no':    r'(?:Receipt|Rcpt|Trans)[#No:.]*\s*([A-Z0-9\-]+)',
    'subtotal':      r'(?:Sub\s*Total)[:\s$₦€£]*([\d,]+\.?\d*)',
    'discount':      r'(?:Discount|Promo)[:\s\-$₦€£]*([\d,]+\.?\d*)',
    'total':         r'(?:TOTAL|Total)[:\s$₦€£]*([\d,]+\.?\d*)',
    'cash_tendered': r'(?:Cash|Tendered)[:\s$₦€£]*([\d,]+\.?\d*)',
    'change':        r'(?:Change|Balance)[:\s$₦€£]*([\d,]+\.?\d*)',
}

ID_PATTERNS = {
    'full_name':         r'(?:Name|Full\s*Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'id_number':         r'(?:ID\s*No|Card\s*No|Number|NIN|BVN)[:\s#]*([A-Z0-9\-]+)',
    'date_of_birth':     r'(?:DOB|Date\s*of\s*Birth|Born)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'sex':               r'(?:Sex|Gender)[:\s]+(M(?:ale)?|F(?:emale)?)',
    'nationality':       r'(?:Nationality|Country)[:\s]+([A-Za-z\s]+)',
    'issue_date':        r'(?:Issued?|Issue\s*Date)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'expiry_date':       r'(?:Expir|Exp\.?\s*Date|Valid\s*Until|Expires)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'address':           r'(?:Address|Addr)[:\s]+([^\n]{10,80})',
    'state_of_origin':   r'(?:State\s*of\s*Origin|State)[:\s]+([A-Za-z\s]+)',
    'issuing_authority': r'(?:Issued\s*By|Authority)[:\s]+([^\n]+)',
}

BANK_STATEMENT_PATTERNS = {
    'account_name':    r'(?:Account\s*Name|Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'account_number':  r'(?:Account\s*No|Account\s*Number)[:\s]+(\d{6,16})',
    'bank_name':       r'([A-Z][A-Za-z\s]+(?:Bank|Financial|Trust))',
    'statement_period':r'(?:Statement\s*(?:Date|Period)|Period)[:\s]+([^\n]+)',
    'opening_balance': r'(?:Opening|O\/B|Brought\s*Forward)[:\s$₦€£]*([\d,]+\.?\d*)',
    'closing_balance': r'(?:Closing|C\/B|Carried\s*Forward)[:\s$₦€£]*([\d,]+\.?\d*)',
}

PAYSLIP_PATTERNS = {
    'employee_name':   r'(?:Employee|Name)[:\s]+([A-Z][A-Za-z\s]+)',
    'employee_id':     r'(?:Employee\s*ID|Staff\s*ID)[:\s]+([A-Z0-9\-]+)',
    'department':      r'(?:Department|Dept)[:\s]+([^\n]+)',
    'pay_period':      r'(?:Pay\s*Period|Period)[:\s]+([^\n]+)',
    'basic_salary':    r'(?:Basic\s*(?:Salary|Pay))[:\s$₦€£]*([\d,]+\.?\d*)',
    'gross_salary':    r'(?:Gross\s*(?:Pay|Salary))[:\s$₦€£]*([\d,]+\.?\d*)',
    'net_salary':      r'(?:Net\s*(?:Pay|Salary)|Take\s*Home)[:\s$₦€£]*([\d,]+\.?\d*)',
    'tax_paye':        r'(?:PAYE|Income\s*Tax)[:\s$₦€£]*([\d,]+\.?\d*)',
    'pension':         r'(?:Pension|Retirement\s*Fund)[:\s$₦€£]*([\d,]+\.?\d*)',
}

INSURANCE_PATTERNS = {
    'policy_number':  r'(?:Policy\s*(?:No|Number))[:\s]+([A-Z0-9\-/]+)',
    'insured_name':   r'(?:Insured|Policy\s*Holder)[:\s]+([A-Z][A-Za-z\s]+)',
    'sum_insured':    r'(?:Sum\s*Insured|Coverage)[:\s$₦€£]*([\d,]+\.?\d*)',
    'premium':        r'(?:(?:Annual\s*)?Premium)[:\s$₦€£]*([\d,]+\.?\d*)',
    'start_date':     r'(?:Inception|Start|Commencement)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'end_date':       r'(?:Expiry|Expiration|End\s*Date)[:\s]+([\d]{1,2}[\/\-][\d]{1,2}[\/\-][\d]{2,4})',
    'insurer':        r'(?:Insurer|Insurance\s*Company)[:\s]+([A-Z][A-Za-z\s]+(?:Insurance|Assurance))',
}

PATTERN_MAP = {
    'invoice':         INVOICE_PATTERNS,
    'receipt':         RECEIPT_PATTERNS,
    'id':              ID_PATTERNS,
    'passport':        ID_PATTERNS,
    'bank_statement':  BANK_STATEMENT_PATTERNS,
    'payslip':         PAYSLIP_PATTERNS,
    'insurance':       INSURANCE_PATTERNS,
}


# ─── Core extraction ──────────────────────────────────────────────────────────

def run_ocr(image_path: str, lang='en') -> tuple[list[str], str]:
    """Run PaddleOCR and return (lines, full_text)."""
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=True, lang=lang)
    result = ocr.predict(image_path)
    lines = []
    for res in result:
        lines.extend(res.json['res'].get('rec_texts', []))
    return lines, '\n'.join(lines)


def regex_extract(full_text: str, patterns: dict) -> dict:
    extracted = {}
    for field, pattern in patterns.items():
        m = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
        extracted[field] = m.group(1).strip() if m else None
    return extracted


def llm_extract(full_text: str, fields: list[str]) -> dict:
    import os, anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    prompt = f"""Extract the following fields from this document text.
Return a JSON object. Use null for missing fields. Do not guess — only extract what is present.

FIELDS: {json.dumps(fields)}

DOCUMENT:
{full_text}

Return only valid JSON."""
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )
    try:
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return {'_raw': response.content[0].text}


def llm_auto_detect_type(full_text: str) -> str:
    import os, anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    prompt = f"""What type of document is this? Choose from:
invoice, receipt, id, passport, bank_statement, payslip, insurance, contract, other

DOCUMENT (first 1000 chars):
{full_text[:1000]}

Reply with only the document type, nothing else."""
    response = client.messages.create(
        model='claude-opus-4-5',
        max_tokens=20,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text.strip().lower()


def verify_result(fields: dict, doc_type: str) -> dict:
    warnings = []
    missing = [k for k, v in fields.items() if v is None]
    if missing:
        warnings.append(f"Missing fields: {', '.join(missing)}")

    # Check ID expiry
    expiry = fields.get('expiry_date') or fields.get('due_date') or fields.get('end_date')
    if expiry:
        from datetime import datetime
        for fmt in ('%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y'):
            try:
                exp_dt = datetime.strptime(expiry, fmt)
                if exp_dt < datetime.now():
                    warnings.append(f"⚠️  EXPIRED: {expiry}")
                break
            except ValueError:
                continue

    return {'warnings': warnings, 'missing_fields': missing}


# ─── Main ────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='Structured document field extraction')
    p.add_argument('input', help='Image file path')
    p.add_argument('--type', required=True,
                   help='Document type: invoice|receipt|id|passport|bank_statement|payslip|insurance|contract|auto')
    p.add_argument('--out', default=None, help='Output JSON file path')
    p.add_argument('--lang', default='en', help='OCR language')
    p.add_argument('--llm', action='store_true', help='Use LLM for extraction')
    p.add_argument('--fields', default=None, help='Custom fields (comma-separated, with --llm)')
    p.add_argument('--verify', action='store_true', help='Verify completeness and expiry')
    return p.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"📄 Processing: {input_path}", file=sys.stderr)
    lines, full_text = run_ocr(str(input_path), lang=args.lang)
    print(f"   OCR: {len(lines)} lines extracted", file=sys.stderr)

    doc_type = args.type.lower()

    # Auto-detect
    if doc_type == 'auto':
        if not args.llm:
            print("❌ --type auto requires --llm flag", file=sys.stderr)
            sys.exit(1)
        doc_type = llm_auto_detect_type(full_text)
        print(f"   Auto-detected type: {doc_type}", file=sys.stderr)

    # Extract fields
    if args.llm:
        if args.fields:
            fields_list = [f.strip() for f in args.fields.split(',')]
        elif doc_type in PATTERN_MAP:
            fields_list = list(PATTERN_MAP[doc_type].keys())
        else:
            fields_list = ['date', 'name', 'amount', 'reference', 'address',
                           'phone', 'email', 'signature_present']
        print(f"   Using LLM extraction for {len(fields_list)} fields...", file=sys.stderr)
        extracted = llm_extract(full_text, fields_list)
    elif doc_type in PATTERN_MAP:
        print(f"   Using regex extraction ({len(PATTERN_MAP[doc_type])} patterns)...", file=sys.stderr)
        extracted = regex_extract(full_text, PATTERN_MAP[doc_type])
    else:
        print(f"   ⚠️  Unknown type '{doc_type}'. Use --llm for custom extraction.", file=sys.stderr)
        extracted = {}

    output = {
        'source': str(input_path),
        'document_type': doc_type,
        'extracted_fields': extracted,
        'ocr_line_count': len(lines),
    }

    if args.verify:
        verification = verify_result(extracted, doc_type)
        output['verification'] = verification
        for w in verification['warnings']:
            print(f"   {w}", file=sys.stderr)

    result_json = json.dumps(output, indent=2, ensure_ascii=False)

    if args.out:
        Path(args.out).write_text(result_json, encoding='utf-8')
        print(f"✅ Saved: {args.out}", file=sys.stderr)
    else:
        print(result_json)


if __name__ == '__main__':
    main()
