import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from database import db

orders_collection = db["orders"]

def fetch_sold_items(filter_type="all", start_date=None, end_date=None, product=None, month=None):
    """Fetch sold items from orders, flattening them into individual records."""
    query = {}

    # Handle filter types like today, month, year
    if filter_type == "today":
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  # Midnight today
        end = start + timedelta(days=1)  # End of the day
        query["createdAt"] = {"$gte": start, "$lt": end}

    elif filter_type == "month":
        start = datetime(datetime.now().year, datetime.now().month, 1)  # First day of the month
        end = datetime(datetime.now().year, datetime.now().month + 1, 1) if datetime.now().month < 12 else datetime(datetime.now().year + 1, 1, 1)
        query["createdAt"] = {"$gte": start, "$lt": end}

    elif filter_type == "year":
        start = datetime(datetime.now().year, 1, 1)  # First day of the year
        end = datetime(datetime.now().year + 1, 1, 1)  # First day of next year
        query["createdAt"] = {"$gte": start, "$lt": end}

    if start_date and end_date:
        query["createdAt"] = {"$gte": start_date, "$lte": end_date}

    if product:
        query["items.name"] = {"$regex": product, "$options": "i"}

    if month:
        start = datetime(datetime.now().year, month, 1)
        end = datetime(datetime.now().year, month + 1, 1) if month < 12 else datetime(datetime.now().year + 1, 1, 1)
        query["createdAt"] = {"$gte": start, "$lt": end}

    orders = orders_collection.find(query)

    sold_items = []
    for order in orders:
        for item in order.get("items", []):
            created_at = order.get("createdAt")

            # Convert to DD-MM-YY HH:MM:SS format
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%d-%m-%y %H:%M:%S")
            else:
                created_at = "Unknown Date"

            sold_items.append({
                "item_name": item.get("name", "Unknown"),
                "quantity": item.get("quantity", 0),
                "selling_price": item.get("price", 0),
                "total_revenue": item.get("total", 0),
                "profit": item.get("total", 0) * 0.3,  # Assuming 30% profit margin
                "date": created_at
            })

    return sold_items

def sales_ui(root):
    frame = tk.Frame(root)
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    ttk.Label(frame, text="Sales", font=("Arial", 18, "bold"), background="#ecf0f1", foreground="#2c3e50").pack(pady=10)

    # Filters
    filter_frame = tk.Frame(frame)
    filter_frame.pack(fill="x")

    ttk.Label(filter_frame, text="Filter By:").pack(side="left", padx=5)
    filter_var = tk.StringVar(value="all")

    filters = [("All", "all"), ("Today", "today"), ("This Month", "month"), ("This Year", "year")]

    for text, value in filters:
        ttk.Radiobutton(filter_frame, text=text, variable=filter_var, value=value).pack(side="left")

    # Date Range Picker
    ttk.Label(filter_frame, text="Start Date:").pack(side="left", padx=5)
    start_date_picker = DateEntry(filter_frame, width=12, date_pattern="yyyy-mm-dd")
    start_date_picker.pack(side="left", padx=5)

    ttk.Label(filter_frame, text="End Date:").pack(side="left", padx=5)
    end_date_picker = DateEntry(filter_frame, width=12, date_pattern="yyyy-mm-dd")
    end_date_picker.pack(side="left", padx=5)

    # Month Picker
    ttk.Label(filter_frame, text="Month:").pack(side="left", padx=5)
    month_var = tk.StringVar()
    month_entry = ttk.Combobox(filter_frame, textvariable=month_var, values=[str(i) for i in range(1, 13)], width=5)
    month_entry.pack(side="left", padx=5)

    # Product Filter
    ttk.Label(filter_frame, text="Product:").pack(side="left", padx=5)
    product_var = tk.StringVar()
    product_entry = tk.Entry(filter_frame, textvariable=product_var, width=15)
    product_entry.pack(side="left", padx=5)

    # Clear Filters Button
    def clear_filters():
        """Reset all filters to their default state."""
        filter_var.set("all")
        start_date_picker.set_date("")  # Clear start date
        end_date_picker.set_date("")  # Clear end date
        month_var.set("")  # Clear month selection
        product_var.set("")  # Clear product search
        update_sales()  # Refresh the data based on default (all) filter

    clear_button = ttk.Button(filter_frame, text="Clear Filters", command=clear_filters)
    clear_button.pack(side="left", padx=5)

    # Sales Table
    columns = ("Item Name", "Quantity Sold", "Selling Price", "Total Revenue", "Profit", "Date")
    sales_table = ttk.Treeview(frame, columns=columns, show="headings")

    for col in columns:
        sales_table.heading(col, text=col)
        sales_table.column(col, anchor="center")

    sales_table.pack(expand=True, fill="both")

    # Total Sales and Profit
    totals_frame = tk.Frame(frame)
    totals_frame.pack(fill="x", pady=10)

    total_sales_label = ttk.Label(totals_frame, text="Total Sales: 0", font=("Arial", 12, "bold"))
    total_sales_label.pack(side="left", padx=10)

    total_profit_label = ttk.Label(totals_frame, text="Total Profit: 0", font=("Arial", 12, "bold"))
    total_profit_label.pack(side="right", padx=10)

    def update_sales():
        """Update table based on selected filter."""
        filter_type = filter_var.get()
        start_date = start_date_picker.get_date() if start_date_picker.get_date() else None
        end_date = end_date_picker.get_date() if end_date_picker.get_date() else None
        product = product_var.get()
        month = int(month_var.get()) if month_var.get() else None

        sold_items = fetch_sold_items(filter_type, start_date, end_date, product, month)

        sales_table.delete(*sales_table.get_children())

        total_sales = 0
        total_profit = 0

        for item in sold_items:
            total_sales += item["total_revenue"]
            total_profit += item["profit"]

            sales_table.insert("", tk.END, values=(
                item["item_name"],
                item["quantity"],
                f"Ksh {item['selling_price']:.2f}",
                f"Ksh {item['total_revenue']:.2f}",
                f"Ksh {item['profit']:.2f}",
                item["date"]
            ))

        total_sales_label.config(text=f"Total Sales: Ksh {total_sales:,.2f}")
        total_profit_label.config(text=f"Total Profit: Ksh {total_profit:,.2f}")

    # Bind filters to update table
    filter_var.trace_add("write", lambda *args: update_sales())
    start_date_picker.bind("<<DateEntrySelected>>", lambda *args: update_sales())
    end_date_picker.bind("<<DateEntrySelected>>", lambda *args: update_sales())
    month_entry.bind("<<ComboboxSelected>>", lambda *args: update_sales())

    # Load initial data
    update_sales()

    return frame
