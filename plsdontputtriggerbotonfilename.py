import json
import time
import threading
import keyboard
import sys
import win32api
from ctypes import WinDLL
import numpy as np
from mss import mss
import socket
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Socket connection setup
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect(('localhost', 65432))
except Exception as e:
    logging.error(f"Failed to connect to server: {e}")
    sys.exit()

def exiting():
    """Handle graceful exit."""
    logging.info("Exiting the program...")
    try:
        sys.exit()
    except:
        raise SystemExit

# Windows libraries for screen metrics and DPI settings
user32, kernel32, shcore = (
    WinDLL("user32", use_last_error=True),
    WinDLL("kernel32", use_last_error=True),
    WinDLL("shcore", use_last_error=True),
)

shcore.SetProcessDpiAwareness(2)
WIDTH, HEIGHT = [user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)]

ZONE = 5
GRAB_ZONE = (
    int(WIDTH / 2 - ZONE),
    int(HEIGHT / 2 - ZONE),
    int(WIDTH / 2 + ZONE),
    int(HEIGHT / 2 + ZONE),
)

class TriggerBot:
    def __init__(self):
        self.sct = mss()
        self.triggerbot = False
        self.triggerbot_toggle = True
        self.exit_program = False
        self.toggle_lock = threading.Lock()
        self.Spoofed = 'k'

        # Load config data
        try:
            with open('config.json') as json_file:
                data = json.load(json_file)
                self.trigger_hotkey = int(data["trigger_hotkey"], 16)
                self.always_enabled = data["always_enabled"]
                self.trigger_delay = data["trigger_delay"]
                self.base_delay = data["base_delay"]
                self.color_tolerance = data["color_tolerance"]
                self.R, self.G, self.B = (250, 100, 250)  # Purple color
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            exiting()

    def cooldown(self):
        """Cooldown after toggling the triggerbot."""
        time.sleep(0.1)
        with self.toggle_lock:
            self.triggerbot_toggle = True
            beeps = (kernel32.Beep(440, 75), kernel32.Beep(700, 100)) if self.triggerbot else (kernel32.Beep(440, 75), kernel32.Beep(200, 100))
            logging.info("Cooldown finished, triggerbot status: %s", self.triggerbot)

    def search_for_color(self):
        """Capture screen and search for specific color."""
        img = np.array(self.sct.grab(GRAB_ZONE))
        pixels = img.reshape(-1, 4)

        color_mask = (
            (pixels[:, 0] > self.R - self.color_tolerance) & (pixels[:, 0] < self.R + self.color_tolerance) &
            (pixels[:, 1] > self.G - self.color_tolerance) & (pixels[:, 1] < self.G + self.color_tolerance) &
            (pixels[:, 2] > self.B - self.color_tolerance) & (pixels[:, 2] < self.B + self.color_tolerance)
        )
        matching_pixels = pixels[color_mask]

        if self.triggerbot and len(matching_pixels) > 0:
            delay_percentage = self.trigger_delay / 100.0
            actual_delay = self.base_delay + self.base_delay * delay_percentage
            time.sleep(actual_delay)
            sock.send(self.Spoofed.encode())
            logging.info("Sent key: %s", self.Spoofed)

    def toggle(self):
        """Toggle the triggerbot on/off."""
        if keyboard.is_pressed("f10"):
            with self.toggle_lock:
                if self.triggerbot_toggle:
                    self.triggerbot = not self.triggerbot
                    logging.info("Triggerbot toggled to: %s", self.triggerbot)
                    self.triggerbot_toggle = False
                    threading.Thread(target=self.cooldown).start()

        if keyboard.is_pressed("ctrl+shift+x"):  # Exit the program
            self.exit_program = True
            exiting()

    def hold(self):
        """Hold mode when triggerbot is not always enabled."""
        while True:
            if win32api.GetAsyncKeyState(self.trigger_hotkey) < 0:
                self.triggerbot = True
                self.search_for_color()
            else:
                time.sleep(0.1)

            if keyboard.is_pressed("ctrl+shift+x"):
                self.exit_program = True
                exiting()

    def start(self):
        """Main function to start the triggerbot."""
        while not self.exit_program:
            if self.always_enabled:
                self.toggle()
                self.search_for_color() if self.triggerbot else time.sleep(0.1)
            else:
                self.hold()

# Run the triggerbot
if __name__ == "__main__":
    TriggerBot().start()

