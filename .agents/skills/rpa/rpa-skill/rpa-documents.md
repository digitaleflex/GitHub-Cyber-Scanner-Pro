# RPA Document Automation Module

> Version: 1.0 | Stack: openpyxl + pypdf + reportlab + python-docx + uv

## Overview

Document automation for Excel spreadsheets, PDF files, Word documents, Email (IMAP/SMTP), and CSV processing. All examples use `uv` exclusively for Python package management.

---

## Quick Start

```bash
# Install document automation dependencies
uv add openpyxl pandas pypdf reportlab python-docx aiosmtplib aioimaplib jinja2

# Optional: For advanced Excel features
uv add xlsxwriter xlrd

# Optional: For PDF form filling
uv add pypdf[crypto] fillpdf

# Optional: For email validation
uv add email-validator
```

---

## Table of Contents

1. [Excel Automation](#excel-automation)
2. [PDF Automation](#pdf-automation)
3. [Word Document Automation](#word-document-automation)
4. [Email Automation](#email-automation)
5. [CSV Processing](#csv-processing)
6. [Document Workflows](#document-workflows)
7. [Templates and Mail Merge](#templates-and-mail-merge)

---

## Excel Automation

### Basic Read/Write Operations

```python
# excel_basics.py
"""Excel read/write with openpyxl."""
from pathlib import Path
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd


class ExcelHandler:
    """Enterprise Excel automation handler."""
    
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.workbook: Workbook | None = None
    
    def create_workbook(self) -> Workbook:
        """Create new workbook."""
        self.workbook = Workbook()
        return self.workbook
    
    def load_workbook(self, data_only: bool = False) -> Workbook:
        """Load existing workbook."""
        self.workbook = load_workbook(
            self.filepath,
            data_only=data_only  # True = get calculated values, not formulas
        )
        return self.workbook
    
    def save(self, filepath: str | Path | None = None):
        """Save workbook."""
        save_path = Path(filepath) if filepath else self.filepath
        self.workbook.save(save_path)
    
    def read_sheet_to_dataframe(
        self,
        sheet_name: str | None = None,
        header_row: int = 1
    ) -> pd.DataFrame:
        """Read sheet to pandas DataFrame."""
        if not self.workbook:
            self.load_workbook(data_only=True)
        
        sheet = self.workbook[sheet_name] if sheet_name else self.workbook.active
        
        data = []
        headers = []
        
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), 1):
            if row_idx == header_row:
                headers = list(row)
            elif row_idx > header_row:
                data.append(row)
        
        return pd.DataFrame(data, columns=headers)
    
    def write_dataframe(
        self,
        df: pd.DataFrame,
        sheet_name: str = "Sheet1",
        start_row: int = 1,
        start_col: int = 1,
        include_header: bool = True,
        include_index: bool = False
    ):
        """Write DataFrame to sheet."""
        if not self.workbook:
            self.create_workbook()
        
        # Get or create sheet
        if sheet_name in self.workbook.sheetnames:
            sheet = self.workbook[sheet_name]
        else:
            sheet = self.workbook.create_sheet(sheet_name)
        
        # Write data
        for r_idx, row in enumerate(
            dataframe_to_rows(df, index=include_index, header=include_header),
            start_row
        ):
            for c_idx, value in enumerate(row, start_col):
                sheet.cell(row=r_idx, column=c_idx, value=value)
    
    def apply_formatting(
        self,
        sheet_name: str,
        cell_range: str,
        bold: bool = False,
        font_size: int = 11,
        font_color: str = "000000",
        bg_color: str | None = None,
        alignment: str = "left",
        border: bool = False
    ):
        """Apply formatting to cell range."""
        sheet = self.workbook[sheet_name]
        
        # Define styles
        font = Font(bold=bold, size=font_size, color=font_color)
        align = Alignment(horizontal=alignment, vertical="center")
        
        fill = None
        if bg_color:
            fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
        
        border_style = None
        if border:
            side = Side(style="thin", color="000000")
            border_style = Border(left=side, right=side, top=side, bottom=side)
        
        # Apply to range
        for row in sheet[cell_range]:
            for cell in row:
                cell.font = font
                cell.alignment = align
                if fill:
                    cell.fill = fill
                if border_style:
                    cell.border = border_style


# Usage
if __name__ == "__main__":
    handler = ExcelHandler("report.xlsx")
    handler.create_workbook()
    
    # Create sample data
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Sales": [1000, 1500, 1200],
        "Region": ["North", "South", "East"]
    })
    
    handler.write_dataframe(df, "Sales Data")
    handler.apply_formatting(
        "Sales Data",
        "A1:C1",
        bold=True,
        bg_color="4472C4",
        font_color="FFFFFF"
    )
    handler.save()
```

### Excel with Formulas and Charts

```python
# excel_advanced.py
"""Advanced Excel with formulas and charts."""
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter


class ExcelReportBuilder:
    """Build Excel reports with charts and formulas."""
    
    def __init__(self):
        self.workbook = Workbook()
        self.active_sheet = self.workbook.active
    
    def add_formula(self, sheet_name: str, cell: str, formula: str):
        """Add formula to cell."""
        sheet = self.workbook[sheet_name]
        sheet[cell] = formula
    
    def add_summary_formulas(self, sheet_name: str, data_range: str, summary_row: int):
        """Add SUM, AVERAGE, MIN, MAX formulas."""
        sheet = self.workbook[sheet_name]
        
        # Parse range (e.g., "B2:B10")
        start_col = data_range.split(":")[0][0]
        
        formulas = {
            "SUM": f"=SUM({data_range})",
            "AVERAGE": f"=AVERAGE({data_range})",
            "MIN": f"=MIN({data_range})",
            "MAX": f"=MAX({data_range})"
        }
        
        col_idx = ord(start_col) - ord('A') + 1
        for idx, (name, formula) in enumerate(formulas.items()):
            sheet.cell(row=summary_row, column=1, value=name)
            sheet.cell(row=summary_row + idx, column=col_idx, value=formula)
    
    def add_bar_chart(
        self,
        sheet_name: str,
        data_range: tuple,  # (min_col, min_row, max_col, max_row)
        categories_range: tuple,
        title: str,
        position: str = "E2"
    ):
        """Add bar chart to sheet."""
        sheet = self.workbook[sheet_name]
        
        chart = BarChart()
        chart.type = "col"
        chart.style = 10
        chart.title = title
        
        data = Reference(
            sheet,
            min_col=data_range[0],
            min_row=data_range[1],
            max_col=data_range[2],
            max_row=data_range[3]
        )
        
        cats = Reference(
            sheet,
            min_col=categories_range[0],
            min_row=categories_range[1],
            max_row=categories_range[3]
        )
        
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.shape = 4
        
        sheet.add_chart(chart, position)
    
    def add_pie_chart(
        self,
        sheet_name: str,
        data_range: tuple,
        labels_range: tuple,
        title: str,
        position: str = "E2"
    ):
        """Add pie chart with labels."""
        sheet = self.workbook[sheet_name]
        
        chart = PieChart()
        chart.title = title
        
        data = Reference(
            sheet,
            min_col=data_range[0],
            min_row=data_range[1],
            max_row=data_range[3]
        )
        
        labels = Reference(
            sheet,
            min_col=labels_range[0],
            min_row=labels_range[1],
            max_row=labels_range[3]
        )
        
        chart.add_data(data)
        chart.set_categories(labels)
        
        # Add data labels
        chart.dataLabels = DataLabelList()
        chart.dataLabels.showPercent = True
        chart.dataLabels.showVal = False
        
        sheet.add_chart(chart, position)
    
    def add_line_chart(
        self,
        sheet_name: str,
        data_range: tuple,
        categories_range: tuple,
        title: str,
        position: str = "E2"
    ):
        """Add line chart for trends."""
        sheet = self.workbook[sheet_name]
        
        chart = LineChart()
        chart.style = 10
        chart.title = title
        
        data = Reference(
            sheet,
            min_col=data_range[0],
            min_row=data_range[1],
            max_col=data_range[2],
            max_row=data_range[3]
        )
        
        cats = Reference(
            sheet,
            min_col=categories_range[0],
            min_row=categories_range[1],
            max_row=categories_range[3]
        )
        
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        
        sheet.add_chart(chart, position)
    
    def auto_adjust_columns(self, sheet_name: str):
        """Auto-adjust column widths."""
        sheet = self.workbook[sheet_name]
        
        for column_cells in sheet.columns:
            max_length = 0
            column = column_cells[0].column_letter
            
            for cell in column_cells:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            sheet.column_dimensions[column].width = adjusted_width
    
    def save(self, filepath: str):
        """Save workbook."""
        self.workbook.save(filepath)


# Usage
if __name__ == "__main__":
    builder = ExcelReportBuilder()
    sheet = builder.active_sheet
    sheet.title = "Sales Report"
    
    # Add data
    data = [
        ["Month", "Sales", "Expenses", "Profit"],
        ["Jan", 10000, 7000, 3000],
        ["Feb", 12000, 8000, 4000],
        ["Mar", 15000, 9000, 6000],
        ["Apr", 11000, 7500, 3500],
    ]
    
    for row in data:
        sheet.append(row)
    
    # Add formulas
    sheet["E1"] = "Margin %"
    for row in range(2, 6):
        sheet[f"E{row}"] = f"=D{row}/B{row}*100"
    
    # Add chart
    builder.add_bar_chart(
        "Sales Report",
        data_range=(2, 1, 4, 5),
        categories_range=(1, 2, 1, 5),
        title="Monthly Performance",
        position="G2"
    )
    
    builder.auto_adjust_columns("Sales Report")
    builder.save("sales_report.xlsx")
```

### Bulk Excel Processing

```python
# excel_bulk.py
"""Bulk Excel file processing."""
import asyncio
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from openpyxl import load_workbook
import pandas as pd
import structlog

logger = structlog.get_logger()


class BulkExcelProcessor:
    """Process multiple Excel files in parallel."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    @staticmethod
    def process_single_file(filepath: Path, operation: str) -> dict:
        """Process single Excel file (runs in separate process)."""
        try:
            wb = load_workbook(filepath, data_only=True)
            result = {"file": str(filepath), "status": "success"}
            
            if operation == "extract_data":
                sheet = wb.active
                data = []
                for row in sheet.iter_rows(values_only=True):
                    data.append(row)
                result["data"] = data
                result["rows"] = len(data)
            
            elif operation == "get_metadata":
                result["sheets"] = wb.sheetnames
                result["properties"] = {
                    "creator": wb.properties.creator,
                    "created": str(wb.properties.created),
                    "modified": str(wb.properties.modified)
                }
            
            elif operation == "validate":
                # Check for required sheets/columns
                result["sheets"] = wb.sheetnames
                result["valid"] = "Data" in wb.sheetnames
            
            wb.close()
            return result
            
        except Exception as e:
            return {
                "file": str(filepath),
                "status": "error",
                "error": str(e)
            }
    
    async def process_files(
        self,
        file_paths: list[Path],
        operation: str = "extract_data"
    ) -> list[dict]:
        """Process multiple files in parallel."""
        loop = asyncio.get_event_loop()
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self.process_single_file,
                    fp,
                    operation
                )
                for fp in file_paths
            ]
            
            results = await asyncio.gather(*tasks)
        
        return results
    
    def merge_excel_files(
        self,
        file_paths: list[Path],
        output_path: Path,
        sheet_name: str = "Merged Data"
    ):
        """Merge multiple Excel files into one."""
        all_dataframes = []
        
        for fp in file_paths:
            try:
                df = pd.read_excel(fp)
                df["_source_file"] = fp.name
                all_dataframes.append(df)
                logger.info("Loaded file", file=fp.name, rows=len(df))
            except Exception as e:
                logger.error("Failed to load file", file=fp.name, error=str(e))
        
        if all_dataframes:
            merged = pd.concat(all_dataframes, ignore_index=True)
            merged.to_excel(output_path, sheet_name=sheet_name, index=False)
            logger.info("Merged files saved", output=str(output_path), total_rows=len(merged))
    
    def split_excel_by_column(
        self,
        input_path: Path,
        output_dir: Path,
        split_column: str
    ):
        """Split Excel file by unique values in column."""
        df = pd.read_excel(input_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for value in df[split_column].unique():
            subset = df[df[split_column] == value]
            safe_value = str(value).replace("/", "_").replace("\\", "_")
            output_path = output_dir / f"{safe_value}.xlsx"
            subset.to_excel(output_path, index=False)
            logger.info("Created split file", value=value, rows=len(subset))


# Usage
if __name__ == "__main__":
    processor = BulkExcelProcessor(max_workers=4)
    
    # Find all Excel files
    excel_files = list(Path("./data").glob("*.xlsx"))
    
    # Process in parallel
    results = asyncio.run(processor.process_files(excel_files, "extract_data"))
    
    for result in results:
        print(f"{result['file']}: {result['status']}")
```

---

## PDF Automation

### Reading PDFs

```python
# pdf_reader.py
"""PDF reading and text extraction."""
from pathlib import Path
from pypdf import PdfReader, PdfWriter
import re


class PDFExtractor:
    """Extract content from PDF files."""
    
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.reader = PdfReader(self.filepath)
    
    @property
    def num_pages(self) -> int:
        """Get total page count."""
        return len(self.reader.pages)
    
    @property
    def metadata(self) -> dict:
        """Get PDF metadata."""
        meta = self.reader.metadata
        return {
            "title": meta.title if meta else None,
            "author": meta.author if meta else None,
            "subject": meta.subject if meta else None,
            "creator": meta.creator if meta else None,
            "producer": meta.producer if meta else None,
            "creation_date": str(meta.creation_date) if meta else None
        }
    
    def extract_text(self, page_numbers: list[int] | None = None) -> str:
        """Extract text from pages."""
        text_parts = []
        
        pages_to_process = page_numbers or range(self.num_pages)
        
        for page_num in pages_to_process:
            if 0 <= page_num < self.num_pages:
                page = self.reader.pages[page_num]
                text_parts.append(page.extract_text() or "")
        
        return "\n\n".join(text_parts)
    
    def extract_text_by_pattern(self, pattern: str) -> list[str]:
        """Extract text matching regex pattern."""
        full_text = self.extract_text()
        return re.findall(pattern, full_text)
    
    def extract_tables_simple(self, page_num: int = 0) -> list[list[str]]:
        """Simple table extraction (line-based)."""
        page = self.reader.pages[page_num]
        text = page.extract_text() or ""
        
        lines = text.split("\n")
        tables = []
        current_table = []
        
        for line in lines:
            # Detect table rows (multiple whitespace-separated values)
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 2:
                current_table.append(parts)
            elif current_table:
                if len(current_table) >= 2:
                    tables.append(current_table)
                current_table = []
        
        if current_table and len(current_table) >= 2:
            tables.append(current_table)
        
        return tables
    
    def search_text(self, query: str, case_sensitive: bool = False) -> list[dict]:
        """Search for text across all pages."""
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        for page_num, page in enumerate(self.reader.pages):
            text = page.extract_text() or ""
            matches = list(re.finditer(query, text, flags))
            
            for match in matches:
                # Get context around match
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                results.append({
                    "page": page_num + 1,
                    "match": match.group(),
                    "context": context.strip(),
                    "position": match.start()
                })
        
        return results


# Usage
if __name__ == "__main__":
    extractor = PDFExtractor("document.pdf")
    
    print(f"Pages: {extractor.num_pages}")
    print(f"Metadata: {extractor.metadata}")
    
    # Extract all text
    text = extractor.extract_text()
    print(f"Text length: {len(text)} characters")
    
    # Search for patterns
    emails = extractor.extract_text_by_pattern(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    print(f"Found emails: {emails}")
```

### Creating PDFs with ReportLab

```python
# pdf_generator.py
"""Generate PDFs with ReportLab."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime


class PDFReportGenerator:
    """Generate professional PDF reports."""
    
    def __init__(self, output_path: str | Path, pagesize=letter):
        self.output_path = Path(output_path)
        self.pagesize = pagesize
        self.elements = []
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Define custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name="CustomSubtitle",
            parent=self.styles["Normal"],
            fontSize=14,
            textColor=colors.grey,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name="SectionHeader",
            parent=self.styles["Heading2"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2c3e50")
        ))
    
    def add_title(self, title: str, subtitle: str | None = None):
        """Add report title and optional subtitle."""
        self.elements.append(Paragraph(title, self.styles["CustomTitle"]))
        
        if subtitle:
            self.elements.append(Paragraph(subtitle, self.styles["CustomSubtitle"]))
        
        self.elements.append(Spacer(1, 20))
    
    def add_section(self, title: str, content: str):
        """Add a section with header and content."""
        self.elements.append(Paragraph(title, self.styles["SectionHeader"]))
        self.elements.append(Paragraph(content, self.styles["Normal"]))
        self.elements.append(Spacer(1, 12))
    
    def add_table(
        self,
        data: list[list],
        col_widths: list[float] | None = None,
        header_bg: str = "#3498db",
        alternate_rows: bool = True
    ):
        """Add formatted table."""
        if not data:
            return
        
        table = Table(data, colWidths=col_widths)
        
        style_commands = [
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TOPPADDING", (0, 0), (-1, 0), 12),
            
            # Body styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternate row colors
        if alternate_rows:
            for i in range(1, len(data)):
                if i % 2 == 0:
                    style_commands.append(
                        ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#ecf0f1"))
                    )
        
        table.setStyle(TableStyle(style_commands))
        self.elements.append(table)
        self.elements.append(Spacer(1, 20))
    
    def add_bullet_list(self, items: list[str]):
        """Add bullet point list."""
        list_items = [
            ListItem(Paragraph(item, self.styles["Normal"]))
            for item in items
        ]
        
        bullet_list = ListFlowable(
            list_items,
            bulletType="bullet",
            leftIndent=20
        )
        
        self.elements.append(bullet_list)
        self.elements.append(Spacer(1, 12))
    
    def add_image(self, image_path: str | Path, width: float = 4 * inch):
        """Add image to report."""
        img = Image(str(image_path))
        
        # Maintain aspect ratio
        aspect = img.imageHeight / img.imageWidth
        img.drawWidth = width
        img.drawHeight = width * aspect
        
        self.elements.append(img)
        self.elements.append(Spacer(1, 12))
    
    def add_page_break(self):
        """Add page break."""
        self.elements.append(PageBreak())
    
    def build(self):
        """Build and save PDF."""
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        doc.build(self.elements)
        return self.output_path


# Usage
if __name__ == "__main__":
    report = PDFReportGenerator("monthly_report.pdf")
    
    report.add_title(
        "Monthly Sales Report",
        f"Generated on {datetime.now().strftime('%B %d, %Y')}"
    )
    
    report.add_section(
        "Executive Summary",
        "This report provides an overview of sales performance for the current month. "
        "Overall, we exceeded targets by 15% with strong growth in the North region."
    )
    
    report.add_section("Key Highlights", "")
    report.add_bullet_list([
        "Total revenue: $1.5M (+15% vs target)",
        "New customers acquired: 150",
        "Customer retention rate: 95%",
        "Top performing region: North (+22%)"
    ])
    
    report.add_section("Sales by Region", "")
    report.add_table([
        ["Region", "Sales", "Target", "Variance"],
        ["North", "$500,000", "$410,000", "+22%"],
        ["South", "$350,000", "$340,000", "+3%"],
        ["East", "$400,000", "$380,000", "+5%"],
        ["West", "$250,000", "$270,000", "-7%"],
    ])
    
    output = report.build()
    print(f"Report saved to: {output}")
```

### PDF Manipulation

```python
# pdf_manipulation.py
"""PDF manipulation: merge, split, watermark."""
from pathlib import Path
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io


class PDFManipulator:
    """Merge, split, and modify PDFs."""
    
    @staticmethod
    def merge_pdfs(input_paths: list[Path], output_path: Path):
        """Merge multiple PDFs into one."""
        writer = PdfWriter()
        
        for pdf_path in input_paths:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path
    
    @staticmethod
    def split_pdf(input_path: Path, output_dir: Path, pages_per_file: int = 1):
        """Split PDF into multiple files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        reader = PdfReader(input_path)
        
        output_files = []
        
        for i in range(0, len(reader.pages), pages_per_file):
            writer = PdfWriter()
            
            for j in range(pages_per_file):
                if i + j < len(reader.pages):
                    writer.add_page(reader.pages[i + j])
            
            output_path = output_dir / f"{input_path.stem}_part{i // pages_per_file + 1}.pdf"
            
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            
            output_files.append(output_path)
        
        return output_files
    
    @staticmethod
    def extract_pages(input_path: Path, output_path: Path, page_numbers: list[int]):
        """Extract specific pages to new PDF."""
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page_num in page_numbers:
            if 0 <= page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path
    
    @staticmethod
    def add_watermark(
        input_path: Path,
        output_path: Path,
        watermark_text: str,
        opacity: float = 0.3
    ):
        """Add text watermark to all pages."""
        # Create watermark PDF in memory
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        
        # Configure watermark
        c.setFont("Helvetica", 50)
        c.setFillAlpha(opacity)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        
        # Rotate and center
        c.translate(letter[0] / 2, letter[1] / 2)
        c.rotate(45)
        c.drawCentredString(0, 0, watermark_text)
        
        c.save()
        packet.seek(0)
        
        watermark_reader = PdfReader(packet)
        watermark_page = watermark_reader.pages[0]
        
        # Apply to all pages
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path
    
    @staticmethod
    def add_page_numbers(input_path: Path, output_path: Path):
        """Add page numbers to PDF."""
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page_num, page in enumerate(reader.pages, 1):
            # Create page number overlay
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=letter)
            c.setFont("Helvetica", 10)
            c.drawCentredString(letter[0] / 2, 30, f"Page {page_num}")
            c.save()
            packet.seek(0)
            
            overlay = PdfReader(packet).pages[0]
            page.merge_page(overlay)
            writer.add_page(page)
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path
    
    @staticmethod
    def encrypt_pdf(
        input_path: Path,
        output_path: Path,
        user_password: str,
        owner_password: str | None = None
    ):
        """Encrypt PDF with password protection."""
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        writer.encrypt(
            user_password=user_password,
            owner_password=owner_password or user_password,
            permissions_flag=0  # Restrict all permissions
        )
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path


# Usage
if __name__ == "__main__":
    manipulator = PDFManipulator()
    
    # Merge PDFs
    manipulator.merge_pdfs(
        [Path("doc1.pdf"), Path("doc2.pdf")],
        Path("merged.pdf")
    )
    
    # Add watermark
    manipulator.add_watermark(
        Path("document.pdf"),
        Path("watermarked.pdf"),
        "CONFIDENTIAL"
    )
```

---

## Word Document Automation

### Creating Word Documents

```python
# word_generator.py
"""Generate Word documents with python-docx."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from datetime import datetime


class WordDocumentBuilder:
    """Build Word documents programmatically."""
    
    def __init__(self):
        self.document = Document()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configure document styles."""
        styles = self.document.styles
        
        # Modify Normal style
        normal = styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(11)
    
    def add_title(self, title: str, subtitle: str | None = None):
        """Add document title."""
        heading = self.document.add_heading(title, level=0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        if subtitle:
            para = self.document.add_paragraph(subtitle)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.runs[0].font.color.rgb = RGBColor(128, 128, 128)
    
    def add_heading(self, text: str, level: int = 1):
        """Add section heading."""
        self.document.add_heading(text, level=level)
    
    def add_paragraph(
        self,
        text: str,
        bold: bool = False,
        italic: bool = False,
        alignment: str = "left"
    ):
        """Add paragraph with formatting."""
        para = self.document.add_paragraph()
        run = para.add_run(text)
        run.bold = bold
        run.italic = italic
        
        align_map = {
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
            "justify": WD_ALIGN_PARAGRAPH.JUSTIFY
        }
        para.alignment = align_map.get(alignment, WD_ALIGN_PARAGRAPH.LEFT)
        
        return para
    
    def add_bullet_list(self, items: list[str]):
        """Add bulleted list."""
        for item in items:
            self.document.add_paragraph(item, style="List Bullet")
    
    def add_numbered_list(self, items: list[str]):
        """Add numbered list."""
        for item in items:
            self.document.add_paragraph(item, style="List Number")
    
    def add_table(
        self,
        data: list[list],
        header_row: bool = True,
        col_widths: list[float] | None = None
    ):
        """Add formatted table."""
        if not data:
            return None
        
        num_cols = len(data[0])
        table = self.document.add_table(rows=0, cols=num_cols)
        table.style = "Table Grid"
        
        for row_idx, row_data in enumerate(data):
            row = table.add_row()
            
            for col_idx, cell_value in enumerate(row_data):
                cell = row.cells[col_idx]
                cell.text = str(cell_value) if cell_value is not None else ""
                
                # Style header row
                if row_idx == 0 and header_row:
                    cell.paragraphs[0].runs[0].bold = True
                    shading = cell._element.get_or_add_tcPr()
        
        # Set column widths
        if col_widths:
            for idx, width in enumerate(col_widths):
                for row in table.rows:
                    row.cells[idx].width = Inches(width)
        
        return table
    
    def add_image(
        self,
        image_path: str | Path,
        width: float = 4.0,
        caption: str | None = None
    ):
        """Add image with optional caption."""
        self.document.add_picture(str(image_path), width=Inches(width))
        
        if caption:
            para = self.document.add_paragraph(caption)
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.runs[0].font.italic = True
            para.runs[0].font.size = Pt(10)
    
    def add_page_break(self):
        """Add page break."""
        self.document.add_page_break()
    
    def add_hyperlink(self, text: str, url: str):
        """Add hyperlink."""
        para = self.document.add_paragraph()
        
        # Create hyperlink element
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        
        part = para.part
        r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
        
        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)
        
        new_run = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        
        # Blue underlined text
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "0000FF")
        rPr.append(color)
        
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)
        
        new_run.append(rPr)
        text_elem = OxmlElement("w:t")
        text_elem.text = text
        new_run.append(text_elem)
        
        hyperlink.append(new_run)
        para._p.append(hyperlink)
        
        return para
    
    def save(self, filepath: str | Path):
        """Save document."""
        self.document.save(str(filepath))
        return Path(filepath)


# Usage
if __name__ == "__main__":
    doc = WordDocumentBuilder()
    
    doc.add_title("Project Proposal", "Q4 2024 Initiative")
    
    doc.add_heading("Executive Summary")
    doc.add_paragraph(
        "This proposal outlines the key initiatives for Q4 2024, "
        "focusing on automation and efficiency improvements."
    )
    
    doc.add_heading("Key Objectives")
    doc.add_bullet_list([
        "Reduce manual processing time by 50%",
        "Implement automated reporting",
        "Improve data accuracy to 99.9%"
    ])
    
    doc.add_heading("Timeline")
    doc.add_table([
        ["Phase", "Start Date", "End Date", "Status"],
        ["Planning", "Oct 1", "Oct 15", "Complete"],
        ["Development", "Oct 16", "Nov 30", "In Progress"],
        ["Testing", "Dec 1", "Dec 15", "Pending"],
        ["Deployment", "Dec 16", "Dec 31", "Pending"]
    ])
    
    doc.save("proposal.docx")
```

### Document Templates with Jinja2

```python
# word_templates.py
"""Word document templates with mail merge."""
from pathlib import Path
from docx import Document
from jinja2 import Template
import re


class DocumentTemplateEngine:
    """Mail merge and template processing for Word docs."""
    
    def __init__(self, template_path: str | Path):
        self.template_path = Path(template_path)
        self.document = Document(self.template_path)
    
    def get_placeholders(self) -> list[str]:
        """Extract all placeholders from template."""
        placeholders = set()
        pattern = r"\{\{(\w+)\}\}"
        
        # Check paragraphs
        for para in self.document.paragraphs:
            matches = re.findall(pattern, para.text)
            placeholders.update(matches)
        
        # Check tables
        for table in self.document.tables:
            for row in table.rows:
                for cell in row.cells:
                    matches = re.findall(pattern, cell.text)
                    placeholders.update(matches)
        
        return list(placeholders)
    
    def render(self, data: dict) -> Document:
        """Render template with data."""
        # Process paragraphs
        for para in self.document.paragraphs:
            self._replace_in_paragraph(para, data)
        
        # Process tables
        for table in self.document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        self._replace_in_paragraph(para, data)
        
        return self.document
    
    def _replace_in_paragraph(self, paragraph, data: dict):
        """Replace placeholders in paragraph while preserving formatting."""
        full_text = paragraph.text
        
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in full_text:
                full_text = full_text.replace(placeholder, str(value))
        
        # Only update if changes were made
        if full_text != paragraph.text:
            # Clear existing runs
            for run in paragraph.runs:
                run.text = ""
            
            # Set new text in first run (or create one)
            if paragraph.runs:
                paragraph.runs[0].text = full_text
            else:
                paragraph.add_run(full_text)
    
    def save(self, output_path: str | Path):
        """Save rendered document."""
        self.document.save(str(output_path))
        return Path(output_path)
    
    @classmethod
    def batch_render(
        cls,
        template_path: Path,
        data_list: list[dict],
        output_dir: Path,
        filename_field: str = "name"
    ) -> list[Path]:
        """Render template for multiple records."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_files = []
        
        for data in data_list:
            engine = cls(template_path)
            engine.render(data)
            
            filename = data.get(filename_field, f"document_{len(output_files)}")
            safe_filename = re.sub(r'[^\w\-]', '_', str(filename))
            output_path = output_dir / f"{safe_filename}.docx"
            
            engine.save(output_path)
            output_files.append(output_path)
        
        return output_files


# Usage
if __name__ == "__main__":
    # Single document
    engine = DocumentTemplateEngine("letter_template.docx")
    print(f"Placeholders: {engine.get_placeholders()}")
    
    engine.render({
        "recipient_name": "John Smith",
        "company": "Acme Corp",
        "date": "January 15, 2024",
        "amount": "$5,000"
    })
    engine.save("letter_john_smith.docx")
    
    # Batch processing
    customers = [
        {"name": "Alice", "company": "Tech Inc", "amount": "$10,000"},
        {"name": "Bob", "company": "Data Corp", "amount": "$7,500"},
    ]
    
    output_files = DocumentTemplateEngine.batch_render(
        Path("letter_template.docx"),
        customers,
        Path("./output"),
        filename_field="name"
    )
    print(f"Generated {len(output_files)} documents")
```

---

## Email Automation

### IMAP Email Reading

```python
# email_reader.py
"""Read emails via IMAP."""
import asyncio
import email
from email.header import decode_header
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from aioimaplib import IMAP4_SSL
import structlog

logger = structlog.get_logger()


@dataclass
class EmailMessage:
    """Parsed email message."""
    uid: str
    subject: str
    sender: str
    date: datetime | None
    body_text: str
    body_html: str
    attachments: list[dict]
    
    def __repr__(self):
        return f"Email(from={self.sender}, subject={self.subject[:50]})"


class IMAPEmailReader:
    """Async IMAP email reader."""
    
    def __init__(self, host: str, username: str, password: str, port: int = 993):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client: IMAP4_SSL | None = None
    
    async def connect(self):
        """Connect and authenticate."""
        self.client = IMAP4_SSL(host=self.host, port=self.port)
        await self.client.wait_hello_from_server()
        await self.client.login(self.username, self.password)
        logger.info("Connected to IMAP", host=self.host)
    
    async def disconnect(self):
        """Logout and disconnect."""
        if self.client:
            await self.client.logout()
            logger.info("Disconnected from IMAP")
    
    async def list_folders(self) -> list[str]:
        """List all mailbox folders."""
        _, data = await self.client.list()
        folders = []
        
        for item in data:
            if isinstance(item, bytes):
                # Parse folder name from response
                parts = item.decode().split('" "')
                if len(parts) >= 2:
                    folders.append(parts[-1].strip('"'))
        
        return folders
    
    async def select_folder(self, folder: str = "INBOX") -> int:
        """Select mailbox folder, return message count."""
        _, data = await self.client.select(folder)
        return int(data[0])
    
    async def search_emails(
        self,
        folder: str = "INBOX",
        criteria: str = "ALL",
        limit: int = 10
    ) -> list[str]:
        """Search for emails matching criteria."""
        await self.select_folder(folder)
        _, data = await self.client.search(criteria)
        
        uids = data[0].split()
        return [uid.decode() for uid in uids[-limit:]]
    
    async def fetch_email(self, uid: str) -> EmailMessage:
        """Fetch and parse single email."""
        _, data = await self.client.fetch(uid, "(RFC822)")
        
        raw_email = data[1]
        msg = email.message_from_bytes(raw_email)
        
        # Parse headers
        subject = self._decode_header(msg["Subject"])
        sender = self._decode_header(msg["From"])
        date_str = msg["Date"]
        
        # Parse date
        date = None
        if date_str:
            try:
                date = email.utils.parsedate_to_datetime(date_str)
            except:
                pass
        
        # Parse body and attachments
        body_text = ""
        body_html = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    attachments.append({
                        "filename": filename,
                        "content_type": content_type,
                        "size": len(part.get_payload(decode=True) or b"")
                    })
                elif content_type == "text/plain":
                    body_text = part.get_payload(decode=True).decode(errors="ignore")
                elif content_type == "text/html":
                    body_html = part.get_payload(decode=True).decode(errors="ignore")
        else:
            body_text = msg.get_payload(decode=True).decode(errors="ignore")
        
        return EmailMessage(
            uid=uid,
            subject=subject,
            sender=sender,
            date=date,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments
        )
    
    async def download_attachments(
        self,
        uid: str,
        output_dir: Path,
        filename_filter: str | None = None
    ) -> list[Path]:
        """Download email attachments."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        _, data = await self.client.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(data[1])
        
        downloaded = []
        
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                
                if filename_filter and filename_filter not in filename:
                    continue
                
                filepath = output_dir / filename
                content = part.get_payload(decode=True)
                
                filepath.write_bytes(content)
                downloaded.append(filepath)
                logger.info("Downloaded attachment", filename=filename)
        
        return downloaded
    
    def _decode_header(self, header: str | None) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        result = []
        
        for content, charset in decoded_parts:
            if isinstance(content, bytes):
                result.append(content.decode(charset or "utf-8", errors="ignore"))
            else:
                result.append(content)
        
        return "".join(result)
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()


# Usage
async def main():
    async with IMAPEmailReader(
        host="imap.gmail.com",
        username="user@gmail.com",
        password="app_password"
    ) as reader:
        
        # List folders
        folders = await reader.list_folders()
        print(f"Folders: {folders}")
        
        # Search recent emails
        uids = await reader.search_emails(
            folder="INBOX",
            criteria="UNSEEN",
            limit=5
        )
        
        # Fetch and process
        for uid in uids:
            email_msg = await reader.fetch_email(uid)
            print(f"From: {email_msg.sender}")
            print(f"Subject: {email_msg.subject}")
            print(f"Attachments: {len(email_msg.attachments)}")


if __name__ == "__main__":
    asyncio.run(main())
```

### SMTP Email Sending

```python
# email_sender.py
"""Send emails via SMTP."""
import asyncio
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass, field
import aiosmtplib
import structlog
from jinja2 import Template

logger = structlog.get_logger()


@dataclass
class EmailComposer:
    """Compose email with attachments."""
    sender: str
    recipients: list[str]
    subject: str
    body_text: str = ""
    body_html: str = ""
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments: list[Path] = field(default_factory=list)
    reply_to: str | None = None
    
    def build_message(self) -> MIMEMultipart:
        """Build MIME message."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = self.subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        
        if self.cc:
            msg["Cc"] = ", ".join(self.cc)
        
        if self.reply_to:
            msg["Reply-To"] = self.reply_to
        
        # Add text body
        if self.body_text:
            msg.attach(MIMEText(self.body_text, "plain"))
        
        # Add HTML body
        if self.body_html:
            msg.attach(MIMEText(self.body_html, "html"))
        
        # Add attachments
        for attachment_path in self.attachments:
            self._attach_file(msg, attachment_path)
        
        return msg
    
    def _attach_file(self, msg: MIMEMultipart, filepath: Path):
        """Attach file to message."""
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={filepath.name}"
        )
        msg.attach(part)


class SMTPEmailSender:
    """Async SMTP email sender."""
    
    def __init__(
        self,
        host: str,
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    async def send(self, composer: EmailComposer) -> bool:
        """Send email."""
        try:
            message = composer.build_message()
            
            all_recipients = (
                composer.recipients +
                composer.cc +
                composer.bcc
            )
            
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls
            )
            
            logger.info(
                "Email sent",
                recipients=len(all_recipients),
                subject=composer.subject
            )
            return True
            
        except Exception as e:
            logger.error("Failed to send email", error=str(e))
            return False
    
    async def send_batch(
        self,
        template_text: str,
        template_html: str | None,
        recipients_data: list[dict],
        sender: str,
        subject_template: str,
        attachments: list[Path] | None = None,
        delay_seconds: float = 1.0
    ) -> dict:
        """Send batch emails with personalization."""
        results = {"sent": 0, "failed": 0, "errors": []}
        
        text_tmpl = Template(template_text)
        html_tmpl = Template(template_html) if template_html else None
        subject_tmpl = Template(subject_template)
        
        for data in recipients_data:
            recipient = data.get("email")
            if not recipient:
                continue
            
            composer = EmailComposer(
                sender=sender,
                recipients=[recipient],
                subject=subject_tmpl.render(**data),
                body_text=text_tmpl.render(**data),
                body_html=html_tmpl.render(**data) if html_tmpl else "",
                attachments=attachments or []
            )
            
            success = await self.send(composer)
            
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(recipient)
            
            # Rate limiting
            await asyncio.sleep(delay_seconds)
        
        return results


class EmailTemplates:
    """Pre-built email templates."""
    
    @staticmethod
    def notification(title: str, message: str, action_url: str | None = None) -> str:
        """Simple notification template."""
        action_html = ""
        if action_url:
            action_html = f'''
            <p style="text-align: center; margin-top: 20px;">
                <a href="{action_url}" 
                   style="background-color: #3498db; color: white; 
                          padding: 10px 20px; text-decoration: none;
                          border-radius: 5px;">
                    View Details
                </a>
            </p>
            '''
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #3498db; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{title}</h1>
            </div>
            <div style="padding: 20px; background-color: #f9f9f9;">
                <p>{message}</p>
                {action_html}
            </div>
            <div style="padding: 10px; text-align: center; color: #888; font-size: 12px;">
                This is an automated message.
            </div>
        </body>
        </html>
        '''
    
    @staticmethod
    def report(title: str, sections: list[dict]) -> str:
        """Report email template."""
        sections_html = ""
        for section in sections:
            sections_html += f'''
            <div style="margin-bottom: 20px;">
                <h3 style="color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 5px;">
                    {section["title"]}
                </h3>
                <p>{section["content"]}</p>
            </div>
            '''
        
        return f'''
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
            <h1 style="color: #2c3e50;">{title}</h1>
            {sections_html}
        </body>
        </html>
        '''


# Usage
async def main():
    sender = SMTPEmailSender(
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        password="app_password"
    )
    
    # Single email
    composer = EmailComposer(
        sender="user@gmail.com",
        recipients=["recipient@example.com"],
        subject="Test Email",
        body_text="This is a test email.",
        body_html=EmailTemplates.notification(
            "Hello!",
            "This is a test notification.",
            "https://example.com"
        )
    )
    
    await sender.send(composer)
    
    # Batch emails
    recipients = [
        {"email": "alice@example.com", "name": "Alice", "amount": "$100"},
        {"email": "bob@example.com", "name": "Bob", "amount": "$200"},
    ]
    
    results = await sender.send_batch(
        template_text="Hello {{name}}, your balance is {{amount}}.",
        template_html=None,
        recipients_data=recipients,
        sender="user@gmail.com",
        subject_template="Your Balance Update - {{name}}"
    )
    
    print(f"Sent: {results['sent']}, Failed: {results['failed']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## CSV Processing

### CSV Handler

```python
# csv_handler.py
"""CSV reading, writing, and transformation."""
import csv
from pathlib import Path
from typing import Iterator, Callable
import pandas as pd
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class CSVConfig:
    """CSV processing configuration."""
    delimiter: str = ","
    quotechar: str = '"'
    encoding: str = "utf-8"
    has_header: bool = True
    skip_rows: int = 0


class CSVProcessor:
    """Process CSV files efficiently."""
    
    def __init__(self, config: CSVConfig | None = None):
        self.config = config or CSVConfig()
    
    def read_rows(self, filepath: Path) -> Iterator[dict]:
        """Stream CSV rows as dictionaries."""
        with open(filepath, "r", encoding=self.config.encoding) as f:
            # Skip rows
            for _ in range(self.config.skip_rows):
                next(f, None)
            
            reader = csv.DictReader(
                f,
                delimiter=self.config.delimiter,
                quotechar=self.config.quotechar
            )
            
            for row in reader:
                yield row
    
    def read_to_dataframe(
        self,
        filepath: Path,
        usecols: list[str] | None = None,
        dtype: dict | None = None
    ) -> pd.DataFrame:
        """Read CSV to pandas DataFrame."""
        return pd.read_csv(
            filepath,
            delimiter=self.config.delimiter,
            quotechar=self.config.quotechar,
            encoding=self.config.encoding,
            skiprows=self.config.skip_rows,
            usecols=usecols,
            dtype=dtype
        )
    
    def write_rows(
        self,
        filepath: Path,
        rows: list[dict],
        fieldnames: list[str] | None = None
    ):
        """Write dictionaries to CSV."""
        if not rows:
            return
        
        fieldnames = fieldnames or list(rows[0].keys())
        
        with open(filepath, "w", encoding=self.config.encoding, newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=self.config.delimiter,
                quotechar=self.config.quotechar
            )
            
            if self.config.has_header:
                writer.writeheader()
            
            writer.writerows(rows)
    
    def transform(
        self,
        input_path: Path,
        output_path: Path,
        transform_fn: Callable[[dict], dict | None]
    ) -> int:
        """Transform CSV with custom function."""
        transformed_count = 0
        rows = []
        
        for row in self.read_rows(input_path):
            result = transform_fn(row)
            if result:
                rows.append(result)
                transformed_count += 1
        
        if rows:
            self.write_rows(output_path, rows)
        
        logger.info(
            "CSV transformation complete",
            input=str(input_path),
            output=str(output_path),
            rows=transformed_count
        )
        
        return transformed_count
    
    def merge_files(
        self,
        input_paths: list[Path],
        output_path: Path,
        dedup_column: str | None = None
    ):
        """Merge multiple CSV files."""
        all_rows = []
        seen_keys = set()
        
        for path in input_paths:
            for row in self.read_rows(path):
                if dedup_column:
                    key = row.get(dedup_column)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                
                all_rows.append(row)
        
        if all_rows:
            self.write_rows(output_path, all_rows)
        
        logger.info("Merged CSV files", count=len(input_paths), rows=len(all_rows))
    
    def split_by_column(
        self,
        input_path: Path,
        output_dir: Path,
        split_column: str
    ) -> dict[str, int]:
        """Split CSV by unique column values."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        groups: dict[str, list[dict]] = {}
        
        for row in self.read_rows(input_path):
            key = str(row.get(split_column, "unknown"))
            if key not in groups:
                groups[key] = []
            groups[key].append(row)
        
        counts = {}
        for key, rows in groups.items():
            safe_key = "".join(c if c.isalnum() else "_" for c in key)
            output_path = output_dir / f"{safe_key}.csv"
            self.write_rows(output_path, rows)
            counts[key] = len(rows)
        
        return counts
    
    def validate(
        self,
        filepath: Path,
        required_columns: list[str],
        validators: dict[str, Callable] | None = None
    ) -> dict:
        """Validate CSV file."""
        errors = []
        row_count = 0
        
        try:
            for idx, row in enumerate(self.read_rows(filepath), 1):
                row_count = idx
                
                # Check required columns
                for col in required_columns:
                    if col not in row or not row[col]:
                        errors.append(f"Row {idx}: Missing required column '{col}'")
                
                # Run validators
                if validators:
                    for col, validator in validators.items():
                        if col in row:
                            try:
                                if not validator(row[col]):
                                    errors.append(f"Row {idx}: Invalid value in '{col}'")
                            except Exception as e:
                                errors.append(f"Row {idx}: Validation error in '{col}': {e}")
        
        except Exception as e:
            errors.append(f"File error: {e}")
        
        return {
            "valid": len(errors) == 0,
            "rows": row_count,
            "errors": errors[:20],  # Limit errors
            "total_errors": len(errors)
        }


# Usage
if __name__ == "__main__":
    processor = CSVProcessor()
    
    # Transform CSV
    def clean_row(row):
        return {
            "name": row["name"].strip().title(),
            "email": row["email"].strip().lower(),
            "amount": float(row["amount"].replace("$", "").replace(",", ""))
        }
    
    processor.transform(
        Path("input.csv"),
        Path("output.csv"),
        clean_row
    )
    
    # Validate CSV
    result = processor.validate(
        Path("data.csv"),
        required_columns=["name", "email"],
        validators={
            "email": lambda x: "@" in x,
            "amount": lambda x: float(x) >= 0
        }
    )
    
    print(f"Valid: {result['valid']}, Errors: {result['total_errors']}")
```

---

## Document Workflows

### End-to-End Document Pipeline

```python
# document_workflow.py
"""Complete document automation workflow."""
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import structlog

from excel_basics import ExcelHandler
from pdf_generator import PDFReportGenerator
from word_generator import WordDocumentBuilder
from email_sender import SMTPEmailSender, EmailComposer
from csv_handler import CSVProcessor

logger = structlog.get_logger()


class DocumentType(Enum):
    EXCEL = "excel"
    PDF = "pdf"
    WORD = "word"


@dataclass
class WorkflowResult:
    success: bool
    output_path: Path | None
    error: str | None = None


class DocumentWorkflow:
    """Orchestrate document generation and distribution."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_report(
        self,
        data_source: Path,
        doc_type: DocumentType,
        template: str | None = None
    ) -> WorkflowResult:
        """Generate report from data source."""
        try:
            # Load data
            csv_processor = CSVProcessor()
            df = csv_processor.read_to_dataframe(data_source)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if doc_type == DocumentType.EXCEL:
                output_path = self.output_dir / f"report_{timestamp}.xlsx"
                handler = ExcelHandler(output_path)
                handler.create_workbook()
                handler.write_dataframe(df, "Data")
                handler.apply_formatting("Data", "A1:Z1", bold=True, bg_color="4472C4")
                handler.save()
                
            elif doc_type == DocumentType.PDF:
                output_path = self.output_dir / f"report_{timestamp}.pdf"
                report = PDFReportGenerator(output_path)
                report.add_title("Data Report", f"Generated: {datetime.now()}")
                
                # Convert DataFrame to table data
                table_data = [df.columns.tolist()] + df.values.tolist()
                report.add_table(table_data[:50])  # Limit rows
                report.build()
                
            elif doc_type == DocumentType.WORD:
                output_path = self.output_dir / f"report_{timestamp}.docx"
                doc = WordDocumentBuilder()
                doc.add_title("Data Report")
                
                table_data = [df.columns.tolist()] + df.head(50).values.tolist()
                doc.add_table(table_data)
                doc.save(output_path)
            
            logger.info("Report generated", path=str(output_path))
            return WorkflowResult(success=True, output_path=output_path)
            
        except Exception as e:
            logger.error("Report generation failed", error=str(e))
            return WorkflowResult(success=False, output_path=None, error=str(e))
    
    async def process_and_distribute(
        self,
        data_source: Path,
        recipients: list[str],
        smtp_config: dict,
        doc_types: list[DocumentType] = None
    ) -> dict:
        """Generate reports and email to recipients."""
        doc_types = doc_types or [DocumentType.EXCEL, DocumentType.PDF]
        
        results = {
            "documents": [],
            "email_sent": False,
            "errors": []
        }
        
        # Generate documents
        attachments = []
        for doc_type in doc_types:
            result = await self.generate_report(data_source, doc_type)
            results["documents"].append({
                "type": doc_type.value,
                "success": result.success,
                "path": str(result.output_path) if result.output_path else None
            })
            
            if result.success and result.output_path:
                attachments.append(result.output_path)
        
        # Send email if documents generated
        if attachments:
            try:
                sender = SMTPEmailSender(**smtp_config)
                
                composer = EmailComposer(
                    sender=smtp_config.get("username", "noreply@example.com"),
                    recipients=recipients,
                    subject=f"Report - {datetime.now().strftime('%Y-%m-%d')}",
                    body_text="Please find the attached reports.",
                    attachments=attachments
                )
                
                email_success = await sender.send(composer)
                results["email_sent"] = email_success
                
            except Exception as e:
                results["errors"].append(f"Email error: {e}")
        
        return results


# Usage
async def main():
    workflow = DocumentWorkflow(Path("./reports"))
    
    # Generate single report
    result = await workflow.generate_report(
        data_source=Path("sales_data.csv"),
        doc_type=DocumentType.EXCEL
    )
    print(f"Generated: {result.output_path}")
    
    # Full workflow with distribution
    results = await workflow.process_and_distribute(
        data_source=Path("sales_data.csv"),
        recipients=["manager@company.com"],
        smtp_config={
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "reports@company.com",
            "password": "app_password"
        },
        doc_types=[DocumentType.EXCEL, DocumentType.PDF]
    )
    
    print(f"Documents: {len(results['documents'])}")
    print(f"Email sent: {results['email_sent']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Templates and Mail Merge

### Data-Driven Document Generation

```python
# mail_merge.py
"""Mail merge for batch document generation."""
import asyncio
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import structlog

from word_generator import WordDocumentBuilder
from pdf_generator import PDFReportGenerator
from email_sender import SMTPEmailSender, EmailComposer

logger = structlog.get_logger()


class MailMergeEngine:
    """Generate personalized documents from templates."""
    
    def __init__(self, template_dir: Path, output_dir: Path):
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def generate_word_documents(
        self,
        template_name: str,
        records: list[dict],
        filename_field: str = "id"
    ) -> list[Path]:
        """Generate Word documents for each record."""
        from word_templates import DocumentTemplateEngine
        
        template_path = self.template_dir / template_name
        
        return DocumentTemplateEngine.batch_render(
            template_path,
            records,
            self.output_dir,
            filename_field
        )
    
    def generate_pdf_letters(
        self,
        records: list[dict],
        letter_template: str,
        filename_field: str = "id"
    ) -> list[Path]:
        """Generate PDF letters for each record."""
        template = self.jinja_env.from_string(letter_template)
        output_files = []
        
        for record in records:
            content = template.render(**record)
            filename = f"{record.get(filename_field, 'doc')}.pdf"
            output_path = self.output_dir / filename
            
            report = PDFReportGenerator(output_path)
            report.add_paragraph(content)
            report.build()
            
            output_files.append(output_path)
        
        return output_files
    
    async def merge_and_email(
        self,
        records: list[dict],
        email_template_text: str,
        email_template_html: str,
        subject_template: str,
        smtp_config: dict,
        sender_email: str,
        attachment_generator: callable | None = None,
        delay_seconds: float = 1.0
    ) -> dict:
        """Generate and email personalized documents."""
        text_tmpl = self.jinja_env.from_string(email_template_text)
        html_tmpl = self.jinja_env.from_string(email_template_html)
        subject_tmpl = self.jinja_env.from_string(subject_template)
        
        sender = SMTPEmailSender(**smtp_config)
        
        results = {"sent": 0, "failed": 0, "errors": []}
        
        for record in records:
            email_address = record.get("email")
            if not email_address:
                continue
            
            # Generate attachment if needed
            attachments = []
            if attachment_generator:
                try:
                    attachment = attachment_generator(record, self.output_dir)
                    if attachment:
                        attachments.append(attachment)
                except Exception as e:
                    logger.error("Attachment generation failed", error=str(e))
            
            # Compose email
            composer = EmailComposer(
                sender=sender_email,
                recipients=[email_address],
                subject=subject_tmpl.render(**record),
                body_text=text_tmpl.render(**record),
                body_html=html_tmpl.render(**record),
                attachments=attachments
            )
            
            success = await sender.send(composer)
            
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(email_address)
            
            await asyncio.sleep(delay_seconds)
        
        return results


# Invoice generator example
def generate_invoice(record: dict, output_dir: Path) -> Path:
    """Generate invoice PDF for record."""
    output_path = output_dir / f"invoice_{record['id']}.pdf"
    
    report = PDFReportGenerator(output_path)
    report.add_title(f"Invoice #{record['id']}")
    
    report.add_section("Bill To", f"{record['name']}\n{record.get('address', '')}")
    
    report.add_table([
        ["Description", "Quantity", "Price", "Total"],
        [record.get("product", "Service"), "1", record.get("amount", "0"), record.get("amount", "0")]
    ])
    
    report.add_section("Total Due", f"${record.get('amount', 0)}")
    report.build()
    
    return output_path


# Usage
async def main():
    engine = MailMergeEngine(
        template_dir=Path("./templates"),
        output_dir=Path("./output")
    )
    
    customers = [
        {"id": "001", "name": "Alice Smith", "email": "alice@example.com", "amount": "500", "product": "Consulting"},
        {"id": "002", "name": "Bob Jones", "email": "bob@example.com", "amount": "750", "product": "Development"},
    ]
    
    results = await engine.merge_and_email(
        records=customers,
        email_template_text="Dear {{name}},\n\nPlease find your invoice attached.\n\nAmount due: ${{amount}}",
        email_template_html="<p>Dear {{name}},</p><p>Please find your invoice attached.</p><p><strong>Amount due: ${{amount}}</strong></p>",
        subject_template="Invoice #{{id}} - {{name}}",
        smtp_config={
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "billing@company.com",
            "password": "app_password"
        },
        sender_email="billing@company.com",
        attachment_generator=generate_invoice
    )
    
    print(f"Sent: {results['sent']}, Failed: {results['failed']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Dependencies

```bash
# Install all document automation dependencies
uv add openpyxl pandas xlsxwriter xlrd
uv add pypdf reportlab
uv add python-docx
uv add aiosmtplib aioimaplib email-validator
uv add jinja2 structlog

# Optional: Advanced PDF features
uv add fillpdf pypdf[crypto]

# Optional: OCR for scanned documents
uv add pytesseract pdf2image
```

---

## Best Practices

### 1. Memory Management
```python
# Stream large files instead of loading entirely
def process_large_csv(filepath: Path):
    for chunk in pd.read_csv(filepath, chunksize=10000):
        process_chunk(chunk)
```

### 2. Error Handling
```python
# Always wrap document operations
try:
    workbook = load_workbook(path)
except FileNotFoundError:
    logger.error("File not found", path=str(path))
except PermissionError:
    logger.error("Permission denied", path=str(path))
finally:
    if workbook:
        workbook.close()
```

### 3. Validation Before Processing
```python
# Validate before expensive operations
def validate_excel(path: Path) -> bool:
    try:
        wb = load_workbook(path, read_only=True)
        required_sheets = ["Data", "Config"]
        return all(s in wb.sheetnames for s in required_sheets)
    except:
        return False
```

### 4. Cleanup Temporary Files
```python
import tempfile
from contextlib import contextmanager

@contextmanager
def temp_document():
    temp_path = Path(tempfile.mktemp(suffix=".xlsx"))
    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)
```
