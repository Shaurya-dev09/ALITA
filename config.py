# =========================================================
# config.py
# ALITA — Personal AI OS
# =========================================================

import os

# ---------- Branding ----------
APP_NAME = "ALITA"
APP_TAGLINE = "PERSONAL AI OS"
APP_FULL_TITLE = f"{APP_NAME}  |  {APP_TAGLINE}"
APP_STATUS_ONLINE = f"{APP_NAME} ONLINE"
APP_STATUS_FOCUS = "FOCUS MODE"
APP_VERSION = "v1.0.0"

# Wake words
WAKE_WORDS = ("alita", "hey alita")

# ---------- Creator identity ----------
CREATOR_NAME = "Shaurya"
CREATOR_SHORT = (
    f"I was created by {CREATOR_NAME}. "
    f"I'm {APP_NAME} — a personal AI assistant built to help with work, code, and daily tasks."
)
CREATOR_PROFILE = {
    "name": "Shaurya",
    "role": f"Creator of {APP_NAME}",
    "notes": "",
}

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
LOG_DIR = os.path.join(DATA_DIR, "logs")
CAPTURE_DIR = os.path.join(BASE_DIR, "captures")

for _p in (DATA_DIR, MEMORY_DIR, LOG_DIR, CAPTURE_DIR):
    os.makedirs(_p, exist_ok=True)

# ---------- AI keys (loaded from .env file — never hardcode here) ----------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEYS = [
    # "backup-key-1",
]

# ---------- Feature flags ----------
FEATURES = {
    "focus_mode": True,
    "tools": True,
    "memory": True,
    "orchestrator": True,
    "image_gen": False,
    "proactive": False,
    "local_llm": False,
}

# ---------- Risk / confirm ----------
CONFIRM_MEDIUM = True
CONFIRM_HIGH_ALWAYS = True

# ---------- Voice ----------
TTS_ONLINE_VOICE = "hi-IN-SwaraNeural"
TTS_OFFLINE_VOICE = "Microsoft Zira Desktop"