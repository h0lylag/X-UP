# xup/eve.py
import ctypes
from ctypes import wintypes

EVE_PREFIX = "EVE - "

def get_eve_windows():
    """
    Retrieve a list of EVE client names from visible windows using ctypes.
    The EVE_PREFIX is removed from the returned names.
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
                        if title.startswith(EVE_PREFIX):
                            clients.append(title.replace(EVE_PREFIX, ""))
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
