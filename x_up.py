import os
import re
import time
import win32gui
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread, Event

monitor_thread = None
stop_event = Event()

version_number = "0.0.1"

def list_eve_windows():
    """List EVE windows to determine characters."""
    def enum_windows_callback(hwnd, window_names):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.startswith("EVE - "):
                window_names.append(title)
        return True

    eve_windows = []
    win32gui.EnumWindows(enum_windows_callback, eve_windows)
    return eve_windows

def find_latest_log(character_name):
    """Find the latest Fleet log file for the given character."""
    log_dir = os.path.expanduser(r"~\Documents\EVE\logs\Chatlogs")
    print(f"Looking for logs in directory: {log_dir}")
    
    try:
        fleet_logs = [os.path.join(log_dir, file) for file in os.listdir(log_dir) if file.startswith("Fleet_")]
    except FileNotFoundError:
        print(f"Log directory not found: {log_dir}")
        return None
    except Exception as e:
        print(f"Error accessing log directory: {e}")
        return None
    
    fleet_logs.sort(key=os.path.getmtime, reverse=True)  # Sort by modification time
    
    character_pattern = re.compile(rf"Listener:\s+{character_name.strip()}")
    
    for log_file in fleet_logs:
        try:
            with open(log_file, 'r', encoding='utf-16', errors='ignore') as f:
                content = f.read()
                if character_pattern.search(content):
                    print(f"Character '{character_name}' found in log file: {log_file}")
                    return log_file
        except Exception as e:
            print(f"Error reading log file {log_file}: {e}")
    
    print(f"Character '{character_name}' not found in any log file.")
    return None

def monitor_log_file(log_file, character_name, count_var):
    """Monitor the log file for updates."""
    print(f"Monitoring log file: {log_file}")
    dash_pattern = re.compile(rf" ] {character_name} > -{{3,}}")
    x_pattern = re.compile(r" ] [\d\wa-zA-Z\'\-\_ ]+ > +(x| x)", re.IGNORECASE)
    #x_pattern = re.compile(r" > +(x|x\d *x|x *\d) *", re.IGNORECASE)
    
    try:
        with open(log_file, 'r', encoding='utf-16', errors='ignore') as f:
            # Move to the end of the file
            f.seek(0, os.SEEK_END)
            
            count = 0
            while not stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.1)  # Avoid busy waiting
                    continue

                # Print the line being read for debugging
                print(f"Read line: {line.strip()}")

                # Check if the line matches the dash pattern
                if dash_pattern.search(line):
                    count = 0
                    count_var.set(count)
                    print(f"Count reset by dashes from {character_name}. Line: {line.strip()}")
                    continue
                
                # Check if the line matches the x pattern
                ### 
                ### This area is where we need to detect if users are X-ing up with multiple X's
                ###
                if x_pattern.search(line):
                    count += 1
                    count_var.set(count)
                    print(f"Updated count: {count} - Line: {line.strip()}")

    except Exception as e:
        print(f"Error while monitoring log file: {e}")

def start_monitoring(character_name, count_var, log_file_var):
    global monitor_thread, stop_event

    # Stop the previous monitoring thread if it exists
    if monitor_thread and monitor_thread.is_alive():
        stop_event.set()
        monitor_thread.join()

    stop_event.clear()
    log_file = find_latest_log(character_name)
    if not log_file:
        messagebox.showerror("Error", f"No log file found for character: {character_name}")
        return
    log_file_var.set(os.path.basename(log_file))
    monitor_thread = Thread(target=monitor_log_file, args=(log_file, character_name, count_var))
    monitor_thread.daemon = True
    monitor_thread.start()

def on_load_reset_button_click(character_var, count_var, log_file_var):
    character_name = character_var.get().replace("EVE - ", "").strip()
    count_var.set(0)
    start_monitoring(character_name, count_var, log_file_var)

def update_eve_clients(character_var, combobox):
    eve_windows = list_eve_windows()
    eve_windows = [window.replace("EVE - ", "") for window in eve_windows]
    current_value = character_var.get()
    
    if current_value not in eve_windows:
        character_var.set(eve_windows[0] if eve_windows else "")
    
    combobox['values'] = eve_windows
    if current_value not in eve_windows:
        combobox.set(eve_windows[0] if eve_windows else "")
    
    combobox.after(5000, update_eve_clients, character_var, combobox)  # Check every 5 seconds

def toggle_always_on_top():
    if always_on_top_var.get():
        root.attributes('-topmost', True)
    else:
        root.attributes('-topmost', False)

def show_about():
    about_text = (
        "X-UP is a tool for EVE Online that helps people count. Because counting is hard.\n\n"
        f"Version: {version_number}\n\n"
        "Made by h0ly lag"
    )
    messagebox.showinfo("About X-UP", about_text)

def create_gui():
    global root, always_on_top_var
    root = tk.Tk()
    root.title("X-UP")
    root.geometry("285x285")  # Set the initial size to be square
    root.resizable(False, False)  # Make the window non-resizable

    # Create a menu bar
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    # Create a "Settings" menu
    settings_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)

    # Add the "Always on Top" checkbox to the "Settings" menu
    always_on_top_var = tk.BooleanVar()
    settings_menu.add_checkbutton(label="Always on Top", variable=always_on_top_var, command=toggle_always_on_top)

    # Add the "About" button as a root-level menu item
    menu_bar.add_command(label="About", command=show_about)

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

    log_file_var = tk.StringVar()
    log_file_var.set("None")

    ttk.Label(root, text="EVE Client:").pack(pady=5)
    combobox = ttk.Combobox(root, textvariable=character_var, values=eve_windows, state='readonly')
    combobox.pack(pady=5)

    button_frame = ttk.Frame(root)
    button_frame.pack(pady=(20, 0))
    ttk.Button(button_frame, text="Load / Reset", command=lambda: on_load_reset_button_click(character_var, count_var, log_file_var)).pack(side=tk.LEFT, padx=5)

    ttk.Label(root, text="Log File Loaded:").pack()
    ttk.Label(root, textvariable=log_file_var).pack()

    ttk.Label(root, text="X Count:", font=("Helvetica", 16)).pack(pady=(20, 0))
    ttk.Label(root, textvariable=count_var, font=("Helvetica", 48)).pack(pady=(0, 30))  # Add more padding to the bottom

    combobox.after(5000, update_eve_clients, character_var, combobox)  # Start periodic check

    def on_closing():
        stop_event.set()
        if monitor_thread and monitor_thread.is_alive():
            monitor_thread.join()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    create_gui()