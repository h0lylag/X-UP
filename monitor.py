# xup/monitor.py
import os
import re
import time
from threading import Thread, Event
from tkinter import messagebox

monitor_thread = None
stop_event = Event()

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

    # Sort logs by modification time (most recent first)
    fleet_logs.sort(key=os.path.getmtime, reverse=True)
    
    # Prepare the regex to search for the character in the log
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

def monitor_log_updates(log_file, character_name, count_var, count_holder):
    """
    Continuously monitor the given log file for new lines.
    Resets the count if any dash is detected.
    Increments the count when an "x" pattern is found (capped at 25 per match).
    """
    print(f"Monitoring log file: {log_file}")
    dash_pattern = re.compile(r'-')
    x_pattern = re.compile(r" > *(?:x+\s?\d*|\d\s?x)\b", re.IGNORECASE)
    multi_x_pattern = re.compile(r" > *(?:x+\s?(\d+)|(\d+)\s?x)\b", re.IGNORECASE)
    
    try:
        with open(log_file, 'r', encoding='utf-16', errors='ignore') as f:
            # Move to end of file
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
        return  # Do nothing if no valid client is available
    count_holder[0] = 0
    count_var.set(0)
    start_monitoring(character_name, count_var, log_file_var, count_holder)
