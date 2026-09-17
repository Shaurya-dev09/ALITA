# =========================================================
# command_manager.py
# FRIDAY X - Complete Final Version
# =========================================================

import os
import re
import subprocess
import webbrowser
import urllib.parse
from datetime import datetime

import pyautogui
import psutil

from core.system_control import SystemControl
from core.phone_manager import PhoneManager


class CommandManager:

    def __init__(self, voice_engine=None):
        self.voice_engine = voice_engine
        self.system = SystemControl()
        self.phone = PhoneManager()

        self.shutdown_pending = False
        self.restart_pending = False
        self.delete_pending = False
        self.pending_action = None

        # ==================== APPS ====================
        self.apps = {
            "chrome": "chrome",
            "edge": "msedge",
            "notepad": "notepad",
            "calculator": "calc",
            "paint": "mspaint",
            "cmd": "cmd",
            "terminal": "wt",
            "powershell": "powershell",
            "task manager": "taskmgr",
            "explorer": "explorer",
            "file manager": "explorer",
            "settings": "start ms-settings:",
            "camera": "start microsoft.windows.camera:",
            "photos": "start ms-photos:",
            "vlc": "vlc",
            "spotify": "spotify",
            "discord": "discord",
            "steam": "steam",
            "vs code": "code",
            "visual studio code": "code",
            "code": "code",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
        }

        # ==================== WEBSITES ====================
        self.websites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "gmail": "https://mail.google.com",
            "facebook": "https://facebook.com",
            "instagram": "https://instagram.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "linkedin": "https://linkedin.com",
            "github": "https://github.com",
            "chatgpt": "https://chat.openai.com",
            "whatsapp": "https://web.whatsapp.com",
            "reddit": "https://reddit.com",
            "netflix": "https://netflix.com",
        }

    # =========================================================
    # HELPERS
    # =========================================================

    def _normalize(self, command: str) -> str:
        command = str(command or "").lower().strip()
        command = re.sub(r"\s+", " ", command)
        return command

    def _speak(self, text: str):
        if self.voice_engine and hasattr(self.voice_engine, "speak"):
            try:
                self.voice_engine.speak(text)
            except Exception:
                pass

    # =========================================================
    # APP & WEBSITE
    # =========================================================

    def open_app(self, app_name: str):
        app_name = self._normalize(app_name)
        if app_name not in self.apps:
            return None

        app = self.apps[app_name]
        try:
            if app.startswith("start "):
                os.system(app)
            else:
                subprocess.Popen(app, shell=True)
            return True
        except Exception as e:
            print("[COMMAND] Open app error:", e)
            return False

    def open_website(self, site: str):
        site = self._normalize(site)
        if site not in self.websites:
            return None
        webbrowser.open(self.websites[site])
        return True

    def google_search(self, query: str):
        query = str(query).strip()
        if not query:
            return False
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return True

    def open_youtube(self):
        webbrowser.open("https://www.youtube.com")
        return True

    def play_youtube(self, command: str):
        query = command.lower()
        remove_words = [
            "youtube", "pe", "par", "mein", "me", "play", "video",
            "song", "music", "gana", "gaana", "lagao", "chalao",
            "chala do", "bajao", "baja do", "on", "karo", "do"
        ]
        for word in remove_words:
            query = query.replace(word, " ")
        query = re.sub(r"\s+", " ", query).strip()

        if not query:
            return self.open_youtube()

        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        webbrowser.open(url)
        return True

    def open_whatsapp(self):
        webbrowser.open("https://web.whatsapp.com")
        return True

    # =========================================================
    # SYSTEM INFO
    # =========================================================

    def battery_percent(self):
        battery = psutil.sensors_battery()
        if battery:
            return battery.percent
        return None

    def cpu_usage(self):
        return psutil.cpu_percent(interval=0.4)

    def ram_usage(self):
        return psutil.virtual_memory().percent

    def take_screenshot(self):
        try:
            image = pyautogui.screenshot()
            filename = "FRIDAY_Screenshot_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
            path = os.path.join(os.path.expanduser("\~"), "Desktop", filename)
            image.save(path)
            return path
        except Exception as e:
            print("[COMMAND] Screenshot error:", e)
            return None

    # =========================================================
    # PHONE
    # =========================================================

    def connect_phone(self):
        return self.phone.connect_phone()

    def mirror_phone(self):
        return self.phone.mirror_phone()

    def phone_battery(self):
        return self.phone.get_phone_battery()

    def phone_info(self):
        return self.phone.get_phone_info()

    # =========================================================
    # SYSTEM ACTIONS
    # =========================================================

    def volume_up(self):
        return self.system.volume_up()

    def volume_down(self):
        return self.system.volume_down()

    def mute(self):
        return self.system.mute()

    def play_pause(self):
        return self.system.play_pause()

    def next_track(self):
        return self.system.next_track()

    def previous_track(self):
        return self.system.previous_track()

    def lock_pc(self):
        return self.system.lock_pc()

    def open_file_manager(self):
        return self.system.open_file_explorer()

    def open_settings(self):
        return self.system.open_settings()

    def open_task_manager(self):
        return self.system.open_task_manager()

    def open_control_panel(self):
        return self.system.open_control_panel()

    def open_desktop(self):
        return self.system.open_desktop()

    def open_downloads(self):
        return self.system.open_downloads()

    def open_documents(self):
        return self.system.open_documents()

    def open_pictures(self):
        return self.system.open_pictures()

    # =========================================================
    # CONFIRMATION SYSTEM (Risky Actions)
    # =========================================================

    def request_confirmation(self, action_name: str, action_func):
        """Double confirmation ke liye pending action set karta hai"""
        self.pending_action = action_func
        self._speak(f"{action_name} ke liye confirmation chahiye Boss. Bolo yes ya confirm.")
        return "CONFIRMATION_REQUIRED"

    def confirm_pending(self):
        if self.pending_action:
            func = self.pending_action
            self.pending_action = None
            return func()
        return False

    def cancel_pending(self):
        self.pending_action = None
        self.shutdown_pending = False
        self.restart_pending = False
        self.delete_pending = False
        return True

    # =========================================================
    # MAIN PROCESS
    # =========================================================

    def process(self, command: str):
        command = self._normalize(command)
        if not command:
            return None

        print("[COMMAND]", command)

        # ---------- Confirmation handling ----------
        if command in ("yes", "confirm", "haa", "haan", "ok", "theek hai", "kar do"):
            if self.pending_action:
                return self.confirm_pending()
            return None

        if command in ("no", "cancel", "mat kar", "nahi", "stop"):
            if self.pending_action:
                self.cancel_pending()
                self._speak("Cancelled Boss.")
                return True
            return None

        # ---------- YouTube ----------
        if "youtube" in command and any(w in command for w in [
            "play", "song", "music", "video", "gana", "gaana", "lagao", "chalao", "bajao"
        ]):
            return self.play_youtube(command)

        if command in ("youtube", "open youtube", "youtube kholo", "youtube open"):
            return self.open_youtube()

        # ---------- WhatsApp ----------
        if command in ("whatsapp", "open whatsapp", "whatsapp kholo", "whatsapp open"):
            return self.open_whatsapp()

        # ---------- Search ----------
        if command.startswith("search "):
            return self.google_search(command[7:].strip())
        if command.startswith("google "):
            return self.google_search(command[7:].strip())

        # ---------- Websites ----------
        if command in self.websites:
            return self.open_website(command)

        # ---------- Apps ----------
        if command in self.apps:
            return self.open_app(command)

        if command.startswith("open "):
            name = command[5:].strip()
            if name in self.apps:
                return self.open_app(name)
            if name in self.websites:
                return self.open_website(name)

        # ---------- System Info ----------
        if "battery" in command and "phone" not in command:
            percent = self.battery_percent()
            return percent

        if "cpu" in command:
            return self.cpu_usage()

        if "ram" in command:
            return self.ram_usage()

        if "screenshot" in command or "screen shot" in command:
            return self.take_screenshot()

        # ---------- Phone ----------
        if command in ("connect phone", "phone connect"):
            return self.connect_phone()
        if command in ("mirror phone", "phone mirror", "screen mirror"):
            return self.mirror_phone()
        if command in ("phone battery", "mobile battery"):
            return self.phone_battery()
        if command in ("phone info", "mobile info"):
            return self.phone_info()

        # ---------- Volume & Media ----------
        if command in ("volume up", "volume badhao", "awaz badhao"):
            return self.volume_up()
        if command in ("volume down", "volume kam karo", "awaz kam karo"):
            return self.volume_down()
        if command in ("mute", "unmute", "chup karo"):
            return self.mute()
        if command in ("play", "pause", "play pause"):
            return self.play_pause()
        if command in ("next", "next song", "next track", "aage karo"):
            return self.next_track()
        if command in ("previous", "previous song", "previous track", "piche karo"):
            return self.previous_track()

        # ---------- System ----------
        if command in ("lock pc", "lock computer", "pc lock karo", "lock"):
            return self.lock_pc()

        if command in ("file manager", "open file manager", "explorer kholo"):
            return self.open_file_manager()

        if command in ("settings", "open settings", "settings kholo"):
            return self.open_settings()

        if command in ("task manager", "open task manager"):
            return self.open_task_manager()

        if command == "control panel":
            return self.open_control_panel()

        # ---------- Folders ----------
        if command in ("desktop", "open desktop"):
            return self.open_desktop()
        if command in ("downloads", "open downloads"):
            return self.open_downloads()
        if command in ("documents", "open documents"):
            return self.open_documents()
        if command in ("pictures", "open pictures"):
            return self.open_pictures()

        # ---------- Risky actions (confirmation required) ----------
        if command in ("shutdown", "pc band karo", "shutdown karo"):
            return self.request_confirmation("Shutdown", self.system.shutdown_pc)

        if command in ("restart", "restart karo", "pc restart"):
            return self.request_confirmation("Restart", self.system.restart_pc)

        return None  # AI fallback

    # =========================================================
    # SHUTDOWN
    # =========================================================

    def shutdown(self):
        try:
            self.phone.shutdown()
        except Exception:
            pass
        return True

    def __repr__(self):
        return "<FRIDAY X CommandManager>"