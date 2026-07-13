from database import db
import tkinter as tk
from tkinter import ttk, messagebox

inventory_collection = db["inventory"]

# Define Colors & Styles
BG_COLOR = "#ecf0f1"  
HEADER_COLOR = "#34495e"  
TEXT_COLOR = "#2c3e50"  
BUTTON_COLOR = "#3498db"  
BUTTON_HOVER = "#2980b9"
TABLE_COLOR = "#bdc3c7"  

def add_item(name, buying_price, selling_price_low, selling_price_high, quantity):
    existing_item = inventory_collection.find_one({"name": name})
    if existing_item:
        new_quantity = existing_item["quantity"] + quantity
        inventory_collection.update_one(
            {"name": name},
            {"$set": {
                "buying_price": buying_price,
                "selling_price_low": selling_price_low,
                "selling_price_high": selling_price_high,
                "quantity": new_quantity
            }}
        )
        messagebox.showinfo("Success", "Item updated successfully!")
    else:
        item = {
            "name": name,
            "buying_price": buying_price,
            "selling_price_low": selling_price_low,
            "selling_price_high": selling_price_high,
            "quantity": quantity
        }
        inventory_collection.insert_one(item)
        messagebox.showinfo("Success", "Item added successfully!")

def delete_item(name):
    inventory_collection.delete_one({"name": name})
    messagebox.showinfo("Success", "Item deleted successfully!")

def show_inventory():
    items = list(inventory_collection.find({}, {"_id": 0}))
    return items

def inventory_ui(root):
    frame = tk.Frame(root, bg=BG_COLOR)
    frame.pack(expand=True, fill="both")

    ttk.Label(frame, text="Inventory Management", font=("Arial", 18, "bold"), background=BG_COLOR, foreground=TEXT_COLOR).pack(pady=10)

    # Table Frame
    table_frame = tk.Frame(frame, bg=BG_COLOR, bd=2, relief="ridge")
    table_frame.pack(fill="both", expand=True, padx=20, pady=10)

    columns = ("Name", "Buying Price", "Selling Price", "Quantity")
    inventory_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=10, style="Custom.Treeview")


    for col in columns:
        inventory_table.heading(col, text=col, anchor="center")
        inventory_table.column(col, width=180, anchor="center")

    inventory_table.pack(fill="both", expand=True)

    # Table Styling
    style = ttk.Style()
    style.configure("Treeview", rowheight=30, font=("Arial", 12), borderwidth=1)
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"), background="#1abc9c", foreground="black", borderwidth=1, relief="solid",)  # Custom color
    style.configure("Custom.Treeview", background="white", fieldbackground="white", borderwidth=2, relief="solid")
    style.map("Treeview", background=[("selected", "#0f598e")])

    # Alternate Row Colors
    def color_rows():
        for i, item in enumerate(inventory_table.get_children()):
            inventory_table.item(item, tags=("evenrow",) if i % 2 == 0 else ("oddrow",))

    inventory_table.tag_configure("oddrow", background="white")
    inventory_table.tag_configure("evenrow", background="#bbc3cc")

    # Add Item Section
    add_frame = tk.Frame(frame, bg=BG_COLOR)
    add_frame.pack(pady=10)

    labels = ["Name", "Buying Price", "Selling Price Low", "Selling Price High", "Quantity"]
    entries = {}

    # Function to handle placeholders
    def add_placeholder(entry, text):
        def on_focus_in(event):
            if entry.get() == text:
                entry.delete(0, tk.END)
                entry.config(fg="black")

        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, text)
                entry.config(fg="gray")

        entry.insert(0, text)
        entry.config(fg="gray")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    for i, label in enumerate(labels):
        tk.Label(add_frame, text=f"{label}:", font=("Arial", 12), bg=BG_COLOR, fg=TEXT_COLOR).grid(row=i, column=0, padx=10, pady=5, sticky="w")
        entry = tk.Entry(add_frame, font=("Arial", 12), width=20)
        add_placeholder(entry, f"Enter {label.lower()}")
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries[label] = entry

    # Function to add stock
    def add_stock():
        name = entries["Name"].get()
        buying_price = entries["Buying Price"].get()
        selling_price_low = entries["Selling Price Low"].get()
        selling_price_high = entries["Selling Price High"].get()
        quantity = entries["Quantity"].get()

        if name and buying_price and selling_price_low and selling_price_high and quantity:
            try:
                add_item(name, float(buying_price), float(selling_price_low), float(selling_price_high), int(quantity))
                refresh_inventory()
            except ValueError:
                messagebox.showerror("Error", "Enter valid numbers for prices and quantity")
        else:
            messagebox.showerror("Error", "All fields are required")

    # Function to delete stock
    def delete_stock():
        selected_item = inventory_table.selection()
        if selected_item:
            item_name = inventory_table.item(selected_item, "values")[0]
            delete_item(item_name)
            refresh_inventory()
        else:
            messagebox.showerror("Error", "Select an item to delete")

    # Buttons with styling
    button_frame = tk.Frame(frame, bg=BG_COLOR)
    button_frame.pack(pady=10)

    def style_button(button):
        button.config(font=("Arial", 12, "bold"), bg=BUTTON_COLOR, fg="white", padx=10, pady=5, relief="raised", borderwidth=2)
        button.bind("<Enter>", lambda e: button.config(bg=BUTTON_HOVER))
        button.bind("<Leave>", lambda e: button.config(bg=BUTTON_COLOR))

    add_button = tk.Button(button_frame, text="Add Item", command=add_stock)
    delete_button = tk.Button(button_frame, text="Delete Item", command=delete_stock)

    style_button(add_button)
    style_button(delete_button)

    add_button.pack(side="left", padx=5)
    delete_button.pack(side="left", padx=5)

    # Refresh Inventory Function
    def refresh_inventory():
        inventory_table.delete(*inventory_table.get_children())
        items = show_inventory()
        for item in items:
            inventory_table.insert("", tk.END, values=(
                item["name"], item["buying_price"], f"{item['selling_price_low']} - {item['selling_price_high']}", item["quantity"]
            ))
        color_rows()

    refresh_inventory()

    return frame
