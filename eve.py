# xup/eve.py
import win32gui

def get_eve_windows():
    """
    Retrieve a list of EVE client names from visible windows,
    with the "EVE - " prefix removed.
    """
    clients = []
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.startswith("EVE - "):
                clients.append(title.replace("EVE - ", ""))
    win32gui.EnumWindows(enum_callback, None)
    return clients

def refresh_eve_clients(character_var, combobox):
    """
    Update the combobox with the current list of EVE clients.
    If clients are available, the dropdown is enabled; otherwise, it's disabled.
    This function reschedules itself every 5 seconds.
    """
    clients = get_eve_windows()  # Returns client names without the "EVE - " prefix
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
