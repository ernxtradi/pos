import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from printer import print_receipt
from database import db

orders_collection = db["orders"]
inventory_collection = db["inventory"]

def generate_order_number():
    """Generates a unique order number based on the count of orders in the database."""
    last_order = orders_collection.find_one(sort=[("_id", -1)])
    if last_order and "order_number" in last_order:
        return last_order["order_number"] + 1
    return 1001  # Start from 1001 if no orders exist

def search_inventory(search_term):
    """Search inventory for matching items."""
    return list(inventory_collection.find({"name": {"$regex": search_term, "$options": "i"}}, {"_id": 0}))

def submit_order(customer_name, order_items, payment_method):
    """Processes and saves the order, ensuring inventory is sufficient."""
    if not order_items:
        messagebox.showerror("Error", "No items in the order.")
        return

    for item in order_items:
        inventory_item = inventory_collection.find_one({"name": item["name"]})

        if not inventory_item:
            messagebox.showerror("Error", f"{item['name']} is not available in inventory.")
            return

        available_quantity = inventory_item.get("quantity", 0)

        if available_quantity <= 0:
            messagebox.showerror("Error", f"No stock available for {item['name']}.")
            return

        if item["quantity"] > available_quantity:
            messagebox.showerror("Error", f"Not enough stock for {item['name']}. Available: {available_quantity}.")
            return

    order_number = generate_order_number()

    for item in order_items:
        inventory_collection.update_one(
            {"name": item["name"]},
            {"$inc": {"quantity": -item["quantity"]}}
        )

    order = {
        "order_number": order_number,
        "customer_name": customer_name,
        "items": order_items,
        "payment_method": payment_method,
        "createdAt": datetime.now()
    }
    orders_collection.insert_one(order)
    
    print_receipt(order)

    messagebox.showinfo("Success", f"Order #{order_number} has been submitted successfully!")

    return order_number

def add_placeholder(entry, placeholder_text):
    """Adds placeholder behavior to an entry widget."""
    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def on_focus_out(event):
        if entry.get() == "":
            entry.insert(0, placeholder_text)
            entry.config(fg="gray")

    entry.insert(0, placeholder_text)
    entry.config(fg="gray")
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

