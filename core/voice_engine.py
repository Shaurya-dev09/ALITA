# =========================================================
# voice_engine.py
# ALITA — JARVIS-style session + barge-in + clean TTS
# Best practical: continuous talk, interrupt, no emoji speech
# =========================================================

import io
import os
import re
import subprocess
import threading
import time
import unicodedata

import numpy as np
import speech_recognition as sr

from PySide6.QtCore import QObject, Signal

from core.ai_engine import AIEngine
from core.assistant_core import AssistantCore
from core.command_manager import CommandManager

try:
    import config
except Exception:
    config = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOKORO_ONNX = os.path.join(ROOT, "kokoro-v1.0.onnx")
KOKORO_VOICES = os.path.join(ROOT, "voices-v1.0.bin")

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U00002300-\U000023FF"
    "\U0001F1E0-\U0001F1FF"
    "\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)
_MARKDOWN_RE = re.compile(r"[*_`#~\[\]()<>|\\]{1,}")
_MULTI_SPACE = re.compile(r"\s+")

# Stop / interrupt phrases (Hindi + English)
_STOP_WORDS = (
    "stop", "ruk", "rukja", "ruk ja", "chup", "bas", "cancel",
    "quiet", "enough", "shut up", "band kar", "chup ho",
)


def _app_name():
    try:
        return getattr(config, "APP_NAME", "ALITA")
    except Exception:
        return "ALITA"


def _wake_words():
    try:
        return tuple(getattr(config, "WAKE_WORDS", ("alita", "hey alita")))
    except Exception:
        return ("alita", "hey alita")


def clean_for_speech(text: str) -> str:
    if not text:
        return ""
    t = _EMOJI_RE.sub(" ", str(text))
    t = _MARKDOWN_RE.sub(" ", t)
    out = []
    for ch in t:
        cat = unicodedata.category(ch)
        if cat.startswith("S") and ch not in "%.,!?-'\":;":
            continue
        if cat in ("Cf", "Mn"):
            continue
        out.append(ch)
    return _MULTI_SPACE.sub(" ", "".join(out)).strip()


