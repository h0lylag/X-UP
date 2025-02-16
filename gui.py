# xup/gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from monitor import on_load_reset_button_click, stop_event, monitor_thread
from eve import list_eve_windows, update_eve_clients

version_number = "v0.0.2"
root = None
always_on_top_var = None

def toggle_always_on_top():
    global always_on_top_var, root
    if always_on_top_var.get():
        root.attributes('-topmost', True)
    else:
        root.attributes('-topmost', False)

def show_about():
    about_text = (
        "X-UP is a tool for EVE Online that helps people count. Because counting is hard.\n\n"
        "Made by h0ly lag"
    )
    messagebox.showinfo("About X-UP", about_text)

def create_gui():
    global root, always_on_top_var
    root = tk.Tk()
    root.title(f'X-UP - {version_number}')
    root.geometry("285x250")
    root.resizable(False, False)

    # Menu bar and settings
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    settings_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)
    always_on_top_var = tk.BooleanVar()
    settings_menu.add_checkbutton(label="Always on Top", variable=always_on_top_var, command=toggle_always_on_top)
    menu_bar.add_command(label="About", command=show_about)

    # Get the list of EVE windows
    eve_windows = list_eve_windows()
    if not eve_windows:
        messagebox.showerror("Error", "No EVE clients detected.")
        root.destroy()
        return

    character_var = tk.StringVar()
    character_var.set(eve_windows[0].replace("EVE - ", ""))
    eve_windows = [window.replace("EVE - ", "") for window in eve_windows]

    count_var = tk.IntVar()
    count_var.set(0)
    # A mutable container to hold the count
    count_holder = [0]

    log_file_var = tk.StringVar()
    log_file_var.set("None")

    # Frame for client dropdown and Load Character button
    client_frame = ttk.Frame(root)
    client_frame.pack(pady=5)
    
    combobox = ttk.Combobox(client_frame, textvariable=character_var, values=eve_windows, state='readonly')
    combobox.pack(side=tk.LEFT, padx=5)
    combobox.after(5000, update_eve_clients, character_var, combobox)
    
    ttk.Button(client_frame, text="Load Character",
               command=lambda: on_load_reset_button_click(character_var, count_var, log_file_var, count_holder)
              ).pack(side=tk.LEFT, padx=5)

    # Log file display
    log_frame = ttk.Frame(root)
    log_frame.pack(pady=5)
    ttk.Label(log_frame, text="Log:").grid(row=0, column=0, padx=0)
    ttk.Label(log_frame, textvariable=log_file_var).grid(row=0, column=1, padx=0)

    # Count display
    ttk.Label(root, text="X Count:", font=("Helvetica", 16)).pack(pady=(10, 0))
    ttk.Label(root, textvariable=count_var, font=("Helvetica", 56)).pack(pady=(0, 10))

    # Reset button with larger text
    style = ttk.Style()
    style.configure("Large.TButton", font=("Helvetica", 16, "bold"))
    reset_count_button = ttk.Button(
        root,
        text="RESET",
        style="Large.TButton",
        command=lambda: (count_holder.__setitem__(0, 0), count_var.set(0))
    )
    reset_count_button.pack(pady=(0, 0))

    def on_closing():
        # Ensure that the monitoring thread is stopped before closing the GUI
        stop_event.set()
        if monitor_thread and monitor_thread.is_alive():
            monitor_thread.join()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
