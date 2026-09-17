# =========================================================
# eye_widget.py  FINAL
# Multi-emoji row under eyes (no cut) + matching expression
# =========================================================

from __future__ import annotations

import math
import re
import time
import unicodedata

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient, QPainterPath, QFont
from PySide6.QtWidgets import QWidget

EXPRESSIONS = [
    "neutral", "happy", "cool", "think", "wink", "surprise",
    "skeptical", "calm", "sad", "scan", "sassy", "glitch", "angry",
]

EMOJI_TO_EXPR: dict[str, str] = {}
for em, exp in [
    ("😀😃😄😁😆😅🤣😂🙂🙃😊😇🥰😍🤩😘😗☺️😚😙 Cul🥲😋😛", "happy"),
    ("😜🤪😝🤑🤗🤭👌👍👏🎉🎊❤️❤💕💖💗💙💚💛🧡💜🤍🤎💯✨⭐🌟", "happy"),
    ("😎🤓🥸🔥💪🙌", "cool"),
    ("🤔🧐😕😟🙁☹️☹💭💡🧠", "think"),
    ("😉😜😋😈😏", "wink"),
    ("😮😲😳😯😨🤯😱‼️❗❕❓❔", "surprise"),
    ("🤨😒🙄😑😐😶😏😕", "skeptical"),
    ("😌☺️😇😴💤🧘☮️", "calm"),
    ("😢😭😞😔😟😥😰😓💔😿🥺", "sad"),
    ("🔎🔍📡🛰️👀👁️👁", "scan"),
    ("😏💅👑😼", "sassy"),
    ("⚡💥⚠️⚠❌🚫🐛🤖💀☠️", "glitch"),
    ("😠😡🤬💢👿👊😤", "angry"),
]:
    for ch in em:
        if ch.strip():
            EMOJI_TO_EXPR[ch] = exp

EXPR_FALLBACK_EMOJI = {
    "neutral": "",
    "happy": "😊",
    "cool": "😎",
    "think": "🤔",
    "wink": "😉",
    "surprise": "😮",
    "skeptical": "🤨",
    "calm": "😌",
    "sad": "😢",
    "scan": "🔎",
    "sassy": "😏",
    "glitch": "⚡",
    "angry": "😠",
}

# Priority when multiple moods in one reply (higher = wins for eyes)
EXPR_PRIORITY = {
    "angry": 10,
    "glitch": 9,
    "surprise": 8,
    "sad": 7,
    "think": 6,
    "wink": 5,
    "sassy": 4,
    "cool": 3,
    "scan": 3,
    "happy": 2,
    "calm": 1,
    "skeptical": 1,
    "neutral": 0,
}

_EMOJI_RE = re.compile(
    "(?:"
    "[\U0001F1E0-\U0001F1FF]{2}"
    "|[\U0001F300-\U0001F9FF]"
    "|[\U0001FA00-\U0001FAFF]"
    "|[\U00002700-\U000027BF]"
    "|[\U00002600-\U000026FF]"
    "|[\U00002300-\U000023FF]"
    "|[\U0000FE00-\U0000FE0F]"
    "|\U0000200D"
    ")+",
    flags=re.UNICODE,
)

MAX_BADGE_EMOJIS = 5


def extract_emojis(text: str) -> list[str]:
    if not text:
        return []
    found = _EMOJI_RE.findall(text)
    out = []
    for e in found:
        e = e.strip()
        if not e:
            continue
        if all(unicodedata.category(c) in ("Mn", "Cf") for c in e):
            continue
        if e not in out:
            out.append(e)
    return out


def map_emoji_to_expr(emoji: str) -> str | None:
    if not emoji:
        return None
    if emoji in EMOJI_TO_EXPR:
        return EMOJI_TO_EXPR[emoji]
    for ch in emoji:
        if ch in EMOJI_TO_EXPR:
            return EMOJI_TO_EXPR[ch]
    cleaned = emoji.replace("\ufe0f", "").replace("\u200d", "")
    for ch in cleaned:
        if ch in EMOJI_TO_EXPR:
            return EMOJI_TO_EXPR[ch]
    return None


class EyeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)

        self.serious = False
        self.state = "idle"
        self.expression = "neutral"

        self._mode = 0.0
        self._mode_target = 0.0
        self._t = 0.0
        self._blink = 1.0
        self._blink_target = 1.0
        self._next_blink = time.time() + 2.5
        self._wink_side = None
        self._wink_until = 0.0
        self._pulse = 0.0
        self._look_x = self._look_y = 0.0
        self._look_tx = self._look_ty = 0.0
        self._ring = 0.0
        self._flash = 0.0
        self._expr_until = 0.0
        self._emoji_alpha = 0.0
        self._emoji_scale = 1.0

        # multi-emoji list (not single string)
        self._chat_emojis: list[str] = []
        self._chat_emoji_until = 0.0

        self._demo = False
        self._demo_i = 0
        self._demo_next = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_serious_mode(self, enabled: bool):
        self.serious = bool(enabled)
        self._mode_target = 1.0 if enabled else 0.0
        self._flash = 1.0
        if enabled and self.expression in ("neutral", "scan"):
            self.expression = "neutral"
            self._expr_until = time.time() + 99
        self.update()

    def set_state(self, state: str):
        s = (state or "idle").lower()
        if "listen" in s:
            self.state = "listen"
        elif "think" in s or "process" in s:
            self.state = "think"
            if self.expression == "neutral":
                self.set_expression("think", 5)
        elif "speak" in s:
            self.state = "speak"
        else:
            self.state = "idle"
        self.update()

    def set_expression(self, exp: str, hold_sec: float = 5.0):
        exp = (exp or "neutral").lower().strip()
        aliases = {
            "happy": "happy", "welcoming": "happy", "smile": "happy",
            "cool": "cool", "confident": "cool",
            "think": "think", "thinking": "think", "processing": "think", "curious": "think",
            "wink": "wink", "playful": "wink",
            "surprise": "surprise", "surprised": "surprise", "shock": "surprise", "shocked": "surprise",
            "skeptical": "skeptical", "doubt": "skeptical", "doubtful": "skeptical",
            "calm": "calm", "resting": "calm",
            "sad": "sad", "apologetic": "sad", "sorry": "sad",
            "scan": "scan", "scanning": "scan", "focused": "scan", "hunt": "scan",
            "sassy": "sassy", "energetic": "sassy",
            "glitch": "glitch", "error": "glitch",
            "angry": "angry", "mad": "angry", "gussa": "angry", "rage": "angry",
            "neutral": "neutral", "idle": "neutral", "focus": "neutral",
        }
        exp = aliases.get(exp, exp)
        if exp not in EXPRESSIONS:
            exp = "neutral"
        self.expression = exp
        self._expr_until = time.time() + hold_sec
        if exp == "wink":
            self._wink_side = "R"
            self._wink_until = time.time() + 0.7
        self.update()

    def apply_reply_text(self, text: str):
        """All emojis from reply → badge row; strongest mood → eyes."""
        text = text or ""
        emojis = extract_emojis(text)

        chosen_expr = None
        if emojis:
            self._chat_emojis = emojis[:MAX_BADGE_EMOJIS]
            self._chat_emoji_until = time.time() + 8.0
            self._emoji_alpha = 0.0
            self._emoji_scale = 0.4
            best_p = -1
            for em in emojis:
                e = map_emoji_to_expr(em)
                if e is None:
                    continue
                prio = EXPR_PRIORITY.get(e, 0)
                if prio > best_p:
                    best_p = prio
                    chosen_expr = e
            if chosen_expr is None:
                chosen_expr = "happy"
        else:
            self._chat_emojis = []
            self._chat_emoji_until = min(self._chat_emoji_until, time.time() + 0.4)

        t = text.lower()
        if chosen_expr:
            self.set_expression(chosen_expr, 6.0)
        elif any(w in t for w in ("angry", "gussa", "mad", "hate")):
            self.set_expression("angry")
        elif any(w in t for w in ("sorry", "sad", "apolog")):
            self.set_expression("sad")
        elif any(w in t for w in ("wow", "surprise", "shock")):
            self.set_expression("surprise")
        elif "wink" in t:
            self.set_expression("wink")
        elif any(w in t for w in ("think", "hmm", "process")):
            self.set_expression("think")
        elif any(w in t for w in ("happy", "great", "nice", "haha", "love")):
            self.set_expression("happy")
        elif any(w in t for w in ("error", "glitch", "fail")):
            self.set_expression("glitch")
        elif any(w in t for w in ("scan", "search")):
            self.set_expression("scan")
        elif not self.serious:
            self.set_expression("neutral", 2)

    def start_expression_demo(self):
        self._demo = True
        self._demo_i = 0
        self._demo_next = time.time()
        self._chat_emojis = []
        self.set_expression(EXPRESSIONS[0], 2.5)

    def stop_expression_demo(self):
        self._demo = False
        self._chat_emojis = []
        self.set_expression("neutral", 2)

    def toggle_expression_demo(self):
        if self._demo:
            self.stop_expression_demo()
        else:
            self.start_expression_demo()
        return self._demo

    def _tick(self):
        self._t += 0.016
        now = time.time()

        self._mode += (self._mode_target - self._mode) * 0.12
        if abs(self._mode - self._mode_target) < 0.002:
            self._mode = self._mode_target
        if self._flash > 0:
            self._flash = max(0.0, self._flash - 0.05)

        if now > self._chat_emoji_until and not self._demo:
            self._chat_emojis = []

        want = 1.0 if (self._chat_emojis or (self._demo and self.expression != "neutral")) else 0.0
        self._emoji_alpha += (want - self._emoji_alpha) * 0.12
        target_scale = 1.0 if want > 0.5 else 0.5
        self._emoji_scale += (target_scale - self._emoji_scale) * 0.15

        speed = 2.4 if self.expression in ("scan", "glitch", "sassy") else (
            1.6 if self.expression in ("think", "angry") else 0.7
        )
        self._ring = (self._ring + speed) % 360

        if self._demo and now >= self._demo_next:
            self._demo_i = (self._demo_i + 1) % len(EXPRESSIONS)
            self.set_expression(EXPRESSIONS[self._demo_i], 2.4)
            fb = EXPR_FALLBACK_EMOJI.get(EXPRESSIONS[self._demo_i], "")
            self._chat_emojis = [fb] if fb else []
            self._chat_emoji_until = now + 2.5
            self._emoji_scale = 0.5
            self._demo_next = now + 2.6

        if self.expression != "neutral" and now > self._expr_until and not self._demo:
            self.expression = "neutral"

        if now >= self._next_blink and self.expression != "wink":
            self._blink_target = 0.0
            self._next_blink = now + (5.5 if self._mode > 0.5 else 2.8)
        if self._blink < 0.05 and self._blink_target < 0.5:
            self._blink_target = 1.0
        if self._wink_side and now > self._wink_until:
            self._wink_side = None
            if self.expression == "wink" and not self._demo:
                self.expression = "neutral"
        self._blink += (self._blink_target - self._blink) * 0.45

        exp = self.expression
        if exp == "think":
            self._look_tx, self._look_ty = 0.55, -0.25
        elif exp == "scan":
            self._look_tx = 0.6 * math.sin(self._t * 2.0)
            self._look_ty = 0.22 * math.cos(self._t * 1.4)
        elif exp == "cool":
            self._look_tx, self._look_ty = 0.28, -0.08
        elif exp == "skeptical":
            self._look_tx, self._look_ty = -0.3, 0.08
        elif exp == "sad":
            self._look_tx, self._look_ty = 0.0, 0.4
        elif exp == "sassy":
            self._look_tx = 0.35 * math.sin(self._t * 2.2)
            self._look_ty = -0.15
        elif exp == "glitch":
            self._look_tx = 0.45 * math.sin(self._t * 25)
            self._look_ty = 0.3 * math.cos(self._t * 30)
        elif exp == "angry":
            self._look_tx, self._look_ty = 0.0, 0.06
        else:
            if self.serious:
                self._look_tx = 0.02 * math.sin(self._t * 8)
                self._look_ty = 0.015 * math.cos(self._t * 9)
            else:
                self._look_tx = self._look_ty = 0.0

        self._look_x += (self._look_tx - self._look_x) * 0.14
        self._look_y += (self._look_ty - self._look_y) * 0.14

        if exp in ("happy", "sassy", "glitch", "angry") or self.state == "speak":
            self._pulse = 0.45 + 0.45 * math.sin(self._t * (14 if exp == "angry" else 9))
        elif exp == "surprise":
            self._pulse = 0.55
        else:
            self._pulse += (0.05 - self._pulse) * 0.1
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w * 0.5, h * 0.48
        gap = min(w, h) * 0.34
        ew = min(w, h) * 0.28
        eh = ew * 0.52
        m = self._mode
        exp = self.expression

        if exp == "glitch":
            primary = QColor(0, 255, 120) if int(self._t * 12) % 2 else QColor(255, 40, 70)
            secondary = QColor(255, 0, 100)
            core = QColor(0, 0, 0)
        elif exp == "angry":
            primary = QColor(255, 45, 55)
            secondary = QColor(200, 20, 30)
            core = QColor(25, 0, 0)
        elif exp == "sad":
            primary = QColor(90, 150, 220)
            secondary = QColor(50, 100, 180)
            core = QColor(10, 20, 40)
        elif exp == "scan":
            primary = QColor(0, 255, 200) if m < 0.5 else QColor(255, 120, 40)
            secondary = QColor(0, 180, 255) if m < 0.5 else QColor(255, 60, 20)
            core = QColor(0, 20, 30)
        elif m > 0.5:
            primary = QColor(255, 30, 55)
            secondary = QColor(180, 20, 40)
            core = QColor(40, 0, 8)
        else:
            primary = QColor(0, 230, 255)
            secondary = QColor(0, 150, 255)
            core = QColor(0, 30, 50)

        gx = 5 * math.sin(self._t * 40) if exp == "glitch" else 0
        self._draw_eye(p, cx - gap + gx, cy, ew, eh, "L", primary, secondary, core, m, exp)
        self._draw_eye(p, cx + gap - gx, cy, ew, eh, "R", primary, secondary, core, m, exp)

        # ---- multi-emoji row (no cut) ----
        badges = list(self._chat_emojis)
        if not badges and self._demo:
            fb = EXPR_FALLBACK_EMOJI.get(exp, "")
            if fb:
                badges = [fb]

        if badges and self._emoji_alpha > 0.05:
            float_y = 3.0 * math.sin(self._t * 3.2)
            pulse = 0.92 + 0.08 * math.sin(self._t * 5.0)
            scale = self._emoji_scale * pulse
            alpha = int(255 * self._emoji_alpha)
            n = len(badges)
            # smaller font if many
            font_size = 18 if n <= 2 else (15 if n <= 4 else 13)
            slot = 28 if n <= 2 else (24 if n <= 4 else 20)
            total_w = n * slot
            start_x = cx - total_w * 0.5 + slot * 0.5

            p.setFont(QFont("Segoe UI Emoji", font_size))
            p.setPen(QColor(255, 255, 255, alpha))
            for i, em in enumerate(badges):
                x = start_x + i * slot
                y = cy + eh * 1.62 + float_y
                p.save()
                p.translate(x, y)
                p.scale(scale, scale)
                p.drawText(QRectF(-14, -12, 28, 28), Qt.AlignCenter, em)
                p.restore()

        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.setPen(QColor(primary.red(), primary.green(), primary.blue(), 220))
        tag = exp.upper()
        if self._demo:
            tag = f"DEMO · {tag}"
        elif self.serious:
            tag = f"FOCUS · {tag}"
        p.drawText(QRectF(0, h - 26, w, 22), Qt.AlignCenter, tag)

        if self.serious and exp != "scan":
            p.setPen(QColor(255, 50, 70, 200))
            p.setFont(QFont("Consolas", 9, QFont.Bold))
            p.drawText(QPointF(cx - 55, cy - eh * 2.0), "AI / FOCUS LOCKED")
        if exp == "scan":
            p.setPen(QColor(primary.red(), primary.green(), primary.blue(), 210))
            p.setFont(QFont("Consolas", 9, QFont.Bold))
            p.drawText(QPointF(cx - 36, cy - eh * 2.0), "SCANNING…")
        if exp == "angry":
            p.setPen(QColor(255, 60, 60, 220))
            p.setFont(QFont("Consolas", 9, QFont.Bold))
            p.drawText(QPointF(cx - 32, cy - eh * 2.0), "⚠ HOSTILE")

        if self._flash > 0.05:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, int(28 * self._flash)))
            p.drawRect(self.rect())
        p.end()

    def _draw_eye(self, p, cx, cy, ew, eh, side, primary, secondary, core, m, exp):
        open_y = max(0.04, min(1.0, self._blink))
        if self._wink_side == side:
            open_y = 0.03
        if open_y < 0.08:
            p.setPen(QPen(primary, 3.5))
            p.drawLine(QPointF(cx - ew, cy), QPointF(cx + ew, cy))
            return

        if exp == "surprise":
            open_y, eh = 1.0, eh * 1.35
        elif exp == "happy":
            open_y *= 0.55
        elif exp == "cool":
            open_y *= 0.62
        elif exp == "sad":
            open_y *= 0.55
            cy += eh * 0.12
        elif exp == "skeptical":
            open_y *= 0.68
        elif exp == "calm":
            open_y *= 0.85
        elif exp == "sassy":
            open_y *= 0.7
        elif exp == "angry":
            open_y *= 0.52
            eh *= 0.88
        elif exp == "scan":
            open_y = max(open_y, 0.88)
            eh *= 1.05
        elif self.serious:
            open_y = 0.58 + open_y * 0.32
            eh *= 0.9

        eh_open = eh * open_y

        g = QRadialGradient(cx, cy, ew * 1.4)
        c = QColor(primary)
        c.setAlpha(int(35 + 70 * self._pulse))
        g.setColorAt(0.0, c)
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(cx, cy), ew * 1.3, eh_open * 1.15)

        upper, lower = [], []
        n = 28
        for i in range(n + 1):
            t = i / n
            x = cx + ew * (1 - 2 * t) if side == "L" else cx + ew * (-1 + 2 * t)
            arch = math.sin(math.pi * t)
            wing = 0.28 * (t ** 1.5)
            uy = cy - eh_open * (0.92 * arch + 0.12 + wing)
            ly = cy + eh_open * (0.5 * arch + 0.14)
            if exp == "happy":
                ly -= arch * eh_open * 0.28
            if exp == "sad":
                uy += (0.5 - abs(t - 0.5)) * eh_open * 0.25
            if exp == "angry":
                uy += t * eh_open * 0.08
            upper.append(QPointF(x, uy))
            lower.append(QPointF(x, ly))
        if side == "L":
            upper.append(QPointF(cx - ew * 1.08, cy - eh_open * 0.45))
        else:
            upper.append(QPointF(cx + ew * 1.08, cy - eh_open * 0.45))

        path = QPainterPath()
        path.moveTo(upper[0])
        for pt in upper[1:]:
            path.lineTo(pt)
        for pt in reversed(lower):
            path.lineTo(pt)
        path.closeSubpath()

        p.setBrush(
            QColor(4, 8, 14)
            if m < 0.5 and exp not in ("angry", "scan")
            else QColor(12, 2, 5)
        )
        p.drawPath(path)

        p.save()
        p.setClipPath(path)

        ix = cx + self._look_x * ew * 0.4
        iy = cy + self._look_y * eh_open * 0.35
        ir = min(ew * 0.36, eh_open * 0.72)
        if exp == "surprise":
            ir = min(ew * 0.44, eh_open * 0.75)
        if exp == "scan":
            ir = min(ew * 0.4, eh_open * 0.7)
        if self.serious and exp != "scan":
            ir *= 0.88
        if exp == "angry":
            ir *= 0.9

        ig = QRadialGradient(ix, iy, ir)
        ig.setColorAt(0.0, QColor(255, 255, 255, 230))
        ig.setColorAt(0.22, primary)
        ig.setColorAt(0.55, secondary)
        ig.setColorAt(1.0, QColor(0, 0, 0))
        p.setBrush(ig)
        p.drawEllipse(QPointF(ix, iy), ir, ir)

        pen = QPen(primary, 1.5)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(ix, iy), ir * 0.85, ir * 0.85)

        if exp == "scan":
            for ang in range(0, 360, 45):
                rad = math.radians(ang + self._ring)
                p.drawLine(
                    QPointF(ix + math.cos(rad) * ir * 1.25, iy + math.sin(rad) * ir * 1.25),
                    QPointF(ix + math.cos(rad) * ir * 1.4, iy + math.sin(rad) * ir * 1.4),
                )
        elif self.serious:
            arm = ir * 1.35
            p.drawLine(QPointF(ix - arm, iy), QPointF(ix - ir * 0.9, iy))
            p.drawLine(QPointF(ix + ir * 0.9, iy), QPointF(ix + arm, iy))

        if exp == "angry":
            p.setPen(QPen(primary, 2))
            p.drawLine(QPointF(ix - ir * 0.5, iy - ir * 0.3), QPointF(ix, iy - ir * 0.05))
            p.drawLine(QPointF(ix + ir * 0.5, iy - ir * 0.3), QPointF(ix, iy - ir * 0.05))

        pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.save()
        p.translate(ix, iy)
        p.rotate(self._ring)
        p.drawEllipse(QPointF(0, 0), ir * 1.12, ir * 1.12)
        p.restore()

        if exp == "surprise":
            pr = ir * 0.42
        elif exp == "scan":
            pr = ir * 0.2
        elif self.serious and exp != "scan":
            pr = ir * 0.15
        elif exp in ("cool", "angry"):
            pr = ir * 0.16
        elif exp == "sad":
            pr = ir * 0.32
        else:
            pr = ir * 0.26

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0))
        p.drawEllipse(QPointF(ix, iy), pr, pr)
        p.setBrush(QColor(255, 255, 255, 250))
        p.drawEllipse(
            QPointF(ix - pr * 0.35, iy - pr * 0.4),
            max(2.0, pr * 0.4),
            max(2.0, pr * 0.35),
        )
        p.restore()

        pen = QPen(primary, 2.8)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        up = QPainterPath()
        up.moveTo(upper[0])
        for pt in upper[1:]:
            up.lineTo(pt)
        p.drawPath(up)

        self._lashes(p, upper, side, primary)
        self._brow(p, cx, cy, ew, eh_open, side, primary, exp)

    def _lashes(self, p, upper, side, col):
        pts = upper[:-1]
        n = len(pts)
        if n < 5:
            return
        pen = QPen(col)
        pen.setCapStyle(Qt.RoundCap)
        for i in range(9):
            t = 0.08 + 0.84 * (i / 8)
            idx = min(n - 2, int(t * (n - 1)))
            a = pts[idx]
            wave = math.sin(t * math.pi)
            length = 10 + 14 * wave
            ang = math.radians(-90 + (-22 if side == "L" else 22) * (t - 0.5) * 2)
            pen.setWidthF(1.6 + wave)
            p.setPen(pen)
            p.drawLine(
                a,
                QPointF(a.x() + math.cos(ang) * length, a.y() + math.sin(ang) * length),
            )

    def _brow(self, p, cx, cy, ew, eh, side, col, exp):
        pen = QPen(col)
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidthF(3.0)
        p.setPen(pen)
        y = cy - eh * 1.55
        if exp == "surprise":
            a, b = (
                (QPointF(cx - ew * 0.85, y - 18), QPointF(cx + ew * 0.35, y - 20))
                if side == "L"
                else (QPointF(cx + ew * 0.85, y - 18), QPointF(cx - ew * 0.35, y - 20))
            )
        elif exp == "angry":
            a, b = (
                (QPointF(cx - ew * 0.92, y + 16), QPointF(cx + ew * 0.45, y - 14))
                if side == "L"
                else (QPointF(cx + ew * 0.92, y + 16), QPointF(cx - ew * 0.45, y - 14))
            )
        elif exp == "think" and side == "R":
            a, b = QPointF(cx - ew * 0.25, y + 2), QPointF(cx + ew * 0.9, y - 18)
        elif exp == "sad":
            a, b = (
                (QPointF(cx - ew * 0.85, y - 4), QPointF(cx + ew * 0.35, y + 14))
                if side == "L"
                else (QPointF(cx + ew * 0.85, y - 4), QPointF(cx - ew * 0.35, y + 14))
            )
        elif self.serious or exp == "scan":
            a, b = (
                (QPointF(cx - ew * 0.9, y + 8), QPointF(cx + ew * 0.4, y - 6))
                if side == "L"
                else (QPointF(cx + ew * 0.9, y + 8), QPointF(cx - ew * 0.4, y - 6))
            )
        else:
            a, b = (
                (QPointF(cx - ew * 0.8, y + 2), QPointF(cx + ew * 0.35, y - 4))
                if side == "L"
                else (QPointF(cx + ew * 0.8, y + 2), QPointF(cx - ew * 0.35, y - 4))
            )
        p.drawLine(a, b)