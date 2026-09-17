# =========================================================
# system_tool.py - Basic laptop control
# =========================================================

import os
import subprocess
import webbrowser

APP_MAP = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "explorer": "explorer.exe",
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
}


class SystemTool:
    def __init__(self):
        self.user = os.environ.get("USERNAME", "ADMIN")

    def open_app(self, name: str):
        name = (name or "").lower().strip()
        if not name:
            return "Kaunsa app kholna hai?"
        if name in ("browser", "youtube"):
            webbrowser.open("https://www.youtube.com" if name == "youtube" else "https://www.google.com")
            return f"Opened {name}."
        path = APP_MAP.get(name)
        if path:
            path = path.format(user=self.user)
            try:
                if os.path.isfile(path) or path.endswith(".exe") and "\\" not in path:
                    subprocess.Popen(path, shell=True)
                    return f"Opening {name}."
            except Exception as e:
                return f"Open failed: {e}"
        # fallback
        try:
            subprocess.Popen(name, shell=True)
            return f"Tried to open {name}."
        except Exception as e:
            return f"Could not open {name}: {e}"

    def open_path(self, path: str):
        path = os.path.expandvars(path or "")
        if not path:
            return "Path nahi diya."
        try:
            os.startfile(path)
            return f"Opened {path}."
        except Exception as e:
            return f"Failed: {e}"

    def open_url(self, url: str):
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened {url}."