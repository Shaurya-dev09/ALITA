# =========================================================
# assistant_core.py
# ALITA — Entry → Orchestrator
# FIX: full reply for UI; speak goes through cleaned voice_engine.speak
# =========================================================

from __future__ import annotations

try:
    from core.orchestrator import Orchestrator
except Exception as e:
    Orchestrator = None
    print("[ASSISTANT] Orchestrator import failed:", e)


class AssistantCore:
    """
    Thin entry used by VoiceEngine.
    - process() returns FULL text (emoji ok) for response_generated / eyes
    - speak_callback = VoiceEngine.speak (already strips emoji for TTS)
    """

    def __init__(self, command_manager=None, ai_engine=None, speak_callback=None):
        self.command_manager = command_manager
        self.ai_engine = ai_engine
        self.speak_callback = speak_callback

        self.orchestrator = None
        if Orchestrator is not None:
            try:
                self.orchestrator = Orchestrator(
                    ai_engine=ai_engine,
                    speak_callback=speak_callback,
                )
                print("[ASSISTANT] Orchestrator ready.")
            except Exception as e:
                print("[ASSISTANT] Orchestrator init failed:", e)
                self.orchestrator = None

    def _speak(self, text: str):
        if not self.speak_callback or not text:
            return
        try:
            self.speak_callback(str(text))
        except Exception as e:
            print("[ASSISTANT] speak error:", e)

    def process(self, text: str):
        text = str(text or "").strip()
        if not text:
            return ""

        # 1) Orchestrator (preferred)
        if self.orchestrator is not None:
            try:
                result = self.orchestrator.process(text)
                if result is None:
                    return ""
                # If orchestrator already spoke, still return full string for UI
                if isinstance(result, str):
                    return result.strip()
                return str(result)
            except Exception as e:
                print("[ASSISTANT] Orchestrator error:", e)

        # 2) Direct AI fallback
        if self.ai_engine is not None:
            try:
                reply = None
                if hasattr(self.ai_engine, "ask"):
                    reply = self.ai_engine.ask(text)
                elif hasattr(self.ai_engine, "generate"):
                    reply = self.ai_engine.generate(text)
                elif hasattr(self.ai_engine, "chat"):
                    reply = self.ai_engine.chat(text)

                if reply:
                    reply = str(reply).strip()
                    # TTS: cleaned inside VoiceEngine.speak
                    self._speak(reply)
                    # UI / eyes: full reply (emoji included)
                    return reply
            except Exception as e:
                print("[ASSISTANT] AI fallback error:", e)

        msg = "Samajh nahi payi, Boss."
        self._speak(msg)
        return msg

    def shutdown(self):
        try:
            if self.ai_engine and hasattr(self.ai_engine, "shutdown"):
                self.ai_engine.shutdown()
        except Exception:
            pass
        try:
            if self.orchestrator and hasattr(self.orchestrator, "shutdown"):
                self.orchestrator.shutdown()
        except Exception:
            pass

    def __repr__(self):
        return "<ALITA AssistantCore>"