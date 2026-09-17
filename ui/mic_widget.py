from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QTimer


class MicWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.radius = 28
        self.grow = True

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

        self.setMinimumSize(120,120)

    def animate(self):
        if self.grow:
            self.radius += 1
            if self.radius >= 40:
                self.grow = False
        else:
            self.radius -= 1
            if self.radius <= 28:
                self.grow = True

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.translate(self.width()/2, self.height()/2)

        painter.setBrush(QColor("#00E5FF"))
        painter.setPen(QColor("#00E5FF"))

        painter.drawEllipse(-self.radius//2,
                            -self.radius//2,
                            self.radius,
                            self.radius)