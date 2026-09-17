# =========================================================
# dashboard.py
# ALITA — Normal (cyan boxes) vs Focus (flat, no boxes)
# + EyeWidget + on_reply + Expr Demo toggle
# =========================================================

import math
import random
import socket
from datetime import datetime

import psutil

from PySide6.QtCore import (
    Qt, QTimer, QPointF, QRect, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QVBoxLayout, QWidget,
    QGraphicsOpacityEffect,
)

try:
    from ui.eye_widget import EyeWidget as CenterCore
except Exception:
    try:
        from ui.ai_core import AICoreWidget as CenterCore
    except Exception:
        CenterCore = None

try:
    import config
except Exception:
    class config:
        APP_NAME = "ALITA"
        APP_TAGLINE = "PERSONAL AI OS"
        APP_FULL_TITLE = "ALITA  |  PERSONAL AI OS"
        APP_STATUS_ONLINE = "ALITA ONLINE"
        APP_STATUS_SERIOUS = "FOCUS MODE"
        APP_VERSION = "v1.0.0"


STYLE_PANEL_NORMAL = """
#hud_panel {
    background: rgba(0, 28, 48, 200);
    border: 1px solid rgba(0, 200, 255, 100);
    border-radius: 10px;
}
"""
STYLE_PANEL_FOCUS = """
#hud_panel {
    background: transparent;
    border: none;
    border-radius: 0px;
}
"""
STYLE_DASH_NORMAL = """
#dashboard {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #020b14, stop:0.5 #041828, stop:1 #020b14);
}
"""
STYLE_DASH_FOCUS = """
#dashboard {
    background: #050003;
}
"""


class HudPanel(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("hud_panel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(6)
        self.title_lbl = None
        if title:
            self.title_lbl = QLabel(title)
            self.title_lbl.setObjectName("hud_title")
            self.layout.addWidget(self.title_lbl)

    def set_focus_chrome(self, focus: bool):
        if self.title_lbl:
            self.title_lbl.setVisible(not focus)
        self.setStyleSheet(STYLE_PANEL_FOCUS if focus else STYLE_PANEL_NORMAL)


class RadarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 140)
        self.angle = 0.0
        self.blips = [
            {
                "a": random.uniform(0, 360),
                "r": random.uniform(0.3, 0.85),
                "s": random.uniform(0.2, 0.6),
            }
            for _ in range(5)
        ]
        self.serious = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)

    def set_serious_mode(self, enabled: bool):
        self.serious = bool(enabled)

    def _tick(self):
        self.angle = (self.angle + (3.5 if self.serious else 2.2)) % 360
        for b in self.blips:
            b["a"] = (b["a"] + b["s"] * (1.4 if self.serious else 1.0)) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) * 0.42
        color = QColor(255, 50, 70) if self.serious else QColor(0, 210, 255)
        p.setBrush(Qt.NoBrush)
        rings = 4 if self.serious else 3
        for i in range(1, rings + 1):
            pen = QPen(QColor(color.red(), color.green(), color.blue(), 40 + i * 30))
            pen.setWidthF(1.0 if self.serious else 1.2)
            p.setPen(pen)
            p.drawEllipse(QPointF(cx, cy), r * i / rings, r * i / rings)
        pen = QPen(QColor(color.red(), color.green(), color.blue(), 200))
        pen.setWidthF(2)
        p.setPen(pen)
        rad = math.radians(self.angle)
        p.drawLine(
            QPointF(cx, cy),
            QPointF(cx + math.cos(rad) * r, cy + math.sin(rad) * r),
        )
        for b in self.blips:
            br = math.radians(b["a"])
            x = cx + math.cos(br) * r * b["r"]
            y = cy + math.sin(br) * r * b["r"]
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            size = 2.5 if self.serious else 3
            p.drawEllipse(QPointF(x, y), size, size)
        p.end()


class DataStreamWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("hud_sub")
        self.setWordWrap(True)
        self.lines = []
        self.serious = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(800)
        self._tick()

    def set_serious_mode(self, enabled: bool):
        self.serious = bool(enabled)
        self.setStyleSheet(
            "color: rgba(255,80,100,180); font-family: Consolas; font-size: 10px;"
            if enabled else
            "color: rgba(0,200,255,160); font-family: Consolas; font-size: 10px;"
        )

    def _tick(self):
        hexline = " ".join(f"{random.randint(0, 0xFFFF):04X}" for _ in range(4))
        self.lines.append(hexline)
        self.lines = self.lines[-5 if self.serious else 6:]
        self.setText("\n".join(self.lines))


