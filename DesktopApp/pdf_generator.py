from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
import os

class PDFInvoiceGenerator:
    def __init__(self, output_path, invoice_data):
        self.output_path = output_path
        self.data = invoice_data
        # A5 Landscape: 210mm wide x 148mm high
        self.c = canvas.Canvas(output_path, pagesize=landscape(A5))
        self.width, self.height = landscape(A5)
        # Margins
        self.left = 10 * mm
        self.right = self.width - 10 * mm
        self.top = self.height - 10 * mm
        self.bottom = 10 * mm
        self.y = self.top

    def generate(self):
        self.draw_header()
        self.draw_meta()
        self.draw_table()
        self.draw_totals()
        self.draw_footer()
        try:
            self.c.save()
        except: pass
        return self.output_path

    def draw_header(self):
        # 1. Pharmacy Name (Centered, Bold, Largest)
        self.c.setFont("Helvetica-Bold", 16)
        name = self.data.get('pharmacy_name', 'PHARMACY NAME').upper()
        self.c.drawCentredString(self.width/2, self.y, name)
        self.y -= 6 * mm

        # 2. Address (Centered)
        self.c.setFont("Helvetica", 10)
        address = self.data.get('pharmacy_address', 'Address')
        self.c.drawCentredString(self.width/2, self.y, address)
        self.y -= 5 * mm

        # 3. PAN + ODA (Centered) - "PAN: ... | Oda: ..."
        pan = self.data.get('pan_number', '-')
        oda = self.data.get('oda_number', '-')
        contact = self.data.get('pharmacy_contact', '-')
        # Formatting: PAN: xxx | Oda: xxx | Ph: xxx
        meta_line = f"PAN: {pan}"
        if oda and oda != '-': meta_line += f" | ODA: {oda}"
        if contact and contact != '-': meta_line += f" | Ph: {contact}"
        
        self.c.drawCentredString(self.width/2, self.y, meta_line)
        self.y -= 3 * mm

        # 4. Separator Line
        self.c.setLineWidth(0.5)
        self.c.line(self.left, self.y, self.right, self.y)
        self.y -= 5 * mm

        # 5. Title "PHARMACY RECEIPT"
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawCentredString(self.width/2, self.y, "PHARMACY RECEIPT")
        self.y -= 8 * mm

    def draw_meta(self):
        # 2 Columns of Meta Data
        # Left: Invoice No, Date, Payment Method
        # Right: Customer Name, Phone, Sex
        
        start_y = self.y
        col1_x = self.left + 5 * mm
        col2_x = self.width / 2 + 5 * mm
        
        self.c.setFont("Helvetica-Bold", 9)
        
        # Left Col
        self.c.drawString(col1_x, self.y, f"Invoice No: {self.data.get('bill_number', '-')}")
        self.y -= 4 * mm
        created_at = self.data.get('created_at', '') # Should be YYYY-MM-DD
        # If created_at contains time, maybe split? User said "Invoice Date" input.
        # Ensure it fits "Invoice Date" label from input if present, else created_at
        inv_date = self.data.get('invoice_date', created_at)
        self.c.drawString(col1_x, self.y, f"Date: {inv_date}")
        self.y -= 4 * mm
        self.c.drawString(col1_x, self.y, f"Pay Mode: {self.data.get('payment_category', 'CASH')}")
        
        # Right Col (Reset Y)
        self.y = start_y
        self.c.drawString(col2_x, self.y, f"Customer: {self.data.get('customer_name', 'Walk-in')}")
        self.y -= 4 * mm
        self.c.drawString(col2_x, self.y, f"Phone: {self.data.get('customer_contact', '-')}")
        self.y -= 4 * mm
        self.c.drawString(col2_x, self.y, f"Sex: {self.data.get('customer_sex', '-')}")
        
        self.y -= 8 * mm # Space before table

    def draw_table(self):
        # Columns: S.N, Particulars, Batch, Exp, Rate, Qty, Amount
        # Widths (Total ~190mm avail): 
        # S.N(8), Particulars(60), Batch(20), Exp(20), Rate(18), Qty(12), Amount(22) -> Sum = 160. fits easily in 190.
        
        cols = [
            ("S.N", 8*mm), 
            ("Particulars", 70*mm), 
            ("Batch", 22*mm), 
            ("Exp", 20*mm), 
            ("Rate", 18*mm), 
            ("Qty", 12*mm), 
            ("Amount", 25*mm)
        ]
        
        # Header Background
        self.c.setFillColor(colors.lightgrey)
        self.c.rect(self.left, self.y - 2*mm, self.right - self.left, 6*mm, fill=1, stroke=0)
        self.c.setFillColor(colors.black)
        
        # Header Text
        x = self.left
        self.c.setFont("Helvetica-Bold", 8)
        for name, w in cols:
            # Center header text in col roughly?
            self.c.drawString(x + 1*mm, self.y, name)
            x += w
            
        self.y -= 6 * mm
        
        # Rows
        self.c.setFont("Helvetica", 8)
        items = self.data.get('items', [])
        
        for i, item in enumerate(items):
            x = self.left
            
            # Data extraction
            # item keys might be 'name' or 'medicine_name', 'qty' or 'quantity' depending on source
            # The 'process_sale' payload maps keys.
            name = item.get('name', item.get('medicine_name', ''))[:35]
            batch = item.get('batch', item.get('batch_number', ''))
            exp = item.get('expiry', item.get('expiry_date', ''))
            qty = item.get('qty', item.get('quantity', 0))
            rate = float(item.get('rate', item.get('selling_price', item.get('unit_price', 0))))
            amount = qty * rate
            
            vals = [
                str(i+1),
                name,
                batch,
                exp,
                f"{rate:.2f}",
                str(qty),
                f"{amount:.2f}"
            ]
            
            # Draw
            for (col_name, w), val in zip(cols, vals):
                self.c.drawString(x + 1*mm, self.y, str(val))
                x += w
                
            self.y -= 5 * mm
            
            # Page Break Check (Minimal implementation)
            if self.y < 35 * mm:
                self.c.showPage()
                self.y = self.height - 10 * mm
                self.draw_header() # Repeat header? Maybe simplified
                self.y -= 10 * mm

    def draw_totals(self):
        # Bottom Right
        self.y -= 2 * mm
        self.c.line(self.left, self.y, self.right, self.y)
        self.y -= 5 * mm
        
        x_label = self.right - 60 * mm
        x_val = self.right - 10 * mm
        
        # Subtotal comes from data
        total = float(self.data.get('total_amount', 0))
        discount = float(self.data.get('discount_amount', 0))
        grand = float(self.data.get('grand_total', total - discount))
        
        self.c.setFont("Helvetica", 9)
        
        # Total
        self.c.drawString(x_label, self.y, "Total:")
        self.c.drawRightString(x_val, self.y, f"{total:.2f}")
        self.y -= 4 * mm
        
        # Discount
        if discount > 0:
            self.c.drawString(x_label, self.y, "Discount:")
            self.c.drawRightString(x_val, self.y, f"{discount:.2f}")
            self.y -= 4 * mm
            
        # Grand Total
        self.c.setFont("Helvetica-Bold", 10)
        self.c.drawString(x_label, self.y, "Grand Total:")
        self.c.drawRightString(x_val, self.y, f"Rs. {grand:,.2f}")
        
    def draw_footer(self):
        # Bottom Left: Cashier Name
        # Bottom Right/Center: Thank you
        
        y_foot = 10 * mm
        self.c.setFont("Helvetica", 8)
        self.c.drawString(self.left, y_foot, f"Cashier: {self.data.get('sold_by', 'Staff')}")
        
        self.c.drawCentredString(self.width/2, y_foot, "Thank You! Get Well Soon.")

def generate_invoice(data, path):
    gen = PDFInvoiceGenerator(path, data)
    return gen.generate()
