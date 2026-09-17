# =========================================================
# screen_tool.py - Screenshot + screen reading
# =========================================================

import os
from datetime import datetime

try:
    import mss
    import mss.tools
except Exception:
    mss = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    import pytesseract
except Exception:
    pytesseract = None


class ScreenTool:
    def __init__(self, save_dir=None):
        base = save_dir or os.path.join(os.path.expanduser("~"), "Desktop", "FRIDAY X", "captures")
        self.save_dir = base
        os.makedirs(self.save_dir, exist_ok=True)

    def take_screenshot(self, name=None):
        if mss is None:
            return None, "Screenshot library missing. Run: pip install mss pillow"
        name = name or f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(self.save_dir, name)
        try:
            with mss.mss() as sct:
                mon = sct.monitors[0]
                shot = sct.grab(mon)
                mss.tools.to_png(shot.rgb, shot.size, output=path)
            return path, f"Screenshot saved: {path}"
        except Exception as e:
            return None, f"Screenshot failed: {e}"

    def read_screen_text(self):
        """OCR text from current screen."""
        path, msg = self.take_screenshot()
        if not path:
            return msg
        if pytesseract is None or Image is None:
            return (
                f"Screenshot saved at {path}. "
                "OCR not installed. Run: pip install pytesseract pillow "
                "and install Tesseract-OCR for Windows."
            )
        try:
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            text = (text or "").strip()
            if not text:
                return f"Screenshot saved ({path}) but no text found."
            return f"On screen I can read:\n{text[:2000]}"
        except Exception as e:
            return f"Screenshot at {path}. OCR error: {e}"

    def describe_for_ai(self):
        """Path + OCR snippet for Gemini vision/text."""
        path, msg = self.take_screenshot()
        if not path:
            return {"path": None, "ocr": "", "message": msg}
        ocr = ""
        if pytesseract and Image:
            try:
                ocr = pytesseract.image_to_string(Image.open(path)).strip()
            except Exception:
                pass
        return {"path": path, "ocr": ocr[:3000], "message": msg}