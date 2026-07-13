import tkinter as tk
from tkinter import ttk, Toplevel, messagebox
from tkcalendar import DateEntry
from database import db
from bson import ObjectId
from datetime import datetime

# Connect to MongoDB
orders_collection = db["orders"]

def fetch_orders(filters=None):
    """Fetch all orders from MongoDB."""
    try:
        if filters:
            return list(orders_collection.find(filters).sort("createdAt", -1))  # Sort by latest date
        return list(orders_collection.find({}, {
            "_id": 1, "order_number": 1, "customer_name": 1,
            "items": 1, "payment_method": 1, "createdAt": 1
        }).sort("createdAt", -1))  # Sort by latest date
    except Exception as e:
        messagebox.showerror("Database Error", f"Failed to fetch orders: {e}")
        return []

def show_order_details(order):
    """Open a modal to display order items."""
    items = order.get("items", [])

    if not items:
        messagebox.showinfo("No Items", "This order has no items.")
        return

    modal = Toplevel()
    modal.title(f"Order {order['order_number']} Details")
    modal.geometry("500x400")

    ttk.Label(modal, text=f"Order #{order['order_number']}", font=("Arial", 14, "bold")).pack(pady=5)
    ttk.Label(modal, text=f"Customer: {order['customer_name']}", font=("Arial", 12)).pack()
    ttk.Label(modal, text=f"Payment: {order['payment_method']}", font=("Arial", 12)).pack()

    table_frame = ttk.Frame(modal)
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    columns = ("name", "quantity", "price", "total")
    table = ttk.Treeview(table_frame, columns=columns, show="headings")
    table.pack(fill="both", expand=True)

    table.heading("name", text="Item Name")
    table.heading("quantity", text="Qty")
    table.heading("price", text="Price")
    table.heading("total", text="Total")

    for item in items:
        table.insert("", "end", values=(item["name"], item["quantity"], f"Ksh {item['price']}", f"Ksh {item['total']}"))

    ttk.Button(modal, text="Close", command=modal.destroy).pack(pady=10)

def all_orders_ui(parent):
    """Displays all orders in a table."""
    for widget in parent.winfo_children():
        widget.destroy()

    ttk.Label(parent, text="All Orders", font=("Arial", 18, "bold")).pack(pady=10)

    filter_frame = ttk.Frame(parent)
    filter_frame.pack(fill="x", padx=10, pady=5)

    order_no_var = tk.StringVar()
    customer_name_var = tk.StringVar()
    date_var = tk.StringVar()
    month_var = tk.StringVar()

    ttk.Label(filter_frame, text="Order #:").grid(row=0, column=0, padx=5)
    order_entry = tk.Entry(filter_frame, textvariable=order_no_var, width=10)
    order_entry.grid(row=0, column=1)

    ttk.Label(filter_frame, text="Customer:").grid(row=0, column=2, padx=5)
    customer_entry = tk.Entry(filter_frame, textvariable=customer_name_var, width=15)
    customer_entry.grid(row=0, column=3)

    ttk.Label(filter_frame, text="Date:").grid(row=0, column=4, padx=5)
    date_picker = DateEntry(filter_frame, textvariable=date_var, width=13, background='darkblue',
                            foreground='white', date_pattern='yyyy-mm-dd')
    date_picker.grid(row=0, column=5)

    table_frame = ttk.Frame(parent)
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    columns = ("order_number", "customer_name", "total_amount", "payment_method", "date")
    table = ttk.Treeview(table_frame, columns=columns, show="headings")
    table.pack(fill="both", expand=True)

    table.heading("order_number", text="Order #")
    table.heading("customer_name", text="Customer")
    table.heading("total_amount", text="Total Amount")
    table.heading("payment_method", text="Payment")
    table.heading("date", text="Date")

    def load_orders(orders):
        """Load orders into the table."""
        table.delete(*table.get_children())
        for order in orders:
            total_amount = sum(item["total"] for item in order.get("items", []))
            created_at = order.get("createdAt", "")
            if created_at:
                created_at = created_at.strftime("%d-%m-%Y %H:%M:%S")
            else:
                created_at = "N/A"
            table.insert("", "end", values=(
                order.get("order_number", ""),
                order.get("customer_name", ""),
                f"Ksh {total_amount}",
                order.get("payment_method", ""),
                created_at  # Include createdAt in values
            ), tags=(str(order["_id"]),))

    def apply_filters(*args):
        """Applies user filters dynamically as they type."""
        filters = {}

        if order_no_var.get():
            try:
                filters["$expr"] = {
                   "$regexMatch": {
                        "input": {"$toString": "$order_number"},
                        "regex": order_no_var.get(),
                        "options": "i"
                    }
                }
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply order number filter: {e}")
                return
 
        if customer_name_var.get():
            filters["customer_name"] = {"$regex": customer_name_var.get(), "$options": "i"}

        if date_var.get():
            try:
                day = datetime.strptime(date_var.get(), "%Y-%m-%d")
                next_day = day.replace(hour=23, minute=59, second=59)
                filters["createdAt"] = {"$gte": day, "$lte": next_day}
            except ValueError:
                messagebox.showerror("Invalid Input", "Date must be in YYYY-MM-DD format.")
                return

        if month_var.get():
            try:
                month = datetime.strptime(month_var.get(), "%Y-%m")
                next_month = datetime(month.year + (month.month // 12), ((month.month % 12) + 1), 1)
                filters["createdAt"] = {"$gte": month, "$lt": next_month}
            except ValueError:
                messagebox.showerror("Invalid Input", "Month must be in YYYY-MM format.")
                return

        try:
            filtered_orders = list(orders_collection.find(filters).sort("createdAt", -1))
            load_orders(filtered_orders)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters: {e}")

    def clear_filters():
        """Clear all filters and reload all orders in descending order."""
        order_no_var.set("")
        customer_name_var.set("")
        date_var.set("")
        month_var.set("")
        date_picker.set_date('')
        load_orders(fetch_orders())  # Fetch all orders, sorted by latest to earliest

    # Bind the filters to the apply_filters function to update dynamically as they type
    order_entry.bind("<KeyRelease>", apply_filters)
    customer_entry.bind("<KeyRelease>", apply_filters)
    date_picker.bind("<FocusOut>", apply_filters)
    month_entry = tk.Entry(filter_frame, textvariable=month_var, width=15)
    month_entry.grid(row=0, column=6)
    month_entry.bind("<KeyRelease>", apply_filters)

    ttk.Button(filter_frame, text="Clear Filters", command=clear_filters).grid(row=0, column=7, padx=10)

    # Initially load all orders in descending order
    load_orders(fetch_orders())

    def on_item_click(event):
        selected_item = table.selection()
        if selected_item:
            order_id_str = table.item(selected_item)["tags"][0]
            try:
                order = orders_collection.find_one({"_id": ObjectId(order_id_str)})
                if order:
                    show_order_details(order)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch order details: {e}")

    table.bind("<Double-1>", on_item_click)
