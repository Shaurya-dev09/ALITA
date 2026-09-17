# =========================================================
# memory/store.py
# ALITA — Controlled long-term memory (no secrets)
# =========================================================

from __future__ import annotations

import json
import os
import time
from typing import Any

try:
    import config
    MEMORY_DIR = getattr(config, "MEMORY_DIR", os.path.join("data", "memory"))
    CREATOR_PROFILE = getattr(config, "CREATOR_PROFILE", {"name": "Shaurya"})
    CREATOR_SHORT = getattr(config, "CREATOR_SHORT", "")
    APP_NAME = getattr(config, "APP_NAME", "ALITA")
except Exception:
    MEMORY_DIR = os.path.join("data", "memory")
    CREATOR_PROFILE = {"name": "Shaurya"}
    CREATOR_SHORT = "I was created by Shaurya."
    APP_NAME = "ALITA"

os.makedirs(MEMORY_DIR, exist_ok=True)


class MemoryStore:
    """
    Categories: creator, preferences, projects, context (short), notes
    Never store passwords / API keys here.
    """

    def __init__(self, root: str | None = None):
        self.root = root or MEMORY_DIR
        os.makedirs(self.root, exist_ok=True)
        self._creator_path = os.path.join(self.root, "creator.json")
        self._prefs_path = os.path.join(self.root, "preferences.json")
        self._projects_path = os.path.join(self.root, "projects.json")
        self._context_path = os.path.join(self.root, "context.json")
        self._ensure_defaults()

    def _read(self, path: str, default: Any):
        if not os.path.isfile(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _write(self, path: str, data: Any) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("[MEMORY] write error:", e)
            return False

    def _ensure_defaults(self):
        if not os.path.isfile(self._creator_path):
            self._write(self._creator_path, {
                "name": CREATOR_PROFILE.get("name", "Shaurya"),
                "role": CREATOR_PROFILE.get("role", f"Creator of {APP_NAME}"),
                "notes": CREATOR_PROFILE.get("notes", ""),
                "intro": CREATOR_SHORT or f"I was created by Shaurya. I am {APP_NAME}.",
            })
        if not os.path.isfile(self._prefs_path):
            self._write(self._prefs_path, {
                "language": "hinglish",
                "brief_replies": True,
                "call_user": "Boss",
            })
        if not os.path.isfile(self._projects_path):
            self._write(self._projects_path, {"items": []})
        if not os.path.isfile(self._context_path):
            self._write(self._context_path, {"recent": [], "last_task": None})

    # ----- Creator (identity; do not invent beyond this) -----

    def get_creator(self) -> dict:
        return self._read(self._creator_path, {})

    def creator_intro(self) -> str:
        c = self.get_creator()
        return c.get("intro") or f"I was created by {c.get('name', 'Shaurya')}."

    # ----- Preferences -----

    def get_prefs(self) -> dict:
        return self._read(self._prefs_path, {})

    def set_pref(self, key: str, value: Any) -> bool:
        prefs = self.get_prefs()
        prefs[key] = value
        return self._write(self._prefs_path, prefs)

    # ----- Projects registry -----

    def list_projects(self) -> list:
        data = self._read(self._projects_path, {"items": []})
        return data.get("items", [])

    def add_project(self, name: str, path: str) -> bool:
        data = self._read(self._projects_path, {"items": []})
        items = data.get("items", [])
        items.append({"name": name, "path": path, "ts": time.time()})
        data["items"] = items[-50:]
        return self._write(self._projects_path, data)

    # ----- Short conversation / task context -----

    def push_context(self, role: str, text: str, limit: int = 20) -> None:
        data = self._read(self._context_path, {"recent": [], "last_task": None})
        recent = data.get("recent", [])
        recent.append({"role": role, "text": str(text)[:500], "ts": time.time()})
        data["recent"] = recent[-limit:]
        self._write(self._context_path, data)

    def get_recent_context(self, n: int = 8) -> list:
        data = self._read(self._context_path, {"recent": []})
        return data.get("recent", [])[-n:]

    def set_last_task(self, summary: str) -> None:
        data = self._read(self._context_path, {"recent": [], "last_task": None})
        data["last_task"] = summary
        self._write(self._context_path, data)

    def summary_for_prompt(self) -> str:
        c = self.get_creator()
        p = self.get_prefs()
        lines = [
            f"Assistant name: {APP_NAME}",
            f"Creator: {c.get('name', 'Shaurya')} — use only stored facts; do not invent.",
            f"User address: {p.get('call_user', 'Boss')}",
            f"Prefer language: {p.get('language', 'hinglish')}",
        ]
        recent = self.get_recent_context(6)
        if recent:
            lines.append("Recent context:")
            for r in recent:
                lines.append(f"  - {r.get('role')}: {r.get('text')}")
        return "\n".join(lines)