class VoiceEngine(QObject):

    listening_started = Signal()
    listening_stopped = Signal()
    speaking_started = Signal()
    speaking_finished = Signal()
    thinking_started = Signal()
    thinking_finished = Signal()
    wake_word_detected = Signal()
    command_received = Signal(str)
    response_generated = Signal(str)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = False
        self.thread = None
        self.wake_words = _wake_words()

        # End-of-speech: balanced for Hinglish
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.55
        self.recognizer.phrase_threshold = 0.2
        self.recognizer.non_speaking_duration = 0.25

        try:
            self.microphone = sr.Microphone()
        except Exception as error:
            print("[VOICE] Microphone error:", error)
            self.microphone = None

        self.microphone_ready = False
        self._mixer_ready = False
        self._mixer_sr = None
        self._speak_lock = threading.Lock()
        self._speaking = False
        self._listening = False
        self._thinking = False
        self._interrupt_flag = False

        self._kokoro = None
        self.kokoro_voice = "hf_alpha"
        self.kokoro_speed = 1.2
        self._init_kokoro()

        self.command_manager = CommandManager(self.speak)
        self.ai_engine = AIEngine()
        self.assistant_core = AssistantCore(
            command_manager=self.command_manager,
            ai_engine=self.ai_engine,
            speak_callback=self.speak,
        )

        # JARVIS session: long continuous window after wake
        self.conversation_mode = False
        self.conversation_timeout = 40
        self.last_interaction = 0
        self.last_command = ""

        print("[VOICE] JARVIS-session + barge-in | Kokoro/Zira | clean speech")
        self.status_changed.emit("READY")

    def _init_kokoro(self):
        try:
            if not os.path.isfile(KOKORO_ONNX) or not os.path.isfile(KOKORO_VOICES):
                print("[VOICE] Kokoro files missing at", ROOT)
                return
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro(KOKORO_ONNX, KOKORO_VOICES)
            try:
                self._kokoro.create("ok", voice=self.kokoro_voice, speed=self.kokoro_speed)
                print("[VOICE] Kokoro loaded + warmed.")
            except Exception:
                print("[VOICE] Kokoro loaded.")
        except Exception as e:
            print("[VOICE] Kokoro init failed:", e)
            self._kokoro = None

    # ---------- interrupt / barge-in ----------
    def interrupt_speech(self):
        """Stop TTS immediately (user spoke / stop word)."""
        self._interrupt_flag = True
        try:
            import pygame
            if self._mixer_ready:
                pygame.mixer.music.stop()
        except Exception:
            pass

    def speak(self, text):
        raw = str(text or "").strip()
        if not raw:
            return False

        text = clean_for_speech(raw)
        if not text:
            return False

        if len(text) > 220:
            text = text[:217].rsplit(" ", 1)[0] + "..."

        def _run():
            with self._speak_lock:
                self._interrupt_flag = False
                self._speaking = True
                try:
                    self.speaking_started.emit()
                    self.status_changed.emit("SPEAKING")
                except Exception:
                    pass
                try:
                    ok = False
                    if self._kokoro is not None:
                        print("[VOICE] Using Kokoro")
                        ok = self._speak_kokoro(text)
                    if not ok and not self._interrupt_flag:
                        print("[VOICE] Using Zira fallback")
                        self._speak_zira(text)
                except Exception as e:
                    print("[VOICE] Speak error:", e)
                finally:
                    self._speaking = False
                    try:
                        self.speaking_finished.emit()
                        if self.running:
                            self.status_changed.emit("IDLE")
                    except Exception:
                        pass

        threading.Thread(target=_run, daemon=True, name="ALITA-Speak").start()
        return True

    def _speak_kokoro(self, text: str) -> bool:
        try:
            import soundfile as sf
            import pygame

            t0 = time.time()
            samples, sample_rate = self._kokoro.create(
                text, voice=self.kokoro_voice, speed=self.kokoro_speed
            )
            samples = np.asarray(samples, dtype=np.float32)
            gen_ms = int((time.time() - t0) * 1000)

            if self._interrupt_flag:
                return True

            buf = io.BytesIO()
            sf.write(buf, samples, int(sample_rate), format="WAV")
            buf.seek(0)

            if not self._mixer_ready or self._mixer_sr != int(sample_rate):
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
                pygame.mixer.init(
                    frequency=int(sample_rate), size=-16, channels=1, buffer=256
                )
                self._mixer_ready = True
                self._mixer_sr = int(sample_rate)

            pygame.mixer.music.load(buf)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if not self.running or self._interrupt_flag:
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.02)

            print(f"[VOICE] Kokoro gen={gen_ms}ms chars={len(text)}")
            return True
        except Exception as e:
            print("[VOICE] Kokoro speak error:", e)
            return False

    def _speak_zira(self, text: str) -> bool:
        try:
            if self._interrupt_flag:
                return True
            safe = text.replace("'", "''")
            ps = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Rate = 2; $s.Volume = 100; "
                "try { $s.SelectVoice('Microsoft Zira Desktop') } catch {}; "
                f"$s.Speak('{safe}')"
            )
            flags = (
                subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True,
                timeout=45,
                creationflags=flags,
            )
            return r.returncode == 0
        except Exception as e:
            print("[VOICE] Zira error:", e)
            return False

    def test_voice(self):
        self.speak(f"{_app_name()} online, Boss.")

    def initialize_microphone(self):
        if self.microphone_ready:
            return True
        if self.microphone is None:
            return False
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
            self.microphone_ready = True
            print("[VOICE] Mic ready. energy=", int(self.recognizer.energy_threshold))
            return True
        except Exception as error:
            print("[VOICE] Mic calibration error:", error)
            return False

    def listen_once(self, timeout=2.2, phrase_time_limit=6):
        if not self.microphone_ready:
            if not self.initialize_microphone():
                return None

        self._listening = True
        try:
            self.listening_started.emit()
            self.status_changed.emit("LISTENING")
        except Exception:
            pass

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            for lang in ("en-IN", "hi-IN"):
                try:
                    text = self.recognizer.recognize_google(audio, language=lang)
                    if text:
                        return text.strip().lower()
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print("[VOICE] STT error:", e)
                    return None
            return None
        except sr.WaitTimeoutError:
            return None
        except Exception as error:
            print("[VOICE] Listen error:", error)
            return None
        finally:
            self._listening = False
            try:
                self.listening_stopped.emit()
                if self.running and not self._speaking:
                    self.status_changed.emit("IDLE")
            except Exception:
                pass

    def _is_stop(self, text: str) -> bool:
        t = (text or "").lower().strip()
        if not t:
            return False
        for w in _STOP_WORDS:
            if w in t:
                return True
        return False

    def _extract_command(self, text):
        clean = str(text or "").strip().lower()
        if not clean:
            return None
        for wake in self.wake_words:
            if wake in clean:
                return clean.split(wake, 1)[1].strip()
        return None

    def _has_wake(self, text: str) -> bool:
        clean = (text or "").lower()
        return any(w in clean for w in self.wake_words)

    def process_command(self, text):
        text = str(text or "").strip()
        if not text:
            return False

        # Interrupt / stop while (or after) speaking
        if self._is_stop(text):
            self.interrupt_speech()
            self.conversation_mode = True
            self.last_interaction = time.time()
            self.speak("Theek hai, Boss.")
            return True

        # If speaking and user said wake name → barge-in
        if self._speaking and self._has_wake(text):
            self.interrupt_speech()
            time.sleep(0.15)
            cmd = self._extract_command(text)
            if cmd:
                text = cmd
            else:
                self.conversation_mode = True
                self.last_interaction = time.time()
                return True

        self.last_command = text
        try:
            self.command_received.emit(text)
        except Exception:
            pass

        self._thinking = True
        try:
            self.thinking_started.emit()
            self.status_changed.emit("THINKING")
        except Exception:
            pass

        try:
            result = self.assistant_core.process(text)
            if isinstance(result, str) and result.strip():
                try:
                    self.response_generated.emit(result.strip())
                except Exception:
                    pass
            return result
        except Exception as error:
            print("[VOICE] Process error:", error)
            msg = "Sorry Boss."
            try:
                self.response_generated.emit(msg)
            except Exception:
                pass
            self.speak(msg)
            return False
        finally:
            self._thinking = False
            try:
                self.thinking_finished.emit()
            except Exception:
                pass
            self.last_interaction = time.time()
            self.conversation_mode = True

    def _run(self):
        try:
            self.status_changed.emit("IDLE")
        except Exception:
            pass

        while self.running:
            try:
                # While speaking: still listen for barge-in (short)
                if self._speaking:
                    heard = self.listen_once(timeout=0.4, phrase_time_limit=2)
                    if heard:
                        if self._is_stop(heard) or self._has_wake(heard):
                            self.interrupt_speech()
                            time.sleep(0.1)
                            if self._is_stop(heard):
                                self.conversation_mode = True
                                self.last_interaction = time.time()
                                self.speak("Theek hai, Boss.")
                            else:
                                cmd = self._extract_command(heard)
                                if cmd:
                                    self.process_command(cmd)
                                else:
                                    self.conversation_mode = True
                                    self.last_interaction = time.time()
                    else:
                        time.sleep(0.05)
                    continue

                # Continuous session — no wake word needed
                if self.conversation_mode:
                    if time.time() - self.last_interaction > self.conversation_timeout:
                        self.conversation_mode = False
                        print("[VOICE] Session timeout — say wake word again")
                        continue

                    cmd = self.listen_once(timeout=2.0, phrase_time_limit=6)
                    if not cmd:
                        continue

                    # Optional: saying wake again still works
                    if self._has_wake(cmd):
                        try:
                            self.wake_word_detected.emit()
                        except Exception:
                            pass
                        inner = self._extract_command(cmd)
                        if inner:
                            self.process_command(inner)
                        else:
                            self.speak("Haan Boss.")
                            self.last_interaction = time.time()
                        continue

                    self.process_command(cmd)
                    continue

                # Idle: need wake word
                heard = self.listen_once(timeout=1.8, phrase_time_limit=5)
                if not heard:
                    continue

                if not self._has_wake(heard):
                    continue

                try:
                    self.wake_word_detected.emit()
                except Exception:
                    pass

                command = self._extract_command(heard)
                if command:
                    self.process_command(command)
                else:
                    self.speak("Haan Boss.")
                    self.conversation_mode = True
                    self.last_interaction = time.time()

            except Exception as error:
                print("[VOICE] Loop error:", error)
                time.sleep(0.1)

    def start(self, startup_voice=True):
        if self.running:
            return
        self.running = True
        self.initialize_microphone()
        self.thread = threading.Thread(
            target=self._run, daemon=True, name="ALITA-VoiceEngine"
        )
        self.thread.start()
        print("[VOICE] Engine started (JARVIS session).")
        if startup_voice:
            def _boot():
                time.sleep(0.5)
                self.test_voice()
            threading.Thread(target=_boot, daemon=True, name="ALITA-Startup").start()

    def stop(self):
        self.running = False
        self.conversation_mode = False
        self.interrupt_speech()
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
        try:
            self.assistant_core.shutdown()
        except Exception:
            pass

    @property
    def is_speaking(self):
        return self._speaking

    @property
    def is_listening(self):
        return self._listening

    @property
    def is_thinking(self):
        return self._thinking

    def __repr__(self):
        return "<ALITA VoiceEngine JARVIS-session>"