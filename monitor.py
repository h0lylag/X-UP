# xup/monitor.py
import os
import re
import time
from threading import Thread, Event
from tkinter import messagebox

monitor_thread = None
stop_event = Event()

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

def monitor_log_file(log_file, character_name, count_var, count_holder):
    """Monitor the log file for updates."""
    print(f"Monitoring log file: {log_file}")
    # Matches any single dash character.
    dash_pattern = re.compile(r'-')
    x_pattern = re.compile(r" > *(?:x+\s?\d*|\d\s?x)\b", re.IGNORECASE)
    
    try:
        with open(log_file, 'r', encoding='utf-16', errors='ignore') as f:
            f.seek(0, os.SEEK_END)  # Move to the end of the file
            
            while not stop_event.is_set():
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                print(f"Read line: {line.strip()}")

                # Reset count if any dash is detected
                if dash_pattern.search(line):
                    count_holder[0] = 0
                    count_var.set(0)
                    print(f"Count reset by dash. Line: {line.strip()}")
                    continue
                
                # Check for an "x" pattern
                if x_pattern.search(line):
                    multi_x_pattern = re.compile(r" > *(?:x+\s?(\d+)|(\d+)\s?x)\b", re.IGNORECASE)
                    match = multi_x_pattern.search(line)
                    if match:
                        x_count = int(match.group(1) or match.group(2))
                        x_count = min(x_count, 25)  # Cap the count at 25
                        count_holder[0] += x_count
                        count_var.set(count_holder[0])
                        print(f"Updated count by {x_count}: {count_holder[0]} - Line: {line.strip()}")
                    else:
                        count_holder[0] += 1
                        count_var.set(count_holder[0])
                        print(f"Updated count: {count_holder[0]} - Line: {line.strip()}")

    except Exception as e:
        print(f"Error while monitoring log file: {e}")

def start_monitoring(character_name, count_var, log_file_var, count_holder):
    """Start (or restart) the monitoring thread for the given character."""
    global monitor_thread, stop_event

    if monitor_thread and monitor_thread.is_alive():
        stop_event.set()
        monitor_thread.join()

    stop_event.clear()
    log_file = find_latest_log(character_name)
    if not log_file:
        messagebox.showerror("Error", f"No log file found for character: {character_name}")
        return
    log_file_var.set(os.path.basename(log_file))
    monitor_thread = Thread(target=monitor_log_file, args=(log_file, character_name, count_var, count_holder))
    monitor_thread.daemon = True
    monitor_thread.start()

def on_load_reset_button_click(character_var, count_var, log_file_var, count_holder):
    """Reset the count and (re)start monitoring for the selected character."""
    character_name = character_var.get().replace("EVE - ", "").strip()
    count_holder[0] = 0
    count_var.set(0)
    start_monitoring(character_name, count_var, log_file_var, count_holder)
