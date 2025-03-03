import ctypes
from ctypes import wintypes
import os
import re
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Event, Thread


VERSION = "v0.0.4"

monitor_thread = None
stop_event = Event()


# Used to retrieve a list of EVE clients from running applications
def get_eve_windows():
    """
    Retrieve a list of EVE client names from visible windows using ctypes.
    """
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    GetWindowTextLength = user32.GetWindowTextLengthW
    GetWindowText = user32.GetWindowTextW
    IsWindowVisible = user32.IsWindowVisible

    clients = []

    def foreach_window(hwnd, _):
        try:
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    # GetWindowText returns the number of characters copied
                    if GetWindowText(hwnd, buff, length + 1) > 0:
                        title = buff.value
                        window_prefix = "EVE - "
                        if title.startswith(window_prefix):
                            clients.append(title.replace(window_prefix, ""))
        except Exception as e:
            print(f"Error processing window {hwnd}: {e}")
        return True

    try:
        result = EnumWindows(EnumWindowsProc(foreach_window), 0)
        if not result:
            err = ctypes.get_last_error()
            print(f"EnumWindows failed with error code: {err}")
    except Exception as e:
        print(f"Exception during EnumWindows: {e}")

    return clients


# Updates the EVE client dropdown with the current list of clients
def refresh_eve_clients(character_var, combobox):
    """
    Update the combobox with the current list of EVE clients.
    If clients are available, the dropdown is enabled; otherwise, it's disabled.
    This function reschedules itself every 5 seconds.
    """
    try:
        clients = get_eve_windows()  # Returns client names without the EVE_PREFIX
    except Exception as e:
        print(f"Error retrieving EVE windows: {e}")
        clients = []

    if clients:
        combobox.config(state="readonly")
        combobox['values'] = clients
        # If the current selection is not in the new list, update it
        if character_var.get() not in clients:
            character_var.set(clients[0])
            combobox.set(clients[0])
    else:
        combobox.config(state="disabled")
        combobox['values'] = ["No EVE clients found"]
        character_var.set("No EVE clients found")
        combobox.set("No EVE clients found")
        
    combobox.after(5000, refresh_eve_clients, character_var, combobox)


# Searches for the most recent fleet log file for the specified character
def get_latest_log(character_name):
    """
    Retrieve the most recent Fleet log file for the specified character.
    Returns the full path to the log file if found, or None otherwise.
    """
    log_dir = os.path.expanduser(r"~\Documents\EVE\logs\Chatlogs")
    print(f"Searching logs in: {log_dir}")
    
    try:
        fleet_logs = [os.path.join(log_dir, file) 
                      for file in os.listdir(log_dir) if file.startswith("Fleet_")]
    except FileNotFoundError:
        print(f"Log directory not found: {log_dir}")
        return None
    except Exception as e:
        print(f"Error accessing log directory: {e}")
        return None

    fleet_logs.sort(key=os.path.getmtime, reverse=True)
    
    pattern = re.compile(rf"Listener:\s+{re.escape(character_name.strip())}")
    for log_file in fleet_logs:
        try:
            with open(log_file, 'r', encoding='utf-16', errors='ignore') as f:
                if pattern.search(f.read()):
                    print(f"Found log for '{character_name}': {log_file}")
                    return log_file
        except Exception as e:
            print(f"Error reading log file {log_file}: {e}")
    
    print(f"No log found for character: {character_name}")
    return None



# Continuously monitors the log file for new lines and updates the count
# This function is called when the log-monitoring thread is started
def monitor_log_updates(log_file, character_name, count_var, count_holder):
    """
    Continuously monitor the given log file for new lines.
    Resets the count if any dash is detected.
    Increments the count when an "x" pattern is found (capped at 25 per match).
    """
    print(f"Monitoring log file: {log_file}")
    dash_pattern = re.compile(r'-')
    x_pattern = re.compile(r"\b(?:x(?:\s*(\d+))?|(\d+)\s*x)\b", re.IGNORECASE)
    multi_x_pattern = re.compile(r"\b(?:x(?:\s*(\d+))?|(\d+)\s*x)\b", re.IGNORECASE)

    try:
        with open(log_file, 'r', encoding='utf-16', errors='ignore') as f:
            f.seek(0, os.SEEK_END)
            
            while not stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                print(f"Read line: {line.strip()}")
                
                if dash_pattern.search(line):
                    count_holder[0] = 0
                    count_var.set(0)
                    print(f"Count reset by dash. Line: {line.strip()}")
                    continue
                
                if x_pattern.search(line):
                    match = multi_x_pattern.search(line)
                    if match:
                        try:
                            x_count = int(match.group(1) or match.group(2))
                        except (ValueError, TypeError):
                            x_count = 1
                    else:
                        x_count = 1
                    count_holder[0] += x_count
                    count_var.set(count_holder[0])
                    print(f"Incremented count by {x_count}: {count_holder[0]} (Line: {line.strip()})")
    except Exception as e:
        print(f"Error monitoring log file: {e}")


# Starts the log-monitoring thread for the selected character
# This function is called when the "Load Character" button is clicked
def start_monitoring(character_name, count_var, log_file_var, count_holder):
    """
    Start (or restart) the log-monitoring thread for the specified character.
    If a monitoring thread is already active, it is stopped before starting a new one.
    """
    global monitor_thread, stop_event

    if monitor_thread and monitor_thread.is_alive():
        stop_event.set()
        monitor_thread.join()
    
    stop_event.clear()
    log_file = get_latest_log(character_name)
    if not log_file:
        messagebox.showerror("Error", f"No log file found for character: {character_name}")
        return
    log_file_var.set(os.path.basename(log_file))
    monitor_thread = Thread(
        target=monitor_log_updates, 
        args=(log_file, character_name, count_var, count_holder)
    )
    monitor_thread.daemon = True
    monitor_thread.start()

def load_character_monitor(character_var, count_var, log_file_var, count_holder):
    """
    Reset the count and initiate monitoring for the selected character.
    If no valid EVE client is selected, do nothing.
    """
    character_name = character_var.get().replace("EVE - ", "").strip()
    if character_name == "No EVE clients found":
        return 
    count_holder[0] = 0
    count_var.set(0)
    start_monitoring(character_name, count_var, log_file_var, count_holder)


# try to set the window icon from the static folder if possible but
# this thing has been finicky when compiled idk
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


# reset the internal counter and update the display
def reset_count(count_holder, count_var):
    """Reset the internal counter and update the display."""
    count_holder[0] = 0
    count_var.set(0)


# toggle the 'always on top' state for the main window
def toggle_always_on_top(root, top_var):
    """Toggle the 'always on top' state for the main window."""
    root.attributes('-topmost', top_var.get())

# display the About dialog
def show_about():
    """Display the About dialog."""
    about_text = (
        "X-UP is a tool for EVE Online that helps people count. Because counting is hard.\n\n"
        "Made by h0ly lag"
    )
    messagebox.showinfo("About X-UP", about_text)


# build the main GUI window
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


# run the GUI
if __name__ == "__main__":
    build_gui()