def orders_ui(root):
    """Builds the orders interface."""
    frame = tk.Frame(root)
    frame.pack(expand=True, fill="both")
  
    ttk.Label(frame, text="Orders", font=("Arial", 18, "bold"), background="#ecf0f1", foreground="#2c3e50").pack(pady=10)
    
    left_frame = tk.Frame(frame)
    left_frame.pack(side="left", fill="y", padx=10, pady=10)

    right_frame = tk.Frame(frame)
    right_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

    # Customer Name Input
    tk.Label(right_frame, text="Customer Name:").pack()
    customer_name_entry = tk.Entry(right_frame)
    customer_name_entry.pack(fill="x", pady=5)
    add_placeholder(customer_name_entry, "Enter Customer Name")

    # Search Section
    tk.Label(left_frame, text="Search Item:").pack()
    search_entry = tk.Entry(left_frame)
    search_entry.pack(fill="x", pady=5)
    add_placeholder(search_entry, "Search inventory...")

    search_listbox = tk.Listbox(left_frame, height=15)
    search_listbox.pack(fill="both", expand=True)

    def update_search_results(event=None):
        """Updates search results as user types."""
        search_listbox.delete(0, tk.END)
        search_term = search_entry.get()
        items = search_inventory(search_term)
        for item in items:
            search_listbox.insert(tk.END, item['name'])
    
    def add_to_order(event):
        """Adds selected item from search to order table only if inventory is available."""
        selected_index = search_listbox.curselection()
        if not selected_index:
            return

        item_name = search_listbox.get(selected_index[0])
        inventory_item = inventory_collection.find_one({"name": item_name})

        if not inventory_item:
            messagebox.showerror("Error", f"{item_name} not found in inventory.")
            return

        available_quantity = inventory_item.get("quantity", 0)

        if available_quantity <= 0:
             messagebox.showerror("Error", f"{item_name} is out of stock and cannot be added.")
             return

        price_high = inventory_item.get("selling_price_high", 0)
        price_low = inventory_item.get("selling_price_low", 0)

        for item in order_table.get_children():
            values = order_table.item(item, "values")
            if values[0] == item_name:
                new_quantity = int(values[2]) + 1
                if new_quantity > available_quantity:
                    messagebox.showerror("Error", f"Not enough stock for {item_name}. Available: {available_quantity}.")
                    return
            
                new_total = new_quantity * float(values[1])
                order_table.item(item, values=(item_name, values[1], new_quantity, new_total, "❌"))  # Add "❌" here
                return

        order_table.insert("", tk.END, values=(item_name, price_high, 1, price_high, "❌"))  # Add "❌" here for new rows
    
    search_entry.bind("<KeyRelease>", update_search_results)
    search_listbox.bind("<Double-1>", add_to_order)

    # Order Table
    tk.Label(right_frame, text="Order Items:").pack()
    order_table = ttk.Treeview(right_frame, columns=("Name", "Price", "Quantity", "Total", "Action"), show="headings")
    order_table.heading("Name", text="Item Name")
    order_table.heading("Price", text="Selling Price")
    order_table.heading("Quantity", text="Quantity")
    order_table.heading("Total", text="Total Price")
    order_table.heading("Action", text="Action")  # Add Action column
    order_table.pack(expand=True, fill="both")

    def delete_item(event):
        """Deletes the selected item from the order table."""
        selected_item = order_table.selection()
        if not selected_item:
            return

        item_id = selected_item[0]
        order_table.delete(item_id)

    def edit_item(event):
        """Allows editing of price and quantity."""
        selected_item = order_table.selection()
        if not selected_item:
            return

        item_id = selected_item[0]
        column_id = order_table.identify_column(event.x)
        col_index = int(column_id[1:]) - 1  # Identify the column index

        if col_index not in [1, 2]:  # Only allow editing of price and quantity
            return

        x, y, width, height = order_table.bbox(item_id, column=column_id)  # Get cell position
        entry = tk.Entry(order_table)
        entry.place(x=x, y=y, width=width, height=height)

        def save_edit():
            new_value = entry.get()
            entry.destroy()
            try:
                new_value = float(new_value) if col_index == 1 else int(new_value)
            except ValueError:
                messagebox.showerror("Invalid Input", "Enter a valid number.")
                return
            
            values = list(order_table.item(item_id, "values"))
            price_low = 0
            price_high = 0

            inventory_item = inventory_collection.find_one({"name": values[0]})
            if inventory_item:
                price_high = inventory_item.get("selling_price_high", 0)
                price_low = inventory_item.get("selling_price_low", 0)

            if col_index == 1:  # If editing price
                if not (price_low <= new_value <= price_high):
                    messagebox.showerror("Error", f"Price must be between {price_low} and {price_high}")
                    return
                values[1] = new_value

            elif col_index == 2:  # If editing quantity
                if new_value < 1:
                    messagebox.showerror("Error", "Quantity must be at least 1")
                    return
                values[2] = new_value

            values[3] = float(values[1]) * int(values[2])  # Update total
            values[4] = "❌"  # Ensure "Action" column is populated

            order_table.item(item_id, values=values)  # Save changes

        entry.insert(0, order_table.item(item_id, "values")[col_index])
        entry.bind("<Return>", lambda event: save_edit())
        entry.bind("<FocusOut>", lambda event: save_edit())
        entry.focus()

    order_table.bind("<Double-1>", edit_item)

    # Bind delete action for the "❌" button in the Action column
    def handle_click(event):
        region = order_table.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = order_table.identify_row(event.y)
        col_id = order_table.identify_column(event.x)

        if not row_id or col_id != "#5":  # Action column is the 5th one
            return

        order_table.delete(row_id)

    order_table.bind("<Button-1>", handle_click)

    # Payment Selection
    payment_method = tk.StringVar(value="Cash")
    tk.Radiobutton(right_frame, text="Cash", variable=payment_method, value="Cash").pack()
    tk.Radiobutton(right_frame, text="Mpesa", variable=payment_method, value="Mpesa").pack()

    def clear_inputs():
        customer_name_entry.delete(0, tk.END)
        add_placeholder(customer_name_entry, "Enter Customer Name")
        search_entry.delete(0, tk.END)
        add_placeholder(search_entry, "Search inventory...")
        search_listbox.delete(0, tk.END)
        order_table.delete(*order_table.get_children())

    def finalize_order():
        customer_name = customer_name_entry.get()
        order_items = [{"name": values[0], "price": float(values[1]), "quantity": int(values[2]), "total": float(values[3])} for values in (order_table.item(i, "values") for i in order_table.get_children())]
        
        order_number = submit_order(customer_name, order_items, payment_method.get())
        if order_number:
            clear_inputs()

    tk.Button(right_frame, text="Submit Order", command=finalize_order).pack(pady=10)

    return frame
