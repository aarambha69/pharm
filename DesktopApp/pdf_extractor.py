import pdfplumber
import re
from datetime import datetime

class InvoiceExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.metadata = {}
        self.items = []
        self.is_valid_template = False
        
    def extract(self):
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[0]
                text = page.extract_text()
                
                # Check for hidden white text? pdfplumber extracts all text usually
                # Or check strict strings
                if "TEMPLATE_ID:AARAMBHA_A4_V1" in text:
                    self.is_valid_template = True
                    return self._extract_template_mode(page)
                else:
                    return self._extract_generic_mode(page)
        except Exception as e:
            return {"error": str(e)}

    def _extract_template_mode(self, page):
        text = page.extract_text()
        
        # 1. Meta
        inv_match = re.search(r"INV_NO:([^\s]+)", text)
        date_match = re.search(r"DATE:([^\n]+)", text)
        
        # 2. Table extraction (Coordinates based on Generator)
        # We know table starts roughly after header.
        # ReportLab coordinates are Bottom-Left origin, but pdfplumber is Top-Left.
        # We need to define bounding box for table.
        # Or better: search for "SN Product Batch" header line
        
        table_settings = {
            "vertical_strategy": "text", 
            "horizontal_strategy": "text",
        }
        tables = page.extract_tables(table_settings)
        
        # Process tables to find the items table
        items_data = []
        for table in tables:
            # Check header
            if table[0] and "SN" in str(table[0]) and "Product" in str(table[0]):
                # This is items table
                for row in table[1:]:
                    # row: [SN, Product, Batch, Exp, Qty, Rate, Amount] (approx)
                    if not row[0]: continue # Skip empty
                    # Clean vals
                    try:
                        clean_row = [str(c).strip() if c else "" for c in row]
                        # Merge if needed
                        items_data.append(clean_row)
                    except: pass
                    
        return {
            "template": "AARAMBHA_A4_V1",
            "invoice_no": inv_match.group(1) if inv_match else "Unknown",
            "date": date_match.group(1) if date_match else "Unknown",
            "items": items_data,
            "raw_text": text[:200] + "..."
        }

    def _extract_generic_mode(self, page):
        # Fallback
        return {
            "template": "Generic (Unknown)",
            "warning": "Template ID not found. Extraction may be inaccurate.",
            "items": [],
            "raw_text": page.extract_text()[:500]
        }
