---
description: Comprehensive PDF manipulation toolkit for extracting text and tables, creating new PDFs, merging/splitting documents, and handling forms. When Claude needs to fill in a PDF form or programmatically process, generate, or analyze PDF documents at scale.
name: pdf
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see reference.md. If you need to fill out a PDF form, read forms.md and follow its instructions.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - Create PDFs

#### Basic PDF Creation
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Add text
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Add a line
c.line(100, height - 140, 400, height - 140)

# Save
c.save()
```

#### Create PDF with Multiple Pages
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Add content
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Page 2
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Build PDF
doc.build(story)
```

## Command-Line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create watermark (or load existing)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extract Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see forms.md) | See forms.md |

## Best Practices for Data Extraction from PDFs

### Always Verify Against Source Documents

When extracting structured data (names, emails, qualifications, dates, etc.) from PDFs:

1. **Read raw text first** - Before writing extraction logic, extract and review the full text from each PDF to understand the actual formatting:
   ```python
   import pdfplumber
   from pathlib import Path
   
   for pdf_path in Path("documents").glob("*.pdf"):
       print(f"\n{'='*60}\nFILE: {pdf_path.name}\n{'='*60}")
       with pdfplumber.open(pdf_path) as pdf:
           for page in pdf.pages:
               text = page.extract_text()
               if text:
                   print(text[:2000])  # Review first 2000 chars
   ```

2. **Don't trust regex blindly** - Automated regex patterns often fail due to:
   - Format variations: "Bachelor of Science in Finance" vs "B.Sc, Finance" vs "B.S. (Finance)"
   - Different section headers: "EDUCATION" vs "ACADEMICS" vs "Academic Qualification"
   - Non-standard punctuation: parentheses, commas, semicolons, dashes
   - Inline vs sectioned layouts

3. **Verify extraction output** - Always spot-check extracted data against the original PDF content. If automated extraction returns "Not found" or suspicious values, manually review the source.

### Common Pitfalls in PDF Data Extraction

| Problem | Cause | Solution |
|---------|-------|----------|
| Missing data | Regex too narrow | Review raw text, broaden patterns |
| Garbled text | PDF uses custom fonts/encoding | Try OCR with pytesseract instead |
| Wrong data | Multiple documents in one PDF | Check for page breaks, multiple resumes |
| Truncated values | Field length limits | Remove arbitrary truncation |
| Calculated values wrong | Date parsing errors | Validate date ranges manually |

### Recommended Extraction Workflow

```python
# Step 1: Extract and review raw text from ALL documents first
texts = {}
for pdf_path in pdf_files:
    with pdfplumber.open(pdf_path) as pdf:
        texts[pdf_path.name] = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

# Step 2: Analyze actual formats present in the documents
# - What section headers are used?
# - How are degrees/dates/emails formatted?
# - Are there multiple records per document?

# Step 3: Build extraction logic based on observed patterns
# - Use flexible regex that handles variations
# - Include fallback patterns
# - Log what was matched vs not matched

# Step 4: Verify results against source
# - Spot check 10-20% of extractions manually
# - Investigate any "Not found" results
# - Cross-reference suspicious values
```

### Example: Flexible Education Extraction

```python
import re

def extract_education(text):
    """Extract educational qualifications with flexible pattern matching."""
    education = []
    
    # Multiple patterns to catch format variations
    patterns = [
        # "Bachelor of Science in Finance"
        r"(Bachelor'?s?|Master'?s?|Doctor\w*|Associate'?s?)\s+(?:of\s+)?(\w+)(?:\s+(?:in|of)\s+[\w\s,]+)?",
        # "B.Sc, Finance" or "B.S. (Finance)"
        r"(B\.?S\.?c?|M\.?S\.?c?|B\.?A\.?|M\.?A\.?|M\.?B\.?A\.?|Ph\.?D\.?|LL\.?B\.?|LL\.?M\.?)[\s,.\(]+([A-Za-z\s]+)",
        # "PhD (Economics)"
        r"(PhD|MBA|LLB|LLM|CAIIB|CPA|CFA|CFM)\s*\(?([A-Za-z\s]*)\)?",
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            edu_text = match.group(0).strip()
            if edu_text and len(edu_text) > 2:
                # Avoid duplicates
                if not any(edu_text.lower() in e.lower() for e in education):
                    education.append(edu_text)
    
    return education if education else ["Not specified - VERIFY MANUALLY"]
```

## Next Steps

- For advanced pypdfium2 usage, see reference.md
- For JavaScript libraries (pdf-lib), see reference.md
- If you need to fill out a PDF form, follow the instructions in forms.md
- For troubleshooting guides, see reference.md
