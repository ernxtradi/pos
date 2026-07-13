import win32print
import win32ui
from datetime import datetime

# Get current date and time
now = datetime.now()

# Change this to match your receipt printer's name
PRINTER_NAME = "P-822B"

def format_receipt(order):
    """Formats the receipt for printing."""
    if not order:
        return None

    receipt_text = "\n"
    receipt_text += "sales Receipt \n"
    receipt_text += "SWEET ROOT ENTERPRISES\n"
    receipt_text += "Tel: 254 725 920 099\n"
    receipt_text += "-" * 30 + "\n"
    receipt_text += f"Order No: {order.get('order_number', 'N/A')}\n"
    receipt_text += f"Date: {now.strftime('%d-%m-%Y %H:%M:%S')}\n"
    receipt_text += f"Customer: {order.get('customer_name', 'Walk-in')}\n"
    receipt_text += f"Payment: {order.get('payment_method', 'Cash')}\n"
    receipt_text += "-" * 30 + "\n"
    
    for item in order.get("items", []):
        name = item.get("name", "Customer")
        qty = item.get("quantity", 1)
        price = item.get("price", 0.0)
        total = item.get("total", 0.0)
        receipt_text += f"{name[:15]:<15} x{qty:<2} {price:>6}  = {total:>6}\n"

    receipt_text += "-" * 30 + "\n"
    total_price = sum(item["total"] for item in order.get("items", []))
    receipt_text += f"TOTAL: KSH {total_price:>22.2f}\n"
    receipt_text += "-" * 30 + "\n"
    receipt_text += "Thank you for shopping!\n"
    receipt_text += "For POS call 254 713 522 833 !\n"
    receipt_text += "\n\n\n\n\n\n\n\n"

    return receipt_text

def print_receipt(order):
    """Sends receipt text to the thermal printer."""
    receipt_text = format_receipt(order)
    if not receipt_text:
        print("Error: No receipt data to print.")
        return False

    try:
        hprinter = win32print.OpenPrinter(PRINTER_NAME)
        hprinter_job = win32print.StartDocPrinter(hprinter, 1, ("Receipt Print Job", None, "RAW"))
        win32print.StartPagePrinter(hprinter)

        win32print.WritePrinter(hprinter, receipt_text.encode('utf-8'))

        win32print.EndPagePrinter(hprinter)
        win32print.EndDocPrinter(hprinter)
        win32print.ClosePrinter(hprinter)
        print("Receipt printed successfully.")
        return True

    except Exception as e:
        print(f"Error printing receipt: {e}")
        return False
