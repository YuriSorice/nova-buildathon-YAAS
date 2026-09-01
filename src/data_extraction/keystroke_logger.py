import csv
import time
from pynput import mouse, keyboard

log_file = "keystroke_log.csv"

with open(log_file, "w", newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "key", "action"])

def log_event(key, action):
    """Append Unix timestamp, key pressed, and action to the CSV file."""
    key_name = str(key).replace("'", "")

    with open(log_file, mode="a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([time.time(), key_name, action])

def on_press(key):
    """Records the keypress as well as the associated action."""
    log_event(key, "pressed")


def on_release(key):
    """Resets the keyboard as nothing pressed, if the key released is ESC, stop recording."""
    log_event(key, "released")

    if key == keyboard.Key.esc:
        return False

print(f"Logging keystrokes to {log_file}. Press ESC to stop.")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()