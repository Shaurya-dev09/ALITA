# =========================================================
# ai_core.py
# FRIDAY X - Pure Line Rings + Voice Reactive (FIXED)
# =========================================================

from __future__ import annotations

import math
import time
import random

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget


class AICoreWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setMinimumSize(480, 480)

        self.r1 = 0.0
        self.r2 = 0.0
        self.r3 = 0.0
        self.r4 = 0.0
        self.r5 = 0.0
        self.phase = 0.0

        self.voice_level = 0.0
        self.target_voice_level = 0.0
        self.glow = 0.45

        self.listening = False
        self.speaking = False
        self.thinking = False
        self.serious_mode = False
        self.battery_percent = 100
        self.current_state = "IDLE"

        self.dots = []
        for i in range(14):
            self.dots.append({
                "angle": i * (360 / 14) + random.uniform(-8, 8),
                "speed": random.uniform(0.35, 1.1),
                "ring": random.choice([0, 1, 2, 3]),
            })

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_state(self, state: str):
        state = str(state or "").upper().strip()
        self.current_state = state
        self.listening = "LISTEN" in state
        self.speaking = "SPEAK" in state
        self.thinking = "THINK" in state or "PROCESS" in state
        if state in ("IDLE", "READY", "STANDBY"):
            self.listening = self.speaking = self.thinking = False

    def set_serious_mode(self, enabled: bool):
        self.serious_mode = bool(enabled)

    def set_listening(self, value: bool):
        self.listening = bool(value)
        if value:
            self.speaking = self.thinking = False
            self.current_state = "LISTENING"

    def set_speaking(self, value: bool):
        self.speaking = bool(value)
        if value:
            self.listening = self.thinking = False
            self.current_state = "SPEAKING"

    def set_thinking(self, value: bool):
        self.thinking = bool(value)
        if value:
            self.listening = self.speaking = False
            self.current_state = "THINKING"

    def set_charging(self, value: bool):
        pass

    def set_battery(self, percent):
        try:
            self.battery_percent = max(0, min(100, int(percent)))
        except Exception:
            self.battery_percent = 100

    def set_voice_level(self, level):
        try:
            self.target_voice_level = max(0.0, min(1.0, float(level)))
        except Exception:
            self.target_voice_level = 0.0

    def set_energy(self, level):
        self.set_voice_level(level)

    def start_listening(self):
        self.set_listening(True)

    def stop_listening(self):
        self.listening = False

    def start_thinking(self):
        self.set_thinking(True)

    def stop_thinking(self):
        self.thinking = False

    def start_speaking(self):
        self.set_speaking(True)

    def stop_speaking(self):
        self.speaking = False
        self.voice_level = 0.0
        self.target_voice_level = 0.0

    def idle(self):
        self.listening = self.thinking = self.speaking = False
        self.current_state = "IDLE"

    def _tick(self):
        if self.speaking:
            self.target_voice_level = 0.35 + abs(math.sin(time.time() * 9.5)) * 0.55
        elif self.listening:
            self.target_voice_level = 0.15 + abs(math.sin(time.time() * 5.5)) * 0.25
        elif self.thinking:
            self.target_voice_level = 0.20 + abs(math.sin(time.time() * 7.0)) * 0.15
        else:
            self.target_voice_level *= 0.92

        self.voice_level += (self.target_voice_level - self.voice_level) * 0.18

        spd = 1.0 + self.voice_level * 0.8

        self.r1 = (self.r1 + 0.32 * spd) % 360
        self.r2 = (self.r2 - 0.48 * spd) % 360
        self.r3 = (self.r3 + 0.70 * spd) % 360
        self.r4 = (self.r4 - 0.95 * spd) % 360
        self.r5 = (self.r5 + 0.40 * spd) % 360
        self.phase = (self.phase + 0.05) % (math.pi * 2)

        for d in self.dots:
            d["angle"] = (d["angle"] + d["speed"] * spd) % 360

        if self.speaking:
            self.glow = min(1.0, self.glow + 0.03)
        elif self.listening:
            self.glow = 0.62 + math.sin(time.time() * 3.0) * 0.12
        elif self.thinking:
            self.glow = 0.68 + math.sin(time.time() * 4.5) * 0.10
        else:
            self.glow = max(0.38, self.glow * 0.990)

        self.update()

    def _col(self):
        if self.serious_mode:
            return {
                "main": QColor(255, 70, 80),
                "dim": QColor(255, 70, 80, 110),
                "bright": QColor(255, 150, 150),
                "label": QColor(255, 110, 110, 220),
            }
        return {
            "main": QColor(0, 210, 255),
            "dim": QColor(0, 180, 255, 120),
            "bright": QColor(130, 240, 255),
            "label": QColor(0, 210, 255, 220),
        }

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), Qt.transparent)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        center = QPointF(cx, cy)
        c = self._col()

        base = min(w, h) * 0.155
        react = self.voice_level * 22.0
        base = base + react * 0.35

        def draw_ring(radius, color, width=1.8):
            pen = QPen(color)
            pen.setWidthF(width)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)          # IMPORTANT
            p.drawEllipse(center, radius, radius)

        def draw_arc(radius, start, span, color, width=2.0):
            pen = QPen(color)
            pen.setWidthF(width)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)          # IMPORTANT
            r = int(radius)
            p.drawArc(int(cx - r), int(cy - r), r * 2, r * 2, int(start * 16), int(span * 16))

        # Outer soft rings
        a = int(35 * self.glow)
        draw_ring(base * 2.05 + react * 0.4, QColor(c["main"].red(), c["main"].green(), c["main"].blue(), a), 1.0)
        draw_ring(base * 1.80 + react * 0.3, QColor(c["main"].red(), c["main"].green(), c["main"].blue(), int(a * 1.5)), 1.2)

        # RING 1
        r1 = base * 1.52 + react * 0.55
        p.save()
        p.translate(center)
        p.rotate(self.r1)
        p.translate(-cx, -cy)
        draw_arc(r1, 8, 75, c["main"], 2.3)
        draw_arc(r1, 115, 65, c["main"], 2.3)
        draw_arc(r1, 225, 55, c["main"], 2.3)
        p.restore()

        # RING 2 + ticks
        r2 = base * 1.26 + react * 0.40
        p.save()
        p.translate(center)
        p.rotate(self.r2)
        draw_ring(r2, c["dim"], 1.5)
        for i in range(0, 360, 18):
            rad = math.radians(i)
            x1 = cx + math.cos(rad) * (r2 - base * 0.07)
            y1 = cy + math.sin(rad) * (r2 - base * 0.07)
            x2 = cx + math.cos(rad) * (r2 + base * 0.08)
            y2 = cy + math.sin(rad) * (r2 + base * 0.08)
            p.setPen(QPen(c["dim"], 1.15))
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        p.restore()

        # RING 3
        r3 = base * 1.02 + react * 0.30
        p.save()
        p.translate(center)
        p.rotate(self.r3)
        draw_ring(r3, c["main"], 1.7)
        p.restore()

        # RING 4
        r4 = base * 0.76 + react * 0.22
        p.save()
        p.translate(center)
        p.rotate(self.r4)
        draw_ring(r4, c["dim"], 1.4)
        draw_arc(r4, 35, 55, c["bright"], 2.0)
        draw_arc(r4, 195, 45, c["bright"], 2.0)
        p.restore()

        # RING 5 (innermost hollow)
        r5 = base * 0.48 + react * 0.15
        p.save()
        p.translate(center)
        p.rotate(self.r5)
        draw_ring(r5, c["main"], 1.8)
        draw_ring(base * 0.30 + react * 0.08, c["dim"], 1.25)
        p.restore()

        # Orbiting dots
        radii = [r1, r2, r3, r4]
        for d in self.dots:
            rad = math.radians(d["angle"])
            rr = radii[d["ring"] % 4]
            x = cx + math.cos(rad) * rr
            y = cy + math.sin(rad) * rr
            size = 2.4 + self.voice_level * 1.8 + math.sin(self.phase + d["angle"] * 0.05) * 0.7
            p.setBrush(c["bright"])
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, y), size, size)

        # CRITICAL FIX: reset brush so next ellipses are NOT filled
        p.setBrush(Qt.NoBrush)

        # Speaking rings
        if self.speaking:
            for i in range(4):
                alpha = max(0, 130 - i * 28)
                pen = QPen(QColor(c["main"].red(), c["main"].green(), c["main"].blue(), alpha))
                pen.setWidthF(1.5)
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                grow = self.voice_level * (10 + i * 6)
                p.drawEllipse(center, r1 + grow + i * 8, r1 + grow + i * 8)

        elif self.listening:
            pulse = math.sin(time.time() * 4.6) * (5 + self.voice_level * 4)
            pen = QPen(c["main"])
            pen.setWidthF(2.2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)          # FIXED
            p.drawEllipse(center, r1 + pulse, r1 + pulse)

        elif self.thinking:
            color = QColor(255, 80, 80, 200) if self.serious_mode else QColor(255, 170, 40, 200)
            pen = QPen(color)
            pen.setWidthF(2.4)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            ang = int((time.time() * 230) % 360)
            rr = r1 + 12
            p.drawArc(int(cx - rr), int(cy - rr), int(rr * 2), int(rr * 2), ang * 16, 90 * 16)

        # Battery
        bx, by = 18, 18
        p.setPen(QPen(QColor(140, 200, 230, 160), 1.4))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(bx, by, 42, 16, 3, 3)
        p.drawRect(bx + 42, by + 4, 3, 8)

        if self.battery_percent > 55:
            color = QColor(0, 220, 130)
        elif self.battery_percent > 25:
            color = QColor(255, 180, 40)
        else:
            color = QColor(255, 60, 60)
        fill = int(36 * self.battery_percent / 100)
        p.fillRect(bx + 2, by + 2, fill, 12, color)

        p.setPen(QColor(190, 220, 255))
        font = QFont("Segoe UI", 8, QFont.Bold)
        p.setFont(font)
        p.drawText(bx + 50, by + 13, f"{self.battery_percent}%")

        # Label
        label = "STANDBY" if self.current_state in ("IDLE", "READY", "") else self.current_state
        p.setPen(c["label"])
        font = QFont("Segoe UI", 10, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2.0)
        p.setFont(font)
        tr = p.fontMetrics().boundingRect(label)
        p.drawText(int(cx - tr.width() / 2), int(cy + base * 2.05 + react * 0.3), label)

        p.end()

    def __repr__(self):
        return f"<FRIDAY X AICoreWidget pure-lines voice={self.voice_level:.2f}>"