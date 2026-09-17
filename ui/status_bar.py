# =========================================================
# status_bar.py
# FRIDAY X - Complete Final (Serious Mode Support)
# =========================================================

import socket

import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
)


class StatusBar(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("status_bar")
        self.serious_mode = False

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        self.refresh()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 8, 16, 8)
        self.layout.setSpacing(20)

        self.ai_label = QLabel("FRIDAY : READY")
        self.ai_label.setObjectName("status_online")

        self.cpu_label = QLabel("CPU --%")
        self.cpu_label.setObjectName("status_item")

        self.ram_label = QLabel("RAM --%")
        self.ram_label.setObjectName("status_item")

        self.battery_label = QLabel("BAT --%")
        self.battery_label.setObjectName("status_item")

        self.network_label = QLabel("NET CHECKING")
        self.network_label.setObjectName("status_item")

        try:
            host = socket.gethostname()
        except Exception:
            host = "UNKNOWN"

        self.host_label = QLabel(host)
        self.host_label.setObjectName("status_item")

        self.layout.addWidget(self.ai_label)
        self.layout.addStretch()
        self.layout.addWidget(self.cpu_label)
        self.layout.addWidget(self.ram_label)
        self.layout.addWidget(self.battery_label)
        self.layout.addWidget(self.network_label)
        self.layout.addWidget(self.host_label)

    def set_serious_mode(self, enabled: bool):
        self.serious_mode = bool(enabled)

    def set_ai_state(self, state: str):
        state = str(state or "").upper()

        if "SPEAK" in state:
            text = "FRIDAY : SPEAKING"
        elif "LISTEN" in state:
            text = "FRIDAY : LISTENING"
        elif "THINK" in state or "PROCESS" in state:
            text = "FRIDAY : PROCESSING"
        elif "ERROR" in state:
            text = "FRIDAY : ERROR"
        elif self.serious_mode:
            text = "FRIDAY : SERIOUS"
        else:
            text = "FRIDAY : READY"

        self.ai_label.setText(text)

    def check_network(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            self.network_label.setText("NET ONLINE")
            self.network_label.setObjectName("status_online")
        except OSError:
            self.network_label.setText("NET OFFLINE")
            self.network_label.setObjectName("status_item")

        self._refresh_style(self.network_label)

    def _refresh_style(self, widget):
        style = widget.style()
        if style:
            style.unpolish(widget)
            style.polish(widget)
            widget.update()

    def refresh(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()

            self.cpu_label.setText(f"CPU {round(cpu)}%")
            self.ram_label.setText(f"RAM {round(ram)}%")

            if battery is None:
                self.battery_label.setText("BAT N/A")
            else:
                self.battery_label.setText(f"BAT {round(battery.percent)}%")
        except Exception:
            pass

        self.check_network()

    def shutdown(self):
        if self.timer.isActive():
            self.timer.stop()

    def __repr__(self):
        return f"<FRIDAY X StatusBar serious={self.serious_mode}>"