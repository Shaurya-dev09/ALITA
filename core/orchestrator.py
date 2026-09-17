# =========================================================
# orchestrator.py
# ALITA — tools fast-path + AI + memory
# FIX: shorter prompts (faster) | full reply for UI
# =========================================================

from __future__ import annotations

import traceback

from core.memory.store import MemoryStore
from core.permissions import PermissionEngine

try:
    from tools.router import ToolsRouter
except Exception:
    ToolsRouter = None

try:
    import config

    APP_NAME = getattr(config, "APP_NAME", "ALITA")
    CONFIRM_MEDIUM = getattr(config, "CONFIRM_MEDIUM", True)
except Exception:
    APP_NAME = "ALITA"
    CONFIRM_MEDIUM = True


class Orchestrator:
    """
    - Pending confirm first
    - Local tools
    - AI + short memory context
    Returns FULL text (emoji ok). Speak is cleaned in VoiceEngine.
    """

    def __init__(self, ai_engine=None, speak_callback=None):
        self.ai_engine = ai_engine
        self.speak_callback = speak_callback
        self.memory = MemoryStore()
        self.permissions = PermissionEngine(confirm_medium=CONFIRM_MEDIUM)
        self.tools = None
        if ToolsRouter is not None:
            try:
                self.tools = ToolsRouter()
            except Exception as e:
                print("[ORCH] tools failed:", e)

    def _speak(self, text: str):
        if self.speak_callback and text:
            try:
                # VoiceEngine.speak strips emoji/symbols
                self.speak_callback(str(text))
            except Exception:
                pass

    def _identity_reply(self, text: str) -> str | None:
        t = text.lower()
        if any(
            k in t
            for k in (
                "who created you",
                "kisne banaya",
                "your creator",
                "tumhe kisne",
                "kisne design",
            )
        ):
            return self.memory.creator_intro()
        if any(
            k in t
            for k in (
                "who are you",
                "tum kaun",
                "what is your name",
                "tera naam",
                "introduce yourself",
                "apna introduction",
            )
        ):
            return (
                f"Main {APP_NAME} hoon, aapka personal AI assistant. "
                f"{self.memory.creator_intro()}"
            )
        return None

    def process(self, text: str) -> str:
        text = str(text or "").strip()
        if not text:
            return ""

        # 1) Confirmation pending
        if self.permissions.has_pending():
            decision, pending = self.permissions.resolve(text)
            if decision == "yes" and pending:
                msg = f"Confirmed. Continuing: {pending.get('description', '')}"
                self.memory.push_context("user", text)
                self.memory.push_context("alita", msg)
                self._speak(msg)
                return msg
            if decision == "no":
                msg = "Theek hai, cancel kar diya."
                self._speak(msg)
                return msg
            msg = "Please say yes or no."
            self._speak(msg)
            return msg

        # 2) Identity
        ident = self._identity_reply(text)
        if ident:
            self.memory.push_context("user", text)
            self.memory.push_context("alita", ident)
            self._speak(ident)
            return ident

        # 3) Local tools (fast path)
        if self.tools is not None:
            try:
                result = self.tools.handle(text)
                if result:
                    out = str(result).strip()
                    self.memory.push_context("user", text)
                    self.memory.push_context("alita", out[:300])
                    self._speak(out)
                    return out
            except Exception as e:
                print("[ORCH] tool error:", e)
                traceback.print_exc()

        # 4) AI — short context only (speed)
        if self.ai_engine is not None:
            try:
                context = ""
                try:
                    context = (self.memory.summary_for_prompt() or "").strip()
                except Exception:
                    context = ""

                # Keep prompt small — system personality already in AIEngine
                if context:
                    prompt = f"{context}\n\nUser: {text}"
                else:
                    prompt = text

                reply = None
                if hasattr(self.ai_engine, "ask"):
                    reply = self.ai_engine.ask(prompt)
                elif hasattr(self.ai_engine, "generate"):
                    reply = self.ai_engine.generate(prompt)
                elif hasattr(self.ai_engine, "chat"):
                    reply = self.ai_engine.chat(prompt)

                if reply:
                    reply = str(reply).strip()
                    self.memory.push_context("user", text)
                    self.memory.push_context("alita", reply)
                    self._speak(reply)
                    return reply
            except Exception as e:
                print("[ORCH] AI error:", e)
                traceback.print_exc()

        msg = "Samajh nahi payi. Thoda clear boliye, Boss."
        self._speak(msg)
        return msg

    def shutdown(self):
        try:
            if self.tools and hasattr(self.tools, "shutdown"):
                self.tools.shutdown()
        except Exception:
            pass