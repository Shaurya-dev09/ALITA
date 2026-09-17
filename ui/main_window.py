# =========================================================
# main_window.py
# ALITA — HUD + Focus + Command + Reply → Eyes/Emoji wiring
# =========================================================

import threading

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from ui.dashboard import Dashboard
from ui.styles import get_stylesheet

try:
    from core.voice_engine import VoiceEngine
except Exception:
    VoiceEngine = None

try:
    import config
except Exception:
    class config:
        APP_NAME = "ALITA"
        APP_FULL_TITLE = "ALITA  |  PERSONAL AI OS"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.voice_engine = None
        self.dashboard = None

        self.setup_window()
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_voice_engine()

    def setup_window(self):
        title = getattr(config, "APP_FULL_TITLE", "ALITA")
        self.setWindowTitle(title)
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(get_stylesheet(False))

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.dashboard = Dashboard()
        self.dashboard.on_mode_changed = self._on_focus_mode_changed

        if hasattr(self.dashboard, "command_input") and self.dashboard.command_input:
            self.dashboard.command_input.returnPressed.connect(self._on_command_enter)

        layout.addWidget(self.dashboard)

    def setup_shortcuts(self):
        sc = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        sc.activated.connect(self._toggle_serious)

    def _toggle_serious(self):
        if self.dashboard:
            self.dashboard.toggle_serious_mode()

    def _on_focus_mode_changed(self, enabled: bool):
        self.setStyleSheet(get_stylesheet(enabled))

        if not self.voice_engine or not hasattr(self.voice_engine, "speak"):
            return

        if enabled:
            msg = "Focus mode on. Distractions down, Boss."
        else:
            msg = "Focus mode off. Back to normal."

        def _speak():
            try:
                self.voice_engine.speak(msg)
            except Exception as error:
                print("[UI] Focus speak error:", error)

        threading.Thread(target=_speak, daemon=True).start()

    def _on_command_enter(self):
        if not self.dashboard or not self.dashboard.command_input:
            return

        text = self.dashboard.command_input.text().strip()
        if not text:
            return

        self.dashboard.command_input.clear()
        print("[UI] Command:", text)

        if not self.voice_engine:
            return

        if hasattr(self.voice_engine, "process_command"):
            def _run():
                try:
                    self.voice_engine.process_command(text)
                except Exception as e:
                    print("[UI] process_command error:", e)
            threading.Thread(target=_run, daemon=True).start()
        elif hasattr(self.voice_engine, "assistant_core"):
            def _run():
                try:
                    self.voice_engine.assistant_core.process(text)
                except Exception as e:
                    print("[UI] assistant process error:", e)
            threading.Thread(target=_run, daemon=True).start()

    def setup_voice_engine(self):
        if VoiceEngine is None:
            print("[UI] VoiceEngine not available.")
            return

        try:
            self.voice_engine = VoiceEngine()

            self.voice_engine.listening_started.connect(self._on_listening)
            self.voice_engine.listening_stopped.connect(self._on_idle)
            self.voice_engine.speaking_started.connect(self._on_speaking)
            self.voice_engine.speaking_finished.connect(self._on_idle)
            self.voice_engine.thinking_started.connect(self._on_thinking)
            self.voice_engine.thinking_finished.connect(self._on_idle)
            self.voice_engine.status_changed.connect(self._on_status)

            if hasattr(self.voice_engine, "command_received"):
                self.voice_engine.command_received.connect(self._on_user_command)
            if hasattr(self.voice_engine, "response_generated"):
                self.voice_engine.response_generated.connect(self._on_alita_response)

            self.voice_engine.start(startup_voice=True)
            print("[UI] VoiceEngine started.")
        except Exception as error:
            print("[UI] VoiceEngine setup error:", error)
            self.voice_engine = None

    def _on_listening(self):
        if self.dashboard:
            self.dashboard.set_status("LISTENING")

    def _on_speaking(self):
        if self.dashboard:
            self.dashboard.set_status("SPEAKING")

    def _on_thinking(self):
        if self.dashboard:
            self.dashboard.set_status("THINKING")
            if hasattr(self.dashboard, "set_expression"):
                self.dashboard.set_expression("think", 6)

    def _on_idle(self):
        if self.dashboard:
            if self.dashboard.is_serious_mode():
                self.dashboard.set_status("FOCUS")
            else:
                self.dashboard.set_status("READY")

    def _on_status(self, text):
        if self.dashboard:
            self.dashboard.set_status(str(text))

    def _on_user_command(self, text):
        print("[UI] User:", text)

    def _on_alita_response(self, text):
        """Reply aate hi eyes + emoji badge update."""
        print("[UI] ALITA:", text)
        if self.dashboard and hasattr(self.dashboard, "on_reply"):
            try:
                self.dashboard.on_reply(str(text or ""))
            except Exception as e:
                print("[UI] on_reply error:", e)

    def closeEvent(self, event):
        try:
            if self.voice_engine:
                self.voice_engine.stop()
        except Exception:
            pass
        try:
            if self.dashboard:
                self.dashboard.shutdown()
        except Exception:
            pass
        event.accept()

    def __repr__(self):
        return "<ALITA MainWindow>"