# =========================================================
# memory_manager.py
# FRIDAY X - Complete Final Version
# =========================================================

import json
import os
import threading
from datetime import datetime


class MemoryManager:

    def __init__(self, base_dir=None):
        self.base_dir = (
            base_dir
            or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        )

        self.memory_directory = os.path.join(self.base_dir, "memory")
        self.memory_file = os.path.join(self.memory_directory, "memory.json")

        self.lock = threading.RLock()

        self.data = {
            "user": {},
            "preferences": {},
            "contacts": {},
            "facts": [],
            "notes": [],
            "routines": [],
            "conversation_summary": [],
        }

        self._ensure_storage()
        self._load()

    # =========================================================
    # STORAGE
    # =========================================================

    def _ensure_storage(self):
        os.makedirs(self.memory_directory, exist_ok=True)
        if not os.path.exists(self.memory_file):
            self._save()

    def _load(self):
        with self.lock:
            try:
                with open(self.memory_file, "r", encoding="utf-8") as file:
                    loaded = json.load(file)

                if not isinstance(loaded, dict):
                    return

                for key in self.data:
                    if key in loaded:
                        self.data[key] = loaded[key]

            except (OSError, json.JSONDecodeError):
                self._save()

    def _save(self):
        with self.lock:
            temporary_file = self.memory_file + ".tmp"
            try:
                with open(temporary_file, "w", encoding="utf-8") as file:
                    json.dump(self.data, file, indent=4, ensure_ascii=False)
                os.replace(temporary_file, self.memory_file)
            except Exception:
                try:
                    if os.path.exists(temporary_file):
                        os.remove(temporary_file)
                except OSError:
                    pass
                raise

    # =========================================================
    # USER MEMORY
    # =========================================================

    def set_user(self, key, value):
        key = str(key or "").strip()
        if not key:
            return False
        with self.lock:
            self.data["user"][key] = value
            self._save()
        return True

    def get_user(self, key, default=None):
        key = str(key or "").strip()
        with self.lock:
            return self.data["user"].get(key, default)

    def remove_user(self, key):
        key = str(key or "").strip()
        with self.lock:
            if key not in self.data["user"]:
                return False
            del self.data["user"][key]
            self._save()
        return True

    # =========================================================
    # PREFERENCES
    # =========================================================

    def set_preference(self, key, value):
        key = str(key or "").strip()
        if not key:
            return False
        with self.lock:
            self.data["preferences"][key] = value
            self._save()
        return True

    def get_preference(self, key, default=None):
        key = str(key or "").strip()
        with self.lock:
            return self.data["preferences"].get(key, default)

    def remove_preference(self, key):
        key = str(key or "").strip()
        with self.lock:
            if key not in self.data["preferences"]:
                return False
            del self.data["preferences"][key]
            self._save()
        return True

    # =========================================================
    # CONTACTS
    # =========================================================

    def save_contact(self, name, number):
        name = str(name or "").strip().lower()
        number = str(number or "").strip()
        if not name or not number:
            return False
        with self.lock:
            self.data["contacts"][name] = number
            self._save()
        return True

    def get_contact(self, name):
        name = str(name or "").strip().lower()
        with self.lock:
            return self.data["contacts"].get(name)

    def get_contacts(self):
        with self.lock:
            return dict(self.data["contacts"])

    def remove_contact(self, name):
        name = str(name or "").strip().lower()
        with self.lock:
            if name not in self.data["contacts"]:
                return False
            del self.data["contacts"][name]
            self._save()
        return True

    # =========================================================
    # FACTS
    # =========================================================

    def add_fact(self, text):
        text = str(text or "").strip()
        if not text:
            return False
        with self.lock:
            for fact in self.data["facts"]:
                if str(fact).strip().lower() == text.lower():
                    return False
            self.data["facts"].append(text)
            self._save()
        return True

    def get_facts(self):
        with self.lock:
            return list(self.data["facts"])

    def remove_fact(self, text):
        text = str(text or "").strip().lower()
        if not text:
            return False
        with self.lock:
            for index, fact in enumerate(self.data["facts"]):
                if str(fact).strip().lower() == text:
                    self.data["facts"].pop(index)
                    self._save()
                    return True
        return False

    # =========================================================
    # NOTES
    # =========================================================

    def add_note(self, text):
        text = str(text or "").strip()
        if not text:
            return False
        note = {
            "text": text,
            "created_at": datetime.now().isoformat(),
        }
        with self.lock:
            self.data["notes"].append(note)
            self._save()
        return True

    def get_notes(self):
        with self.lock:
            return list(self.data["notes"])

    def remove_note(self, index):
        try:
            index = int(index)
        except (ValueError, TypeError):
            return False
        with self.lock:
            notes = self.data["notes"]
            if index < 0 or index >= len(notes):
                return False
            notes.pop(index)
            self._save()
        return True

    # =========================================================
    # ROUTINES / SCHEDULES
    # =========================================================

    def add_routine(self, text):
        text = str(text or "").strip()
        if not text:
            return False
        routine = {
            "text": text,
            "created_at": datetime.now().isoformat(),
        }
        with self.lock:
            self.data["routines"].append(routine)
            self._save()
        return True

    def get_routines(self):
        with self.lock:
            return list(self.data["routines"])

    # =========================================================
    # SEARCH
    # =========================================================

    def search(self, query):
        query = str(query or "").strip().lower()
        if not query:
            return []

        results = []
        with self.lock:
            for category in ("user", "preferences", "contacts"):
                values = self.data[category]
                for key, value in values.items():
                    searchable = f"{key}: {value}"
                    if query in searchable.lower():
                        results.append({
                            "category": category,
                            "key": key,
                            "value": value,
                        })

            for fact in self.data["facts"]:
                if query in str(fact).lower():
                    results.append({"category": "facts", "value": fact})

            for note in self.data["notes"]:
                if query in str(note).lower():
                    results.append({"category": "notes", "value": note})

            for routine in self.data.get("routines", []):
                if query in str(routine).lower():
                    results.append({"category": "routines", "value": routine})

        return results

    # =========================================================
    # FULL CONTEXT
    # =========================================================

    def get_context(self):
        with self.lock:
            return {
                "user": dict(self.data["user"]),
                "preferences": dict(self.data["preferences"]),
                "contacts": dict(self.data["contacts"]),
                "facts": list(self.data["facts"]),
                "notes": list(self.data["notes"]),
                "routines": list(self.data.get("routines", [])),
            }

    # =========================================================
    # CLEAR
    # =========================================================

    def clear_all(self):
        with self.lock:
            self.data = {
                "user": {},
                "preferences": {},
                "contacts": {},
                "facts": [],
                "notes": [],
                "routines": [],
                "conversation_summary": [],
            }
            self._save()

    # =========================================================
    # SHUTDOWN
    # =========================================================

    def shutdown(self):
        with self.lock:
            self._save()

    def __repr__(self):
        return "<FRIDAY X MemoryManager>"