class GhostPanel(QFrame):
    def __init__(self, rect: QRect, serious: bool, parent=None):
        super().__init__(parent)
        self.setGeometry(rect)
        if serious:
            self.setStyleSheet(
                "background: rgba(20,0,5,240); border: 1px solid #ff2244; border-radius: 4px;"
            )
        else:
            self.setStyleSheet(
                "background: rgba(0,35,60,220); border: 2px solid #00d4ff; border-radius: 10px;"
            )
        self.show()
        self.raise_()


class Dashboard(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboard")
        self.serious_mode = False
        self.on_mode_changed = None
        self._animating = False
        self._ghosts = []
        self._effects = {}
        self._expr_demo_on = False

        self.ai_core = None
        self.radar = None
        self.clock_label = None
        self.date_label = None
        self.cpu_bar = None
        self.ram_bar = None
        self.net_bar = None
        self.cpu_val = None
        self.ram_val = None
        self.net_val = None
        self.status_label = None
        self.brand_label = None
        self.weather_temp = None
        self.command_input = None
        self.flash_label = None
        self.btn_expr = None
        self._hud_panels = []

        self.setup_ui()
        self._apply_mode_chrome(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.brand_label = QLabel(getattr(config, "APP_FULL_TITLE", "ALITA"))
        self.brand_label.setObjectName("brand_title")
        self.version_label = QLabel(getattr(config, "APP_VERSION", "v1.0.0"))
        self.version_label.setObjectName("brand_sub")
        self.status_label = QLabel("●  ALL SYSTEMS NOMINAL")
        self.status_label.setObjectName("status_ok")
        top.addWidget(self.brand_label)
        top.addWidget(self.version_label)
        top.addStretch()
        top.addWidget(self.status_label)
        root.addLayout(top)

        grid = QGridLayout()
        grid.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(10)

        self.clock_panel = HudPanel()
        self.clock_label = QLabel("--:--")
        self.clock_label.setObjectName("hud_value")
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.date_label = QLabel("")
        self.date_label.setObjectName("hud_sub")
        self.date_label.setAlignment(Qt.AlignCenter)
        self.clock_panel.layout.addWidget(self.clock_label)
        self.clock_panel.layout.addWidget(self.date_label)
        left.addWidget(self.clock_panel)

        self.diag_panel = HudPanel("SYSTEM DIAGNOSTICS")
        self.cpu_val = QLabel("CPU  --%")
        self.cpu_val.setObjectName("hud_sub")
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.ram_val = QLabel("MEMORY  --%")
        self.ram_val.setObjectName("hud_sub")
        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.net_val = QLabel("NETWORK  --%")
        self.net_val.setObjectName("hud_sub")
        self.net_bar = QProgressBar()
        self.net_bar.setRange(0, 100)
        for w in (self.cpu_val, self.cpu_bar, self.ram_val, self.ram_bar, self.net_val, self.net_bar):
            self.diag_panel.layout.addWidget(w)
        left.addWidget(self.diag_panel)

        self.track_panel = HudPanel("GLOBAL TRACKING")
        track_info = QLabel("SAT-LINK  •  ACTIVE NODES")
        track_info.setObjectName("hud_sub")
        self.track_panel.layout.addWidget(track_info)
        self.track_panel.layout.addStretch()
        left.addWidget(self.track_panel, 1)
        grid.addLayout(left, 0, 0)

        center = QVBoxLayout()
        center.setSpacing(10)

        if CenterCore is not None:
            self.ai_core = CenterCore()
        else:
            self.ai_core = QLabel("CORE MISSING")
            self.ai_core.setAlignment(Qt.AlignCenter)
        self.ai_core.setMinimumHeight(300)
        center.addWidget(self.ai_core, 1)

        self.online_panel = HudPanel()
        online_row = QHBoxLayout()
        self.online_label = QLabel("●  " + getattr(config, "APP_STATUS_ONLINE", "ONLINE"))
        self.online_label.setObjectName("status_ok")
        online_row.addWidget(self.online_label)
        online_row.addStretch()
        self.online_panel.layout.addLayout(online_row)
        center.addWidget(self.online_panel)

        self.command_input = QLineEdit()
        self.command_input.setObjectName("command_input")
        self.command_input.setPlaceholderText("Type a command or ask ALITA...")
        center.addWidget(self.command_input)

        self.stream_panel = HudPanel("DATA STREAM")
        self.data_stream = DataStreamWidget()
        self.stream_panel.layout.addWidget(self.data_stream)
        center.addWidget(self.stream_panel)
        grid.addLayout(center, 0, 1)

        right = QVBoxLayout()
        right.setSpacing(10)

        self.weather_panel = HudPanel("WEATHER")
        self.weather_temp = QLabel("--°")
        self.weather_temp.setObjectName("hud_value")
        self.weather_sub = QLabel("Local")
        self.weather_sub.setObjectName("hud_sub")
        self.weather_panel.layout.addWidget(self.weather_temp)
        self.weather_panel.layout.addWidget(self.weather_sub)
        right.addWidget(self.weather_panel)

        self.radar_panel = HudPanel("THREAT RADAR")
        self.radar = RadarWidget()
        self.radar_panel.layout.addWidget(self.radar, 1)
        right.addWidget(self.radar_panel, 1)

        self.quick_panel = HudPanel("QUICK COMMANDS")
        qgrid = QGridLayout()
        for i, name in enumerate(["Status", "Weather", "Expr Demo", "Focus"]):
            btn = QPushButton(name)
            btn.setObjectName("quick_btn")
            btn.setCursor(Qt.PointingHandCursor)
            if name == "Focus":
                btn.clicked.connect(self.toggle_serious_mode)
            elif name == "Expr Demo":
                self.btn_expr = btn
                btn.clicked.connect(self.toggle_expression_demo)
            elif name == "Status":
                btn.clicked.connect(lambda: self.set_ai_state("idle"))
            qgrid.addWidget(btn, i // 2, i % 2)
        self.quick_panel.layout.addLayout(qgrid)
        right.addWidget(self.quick_panel)
        grid.addLayout(right, 0, 2)

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 4)
        grid.setColumnStretch(2, 2)
        root.addLayout(grid, 1)

        bottom = QHBoxLayout()
        self.bottom_status = QLabel("ALITA : READY")
        self.bottom_status.setObjectName("hud_sub")
        bottom.addWidget(self.bottom_status)
        bottom.addStretch()
        try:
            host = socket.gethostname()
        except Exception:
            host = "LOCAL"
        bottom.addWidget(QLabel(host))
        root.addLayout(bottom)

        self.flash_label = QLabel(self)
        self.flash_label.setAlignment(Qt.AlignCenter)
        self.flash_label.hide()

        self._hud_panels = [
            self.clock_panel, self.diag_panel, self.track_panel,
            self.online_panel, self.stream_panel,
            self.weather_panel, self.radar_panel, self.quick_panel,
        ]

        self._anim_widgets = [
            self.clock_panel, self.diag_panel, self.track_panel,
            self.ai_core, self.online_panel, self.command_input,
            self.stream_panel, self.weather_panel, self.radar_panel,
            self.quick_panel,
        ]
        for w in self._anim_widgets:
            eff = QGraphicsOpacityEffect(w)
            eff.setOpacity(1.0)
            w.setGraphicsEffect(eff)
            self._effects[w] = eff

    def _apply_mode_chrome(self, focus: bool):
        self.setStyleSheet(STYLE_DASH_FOCUS if focus else STYLE_DASH_NORMAL)
        for panel in self._hud_panels:
            panel.set_focus_chrome(focus)

        if focus:
            self.command_input.setStyleSheet(
                "QLineEdit { background: transparent; border: none; "
                "border-bottom: 1px solid #ff3355; color: #ffb0b8; "
                "padding: 8px; font-size: 13px; }"
            )
            self.track_panel.setVisible(False)
            self.weather_panel.setVisible(False)
            self.stream_panel.setVisible(False)
        else:
            self.command_input.setStyleSheet("")
            self.track_panel.setVisible(True)
            self.weather_panel.setVisible(True)
            self.stream_panel.setVisible(True)

        if hasattr(self.data_stream, "set_serious_mode"):
            self.data_stream.set_serious_mode(focus)

    def _play_gather_animation(self, engaging: bool):
        if self._animating:
            return
        self._animating = True

        if engaging:
            self.flash_label.setText("FOCUS MODE ENGAGED")
            self.flash_label.setStyleSheet(
                "color:#ff4466;font-size:26px;font-weight:700;letter-spacing:5px;"
                "background:rgba(0,0,0,200);padding:16px;"
            )
        else:
            self.flash_label.setText("NORMAL MODE RESTORED")
            self.flash_label.setStyleSheet(
                "color:#00d4ff;font-size:26px;font-weight:700;letter-spacing:5px;"
                "background:rgba(0,10,20,160);padding:16px;"
            )
        self.flash_label.setGeometry(0, self.height() // 2 - 40, self.width(), 80)
        self.flash_label.show()
        self.flash_label.raise_()

        cx = self.width() // 2
        cy = self.height() // 2
        target = QRect(cx - 28, cy - 22, 56, 44)

        self._ghosts = []
        group_in = QParallelAnimationGroup(self)

        for idx, w in enumerate(self._anim_widgets):
            if not w.isVisible():
                continue
            eff = self._effects.get(w)
            if eff:
                fa = QPropertyAnimation(eff, b"opacity", self)
                fa.setDuration(320)
                fa.setStartValue(1.0)
                fa.setEndValue(0.08)
                fa.setEasingCurve(QEasingCurve.InCubic)
                group_in.addAnimation(fa)

            top_left = w.mapTo(self, w.rect().topLeft())
            rect = QRect(top_left, w.size())
            if rect.width() < 16 or rect.height() < 16:
                continue

            ghost = GhostPanel(rect, engaging, self)
            self._ghosts.append((ghost, rect))

            anim = QPropertyAnimation(ghost, b"geometry", self)
            anim.setDuration(480 + idx * 18)
            anim.setStartValue(rect)
            anim.setEndValue(target)
            anim.setEasingCurve(QEasingCurve.InOutQuint)
            group_in.addAnimation(anim)

        def _at_center():
            QTimer.singleShot(160, _fly_back)

        def _fly_back():
            group_out = QParallelAnimationGroup(self)
            for idx, (ghost, orig) in enumerate(self._ghosts):
                anim = QPropertyAnimation(ghost, b"geometry", self)
                anim.setDuration(500 + idx * 20)
                anim.setStartValue(ghost.geometry())
                anim.setEndValue(orig)
                anim.setEasingCurve(QEasingCurve.OutBack)
                group_out.addAnimation(anim)

            for w in self._anim_widgets:
                eff = self._effects.get(w)
                if eff:
                    fa = QPropertyAnimation(eff, b"opacity", self)
                    fa.setDuration(450)
                    fa.setStartValue(0.08)
                    fa.setEndValue(1.0)
                    fa.setEasingCurve(QEasingCurve.OutCubic)
                    group_out.addAnimation(fa)

            def _done():
                for ghost, _ in self._ghosts:
                    ghost.deleteLater()
                self._ghosts.clear()
                self.flash_label.hide()
                for eff in self._effects.values():
                    eff.setOpacity(1.0)
                self._animating = False
                self._apply_mode_chrome(self.serious_mode)

            group_out.finished.connect(_done)
            group_out.start()

        group_in.finished.connect(_at_center)
        group_in.start()

    def set_serious_mode(self, enabled: bool):
        self.serious_mode = bool(enabled)

        if self.ai_core and hasattr(self.ai_core, "set_serious_mode"):
            self.ai_core.set_serious_mode(self.serious_mode)
        if self.radar and hasattr(self.radar, "set_serious_mode"):
            self.radar.set_serious_mode(self.serious_mode)

        if self.serious_mode:
            self.online_label.setText(
                "●  " + getattr(config, "APP_STATUS_SERIOUS", "FOCUS MODE")
            )
            self.status_label.setText("●  FOCUS MODE ACTIVE")
            self.bottom_status.setText("ALITA : FOCUS")
        else:
            self.online_label.setText(
                "●  " + getattr(config, "APP_STATUS_ONLINE", "ONLINE")
            )
            self.status_label.setText("●  ALL SYSTEMS NOMINAL")
            self.bottom_status.setText("ALITA : READY")

        win = self.window()
        if win is not None:
            try:
                from ui.styles import get_stylesheet
                win.setStyleSheet(get_stylesheet(self.serious_mode))
            except Exception:
                pass

        self._play_gather_animation(engaging=self.serious_mode)

        if callable(self.on_mode_changed):
            try:
                self.on_mode_changed(self.serious_mode)
            except Exception:
                pass

    def toggle_serious_mode(self):
        if self._animating:
            return self.serious_mode
        self.set_serious_mode(not self.serious_mode)
        return self.serious_mode

    def is_serious_mode(self):
        return self.serious_mode

    def get_ai_core(self):
        return self.ai_core

    def set_ai_state(self, state: str):
        if self.ai_core and hasattr(self.ai_core, "set_state"):
            try:
                self.ai_core.set_state(str(state))
            except Exception:
                pass
        state_u = str(state or "").upper()
        if "LISTEN" in state_u:
            self.bottom_status.setText("ALITA : LISTENING")
        elif "SPEAK" in state_u:
            self.bottom_status.setText("ALITA : SPEAKING")
        elif "THINK" in state_u or "PROCESS" in state_u:
            self.bottom_status.setText("ALITA : PROCESSING")
            self.set_expression("think", 5)
        elif "FOCUS" in state_u or self.serious_mode:
            self.bottom_status.setText("ALITA : FOCUS")
        else:
            self.bottom_status.setText("ALITA : READY")

    def set_status(self, text: str):
        self.set_ai_state(text)

    def set_expression(self, exp: str, hold_sec: float = 4.0):
        if self.ai_core and hasattr(self.ai_core, "set_expression"):
            self.ai_core.set_expression(exp, hold_sec)
        e = (exp or "").lower()
        if e == "angry":
            self.status_label.setText("●  ALERT / HOSTILE")
            self.bottom_status.setText("ALITA : ANGRY")
            self.online_label.setText("●  MOOD: ANGRY")
        elif e == "scan":
            self.bottom_status.setText("ALITA : SCANNING")
        elif e == "glitch":
            self.bottom_status.setText("ALITA : GLITCH")
        elif not self.serious_mode and e in ("neutral", "happy", "calm"):
            self.online_label.setText(
                "●  " + getattr(config, "APP_STATUS_ONLINE", "ONLINE")
            )
            self.status_label.setText("●  ALL SYSTEMS NOMINAL")

    def on_reply(self, text: str):
        """Chat reply → emoji badge + eye expression."""
        if self.ai_core and hasattr(self.ai_core, "apply_reply_text"):
            self.ai_core.apply_reply_text(text or "")
        elif self.ai_core and hasattr(self.ai_core, "set_expression"):
            self.ai_core.set_expression("happy", 3)

    def toggle_expression_demo(self):
        if not self.ai_core:
            return
        if hasattr(self.ai_core, "toggle_expression_demo"):
            on = self.ai_core.toggle_expression_demo()
        elif self._expr_demo_on and hasattr(self.ai_core, "stop_expression_demo"):
            self.ai_core.stop_expression_demo()
            on = False
        elif hasattr(self.ai_core, "start_expression_demo"):
            self.ai_core.start_expression_demo()
            on = True
        else:
            return
        self._expr_demo_on = bool(on)
        if self.btn_expr:
            self.btn_expr.setText("Stop Demo" if on else "Expr Demo")
        self.bottom_status.setText(
            "ALITA : EXPR DEMO" if on else "ALITA : READY"
        )

    def refresh(self):
        now = datetime.now()
        self.clock_label.setText(now.strftime("%H:%M"))
        self.date_label.setText(now.strftime("%A, %B %d, %Y").upper())
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.cpu_bar.setValue(int(cpu))
            self.ram_bar.setValue(int(ram))
            self.cpu_val.setText(f"CPU  {int(cpu)}%")
            self.ram_val.setText(f"MEMORY  {int(ram)}%")
            net = min(95, int(cpu * 0.4 + ram * 0.3 + 20))
            self.net_bar.setValue(net)
            self.net_val.setText(f"NETWORK  {net}%")
        except Exception:
            pass
        if self.weather_temp.text() in ("--°", ""):
            self.weather_temp.setText("29°C")
            self.weather_sub.setText("Local • Clear")

    def shutdown(self):
        if self.timer.isActive():
            self.timer.stop()
        if self.radar and hasattr(self.radar, "timer"):
            self.radar.timer.stop()
        if hasattr(self, "data_stream") and hasattr(self.data_stream, "timer"):
            self.data_stream.timer.stop()
        if self.ai_core and hasattr(self.ai_core, "stop_expression_demo"):
            try:
                self.ai_core.stop_expression_demo()
            except Exception:
                pass

    def __repr__(self):
        return f"<ALITA HUD serious={self.serious_mode}>"