# =========================================================
# info_panel.py
# FRIDAY X - Complete Final (Serious Mode Support)
# =========================================================

import os
import shutil
import socket
from datetime import datetime

import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class MetricCard(QFrame):

    def __init__(self, name: str, value: str = "--", parent=None):
        super().__init__(parent)
        self.setObjectName("metric_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 11, 12, 11)
        layout.setSpacing(3)

        self.value_label = QLabel(str(value))
        self.value_label.setObjectName("metric_value")

        self.name_label = QLabel(str(name))
        self.name_label.setObjectName("metric_name")

        layout.addWidget(self.value_label)
        layout.addWidget(self.name_label)

    def set_value(self, value):
        self.value_label.setText(str(value))


class InfoPanel(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("info_panel")
        self.serious_mode = False

        self.setup_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

        self.refresh()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)

        header = QHBoxLayout()

        self.title_label = QLabel("SYSTEM STATUS")
        self.title_label.setObjectName("info_title")

        self.online_label = QLabel("● ONLINE")
        self.online_label.setObjectName("status_online")

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.online_label)

        self.layout.addLayout(header)

        self.computer_frame = QFrame()
        self.computer_frame.setObjectName("metric_card")

        computer_layout = QVBoxLayout(self.computer_frame)
        computer_layout.setContentsMargins(12, 11, 12, 11)
        computer_layout.setSpacing(3)

        self.computer_name = QLabel("COMPUTER")
        self.computer_name.setObjectName("metric_name")

        self.computer_value = QLabel("--")
        self.computer_value.setObjectName("metric_value")

        computer_layout.addWidget(self.computer_name)
        computer_layout.addWidget(self.computer_value)

        self.layout.addWidget(self.computer_frame)

        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(8)

        self.cpu_card = MetricCard("CPU", "--%")
        self.ram_card = MetricCard("RAM", "--%")
        self.battery_card = MetricCard("BATTERY", "--%")
        self.disk_card = MetricCard("DISK", "--%")

        self.metrics_grid.addWidget(self.cpu_card, 0, 0)
        self.metrics_grid.addWidget(self.ram_card, 0, 1)
        self.metrics_grid.addWidget(self.battery_card, 1, 0)
        self.metrics_grid.addWidget(self.disk_card, 1, 1)

        self.layout.addLayout(self.metrics_grid)

        self.storage_card = QFrame()
        self.storage_card.setObjectName("metric_card")

        storage_layout = QVBoxLayout(self.storage_card)
        storage_layout.setContentsMargins(12, 10, 12, 10)
        storage_layout.setSpacing(3)

        storage_title = QLabel("STORAGE")
        storage_title.setObjectName("metric_name")

        self.storage_value = QLabel("--")
        self.storage_value.setObjectName("info_value")

        storage_layout.addWidget(storage_title)
        storage_layout.addWidget(self.storage_value)

        self.layout.addWidget(self.storage_card)

        self.network_card = QFrame()
        self.network_card.setObjectName("metric_card")

        network_layout = QVBoxLayout(self.network_card)
        network_layout.setContentsMargins(12, 10, 12, 10)
        network_layout.setSpacing(3)

        network_title = QLabel("NETWORK")
        network_title.setObjectName("metric_name")

        self.network_value = QLabel("Checking...")
        self.network_value.setObjectName("info_value")

        network_layout.addWidget(network_title)
        network_layout.addWidget(self.network_value)

        self.layout.addWidget(self.network_card)

        self.time_card = QFrame()
        self.time_card.setObjectName("metric_card")

        time_layout = QVBoxLayout(self.time_card)
        time_layout.setContentsMargins(12, 10, 12, 10)
        time_layout.setSpacing(3)

        time_title = QLabel("LOCAL TIME")
        time_title.setObjectName("metric_name")

        self.time_value = QLabel("--:--:--")
        self.time_value.setObjectName("metric_value")

        time_layout.addWidget(time_title)
        time_layout.addWidget(self.time_value)

        self.layout.addWidget(self.time_card)
        self.layout.addStretch()

    def set_serious_mode(self, enabled: bool):
        self.serious_mode = bool(enabled)

    def refresh_cpu(self):
        try:
            value = psutil.cpu_percent(interval=None)
            self.cpu_card.set_value(f"{round(value)}%")
        except Exception:
            self.cpu_card.set_value("N/A")

    def refresh_ram(self):
        try:
            value = psutil.virtual_memory().percent
            self.ram_card.set_value(f"{round(value)}%")
        except Exception:
            self.ram_card.set_value("N/A")

    def refresh_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                self.battery_card.set_value("N/A")
                return
            self.battery_card.set_value(f"{round(battery.percent)}%")
        except Exception:
            self.battery_card.set_value("N/A")

    def refresh_disk(self):
        try:
            drive = os.path.abspath(os.sep)
            usage = shutil.disk_usage(drive)
            used_percent = usage.used / usage.total * 100
            used_gb = usage.used / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            self.disk_card.set_value(f"{round(used_percent)}%")
            self.storage_value.setText(
                f"{used_gb:.0f} GB used  •  {total_gb:.0f} GB total  •  {free_gb:.0f} GB free"
            )
        except Exception:
            self.disk_card.set_value("N/A")
            self.storage_value.setText("Unavailable")

    def refresh_network(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1)
            self.network_value.setText("ONLINE  •  Internet connected")
            self.online_label.setText("● ONLINE")
        except OSError:
            self.network_value.setText("OFFLINE  •  No internet")
            self.online_label.setText("● OFFLINE")

    def refresh_computer(self):
        try:
            self.computer_value.setText(socket.gethostname())
        except Exception:
            self.computer_value.setText("Unknown")

    def refresh_time(self):
        try:
            now = datetime.now()
            self.time_value.setText(now.strftime("%I:%M:%S %p"))
        except Exception:
            self.time_value.setText("--:--:--")

    def refresh(self):
        self.refresh_cpu()
        self.refresh_ram()
        self.refresh_battery()
        self.refresh_disk()
        self.refresh_network()
        self.refresh_computer()
        self.refresh_time()

    def set_computer(self, value):
        self.computer_value.setText(str(value))

    def set_internet_status(self, value):
        self.network_value.setText(str(value))

    def set_storage(self, value):
        self.storage_value.setText(str(value))

    def shutdown(self):
        if self.timer.isActive():
            self.timer.stop()

    def __repr__(self):
        return f"<FRIDAY X InfoPanel serious={self.serious_mode}>"