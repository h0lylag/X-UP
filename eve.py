# xup/eve.py
import win32gui

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

def update_eve_clients(character_var, combobox):
    """
    Periodically update the list of EVE clients in the given combobox.
    """
    eve_windows = list_eve_windows()
    eve_windows = [window.replace("EVE - ", "") for window in eve_windows]
    current_value = character_var.get()

    if current_value not in eve_windows and eve_windows:
        character_var.set(eve_windows[0])
    
    combobox['values'] = eve_windows
    if current_value not in eve_windows and eve_windows:
        combobox.set(eve_windows[0])
    
    # Schedule the next update in 5 seconds
    combobox.after(5000, update_eve_clients, character_var, combobox)
