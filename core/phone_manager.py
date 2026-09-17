# =========================================================
# phone_manager.py
# FRIDAY X - Complete Final Version
# =========================================================

import os
import shutil
import subprocess
import time


class PhoneManager:

    def __init__(self, speak_callback=None):
        self.speak = speak_callback
        self.adb_path = None
        self.device_id = None
        self._find_adb()

    def _speak(self, text):
        if self.speak and text:
            try:
                self.speak(str(text))
            except Exception:
                pass

    # =========================================================
    # ADB DETECTION
    # =========================================================

    def _find_adb(self):
        candidates = [
            shutil.which("adb"),
            os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb.exe"),
            os.path.join(os.environ.get("ANDROID_SDK_ROOT", ""), "platform-tools", "adb.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe"),
        ]

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                self.adb_path = candidate
                return True

        self.adb_path = None
        return False

    def is_available(self):
        return self._find_adb()

    # =========================================================
    # DEVICE LIST
    # =========================================================

    def get_devices(self):
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if result.returncode != 0:
                return []

            devices = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("List of devices"):
                    continue
                parts = line.split("\t")
                if len(parts) >= 2 and parts[1].strip() == "device":
                    devices.append(parts[0].strip())

            return devices
        except Exception as error:
            print("[PHONE] Device detection error:", error)
            return []

    def refresh_device(self):
        devices = self.get_devices()
        if devices:
            self.device_id = devices[0]
            return True
        self.device_id = None
        return False

    # =========================================================
    # CONNECT
    # =========================================================

    def connect_phone(self):
        if not self.is_available():
            self._speak("ADB is not installed on this laptop, Boss.")
            return False

        if self.refresh_device():
            self._speak("Your phone is connected, Boss.")
            return True

        self._speak("I can't find your phone, Boss.")
        return False

    # =========================================================
    # ADB COMMAND
    # =========================================================

    def adb_command(self, *arguments, timeout=15):
        if not self.is_available():
            return None

        if not self.device_id:
            if not self.refresh_device():
                return None

        command = [self.adb_path, "-s", self.device_id, *arguments]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            if result.returncode != 0:
                error_text = result.stderr.strip()
                if error_text:
                    print("[PHONE] ADB error:", error_text)
                return None

            return result.stdout.strip()
        except Exception as error:
            print("[PHONE] ADB command error:", error)
            return None

    # =========================================================
    # PHONE INFO
    # =========================================================

    def get_phone_info(self):
        if not self.refresh_device():
            return None

        return {
            "manufacturer": self.adb_command("shell", "getprop", "ro.product.manufacturer"),
            "model": self.adb_command("shell", "getprop", "ro.product.model"),
            "android_version": self.adb_command("shell", "getprop", "ro.build.version.release"),
            "device_id": self.device_id,
        }

    def get_phone_battery(self):
        output = self.adb_command("shell", "dumpsys", "battery")
        if not output:
            return None

        level = None
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("level:"):
                try:
                    level = int(line.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    pass
                break

        return level

    # =========================================================
    # SCREENSHOT
    # =========================================================

    def phone_screen(self):
        if not self.refresh_device():
            self._speak("Your phone is not connected, Boss.")
            return None

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(desktop, f"FRIDAY_Phone_{timestamp}.png")

        try:
            with open(output_path, "wb") as output_file:
                result = subprocess.run(
                    [self.adb_path, "-s", self.device_id, "exec-out", "screencap", "-p"],
                    stdout=output_file,
                    stderr=subprocess.PIPE,
                    timeout=20,
                    check=False,
                )

            if result.returncode != 0:
                print("[PHONE] Screenshot error:", result.stderr.decode(errors="ignore"))
                return None

            return output_path
        except Exception as error:
            print("[PHONE] Screenshot error:", error)
            return None

    # =========================================================
    # MIRROR
    # =========================================================

    def mirror_phone(self):
        scrcpy = shutil.which("scrcpy")
        if not scrcpy:
            self._speak("Scrcpy is not installed yet, Boss.")
            return False

        if not self.refresh_device():
            self._speak("Your phone is not connected, Boss.")
            return False

        try:
            subprocess.Popen(
                [scrcpy, "--serial", self.device_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._speak("Opening your phone screen, Boss.")
            return True
        except Exception as error:
            print("[PHONE] Mirror error:", error)
            return False

    # =========================================================
    # NAVIGATION
    # =========================================================

    def send_key(self, keycode):
        result = self.adb_command("shell", "input", "keyevent", str(keycode))
        return result is not None

    def home(self):
        return self.send_key(3)

    def back(self):
        return self.send_key(4)

    def recents(self):
        return self.send_key(187)

    def volume_up(self):
        return self.send_key(24)

    def volume_down(self):
        return self.send_key(25)

    def power(self):
        return self.send_key(26)

    # =========================================================
    # OPEN URL / PACKAGE
    # =========================================================

    def open_url(self, url):
        url = str(url or "").strip()
        if not url:
            return False
        result = self.adb_command(
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", url
        )
        return result is not None

    def open_package(self, package_name):
        package_name = str(package_name or "").strip()
        if not package_name:
            return False
        result = self.adb_command("shell", "monkey", "-p", package_name, "1")
        return result is not None

    # =========================================================
    # SETTINGS
    # =========================================================

    def open_phone_settings(self):
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", "ms-settings:mobile-devices"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._speak("Opening phone settings, Boss.")
            return True
        except Exception as error:
            print("[PHONE] Settings error:", error)
            return False

    # =========================================================
    # DISCONNECT / SHUTDOWN
    # =========================================================

    def disconnect(self):
        self.device_id = None

    def shutdown(self):
        self.disconnect()

    def __repr__(self):
        return "<FRIDAY X PhoneManager>"