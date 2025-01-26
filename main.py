import os
from datetime import datetime
import sqlite3
from fpdf import FPDF


class InvoiceDB:
    def __init__(self):
        self.conn = sqlite3.connect('invoices.db')
        self.create_table()

    def create_table(self):
        self.conn.execute('''
       CREATE TABLE IF NOT EXISTS invoices (
           invoice_number TEXT PRIMARY KEY,
           date TEXT,
           amount REAL,
           quantity REAL,
           rate REAL,
           client TEXT
       )''')

    def save_invoice(self, invoice_num, date, amount, quantity, rate, client):
        self.conn.execute('''
       INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?)
       ''', (invoice_num, date, amount, quantity, rate, client))
        self.conn.commit()

    def get_last_invoice_number(self):
        cursor = self.conn.execute('SELECT invoice_number FROM invoices ORDER BY invoice_number DESC LIMIT 1')
        result = cursor.fetchone()
        return result[0] if result else 'SG7852'


class InvoicePDF(FPDF):
    def __init__(self, invoice_number):
        super().__init__()
        self.invoice_number = invoice_number
        self.add_page()

    def header(self):
        self.set_font('Arial', '', 12)
        self.cell(100, 20, 'Brunch chef', 0, 0, 'L')
        self.set_font('Arial', 'B', 24)
        self.cell(90, 20, 'INVOICE', 0, 1, 'R')

        self.set_font('Arial', '', 12)
        self.cell(100, 10, '', 0, 0)
        self.cell(90, 10, f'# {self.invoice_number}', 0, 1, 'R')

    def add_bill_info(self, client, date, amount):
        self.cell(0, 20, '', 0, 1)
        self.cell(30, 10, 'Bill To:', 0, 1)
        self.set_font('Arial', 'B', 12)
        self.cell(100, 10, client, 0, 0)

        self.set_font('Arial', '', 12)
        self.cell(40, 10, 'Date:', 0, 0)
        self.cell(50, 10, date, 0, 1, 'R')

        self.cell(100, 10, '', 0, 0)
        self.cell(40, 10, 'Balance Due:', 0, 0)
        self.cell(50, 10, f'£{amount:.2f}', 0, 1, 'R')

    def add_items_header(self):
        self.set_fill_color(50, 50, 50)
        self.set_text_color(255, 255, 255)
        self.cell(100, 10, 'Item', 1, 0, 'L', True)
        self.cell(30, 10, 'Quantity', 1, 0, 'C', True)
        self.cell(30, 10, 'Rate', 1, 0, 'C', True)
        self.cell(30, 10, 'Amount', 1, 1, 'C', True)
        self.set_text_color(0, 0, 0)

    def add_item(self, qty, rate):
        amount = qty * rate
        self.cell(100, 10, '', 1, 0)
        self.cell(30, 10, f'{qty}', 1, 0, 'C')
        self.cell(30, 10, f'£{rate:.2f}', 1, 0, 'C')
        self.cell(30, 10, f'£{amount:.2f}', 1, 1, 'C')
        return amount

    def add_total(self, subtotal):
        self.cell(130, 10, '', 0, 0)
        self.cell(30, 10, 'Subtotal:', 0, 0, 'R')
        self.cell(30, 10, f'£{subtotal:.2f}', 0, 1, 'R')

        self.cell(130, 10, '', 0, 0)
        self.cell(30, 10, 'Tax (0%):', 0, 0, 'R')
        self.cell(30, 10, '£0.00', 0, 1, 'R')

        self.cell(130, 10, '', 0, 0)
        self.cell(30, 10, 'Total:', 0, 0, 'R')
        self.cell(30, 10, f'£{subtotal:.2f}', 0, 1, 'R')


def generate_next_invoice_number(db):
    last_number = db.get_last_invoice_number()
    current_num = int(last_number[2:])
    next_num = current_num + 1
    return f'SG{next_num:04d}'


def generate_invoice(quantity, rate, client="Bridge Baker"):
    # Create invoices directory if it doesn't exist
    invoice_dir = 'invoices'
    if not os.path.exists(invoice_dir):
        os.makedirs(invoice_dir)

    db = InvoiceDB()
    invoice_number = generate_next_invoice_number(db)
    date = datetime.now().strftime("%b %d, %Y")
    amount = quantity * rate

    pdf = InvoicePDF(invoice_number)
    pdf.add_bill_info(client, date, amount)
    pdf.add_items_header()
    subtotal = pdf.add_item(quantity, rate)
    pdf.add_total(subtotal)

    # Save PDF in invoices directory
    filename = os.path.join(invoice_dir, f'{invoice_number}.pdf')
    pdf.output(filename)

    # Save to database
    db.save_invoice(invoice_number, date, amount, quantity, rate, client)

    return filename


def main():
    try:
        while True:
            quantity = float(input("Enter quantity (or 0 to exit): "))
            if quantity == 0:
                break

            rate = float(input("Enter rate (£): "))
            client = input("Enter client name (press Enter for 'Bridge Baker'): ").strip()

            if not client:
                client = "Bridge Baker"

            filename = generate_invoice(quantity, rate, client)
            print(f"Invoice generated successfully: {filename}")

            another = input("Generate another invoice? (y/n): ").lower()
            if another != 'y':
                break

    except ValueError as e:
        print("Invalid input. Please enter numeric values for quantity and rate.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()