# =========================================================
# router.py - Route simple intents to tools
# =========================================================

import re

from tools.screen_tool import ScreenTool
from tools.project_tool import ProjectTool
from tools.image_tool import ImageTool
from tools.system_tool import SystemTool


class ToolsRouter:
    def __init__(self):
        self.screen = ScreenTool()
        self.project = ProjectTool()
        self.image = ImageTool()
        self.system = SystemTool()

    def handle(self, text: str):
        t = (text or "").strip().lower()
        if not t:
            return None

        # Screenshot
        if any(k in t for k in ("screenshot", "स्क्रीनशॉट", "screen shot", "capture screen")):
            _, msg = self.screen.take_screenshot()
            return msg

        # Screen read
        if any(k in t for k in ("screen padho", "read screen", "what's on my screen", "what is on my screen", "screen pe kya")):
            return self.screen.read_screen_text()

        # Project structure
        if any(k in t for k in ("project structure", "project files", "list project", "project dikhao")):
            return self.project.list_structure()

        # Read file: "read file config.py"
        m = re.search(r"(?:read file|file padho|open file)\s+(.+)", t)
        if m:
            return self.project.read_file(m.group(1).strip().strip("\"'"))

        # Image
        m = re.search(r"(?:generate image|image bana|photo bana|draw)\s+(.+)", t)
        if m:
            _, msg = self.image.generate(m.group(1).strip())
            return msg
        if t in ("generate image", "image bana", "photo bana"):
            return "Bolo image mein kya hona chahiye."

        # Open app
        m = re.search(r"(?:open|kholo|launch)\s+(.+)", t)
        if m:
            target = m.group(1).strip()
            if target.startswith("http") or "." in target and " " not in target:
                return self.system.open_url(target)
            return self.system.open_app(target)

        return None  # not handled → AI fallback