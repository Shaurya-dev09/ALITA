# =========================================================
# ai_engine.py
# ALITA — Gemini FAST (google.genai + legacy fallback)
# FIX: no slow init pings | short replies | quick model pick
# =========================================================

from __future__ import annotations

import os
import traceback

try:
    import config
except Exception:
    config = None


def _app_name() -> str:
    try:
        return getattr(config, "APP_NAME", "ALITA")
    except Exception:
        return "ALITA"


def _api_keys() -> list:
    keys = []
    try:
        if config is None:
            return keys
        k = (getattr(config, "GEMINI_API_KEY", None) or "").strip()
        if k:
            keys.append(k)
        for item in getattr(config, "GEMINI_API_KEYS", []) or []:
            s = str(item).strip()
            if s and s not in keys:
                keys.append(s)
    except Exception:
        pass
    env = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if env and env not in keys:
        keys.append(env)
    return keys


# Prefer real, fast, available flash models first
MODEL_CANDIDATES = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-flash-latest",
]


class AIEngine:
    def __init__(self):
        self._ready = False
        self._mode = None  # "genai" | "legacy"
        self._client = None
        self._model = None
        self._model_name = None
        self._init_client()

    def _system_preamble(self) -> str:
        name = _app_name()
        return (
            f"You are {name}, a personal AI assistant created by Shaurya.\n"
            "Personality: intelligent, calm, helpful, confident, lightly warm. "
            "Never robotic.\n"
            "Languages: English, Hindi, Hinglish — match the user.\n"
            "Address the user as Boss when natural.\n"
            "SPEED RULES (important):\n"
            "- Keep normal answers SHORT (1–3 sentences) unless user asks for detail.\n"
            "- No long preambles, no repeating the question.\n"
            "- You MAY use 1 emoji at the end for mood if it fits.\n"
            "- Do not invent device actions or facts.\n"
            "If you don't know, say so briefly.\n"
        )

    def _init_client(self):
        keys = _api_keys()
        if not keys:
            print("[AI] No Gemini API key in config / env.")
            return

        # Prefer new package — pick first model WITHOUT live ping (fast startup)
        try:
            from google import genai as google_genai

            for key in keys:
                try:
                    client = google_genai.Client(api_key=key)
                    # Use first candidate; real errors handled in ask()
                    name = MODEL_CANDIDATES[0]
                    preferred = None
                    try:
                        preferred = getattr(config, "GEMINI_MODEL", None)
                    except Exception:
                        preferred = None
                    if preferred and str(preferred).strip():
                        name = str(preferred).strip()

                    self._client = client
                    self._model_name = name
                    self._mode = "genai"
                    self._ready = True
                    print(f"[AI] Ready (google.genai) model={name}")
                    return
                except Exception as e:
                    print("[AI] google.genai client error:", e)
        except ImportError:
            print("[AI] google.genai not installed — pip install google-genai")

        # Legacy fallback
        try:
            import google.generativeai as genai

            for key in keys:
                try:
                    genai.configure(api_key=key)
                    name = MODEL_CANDIDATES[0]
                    try:
                        preferred = getattr(config, "GEMINI_MODEL", None)
                        if preferred and str(preferred).strip():
                            name = str(preferred).strip()
                    except Exception:
                        pass
                    m = genai.GenerativeModel(
                        name,
                        system_instruction=self._system_preamble(),
                    )
                    self._model = m
                    self._model_name = name
                    self._mode = "legacy"
                    self._ready = True
                    print(f"[AI] Ready (legacy) model={name}")
                    return
                except Exception as e:
                    print("[AI] legacy configure error:", e)
        except ImportError:
            print("[AI] google.generativeai not installed")

        print("[AI] Init failed — check key + model names.")

    def _try_next_model(self) -> bool:
        """On 404 / unavailable, rotate model once."""
        if not self._model_name:
            return False
        try:
            idx = MODEL_CANDIDATES.index(self._model_name)
        except ValueError:
            idx = -1
        for name in MODEL_CANDIDATES[idx + 1 :]:
            self._model_name = name
            if self._mode == "legacy":
                try:
                    import google.generativeai as genai

                    self._model = genai.GenerativeModel(
                        name,
                        system_instruction=self._system_preamble(),
                    )
                    print(f"[AI] Switched model → {name}")
                    return True
                except Exception:
                    continue
            else:
                print(f"[AI] Switched model → {name}")
                return True
        return False

    def ask(self, prompt: str) -> str:
        prompt = str(prompt or "").strip()
        if not prompt:
            return ""

        if not self._ready:
            self._init_client()
        if not self._ready:
            return (
                "AI service right now respond nahi kar paa rahi. "
                "API key / model check karo, Boss."
            )

        try:
            if self._mode == "genai" and self._client is not None:
                # Fast generation config
                try:
                    from google.genai import types

                    cfg = types.GenerateContentConfig(
                        system_instruction=self._system_preamble(),
                        max_output_tokens=256,
                        temperature=0.7,
                    )
                    r = self._client.models.generate_content(
                        model=self._model_name,
                        contents=prompt,
                        config=cfg,
                    )
                except Exception:
                    # older client without config types
                    full = self._system_preamble() + "\n\nUser: " + prompt
                    r = self._client.models.generate_content(
                        model=self._model_name,
                        contents=full,
                    )
                text = getattr(r, "text", None)
                if text:
                    return str(text).strip()
                return "Kuch clear jawab nahi mila, Boss."

            if self._mode == "legacy" and self._model is not None:
                try:
                    import google.generativeai as genai

                    resp = self._model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=256,
                            temperature=0.7,
                        ),
                    )
                except Exception:
                    resp = self._model.generate_content(prompt)
                text = getattr(resp, "text", None)
                if text:
                    return str(text).strip()
                return "Kuch clear jawab nahi mila, Boss."

        except Exception as e:
            print("[AI] generate error:", e)
            traceback.print_exc()
            msg = str(e)
            if (
                "404" in msg
                or "NOT_FOUND" in msg
                or "no longer available" in msg
                or "not found" in msg.lower()
            ):
                if self._try_next_model():
                    try:
                        return self.ask(prompt)
                    except Exception:
                        pass
            if "401" in msg or "UNAUTHENTICATED" in msg:
                return (
                    "API key invalid / unauthorized hai, Boss. "
                    "Config mein naya Gemini key daalo."
                )
            return "AI service mein problem hai. Thodi der baad try karo, Boss."

        return "AI service mein problem hai. Thodi der baad try karo, Boss."

    def generate(self, prompt: str) -> str:
        return self.ask(prompt)

    def chat(self, prompt: str) -> str:
        return self.ask(prompt)

    def shutdown(self):
        self._ready = False
        self._client = None
        self._model = None

    def __repr__(self):
        return f"<ALITA AIEngine mode={self._mode} model={self._model_name}>"