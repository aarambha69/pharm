from pdf_generator import generate_invoice
import os

# Dummy Data for Testing
data = {
    "bill_number": "INV-TEST-001",
    "created_at": "2082-10-01 10:30 AM",
    "invoice_date": "2082-10-01",
    "pharmacy_name": "Hamro Pharmacy One",
    "pharmacy_address": "Kathmandu, Nepal",
    "pharmacy_contact": "9812345678",
    "pan_number": "PAN-12345",
    "oda_number": "ODA-9876",
    "customer_name": "Ram Bahadur",
    "customer_contact": "9800000000",
    "customer_sex": "Male",
    "payment_category": "CASH",
    "items": [
        {"medicine_name": "Paracetamol 500mg", "batch_number": "B123", "expiry_date": "2026/12", "unit_price": 2.0, "quantity": 10, "selling_price": 2.0},
        {"name": "Cough Syrup", "batch": "C99", "expiry": "2025/11", "rate": 150.0, "qty": 1},
        {"medicine_name": "Vitamin C", "batch": "V55", "expiry": "2027/01", "rate": 5.0, "qty": 20},
    ],
    "subtotal": 270.0,
    "discount_amount": 0,
    "tax_amount": 0,
    "grand_total": 270.0,
    "sold_by": "Test User"
}

output_file = "sample_invoice.pdf"
try:
    path = generate_invoice(data, output_file)
    print(f"Success! Created {path}")
    os.startfile(os.path.abspath(path))
except Exception as e:
    print(f"Error: {e}")
