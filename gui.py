# xup/gui.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from monitor import load_character_monitor, stop_event, monitor_thread
from eve import get_eve_windows, refresh_eve_clients  # Assumes these functions have been optimized

VERSION = "v0.0.2"

def set_window_icon(root):
    """Set the window icon from the static folder."""
    try:
        # When compiled with Nuitka, sys.frozen is True and data files are in sys._MEIPASS
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, "static", "icon.ico")
        root.iconbitmap(icon_path)
    except Exception as e:
        print("Error setting window icon:", e)

def toggle_always_on_top(root, top_var):
    """Toggle the 'always on top' state for the main window."""
    root.attributes('-topmost', top_var.get())

def show_about():
    """Display the About dialog."""
    about_text = (
        "X-UP is a tool for EVE Online that helps people count. Because counting is hard.\n\n"
        "Made by h0ly lag"
    )
    messagebox.showinfo("About X-UP", about_text)

def reset_count(count_holder, count_var):
    """Reset the internal counter and update the display."""
    count_holder[0] = 0
    count_var.set(0)

def build_gui():
    root = tk.Tk()
    set_window_icon(root)
    root.title(f"X-UP - {VERSION}")
    root.geometry("285x275")
    root.resizable(False, False)
    
    # Always on top toggle variable
    always_on_top = tk.BooleanVar(value=False)
    
    # Build the menu
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    settings_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)
    settings_menu.add_checkbutton(
        label="Always on Top",
        variable=always_on_top,
        command=lambda: toggle_always_on_top(root, always_on_top)
    )
    menu_bar.add_command(label="About", command=show_about)
    
    # Get initial EVE client list
    clients = get_eve_windows()
    if clients:
        initial_client = clients[0]
        combobox_state = "readonly"
    else:
        initial_client = "No EVE clients found"
        clients = [initial_client]
        combobox_state = "disabled"
    
    character_var = tk.StringVar(value=initial_client)
    count_var = tk.IntVar(value=0)
    count_holder = [0]  # Mutable container for the counter
    log_file_var = tk.StringVar(value="None")
    
    # Frame for client dropdown and Load button
    client_frame = ttk.Frame(root)
    client_frame.pack(pady=5)
    
    combobox = ttk.Combobox(
        client_frame,
        textvariable=character_var,
        values=clients,
        state=combobox_state
    )
    combobox.pack(side=tk.LEFT, padx=5)
    # Refresh client list every 5 seconds; refresh_eve_clients enables/disables the dropdown as needed.
    combobox.after(5000, refresh_eve_clients, character_var, combobox)
    
    ttk.Button(
        client_frame, 
        text="Load Character",
        command=lambda: load_character_monitor(character_var, count_var, log_file_var, count_holder)
    ).pack(side=tk.LEFT, padx=5)
    
    # Log file display
    log_frame = ttk.Frame(root)
    log_frame.pack(pady=5)
    ttk.Label(log_frame, text="Log:").grid(row=0, column=0, padx=0)
    ttk.Label(log_frame, textvariable=log_file_var).grid(row=0, column=1, padx=0)
    
    # X Count display
    ttk.Label(root, text="X Count:", font=("Helvetica", 16)).pack(pady=(10, 0))
    ttk.Label(root, textvariable=count_var, font=("Helvetica", 56)).pack(pady=(0, 10))
    
    # Reset button with larger text
    style = ttk.Style()
    style.configure("Large.TButton", font=("Helvetica", 16, "bold"))
    reset_btn = ttk.Button(
        root,
        text="RESET",
        style="Large.TButton",
        command=lambda: reset_count(count_holder, count_var)
    )
    reset_btn.pack(pady=(0, 0))
    
    def on_close():
        stop_event.set()
        if monitor_thread and monitor_thread.is_alive():
            monitor_thread.join()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    build_gui()
