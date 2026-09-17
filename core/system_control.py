# =========================================================
# system_control.py
# FRIDAY X - Complete Final Version
# =========================================================

import ctypes
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

import psutil
import pyautogui
import webbrowser

try:
    import screen_brightness_control as sbc
except Exception:
    sbc = None

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

try:
    import winshell
except Exception:
    winshell = None


class SystemControl:

    # Windows Virtual Keys
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1
    VK_MEDIA_STOP = 0xB2
    VK_MEDIA_PLAY_PAUSE = 0xB3
    KEYEVENTF_KEYUP = 0x0002

    def __init__(self, speak_callback=None):
        self.speak = speak_callback
        self.home = Path.home()
        self.desktop = self.home / "Desktop"
        self.downloads = self.home / "Downloads"
        self.documents = self.home / "Documents"
        self.pictures = self.home / "Pictures"
        self.music = self.home / "Music"
        self.videos = self.home / "Videos"

    def _speak(self, text):
        if self.speak:
            try:
                self.speak(str(text))
            except Exception:
                pass

    def _press_key(self, key):
        try:
            ctypes.windll.user32.keybd_event(key, 0, 0, 0)
            ctypes.windll.user32.keybd_event(key, 0, self.KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    def _run(self, *cmd):
        try:
            subprocess.Popen(
                list(cmd),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    # =========================================================
    # VOLUME
    # =========================================================

    def volume_up(self, steps=5):
        for _ in range(max(1, int(steps))):
            self._press_key(self.VK_VOLUME_UP)
        return True

    def volume_down(self, steps=5):
        for _ in range(max(1, int(steps))):
            self._press_key(self.VK_VOLUME_DOWN)
        return True

    def mute(self):
        return self._press_key(self.VK_VOLUME_MUTE)

    # =========================================================
    # MEDIA
    # =========================================================

    def play_pause(self):
        return self._press_key(self.VK_MEDIA_PLAY_PAUSE)

    def next_track(self):
        return self._press_key(self.VK_MEDIA_NEXT_TRACK)

    def previous_track(self):
        return self._press_key(self.VK_MEDIA_PREV_TRACK)

    def stop_media(self):
        return self._press_key(self.VK_MEDIA_STOP)

    # =========================================================
    # POWER
    # =========================================================

    def shutdown_pc(self, delay=5):
        return self._run("shutdown", "/s", "/t", str(delay))

    def restart_pc(self, delay=5):
        return self._run("shutdown", "/r", "/t", str(delay))

    def cancel_shutdown(self):
        return self._run("shutdown", "/a")

    def sleep_pc(self):
        try:
            ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
            return True
        except Exception:
            return False

    def lock_pc(self):
        try:
            ctypes.windll.user32.LockWorkStation()
            return True
        except Exception:
            return False

    def logout(self):
        return self._run("shutdown", "/l")

    # =========================================================
    # BRIGHTNESS
    # =========================================================

    def brightness_up(self, value=10):
        if sbc is None:
            return False
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(min(current + value, 100))
            return True
        except Exception:
            return False

    def brightness_down(self, value=10):
        if sbc is None:
            return False
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(max(current - value, 0))
            return True
        except Exception:
            return False

    # =========================================================
    # SCREENSHOT
    # =========================================================

    def screenshot(self):
        if ImageGrab is None:
            return None
        try:
            filename = "FRIDAY_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            path = self.desktop / filename
            image = ImageGrab.grab()
            image.save(path)
            return str(path)
        except Exception:
            return None

    # =========================================================
    # FOLDERS
    # =========================================================

    def open_desktop(self):
        os.startfile(self.desktop)
        return True

    def open_downloads(self):
        os.startfile(self.downloads)
        return True

    def open_documents(self):
        os.startfile(self.documents)
        return True

    def open_pictures(self):
        os.startfile(self.pictures)
        return True

    def open_music(self):
        os.startfile(self.music)
        return True

    def open_videos(self):
        os.startfile(self.videos)
        return True

    def open_file_explorer(self):
        return self._run("explorer.exe")

    # =========================================================
    # SETTINGS
    # =========================================================

    def open_settings(self):
        return self._run("explorer.exe", "ms-settings:")

    def open_display_settings(self):
        return self._run("explorer.exe", "ms-settings:display")

    def open_wifi_settings(self):
        return self._run("explorer.exe", "ms-settings:network-wifi")

    def open_bluetooth_settings(self):
        return self._run("explorer.exe", "ms-settings:bluetooth")

    def open_sound_settings(self):
        return self._run("explorer.exe", "ms-settings:sound")

    def open_apps_settings(self):
        return self._run("explorer.exe", "ms-settings:appsfeatures")

    # =========================================================
    # SYSTEM APPS
    # =========================================================

    def open_task_manager(self):
        return self._run("taskmgr.exe")

    def open_control_panel(self):
        return self._run("control.exe")

    def open_cmd(self):
        return self._run("cmd.exe")

    def open_powershell(self):
        return self._run("powershell.exe")

    def open_registry(self):
        return self._run("regedit.exe")

    def open_device_manager(self):
        return self._run("devmgmt.msc")

    def open_disk_management(self):
        return self._run("diskmgmt.msc")

    def open_services(self):
        return self._run("services.msc")

    # =========================================================
    # SYSTEM INFO
    # =========================================================

    def battery_percentage(self):
        try:
            battery = psutil.sensors_battery()
            return battery.percent if battery else None
        except Exception:
            return None

    def battery_plugged(self):
        try:
            battery = psutil.sensors_battery()
            return battery.power_plugged if battery else None
        except Exception:
            return None

    def cpu_usage(self):
        try:
            return psutil.cpu_percent(interval=0.5)
        except Exception:
            return None

    def ram_usage(self):
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return None

    def disk_usage(self):
        try:
            return psutil.disk_usage("/").percent
        except Exception:
            return None

    def internet_available(self):
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), 3)
            return True
        except Exception:
            return False

    # =========================================================
    # CLEANUP
    # =========================================================

    def empty_recycle_bin(self):
        if winshell is None:
            return False
        try:
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            return True
        except Exception:
            return False

    def clear_temp(self):
        try:
            temp = os.environ.get("TEMP", "")
            if not temp:
                return False
            for item in os.listdir(temp):
                path = os.path.join(temp, item)
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
            return True
        except Exception:
            return False

    # =========================================================
    # PROCESS
    # =========================================================

    def kill_process(self, process_name):
        try:
            subprocess.call(
                ["taskkill", "/F", "/IM", process_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    # =========================================================
    # WINDOW CONTROLS
    # =========================================================

    def minimize_all(self):
        pyautogui.hotkey("win", "d")
        return True

    def show_desktop(self):
        pyautogui.hotkey("win", "d")
        return True

    def switch_window(self):
        pyautogui.hotkey("alt", "tab")
        return True

    def close_window(self):
        pyautogui.hotkey("alt", "f4")
        return True

    def refresh(self):
        pyautogui.press("f5")
        return True

    # =========================================================
    # CLIPBOARD
    # =========================================================

    def copy_to_clipboard(self, text):
        try:
            import pyperclip
            pyperclip.copy(str(text))
            return True
        except Exception:
            return False

    def get_clipboard(self):
        try:
            import pyperclip
            return pyperclip.paste()
        except Exception:
            return None

    # =========================================================
    # WIFI / BLUETOOTH (basic)
    # =========================================================

    def wifi_on(self):
        try:
            subprocess.call(
                ["netsh", "interface", "set", "interface", "Wi-Fi", "enable"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def wifi_off(self):
        try:
            subprocess.call(
                ["netsh", "interface", "set", "interface", "Wi-Fi", "disable"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def bluetooth_settings(self):
        return self.open_bluetooth_settings()

    # =========================================================
    # SHUTDOWN
    # =========================================================

    def shutdown(self):
        return True

    def __repr__(self):
        return "<FRIDAY X SystemControl>"