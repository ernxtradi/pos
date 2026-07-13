import tkinter as tk
from tkinter import ttk, messagebox
import time
from inventory import inventory_ui
from orders import orders_ui
from sales import sales_ui
from allOrders import all_orders_ui

# Initialize root
root = tk.Tk()
root.title("Thunder POS")
root.state("zoomed")  # Start in fullscreen mode

# Sidebar menu (Initially hidden, will be shown on other pages)
sidebar = tk.Frame(root, width=200, bg="#2C3E50")

# Main content frame
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, side="right")


# Function to clear the main frame before switching screens
def clear_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()


# Home Screen UI
def show_home():
    """Displays the home screen without the sidebar."""
    clear_frame()
    sidebar.pack_forget()  # Hide sidebar

    frame = tk.Frame(main_frame, bg="#f4f4f4")
    frame.pack(expand=True, fill="both")

    # Header Section
    header = tk.Frame(frame, bg="#007BFF", height=70)
    header.pack(fill="x", padx=10, pady=5)

    title_label = tk.Label(header, text="Thunder POS - Home", font=("Arial", 18, "bold"), fg="white", bg="#007BFF")
    title_label.pack(pady=15)

    # Time & Date Display
    time_label = tk.Label(frame, font=("Arial", 12, "bold"), bg="#f4f4f4")
    time_label.pack(pady=5)

    def update_time():
        """Updates time & date every second."""
        current_time = time.strftime("%A, %B %d, %Y | %I:%M:%S %p")
        time_label.config(text=current_time)
        frame.after(1000, update_time)

    update_time()

    # Navigation Buttons
    btn_frame = tk.Frame(frame, bg="#f4f4f4")
    btn_frame.pack(pady=20)

    buttons = [
        ("🛒 Orders", "orders"),
        ("📦 Inventory", "inventory"),
        ("📋 All Orders", "all_orders"),
        ("📊 Sales", "sales"),
       
    ]

    for text, screen in buttons:
        btn = tk.Button(btn_frame, text=text, font=("Arial", 14), width=20, height=2, bg="#007BFF", fg="white",
                        activebackground="#0056b3", activeforeground="white",
                        command=lambda s=screen: navigate_to(s))
        btn.pack(pady=10)

    # Footer Buttons (Logout & Exit)
    footer_frame = tk.Frame(frame, bg="#f4f4f4")
    footer_frame.pack(pady=30)

    def logout():
        """Logs out the user after confirmation."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            root.quit()

    tk.Button(footer_frame, text="🔑 Logout", font=("Arial", 12), bg="red", fg="white",
              command=logout).pack(side="left", padx=20)
    tk.Button(footer_frame, text="❌ Exit", font=("Arial", 12), bg="black", fg="white",
              command=root.quit).pack(side="right", padx=20)


# Screen navigation function
def navigate_to(screen):
    """Clears frame and switches to the selected screen."""
    clear_frame()

    if screen == "home":
        show_home()
        return

    sidebar.pack(fill="y", side="left")  # Show sidebar on other pages

    screen_map = {
        "inventory": lambda: inventory_ui(main_frame),
        "orders": lambda: orders_ui(main_frame),
        "all_orders": lambda: all_orders_ui(main_frame),
        "sales": lambda: sales_ui(main_frame),

    }

    if screen in screen_map:
        screen_map[screen]()


# Sidebar menu (Visible on all pages except Home)
menu_items = [
    ("🏠 Home", "home"),
    ("📦 Inventory", "inventory"),
    ("🛒 Orders", "orders"),
    ("📋 All Orders", "all_orders"),
    ("📊 Sales", "sales"),
]

for text, screen in menu_items:
    ttk.Button(sidebar, text=text, command=lambda s=screen: navigate_to(s)).pack(pady=10, padx=5, fill="x")

# Start with the Home screen
show_home()

# Run the application
root.mainloop()
