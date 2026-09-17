# =========================================================
# image_tool.py - Generate images via Gemini (when available)
# =========================================================

import os
from datetime import datetime

try:
    import config
except Exception:
    config = None


class ImageTool:
    def __init__(self, save_dir=None):
        base = save_dir or os.path.join(os.path.expanduser("~"), "Desktop", "FRIDAY X", "captures")
        self.save_dir = base
        os.makedirs(self.save_dir, exist_ok=True)

    def generate(self, prompt: str):
        prompt = (prompt or "").strip()
        if not prompt:
            return None, "Bolo kya image banani hai."

        # Try google generativeai if project already uses it
        try:
            import google.generativeai as genai
            key = getattr(config, "GEMINI_API_KEY", None) or getattr(config, "API_KEY", None)
            if not key:
                # try list of keys
                keys = getattr(config, "GEMINI_API_KEYS", None) or []
                key = keys[0] if keys else None
            if not key:
                return None, "Gemini API key config mein nahi mili."

            genai.configure(api_key=key)
            # Image models change; try common ones
            model_names = [
                "gemini-2.0-flash-exp-image-generation",
                "gemini-2.0-flash-preview-image-generation",
                "imagen-3.0-generate-002",
            ]
            last_err = None
            for name in model_names:
                try:
                    model = genai.GenerativeModel(name)
                    resp = model.generate_content(prompt)
                    # Best-effort extract
                    path = os.path.join(
                        self.save_dir,
                        f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    )
                    saved = self._save_response_image(resp, path)
                    if saved:
                        return saved, f"Image saved: {saved}"
                except Exception as e:
                    last_err = e
                    continue
            return None, f"Image generate abhi model se fail: {last_err}"
        except Exception as e:
            return None, (
                f"Image tool setup issue: {e}. "
                "Text se describe kar sakti hoon; full image API baad mein tune karenge."
            )

    def _save_response_image(self, resp, path):
        try:
            # Different SDK shapes
            cands = getattr(resp, "candidates", None) or []
            for c in cands:
                content = getattr(c, "content", None)
                parts = getattr(content, "parts", None) or []
                for p in parts:
                    inline = getattr(p, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        data = inline.data
                        if isinstance(data, str):
                            import base64
                            data = base64.b64decode(data)
                        with open(path, "wb") as f:
                            f.write(data)
                        return path
            return None
        except Exception:
            return None