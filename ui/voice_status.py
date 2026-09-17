# =========================================================
# voice_status.py
# FRIDAY X - Complete Final (Serious Mode Support)
# =========================================================

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)


class VoiceStatusWidget(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("voice_status")
        self.current_state = "READY"
        self.serious_mode = False
        self.animation_index = 0

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(400)

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        self.layout.setSpacing(14)

        self.icon_label = QLabel("◉")
        self.icon_label.setObjectName("voice_icon")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedWidth(30)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.status_label = QLabel("SYSTEM READY")
        self.status_label.setObjectName("voice_text")

        self.hint_label = QLabel('Say "FRIDAY" to activate')
        self.hint_label.setObjectName("voice_hint")

        text_layout.addWidget(self.status_label)
        text_layout.addWidget(self.hint_label)

        self.level_bar = QProgressBar()
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(10)
        self.level_bar.setTextVisible(False)
        self.level_bar.setFixedHeight(6)
        self.level_bar.setMaximumWidth(120)
        self._update_bar_style()

        self.layout.addWidget(self.icon_label)
        self.layout.addLayout(text_layout, 1)
        self.layout.addWidget(self.level_bar)

    def _update_bar_style(self):
        if self.serious_mode:
            chunk = "#ff4d6d"
            border = "#5a1828"
            bg = "#120508"
        else:
            chunk = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b8e6, stop:1 #00e8b0)"
            border = "#0d354c"
            bg = "#041018"

        self.level_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {chunk};
                border-radius: 3px;
            }}
        """)

    def set_serious_mode(self, enabled: bool):
        self.serious_mode = bool(enabled)
        self._update_bar_style()
        self._apply_style(self._current_border())

    def _current_border(self):
        if self.serious_mode:
            return {
                "READY": "#5a1828",
                "LISTENING": "#ff4d6d",
                "THINKING": "#ff8c42",
                "SPEAKING": "#ff6b6b",
                "ERROR": "#ff2244",
            }.get(self.current_state, "#5a1828")
        return {
            "READY": "#0e3d58",
            "LISTENING": "#00d4ff",
            "THINKING": "#8c6bff",
            "SPEAKING": "#00e8b0",
            "ERROR": "#ff4d6d",
        }.get(self.current_state, "#0e3d58")

    def set_text(self, text: str):
        text = str(text or "")
        lower = text.lower()

        if "listen" in lower:
            self.set_listening()
        elif "think" in lower or "process" in lower:
            self.set_thinking()
        elif "speak" in lower:
            self.set_speaking()
        elif "ready" in lower or "idle" in lower or "standby" in lower:
            self.set_ready()
        elif "error" in lower:
            self.set_error(text)
        else:
            self.status_label.setText(text.upper())

    def set_ready(self):
        self.current_state = "READY"
        self.icon_label.setText("◉")
        self.status_label.setText("SYSTEM READY")
        self.hint_label.setText('Say "FRIDAY" to activate')
        self.level_bar.setValue(10)
        self._apply_style(self._current_border())

    def set_idle(self):
        self.set_ready()
        self.current_state = "IDLE"
        self.status_label.setText("STANDBY")
        self.hint_label.setText("Waiting for wake word")

    def set_listening(self):
        self.current_state = "LISTENING"
        self.icon_label.setText("◉")
        self.status_label.setText("LISTENING")
        self.hint_label.setText("I'm listening, Boss...")
        self._apply_style(self._current_border())

    def set_thinking(self):
        self.current_state = "THINKING"
        self.icon_label.setText("◎")
        self.status_label.setText("PROCESSING")
        self.hint_label.setText("Working on your request...")
        self._apply_style(self._current_border())

    def set_speaking(self):
        self.current_state = "SPEAKING"
        self.icon_label.setText("◉")
        self.status_label.setText("SPEAKING")
        self.hint_label.setText("FRIDAY is responding...")
        self._apply_style(self._current_border())

    def set_error(self, message="SYSTEM ERROR"):
        self.current_state = "ERROR"
        self.icon_label.setText("!")
        self.status_label.setText("ERROR")
        self.hint_label.setText(str(message))
        self.level_bar.setValue(0)
        self._apply_style(self._current_border())

    def _apply_style(self, border_color: str):
        bg = "rgba(18, 6, 10, 210)" if self.serious_mode else "rgba(5, 18, 28, 200)"
        self.setStyleSheet(f"""
            QFrame#voice_status {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)

    def _animate(self):
        self.animation_index += 1

        if self.current_state == "LISTENING":
            values = (32, 55, 78, 48, 68, 90, 42)
            self.level_bar.setValue(values[self.animation_index % len(values)])
            dots = "." * ((self.animation_index % 4) + 1)
            self.status_label.setText("LISTENING" + dots)

        elif self.current_state == "THINKING":
            values = (25, 48, 70, 38)
            self.level_bar.setValue(values[self.animation_index % len(values)])
            dots = "." * ((self.animation_index % 4) + 1)
            self.status_label.setText("PROCESSING" + dots)

        elif self.current_state == "SPEAKING":
            values = (48, 82, 60, 95, 55, 78)
            self.level_bar.setValue(values[self.animation_index % len(values)])
            dots = "." * ((self.animation_index % 4) + 1)
            self.status_label.setText("SPEAKING" + dots)

        elif self.current_state in ("READY", "IDLE"):
            self.level_bar.setValue(10)

    def refresh(self):
        self._animate()

    def shutdown(self):
        if self.timer.isActive():
            self.timer.stop()

    def __repr__(self):
        return f"<FRIDAY X VoiceStatusWidget state={self.current_state} serious={self.serious_mode}>"